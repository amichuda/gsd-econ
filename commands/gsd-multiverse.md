---
description: "Run a specification-curve multiverse analysis using the project's logged data-cleaning decisions and an optional methodology grid. Produces an audit table and a specification curve figure."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: "[--grid <design>] [--mode auto|full|main-effects|sample] [--max-cells <N>] [--evaluator <path>] [--dry-run]"
model_tier: standard
---

# /gsd-multiverse

Automated robustness analysis. Reads `decisions.jsonl` (data-cleaning and methodology choices logged by execute-phase agents) and an optional design-family grid (`config/multiverse-grids/{rct,did,iv,rdd}.yaml`), constructs the cross-product of all defensible specifications, and runs the analysis once per cell.

The output is a specification curve — the same plot Simonsohn, Simmons & Nelson (2020) advocate — plus an audit table suitable for journal supplementary material.

## When to invoke

After the execute phase is done and `decisions.jsonl` exists in the project root. Before submission, when you want to know whether the headline result is fragile to defensible alternative choices.

Typical invocations:

```
/gsd-multiverse                          # Auto-detect design, use full grid
/gsd-multiverse --grid did               # Force the DiD grid
/gsd-multiverse --grid did --grid iv     # Compose two grids
/gsd-multiverse --dry-run                # Show the proposed grid without running
/gsd-multiverse --mode main-effects      # Quick sensitivity sweep (one axis at a time)
/gsd-multiverse --mode full              # Full cross-product (warning: can be slow)
```

## Inputs the command expects

1. `decisions.jsonl` at the project root, formatted per `rules/decision-logging.md`. If missing, the command surfaces this and points the user at the execute-phase agents that should have created it.

2. An evaluator script at `code/multiverse_evaluator.py` (or path provided via `--evaluator`). The evaluator must define:

   ```python
   def evaluate(spec: dict) -> dict:
       """Run the analysis with the given specification.

       Args:
           spec: dict mapping axis name to chosen value, e.g.
               {"se_clustering": "robust_individual",
                "stratum_fe": "include_strata", ...}

       Returns:
           dict with at least 'coefficient' and 'se'.
           May include 'p_value', 'n_obs', 'r_squared', etc.
       """
       ...
   ```

   If this file doesn't exist, the multiverse-runner agent will help scaffold one based on the project's existing analysis code.

3. (Optional) `--grid <name>` flags pointing at one or more methodology grids in `config/multiverse-grids/`. If omitted, the command auto-detects the design from `.planning/METHODOLOGY.md`.

## Process

### Step 1 — Verify preconditions

- Check that `decisions.jsonl` exists and is parseable. If missing, surface and stop.
- Check that the evaluator script exists, or offer to scaffold one.
- If neither `--grid` nor a usable METHODOLOGY.md is available, ask which grid(s) to compose.

### Step 2 — Show the proposed multiverse

Run `scripts/multiverse_runner.py --dry-run` to print the proposed grid. The output shows:

- Each axis name and source (decisions.jsonl line, or grid file)
- All values to test for each axis
- The total cell count and the main-effects subset count

Present this to the user and ask:
- Are there axes to drop (not actually contested in retrospect)?
- Are there alternatives within an axis to drop (not actually defensible)?
- Should any axis be marked `pap_committed` (held fixed)?
- What sampling mode: full, main-effects, or sample?

Edit `decisions.jsonl` based on user input. Do not edit the grid YAMLs directly; instead, if the user wants to drop grid axes, create a project-local override `.planning/multiverse-overrides.yaml` documenting the choices.

### Step 3 — Run the multiverse

Invoke `scripts/multiverse_runner.py` with the chosen mode:

```bash
python3 scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --grid config/multiverse-grids/<design>.yaml \
    --evaluator code/multiverse_evaluator.py \
    --output multiverse_results.csv \
    --mode <chosen> \
    --summarize
```

This may take time. The runner prints progress every 5%. If a cell raises an exception, the row records `error: <message>` and the runner continues.

### Step 4 — Build the reports

Spawn the `multiverse-reporter` subagent to produce both deliverables from `multiverse_results.csv`:

