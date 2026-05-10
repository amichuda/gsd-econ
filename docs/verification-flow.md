# Verification flow

This document specifies how RUT test results map to GSD's verification gate behavior. It's the core of the integration — get this right and the rest follows.

## The four-by-three matrix

Every RUT test has a **severity** (`blocker`, `warning`, `info`) and a **clarity** (`deterministic`, `heuristic`, `judgment`). The combination determines what the verifier does.

|                  | **Deterministic**            | **Heuristic**                   | **Judgment**                        |
|------------------|------------------------------|----------------------------------|-------------------------------------|
| **Blocker**      | Hard gate. Auto-run. Fix loop on fail. | Hard gate. Run with evidence. Human acks before advance. | Never auto-gated. Deferred to `/gsd-referee-sim`. |
| **Warning**      | Auto-run. Surfaces in `VERIFICATION.md`. Does not block. | Run with evidence. Surfaces in `VERIFICATION.md`. | Deferred to referee-sim. Surfaces as suggestion. |
| **Info**         | Auto-run. Logged in `STATE.md`. | Logged with evidence. | Deferred. |

Three rules to remember:

1. **Judgment-clarity tests never auto-gate.** "Is the contribution interesting?" is not a question the verifier should answer with a pass/fail. These tests run only during `/gsd-referee-sim`, which produces an adversarial report you read before submission.
2. **Heuristic-clarity blockers require human acknowledgment.** "Pre-trends look reasonable" is heuristic — the verifier extracts the relevant figure and prose, presents them, and waits for you to confirm. This is intentional friction.
3. **Deterministic-clarity blockers loop automatically.** "Tables report N" is yes/no. If the verifier finds a table without N, it generates a fix plan and re-runs the executor.

## The fix-plan loop

GSD already has this for software:

```
verify-work fails
   │
   ▼
GSD generates fix plans
   │
   ▼
execute-phase runs them
   │
   ▼
verify-work re-runs
   │
   ▼
[loop until pass or human intervention]
```

`gsd-econ` reuses this exact machinery. When `replication-verifier` finds a blocker fail, it writes a fix plan in the same XML format GSD's planner uses:

```xml
<task type="fix">
  <name>Add N row to Table 3</name>
  <files>tables/main_results.tex, code/02_make_tables.R</files>
  <action>
    Test universal-tables-have-n-obs failed for Table 3. Add a row reporting
    N below the last coefficient row. Use the same N as the underlying
    regression in code/02_make_tables.R, line 47.
  </action>
  <verify>grep -c "N" tables/main_results.tex returns >= 1 per table</verify>
  <test_id>universal-tables-have-n-obs</test_id>
  <done>All 4 main tables report N. Test passes on re-verify.</done>
</task>
```

Note the new `<test_id>` field — gsd-econ extends GSD's plan schema with this so `STATE.md` accumulates a per-test pass history. By submission time you have a verifiable trail of identification diagnostics, which is gold for R&R.

## Tag-based test loading

Every phase has a methodology context. The verifier loads tests by intersection:

```
applicable_tests = registry.filter(
    methodology ∈ METHODOLOGY.md.primary ∪ METHODOLOGY.md.secondary ∪ {"universal"}
    ∧ scope     ⊇ phase.scope
)
```

Concretely, if `METHODOLOGY.md` declares:

```yaml
primary: did
secondary: [ols]
scope: paper
```

…and the current phase is `03-identification-diagnostics` with scope `paper`, the verifier loads:

- All `did` blockers and warnings
- All `ols` blockers and warnings
- All `universal` blockers and warnings
- Filtered to `scope: paper`

Phases can override scope. The replication-package phase sets `scope: replication`, which loads `universal-replication-reproduces-results` (RUT) plus any replication-specific tests from gsd-econ.

## Human-in-the-loop for heuristic tests

Heuristic blockers should not loop without you in the seat. The verifier presents:

```
TEST: did-parallel-trends-plot
SEVERITY: blocker
CLARITY: heuristic

Evidence found:
  - Figure: tables/figures/event_study.pdf
  - Pre-period coefficients: -0.012, 0.008, -0.003 (all p > 0.30)
  - F-test of joint pre-trend = 0: p = 0.62

Verdict: ACCEPT / REJECT / NEEDS-MORE-EVIDENCE?
```

Your call. If you reject, the verifier writes a fix plan that asks the executor to investigate further (e.g., add more pre-periods, switch estimator). If you accept, it logs the evidence to `STATE.md` and advances.

This is how `/gsd-verify-work` already behaves for UAT — we're using the same affordance for a different domain.

## What the verifier *does not* do

- It does not run your `make` or render your Quarto. Those are GSD executor responsibilities, scheduled by the plan.
- It does not invent test results. If a test references evidence that doesn't exist (e.g., `did-parallel-trends-plot` and there's no event-study figure), the verdict is `NEEDS-EVIDENCE` and a fix plan is written to produce it.
- It does not silently skip tests. Every applicable test is either run or explicitly deferred (judgment-clarity → referee-sim). The phase `VERIFICATION.md` lists everything.

## Format of `VERIFICATION.md`

Each phase produces one. Schema:

```markdown
# Phase 3 — Identification Diagnostics

## Test Results

### Blockers
- [PASS] universal-tables-have-n-obs (deterministic)
- [PASS] did-parallel-trends-plot (heuristic, accepted by user 2026-04-12)
- [FAIL] did-staggered-heterogeneous-effects (deterministic)
  → Fix plan: phases/03-identification-diagnostics/02-PLAN.md
- [DEFERRED] universal-contribution-is-new (judgment → referee-sim)

### Warnings
- [PASS] universal-clustered-ses-justified (deterministic)
- [FAIL] universal-multiple-testing-corrected (heuristic)
  → Recorded; not blocking. Address in robustness phase.

### Info
- [PASS] universal-sample-restrictions-stated (deterministic)

## Phase verdict
BLOCKED — 1 blocker fail. See fix plan above.
```

This file is committed to git. It is the audit trail.

## Re-verification after fix

When a fix plan completes, the verifier re-runs *only the previously failed tests* by default. You can force a full re-run with `/gsd-verify-replication --full` if you suspect changes affected other gates.

## Submission gate

`/gsd-submit-paper` runs a full verification across all phases (every `VERIFICATION.md` must show no open blockers) plus the judgment-clarity tests via `referee-sim`. If anything is open, it refuses to package the submission. This is the last line of defense against shipping a paper with an unaddressed parallel-trends violation.
