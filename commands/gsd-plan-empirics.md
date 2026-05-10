---
description: Plan an empirical phase. Constrains the planner's task schema to econometric work (cluster level, FE structure, SE method, sample restrictions). Spawns identification-checker as plan_check.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: phase_number
---

# /gsd-plan-empirics

You are running the planning phase for empirical work. This replaces `/gsd-plan-phase` for research workflows.

Phase number: $ARGUMENTS

## Process

### Step 1 — Read context

Load:
- `.planning/METHODOLOGY.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/XX-<slug>/CONTEXT.md` (from `/gsd-discuss-identification`)
- `.planning/research/literature-scout.md`
- `.planning/STATE.md`

### Step 2 — Spawn empirics researcher

Spawn the `econ-researcher` agent with this brief:

> Phase: $ARGUMENTS — <phase title from ROADMAP.md>
> Methodology: <from METHODOLOGY.md>
> Locked decisions: <from CONTEXT.md>
>
> Your task: investigate implementation. For the methodology and locked decisions, find:
> 1. The 2–3 most current canonical implementations (Stata/R/Python packages, recent papers' replication archives)
> 2. Common pitfalls specific to these design choices
> 3. Any methodological debates affecting the implementation choice (e.g., for staggered DiD, the post-2021 estimator landscape)
>
> Write findings to `.planning/phases/XX-<slug>/RESEARCH.md`.

Wait for completion. Read the output.

### Step 3 — Generate task plans

Decompose the phase into 2–4 atomic plans. Each plan must use this XML schema (extends GSD's task format with empirics fields):

```xml
<plan id="XX-NN">
  <name><short descriptive name></name>
  <objective><one sentence: what changes in the codebase and what artifact appears></objective>

  <inputs>
    <data>relative paths to input data files</data>
    <code>relative paths to upstream code dependencies</code>
  </inputs>

  <outputs>
    <table>tables/...</table>
    <figure>figures/...</figure>
    <log>logs/...</log>
  </outputs>

  <empirics>
    <model>e.g., TWFE, Callaway-Sant'Anna, IV-2SLS with sandwich SE</model>
    <fe>fixed effects: <list></fe>
    <controls>covariates: <list></controls>
    <cluster_level><level></cluster_level>
    <se_method>e.g., CR1, CR2, Conley(d=200km), bootstrap</se_method>
    <sample_restrictions><list></sample_restrictions>
    <weights><yes/no, type></weights>
  </empirics>

  <tasks>
    <task id="XX-NN-01">
      <name><name></name>
      <files><files to create or modify></files>
      <action><detailed action with specific package calls and parameter values></action>
      <verify><exact command or output that confirms task done></verify>
      <done><pass condition></done>
    </task>
    ...
  </tasks>

  <gates>
    <test_id>universal-tables-have-n-obs</test_id>
    <test_id>did-parallel-trends-plot</test_id>
    <!-- loaded from registry by methodology + phase scope -->
  </gates>
</plan>
```

The `<gates>` section is the contract: this plan is not done until these tests pass.

### Step 4 — Spawn identification-checker

Spawn the `identification-checker` agent with the plans as input. It reviews:

- Are the empirics fields consistent with the locked identification decisions in CONTEXT.md? (E.g., if CONTEXT.md says "cluster at village level," does every plan specify village clustering?)
- Are the chosen estimators appropriate? Flag e.g., naive TWFE for staggered DiD with heterogeneous treatment effects.
- Are there missing robustness specs that the literature would expect?
- Are SEs computed appropriately for the design?
- Are sample restrictions consistent across plans? (No silent compositional changes between baseline and robustness.)

Output: `.planning/phases/XX-<slug>/PLAN-CHECK.md` with verdict per plan.

### Step 5 — Iterate if needed

If the identification-checker flags blockers:
- Show the user the verdict
- Decide whether to revise the plan or push back on the checker (rare but legitimate)
- Loop until verdict is clean

### Step 6 — Spawn plan checker

Spawn GSD's standard plan-checker (or the gsd-econ override if present) to verify plans achieve phase goals.

### Step 7 — Show plans to user

Present the final plans, one at a time. The user reviews and either accepts or requests changes.

### Step 8 — Hand-off

Commit. Tell the user: `/gsd-execute-phase $ARGUMENTS` to run them.

## Constraints

- **Every plan must specify cluster level explicitly.** No silent defaults. If the design implies something non-obvious (two-way clustering, Conley spatial), it's in the plan, not in some helper script the executor finds.
- **No naive TWFE for staggered DiD.** If the user is doing staggered adoption, the plan uses Callaway-Sant'Anna, Sun-Abraham, BJS, or de Chaisemartin–D'Haultfœuille. If the user insists on TWFE, the identification-checker emits a `warning` test failure and the plan documents the deviation.
- **Robustness is not optional.** Every main-results phase has a corresponding robustness plan in the next phase. The `<gates>` of the main-results plan reference at least one robustness test from the registry.
- **Do not generate code in this command.** Only the plan. Code is the executor's job.

## Output

- `.planning/phases/XX-<slug>/RESEARCH.md` ✓
- `.planning/phases/XX-<slug>/01-PLAN.md` … `NN-PLAN.md` ✓
- `.planning/phases/XX-<slug>/PLAN-CHECK.md` ✓
- Clean commit
- Pointer to `/gsd-execute-phase $ARGUMENTS`
