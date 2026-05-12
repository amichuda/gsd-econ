#!/usr/bin/env python3
"""Multiverse analysis runner for gsd-econ.

Reads decisions.jsonl + optional methodology grid YAMLs, constructs the
specification grid, runs an evaluator over each cell, and produces a
specification-curve audit table.

Usage:
    python3 scripts/multiverse_runner.py \\
        --decisions decisions.jsonl \\
        --grid config/multiverse-grids/rct.yaml \\
        --evaluator path/to/evaluator.py \\
        --output multiverse_results.csv

The evaluator script must define a function:

    def evaluate(spec: dict) -> dict:
        '''
        Run the analysis with the given specification.

        Args:
            spec: dict mapping axis names to chosen values, e.g.
                {"se_clustering": "robust_individual",
                 "stratum_fe": "include_strata",
                 ...}

        Returns:
            dict with at least 'coefficient' and 'se' keys.
            May include 'p_value', 'n_obs', 'r_squared', etc.
        '''
        ...

The runner imports this function and calls it for each cell of the grid.

For very large grids (>1000 cells), the runner falls back to fractional
factorial sampling unless --enumerate-all is given.

Output is a CSV with one row per specification, sortable and plottable
for the specification curve.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip3 install pyyaml --user", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Axis:
    """One dimension of the multiverse grid."""
    name: str
    default: str
    alternatives: list[str]
    source: str  # "decisions.jsonl" or "grid:<filename>"
    pap_committed: bool = False
    description: str = ""

    @property
    def values(self) -> list[str]:
        """All values to test for this axis (default + alternatives, deduped)."""
        seen: set[str] = set()
        out: list[str] = []
        for v in [self.default, *self.alternatives]:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out


@dataclass
class Multiverse:
    """The full grid: a collection of axes."""
    axes: list[Axis] = field(default_factory=list)

    @property
    def total_cells(self) -> int:
        n = 1
        for axis in self.axes:
            n *= len(axis.values)
        return n

    def specifications(self) -> Iterator[dict[str, str]]:
        """Yield every cell of the cross-product as a dict."""
        if not self.axes:
            yield {}
            return
        value_lists = [axis.values for axis in self.axes]
        names = [axis.name for axis in self.axes]
        for combo in itertools.product(*value_lists):
            yield dict(zip(names, combo))

    def sample_specifications(self, n: int, seed: int = 42) -> Iterator[dict[str, str]]:
        """Random sample of n specifications (without replacement up to total_cells)."""
        rng = random.Random(seed)
        total = self.total_cells
        k = min(n, total)
        if k == total:
            yield from self.specifications()
            return
        # Sample indices without replacement, then convert each to a spec.
        indices = rng.sample(range(total), k)
        names = [axis.name for axis in self.axes]
        for idx in indices:
            spec: dict[str, str] = {}
            remaining = idx
            for axis in self.axes:
                values = axis.values
                spec[axis.name] = values[remaining % len(values)]
                remaining //= len(values)
            yield spec

    def main_effects_specifications(self) -> Iterator[dict[str, str]]:
        """Yield specifications that vary one axis at a time, holding others at default.

        Useful for a quick sensitivity sweep when the full grid is too large.
        Total count: 1 (all defaults) + sum_axis (|values_axis| - 1).
        """
        defaults = {axis.name: axis.default for axis in self.axes}
        yield dict(defaults)
        for axis in self.axes:
            for value in axis.values:
                if value == axis.default:
                    continue
                spec = dict(defaults)
                spec[axis.name] = value
                yield spec

    @property
    def main_effects_count(self) -> int:
        return 1 + sum(len(axis.values) - 1 for axis in self.axes)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_decisions(path: Path) -> list[Axis]:
    """Load decisions.jsonl, return non-PAP-committed entries as Axis objects."""
    if not path.exists():
        return []
    axes: list[Axis] = []
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"Warning: skipping malformed line {line_no} in {path}: {e}",
                    file=sys.stderr,
                )
                continue
            # Skip PAP-committed and decisions with no alternatives.
            if d.get("pap_committed", False):
                continue
            alts = d.get("alternatives", [])
            if not alts:
                continue
            # The decision itself is the "default" of this axis; alternatives are the rest.
            axes.append(Axis(
                name=d.get("id", f"line{line_no}"),
                default=d.get("decision", "<unspecified>"),
                alternatives=list(alts),
                source=f"decisions.jsonl line {line_no}",
                pap_committed=False,
                description=d.get("justification", "")[:200],
            ))
    return axes


def load_grid(path: Path) -> list[Axis]:
    """Load a methodology grid YAML, return axes."""
    if not path.exists():
        raise FileNotFoundError(f"Grid not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "axes" not in data:
        raise ValueError(f"{path} is not a valid grid (missing 'axes' field)")
    grid_axes = data["axes"]
    out: list[Axis] = []
    for name, spec in grid_axes.items():
        if not isinstance(spec, dict):
            continue
        # Skip axes with only one alternative (typically design-determined)
        alts = spec.get("alternatives", [])
        if len(alts) <= 1:
            continue
        default = spec.get("default", alts[0] if alts else "")
        # Ensure default is the first alternative if not already there
        out.append(Axis(
            name=name,
            default=default,
            alternatives=[a for a in alts if a != default],
            source=f"grid:{path.name}",
            pap_committed=spec.get("pap_relevance", "low") == "high",  # Initial guess; user can override
            description=spec.get("description", ""),
        ))
    return out


# ---------------------------------------------------------------------------
# Evaluator loading
# ---------------------------------------------------------------------------


def load_evaluator(path: Path) -> Callable[[dict], dict]:
    """Import the user's evaluator script and return its evaluate() function."""
    if not path.exists():
        raise FileNotFoundError(f"Evaluator not found: {path}")
    spec = importlib.util.spec_from_file_location("user_evaluator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load evaluator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "evaluate"):
        raise AttributeError(f"Evaluator at {path} does not define an evaluate() function")
    return module.evaluate


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


def run_multiverse(
    multiverse: Multiverse,
    evaluator: Callable[[dict], dict],
    output_path: Path,
    mode: str = "auto",
    max_cells: int = 1000,
    seed: int = 42,
    verbose: bool = True,
) -> None:
    """Run the evaluator over the multiverse and write results to CSV.

    Modes:
      "full":         enumerate every cell
      "main_effects": vary one axis at a time, others at default
      "sample":       random sample of max_cells cells
      "auto":         "full" if total <= max_cells, else "main_effects"
    """
    total = multiverse.total_cells
    main_count = multiverse.main_effects_count

    if mode == "auto":
        mode = "full" if total <= max_cells else "main_effects"

    if mode == "full":
        spec_iter = multiverse.specifications()
        n_specs = total
    elif mode == "main_effects":
        spec_iter = multiverse.main_effects_specifications()
        n_specs = main_count
    elif mode == "sample":
        spec_iter = multiverse.sample_specifications(max_cells, seed=seed)
        n_specs = min(max_cells, total)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    if verbose:
        print(f"  Running {n_specs} specifications (mode: {mode}, total grid size: {total})")

    # Determine output columns by running the first spec.
    axis_names = [axis.name for axis in multiverse.axes]
    rows: list[dict[str, Any]] = []
    result_keys: list[str] = []
    saw_error: bool = False

    for i, spec in enumerate(spec_iter, 1):
        try:
            result = evaluator(spec)
        except Exception as e:
            result = {"error": f"{type(e).__name__}: {e}"}
            saw_error = True
        if not result_keys:
            result_keys = list(result.keys())
        # If a later result has new keys (e.g., error appears after some successes), extend.
        for k in result.keys():
            if k not in result_keys:
                result_keys.append(k)
        row = {**spec}
        for k in result_keys:
            row[k] = result.get(k)
        rows.append(row)
        if verbose and i % max(1, n_specs // 20) == 0:
            print(f"    {i}/{n_specs} done")

    # Ensure "error" column is always written when any cell errored, even if
    # the first successful result didn't include it.
    if saw_error and "error" not in result_keys:
        result_keys.append("error")

    # Write CSV.
    if not rows:
        print("Warning: no specifications ran", file=sys.stderr)
        return
    fieldnames = axis_names + result_keys
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    if verbose:
        print(f"  ✓ Wrote {len(rows)} rows to {output_path}")


def summarize(csv_path: Path, coef_col: str = "coefficient") -> None:
    """Print a quick text summary of the multiverse results.

    Reports range, IQR, share of significant results, and the cells that
    produced the most extreme results.
    """
    rows: list[dict[str, str]] = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("No results to summarize.")
        return
    coefs: list[float] = []
    for row in rows:
        v = row.get(coef_col, "")
        if v in ("", None):
            continue
        try:
            coefs.append(float(v))
        except ValueError:
            continue
    if not coefs:
        print(f"No numeric values found in column '{coef_col}'")
        return
    coefs.sort()
    n = len(coefs)
    median = coefs[n // 2]
    q1 = coefs[n // 4]
    q3 = coefs[(3 * n) // 4]
    print(f"\n  Specification curve summary ({n} cells, column='{coef_col}'):")
    print(f"    min:    {coefs[0]:.4f}")
    print(f"    Q1:     {q1:.4f}")
    print(f"    median: {median:.4f}")
    print(f"    Q3:     {q3:.4f}")
    print(f"    max:    {coefs[-1]:.4f}")
    print(f"    range:  {coefs[-1] - coefs[0]:.4f}")
    print(f"    IQR:    {q3 - q1:.4f}")
    # Crude significance check: count rows where p_value < 0.05 if column exists.
    pvals = [
        float(r.get("p_value", "nan"))
        for r in rows
        if r.get("p_value") not in ("", None, "nan")
    ]
    pvals = [p for p in pvals if not (p != p)]  # filter NaN
    if pvals:
        sig = sum(1 for p in pvals if p < 0.05)
        print(f"    p<0.05: {sig}/{len(pvals)} ({100*sig/len(pvals):.1f}%)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--decisions", type=Path, default=Path("decisions.jsonl"),
                   help="Path to decisions.jsonl (default: ./decisions.jsonl)")
    p.add_argument("--grid", type=Path, action="append", default=[],
                   help="Methodology grid YAML to compose. Can be given multiple times.")
    p.add_argument("--evaluator", type=Path, required=True,
                   help="Path to a Python file defining evaluate(spec) -> dict")
    p.add_argument("--output", type=Path, default=Path("multiverse_results.csv"),
                   help="Output CSV path")
    p.add_argument("--mode", choices=["auto", "full", "main_effects", "sample"],
                   default="auto", help="Sampling strategy when grid is large")
    p.add_argument("--max-cells", type=int, default=1000,
                   help="Cap on cells in auto/sample mode")
    p.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    p.add_argument("--dry-run", action="store_true",
                   help="Show grid size and proposed run plan; don't execute")
    p.add_argument("--summarize", action="store_true",
                   help="Print a summary of results after running")
    p.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = p.parse_args(argv[1:])

    # Load axes
    axes: list[Axis] = []
    decision_axes = load_decisions(args.decisions)
    if decision_axes:
        axes.extend(decision_axes)
        if not args.quiet:
            print(f"→ Loaded {len(decision_axes)} axis(es) from {args.decisions}")
    for grid_path in args.grid:
        grid_axes = load_grid(grid_path)
        axes.extend(grid_axes)
        if not args.quiet:
            print(f"→ Loaded {len(grid_axes)} axis(es) from {grid_path}")

    if not axes:
        print("Error: no axes loaded. Provide --decisions and/or --grid.", file=sys.stderr)
        return 1

    multiverse = Multiverse(axes=axes)
    if not args.quiet:
        print(f"\n  Multiverse: {len(axes)} axes, {multiverse.total_cells} total cells")
        print(f"    Main-effects subset: {multiverse.main_effects_count} cells")

    if args.dry_run:
        print("\n  Axes:")
        for axis in axes:
            print(f"    - {axis.name}: {len(axis.values)} values ({axis.source})")
            for v in axis.values:
                marker = " [default]" if v == axis.default else ""
                print(f"        {v}{marker}")
        return 0

    # Load evaluator
    evaluator = load_evaluator(args.evaluator)

    # Run
    run_multiverse(
        multiverse=multiverse,
        evaluator=evaluator,
        output_path=args.output,
        mode=args.mode,
        max_cells=args.max_cells,
        seed=args.seed,
        verbose=not args.quiet,
    )

    if args.summarize:
        summarize(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
