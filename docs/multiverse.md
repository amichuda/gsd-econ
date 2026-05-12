# Multiverse analysis

`/gsd-multiverse` automates **specification-curve analysis** (Simonsohn,
Simmons & Nelson 2020) for empirical economics papers. It reads the
data-cleaning and methodology decisions logged during the execute phase,
composes them with a methodology grid for the design family, and runs
the analysis across every defensible specification.

The output is a specification curve — coefficient + 95% CI for every
plausible analytical path — plus an audit table suitable for journal
supplementary material.

## What problem this solves

Robustness analysis in empirical economics is historically asymmetric.
Authors choose which alternatives to test based on what reasonably
defensible alternatives they happened to think of. A skeptical reader
has to guess which alternatives weren't tested. Specification curves
(Simonsohn-Simmons-Nelson 2020), multiverse analysis (Steegen et al.
2016), and related approaches address this by mandating that *all*
defensible alternatives be reported — but the boilerplate has
historically prevented widespread adoption.

The cost of multiverse analysis is high for two reasons. The first is
enumerating the grid: most papers have 20-50 contested choices, each
with 2-4 alternatives, generating a grid of 10^15 to 10^30
specifications. The second is running them: each cell requires a full
analysis pipeline executed end-to-end.

This framework lowers both costs:

- The execute-phase agents log contested decisions to `decisions.jsonl`
  as they make them, capturing alternatives at the moment of choice
  rather than asking the author to reconstruct them in retrospect.
- The methodology grids (`config/multiverse-grids/`) ship with the
  standard list of contested methodology choices for each design family,
  with citations.
- The multiverse runner composes the two and runs the cross-product (or
  a sampled subset for large grids).

## The conceptual claim

The framework's claim is that **automated specification-curve analysis
should be the default standard for empirical work**, replacing
hand-picked robustness tables. The cost was the obstacle; once the cost
is removed, the asymmetry is no longer defensible.

This is not a methodological innovation — Simonsohn et al. proposed
specification curves in 2020 and Steegen et al. proposed multiverses in
2016. The contribution here is operational: making them cheap enough
that "I didn't have time" stops being an excuse.

## How decisions get into the multiverse

The pipeline has two sources:

**Project-specific decisions**, logged to `decisions.jsonl` during the
execute phase by `econometrician` and `tables-figures-builder` (and any
custom analysis code that follows the contract). These capture
data-cleaning choices, variable construction, and project-specific
methodology decisions. See `rules/decision-logging.md` for the schema
and what counts as "contested."

**Methodology-grid decisions**, shipped as YAML files in
`config/multiverse-grids/`. These capture the well-known contested
choices for each design family (DiD estimator choice, RDD bandwidth,
IV weak-instrument correction, RCT clustering level, etc.). Each axis
has a default, alternatives, justification, and citations.

The multiverse runner reads both and constructs the cross-product. By
construction, axes with `pap_committed: true` are held fixed —
pre-registered commitments aren't reopened.

## Workflow

The standard sequence:

1. Run the execute phase normally. The agents log decisions as they go.
2. After analysis is complete and the headline result is written, run
   `/gsd-multiverse`.
