# Changelog

All notable changes to gsd-econ are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-05-12

The "automated robustness" release. Adds specification-curve / multiverse
analysis as a first-class feature.

### Added

- **`/gsd-multiverse` command.** Reads logged data-cleaning and methodology
  decisions, composes them with a design-family grid, runs every defensible
  specification through a user-provided evaluator, and produces a
  specification curve plus audit table. Implements the Simonsohn-Simmons-Nelson
  (2020) specification curve methodology with automated grid construction.

- **`rules/decision-logging.md`.** New rule file that defines what makes a
  data-cleaning or methodology decision "contested" and how to log it to
  `decisions.jsonl`. Includes positive examples (sample restrictions,
  missing-data handling, outlier thresholds, derived-variable definitions,
  SE clustering, multiple-testing corrections) and explicit negative
  examples (data integrity exclusions, type conversions, documented missing
  codes). Loaded lazily by execute-phase agents via the AGENTS.md table.

- **Methodology grids for the four common designs.** `config/multiverse-grids/`
  ships templated parameter grids with defaults, alternatives, justifications,
  and citations:
  - `rct.yaml`: 8 axes (SE clustering, stratum FE, controls, outcome window,
    non-compliance handling, multiple testing, attrition, heterogeneity)
  - `did.yaml`: 7 axes (estimator choice including CS-2021/SA-2019/dCDH/BJS,
    control group, parallel-trends window, SE clustering, honest DiD,
    event-study window, controls)
  - `iv.yaml`: 6 axes (weak-IV inference, controls, SE clustering,
    exclusion-restriction tests, shift-share inference, LATE interpretation)
  - `rdd.yaml`: 8 axes (bandwidth, polynomial order, kernel, manipulation
    test, SE structure, mass-point handling, donut radius)

- **`scripts/multiverse_runner.py`.** Pure-Python deterministic harness that
  loads decisions and grids, constructs the cross-product, and runs the
  user's `evaluate(spec) -> dict` function over every cell (or a
  main-effects subset, or a random sample for very large grids). Records
  errors per-cell rather than crashing.

- **`multiverse-reporter` agent.** Specialist that produces both a
  publication-quality specification curve PDF (for the manuscript /
  supplementary material) and a self-contained interactive HTML report
  (for sharing with coauthors or referees) from `multiverse_results.csv`.
  Single agent for both outputs — both derive from the same data so they
  stay in sync. The HTML embeds the SVG plot, a sortable/filterable audit
  table, axis-decomposition diagnostics, and download links, all inline
  with no external dependencies (works on an airplane). Standard
  SSN-2020 layout for the curve.

- **`docs/multiverse.md`.** Full conceptual documentation explaining the
  problem (asymmetric robustness analysis is the norm in empirical
  economics), the solution (multiverse with automated grid construction),
  the workflow, and the honest limits.

- **Execute-phase agent updates.** `econometrician` and
  `tables-figures-builder` now have explicit Step 7 / constraint-bullet
  instructions to log contested decisions to `decisions.jsonl` as they
  work. Conservative — only contested choices, not trivial ones.

### Changed

- **`AGENTS.md`** now references `rules/decision-logging.md` in the
  lazy-load table so agents pick it up during the execute phase.

- **README.md** has a one-paragraph "Related work" section pointing at
  `docs/related-work.md` (which was added in the previous session).

### Notes

This is the first release where gsd-econ provides a research-methodology
contribution beyond workflow scaffolding. Specification curves are not new
(Simonsohn et al. 2020, Steegen et al. 2016); what's new here is making
them cheap enough to be a default rather than an exception. The framework
captures contested decisions at the moment they're made and runs the
multiverse mechanically.

The implementation is intentionally minimal: the runner is deterministic
(no LLM in the loop for the sweep itself), the grids are starting points
not exhaustive lists, and the evaluator contract is "any function that
returns `{coefficient, se}`". Future work (v0.4+) may add:

- Crash-safety with periodic CSV flushing
- ANOVA-style decomposition of fragility by axis
- Pre-built evaluator scaffolds for common (Stata/R/Python) analysis
  setups
- Composition with Shin-2026's audit-locked specification search

## [0.2.0] — 2026-05-11

The OpenCode-compatibility release. The earlier symlink-based install
didn't work for OpenCode because of differences in agent frontmatter
schema; this release closes that gap and adds proper model-tier routing.

### Added

- **OpenCode agent frontmatter transform.** `scripts/transform-agent-frontmatter.py`
  rewrites Claude-Code-style frontmatter (string-form `tools`, capitalized
  tool names) to OpenCode's required schema (object-form `tools`, lowercase
  keys, `mode: subagent`, WebSearch → webfetch mapping).

