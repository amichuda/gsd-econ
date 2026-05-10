# Roadmap — Mobile money and consumption smoothing

Adapted from the default gsd-econ template. Phase 6 (Monte Carlo) is dropped (not a methods paper); Phase 3 is split into 3a and 3b given the staggered design's complexity.

---

## Phase 1 — Data acquisition and cleaning

**Goal.** Merge UBOS UNHS 2009/10 and 2013/14 household panels with district-level mobile-money rollout data (UCC) and weather (CHIRPS satellite rainfall, MOD13 NDVI). Produce a household-district-year analysis dataset.

**Inputs.**
- UBOS UNHS panels (restricted access)
- UCC mobile-money agent registry (district-month panel)
- CHIRPS rainfall (district-month, 1981–2014)
- MOD13 NDVI (district-month, 2000–2014)

**Outputs.**
- `data/clean/household_panel.parquet`
- `data/clean/district_rollout.parquet`
- `data/README.md`
- `code/01_clean.R`

**Tests.** `universal-sample-restrictions-stated`

---

## Phase 2 — Stylized facts

**Goal.** Document the rollout timeline, weather shock distribution, and baseline household consumption patterns. Set up Section 2 of the paper.

**Outputs.**
- `tables/01_rollout_timeline.tex`
- `tables/02_summary_stats.tex`
- `figures/01_rollout_map.pdf`
- `figures/02_shock_distribution.pdf`

**Tests.** `universal-tables-have-n-obs`, `universal-sample-restrictions-stated`

---

## Phase 3a — Identification: parallel trends

**Goal.** Estimate event-study specification with relative-time dummies. Show no pre-treatment trend in consumption response.

**Outputs.**
- `tables/03_event_study.tex`
- `figures/03_event_study.pdf` (the parallel-trends visualization)
- Identification subsection draft (Section 3.1)

**Tests.** `did-parallel-trends-plot` (heuristic-blocker), `universal-clustered-ses-justified`

---

## Phase 3b — Identification: estimator choice

**Goal.** Compare TWFE, Callaway-Sant'Anna, and Sun-Abraham estimators on the staggered rollout. Lock in the primary estimator based on heterogeneity diagnostics.

**Outputs.**
- `tables/04_estimator_comparison.tex`
- `figures/04_goodman_bacon_decomposition.pdf`
- Decision in `STATE.md`: which estimator becomes the primary spec

**Tests.** `did-staggered-heterogeneous-effects` (deterministic-blocker — must use a non-naive estimator if heterogeneity is detected)

---

## Phase 4 — Main specification

**Goal.** Run the locked specification with all four primary outcomes. Build Tables 5 and 6.

**Outputs.**
- `tables/05_main_consumption.tex`
- `tables/06_main_remittance.tex`
- `code/04_main.R`
- Section 4 draft

**Tests.** `universal-tables-have-n-obs`, `universal-clustered-ses-justified`, `universal-multiple-testing-corrected` (4 primary outcomes → Romano-Wolf required)

---

## Phase 5 — Robustness and heterogeneity

**Goal.** Address the robustness commitments from REQUIREMENTS.md. Document heterogeneity by migration ties and gender of head.

**Outputs.**
- `tables/07_robustness.tex`
- `tables/08_heterogeneity.tex`
- `tables/09_iv_robustness.tex` (rainfall as IV)
- `tables/10_conley_se.tex` (spatial-correlation robustness)

**Tests.**
- All Phase 4 tests
- `did-conley-ses-when-spatial` (warning-heuristic)
- `iv-first-stage-f-stat` (deterministic-blocker, for the IV robustness spec)
- `iv-weak-instrument-robust-inference` (deterministic-blocker, IV robustness spec)
- `iv-exclusion-narrative-explicit` (heuristic-blocker, IV robustness spec)

---

## Phase 6 — Tables and figures pipeline

**Goal.** Run `/gsd-tables-figures 6` to finalize all tables and figures in publication style. Resolve cross-references. House style consistent.

**Outputs.** All `tables/*.tex` and `figures/*.pdf` finalized.

**Tests.** `universal-tables-have-n-obs`, `universal-clustered-ses-justified`

---

## Phase 7 — Manuscript writing

**Goal.** Complete intro, related literature, conclusion, abstract. Polish all sections. Prepare for `/gsd-referee-sim`.

**Outputs.**
- `paper/manuscript.tex`
- `paper/online-appendix.tex`

**Tests.** None auto-loaded; `/gsd-referee-sim` runs after this phase.

---

## Phase 8 — Submission

**Goal.** Run `/gsd-submit-paper jae`. Build replication archive with synthetic data substitute (UBOS access requires application). Final referee-sim run.

**Outputs.**
- `submission/manuscript.pdf`
- `submission/online-appendix.pdf`
- `submission/cover-letter.pdf`
- `submission/replication/` (with synthetic data, instructions for actual data access)
- `submission/declarations/ai-use-disclosure.md`

**Tests.** `universal-replication-reproduces-results` (against synthetic data); all blocker tests across all phases must pass.
