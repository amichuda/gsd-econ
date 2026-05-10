# Methodology declaration for the example paper

```yaml
primary: did

secondary:
  - ols       # for descriptive baselines and Phase 2 stylized facts
  - iv        # only as robustness: rainfall as IV for shock realization timing

scope: paper

target_journal: jae

prereg:
  required: false
  url: ""
  hash: ""
  submitted_at: ""

test_inclusions:
  # Force-load Conley SE warning even though it's a `did` test —
  # we want this to surface explicitly given Uganda district contiguity.
  - did-conley-ses-when-spatial

test_exclusions:
  # No exclusions for this project. If we needed to add one:
  # - id: experiment_field-pap-deviation-disclosed
  #   reason: "Not applicable; observational paper, no PAP."
  # (But this would be redundant — the methodology filter already excludes
  # experiment_field tests since methodology is `did`.)

replication:
  reproduces_in: 90
  language: R
  data_access: restricted   # UBOS data requires application; synthetic substitute provided
```

## Notes on this declaration

- **`primary: did`** locks the workflow into DiD-flavored questions (parallel trends, staggered estimator, cluster level) at every discuss/plan/verify step.
- **`secondary: [ols, iv]`** loads OLS tests (e.g., `universal-clustered-ses-justified` is universal anyway) and IV tests for the robustness section. The `iv-first-stage-f-stat` and `iv-weak-instrument-robust-inference` tests will gate the IV robustness specification when it's executed.
- **`prereg.required: false`** — observational paper. The experiment_field tests (attrition, PAP deviation) won't load.
- **`test_inclusions: [did-conley-ses-when-spatial]`** — even though this is a `warning` and would load by default, listing it here ensures it's *not* accidentally suppressed if someone adjusts methodology tags later. Belt-and-suspenders.
- **`replication.data_access: restricted`** signals to `/gsd-submit-paper` that the replication archive will not include raw UBOS data; a synthetic substitute and access instructions are required instead.