- **Model-tier resolution at install time.** When the runtime is OpenCode,
  `install.sh` now reads `.planning/config.json`'s `model_tiers` mapping
  and writes an explicit `model:` field into each agent file. Previously
  the tier system was decorative; every subagent inherited the session
  model.

- **`--models-config <file>` flag.** Apply a YAML model configuration
  (provider, tiers, session model, permissions) to both
  `.planning/config.json` and `opencode.json` in one command. Idempotent;
  re-running with a different YAML changes models while preserving any
  other user edits to either file.

- **`--interactive-models` flag.** TTY-based picker that walks the user
  through provider and tier choices and generates a YAML the apply
  pipeline can consume. Pre-populated with current pricing (May 2026) for
  Anthropic, OpenRouter, OpenAI, and Ollama.

- **Ready-made templates.** `config/model-configs/` ships four
  representative configurations:
  - `anthropic-direct.yaml` (~$30-60 per evaluation)
  - `openrouter-hybrid.yaml` (~$5-15)
  - `openrouter-deepseek.yaml` (~$0.50-1.50)
  - `ollama-local.yaml` ($0, requires hardware)

- **`docs/related-work.md`.** Full attribution and comparison to neighboring
  projects in the empirical-economics-AI-agent space: Bäckman's
  AI-research-feedback, Crawfurd's claude-skills, Korinek (NBER WP 34202),
  Dawid et al. (arXiv 2504.09736), Shin (arXiv 2603.17381), Karpathy's
  autoresearch, plus the upstream GSD, RUT, zeropaper, HeavySkill, and
  Yona et al. inspirations.

### Fixed

- **`wire_config` preserves user edits.** Previously, `--wire-only` used
  `jq -s '.[0] * .[1]'` to merge the upstream example over the user's
  config — the merge direction was wrong, so user edits to `model_tiers`
  (or anywhere else) got silently clobbered on every re-run. Now
  `wire_config` only writes config.json when it doesn't exist; existing
  configs are preserved byte-identically. Regression tests in
  `verification/test_config_preservation.py`.

- **`make verify` portability.** Now uses `python3 -m pytest` instead of
  bare `pytest`. Detects `uv` and prefers `uv run --group dev` when
  available. Falls back to system pip with proper escalation
  (--user, --break-system-packages) for modern Ubuntu and macOS.

### Changed

- **`pyproject.toml`** introduced. Dev dependencies declared under
  `[dependency-groups] dev = ["pytest>=7.0", "pyyaml>=6.0"]` so `uv sync`
  manages the venv.

- **`config.json.example`** now uses provider-prefixed model strings
  (`anthropic/claude-opus-4-7` rather than bare `claude-opus-4-7`) since
  OpenCode requires that format. Backward-compatible with Claude Code.

## [0.1.0] — 2026-05-07

Initial release. Spec-driven workflow framework for empirical economics,
built on get-shit-done (TÂCHES) and research-unit-tests (rdahis), with
domain-specific commands, agents, and methodology-discipline rules.

### Initial features

- 10 slash commands covering the empirical lifecycle: `gsd-new-paper`,
  `gsd-discuss-identification`, `gsd-plan-empirics`,
  `gsd-verify-replication`, `gsd-test-paper`, `gsd-tables-figures`,
  `gsd-pre-register`, `gsd-rr-response`, `gsd-polish-pass`,
  `gsd-submit-paper`, `gsd-referee-sim`.

- 13 specialist agents organized by reasoning load (light / standard / heavy):
  `identification-checker`, `econometrician`, `referee-deliberator`,
  `polish-consistency`, `referee-sim` (heavy), `econ-researcher`,
  `tables-figures-builder`, `polish-numbers`, `polish-claims` (standard),
  `replication-verifier`, `polish-cross-refs`, `polish-citations`,
  `referee-sim-light` (light).

- 8 methodology-discipline rule files: `identification.md`,
  `methodology-integrity.md`, `file-discipline.md`, `git-discipline.md`,
  `preregistration.md`, `data-handling.md`, `manuscript-discipline.md`,
  `uncertainty-honesty.md`.

- `--meta-cog` flag for parallel-rollout agreement-as-confidence
  calibration. `--heavy` flag for HeavySkill-style cheap-fan-plus-deliberator
  aggregation. `--offload-policy` for polish-pass triage.

- Cross-runtime support: Claude Code and OpenCode (with caveats — see v0.2
  for the proper fix).

- 200+ verification tests, shellcheck-clean install script, MIT license
  with attribution to all upstream projects.
