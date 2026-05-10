---
description: Verify a phase by running RUT tests applicable to the methodology + phase scope. Replaces /gsd-verify-work for research. Generates fix plans for blocker failures, surfaces warnings, defers judgment-clarity to referee-sim.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: phase_number [--full] [--test-id <id>]
---

# /gsd-verify-replication

You are verifying that a completed phase passes its required quality gates. This replaces `/gsd-verify-work` for research workflows.

Phase: $ARGUMENTS

## Process

### Step 1 — Determine which tests apply

Load:
- `.planning/METHODOLOGY.md` for methodology tags and any test inclusions/exclusions.
- `.planning/phases/XX-<slug>/CONTEXT.md` for phase-level scope (paper / replication).
- `.planning/phases/XX-<slug>/PLAN-*.md` `<gates>` blocks for plan-declared required tests.

Merge the two test registries:
- `vendor/research-unit-tests/registry.yaml`
- `vendor/gsd-econ/tests/registry.yaml`

Compute the applicable test set:

```
applicable = registry.filter(
    methodology ∈ METHODOLOGY.primary
              ∪ METHODOLOGY.secondary
              ∪ {"universal"}
    ∧ scope    ⊆ phase.scope_set
    ∧ id       ∉ METHODOLOGY.test_exclusions
)
∪
explicit_gates_from_plans
```

If `--test-id <id>` was passed, restrict to that single test (used for re-verification after fix).

If `--full` was passed, ignore the "previously passed" cache and re-run everything.

### Step 2 — Spawn replication-verifier per test

For each applicable test:

1. Read the test markdown file (path from registry).
2. Spawn `replication-verifier` agent with:
   - The test markdown body
   - Phase context (relevant code files, output files, paper draft sections)
   - Methodology declaration
3. The agent collects evidence and returns a verdict object:
   ```
   {
     test_id: <id>,
     verdict: PASS | FAIL | NEEDS-EVIDENCE | DEFERRED,
     evidence: [<paths or excerpts>],
     reasoning: <one paragraph>
   }
   ```

For `clarity: judgment` tests: the verdict is automatically `DEFERRED` with reason "judgment-clarity tests run during /gsd-referee-sim, not at phase verification."

For `clarity: heuristic` blockers: the verdict is `PASS-PROVISIONAL` and surfaced to the user for confirmation. See Step 4.

For `clarity: deterministic`: the agent returns PASS or FAIL based on the criterion.

### Step 3 — Aggregate

Build the phase verdict matrix. Distinguish:
- Hard blockers (deterministic-blocker FAIL or NEEDS-EVIDENCE)
- Provisional blockers (heuristic-blocker awaiting human ack)
- Warnings (warning-severity, any clarity)
- Info (info-severity)
- Deferred (judgment)

### Step 4 — Human-in-the-loop for heuristic blockers

For each heuristic blocker:

```
TEST: <id>
SEVERITY: blocker
CLARITY: heuristic

Evidence:
<bullet list of evidence the agent found>

Verifier reasoning:
<one paragraph>

Verdict: ACCEPT / REJECT / NEEDS-MORE-EVIDENCE
```

If user ACCEPTS: log the evidence + acceptance to `STATE.md` with timestamp, mark test PASS.
If user REJECTS: treat as FAIL, generate a fix plan (Step 5).
If user requests MORE-EVIDENCE: spawn the verifier again with explicit instructions about what evidence is missing.

### Step 5 — Fix plans for failures

For every hard-blocker FAIL or rejected heuristic-blocker, generate a fix plan in GSD's standard XML format, with the gsd-econ extension:

```xml
<task type="fix">
  <name><short>: address <test_id></name>
  <files><inferred from evidence></files>
  <action>
    Test <test_id> failed. <reasoning from verifier>.

    To fix: <specific actions>.

    Reference the test criterion exactly:
    > <quote from test markdown>
  </action>
  <verify>
    Re-run /gsd-verify-replication $ARGUMENTS --test-id <id>.
    Verdict must be PASS.
  </verify>
  <test_id><id></test_id>
  <done>Test <id> passes on re-verify.</done>
</task>
```

Save fix plans to `.planning/phases/XX-<slug>/FIX-NN-PLAN.md`.

### Step 6 — Write VERIFICATION.md

Save to `.planning/phases/XX-<slug>/VERIFICATION.md`. Schema:

```markdown
# Phase $ARGUMENTS — Verification

Run: <ISO timestamp>
Methodology context: <primary/secondary tags>

## Test Results

### Blockers
- [PASS|FAIL|DEFERRED] <test_id> (<clarity>) — <one-line summary>
  ...

### Warnings
- ...

### Info
- ...

### Deferred (judgment)
- <test_id> — will run at /gsd-referee-sim

## Evidence
- <test_id> → <path to evidence or excerpt>
- ...

## Phase verdict
PASS | BLOCKED (<n> blocker fails) | PROVISIONAL (awaiting human ack on <n>)

## Next action
- If PASS: phase $ARGUMENTS complete. Proceed to /gsd-discuss-identification <next>.
- If BLOCKED: run /gsd-execute-phase $ARGUMENTS to apply fix plans, then /gsd-verify-replication $ARGUMENTS again.
```

### Step 7 — Update STATE.md

Append a verification event to STATE.md's history. Schema:

```markdown
## <ISO timestamp> — Phase $ARGUMENTS verification
Verdict: <PASS|BLOCKED|PROVISIONAL>
Tests run: <count>
Blockers: <count_pass>/<count_fail>
Notable: <any judgment-deferred or heuristic that needed human ack>
```

This accumulates over the project. By submission, STATE.md has the full diagnostic trail.

### Step 8 — Hand-off

If PASS: tell the user phase verification clean, suggest next phase.
If BLOCKED: tell the user fix plans are ready at `phases/XX-<slug>/FIX-*-PLAN.md`, and to run `/gsd-execute-phase $ARGUMENTS` to apply them.

Commit `git add .planning/ && git commit -m "verify(phase-$ARGUMENTS): <PASS|BLOCKED with N fixes>"`.

## Constraints

- **Do not invent test results.** If the verifier returns NEEDS-EVIDENCE, surface it as such; don't paper over with a guess.
- **Do not auto-pass heuristic blockers.** Human-in-the-loop is mandatory for these. Never silently log as PASS without explicit acceptance.
- **Do not run judgment-clarity tests here.** Defer to `/gsd-referee-sim`.
- **Always read the test markdown body fully** before evaluating. The verifier reads "How to check" and "Pass condition" — do not interpret based on the title or registry entry alone.
- **Do not skip tests for convenience.** If the user wants to skip a specific test, they must add its id to `METHODOLOGY.md.test_exclusions` with a written justification. The verifier reads this and surfaces the exclusion in `VERIFICATION.md` for the audit trail.

## Output

- `.planning/phases/XX-<slug>/VERIFICATION.md` ✓
- `.planning/phases/XX-<slug>/FIX-*-PLAN.md` (only if blockers failed) ✓
- Updated `.planning/STATE.md` ✓
- Clean commit
- Phase verdict communicated explicitly