3. The command shows the proposed grid (e.g., "8 axes, 1,536 cells; in
   main-effects mode, 24 specifications") and asks for any pruning.
4. The runner executes each spec via your evaluator script.
5. The plotter produces a specification curve and audit table.

The deliverable for the paper is the headline result plus the
specification curve as a figure plus the audit CSV as supplementary
material.

## The evaluator contract

Users provide a Python function:

```python
def evaluate(spec: dict) -> dict:
    """
    Run the analysis with the given specification.

    Args:
        spec: dict mapping axis name to chosen value, e.g.
            {"se_clustering": "robust_individual",
             "stratum_fe": "include_strata",
             "controls": "no_controls",
             ...}

    Returns:
        dict with at least 'coefficient' and 'se'. May also include
        'p_value', 'n_obs', 'r_squared', etc.
    """
    ...
```

This contract is deliberately minimal. The framework imposes no
opinion about how you implement the evaluator — you can use any
statistical software accessible from Python, including Stata or R
via subprocess calls. What matters is that `evaluate(spec)` returns a
consistent dict for every spec it's called with.

For most projects, the evaluator is a function that:
1. Takes the spec dict
2. Calls into your existing analysis pipeline with the right parameter
   substitutions
3. Runs the regression
4. Returns the coefficient and SE

If your analysis is in Stata, the evaluator can subprocess into
`stata -b do ...` with the spec values as arguments. Same for R or
SAS. The framework doesn't constrain this.

## Sampling for large grids

The full cross-product is often intractable: 10 axes with 3 values
each is 59,049 cells. The runner has three modes:

- **Full enumeration** (`--mode full`): every cell. Use when the grid
  is small (< 1000 cells) or you have time.
- **Main effects** (`--mode main_effects`): vary one axis at a time
  with others at default. Linear in axes (~1 + sum(|values|) cells).
  Fast and informative; the standard quick check.
- **Random sample** (`--mode sample --max-cells N`): random sample of
  N cells. Useful for very large grids where you want the distribution
  but can't enumerate.

The default is `auto`: full if ≤ max-cells, else main-effects.

## Interpreting the specification curve

The curve shows the coefficient for every specification. Three
patterns to watch for:

**Stable**: the coefficient varies modestly across cells (e.g., 0.080
to 0.110 for an estimated 0.094). The headline result is robust;
report the curve in supplementary material and move on.

**Fragile to a single axis**: one axis explains most of the variation
(e.g., switcher handling drives the coefficient from 0.07 to 0.13).
The paper should discuss this specific choice prominently and ideally
present the result both ways.

**Diffusely fragile**: the coefficient varies widely across cells
with no clear single-axis driver. This is the hardest case to write
up honestly. The paper should report the range and acknowledge that
the headline is one defensible cell within a wide distribution.

The framework doesn't decide for you what the right interpretation is.
It shows you the data; the writeup is yours.

## Pitfalls

**Optimization is the enemy.** The single most important rule: the
agent never picks a "best" specification. If you let it optimize for
maximum coefficient, you've automated p-hacking. The framework rules
forbid this explicitly. The deliverable is the distribution, not the
winner.

**The grid is a starting point.** A creative referee can always raise
an objection your multiverse didn't cover. The framework can't
guarantee completeness; it can guarantee transparency about what was
covered. Document the grid you used.

**Cleaning decisions are often the largest contributors.** The
methodology grids capture well-known statistical choices, but in many
papers the biggest robustness exposures come from cleaning decisions
(sample restrictions, variable definitions, outlier handling) that
aren't in any methodology textbook. The `decisions.jsonl` log is
where you capture these; don't let it be skinny.

**Grid composition can explode.** Two grids with 8 axes each may
generate 10^14 cells. Use main-effects mode or sample mode for these
cases. The runner will warn you when the full grid exceeds the
max-cells cap.

## Implementation notes

The runner is `scripts/multiverse_runner.py`. It's pure Python, only
depends on PyYAML (for the grids), and imports your evaluator script
via importlib. No statistical-software-specific dependencies; the
evaluator handles all that.

The runner is deliberately not an "AI agent" in the sense of using an
LLM — it's a deterministic harness. The LLM work happens upstream
(logging decisions during execute) and downstream (the plotter). The
sweep itself is mechanical; treating it as agentic would be both
slower and less reliable.

For very long-running multiverse sweeps (overnight runs), use
`--quiet` and redirect output. The CSV is written at the end; for
crash safety, consider modifying the runner to flush periodically (an
exercise for v0.4).

## See also

- `docs/multiverse-tutorial.md` — **worked tutorial** using the
  TGBLMM 2024 (Tjernström et al., Econometrica) replication package
  as the running example; covers setup → decisions.jsonl → evaluator
  → run → report end-to-end
- `rules/decision-logging.md` — what to log
- `config/multiverse-grids/README.md` — methodology grids
- `commands/gsd-multiverse.md` — the command-line entry point
- `scripts/multiverse_runner.py` — the runner
- Simonsohn, U., Simmons, J. P., & Nelson, L. D. (2020).
  Specification curve analysis. *Nature Human Behaviour*, 4(11),
  1208-1214.
- Steegen, S., Tuerlinckx, F., Gelman, A., & Vanpaemel, W. (2016).
  Increasing transparency through a multiverse analysis. *Perspectives
  on Psychological Science*, 11(5), 702-712.
- Slichter, D. (2014). The Significance of Specification Tests.
- Patel, C. J., Burford, B., & Ioannidis, J. P. A. (2015). Assessment
  of vibration of effects due to model specification can demonstrate
  the instability of observational associations. *Journal of Clinical
  Epidemiology*, 68(9), 1046-1058.
