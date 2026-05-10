---
name: econ-research
description: Project-level skill that aggregates the gsd-econ workflow knowledge for use by GSD's verifier and plan_check agents. Contains pointers to the test registries, the methodology→test mapping, and the locked-decision protocol.
---

# Skill: econ-research

This skill is loaded into GSD's `verifier` and `plan_check` agents via the `agent_skills` config wiring (see `vendor/gsd-econ/config/config.json.example`). Its job is to give those agents the context they need without bloating every conversation.

## What this skill provides

- **Test registry locations:**
  - Upstream RUT: `vendor/research-unit-tests/registry.yaml`, tests in `vendor/research-unit-tests/core/`
  - gsd-econ: `vendor/gsd-econ/tests/registry.yaml`, tests in `vendor/gsd-econ/tests/core/`
  - Project-private: `tests/community/<your-username>/`

- **Methodology → test mapping rule:**
  ```
  applicable = registry.filter(
      methodology ∈ METHODOLOGY.primary
                ∪ METHODOLOGY.secondary
                ∪ {"universal"}
      ∧ scope    ⊆ phase.scope_set
      ∧ id       ∉ METHODOLOGY.test_exclusions
  )
  ```

- **Severity → gate behavior mapping:**
  - `blocker` deterministic → hard gate, fix-plan loop on fail
  - `blocker` heuristic → human ack required, fix-plan loop on rejection
  - `blocker` judgment → deferred to `/gsd-referee-sim`
  - `warning` → surface in `VERIFICATION.md`, don't block
  - `info` → log in `STATE.md`

- **Locked decision protocol:**
  - Decisions in `METHODOLOGY.md` and per-phase `CONTEXT.md` flagged `[LOCKED-IN-PHASE-N]` should not be revisited without an explicit override.
  - The verifier reads `[LOCKED-IN-PHASE-N]` markers and treats them as constraints on its evaluation.

## How to read a test markdown

Every RUT-format test has these required sections:
- Methodology, Scope, Severity, Clarity (frontmatter or top of body)
- Criterion (what passing means)
- How to check (operational instructions)
- Pass condition (the contract)

The `replication-verifier` reads "How to check" and "Pass condition" verbatim, applies them, and returns a structured verdict. See `agents/replication-verifier.md` for the full protocol.

## How to interpret `METHODOLOGY.md`

```yaml
primary: did                  # one tag, dominant identification
secondary: [iv, ols]          # supporting strategies (zero or more)
scope: paper                  # paper / proposal / replication
target_journal: jae           # short journal handle

prereg:
  required: true
  url: https://aearegistry.org/...   # empty until pre-registered
  hash: sha256:abc...
  submitted_at: 2026-04-12

test_inclusions:
  - <test_id>                  # tests to force-include even if registry filter would skip
test_exclusions:
  - <test_id>: "<written justification>"   # required: every exclusion has a reason
```

The verifier consults `test_exclusions` last (after applying the methodology + scope filter) and surfaces each exclusion with its justification in the phase's `VERIFICATION.md` for the audit trail.

## How to interpret a phase's `CONTEXT.md`

Two sections matter most for verification:

1. **Locked decisions** — establishes the empirical commitments that all plans in the phase must respect. The verifier checks consistency.
2. **Tests this phase must pass** — explicit list of test IDs. Joined with the registry-filter result; the union is the phase's gate set.

## Plan XML extensions

gsd-econ extends GSD's task XML with two domain-specific blocks:

- `<empirics>` — model, FE, controls, cluster level, SE method, sample restrictions, weights
- `<gates>` — list of `<test_id>` that must pass after execution

Plans that omit either block are valid GSD plans but won't gate properly. The `identification-checker` flags missing `<empirics>` as MAJOR; missing `<gates>` as MINOR (verifier will load gates from registry by methodology if not provided in plan).

## Where things go in `.planning/`

```
.planning/
├── PROJECT.md
├── REQUIREMENTS.md
├── METHODOLOGY.md            ← this drives test loading
├── ROADMAP.md
├── STATE.md                  ← verifier writes test history
├── research/
│   └── literature-scout.md   ← econ-researcher writes here
├── phases/
│   └── XX-<slug>/
│       ├── CONTEXT.md        ← /gsd-discuss-identification output
│       ├── RESEARCH.md       ← /gsd-plan-empirics researcher output
│       ├── 01-PLAN.md ...    ← XML task plans
│       ├── PLAN-CHECK.md     ← identification-checker verdict
│       ├── XX-SUMMARY.md     ← post-execution
│       ├── VERIFICATION.md   ← verifier writes test verdicts here
│       └── FIX-NN-PLAN.md    ← (only if blockers failed)
├── test-runs/                ← /gsd-test-paper outputs
├── referee-sim/              ← /gsd-referee-sim outputs
└── submission/               ← /gsd-submit-paper bundle staging
```

Verifier and plan_check agents have read access to all of this and write access to `VERIFICATION.md`, `FIX-NN-PLAN.md`, `STATE.md`, and `test-runs/`.
