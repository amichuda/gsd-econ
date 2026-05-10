---
description: Identification-shaped discussion before planning a phase. Asks methodology-specific gray-area questions (parallel trends for DiD, exclusion restrictions for IV, etc.) and writes CONTEXT.md with locked decisions for the planner.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: phase_number
---

# /gsd-discuss-identification

You are running the discussion phase for an empirical research project. This replaces `/gsd-discuss-phase` when the phase involves identification choices.

Phase number: $ARGUMENTS

## Process

### Step 1 — Read context

Load:

- `.planning/METHODOLOGY.md` to get methodology tags and locked decisions.
- `.planning/REQUIREMENTS.md` to see which decisions are OPEN vs LOCKED.
- `.planning/ROADMAP.md` to find phase $ARGUMENTS and read its description.
- `.planning/research/literature-scout.md` for relevant prior work.
- `.planning/STATE.md` for any decisions logged in earlier phases.

### Step 2 — Identify the gray areas

Based on the phase description and methodology tag, generate a checklist of identification-specific questions. Use this routing:

**If `methodology.primary` is `did`:**
- Parallel trends: how many pre-periods, what test, what's the placebo
- Treatment timing: simultaneous vs staggered; if staggered, which estimator (Callaway-Sant'Anna, Sun-Abraham, BJS, de Chaisemartin–D'Haultfœuille)
- Treatment intensity: binary vs dose; if dose, what functional form
- Control group definition: never-treated vs not-yet-treated vs both
- SE structure: cluster level (treatment unit, geography, both via two-way)
- Spillovers: assumed away or modeled; if modeled, how

**If `methodology.primary` is `iv`:**
- Instrument source and variation
- Exclusion restriction: explicit prose argument, plus what evidence supports it
- Relevance: expected first-stage F (rule-of-thumb 10+, Lee et al. 2022 thresholds)
- Monotonicity (for LATE interpretation)
- Compliance subgroup: characterization of compliers
- Multiple instruments: just-identified or over-identified; if over, plan for over-id test
- SE structure as above

**If `methodology.primary` is `rdd`:**
- Sharp vs fuzzy
- Running variable and cutoff
- Bandwidth strategy: optimal-MSE (Calonico-Cattaneo-Titiunik), cross-validation, fixed
- Polynomial order (default linear or quadratic; never higher unless justified)
- Manipulation tests (McCrary, Cattaneo-Jansson-Ma)
- Covariate balance at the cutoff
- Donut radius if applicable

**If `methodology.primary` is `experiment_field`:**
- Randomization unit and stratification
- Power calculation: minimum detectable effect, assumed ICC, attrition rate
- Compliance: ITT vs LATE focus
- Spillovers: how excluded or measured
- Pre-analysis plan: registered? hash committed?
- Multiple outcomes: family structure, FWER vs FDR

**If `methodology.primary` is `ols` (descriptive or selection-on-observables):**
- Why OLS is the right tool here (and not a quasi-experimental design)
- Control set: which controls, why these, expected omitted-variable bias direction
- Functional form decisions
- SE structure

For phases that aren't identification-related (e.g., data cleaning, tables-figures pipeline), fall back to GSD's generic gray-area questions.

### Step 3 — Run the interview

Ask one question per turn. After each answer:

1. Restate what you heard.
2. If the user's answer raises a follow-up (e.g., "I'm using staggered DiD" → "which estimator?"), ask it next.
3. If the user is uncertain, suggest options based on the literature scout and current best practice. Don't choose for them, but reduce decision surface.
4. Tag every concrete decision the user makes with `[LOCKED-IN-PHASE-N]`.

### Step 4 — Write CONTEXT.md

When the user has worked through the relevant questions, write `.planning/phases/XX-<phase-slug>/CONTEXT.md` (where XX is the zero-padded phase number). Structure:

```markdown
# Phase $ARGUMENTS — Context

## Methodology in scope
- Primary: <tag>
- Secondary: <tags>
- This phase's role in identification: <one sentence>

## Locked decisions
- <decision>: <choice> — <rationale>
- ...

## Open questions (defer or escalate)
- <question>: <reason it's not locked yet, who decides, when>

## Implications for planning
- The planner should produce tasks that: <list>
- The planner should NOT: <list of exclusions>

## Tests this phase must pass
- <test_id> (loaded from registry by methodology + scope intersection)
- ...

## Evidence to produce for verification
- <artifact>: <where it should land>
```

### Step 5 — Update REQUIREMENTS.md

Move decisions from OPEN to LOCKED. Add new requirements that emerged in discussion. Show diffs to user before committing.

### Step 6 — Hand-off

Commit `git add .planning/ && git commit -m "chore(phase-$ARGUMENTS): identification context locked"`.

Tell the user the next step is `/gsd-plan-empirics $ARGUMENTS`.

## Constraints

- **Never let the user skip the parallel-trends question for a DiD phase, the exclusion-restriction question for an IV phase, the manipulation-test question for an RDD phase, or the power calculation for an RCT phase.** These are non-negotiable. If the user says "we'll deal with that later," push back: "It's cheap to lock now and expensive to retrofit. Three options: A, B, or 'investigate further' which becomes a planning task."
- **Do not assume `assumptions` mode.** Even if the GSD config has `discuss_mode: assumptions`, identification phases must use full discussion. Read METHODOLOGY.md to determine if the current phase is identification-related; if so, override.
- **Do not invent decisions on the user's behalf.** Suggest options, but the user owns the call.
- **Surface trade-offs.** When the user picks Calonico-Cattaneo-Titiunik over a fixed bandwidth, tell them what they gain (asymptotic optimality) and what they pay (sensitivity to kernel choice, harder to explain to applied audience).

## Output

By end of this command:

- `.planning/phases/XX-<slug>/CONTEXT.md` ✓
- Updated `.planning/REQUIREMENTS.md` (LOCKED moved appropriately)
- Updated `.planning/STATE.md` (decisions log entry)
- Clean commit
- Explicit pointer to `/gsd-plan-empirics $ARGUMENTS`
