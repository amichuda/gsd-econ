# Tutorial: running a multiverse on someone else's replication package

This is a worked tutorial. By the end you will have:

1. Imported an existing Stata or Python replication archive into a
   gsd-econ project
2. Derived a `decisions.jsonl` automatically from the cleaning
   module's function signatures
3. Written an evaluator that varies cleaning and methodology choices
4. Run a specification-curve multiverse against the package
5. Generated a PDF specification curve and an interactive HTML report

The running example is the **TGBLMM 2024 (Tjernström-Ghanem-Barriga
Cabanillas-Lybbert-Michler-Michuda) Econometrica replication package**,
on hybrid maize adoption in Kenya. The same workflow applies to any
replication package that exposes cleaning choices as function arguments
(which is, hopefully, more and more of them).

For the conceptual framework — *why* multiverses, what makes a decision
"contested," what the specification curve interprets — read
[`multiverse.md`](multiverse.md) first. This tutorial is operational.

## Prerequisites

- gsd-econ v0.3+ installed: `./install.sh --runtime <claude|opencode>`
- Python 3.10+ with pandas, statsmodels, pyyaml
  - `pip3 install --break-system-packages pandas statsmodels pyyaml`
  - or use `uv` if available
- The replication package you want to test, unzipped
- A copy of any raw data the cleaning code needs (or be honest about
  what you can and can't faithfully vary — see Step 3.5)

You also need an existing analysis pipeline that produces the headline
coefficient deterministically given parameter inputs. If the
replication package doesn't, you have to build one before the multiverse
is useful. That's typically 1-3 hours of glue code per project.

## Step 0: Project layout

Set up a working directory next to (not inside) the replication package:

```bash
mkdir -p ~/multiverse-runs/grc
cd ~/multiverse-runs/grc

# Symlink or copy in the replication package
ln -s ~/Downloads/grc-replication-package-main grc-rep

# Subdirs the multiverse expects
mkdir -p code data paper output
```

Symlink the data the replication archive ships:

```bash
ln -s "$(pwd)/grc-rep/data_synth/processed/final_long_1997_2000_2004.csv" data/long.csv
ln -s "$(pwd)/grc-rep/data_synth/econometrica_data.csv" data/wide.csv
```

Now wire gsd-econ into this directory:

```bash
~/src/gsd-econ/install.sh --project --runtime opencode \
    --models-config ~/src/gsd-econ/config/model-configs/openrouter-hybrid.yaml
```

You should now have `.planning/`, `agents/`, `rules/`, `commands/`,
`config/`, and an `AGENTS.md` in the working directory.

## Step 1: Inventory the cleaning module

This is the key insight: **a well-engineered cleaning module exposes
contested decisions as function arguments**. Look at
`grc-rep/scripts/data_cleaning/main_cleaner.py`:

```python
parser.add_argument("-dc", "--drop_credit", action="store_true",
    help="whether to drop missing observations before creating credit variables.")
parser.add_argument("-dd", "--drop_dist", action="store_true",
    help="Whether to drop missing observations before creating distance variables.")
parser.add_argument("-m", "--maize_interp", action="store_true",
    help="whether to fill in missing crop values with crop with most observations...")
parser.add_argument("-mfs", "--maize_field_specific", action="store_true",
    help="whether to use the alternative way of calculating labor variables...")
parser.add_argument("-st", "--suri_test", action="store_true",
    help="whether to use the suri HHIDs directly when constructing the variable.")
parser.add_argument("-mi", "--include_1997_intercropping", action="store_true",
    help="whether to use the old crop variable that Suri used in her analysis...")
parser.add_argument("-y", "--years", type=str,
    help="The years on which to do the dataset construction...")
```

Seven cleaning toggles, each with a help string that documents what
choosing the non-default would change. **These are your multiverse
axes.** The author already enumerated the contested decisions and
defended them; you just need to vary them.

Also look at `FinalDatasetCreation.__init__` (in
`grc-rep/scripts/data_cleaning/final_dataset_creation/final_dataset_creation.py`):

```python
def __init__(self,
             years = None, testing = False,
             drop_dist = False, drop_credit = False,
             save_intermediate = False,
             most_freq_maize_interp = False,
             maize_field_specific = False,
             include_1997_intercrop = False):
```

Same toggles, slightly different names. The `__init__` is what
`main_cleaner.py` calls, so the defaults here are the canonical
defaults.

For **buried** decisions — choices baked into method bodies rather
than exposed as arguments — open the variable constructors and look
for `np.where`, `isin`, or magic numbers. Example from
`input_seed_hybrid_identifier.py`:

```python
def _hybrid_indicator(self, data):
    data['hybrid'] = np.where(
        data[self.seed_type_col].isin(['Purchased hybrid']),
        1, 0)
```

The `valid_list` a few lines up shows the alternatives:

```python
valid_list = ['Purchased hybrid', 'Local variety',
    'Open pollinated variety (OPV)', 'OPV', 'Retained hybrid',
    'Seedlings/cuttings/splits',
    'Hybrid and local mix', 'Hybrid purchased & retained',
    'Do not know']
```

So the hybrid-treatment indicator could legitimately be: just
`Purchased hybrid` (default), `Purchased + Retained`, or
`anything-hybrid-containing`. That's another axis.

Don't go hunting for buried decisions exhaustively — log the obvious
ones, then let the agent's review pass find more later.

## Step 2: Generate `decisions.jsonl`

For each function-argument decision, write one JSON line per the
schema in [`rules/decision-logging.md`](../rules/decision-logging.md):

```bash
cat > decisions.jsonl <<'EOF'
{"id": "d001", "phase": "cleaning", "type": "filter", "variable": "credit_variables", "decision": "no_drop", "alternatives": ["drop_missing"], "justification": "Source: FinalDatasetCreation.__init__ exposes drop_credit (bool). Default is False; referee could ask whether complete-case credit handling changes the result.", "pap_committed": false}
{"id": "d002", "phase": "cleaning", "type": "filter", "variable": "distance_variables", "decision": "no_drop", "alternatives": ["drop_missing"], "justification": "Source: FinalDatasetCreation.__init__ exposes drop_dist (bool). Default is False.", "pap_committed": false}
{"id": "d003", "phase": "cleaning", "type": "imputation", "variable": "field_crop", "decision": "no_interp", "alternatives": ["most_freq_maize_interp"], "justification": "Source: most_freq_maize_interp (bool). Fills missing crop values with most-frequent crop on that field. Default is False.", "pap_committed": false}
{"id": "d004", "phase": "cleaning", "type": "variable_construction", "variable": "labor", "decision": "household_level", "alternatives": ["maize_field_specific"], "justification": "Source: maize_field_specific (bool). Alternative labor-variable construction; only applies to 1997 and 2004.", "pap_committed": false}
{"id": "d005", "phase": "cleaning", "type": "sample_restriction", "variable": "hhid", "decision": "constructed_hhids", "alternatives": ["suri_hhids_only"], "justification": "Source: suri_test (bool). Restricts to Suri-2011 HHIDs.", "pap_committed": false}
{"id": "d006", "phase": "cleaning", "type": "variable_construction", "variable": "acres_1997", "decision": "exclude_intercropping", "alternatives": ["include_intercropping_suri_2011_style"], "justification": "Source: include_1997_intercrop (bool). Replicates Suri 2011 acres/yields when True.", "pap_committed": false}
{"id": "d007", "phase": "cleaning", "type": "sample_window", "variable": "years", "decision": "1997_2000_2004", "alternatives": ["1997_2004_suri", "all_available"], "justification": "Source: --years flag. Three legitimate windows.", "pap_committed": false}
{"id": "d008", "phase": "construction", "type": "variable_definition", "variable": "hybrid", "decision": "purchased_hybrid_only", "alternatives": ["purchased_or_retained_hybrid", "any_hybrid_including_mixes"], "justification": "Source: input_seed_hybrid_identifier._hybrid_indicator line 130. The valid_list nearby contains other hybrid-related types.", "pap_committed": false}
EOF
```

A few rules of thumb when writing the entries:

- **Default is what the package ships with.** The first `alternatives`
  entry is the most defensible departure. Order matters only for
  display.
- **`pap_committed: false`** for cleaning toggles — they're not
  pre-registered. Methodology decisions might be `true` if a PAP
  pins them.
- **`justification` should reference the source.** Line number, file
  name, comment text. "Source: line 130 of foo.py" makes the
  decisions log auditable.
- **One decision per line.** Append-only.

Now add the analysis-side decisions visible in the Stata code. For
GRC, open `grc-rep/scripts/2_1_crc.do` and look at lines 8-15:

```stata
* 1 - Decisions for analysis
* (1) run with or without HIV counties?
    global hivdrop "if !high_aids"
* (2) covariates
    define_covariates
```

The author literally labels these "Decisions for analysis." Add them:

```bash
cat >> decisions.jsonl <<'EOF'
{"id": "d009", "phase": "methodology", "type": "sample_restriction", "variable": "high_aids_counties", "decision": "include_all", "alternatives": ["drop_high_aids"], "justification": "Source: scripts/2_1_crc.do line 11 — global hivdrop. Explicitly labeled 'Decisions for analysis' in the do-file.", "pap_committed": false}
{"id": "d010", "phase": "methodology", "type": "controls", "variable": "regression_controls", "decision": "no_controls", "alternatives": ["full_covariates", "covariates_plus_interactions"], "justification": "Source: scripts/2_1_crc.do and 2_2_ols_fe.do — paper reports specifications with no controls, with vars_all, and with covariates plus interactions.", "pap_committed": false}
{"id": "d011", "phase": "methodology", "type": "estimator_choice", "variable": "primary_estimator", "decision": "household_fe", "alternatives": ["ols_no_fe", "ols_with_province_fe", "household_fe_no_controls", "crc_full_sample"], "justification": "Source: scripts/2_2_ols_fe.do and 2_1_crc.do — five distinct specifications reported.", "pap_committed": false}
{"id": "d012", "phase": "inference", "type": "se_clustering", "variable": "standard_errors", "decision": "cluster_hhid", "alternatives": ["robust_no_cluster", "cluster_district", "cluster_province"], "justification": "Source: scripts/2_2_ols_fe.do uses vce(cluster hhid). Coarser clustering is conservative if there is spatial correlation.", "pap_committed": false}
EOF
```

You now have 12 axes. Dry-run to see the grid size:

```bash
python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --evaluator code/multiverse_evaluator.py \
    --dry-run
```

The runner will say `Error: evaluator not found` because we haven't
written it yet. Add `--evaluator /dev/null` doesn't work either; the
runner imports the evaluator at startup. The fix is just to write the
evaluator stub first and run the dry-run after.

## Step 3: Write the evaluator

The evaluator is a Python file with a single `evaluate(spec) -> dict`
function. The runner imports it via `importlib`, so any imports
inside the file are available.

The cleanest pattern is to **shell out to the existing cleaning and
analysis code with the spec values as arguments**, then parse the
output. This keeps the multiverse infrastructure separate from your
research code and avoids re-implementing the cleaning logic.

### 3.1: The subprocess pattern (recommended for real runs)

```python
# code/multiverse_evaluator.py
"""Multiverse evaluator for the GRC replication package.

For each spec dict, shells out to the existing cleaning pipeline,
then runs the Stata analysis, parses the resulting coefficient.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

REP_PACKAGE = Path(__file__).resolve().parent.parent / "grc-rep"
CLEAN_SCRIPT = REP_PACKAGE / "scripts" / "data_cleaning" / "main_cleaner.py"


def _build_clean_args(spec: dict) -> list[str]:
    """Translate a spec dict into CLI arguments for main_cleaner.py."""
    args = ["python3", str(CLEAN_SCRIPT)]

    # Map years
    if spec.get("d007") == "1997_2004_suri":
        args += ["--years", "suri"]
    elif spec.get("d007") == "all_available":
        args += ["--years", "all"]
    else:
        args += ["--years", "1997,2000,2004"]

    # Boolean flags from cleaning decisions
    if spec.get("d001") == "drop_missing":
        args.append("--drop_credit")
    if spec.get("d002") == "drop_missing":
        args.append("--drop_dist")
    if spec.get("d003") == "most_freq_maize_interp":
        args.append("--maize_interp")
    if spec.get("d004") == "maize_field_specific":
        args.append("--maize_field_specific")
    if spec.get("d005") == "suri_hhids_only":
        args.append("--suri_test")
    if spec.get("d006") == "include_intercropping_suri_2011_style":
        args.append("--include_1997_intercropping")

    args += ["--save_final"]
    return args


def _run_analysis(spec: dict, data_path: Path) -> dict:
    """Run the Stata regression with the spec's analysis-axis values."""
    # Write a temp do-file that picks up the cleaned data and runs the
    # spec'd estimator + SE structure. Parse the displayed coefficient.
    estimator = spec.get("d011", "household_fe")
    controls = spec.get("d010", "no_controls")
    cluster = spec.get("d012", "cluster_hhid")
    sample = spec.get("d009", "include_all")

    do_lines = [
        f'use "{data_path}", clear',
        'if "$sample" == "drop_high_aids" keep if !high_aids' if sample == "drop_high_aids" else "",
        # ... rest of the do-file: build covariates, run reghdfe with the
        # right cluster and FE options, then display the coefficient
    ]

    with tempfile.NamedTemporaryFile("w", suffix=".do", delete=False) as f:
        f.write("\n".join(do_lines))
        do_path = f.name

    result = subprocess.run(
        ["stata", "-b", "do", do_path],
        capture_output=True, text=True, timeout=300,
    )
    output = result.stdout
    # Parse coefficient and SE from the do-file's display output
    coef_match = re.search(r"COEF=(-?\d+\.\d+)", output)
    se_match = re.search(r"SE=(-?\d+\.\d+)", output)
    if not coef_match or not se_match:
        return {"coefficient": float("nan"), "se": float("nan"),
                "error": "could not parse Stata output"}
    return {
        "coefficient": float(coef_match.group(1)),
        "se": float(se_match.group(1)),
    }


def evaluate(spec: dict) -> dict:
    # Cache the cleaned data: same cleaning spec → same cleaned data.
    # Hashing the cleaning-spec subset lets us avoid re-cleaning when
    # only analysis axes change.
    cleaning_keys = ["d001", "d002", "d003", "d004", "d005", "d006",
                     "d007", "d008"]
    cleaning_spec = {k: spec.get(k) for k in cleaning_keys}
    cleaning_hash = hash(frozenset(cleaning_spec.items()))
    cleaned_path = Path(f"/tmp/grc_cleaned_{cleaning_hash}.dta")

    if not cleaned_path.exists():
        args = _build_clean_args(spec)
        subprocess.run(args, check=True, timeout=600,
                       cwd=REP_PACKAGE.parent)
        # main_cleaner.py writes to data/processed/final_long_*.dta;
        # copy or rename to cleaned_path
        actual_output = (REP_PACKAGE.parent / "data" / "processed" /
                         f"final_long_{spec['d007']}.dta")
        cleaned_path.symlink_to(actual_output)

    return _run_analysis(spec, cleaned_path)
```

The structure: **clean once per unique cleaning-spec hash, run
analysis per cell.** A multiverse with 8 cleaning axes and 4 analysis
axes only needs `2^8 = 256` cleaning runs but `256 × M = ?` regression
runs where M is the analysis-cross-product size. The caching saves a
lot.

### 3.2: The all-Python pattern (fallback)

If the replication package is pure Python (or you've ported it), you
can call the cleaning and analysis functions directly without
subprocess:

```python
import sys
sys.path.insert(0, str(REP_PACKAGE / "scripts" / "data_cleaning"))
from final_dataset_creation.final_dataset_creation import FinalDatasetCreation

def evaluate(spec):
    # Translate spec into kwargs for FinalDatasetCreation.__init__
    cleaner = FinalDatasetCreation(
        years=_translate_years(spec["d007"]),
        drop_credit=(spec["d001"] == "drop_missing"),
        drop_dist=(spec["d002"] == "drop_missing"),
        most_freq_maize_interp=(spec["d003"] == "most_freq_maize_interp"),
        maize_field_specific=(spec["d004"] == "maize_field_specific"),
        include_1997_intercrop=(spec["d006"] == "include_intercropping_suri_2011_style"),
    )
    df = cleaner.final_long_dataset(
        suri_test=(spec["d005"] == "suri_hhids_only"),
        save_final=False,
    )
    return _run_regression(df, spec)
```

Faster than subprocess (no IPC, no Stata startup), but only works
when the cleaning code is importable Python.

### 3.3: Sanity-check before running the multiverse

**Always do this.** Call the evaluator once with the all-defaults
spec and verify the coefficient matches the published paper's
headline. If it doesn't, the evaluator is buggy and the multiverse
will be meaningless.

```bash
python3 -c "
from code.multiverse_evaluator import evaluate
default_spec = {
    'd001': 'no_drop', 'd002': 'no_drop', 'd003': 'no_interp',
    'd004': 'household_level', 'd005': 'constructed_hhids',
    'd006': 'exclude_intercropping', 'd007': '1997_2000_2004',
    'd008': 'purchased_hybrid_only',
    'd009': 'include_all', 'd010': 'no_controls',
    'd011': 'household_fe', 'd012': 'cluster_hhid',
}
import json
print(json.dumps(evaluate(default_spec), indent=2))
"
```

For GRC, the household-FE no-controls headline coefficient on hybrid
should match Column 1 of Table V in the published paper (or whatever
the paper's "Table 1, Column 1, default specification" is).

If it doesn't match: stop. Fix the evaluator. Don't proceed.

### 3.5: What to do when you can't faithfully vary every axis

You may not have access to all the raw data the cleaning code needs.
GRC ships only the post-cleaning synthetic data; the raw Tegemeo
microdata is gated by Tegemeo's data-sharing agreement. In this case
you have three options:

1. **Acquire the raw data** before running the multiverse. Cleanest
   but slowest path.
2. **Run a partial multiverse** that only varies axes you can
   faithfully vary, and document the rest as "would-have-varied."
   The HTML report should explicitly call out the unvaried axes so
   no one mistakes a stable specification curve for full robustness.
3. **Apply proxy transformations** that approximate what each
   cleaning toggle would have done. For example, "drop missing
   credit observations" on the cleaned data becomes "drop rows where
   `tried_to_get_credit` is missing." These are not faithful
   substitutes but make the framework testable; document each proxy
   per-axis.

Choose deliberately. Don't silently apply proxies — that's worse
than not varying the axis at all.

## Step 4: Dry-run the grid

```bash
python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --evaluator code/multiverse_evaluator.py \
    --dry-run
```

Output for GRC:

```
→ Loaded 12 axis(es) from decisions.jsonl
  Multiverse: 12 axes, 69120 total cells
    Main-effects subset: 21 cells
```

69,120 cells × (cleaning_runtime + analysis_runtime) per cell is more
compute than you want for the first run. Three sampling modes are
available:

- `--mode full`: every cell. Use only when total cells × runtime per
  cell ≤ tolerable.
- `--mode main_effects`: vary one axis at a time, others at default.
  Linear in number of axes. The diagnostic mode — fast, surfaces
  most fragility.
- `--mode sample --max-cells N`: random sample of N cells. Useful
  for broad coverage of very large grids.

For the first pass, **always run main-effects first**. It tells you
which axes matter; if a stable result comes from main-effects, the
full cross-product is unlikely to overturn it.

## Step 5: Run the multiverse

### Main-effects sweep (start here)

```bash
python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --evaluator code/multiverse_evaluator.py \
    --output multiverse_results.csv \
    --mode main_effects \
    --summarize
```

For GRC with 12 axes, this is 21 cells (1 baseline + sum across axes
of `|values| - 1`). At maybe 20 seconds per cell (Stata startup
dominates), the run completes in ~7 minutes.

The runner prints progress every 5%, then a summary:

```
✓ Wrote 21 rows to multiverse_results.csv

  Specification curve summary (21 cells, column='coefficient'):
    min:    -0.0839
    Q1:      0.0062
    median:  0.0141
    Q3:      0.0478
    max:     0.1443
    range:   0.2282
    IQR:     0.0417
    p<0.05:  32/120 (26.7%)
```

If the IQR is small and the range is small, **you're done** — the
result is stable to the main-effects perturbations. Run the full
cross-product later if you want to be exhaustive, but the headline
finding stands.

If the IQR is large, **a single axis is driving fragility**. Look at
the CSV and find which one. Then drill into that axis specifically.

### Full cross-product of an interesting subset

If main-effects flags a few axes as influential, you can run the full
cross-product over just those axes. Filter `decisions.jsonl` to the
ones you care about:

```bash
# Keep only analysis-side decisions (d009-d012)
grep -E '"id": "d0(09|10|11|12)"' decisions.jsonl > decisions-analysis-only.jsonl

python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions-analysis-only.jsonl \
    --evaluator code/multiverse_evaluator.py \
    --output multiverse_results_analysis.csv \
    --mode full \
    --summarize
```

For GRC, that's 2 × 3 × 5 × 4 = 120 cells. At 5 seconds per cell with
warm cleaning cache, ~10 minutes.

## Step 6: Generate the reports

Two outputs: the publication-quality PDF specification curve, and a
self-contained interactive HTML report for sharing.

From within a Claude Code or OpenCode session:

```
Use the multiverse-reporter agent to produce the PDF and HTML reports
from multiverse_results.csv.
```

The agent reads the CSV, identifies the PAP-locked specification
(every `pap_committed: true` decision at its default), sorts cells by
coefficient, and produces:

- `output/figures/multiverse_curve.pdf` — for the manuscript
- `output/figures/multiverse_curve.png` — preview
- `output/multiverse_report.html` — self-contained interactive
- `output/tables/multiverse_audit.tex` — booktabs audit table

The HTML can be opened in any browser, no server. Sortable, filterable
audit table; embedded SVG specification curve; download links for the
underlying CSV. Send it to a coauthor or a referee directly.

## Step 7: Interpret

The summary card on the HTML report gives you the headline diagnostic:

- **Stable** (range small, IQR tiny): report the curve in
  supplementary material and move on.
- **Fragile to a single axis** (one axis spans most of the
  variation): the paper should call out that specific choice
  prominently and present the result both ways.
- **Diffusely fragile** (wide variation, no single-axis driver):
  acknowledge the headline is one defensible cell within a wide
  distribution. Don't claim more than the data supports.

For GRC specifically, the analysis-axes run shows:

| Axis | What it does | Range when varied alone |
|------|--------------|-------------------------|
| d010 (controls) | no_controls vs full_covariates vs +interactions | 0.034 |
| d011 (estimator) | OLS vs OLS+province FE vs HH FE vs CRC | 0.025 |
| d012 (clustering) | hhid vs district vs province vs robust | 0.021 |
| d009 (sample) | with vs without high-AIDS counties | 0.015 |

The dominant axis is the controls choice, and the dominant pattern is:
**within-FE specifications are tight; OLS specifications are not**.
This matches the paper's central methodological argument (that
random-coefficient methods are needed because OLS is biased), but the
multiverse surfaces it in numbers a referee can verify rather than
narrative.

## Common pitfalls

**The evaluator doesn't actually use the spec values.** Sanity check:
run two cells with very different parameter values and verify the
coefficients differ. If they don't, the evaluator is reading the spec
but not applying it. Common cause: typos in the keys (`d011` vs
`d_011`).

**The default-spec coefficient doesn't match the paper.** Stop. Fix
the evaluator. A wrong evaluator produces a confidently wrong
specification curve, which is worse than not running one.

**Cleaning is slow and dominates runtime.** Cache cleaned data by
cleaning-spec hash. The example in Step 3.1 shows the pattern. For
GRC, 256 unique cleaning specs × 60s/clean = 4.5 hours cleaning;
69,120 cells × 5s/regression = 96 hours regressions. With caching,
the cleaning happens once per unique combination — a huge win.

**Some axes have implementation bugs.** The GRC run flagged that
clustering at the district level (`subloc`) fails on the synthetic
data because 1197/2395 rows have missing `subloc`. A real referee
would discover the same thing. This is value the multiverse adds:
**you find out about coding issues before the referee does**.

**The grid is too large.** 12 axes × ~3 values each = 530,000 cells.
Use `--mode main_effects` first; use `--mode sample --max-cells 1000`
for breadth. Full enumeration is rarely the right call for >1000
cells.

**Decisions added by the agent are wrong or trivial.** The
decision-logging rule has the right bar — "would a referee write a
comment asking about this choice?" — but agents err in both
directions. Review `decisions.jsonl` by hand before running. Delete
trivial entries; add missed ones.

## Where to go next

- [`multiverse.md`](multiverse.md) — the conceptual writeup with
  citations to Simonsohn-Simmons-Nelson 2020 and Steegen et al. 2016
- [`../rules/decision-logging.md`](../rules/decision-logging.md) —
  the rule that defines what gets logged
- [`../commands/gsd-multiverse.md`](../commands/gsd-multiverse.md) —
  command reference
- [`../config/multiverse-grids/`](../config/multiverse-grids/) —
  templated methodology grids for RCT, DiD, IV, RDD that compose
  with `decisions.jsonl`

The cleaning-grid pattern this tutorial walks through is the most
faithful form of multiverse analysis: **decisions documented in code
become decisions tested in the multiverse, with no LLM judgment
required on the cleaning side**. The framework's contribution is
operational; the methodological credit goes to the authors who wrote
their cleaning code with explicit toggles in the first place.
