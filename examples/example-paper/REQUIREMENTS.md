# Requirements

## Hypotheses

### Primary

H1. Mobile-money rollout to a rural district reduces the consumption response to weather shocks, measured as a smaller decline in non-food consumption following negative rainfall realizations.
- LOCKED-IN-PHASE-0
- Sign: negative coefficient on (rollout × shock) interaction

H2. The effect of rollout on smoothing operates through increased remittance receipts during shocks, measured by household-reported transfer income from non-resident relatives.
- LOCKED-IN-PHASE-0

### Secondary

H3. The smoothing effect is stronger for households with stronger baseline migration ties (more non-resident kin).
- LOCKED-IN-PHASE-0
- Heterogeneity check; hypothesis from Jack-Suri 2014

H4. Female-headed households see larger smoothing effects than male-headed (a hypothesis from the financial-inclusion literature).
- LOCKED-IN-PHASE-0
- Heterogeneity check; hypothesis from Demirgüç-Kunt et al. 2018

## Outcomes

### Primary outcome(s)

| Outcome | Operational definition | Construction | Status |
|---------|------------------------|--------------|--------|
| Non-food consumption response | Δ log(non-food cons) regressed on shock × rollout | UBOS UNHS panel: aggregated non-food category, deflated to 2010 UGX | LOCKED |
| Remittance receipts | Annual transfer income from non-resident kin | UBOS UNHS module H section, item code 11–14 | LOCKED |

### Secondary outcomes

| Outcome | Operational definition | Construction | Status |
|---------|------------------------|--------------|--------|
| Food consumption response | Same construction, food category | Items 1–10 of module H | LOCKED |
| Asset depletion (livestock) | Δ log(livestock value) | Module L | LOCKED |
| School attendance during shock | Indicator: any household child missed >1 month | Module E | OPEN |

## Sample

- Population: rural households in Uganda surveyed in UNHS 2009/10 and 2013/14 panels
- Frame: UBOS sampling frame, rural enumeration areas
- Eligibility: households surveyed in both rounds (panel attrition addressed in robustness)
- Expected N: ~6,400 households × 2 rounds = ~12,800 observations
- Status: LOCKED-IN-PHASE-0

## Treatment / variation source

- What varies: presence of an active mobile-money agent in the district (binary)
- Unit of variation: district (112 districts in Uganda)
- Source of variation: staggered rollout 2008–2014 driven by mobile carrier expansion strategy
- LOCKED-IN-PHASE-0

## Specification choices

### LOCKED

- Unit fixed effects: household
- Time fixed effects: round (2 rounds, so wave dummy)
- Cluster level: district (treatment level)
- SE method: cluster-robust at district
  - Robustness: Conley SEs at 100km, since districts are spatially contiguous
- Functional form: log on consumption (Box-Cox tested)
- Treatment definition: rollout date = first month with ≥ 1 active agent in district
- Shock definition: SPI-12 (standardized precipitation index, 12-month) below -1.0

### OPEN

- Staggered DiD estimator: TWFE vs Callaway-Sant'Anna vs Sun-Abraham — to be locked in Phase 3 after pilot estimation
- Whether to use district + year FE or district + month-of-year FE — depends on seasonality patterns to be examined in Phase 2
- Inclusion of Northern districts (post-LRA recovery) — open until balance check in Phase 3

## Robustness commitments

- [ ] Drop ever-treated controls (Callaway-Sant'Anna with not-yet-treated only)
- [ ] Alternative shock definitions (NDVI, temperature shock)
- [ ] Sample restriction to non-Northern districts (LRA recovery confound)
- [ ] Conley SEs at 50 / 100 / 200 km bandwidths
- [ ] Lee bounds for differential attrition
- [ ] Romano-Wolf adjustment for the four primary outcomes

## What this paper does NOT claim

- We do not claim mobile money causes general welfare gains; only consumption smoothing against shocks.
- We do not estimate the long-run effect of rollout (data ends 2014, well before mobile money saturation).
- We do not claim the same effects would hold in non-rural settings.
- We do not provide structural estimates of the consumption-smoothing parameter; the analysis is reduced-form.
