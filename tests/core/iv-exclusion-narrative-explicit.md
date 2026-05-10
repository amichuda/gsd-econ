# Exclusion restriction is argued in prose, not just asserted

**Methodology:** iv
**Scope:** paper
**Severity:** blocker
**Clarity:** heuristic

## Criterion

The paper contains a substantive prose argument for why the instrument satisfies the exclusion restriction. Asserting "Z affects Y only through X" without engaging with specific alternative channels is insufficient.

## How to check

1. Locate the IV section of the paper (typically in Section 3 or 4, often labeled "Identification" or "Empirical Strategy").
2. Find the discussion of the instrument and exclusion.
3. Evaluate whether the discussion:
   - Names at least 2 specific alternative channels through which Z could affect Y directly (i.e., not through X)
   - For each named channel, presents either an argument it doesn't apply, evidence ruling it out, or a robustness check addressing it
   - Acknowledges remaining uncertainty rather than claiming the restriction is settled

If the paper presents instrument-source variation that is "natural" (e.g., weather, distance, historical institutions), the bar is the same — naturalness is not an argument for exclusion, only for relevance.

## Pass condition

The verifier finds prose that:
- Discusses ≥ 2 specific alternative channels by name
- Engages substantively with each (argument, evidence, or robustness)
- Distinguishes the relevance argument from the exclusion argument

If only the relevance argument is made (i.e., "Z is correlated with X because..."), the test FAILS — relevance is necessary but not sufficient.

If the discussion is limited to a single sentence assertion ("we assume Z is excluded"), the test FAILS.

If the paper engages with one alternative channel deeply but ignores other obvious ones, the test PASS-PROVISIONAL — the verifier surfaces this for human judgment, since the threshold for "obvious" is contextual.

## Fail handling

The fix plan should request the authors:
1. Identify 2–3 most plausible alternative channels for direct Z→Y effects in their context
2. For each, write a paragraph addressing it (argument, evidence, or planned robustness)
3. If a channel can't be ruled out, propose a robustness specification (e.g., controlling for a proxy of the alternative channel, or a placebo using a unit where Z varies but the alternative channel doesn't)

The fix plan does NOT require authors to "prove" the exclusion holds — that's impossible. It requires substantive engagement with the threats.

## References

- Angrist & Pischke (2009), *Mostly Harmless Econometrics*, Ch. 4 — exclusion restrictions and IV identification.
- Conley, Hansen & Rossi (2012), "Plausibly Exogenous", *Restat* — sensitivity analysis when exclusion is approximately satisfied.
- Mellon (2024) — review of papers using rainfall as an instrument; documents the proliferation of channels rainfall affects beyond the named one. Cautionary tale for "natural" instruments.
