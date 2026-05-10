# Sample restrictions are stated explicitly

**Methodology:** universal
**Scope:** paper
**Severity:** blocker
**Clarity:** deterministic

## Criterion

The paper states the sample used for each set of analyses, including any restrictions applied (eligibility, balance, observation window, exclusions). The paper documents how the analysis sample is constructed from the raw data, with N at each step.

## How to check

1. Locate the data section (typically Section 2 or 3).
2. Find a description of the sample. Look for:
   - The population of interest (e.g., "households with at least one child under 5")
   - Geographic/temporal scope (e.g., "rural districts in <country>, 2010–2018")
   - Eligibility criteria (e.g., "households with at least 12 months of survey participation")
   - Exclusions (e.g., "we drop the top 1% of income observations")
3. Look for a sample-construction table or figure tracking N from raw data → analysis sample. Common formats:
   - A "sample construction" table with rows for each restriction and resulting N
   - A flow chart (rare in econ but common in epi)
   - Inline prose describing each restriction with N
4. Check that the analysis sample N matches the N in the main results tables (this is also tested by `universal-tables-have-n-obs`, but here we check the upstream construction).
5. Check robustness or appendix sections for analyses on different samples (e.g., excluding some subgroup) — these should be clearly marked as such.

## Pass condition

PASS if all are present:
- The paper describes the population and sample selection prose.
- N is reported at each restriction step OR the start-and-end N is reported with restrictions clearly listed.
- The analysis sample N in the methods section matches the N in main results tables.
- Robustness analyses on different samples are explicitly noted.

FAIL if:
- The sample is described only as "our sample" without specifying restrictions.
- N at the restriction-construction step is missing.
- The analysis sample N is silently inconsistent across tables (e.g., Table 2 has N=10,500; Table 3 has N=10,389 with no explanation).

## Fail handling

The fix plan should:
1. Add a sample-construction subsection (typically in Section 2) with:
   - Starting universe and N
   - Each restriction applied, in order, with resulting N
   - Final analysis sample N
2. If multiple analysis samples exist (e.g., one for main, one for a heterogeneity cut), document each explicitly.
3. Cross-check that table Ns match the documented sample. If they don't, identify the source of the discrepancy and either reconcile or document.
4. Add an appendix table or figure showing the sample construction if it's complex.

## References

- Athey & Imbens (2017), "The state of applied econometrics: Causality and policy evaluation", *JEP* — emphasizes sample construction transparency.
- Brodeur, Cook, Heyes (2020), "Methods Matter: p-Hacking and Causal Inference in Economics", *AER* — documents how undisclosed sample restrictions enable p-hacking.
