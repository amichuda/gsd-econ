# Weak-instrument-robust inference reported when first-stage F is low

**Methodology:** iv
**Scope:** paper
**Severity:** blocker
**Clarity:** deterministic

## Criterion

When the first-stage F-statistic falls below the threshold for valid classical IV inference (Lee, McCrary, Moreira, Porter 2022 — effective F ≥ 105 for AR-equivalent inference, or rule-of-thumb F ≥ 10 at minimum), the paper reports weak-instrument-robust confidence intervals (Anderson-Rubin, CLR, or tF-adjusted).

## How to check

1. Locate the first-stage statistics (typically in the main table or a dedicated first-stage table).
2. Read the F-statistic. Distinguish:
   - **Single endogenous regressor, single instrument**: standard F is fine.
   - **Multiple instruments**: report Sanderson-Windmeijer or Kleibergen-Paap rk Wald F (cluster-robust where applicable).
3. Apply thresholds:
   - **F ≥ 105**: classical inference is approximately valid (Lee et al. 2022). Test PASSES.
   - **10 ≤ F < 105**: classical inference may have coverage distortions. Test PASSES only if the paper additionally reports AR confidence intervals or applies the tF adjustment.
   - **F < 10**: classical inference is invalid. Test PASSES only if AR or CLR confidence intervals are reported as the primary inference, with classical only as supplementary.
4. Check that the reported F is cluster-robust if SEs are clustered.

## Pass condition

For every IV specification in the paper:
- The first-stage F (or appropriate multi-instrument analog) is reported in the same table or an adjacent one.
- If F < 105, weak-IV-robust inference is presented (AR, CLR, or tF).
- The robust CIs are clearly distinguished from classical CIs in the paper.

## Fail handling

If F is missing entirely: fix plan requests the authors compute and report the appropriate F-statistic.

If F is below threshold but no robust inference is reported: fix plan requests AR confidence intervals (preferred — distribution-free under weak instruments) or CLR. For Stata, `weakivtest` and `condivreg`. For R, `ivreg` package's `summary` or the `ivmodel` package.

If F is borderline (in 10–105) and only classical inference is reported: same as above — robust inference is no longer optional in this range, even if F ≥ 10.

## References

- Lee, McCrary, Moreira, Porter (2022), "Valid t-ratio Inference for IV", *AER* — the modern critical-value tables.
- Andrews, Stock & Sun (2019), "Weak Instruments in IV Regression: Theory and Practice", *Annual Review of Economics*.
- Stock & Yogo (2005) — the older threshold reference, superseded but still cited.
