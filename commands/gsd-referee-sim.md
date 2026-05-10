---
description: "Adversarial peer review. Spawns K parallel referee-sim runs and aggregates the result. Default mode (no --heavy): K heavy-tier referees with varied framings, aggregated by simple cross-tabulation. --heavy mode: K light-tier referees + 1 heavy-tier deliberator that synthesizes their reports. K defaults to 2; the runs span specialist/cross-field/methods-skeptic/etc. framings."
allowed-tools: Read, Write, Bash, Glob, Grep, Task
arguments: "[--n-referees K] [--heavy] [--severity major|all] [--journal <target>]"
---

# /gsd-referee-sim

This command produces an adversarial peer review of the current manuscript by running K parallel referee-sims and aggregating the results. It is the home for `judgment`-clarity RUT tests, which the verifier intentionally defers because they require domain reasoning rather than pattern matching.

## When to use

- Before submission (mandatory; called by `/gsd-submit-paper`)
- After major revisions, before sharing with coauthors
- After completing the main results phase, as a sanity check before robustness
- Periodically during writing, to surface weaknesses while they're still cheap to fix

## Modes

### Default mode (no `--heavy`)

K heavy-tier `referee-sim` runs with varied framings. Each is a competent specialist; aggregation is by cross-tabulating concerns (convergent vs divergent) and surfacing both for user triage. Cost scales linearly with K on the heavy tier.

When to use: budget allows expensive runs; you want each individual referee report to be as deep as possible; you'll triage the union of concerns yourself.

### Heavy-skill mode (`--heavy`)

K light-tier `referee-sim-light` runs spawned in parallel, each with a distinct framing. After all K complete, a single heavy-tier `referee-deliberator` reads all K reports and synthesizes them into one aggregated report. Cost is roughly K × (light cost) + 1 × (heavy cost).

When to use: K=8+ runs are desirable for diversity; light-tier per-referee cost is much cheaper than heavy-tier; you want a deliberation step that reasons across the parallel reports rather than just cross-tabulating them.