- A publication-quality specification curve PDF (for the paper) at `output/figures/multiverse_curve.pdf`
- A self-contained interactive HTML report (for sharing) at `output/multiverse_report.html`
- A booktabs LaTeX audit table at `output/tables/multiverse_audit.tex`

The agent reads the project's house style (existing figures in `output/figures/`) and produces matching output. Both the PDF and the HTML embed the same specification-curve plot — the HTML adds interactive sortable tables, axis-decomposition diagnostics, and embedded download links.

### Step 5 — Report

Print a structured summary:

```
✓ Multiverse complete.

  Grid: N axes, M cells
  Mode: <full | main_effects | sample>
  Headline (PAP-locked) coefficient: 0.094 (SE 0.045)
  Multiverse range: [0.072, 0.118]
  IQR: [0.085, 0.103]
  % cells with p<0.05: 87/120 (72.5%)

  Most-influential single axis (largest range when varied alone):
    "switcher_handling" — coefficient spans 0.068 to 0.121

  Cells producing the most extreme results:
    Min (0.072): {se_clustering: ..., controls: ...}
    Max (0.118): {se_clustering: ..., controls: ...}

  Figure: output/figures/multiverse_curve.pdf
  Interactive report: output/multiverse_report.html
  Audit table: output/tables/multiverse_audit.tex
  Full CSV: multiverse_results.csv
```

## Constraints

- **Never overwrite an existing multiverse run without confirmation.** If `multiverse_results.csv` exists, archive it as `multiverse_results.YYYY-MM-DD-HHMMSS.csv` before re-running.

- **Don't optimize for any metric.** The runner is neutral; the agent never picks a "best" specification. The deliverable is the full distribution, not a winner.

- **Honor PAP commitments.** Decisions with `pap_committed: true` are held at the committed value. This is non-negotiable: the multiverse tests robustness within the unconstrained subspace, not retroactive PAP revisions.

- **Surface failures rather than masking them.** If a substantial fraction of cells error (>10%), stop and surface the error pattern. Don't silently filter to "successful" cells; that biases the audit.

- **Respect the meta-cognition rule.** Don't fabricate plausible-looking results. If the evaluator fails for some cells, the CSV shows the failures.

## Honest limits

- The multiverse can only test what's in the log. Decisions baked into upstream data construction (before the agent saw the data) are invisible.

- A specification curve shows **whether** the result is fragile. It does not show **why**. Attributing fragility to a specific axis requires decomposition (e.g., ANOVA over the grid), which the v0.3 runner does crudely via main-effects mode but not rigorously.

- For very large grids (millions of cells), the runner falls back to sampling. Sampled results are descriptive, not exhaustive. Document the sampling choice in the audit.

- The methodology grids are **starting points**, not exhaustive. A design-specific concern (a clever placebo test, a structural parameter) should be added to `decisions.jsonl` rather than crammed into a generic grid.

## Output

- `multiverse_results.csv` (project root) — one row per specification with axis values and result columns (`coefficient`, `se`, optional `p_value`, `n_obs`, etc.)
- `output/figures/multiverse_curve.pdf` — publication-quality specification curve (for the paper)
- `output/figures/multiverse_curve.png` — 300 DPI preview
- `output/multiverse_report.html` — self-contained interactive HTML report (for sharing with coauthors/referees)
- `output/tables/multiverse_audit.tex` — booktabs audit table for supplementary material
- A structured summary printed to the terminal (cell count, headline coefficient, range, IQR, share significant, most-influential axis)
- (If re-running) Previous `multiverse_results.csv` archived with timestamp

## See also

- `docs/multiverse-tutorial.md` — worked tutorial: setup, decisions.jsonl, evaluator, run, report
- `rules/decision-logging.md` — what gets logged and why
- `config/multiverse-grids/README.md` — the methodology grid schema
- `docs/multiverse.md` — full conceptual documentation
- Simonsohn, Simmons & Nelson (2020), "Specification Curve Analysis," Nature Human Behaviour
- Steegen, Tuerlinckx, Gelman & Vanpaemel (2016), "Increasing transparency through a multiverse analysis," Perspectives on Psychological Science
