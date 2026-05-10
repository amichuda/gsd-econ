---
description: "Run the full RUT test battery for the paper's methodology, outside the phase verification loop. Use before sending drafts to coauthors or as a pre-flight check."
allowed-tools: Read, Write, Bash, Glob, Grep, Task
arguments: "[--methodology <tag>] [--severity <level>] [--scope <scope>] [--paper-dir <path>]"
---

# /gsd-test-paper

Standalone test runner. Useful when you want to know the current state of the paper without going through a phase cycle.

## Process

### Step 1 — Determine scope

Default scope:
- methodology: from `.planning/METHODOLOGY.md`
- severity: all
- scope: paper

Override with flags:
- `--methodology did,iv` — restrict to specific tags
- `--severity blocker` — only run blockers
- `--scope paper,replication` — multi-scope
- `--paper-dir <path>` — point at a different paper directory (for testing custom tests)

### Step 2 — Build the test set

Load both registries (RUT + gsd-econ) and filter:

```
tests = filter(
  methodology ∈ requested_methodologies ∪ {"universal"}
  ∧ severity ∈ requested_severities
  ∧ scope ⊆ requested_scopes
)
```

If the test set is empty, tell the user and exit with explanation (likely a typo in flags).

### Step 3 — Run

For each test, spawn `replication-verifier` agent with:
- Test markdown
- Paper directory contents
- Methodology context

Collect verdicts.

### Step 4 — Report

Output a summary in three formats simultaneously:

**Console summary** (for the chat):

```
gsd-test-paper run — <ISO timestamp>
Scope: methodology=<...> severity=<...>

Tests run: NN
Pass: NN
Fail: NN
Needs-evidence: NN
Deferred (judgment): NN

CRITICAL FAILURES:
- <test_id>: <one-line reason>
- ...

Full report: .planning/test-runs/<ISO>-test-paper.md
```

**Detailed markdown report** to `.planning/test-runs/<ISO>-test-paper.md`:
- Per-test: id, severity, clarity, verdict, evidence, reasoning
- Aggregate by methodology

**JSON-lines log** to `.planning/test-runs/<ISO>-test-paper.jsonl` for downstream tooling:
```json
{"test_id": "...", "verdict": "PASS", "severity": "blocker", "clarity": "deterministic", "evidence": [...], "timestamp": "..."}
```

### Step 5 — Recommendations

Based on verdicts, suggest the user's next move:

- All blockers PASS, deferred judgment tests pending → "ready to run /gsd-referee-sim before submission"
- Some blockers FAIL → "address before phase progression. Failed tests are listed above. To generate fix plans, run /gsd-verify-replication <phase>."
- Heuristic blockers in PROVISIONAL → "review and accept/reject in /gsd-verify-replication for the relevant phase"
- All clear except info — "draft is in good shape; consider /gsd-referee-sim"

## When to use this vs /gsd-verify-replication

- `/gsd-verify-replication <N>` — phase-scoped, tied to the phase work, generates fix plans, blocks phase progression. Use within the normal workflow.
- `/gsd-test-paper` — paper-scoped, no fix plans, no blocking. Use as a status check, before sending to coauthors, before stand-up meetings, before deciding whether to start a new phase.

You can also run this from the CLI, outside an LLM session:
```bash
bash vendor/gsd-econ/scripts/run-tests.sh
```

The script invokes the same logic via Claude Code in non-interactive mode.

## Constraints

- **Do not produce fix plans.** This is a status check, not a workflow step.
- **Do not modify the paper.** Read-only over the codebase. The only writes are to `.planning/test-runs/`.
- **Do not silently skip excluded tests.** Even tests in `METHODOLOGY.test_exclusions` are surfaced in the report (as "EXCLUDED — see METHODOLOGY.md") for transparency.

## Output

- `.planning/test-runs/<ISO>-test-paper.md`
- `.planning/test-runs/<ISO>-test-paper.jsonl`
- Console summary
- Suggested next action
