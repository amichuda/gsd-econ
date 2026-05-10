# Conley standard errors used when units have geographic structure

**Methodology:** did
**Scope:** paper
**Severity:** warning
**Clarity:** heuristic

## Criterion

When treatment and control units are spatially distributed and shocks could be spatially correlated (which is most empirical settings with geographic units), the paper either uses Conley (1999) standard errors with a stated bandwidth or argues explicitly why standard cluster-robust inference suffices.

## How to check

1. Identify the spatial structure of the data: are units geographic (counties, villages, districts, schools nested in neighborhoods)?
2. If yes, scan the paper for the SE specification:
   - Standard cluster-robust at the geographic unit level
   - Two-way clustered (geographic × time)
   - Conley SEs with a specified spatial bandwidth (e.g., 50km, 100km, 200km)
   - Spatial HAC (Driscoll-Kraay) for panel data with both spatial and serial correlation
3. Look for an argument about why the chosen SE structure is appropriate. Examples of valid arguments for *not* using Conley:
   - "Treatment varies at the state level; states are large enough that within-state spatial correlation is captured by state clustering."
   - "Two-way clustering by district and year subsumes the relevant spatial dependence given the timing of treatment."
4. The test is `warning` severity (not `blocker`) because the right SE structure is context-dependent and reasonable researchers can disagree. The test surfaces the question; the user judges.

## Pass condition

PASS if any of:
- Conley SEs are reported (any reasonable bandwidth)
- Two-way clustering subsumes spatial dependence and the paper briefly justifies
- Treatment is exogenous at a level coarser than the spatial correlation scale, with brief justification
- Robustness section reports SEs under multiple structures (the kitchen-sink approach)

PASS-PROVISIONAL if:
- The data has obvious spatial structure (units within ~100km of each other) AND the paper uses single-level clustering AND no justification is provided. Verifier surfaces for user ack.

FAIL if:
- The data has obvious spatial structure AND single-level clustering is used AND no justification provided AND the user does not accept on review.

## Fail handling

The fix plan typically requests one of:
1. Recompute SEs with Conley (1999) at 50km, 100km, 200km bandwidths; report the most conservative or all three.
2. Add a footnote in the methods section justifying why the current SE structure is sufficient.
3. Robustness check: re-estimate with Driscoll-Kraay if the panel is long.

Implementations:
- Stata: `acreg`, `conleyreg`, or `ols_spatial_HAC` (user-written).
- R: `conleyreg` package, or hand-rolled with the `spdep` and `sandwich` packages.

## References

- Conley (1999), "GMM estimation with cross sectional dependence", *Journal of Econometrics*.
- Driscoll & Kraay (1998), "Consistent covariance matrix estimation with spatially dependent panel data", *Review of Economics and Statistics*.
- Colella, Lalive, Sakalli, Thoenig (2019), "Inference with arbitrary clustering", IZA WP — surveys options.
