# gsd-econ

[![verify](https://github.com/USERNAME/gsd-econ/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/gsd-econ/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A spec-driven workflow for empirical economics research, built on top of [GSD](https://github.com/gsd-build/get-shit-done) and [research-unit-tests](https://github.com/rdahis/research-unit-tests).**

> Treat papers like software projects: declarative specs, atomic commits, automated verification — but with an identification strategy at the center, not a feature list.

> ⚠ Pre-1.0. The repo passes its own structural verification suite ([`VERIFICATION.md`](VERIFICATION.md)), but the LLM-driven workflow has not yet been used end-to-end on a real submission. Treat as a working scaffold; expect to fork and customize.

---

## What this is

`gsd-econ` is an **overlay** for GSD that adapts its primitives (phases → plans → execution → verification) to the structure of an empirical research paper. It plugs `research-unit-tests` (RUT) into GSD's verification gate so that "does this phase pass?" is answered by methodology-specific quality checks instead of software UAT.

You get:

- **A research-shaped phase taxonomy** — data → identification → main results → robustness → writing → submission, instead of vertical feature slices.
- **Custom subagents** that know about identification, econometric pitfalls, replication packages, and adversarial peer review.
- **RUT-driven verification** — declared methodology tags (DiD, IV, RDD, field experiment, etc.) drive which tests gate each phase.
- **Bootstrap templates** for `PROJECT.md`, `REQUIREMENTS.md`, `METHODOLOGY.md`, and the per-phase `CONTEXT.md` files, oriented around research questions rather than user stories.
- **Custom tests** for econometric concerns the upstream RUT registry doesn't cover yet (Conley SEs, attrition balance, exclusion restriction prose, PAP-deviation disclosure).

This is **not** a fork of GSD. It runs as an overlay: install GSD with `--minimal`, then drop these files into your project. Updates to GSD propagate cleanly.

---

## Why

GSD is excellent at what it does — context engineering and orchestration for Claude Code, OpenCode, and friends. But its verification step (`gsd-verify-work`) is built around software UAT: "does the feature work for you?" That's the wrong question for a paper. The right questions are: do the parallel trends hold? Is the first-stage F-stat above 10? Does the replication package produce identical numbers from raw data? Is the contribution actually new?

`research-unit-tests` (rdahis) provides exactly that vocabulary — declarative quality checks tagged by methodology, scope, severity, and clarity. But RUT alone has no orchestration: nothing runs the tests at the right moment, nothing creates fix plans when blockers fail, nothing manages context across sessions.

The two compose. GSD provides the loop; RUT provides the gates.

```
GSD                              gsd-econ                       RUT
─────────────────────            ─────────────────              ─────────────────
discuss → plan → execute    +    methodology-aware         +   declarative
verify → ship                    phases, agents,                quality checks
context engineering              templates                      by methodology
multi-agent orchestration        bootstrap docs                 by severity
atomic commits                                                  by clarity
fix-plan loop
```

---

## Quick start

Prerequisites: a working OpenCode or Claude Code install, plus `git`, `node`, and `bash`.

```bash
git clone https://github.com/<your-username>/gsd-econ ~/src/gsd-econ
cd ~/papers/my-new-paper && git init

# Install everything for this project
bash ~/src/gsd-econ/install.sh

# Or install gsd-econ commands+agents user-wide
bash ~/src/gsd-econ/install.sh --global

# Re-run after `git pull` to pick up new commands/agents
bash vendor/gsd-econ/install.sh --wire-only
```

Modes:
- **`--project`** (default) — full setup for one paper: GSD core (`--minimal`), RUT submodule, gsd-econ overlay, all wired into the current directory.
- **`--global`** — symlinks gsd-econ commands and agents into `~/.claude/agents/` (and/or `~/.opencode/agent/`) so they're available across projects. Per-project setup (`.planning/` scaffold, RUT submodule) still runs per-project.
- **`--wire-only`** — re-link commands and agents and re-merge config without touching submodules. The standard "I just pulled new gsd-econ" affordance.

Useful flags: `--skip-gsd`, `--skip-rut`, `--runtime claude|opencode|both`, `--dry-run`, `--yes`, `--help`.

After install, in your runtime:

```
/gsd-help                # confirm gsd-econ commands appear
/gsd-new-paper           # auto-detects new vs mid-project
/gsd-new-paper --new     # force greenfield mode
/gsd-new-paper --adopt   # force brownfield mode (existing manuscript)
```

`/gsd-new-paper` is the single entry point. It auto-detects whether you're starting fresh or adopting an in-progress paper. For brownfield adoption details, see [`docs/adopting-mid-project.md`](docs/adopting-mid-project.md).

Detailed install: see [`INSTALL.md`](INSTALL.md).

---

## The workflow

```
                                                 [you]
                                                   │
                            ┌──────────────────────┴──────────────────────┐
                            │                                             │
                  /gsd-new-paper                                   /gsd-rr-response
                  /gsd-pre-register                                (R&R cycles)
                            │
                            ▼
                  ┌─────────────────┐
                  │  Phase 1: Data  │
                  │     Phase 2:    │
                  │      ...        │ ◄──── per phase: discuss → plan → execute → verify
                  │  Phase N: Subm. │
                  └─────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
      /gsd-discuss-identification  /gsd-plan-empirics
              │                           │
              └───────────────┬───────────┘
                              ▼
                   /gsd-execute-phase  ◄── (GSD core)
                              │
                              ▼
                   /gsd-verify-replication
                              │
                              ▼
                   ┌──────────────────┐
                   │   RUT tests run  │ ◄── methodology tags filter registry
                   │   blocker fail?  │
                   │   yes → fix plan │
                   │   no → advance   │
                   └──────────────────┘
                              │
                              ▼
                       /gsd-polish-pass
                       (5 polish agents in parallel:
                        numbers, cross-refs, citations,
                        consistency, claims; up to 2 rounds)
                              │
                              ▼
                       /gsd-submit-paper
                       (final referee-sim run)
```

Phases for a typical empirical paper:

1. **Data acquisition + cleaning** (raw → analysis-ready panel)
2. **Stylized facts / descriptives**
3. **Identification diagnostics** (parallel trends, first-stage, manipulation tests)
4. **Main specification**
5. **Robustness + heterogeneity**
6. **Monte Carlo / power** (if applicable)
7. **Tables + figures pipeline**
8. **Manuscript writing** (intro/data/results/discussion)
9. **Replication package + submission**

Each is a GSD phase. RUT tests filtered by your `METHODOLOGY.md` declaration drive the verification gate at the end of each phase.

---

## What's in this repo

```
gsd-econ/
├── README.md                      # this file
├── LICENSE                        # MIT
├── INSTALL.md                     # setup details
├── VERIFICATION.md                # how the repo is itself tested
├── CONTRIBUTING.md
├── Makefile                       # `make verify` and friends
├── install.sh                     # one-command install (--project | --global | --wire-only)
├── AGENTS.md                      # always-on project rules (loaded by OpenCode/Claude Code)
├── rules/                         # lazy-loaded cross-cutting rules
│   ├── identification.md
│   ├── methodology-integrity.md
│   ├── file-discipline.md
│   ├── git-discipline.md
│   ├── preregistration.md
│   ├── data-handling.md
│   ├── manuscript-discipline.md
│   └── uncertainty-honesty.md
├── docs/
│   ├── architecture.md            # how the three layers compose
│   ├── adapting-gsd.md            # what we override vs reuse
│   ├── adopting-mid-project.md    # brownfield retrofit guide
│   ├── model-tiers.md             # reasoning-tier system for agents
│   ├── meta-cognition.md          # --meta-cog flag and the offload-policy system
│   ├── verification-flow.md       # how RUT severities map to GSD gates
│   └── writing-tests.md           # authoring custom RUT tests
├── commands/                      # overlay commands (slash-invoked)
│   ├── gsd-new-paper.md
│   ├── gsd-discuss-identification.md
│   ├── gsd-plan-empirics.md
│   ├── gsd-verify-replication.md
│   ├── gsd-tables-figures.md
│   ├── gsd-pre-register.md
│   ├── gsd-rr-response.md
│   ├── gsd-polish-pass.md         # final pre-submission audit fan-out
│   ├── gsd-submit-paper.md
│   ├── gsd-test-paper.md          # run RUT tests for current methodology
│   └── gsd-referee-sim.md
├── agents/                        # specialized subagents (each declares model_tier)
│   ├── econ-researcher.md
│   ├── identification-checker.md
│   ├── econometrician.md
│   ├── replication-verifier.md
│   ├── tables-figures-builder.md
│   ├── referee-sim.md             # default-mode referee (heavy tier)
│   ├── referee-sim-light.md       # --heavy-mode parallel referee (light tier)
│   ├── referee-deliberator.md     # --heavy-mode synthesizer (heavy tier)
│   ├── polish-numbers.md          # quantitative-claim audit
│   ├── polish-cross-refs.md       # \ref / \cite resolution
│   ├── polish-citations.md        # citation-claim accuracy
│   ├── polish-consistency.md      # cross-section consistency
│   └── polish-claims.md           # real-world fact verification
├── skills/
│   ├── econ-research/SKILL.md     # aggregator skill for project-level injection
│   └── openalex-search/           # programmatic search of OpenAlex (pyalex-based)
│       ├── SKILL.md
│       ├── openalex_search.py     # helper module: find_recent_nber, find_evaluation_candidates, ...
│       └── requirements.txt
├── templates/                     # bootstrap doc templates
│   ├── PROJECT.md.template
│   ├── REQUIREMENTS.md.template
│   ├── METHODOLOGY.md.template
│   ├── ROADMAP.md.template
│   ├── STATE.md.template
│   └── PHASE-CONTEXT.md.template
├── tests/                         # custom RUT-style tests
│   ├── README.md
│   ├── registry.yaml
│   ├── core/                      # tests we'd PR upstream to RUT
│   │   ├── iv-exclusion-narrative-explicit.md
│   │   ├── iv-weak-instrument-robust-inference.md
│   │   ├── did-conley-ses-when-spatial.md
│   │   ├── experiment_field-attrition-balance.md
│   │   ├── experiment_field-pap-deviation-disclosed.md
│   │   ├── universal-clustered-ses-justified.md
│   │   ├── universal-multiple-testing-corrected.md
│   │   └── universal-sample-restrictions-stated.md
│   └── community/README.md
├── config/
│   ├── config.json.example        # GSD config with agent_skills wiring
│   └── settings.json.example      # OpenCode/Claude permissions for econ workflows
├── scripts/
│   └── run-tests.sh               # invoke gsd-test-paper from CLI
├── verification/                  # the repo's own test suite
│   ├── README.md
│   ├── conftest.py
│   ├── test_*.py                  # pytest files, structural & consistency checks
│   ├── manual-checklist.md        # behavioral verification (run pre-release)
│   └── requirements.txt
├── .github/workflows/ci.yml       # runs verification/ on every push/PR
└── examples/
    └── example-paper/             # walkthrough showing one phase end-to-end
        ├── PROJECT.md
        ├── REQUIREMENTS.md
        ├── METHODOLOGY.md
        ├── ROADMAP.md
        └── README.md
```

---

## Design principles

1. **Don't fork upstream — overlay.** GSD ships ~86 skills and 33 agents at full install. We use `--minimal` (6 skills, 0 agents) and add our own. RUT is included as a submodule. Both update independently.
2. **Tests are contracts, not vibes.** Every phase declares which RUT tests must pass. The contract lives in `METHODOLOGY.md`, in version control, visible to coauthors and (eventually) referees.
3. **Severity drives behavior.** `blocker` = hard gate, GSD generates fix plans. `warning` = surfaced but advisory. `info` = logged. `judgment`-clarity tests never auto-gate — they're the referee-sim's job.
4. **Identification is sacred.** The default GSD `assumptions` mode (codebase-first, ask only to correct) is dangerous for identification choices. We force `discuss` mode for any phase tagged as identification.
5. **One thing per commit.** A regression spec, a robustness column, a paragraph rewrite, a figure regeneration. Same atomic-commit philosophy GSD uses for software.
7. **Project rules are explicit and lazy-loaded.** `AGENTS.md` at the project root holds always-on invariants (read-only data, user triages decisions, atomic commits). Cross-cutting rules live in `rules/` — loaded on demand when a session encounters relevant work. This follows the OpenCode/Claude Code convention so the rules apply across runtimes without duplication.
8. **Calibrated confidence as a control signal.** Optional `--meta-cog` flag on judgment-heavy commands (`/gsd-plan-empirics`, `/gsd-discuss-identification`, `/gsd-referee-sim`, `/gsd-polish-pass`) replaces single-pass agent calls with N=3 parallel runs and uses disagreement-as-uncertainty to rate findings. Composable with `/gsd-polish-pass --offload-policy {manual|assisted|aggressive}` for trading off triage volume against framework auto-handling. Implements the workflow-level version of Yona, Geva, and Matias (2026); see [`docs/meta-cognition.md`](docs/meta-cognition.md).

---

## Status

Pre-1.0. Built as a working scaffold; expect to fork and customize. Not affiliated with the upstream GSD or RUT projects.

---

## License

MIT. See [`LICENSE`](LICENSE). Upstream GSD and RUT are also MIT-licensed; their copyrights remain with their respective authors.

## Citation and attribution

If you use this software in research that becomes a paper, working paper, preprint, or thesis, please cite it. Citation metadata is in [`CITATION.cff`](CITATION.cff) — GitHub renders a "Cite this repository" button on the repo page that produces APA and BibTeX citations from that file automatically. Tools like `cffconvert`, Zotero, and Zenodo can also parse it directly.

Please also acknowledge the upstream tools the workflow builds on:

- [GSD](https://github.com/gsd-build/get-shit-done) by TÂCHES — the orchestration and context-engineering layer this overlay sits on top of.
- [research-unit-tests](https://github.com/rdahis/research-unit-tests) by rdahis — the verification taxonomy used at every phase gate.

A typical acknowledgment might read: *"This paper was prepared using the gsd-econ workflow ([citation]), which builds on the get-shit-done framework and research-unit-tests."*

This is a norm, not a license requirement — MIT does not compel attribution beyond the license header. But academic credit norms run on goodwill, and acknowledgments help the projects stay funded and maintained.
