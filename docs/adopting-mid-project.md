# Adopting gsd-econ on a paper that's already in flight

You don't need a fresh project. The single entry point `/gsd-new-paper` supports two modes — `--new` for a blank slate, `--adopt` for retrofitting an existing manuscript and codebase. If you don't pass a flag, the command auto-detects.

## Where adoption pays off

- **Robustness round before R&R.** Main results locked, robustness battery still being built. Each robustness column becomes one atomic task; RUT tests gate them.
- **Coauthor handoff.** Coauthor sends you their analysis branch; you need to verify before merging. `/gsd-test-paper` against their tree gives you a structured report.
- **Pre-submission audit.** Draft is "done" but you want a structured adversarial review before the editor's decision lands. `/gsd-referee-sim` plus `/gsd-test-paper --severity blocker` runs without requiring you to refactor anything.
- **Post-acceptance, pre-replication-archive.** The replication package is the artifact most likely to fail real scrutiny. The submission flow's smoke test catches "doesn't reproduce" before the journal does.
- **Inheriting a project.** Postdoc takes over an advisor's half-finished paper. The discussion phase forces a methodology declaration that surfaces what was actually decided vs assumed.

## Where adoption is a poor fit

- **Final week before submission.** Don't introduce new tooling under deadline pressure.
- **You already trust your pipeline.** If `make all` reproduces, the replication archive is clean, and you're confident in identification — you don't need this. The framework's value is concentrated in cases where workflow is fragmenting under cognitive load.
- **Pure theory papers.** The integration value is in empirical pipelines (data → identification → robustness → replication). For theory, the RUT integration is mostly inert.

## What `--adopt` does

When you run `/gsd-new-paper --adopt` (or let auto-detect choose it), the command runs read-only over your existing manuscript and codebase and writes only planning artifacts under `.planning/`:

1. **Inventories** the manuscript and codebase. Looks at what packages you use, what tables exist, what regression specifications appear in your code.
2. **Infers** a methodology declaration — primary identification strategy, cluster level, SE method, sample restrictions — from your code and prose. Shows the inferred declaration to you for editing.
3. **Runs the project-level literature scout** by spawning `econ-researcher` with the manuscript's abstract/introduction, inferred contribution, inferred methodology, and existing bibliography. This writes `.planning/research/literature-scout.md`, the same artifact greenfield projects get before identification discussion.
4. **Reconstructs `REQUIREMENTS.md`** by walking through the manuscript with you. Hypotheses already published become LOCKED; anything you're still revisiting stays OPEN.
5. **Backfills `ROADMAP.md`** with a minimal "[COMPLETED PRE-ADOPTION]" tag for each finished phase. Doesn't pretend to reconstruct phases that already happened — just records that they did.
6. **Writes an adoption marker to `STATE.md`** with a timestamp. This is the audit trail. If a referee later asks "when did you commit to specification X?", you can answer "before adoption, see commit history" without false claims.
7. **Runs `/gsd-test-paper --severity blocker --severity warning`** to produce a baseline report. Surfaces what passes (encouraging — you've done good work) and what fails (the retrofit gaps).
8. **Asks you to triage each failure** as: address (real defect), acknowledge (won't fix this round, log to STATE.md), or exclude (add to `METHODOLOGY.test_exclusions` with justification).
9. **Hands off** to the right next command for your current phase.

## What `--adopt` does not do

- **Does not modify your manuscript or code.** Only writes to `.planning/`.
- **Does not retroactively run fix plans for completed work.** Your call which gaps to address.
- **Does not relitigate identification choices.** If your DiD paper used naive TWFE for staggered treatment, the framework will flag it (because it should), but won't auto-rewrite.
- **Does not silently overwrite existing planning docs.** If you've used a prior version of gsd-econ, it asks before merging.
- **Does not silently skip the literature scout.** If you defer it, adoption writes an explicit stub at `.planning/research/literature-scout.md` so downstream commands know the context is incomplete.

## A typical adoption session

```
$ cd my-paper-in-progress
$ git submodule add https://github.com/<you>/gsd-econ vendor/gsd-econ
$ git submodule add https://github.com/rdahis/research-unit-tests vendor/research-unit-tests
$ bash vendor/gsd-econ/scripts/install.sh

# in your runtime
> /gsd-new-paper

  → Auto-detected: --adopt mode
    Found: paper/main.tex (8,400 words, 6 sections)
           code/04_main.R (uses fixest::feols with cluster = "village")
           tables/ (7 .tex tables)
           figures/ (4 .pdf figures)
    Continue in --adopt mode? [yes/override to --new]

> yes

  → Inferred methodology:
      primary: did
      secondary: [ols, iv]
      cluster_level: village
      se_method: cluster-robust at village
      sample: rural households, 2010-2018
    Look correct? Edit anything?
...
```

About 30–60 minutes of interactive work, depending on manuscript complexity. The output is a `.planning/` directory that reflects what your project actually is — not what it would be if you'd started fresh — plus a baseline test report with concrete next steps.

## The honest caveat

Adoption will probably surface a methodological choice you made early and half-justified. The framework's discussion layer would have flagged it if you'd used the framework from the start. This is uncomfortable but also exactly the value: better to discover it now than in referee report 2.

If you don't want that, don't adopt mid-project.

## After adoption

Behavior is identical to a greenfield project from this point forward. Each new phase goes through `/gsd-discuss-identification` → `/gsd-plan-empirics` → `/gsd-execute-phase` → `/gsd-verify-replication`. Each commit is atomic. Each phase produces a `VERIFICATION.md`. Submission goes through `/gsd-submit-paper`.

The pre-adoption commit history remains untouched and continues to be the source of truth for what existed when the workflow was engaged.
