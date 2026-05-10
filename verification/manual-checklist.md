# Manual verification checklist

This checklist covers what the automated suite cannot: the LLM-driven behavior of commands and agents on a realistic project. Run it before tagging a release (or whenever you've made substantive changes to commands/agents).

Estimate: 60–120 minutes for a full pass.

## Prerequisites

- A working OpenCode or Claude Code install
- API access (Anthropic API key or local model setup)
- An empty directory to use as the test project

## Setup

```bash
mkdir checklist-test && cd checklist-test
git init
npx get-shit-done-cc@latest --opencode --local --minimal
git submodule add https://github.com/<you>/gsd-econ vendor/gsd-econ
git submodule add https://github.com/rdahis/research-unit-tests vendor/research-unit-tests
bash vendor/gsd-econ/scripts/install.sh
```

In your runtime:

```
/gsd-help
```

- [ ] All 10 gsd-econ commands appear alongside the GSD core commands

## Bootstrap (`--new` mode): `/gsd-new-paper --new`

Use this scenario:

> Research question: Does broadband expansion increase rural employment?
> Data: county × year panel, FCC broadband data merged with QCEW employment
> Methodology: staggered DiD using county-level rollout timing
> Target journal: Journal of Labor Economics

Run `/gsd-new-paper --new` and answer the questions.

- [ ] Asks about research question first
- [ ] Asks one or two questions per turn (not an avalanche)
- [ ] Spawns `econ-researcher` agent before the methodology lock-in
- [ ] Literature scout produces `.planning/research/literature-scout.md`
- [ ] Lit scout output mentions at least 5 papers with reasonable citations
- [ ] `.planning/PROJECT.md` populated with research question and target journal
- [ ] `.planning/REQUIREMENTS.md` distinguishes LOCKED vs OPEN
- [ ] `.planning/METHODOLOGY.md` has `primary: did`, plausible `secondary` tags
- [ ] `.planning/ROADMAP.md` lists ~9 phases adapted to the project
- [ ] `.planning/STATE.md` initialized
- [ ] Final commit clean (`git status` shows no uncommitted changes)
- [ ] Explicit pointer to `/gsd-discuss-identification 1`

## Bootstrap (`--adopt` mode): `/gsd-new-paper --adopt`

Use a copy of an existing in-progress paper (your own, with results half-built).

Run `/gsd-new-paper --adopt`.

- [ ] Inventories manuscript and codebase, shows summary before proceeding
- [ ] Identifies primary methodology from package usage (e.g., recognizes `fixest::feols(... | ... | ... ~ ...)` as IV; `did::att_gt` as Callaway-Sant'Anna DiD)
- [ ] Walks through manuscript section by section with you to populate REQUIREMENTS.md
- [ ] Distinguishes LOCKED (already in manuscript) from OPEN (still being revisited)
- [ ] Backfills ROADMAP.md with `[COMPLETED PRE-ADOPTION]` tags rather than fabricating phase histories
- [ ] Writes adoption marker to STATE.md with timestamp
- [ ] Runs baseline `/gsd-test-paper` automatically
- [ ] Surfaces test failures with three options each (address / acknowledge / exclude)
- [ ] Does NOT modify any code or manuscript files (only writes to .planning/)
- [ ] Does NOT auto-generate fix plans for pre-adoption work
- [ ] Hands off to the appropriate next command for the user's current phase

## Bootstrap (auto-detect): `/gsd-new-paper`

Run on a project that has a manuscript draft.

- [ ] Detects --adopt mode automatically based on .tex/.qmd presence and code patterns
- [ ] Tells the user explicitly which mode it chose and why
- [ ] Lets the user override if the auto-detection is wrong

## Discussion: `/gsd-discuss-identification 3`

Skip ahead to phase 3 (identification diagnostics). Run `/gsd-discuss-identification 3`.

- [ ] Asks DiD-specific questions (parallel trends, staggered estimator, cluster level)
- [ ] Does NOT ask IV-specific or RDD-specific questions (would indicate routing failure)
- [ ] Probes when the user is vague (e.g., "I'll use TWFE" should trigger pushback for staggered design)
- [ ] Surfaces the staggered estimator question with concrete options (CSDID, Sun-Abraham, BJS, dCdH)
- [ ] Writes `.planning/phases/03-*/CONTEXT.md` with locked decisions tagged `[LOCKED-IN-PHASE-3]`
- [ ] Updates REQUIREMENTS.md to move decisions LOCKED ← OPEN
- [ ] Updates STATE.md with decisions log entry

## Planning: `/gsd-plan-empirics 3`

Run `/gsd-plan-empirics 3`.

- [ ] Spawns `econ-researcher` for implementation references
- [ ] Plan XML includes `<empirics>` block with cluster level, SE method, sample restrictions
- [ ] Plan XML includes `<gates>` block with relevant test IDs
- [ ] Spawns `identification-checker` agent to review the plan
- [ ] Identification checker flags reasonable concerns (e.g., naive TWFE on staggered would be flagged)
- [ ] If `identification-checker` returns BLOCKER, planner offers to revise or proceed with override

## Verification (key test): `/gsd-verify-replication 3`

After `/gsd-execute-phase 3` (which actually runs analysis — skip if no real data; you can manually create plausible output files for this test).

- [ ] Loads applicable RUT tests from both registries (RUT + gsd-econ)
- [ ] Filters by methodology (`did` + `universal`)
- [ ] For deterministic-blocker tests (e.g., `universal-tables-have-n-obs`), runs automatically
- [ ] For heuristic-blocker tests (e.g., `did-parallel-trends-plot`), pauses for human ack
- [ ] For judgment tests (e.g., `universal-contribution-is-new`), defers to referee-sim
- [ ] Writes `.planning/phases/03-*/VERIFICATION.md` with structured verdict
- [ ] If a blocker fails, generates a fix plan in `.planning/phases/03-*/FIX-NN-PLAN.md`
- [ ] Fix plan XML includes `<test_id>` field linking back to the failed test
- [ ] Updates STATE.md with verification event

## Standalone: `/gsd-test-paper`

Run `/gsd-test-paper --severity blocker` mid-project.

- [ ] Reports test count by status
- [ ] Writes `.planning/test-runs/<ISO>-test-paper.md`
- [ ] Does NOT generate fix plans (this is a status check, not a workflow step)
- [ ] Does NOT modify the paper or any planning docs
- [ ] Surfaces excluded tests with their reasons (if any in METHODOLOGY.md)

## Pre-registration (skip if not RCT)

Run `/gsd-pre-register` on an RCT project (would need a different test scenario).

- [ ] Confirms intent before drafting
- [ ] Asks which registry (AEA / OSF / AsPredicted / EGAP)
- [ ] Generates a PAP with all required sections for the chosen registry
- [ ] Computes SHA-256 hash of the PAP file
- [ ] Records hash in STATE.md
- [ ] Does NOT auto-submit to any registry

## Tables and figures: `/gsd-tables-figures 7`

- [ ] Inventories existing tables and figures
- [ ] Spawns `tables-figures-builder` agent per artifact
- [ ] Output tables compile standalone (`pdflatex` clean)
- [ ] N reported in tables (verifier check)
- [ ] Footnote states cluster level
- [ ] Figures are vector PDFs

## Referee-sim: `/gsd-referee-sim`

Test both modes.

### Default mode, K=2 (the prior behavior)

Run `/gsd-referee-sim` with no flags.

- [ ] Spawns 2 referee-sim runs in parallel: specialist + cross-field
- [ ] Both runs use heavy-tier agent
- [ ] Cross-tabulated summary aggregates concerns into convergent vs divergent
- [ ] Specialist and cross-field reports differ meaningfully
- [ ] User triages each concern (address now / acknowledge / reject)
- [ ] Triage saved to `.planning/referee-sim/<ISO>/triage.md`

### Default mode, K=4

Run `/gsd-referee-sim --n-referees 4`.

- [ ] Spawns 4 referee-sim runs with distinct framings (specialist, cross-field, methods-skeptic, theory-leaning or similar)
- [ ] Per-referee table in summary shows all 4 with their framings
- [ ] Convergent concerns surface as raised by ≥ ⌈K/2⌉ = 2 referees

### Heavy mode, K=8

Run `/gsd-referee-sim --heavy --n-referees 8`.

- [ ] Spawns 8 `referee-sim-light` runs in parallel (light tier)
- [ ] Each has a distinct framing
- [ ] After all 8 complete, spawns 1 `referee-deliberator` (heavy tier)
- [ ] Deliberator reads all 8 reports and writes `deliberated-report.md`
- [ ] Deliberator classifies concerns by robustness (strong/moderate/singleton) and quality (substantive/surface/wrong)
- [ ] Deliberator verifies singleton substantive concerns against the manuscript
- [ ] Aggregate recommendation is reasoned, not majority-vote arithmetic

### Pathological config detection

Configure `model_tiers` such that `light: claude-opus-4-7` and `heavy: claude-opus-4-7` (same model). Run `/gsd-referee-sim --heavy`.

- [ ] Command warns the user that `--heavy` with light tier == heavy tier is wasteful
- [ ] Suggests configuring a cheaper light model or using default mode

### K too low for heavy mode

Run `/gsd-referee-sim --heavy --n-referees 2`.

- [ ] Warns that heavy mode's value comes from K diversity; K=2 with heavy is more expensive than helpful

## Submission: `/gsd-submit-paper`

- [ ] Pre-flight check: all phases have VERIFICATION.md with PASS verdict
- [ ] Refuses to package if any blocker is open
- [ ] Runs full RUT test battery
- [ ] Runs final `/gsd-referee-sim`
- [ ] Builds `submission/` directory with all required components
- [ ] Replication smoke test runs (or surfaces clearly that it would)
- [ ] AI-use disclosure included in `submission/declarations/`
- [ ] Refuses to bundle restricted-use raw data

## Verification of cleanup

- [ ] No orphan files in `.planning/` from interrupted commands
- [ ] All commits are atomic (one task per commit, descriptive messages)
- [ ] STATE.md is consistent with the commit log
- [ ] All test runs are recorded in `.planning/test-runs/`

## Post-checklist actions

If all checked: tag the release, update CHANGELOG, push.

If any failures: open a GitHub issue with the specific behavior, fix, re-run the affected sections.

## Notes from previous runs

(Append observations from each release pass here for institutional memory.)

### Release v0.1.0 — <date>
- <observations>
