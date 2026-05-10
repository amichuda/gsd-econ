# Cluster level for SEs is stated and matches the variation

**Methodology:** universal
**Scope:** paper
**Severity:** warning
**Clarity:** deterministic

## Criterion

The paper states the cluster level used for standard errors and the choice is consistent with the level of treatment assignment or the level of within-unit correlation in shocks. Default OLS SEs (heteroskedasticity-only) are not used when the design implies clustering.

## How to check

1. Search the methods section and table footnotes for the cluster specification:
   - Phrases like "standard errors clustered at the X level", "cluster-robust at X", "two-way clustered (X, Y)"
2. Check the table footnotes for every regression table — each should state cluster level (or explicitly state homoskedastic / robust SEs).
3. Compare the cluster level to:
   - The level of treatment assignment (e.g., if treatment is village-level, cluster at village or coarser)
   - The level of plausible within-unit correlation (e.g., student outcomes within a class share teacher-level shocks → cluster at class or school)
4. Flag mismatches:
   - Treatment at village level, SEs clustered at individual: too granular (under-conservative).
   - Treatment at individual level, SEs clustered at country (with N=4 countries): too coarse with too few clusters.
5. Also check: if the paper has a panel structure with serial correlation, are SEs clustered at the unit level (panel-robust)?

## Pass condition

PASS if all are present:
- Cluster level is stated in the methods or table footnotes for every regression.
- The cluster level is consistent with the design (treatment assignment level OR coarser).
- For panel data with potential serial correlation, clustering is at the unit level (or higher).

PASS-PROVISIONAL if:
- Cluster level is stated but the choice is non-obvious — verifier surfaces for user judgment.

FAIL if:
- Cluster level is not stated anywhere (treated as homoskedastic SEs by default).
- Cluster level is too granular (clustering at the individual level when treatment varies at the village level, in a setting with within-village correlation).

## Fail handling

The fix plan should:
1. Determine the appropriate cluster level based on:
   - Level of treatment assignment
   - Level of within-unit correlation in shocks (if different)
2. If both apply, two-way cluster.
3. Update the regression call to use the chosen cluster level:
   - R fixest: `feols(y ~ x | fe, data = df, cluster = "village")`
   - R sandwich: `vcovCL(model, cluster = ~village)`
   - Stata: `regress y x, vce(cluster village)` or `, vce(cluster village##year)`
   - Python statsmodels: `cluster` argument or `linearmodels.iv` cluster_entity option
4. Add a footnote to each table stating: "Standard errors clustered at the [village] level in parentheses."
5. If cluster count is small (< 30), use cluster-bootstrap or CR2 (Bell-McCaffrey) for inference.

## References

- Cameron & Miller (2015), "A practitioner's guide to cluster-robust inference", *Journal of Human Resources*.
- Abadie, Athey, Imbens, Wooldridge (2023), "When should you adjust standard errors for clustering?", *QJE* — modern framework distinguishing design-based from sampling-based clustering.
- MacKinnon, Nielsen, Webb (2023), "Cluster-robust inference: A guide to empirical practice", *Journal of Econometrics*.
