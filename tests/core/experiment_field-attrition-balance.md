# Differential attrition is balanced across treatment arms

**Methodology:** experiment_field
**Scope:** paper
**Severity:** blocker
**Clarity:** deterministic

## Criterion

For any field experiment with attrition between baseline and endline, the paper reports a test of differential attrition across treatment arms. If attrition is differential, the paper either bounds the treatment effect under attrition assumptions (Lee bounds, Manski bounds) or addresses the issue with a formal correction.

## How to check

1. Locate the sample size at baseline (typically Table 1, summary statistics).
2. Locate the sample size at endline / analysis (typically the main results table).
3. Compute the attrition rate by arm:
   - Treatment: (N_baseline_T − N_endline_T) / N_baseline_T
   - Control: (N_baseline_C − N_endline_C) / N_baseline_C
4. Look for one of:
   - A paragraph in the methods or data section reporting the per-arm attrition rates and a test of differential attrition (chi-squared, Fisher exact, or t-test on attritor indicator).
   - A table (often labeled "Attrition" or "Sample composition") with per-arm rates and a test.
   - In the robustness section, Lee (2009) bounds or similar attrition-adjusted analysis.
5. Check that the differential attrition test reports the p-value clearly.

## Pass condition

PASS if all are present:
- Per-arm attrition rates reported.
- A formal differential attrition test is run AND its p-value is reported AND p > 0.10 (no evidence of differential attrition).
- OR: differential attrition is detected (p ≤ 0.10) and Lee bounds (or similar) are reported.

FAIL if:
- Attrition is not reported at all.
- Attrition is mentioned but no formal differential test is performed.
- Differential attrition is detected and no bounding analysis is performed.

## Fail handling

The fix plan should:
1. Compute per-arm attrition rates.
2. Run a differential attrition test:
   - Stata: `ttest attritor, by(treatment)` or `regress attritor treatment, robust`
   - R: `lm(attritor ~ treatment, data = baseline_sample)`
3. If p < 0.10:
   - Implement Lee (2009) bounds: trim the higher-retention arm to match the lower-retention arm's rate, in both directions, to bound the treatment effect.
   - Stata: `leebounds`. R: hand-rolled or `attrition` package.
4. Add a paragraph in the methods or results section reporting the rates, the test, and (if applicable) the bounds.

## References

- Lee (2009), "Training, Wages, and Sample Selection", *Restud* — the bounding approach.
- Ghanem, Hirshleifer, Kédagni (2023), "Sharp Sensitivity Analysis for Inverse Propensity Weighting" — modern attrition correction.
- Karlan & Appel (2016), *Failing in the Field* — chapter on attrition in field experiments, common patterns.
