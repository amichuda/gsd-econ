---
description: "Final pre-submission audit. Spawns five polish agents in parallel (numbers, cross-refs, bibliography, consistency, claims), aggregates findings, presents triaged options, generates fix plans for accepted findings, applies up to 2 rounds. Auto-invoked by /gsd-submit-paper."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: "[--round <N>] [--skip <agent_name>]"
---

# /gsd-polish-pass

The final-pass audit before submission. Five polish agents run in parallel against the manuscript, each with a narrow mandate. Their findings are aggregated, presented for user triage, and turned into fix plans.

This is the agent fan-out described in [`docs/architecture.md`](../docs/architecture.md): RUT tests gate during phases (per-phase verification); polish-* agents gate at the end (cross-cutting consistency checks the per-phase tests can't see).

## When to use

- **Before `/gsd-submit-paper`** — required step (and auto-invoked).
- **Before sending a draft to coauthors** — useful for catching the consistency drift that builds up over a writing month.
- **After a revise-and-resubmit round** — re-run before resubmitting, since changes during revision are exactly the time when consistency drifts.

## Process

### Step 1 — Pre-flight

Verify the manuscript exists and compiles:
- Find the main manuscript file (`paper/main.tex` or as discovered).
- Run `pdflatex` (and `bibtex` if needed) to confirm clean compile. Save the log.
- If compilation fails, abort with a clear message — polish agents need a buildable paper.

Set up the output directory:
- `.planning/polish/<ISO-timestamp>/` for this round's reports

### Step 2 — Fan out the polish agents

Spawn all five in parallel:

- `polish-numbers` — quantitative claims trace to source
- `polish-cross-refs` — `\ref` and `\cite` resolve, no orphans
- `polish-citations` — citations match the cited papers' actual content
- `polish-consistency` — cross-section terminology, sample, and claim consistency
- `polish-claims` — real-world facts are accurate and current

Each agent writes to `.planning/polish/<ISO>/polish-<name>-report.md`.

If `--skip <agent_name>` was passed, omit that agent (e.g., `--skip polish-claims` if the user has already triaged claims this round).

Wait for all to complete. Some are slow (`polish-citations` does network lookups, `polish-consistency` reads the whole manuscript carefully) — budget for it.

### Step 3 — Aggregate findings

Read each report. Build a unified findings table:

```
Severity   | Agent              | Location              | One-line description
-----------+--------------------+-----------------------+-------------------------------
BLOCKER    | polish-numbers     | abstract:line 12      | 12.4% drift from Table 3 (12.6%)
BLOCKER    | polish-cross-refs  | §4:line 218           | \ref{tab:hetero} undefined
WARNING    | polish-consistency | §2 vs §4              | "rural" vs "non-urban" sample term
INFO       | polish-claims      | §2.1                  | FCC broadband definition stale
...
```

Deduplicate where two agents report the same underlying issue (e.g., polish-numbers and polish-consistency both flagging the same percentage drift).

### Step 4 — Present to user, triage

Present findings in priority order: BLOCKER first, then WARNING, then INFO. For each, three options:

- **Address** — generate a fix plan (Step 5)
- **Acknowledge** — log to STATE.md as known-but-won't-fix-this-round
- **Dispute** — the user judges the finding is wrong; log with their reasoning

Don't overwhelm. If there are many findings, group by agent and present in batches. Let the user say "address all blockers, acknowledge warnings" as a single decision when reasonable.

### Step 5 — Generate fix plans for "address" decisions

For each addressed finding, write a fix plan in standard XML format:

```xml
<task type="polish-fix">
  <name><agent>: <one-line summary></name>
  <files>paper/main.tex, paper/sections/...</files>
  <action>
    <agent> reported: <verbatim finding>

    Fix: <specific edit to make>

    Verify: <how to confirm fix is right — re-run polish agent, re-compile, etc.>
  </action>
  <verify>
    Re-run /gsd-polish-pass --round &lt;N+1&gt;.
    The previously-failing finding should not reappear.
  </verify>
  <agent><agent_name></agent>
  <done>Finding resolved; downstream agents don't re-flag.</done>
</task>
```

Save fix plans to `.planning/polish/<ISO>/FIX-NN-PLAN.md`. The user runs `/gsd-execute-phase polish` (or applies edits manually) to apply them.

### Step 6 — Round management

Track which round this is via the `--round` argument or by counting prior `polish/` directories. Default cap: 2 rounds.

If round 1 found and addressed N findings, round 2 should find < N (most fixes resolve specific items). If round 2 still finds blockers, surface this clearly and ask the user how to proceed:

- Run round 3 (override the cap)
- Acknowledge remaining blockers as known weaknesses
- Pause and address manually

### Step 7 — Final report

Write `.planning/polish/<ISO>/SUMMARY.md`:

```markdown
# Polish pass — <ISO> — round <N>

## Findings by severity
- BLOCKER: <count> (<addressed> addressed, <ack> acknowledged, <disp> disputed)
- WARNING: ...
- INFO: ...

## Findings by agent
- polish-numbers: <count> findings, <count> blockers
- polish-cross-refs: ...
- polish-citations: ...
- polish-consistency: ...
- polish-claims: ...

## Fix plans generated
- FIX-01-PLAN.md: <one-line>
- FIX-02-PLAN.md: ...

## Acknowledged (logged to STATE.md)
- <finding>: <user reasoning>

## Disputed
- <finding>: <user reasoning>

## Verdict
<CLEAN | NEEDS-REVISION | REQUIRES-USER-ACTION>

## Next step
- If CLEAN: ready for /gsd-submit-paper.
- If NEEDS-REVISION: apply fix plans, then /gsd-polish-pass --round <N+1>.
- If REQUIRES-USER-ACTION: <specific guidance>
```

Update `.planning/STATE.md` with a polish-pass event.

Commit: `chore(polish): round <N> — <count> blockers addressed, <count> ack'd, <count> open`.

## Constraints

- **Do not modify the manuscript.** The orchestrator coordinates findings; fix plans (which the user accepts) drive the modifications via the standard execute-phase machinery. Polish agents themselves are read-only.
- **Do not auto-execute fix plans.** User triage is mandatory. This is the same human-in-the-loop discipline as `/gsd-verify-replication` for heuristic blockers.
- **Cap at 2 rounds by default.** Polish loops can become endless if the user keeps disputing fixes; the cap forces a decision point.
- **Run all five agents** unless `--skip` is passed. Don't decide unilaterally that one isn't relevant. The user can skip if they have specific reason.
- **Wait for parallel completion.** Don't aggregate partial results — the agents catch different bugs and a partial run might mask issues.
- **Distinguish from RUT verification.** Polish-* agents are not RUT tests. They don't gate phases; they don't appear in `tests/registry.yaml`. They're a final-pass audit.

## Output

- `.planning/polish/<ISO>/polish-numbers-report.md`
- `.planning/polish/<ISO>/polish-cross-refs-report.md`
- `.planning/polish/<ISO>/polish-citations-report.md`
- `.planning/polish/<ISO>/polish-consistency-report.md`
- `.planning/polish/<ISO>/polish-claims-report.md`
- `.planning/polish/<ISO>/SUMMARY.md`
- `.planning/polish/<ISO>/FIX-*-PLAN.md` (one per addressed finding)
- Updated STATE.md
- Clean commit
- Verdict communicated to user