The architectural pattern (K cheap parallel + 1 strong deliberator) is inspired by HeavySkill (https://github.com/wjn1996/HeavySkill, Apache-2.0). The integration with the gsd-econ workflow is original; the technique inheritance is acknowledged here and in the `referee-deliberator` agent file.

## Process

### Step 1 — Resolve K and mode

Parse `--n-referees K` (default: 2) and `--heavy` (default: off).

Validate:
- K ≥ 1
- If `--heavy` and K < 4: warn that heavy mode's value comes from K diversity; K=2 with heavy is more expensive than helpful. Proceed anyway if user confirms.
- If not `--heavy` and K ≥ 8: warn about cost; K heavy referees gets expensive fast. Proceed if user confirms.

Recommended values:
- Default mode: K = 2 (specialist + cross-field; the prior behavior). K = 3 adds methods-skeptic. K > 4 in default mode is rarely worth the cost.
- Heavy mode: K = 6–10 typical; K = 8 is the HeavySkill paper's default. K diversity is the value driver here.

### Step 2 — Inventory

Read:
- The full manuscript draft
- `.planning/METHODOLOGY.md`
- `.planning/PROJECT.md`
- `.planning/research/literature-scout.md`
- All `.planning/phases/*/VERIFICATION.md`

Identify the target journal. Default to `METHODOLOGY.target_journal`; override with `--journal`.

Set up output directory:
- `.planning/referee-sim/<ISO>/`
- `.planning/referee-sim/<ISO>/parallel/` for individual referee reports

### Step 3 — Load judgment tests

From the merged RUT + gsd-econ registry, load all tests where:
- `clarity: judgment`
- `methodology` ∈ project methodology tags ∪ `{universal}`

Default: include all severities. With `--severity major`, restrict to `blocker`-severity judgment tests.

### Step 4 — Assign framings

Generate K distinct framings to maximize diversity. For K = 2 you get the prior behavior (specialist + cross-field). For larger K, draw from this menu in order:

1. **Specialist** — deep methodological knowledge of the paper's primary methodology
2. **Cross-field** — econ generalist, not deep in this subfield
3. **Methods-skeptic** — focuses identification and inference
4. **Theory-leaning** — focuses model-mapping, structural claims, mechanism plausibility
5. **Applied-leaning** — focuses external validity, policy relevance, generalizability
6. **Junior-skeptic** — recently-trained referee, knows the latest methodological literature
7. **Senior-applied** — experienced referee, focuses on whether the paper actually moves the field
8. **Cross-disciplinary** — adjacent field (e.g., labor paper reviewed by political-economy researcher)

For K beyond 8, repeat from the start with a perturbed prompt (different journal calibration, different temperament).

### Step 5 — Spawn referees in parallel

#### Default mode

Spawn K instances of the `referee-sim` agent (heavy tier), each with its assigned framing. Each writes to `.planning/referee-sim/<ISO>/parallel/report-<i>.md`.

Wait for all K to complete.

#### Heavy mode

Spawn K instances of the `referee-sim-light` agent (light tier), each with its assigned framing and run number. Each writes to `.planning/referee-sim/<ISO>/parallel/report-<i>.md`.

Wait for all K to complete.

### Step 6 — Aggregate

#### Default mode

Cross-tabulate concerns across the K reports. Build `.planning/referee-sim/<ISO>/summary.md`:

```markdown
# Referee simulation — <ISO>
Mode: default (K=<count> heavy referees)
Journal target: <target>
Severity filter: <major|all>

## Per-referee summary
| Run | Framing | Recommendation | Major concerns |
|-----|---------|----------------|----------------|
| 1 | specialist | <verdict> | <count> |
| 2 | cross-field | <verdict> | <count> |
| ... | ... | ... | ... |

## Convergent concerns (raised by ≥ ⌈K/2⌉ referees)
- <concern>: raised by referees <list>

## Divergent concerns
For each referee i:
- Run <i> (<framing>) only:
  - <concern>
  - ...

## Test verdicts (judgment-clarity)
| Test ID | Verdicts across K runs | Aggregated |
|---------|------------------------|------------|
| ... | <list e.g. "PASS, FAIL, PASS"> | <reasoning-based aggregate> |
```

#### Heavy mode

Spawn the `referee-deliberator` agent (heavy tier). Provide:
- The manuscript path
- All K parallel report paths
- `METHODOLOGY.md`, `PROJECT.md`
- Aggregation context (K, framings used)

The deliberator produces `.planning/referee-sim/<ISO>/deliberated-report.md`. This replaces the cross-tabulated summary as the primary aggregation artifact.

Optionally, also generate a thin `summary.md` with the per-referee table for quick scanning.

### Step 7 — Triage with user

Present findings in priority order. The user picks for each concern:

- **Address now** — creates a fix plan; user runs `/gsd-discuss-identification` or similar
- **Acknowledge** — log to STATE.md as known weakness
- **Reject** — user explicitly disagrees with the simulated referee; log with reasoning

In heavy mode, the deliberator's classification (substantive vs surface vs wrong) provides a recommended triage, but the user owns the final call.

Save the triage to `.planning/referee-sim/<ISO>/triage.md`.

### Step 8 — Hand off

If addressed concerns produce new fix plans, point user to `/gsd-execute-phase` for the affected phase.

If all concerns triaged, the next step is `/gsd-submit-paper` (if pre-submission) or `/gsd-rr-response` (if mid-revision).

Commit. Final message includes mode, K, recommendation distribution.

## Constraints

- **The referee-sim is not a replacement for human review.** It is an adversarial scaffold. Coauthors and trusted colleagues should still read the paper.
- **Do not soften the simulated referees.** A polite referee is a useless referee. Each framing should produce honestly framed concerns.
- **Do not act on referee-sim outputs unilaterally.** The user triages.
- **Spawn K referees genuinely in parallel.** Sequential spawning defeats the purpose of the diversity stage.
- **Do not let referees see each other's outputs.** Independence is the property the parallel stage relies on.
- **In heavy mode, the deliberator must verify singleton substantive concerns against the manuscript.** Light-tier referees hallucinate; the deliberator's job includes catching this.
- **Defer to human judgment.** The aggregated recommendation is advisory. Reasonable disagreement between user and deliberator is a legitimate outcome.

## Output

- `.planning/referee-sim/<ISO>/parallel/report-<1..K>.md` — individual referee reports
- `.planning/referee-sim/<ISO>/summary.md` — cross-tabulated summary (always)
- `.planning/referee-sim/<ISO>/deliberated-report.md` — synthesized review (heavy mode only)
- `.planning/referee-sim/<ISO>/triage.md` — user triage decisions
- Updated STATE.md with known-weakness log
- If concerns are addressed: fix plans under the relevant phase

## Cost guidance

Approximate token cost relative to a single heavy-referee call:

| Mode | K | Cost (relative) | Diversity |
|------|---|-----------------|-----------|
| default | 1 | 1× | none (one referee) |
| default | 2 | 2× | low (two specialists) |
| default | 4 | 4× | moderate |
| default | 8 | 8× | moderate (diminishing — heavy models converge on similar answers) |
| heavy | 4 | ~1.3× | low (K too small for heavy mode's value) |
| heavy | 8 | ~1.5× | high — recommended heavy-mode setting |
| heavy | 16 | ~2.1× | very high — diminishing returns past here |

The exact ratios depend on your `model_tiers` config. The numbers above assume light ≈ Haiku, heavy ≈ Opus, ~15× cost ratio. With light=heavy=Opus, `--heavy` mode reduces to "K+1 heavy calls" and is strictly more expensive than default mode — don't run it that way.

If `--heavy` is passed and the user's `model_tiers.light` equals `model_tiers.heavy`, warn the user and recommend either configuring a cheaper light model or running in default mode.
