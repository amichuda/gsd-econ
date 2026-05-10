# Rule: methodology integrity

Constraints on choosing, implementing, and modifying estimators and inference procedures.

## Estimator-level

- **No naive TWFE for staggered DiD.** If the user is doing staggered adoption, the plan uses Callaway-Sant'Anna, Sun-Abraham, BJS, or de Chaisemartin–D'Haultfœuille. If the user explicitly chooses naive TWFE despite warning, document the deviation in METHODOLOGY.md and proceed.
- **No 2SLS without weak-instrument-robust inference when the first-stage F is below 104.7** (the Lee 2022 cutoff for tF-corrected 5% test) — or below 10 by the older Stock-Yogo rule. Use Anderson-Rubin or Conditional Likelihood Ratio (CLR) as the primary inference. The point estimate is reported, but the t-test on it is not the headline.
- **No RDD with the default bandwidth alone.** Always present a bandwidth sensitivity (CCT plus at least one alternative). If the result depends on the bandwidth choice in a substantive way, that is a finding, not a footnote.
- **No "controls solve confounding."** Adding controls in OLS does not buy identification by itself. If the design is "OLS with controls," the identification claim must explicitly name the conditional independence assumption that's being made and what makes it plausible.

## Standard errors and inference

- **Cluster level is specified explicitly in every plan.** No silent defaults. If the design implies something non-obvious (two-way clustering, Conley spatial, multi-way nested), it goes in the plan, not in some helper script the executor finds later.
- **Multiple testing is corrected when relevant.** Family of hypotheses ≥ 5: report adjusted p-values (Bonferroni minimum, ideally Romano-Wolf or Westfall-Young). The "we report unadjusted p-values" choice is a defensible position, but it is a position that needs to be stated.
- **Few clusters → cluster-robust corrections.** Below ~30 clusters: CR2 standard errors with degrees-of-freedom correction (Imbens-Kolesar), not naive CR1. Below ~10: wild-cluster bootstrap.
- **Spatial correlation when units are spatially distributed.** Conley standard errors with an explicit cutoff (justified, not arbitrary), or HAC equivalent. The default of independent observations across spatial units is wrong by default.

## Reporting integrity

- **Headline coefficients in tables match prose.** When a regression result is referenced in the abstract, intro, or conclusion, the number must trace to the regression output. Drift between text and tables is a `polish-numbers` finding.
- **P-values and stars are consistent with the underlying SE.** If the SE is wild-cluster bootstrap, the p-value reported is from that bootstrap, not the t-test.
- **Robustness is not optional.** Every main-results phase has a corresponding robustness plan in the next phase. The `<gates>` of the main-results plan reference at least one robustness test from the registry.

## Mechanism vs main effect

- **Don't conflate the two.** The point estimate is the average effect; mechanism evidence is separate and identified separately. A heterogeneity table is suggestive of mechanism but does not identify it.
