# Adapting GSD: what we override and why

GSD ships a lot. We use most of it unchanged, override a few things, and ignore some entirely. This document lists the deltas.

## What we use unchanged

These GSD primitives work for research as-is:

- **State management** — `PROJECT.md`, `STATE.md`, the phase directory layout. We just populate them with research content.
- **Plan execution** — `/gsd-execute-phase`. Parallel waves of fresh-context executors writing atomic commits is exactly what you want for a battery of robustness specs.
- **Plan format** — XML task plans. Slightly extended (`<test_id>` field) but otherwise identical.
- **Hooks system** — pre/post-tool hooks. Useful for auto-rendering Quarto/LaTeX after task completion.
- **Workstreams** — `/gsd-workstreams` for parallel papers in the same repo (e.g., a main paper and a companion methodological note).
- **Seeds and threads** — cross-phase persistent context. Underused gold for multi-paper projects sharing a dataset.
- **Atomic commits** — one per task. For a robustness battery, this means one commit per regression spec, which makes git bisect (or rather "git blame the spec choice") feasible.
- **Brownfield commands** — `/gsd-map-codebase` and `/gsd-ingest-docs`. Useful when joining an existing project or merging coauthor branches.

## What we override

These GSD commands have research-specific replacements in `gsd-econ`. Both are available; pick whichever you prefer, but the gsd-econ versions ask better questions for papers.

| GSD command | gsd-econ replacement | Why override |
|---|---|---|
| `/gsd-new-project` | `/gsd-new-paper` | Asks for research question, identification strategy, and target journal instead of tech stack and feature list. Populates `METHODOLOGY.md` (which GSD doesn't have). |
| `/gsd-discuss-phase` | `/gsd-discuss-identification` | When the phase is identification-related, asks identification-specific questions (parallel trends, exclusion restrictions, manipulation, monotonicity) instead of generic implementation gray-areas. |
| `/gsd-plan-phase` | `/gsd-plan-empirics` | Constrains the planner's task schema to empirical work: explicit cluster level, FE structure, SE method, sample restrictions. Spawns `identification-checker` as plan_check. |
| `/gsd-verify-work` | `/gsd-verify-replication` | Replaces software UAT with RUT-driven test verification. See `verification-flow.md`. |
| `/gsd-ship` | `/gsd-submit-paper` | Output is a submission package (manuscript PDF, replication archive, cover letter), not a PR. Final referee-sim run before package. |

The originals still work. If you want to use raw GSD machinery for a non-research subdirectory in the same repo (e.g., a website for the paper), you can mix and match.

## What we add (no GSD analog)

| Command | Purpose |
|---|---|
| `/gsd-pre-register` | Generates an AEA registry / OSF-formatted pre-analysis plan from `REQUIREMENTS.md` and `METHODOLOGY.md`. |
| `/gsd-tables-figures` | Dedicated phase command for the tables/figures rendering pipeline. Produces publication-quality LaTeX from analysis output. |
| `/gsd-rr-response` | Revise & resubmit cycle. Each referee comment becomes a phase. Produces response letter + diff document. |
| `/gsd-test-paper` | Standalone — run the full RUT test battery for the paper's methodology, outside the phase loop. Useful before sending drafts to coauthors. |
| `/gsd-referee-sim` | Adversarial review. Runs all `judgment`-clarity tests against the current draft. Produces a referee-style report. |

## What we configure differently

GSD's defaults are tuned for software. We change three:

1. **`workflow.discuss_mode: "discuss"`** — never `assumptions`. For software, defaulting to "infer from the codebase, ask only to correct" is fine. For identification, it's dangerous: a wrong default identification assumption is much harder to catch than a wrong feature assumption.

2. **Model profile: `quality` for planning, `balanced` for execution.** The `identification-checker` and the planner produce reasoning that has to survive peer review — we don't compromise on the model there. Execution (running regressions, generating tables) can use Sonnet.

3. **`workflow.research_before_questions: true`** — we want the literature scout (`econ-researcher`) to run *before* the discussion phase, so the questions about contribution and identification are informed by what's already been done. GSD defaults to questions-first because in software you usually know the requirements; in research, the contribution is partly defined by the existing literature.

These are written into the example `config.json` and applied by the install script.

## What we ignore

A few GSD features don't have natural research analogs and we don't try to map them:

- **`/gsd-ship --draft`** — there's no "draft PR" for a paper. We don't expose this in `/gsd-submit-paper`.
- **`/gsd-secure-phase`** — the threat-model-anchored security command. There are research-data-security analogs (IRB, PII handling) but they're domain-specific enough that we treat them as out of scope. Use the GSD command if you have a security-sensitive setup; otherwise, your IRB protocol is the threat model.
- **`/gsd-ui-phase` / `/gsd-ui-review`** — frontend-specific. Irrelevant.
- **`/gsd-pr-branch`** — the GSD command that filters `.planning/` commits when creating a PR. Papers don't have PRs in the GSD sense; the analog is preparing a clean replication archive, which `/gsd-submit-paper` handles differently.

## Migration note

If you have a paper repo already managed by GSD (somehow), gsd-econ doesn't break it. The new commands are additive; existing planning docs work; you can adopt the new templates incrementally by copying them from `templates/` into `.planning/` when you start a new milestone.
