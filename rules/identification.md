# Rule: identification

When discussing or planning identification, these constraints apply.

## Non-negotiable steps per methodology

For each empirical methodology, certain identification questions cannot be skipped, regardless of how much pressure exists to move quickly.

- **DiD (any variant)**: parallel trends evidence (visual, leads test, or formal). For staggered designs: which estimator (Callaway-Sant'Anna, Sun-Abraham, BJS, de Chaisemartin–D'Haultfœuille). Anticipation effects discussion. Defining the never-treated control group.
- **IV / 2SLS**: exclusion restriction argument (institutional, not just an assertion). Relevance: first-stage F-statistic with an effective-F or weak-IV-robust alternative (Olea-Pflueger, Anderson-Rubin). Monotonicity if heterogeneous effects matter.
- **RDD**: bandwidth choice and procedure (CCT, Imbens-Kalyanaraman, manual robustness). McCrary or rdd-density manipulation test. Donut hole if appropriate. Visual evidence of discontinuity in treatment.
- **RCT**: power calculation (ex-ante, even if approximate). Pre-analysis plan. Balance table with a joint test. Attrition analysis (Lee bounds if attrition is non-trivial). SUTVA violations consideration.
- **OLS with FE**: identification source must be named explicitly (within-unit variation in X uncorrelated with within-unit variation in unobservables). The "controls" framing is insufficient on its own.
- **Synthetic control**: pre-period fit diagnostic, donor pool justification, placebo tests in time and space.
- **Structural / theory-mapped**: parameter identification source, target moments, sensitivity to alternative model specifications.

## Identification choices are user-owned

Suggest options. Lay out trade-offs. Do not decide on the user's behalf. If a user says "we'll deal with that later," push back: it is cheap to lock identification choices early and expensive to retrofit them after results exist.

## Discussion mode is required

Identification phases use full discussion mode. Even if the GSD config has `discuss_mode: assumptions`, identification work must use full back-and-forth. Read METHODOLOGY.md to determine if the current phase is identification-related; if so, override the config default.

## Surface known weaknesses

If the methodology has a known weakness (naive TWFE for staggered adoption, weak instrument with t > 2 but F < 10, RDD with manipulation evidence at the cutoff, RCT with > 20% attrition), name it explicitly. Do not soft-pedal because the work is already done. The identification-checker emits a `warning` test failure and the plan documents the deviation.

## When the user pushes back

Disagreement is fine. The discussion command exists for that. But do not silently accept "the assumption holds" without asking how the user knows. The right response to assertion is investigation, not acceptance.
