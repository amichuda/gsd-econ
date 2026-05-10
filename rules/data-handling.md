# Rule: data handling

Constraints on data files at every stage.

## `data/raw/` is sacred

Never modify a file in `data/raw/`. Not to fix encoding issues, not to remove obvious typos, not for any reason. Corrections happen in cleaning scripts whose output goes elsewhere. The raw directory's purpose is auditability — anyone replicating must be able to start from exactly the same inputs as you.

If raw data needs to be acquired for the first time, write a script that downloads or queries it, document the source and access date, and store the script alongside the data. Manual one-off downloads are acceptable but document them in METHODOLOGY.md so future-you and replicators can reproduce.

## Cleaned data goes to `data/clean/` (or `data/derived/`)

Always programmatically generated, never hand-edited. The full path from raw to clean must be re-runnable end-to-end. If a cleaning step requires manual intervention (deduplicating an entity-name list, for example), the manual decisions go into a small CSV checked into the repo and the cleaning script reads from it — that way the manual decisions are version-controlled and re-runnable.

## Sensitive data discipline

Never commit data files that contain PII (names, exact addresses, ID numbers, geocoordinates fine enough to identify individual households). If a working dataset has these, the cleaning step de-identifies before saving anywhere git can see.

If de-identification is non-trivial, the de-identified version is what lives in `data/clean/`; the raw version stays out of git entirely (in a parallel directory listed in `.gitignore`, or on encrypted external storage).

## Document everything in METHODOLOGY.md

Every data source: what is it, when was it acquired, what version, by what method, with what restrictions. A replicator should be able to reconstruct your data acquisition without asking you. If access is restricted (proprietary datasets, IRB-restricted), document that explicitly so they don't waste time looking.

## Sample restrictions are stated everywhere

The sample described in the data section, the methods section, each table footnote, and the robustness section must be the same sample. If a heterogeneity analysis legitimately uses a different subsample, that variation is explicitly flagged in the prose and the table footnote. Silent sample changes across tables are a `polish-consistency` finding — and a credibility failure.

## Don't silently drop observations

Every restriction (drop missing X, drop pre-2010, drop top-1% outliers) is reported. Either in the data section's filtering paragraph, in the table footnote, or both. The number of dropped observations and what they were is part of the audit trail.

## Reproducibility tier

A project should aim for reproducibility tier (in increasing order):

1. **Code runs end-to-end on the author's machine.**
2. **Code runs end-to-end on a clean checkout with documented dependencies.**
3. **Code runs in a container or virtualenv with pinned versions, requiring only the raw data input.**
4. **Code is reproducible from raw data download through final paper PDF, with no human intervention.**

Tier 3 is the default goal for any submission-ready paper. Tier 4 is the goal for replication archives.
