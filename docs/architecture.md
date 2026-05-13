# Architecture

`gsd-econ` is a thin overlay. Its job is to wire two existing systems together and add the minimum domain logic needed to make them useful for empirical economics research.

## The three layers

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   gsd-econ (this repo)                                           │
│   ─────────────────────                                          │
│   • Research-shaped phase taxonomy                               │
│   • Domain commands: /gsd-new-paper, /gsd-discuss-identification │
│   • Domain agents: identification-checker, econometrician, ...   │
│   • Bootstrap doc templates                                      │
│   • Custom RUT tests for econ-specific concerns                  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   research-unit-tests (rdahis)                                   │
│   ──────────────────────────                                     │
│   • Declarative quality checks (markdown + YAML registry)        │
│   • Tagged by methodology, scope, severity, clarity              │
│   • Universal + DiD + IV + RDD test families                     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   GSD (TÂCHES)                                                   │
│   ─────────────                                                  │
│   • discuss → plan → execute → verify → ship loop                │
│   • Multi-agent orchestration with fresh-context executors       │
│   • State management (PROJECT.md, REQUIREMENTS.md, STATE.md)     │
│   • Atomic git commits per task                                  │
│   • Fix-plan generation when verification fails                  │
│   • XML-formatted task plans                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

Each layer has a clean responsibility:

- **GSD** owns the *machinery*: how a session is structured, how state survives across context windows, how plans are decomposed into tasks, how tasks are executed in parallel waves, how failed verification triggers a fix loop.
- **RUT** owns the *standards*: what counts as a passing test for a given methodology, organized as machine-readable declarative checks.
- **gsd-econ** owns the *domain shape*: how a research paper differs from a software project, and which RUT tests are required at which phase.

## What flows where

### At project bootstrap (`/gsd-new-paper`)

The single bootstrap command supports two modes:

- `/gsd-new-paper --new` (greenfield) — runs the framing interview and literature scout below
- `/gsd-new-paper --adopt` (brownfield) — reads an existing manuscript and codebase to infer the methodology declaration, then runs the same project-level literature scout before handoff; see [`adopting-mid-project.md`](adopting-mid-project.md) for the retrofit flow
- `/gsd-new-paper` (auto) — auto-detects mode based on project state

For greenfield bootstrap:

```
user input
   │
   ▼
gsd-econ /gsd-new-paper command
   │
   ├──► spawns econ-researcher agent (Semantic Scholar, JEL codes)
   │       │
   │       ▼
   │    research findings → .planning/research/
   │
   ├──► populates from templates:
   │       PROJECT.md      ← research question, contribution
   │       REQUIREMENTS.md ← hypotheses, primary/secondary outcomes
   │       METHODOLOGY.md  ← identification strategy, RUT tag set
   │       ROADMAP.md      ← phased empirical pipeline
   │
   └──► writes test contract:
            METHODOLOGY.md declares e.g. methodology: did, scope: paper
            → all DiD-tagged blockers in RUT registry become required gates
```

For brownfield adoption, the same `.planning/research/literature-scout.md` artifact is required before handoff. If the user defers the scout, `/gsd-new-paper --adopt` writes an explicit deferred-scout stub instead of leaving the file absent. Downstream commands can then distinguish "literature context incomplete" from "bootstrap forgot to run."

### Per phase (`/gsd-discuss-identification` → `/gsd-plan-empirics` → `/gsd-execute-phase` → `/gsd-verify-replication`)

