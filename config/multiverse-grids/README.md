# Multiverse methodology grids

Templated parameter grids for common empirical designs. Each grid
enumerates contested methodology choices, with defaults, alternatives,
justifications, and citations.

`/gsd-multiverse` reads these grids and composes them with the
project's `decisions.jsonl` (which captures project-specific
data-cleaning choices) to produce the full specification-curve
multiverse.

## Available grids

| File | Design | Axes |
|------|--------|------|
| `rct.yaml` | Randomized Controlled Trial | 8 axes: SE clustering, stratum FE, controls, outcome definition, non-compliance, multiple testing, attrition, heterogeneity |
| `did.yaml` | Difference-in-Differences | 7 axes: estimator (CS/SA/dCDH/BJS/TWFE/stacked), control group, pre-trend window, SE clustering, honest DiD, event-study lags, controls |
| `iv.yaml` | Instrumental Variables | 6 axes: weak-IV inference, controls, SE clustering, exclusion-restriction test, shift-share inference, LATE interpretation |
| `rdd.yaml` | Regression Discontinuity | 8 axes: bandwidth, polynomial order, kernel, manipulation test, SE structure, sharp/fuzzy, mass-point handling, donut |

## Schema

Each grid is a YAML file:

```yaml
design: rct                # or did, iv, rdd, ...
version: "0.3.0"

axes:
  axis_name:
    description: "..."
    default: "<one of the alternatives>"
    alternatives:
      - "option_1"
      - "option_2"
      - "option_3"
    justification: |
      Multi-line prose explaining when each alternative is preferable.
    citations: ["author-year-shortform"]
    pap_relevance: high|medium|low
```

`pap_relevance` indicates how often the PAP fixes this dimension:
`high` means PAPs typically commit to it (e.g., SE clustering for an
RCT), `low` means it's typically left open (e.g., bandwidth radius
choice for a sensitivity sweep).

## Choosing a grid

`/gsd-multiverse` auto-detects the project's design from
`.planning/METHODOLOGY.md` if it can. If detection fails or the design
is mixed (e.g., DiD with IV for compliance), the command will ask
which grid to compose.

You can also pass `--grid <design>` explicitly:

```
/gsd-multiverse --grid did
/gsd-multiverse --grid did --grid iv      # Compose two grids
```

## Extending a grid

To add a new axis to an existing grid: edit the YAML, add an entry
following the schema. Re-run `/gsd-multiverse` and the new axis is
included.

To add a new design entirely (e.g., bunching estimators,
synthetic-control panels): copy the closest existing grid, rename,
and adjust. Submit a PR if you want it included upstream.

## Honest limits

These grids capture **commonly-contested choices**, not every choice
a creative referee could possibly raise. The intent is to cover the
80% case efficiently, not to enumerate the long tail. If your project
has design-specific concerns (a clever placebo test, a structural
parameter you want to vary), add them to `decisions.jsonl` so they
compose with the grid rather than living in the grid itself.

The citations are starting points, not exhaustive literature reviews.
Each cited paper has a long downstream literature; the citation is
meant as an anchor for further reading, not a complete reference list.
