---
description: Build or rebuild the tables/figures pipeline for the paper. Produces publication-quality LaTeX from analysis output, with consistent formatting across all numerical results.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: phase_number
---

# /gsd-tables-figures

You are running the tables and figures pipeline phase. This is a specialized phase — output is the rendered LaTeX/PDF artifacts that go into the manuscript.

Phase: $ARGUMENTS

## Process

### Step 1 — Inventory

Scan the paper directory:

- All regression output files (typically `output/`, `tables/raw/`, `results/`)
- All figure source data (typically `output/`, `figures/raw/`)
- Existing tables and figures in the manuscript LaTeX source
- The current `tables/` and `figures/` directories
- The Quarto / LaTeX manuscript draft

Read `.planning/phases/XX-<slug>/CONTEXT.md` and `REQUIREMENTS.md` to understand which results are required for the paper.

### Step 2 — Build the canonical inventory

For each table/figure that should appear in the paper, list:

```
T1: Summary statistics
  source: output/01_descriptives/sumstats.txt
  template: tables/templates/sumstats.tex
  output: tables/01_sumstats.tex
  caption: "Summary statistics, baseline sample"
  position: §3 Data, before Table 2
  status: present | stale | missing
```

Show this inventory to the user and ask for confirmation / corrections.

### Step 3 — Spawn tables-figures-builder

Spawn the `tables-figures-builder` agent for each stale or missing artifact, in parallel waves.

Each task in a plan looks like:

```xml
<task id="XX-NN-MM">
  <name>Build Table 3 — main results</name>
  <files>tables/03_main_results.tex, code/04_make_tables.R</files>
  <action>
    Use the existing fixest output stored at output/03_main/main_results.RDS.

    Build a 4-column LaTeX table:
    - Col 1: OLS, no FE
    - Col 2: + village FE
    - Col 3: + village + year FE
    - Col 4: Col 3 + controls

    All columns: cluster SE at village level (already in fixest output).

    Per universal-tables-have-n-obs: report N below each column.
    Per universal-clustered-ses-justified: footnote stating cluster level.

    Use booktabs format. No vertical lines. Three significant figures.

    Verify the LaTeX compiles standalone.
  </action>
  <verify>
    pdflatex tables/03_main_results.tex   # builds without error
    grep -c "^N " tables/03_main_results.tex   # >= 1
  </verify>
  <test_id>universal-tables-have-n-obs</test_id>
  <test_id>universal-clustered-ses-justified</test_id>
  <done>Compiled, N reported, cluster level footnoted, in tables/.</done>
</task>
```

### Step 4 — Verify pipeline coherence

After build, run:

1. **Reproducibility check:** invoke the project's main build (e.g., `make tables`, `quarto render`, the project's R/Stata pipeline). Confirm tables/figures regenerate identically. If the project doesn't have a top-level build target, this is a finding — surface it.

2. **Cross-reference check:** every `\ref{tab:...}` and `\ref{fig:...}` in the manuscript resolves. Every table/figure in the inventory is referenced at least once. No orphans.

3. **N consistency:** the N reported in tables matches the sample size implied by the data step's output logs. (Triggers `universal-tables-have-n-obs` and a sanity check beyond it.)

4. **Figure quality:** PDF figures are vector (not rasterized at low DPI). Fonts embed. Sizes match the manuscript column width.

### Step 5 — Run RUT tests for this phase

Implicitly invoke the table/figure-relevant tests:
- `universal-tables-have-n-obs`
- `universal-clustered-ses-justified`
- `universal-sample-restrictions-stated` (the sample restrictions used in tables match REQUIREMENTS.md)
- Any methodology-specific table tests (e.g., `did-parallel-trends-plot` if a DiD paper)

Surface results inline; full verification at `/gsd-verify-replication $ARGUMENTS`.

### Step 6 — Commit and hand off

One commit per table/figure rebuilt. Atomic. Trail looks like:

```
abc123 feat(phase-7): rebuild Table 1 (sumstats) — N rows, weighted means
def456 feat(phase-7): rebuild Table 3 (main) — clustered SE footnoted
hij789 feat(phase-7): rebuild Figure 2 (event study) — vector, fonts embedded
```

Tell the user: `/gsd-verify-replication $ARGUMENTS` to run the gates.

## Constraints

- **Do not generate fake numbers.** If the source result file doesn't exist, the task is to compute the result, not synthesize a plausible-looking table. Add a dependency on the upstream phase.
- **Preserve the project's house style.** Read existing tables before generating new ones. Match column alignment, decimal precision, footnote conventions. If the project uses `estout` (Stata) or `modelsummary` (R), use the same.
- **No proprietary fonts.** Stick to Computer Modern, Latin Modern, or another freely-licensed font. The replication archive must be self-contained.
- **Figures: vector first.** PDF or TikZ. Raster only when the source is genuinely raster (e.g., a satellite image). If raster, embed at ≥300 DPI for the column width.

## Output

- All tables/figures rebuilt and present in `tables/` and `figures/`
- Atomic commits, one per artifact
- Inventory check clean
- Pointer to verification step