```
discuss phase
   │
   │   /gsd-discuss-identification asks identification-specific questions
   │   based on the methodology tag (DiD asks parallel-trends questions,
   │   IV asks exclusion-restriction questions, etc.)
   │
   ▼
plan phase
   │
   │   /gsd-plan-empirics constrains the planner to produce empirical
   │   tasks (regression specs, cluster level, FE structure, SE method).
   │   identification-checker reviews planned specs against textbook threats.
   │
   ▼
execute phase
   │
   │   GSD's execute-phase runs unchanged: parallel waves, fresh contexts,
   │   atomic commits per task. The "task" is a regression spec or a
   │   robustness column rather than a feature.
   │
   ▼
verify phase
   │
   │   /gsd-verify-replication replaces /gsd-verify-work.
   │   replication-verifier agent:
   │     1. Identifies applicable tests:
   │        - METHODOLOGY.md → tag set (e.g., did, universal)
   │        - phase context → scope (paper / replication)
   │     2. Loads matching tests from registry.yaml (RUT + gsd-econ)
   │     3. For each test:
   │        - deterministic → run criterion against codebase/output
   │        - heuristic → present evidence, await human ack
   │        - judgment → defer to referee-sim phase
   │     4. Maps results to GSD verification states:
   │        - blocker fail → triggers fix-plan loop
   │        - warning → recorded in {phase}-VERIFICATION.md
   │        - info → logged in STATE.md
   │
   ▼
ship phase
   │
   │   /gsd-submit-paper replaces /gsd-ship.
   │   Final referee-sim run (judgment-clarity tests) before package.
   │   Output: paper PDF + replication archive + cover letter.
```

## File ownership map

```
.planning/                          (created and managed by GSD; gsd-econ adds files)
├── config.json                     ← GSD owns; gsd-econ writes agent_skills wiring
├── PROJECT.md                      ← gsd-econ template, you fill in
├── REQUIREMENTS.md                 ← gsd-econ template, you fill in
├── METHODOLOGY.md                  ← gsd-econ template, drives test loading
├── ROADMAP.md                      ← gsd-econ template, you fill in
├── STATE.md                        ← GSD owns; gsd-econ verifier writes test history here
├── research/                       ← GSD subagents write here
└── phases/
    └── 01-data-cleaning/
        ├── CONTEXT.md              ← /gsd-discuss-identification output
        ├── RESEARCH.md             ← /gsd-plan-empirics researcher output
        ├── 01-PLAN.md              ← XML task plan
        ├── 01-SUMMARY.md           ← post-execution
        ├── VERIFICATION.md         ← gsd-econ verifier writes test results here
        └── UAT.md                  ← (unused for research; replaced by VERIFICATION.md)

vendor/
├── research-unit-tests/            ← submodule, never modified locally
│   ├── registry.yaml
│   └── core/
│       └── *.md
└── gsd-econ/                       ← submodule, this repo
    ├── tests/
    │   ├── registry.yaml           ← merged with RUT's registry by verifier
    │   └── core/
    └── ...
```

## Why two test registries?

RUT's upstream registry (`vendor/research-unit-tests/registry.yaml`) is the canonical, community-vetted set. gsd-econ's local registry (`vendor/gsd-econ/tests/registry.yaml`) holds tests that:

- Are domain-specific to empirical economics in ways the upstream registry doesn't yet cover (Conley SEs, attrition balance, PAP-deviation disclosure)
- Are too opinionated or labor/development-specific for the universal core
- Are work-in-progress and not yet ready to PR upstream

The verifier merges both registries at runtime and applies tag-based filtering uniformly. Tests in `gsd-econ/tests/core/` that prove broadly useful are candidates for upstream PRs to RUT.

## What gsd-econ does *not* do

- **It does not run code.** RUT tests are declarative. The verifier interprets them and orchestrates checks; running `make all` or compiling LaTeX is the executor's job, invoked through GSD's existing tooling.
- **It does not replace GSD's core commands.** `/gsd-new-project`, `/gsd-discuss-phase`, `/gsd-plan-phase`, `/gsd-execute-phase` remain available. The overlay commands (`/gsd-new-paper`, `/gsd-plan-empirics`, etc.) are research-shaped wrappers — they call into the same machinery with different prompts.
- **It does not fork RUT.** Tests we add live in `gsd-econ/tests/`. We never edit `vendor/research-unit-tests/`. This keeps upstream pulls clean.
- **It does not manage your data.** IRB compliance, raw-data privacy, .gitignore for `data/raw/`, etc. — your responsibility. The example in `examples/` shows recommended patterns.

## Extension points

Three places are designed for customization without forking:

1. **`tests/community/`** — your own RUT-style tests for personal or lab-specific concerns.
2. **`agents/`** — clone any agent prompt and rename. The install script picks up everything in this directory.
3. **`templates/`** — edit the bootstrap docs to match your group's house style.

For changes you want to share, the README has contribution notes.
