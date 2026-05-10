# Multiple-testing correction applied for multiple primary outcomes

**Methodology:** universal
**Scope:** paper
**Severity:** warning
**Clarity:** heuristic

## Criterion

When the paper has multiple primary outcomes (≥ 3 by default), it applies a multiple-testing correction (FWER or FDR) and reports adjusted p-values or q-values alongside unadjusted ones. Single primary outcomes don't require this; nor do papers where the secondary outcomes are clearly labeled exploratory.

## How to check

1. Identify the primary outcome(s):
   - Read `REQUIREMENTS.md` for declared primary outcomes.
   - Cross-reference with the paper's main results table.
2. Count primary outcomes:
   - 1 primary: test NOT-APPLICABLE.
   - 2 primary: test surfaces with WARNING; 2 outcomes is borderline.
   - 3+ primary: multiple-testing correction expected.
3. If 3+ primary outcomes, scan for:
   - **Family-Wise Error Rate (FWER) correction**: Bonferroni, Holm, Romano-Wolf step-down. Reports an adjusted p-value or family-wise critical value.
   - **False Discovery Rate (FDR) correction**: Benjamini-Hochberg, Anderson (2008) sharpened q-values. Reports a q-value.
   - **Index summary**: pre-specified mean-effects index across the family (Anderson 2008 standardized index, or Kling-Liebman-Katz). Reports the index point estimate and SE.
4. Each table with multiple primary outcomes should report adjusted alongside unadjusted statistics.

## Pass condition

PASS if any of:
- Single primary outcome (NOT-APPLICABLE).
- Multiple primary outcomes with FWER or FDR correction reported.
- Multiple primary outcomes summarized via a pre-specified mean-effects index.

PASS-PROVISIONAL if:
- 2 primary outcomes and no correction. Verifier surfaces for user judgment (some fields treat 2 as not requiring correction).

FAIL if:
- 3+ primary outcomes and no correction or index reported.
- The paper claims significance based only on unadjusted p-values for ≥ 3 primary tests.

## Fail handling

The fix plan should:
1. Decide the family of tests for correction (the primary outcomes from REQUIREMENTS.md, possibly grouped by domain).
2. Apply one correction:
   - **Romano-Wolf step-down** (preferred for FWER, accounts for dependence): `rwolf` in Stata, `wyoung` package or hand-rolled in R via `multcomp` or bootstrapping.
   - **Anderson sharpened q-values** (preferred for FDR with dependence): hand-rolled or via `qvalue` package in R.
   - **Bonferroni** (most conservative, easy): adjust each p-value by × number of tests.
3. Report adjusted alongside unadjusted in the main table.
4. In the methods section, briefly explain the family definition and correction method.

## References

- Anderson (2008), "Multiple Inference and Gender Differences in the Effects of Early Intervention", *JASA* — sharpened q-values and standardized index.
- Romano & Wolf (2005), "Stepwise multiple testing as formalized data snooping", *Econometrica*.
- List, Shaikh, Xu (2019), "Multiple hypothesis testing in experimental economics", *Experimental Economics* — practical guide.
- Benjamini & Hochberg (1995), "Controlling the false discovery rate", *JRSS-B* — original FDR.
