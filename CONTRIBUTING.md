# Contributing to gsd-econ

Thanks for considering a contribution. This is a young project; the structure can evolve. Concretely useful contributions:

## Add a custom RUT-style test

The highest-leverage contribution. If you've found a methodological pitfall that should be a test, write it.

1. Read [`docs/writing-tests.md`](docs/writing-tests.md) for the format.
2. Author your test in `tests/community/<your-username>/<test-id>.md` (private collection) or `tests/core/<test-id>.md` (proposed for inclusion).
3. Add the registry entry in `tests/registry.yaml`.
4. Smoke-test against the example paper or one of your own.
5. Open a PR.

For tests that are universally applicable (not econ-specific), consider opening the PR upstream to [research-unit-tests](https://github.com/rdahis/research-unit-tests) instead.

## Improve a command or agent

The commands and agents are markdown files. PRs welcome for:
- Better-routed gray-area questions in `gsd-discuss-identification`
- Additional methodology branches (currently DiD, IV, RDD, RCT, OLS — could add synth, ML-prediction, structural)
- Clearer fail-handling instructions in agent prompts
- Better verification message formatting

## Improve docs

The documentation in `docs/` could always be sharper. PRs to:
- `architecture.md` — diagram improvements, missing flows
- `verification-flow.md` — edge cases the matrix doesn't cover
- `adapting-gsd.md` — additional GSD features and how to handle them

## Report a bug

Open an issue with:
- What you tried
- What happened
- What you expected
- Runtime: OpenCode / Claude Code, version
- GSD version, RUT version, gsd-econ commit

## Larger changes

For substantial restructuring (e.g., changing the test registry format, adding a new phase command), open an issue first to discuss. Avoids wasted PR effort.

## Style

- Markdown: 80–120 char soft limit; longer is fine in tables.
- Code (scripts/): bash with `set -euo pipefail`, comments for non-obvious decisions.
- Tone: technical, specific, no marketing language.

## Copyright

Contributions are under MIT, same as the rest of the repo. By contributing, you agree to license your contribution under MIT.

## Prior art and attribution

Two architectural patterns in this repo are inspired by other open work:

**The polish-pass architecture** (parallel polish agents writing reports, user triage, fix-plan generation, capped-round loop) is conceptually inspired by [zeropaper](https://github.com/alejandroll10/zeropaper) by Alejandro Lopez-Lira. We reviewed zeropaper's public README; we did not access or copy any of its agent prompt files, command files, or scripts. zeropaper is released under a restrictive non-MIT license that we do not adopt; the lineage is at the architectural-pattern level only, which is not copyrightable.

**The `--heavy` mode of `/gsd-referee-sim`** (K parallel light-tier agents + one heavy-tier deliberator) is conceptually inspired by [HeavySkill](https://github.com/wjn1996/HeavySkill) by Wang et al. (Apache-2.0). The technique exploits diversity in the parallel stage and depth in the deliberation stage. Our integration is original — HeavySkill's published version is a generic test-time scaling skill, while ours is specialized to adversarial peer review with explicit framing assignments and substantive-vs-surface concern classification. We acknowledge the inheritance in `agents/referee-deliberator.md` and in the command's mode description.

**The framing of `rules/uncertainty-honesty.md`** — hallucinations as *confident errors*, the known/partial/unknown distinction, and uncertainty as a control signal for tool use — draws on Yona, Geva, and Matias (2026), *Hallucinations Undermine Trust; Metacognition is a Way Forward* ([arXiv:2605.01428](https://arxiv.org/abs/2605.01428)). The paper is a position piece arguing that current models lack the discriminative power to fully eliminate hallucinations and that *faithful uncertainty* (linguistic uncertainty aligned with intrinsic uncertainty) is the workflow-level response.

**The `--meta-cog` flag** on `/gsd-plan-empirics`, `/gsd-discuss-identification`, `/gsd-referee-sim`, and `/gsd-polish-pass` operationalizes that paper's "intrinsic uncertainty estimated via repeated sampling" pattern (their Section 5 and Appendix B) at the workflow layer: N=3 parallel agent runs, agreement-as-confidence-signal, offload-policy gating in polish-pass. Documented in [`docs/meta-cognition.md`](docs/meta-cognition.md). The implementation is original; only the underlying conceptual frame is from the paper. We do not implement the paper's deeper proposals (uncertainty-preserving alignment, internal-state probing, fine-tuning for faithful expression) since those live in the model training pipeline, not the workflow layer.

When extending the framework with patterns inspired by other tools, please add the attribution here and write the prompts in your own voice rather than echoing phrasing from any other tool's documentation.
