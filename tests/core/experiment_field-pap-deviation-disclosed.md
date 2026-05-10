# Deviations from pre-analysis plan are disclosed

**Methodology:** experiment_field
**Scope:** paper
**Severity:** blocker
**Clarity:** deterministic

## Criterion

If a pre-analysis plan (PAP) is registered for the paper (`prereg.url` is set in `METHODOLOGY.md`), the paper contains an explicit disclosure of any deviations from the registered plan. Analyses not in the PAP are clearly labeled "exploratory" and distinguished from pre-specified analyses.

## How to check

1. Read `METHODOLOGY.md`. Check whether `prereg.url` is non-empty.
2. If `prereg.url` is empty, this test is `NOT-APPLICABLE` (the paper is not pre-registered).
3. If `prereg.url` is set:
   - Search the manuscript for a section titled "Deviations from pre-analysis plan", "Departures from PAP", "Pre-specified vs. exploratory analyses", or similar.
   - The section should:
     - Explicitly state whether deviations exist.
     - If deviations exist: list each, explain why, and note which results are now exploratory.
     - If no deviations: state explicitly "all analyses follow the pre-registered plan."
4. Additionally, scan the results sections for analyses. Each analysis should be either:
   - Cited to the PAP (e.g., "as pre-specified in our PAP, we estimate equation (3)…")
   - Labeled exploratory (e.g., "in an exploratory analysis, we examine…")
5. The PAP is fetched (or referenced via the hash in STATE.md) and compared against the paper's analyses to detect undisclosed deviations.

## Pass condition

PASS if all are present:
- A "Deviations" section exists (or an explicit "no deviations" statement).
- Every analysis in the paper is either pre-specified-and-cited or labeled exploratory.
- The pre-registered hash in `METHODOLOGY.md` matches the PAP file hash (integrity check — the PAP wasn't silently updated).

FAIL if:
- Pre-registration is set but no deviations section exists.
- The paper presents analyses not in the PAP without labeling them exploratory.
- The PAP hash doesn't match (suggests the PAP was edited after registration without disclosure).

## Fail handling

The fix plan should:
1. Compare the registered PAP to the paper's analyses, line by line. Identify:
   - Analyses in the PAP not in the paper (omissions)
   - Analyses in the paper not in the PAP (additions)
   - Analyses in both with different specifications (modifications)
2. Add a "Deviations from pre-analysis plan" section to the paper covering all three categories.
3. For each deviation, write 1–3 sentences: what changed, why, and what the implication is for interpretation.
4. Flag exploratory analyses inline in the paper (footnotes or section labels).

If the PAP hash doesn't match, that's a more serious issue — the user must reconcile (was the PAP updated post-registration? was the hash recorded incorrectly?). Surface this for human review before any auto-fix.

## References

- Olken (2015), "Promises and perils of pre-analysis plans", *JEP* — overview of PAP discipline.
- AEA RCT Registry guidelines on amendments and deviations.
- Christensen & Miguel (2018), "Transparency, reproducibility, and the credibility of economics research", *JEL*.
