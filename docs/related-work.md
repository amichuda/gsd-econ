# Related work

gsd-econ is not the first or only project in this space. This section
gives credit where due, notes what's nearby, and explains what gsd-econ
adds.

## Direct neighbors: economics-specific paper review

[**Bäckman, *AI-research-feedback* (2026)**](https://github.com/claesbackman/AI-research-feedback)
is the closest existing analog. A collection of Claude Code slash
commands for academic economics paper review, with six parallel
review agents that consolidate into a single structured report. Covers
pre-submission review (`/review-paper`), pre-analysis-plan review
(`/review-pap`), paper-code reproducibility audit
(`/review-paper-code`), fast 2-agent identification check
(`/review-paper-light`), and grant proposal review (`/review-grant`).
Persona-configurable by target journal (AER / QJE / JPE /
Econometrica / REStud, plus finance and macro fields). MIT-licensed.
**Overlap with gsd-econ:** the multi-agent parallel-then-consolidate
review pattern in our `/gsd-referee-sim` is structurally similar.
**Gap gsd-econ fills:** Bäckman's tools are audit-only; they assume a
finished paper exists. gsd-econ adds the forward-construction
scaffolding (project bootstrap, identification discussion, empirics
planning, pre-registration, replication verification).

[**Crawfurd, *claude-skills* (2026)**](https://github.com/lcrawfurd/claude-skills)
([website](https://lcrawfurd.github.io/claude-skills/)) provides
Claude Code skills built around established review frameworks: Edmans'
editorial assessment, Nyhan's peer review checklist, Humphreys'
comprehensive review, Blattman's empirical paper guide, Evans &
Bellemare on intros/abstracts/conclusions, plus Scott Cunningham's
MixtapeTools Referee 2 protocol and a wrapper around Bäckman's
review. Also includes a 5-parallel-audit computational
reproducibility protocol (code audit, cross-language replication,
package layout, output automation, econometrics) based on Gentzkow &
Shapiro, DIME Analytics, Reif, the AEA Data Editor, and the Social
Science Data Editors template. **Gap gsd-econ fills:** these are
high-quality framework-wrappers for review and audit; gsd-econ
provides the methodology-discipline rules and the full-workflow
scaffolding around them.

## Academic papers in the same design space

[**Korinek (2025), *AI Agents for Economic Research*, NBER WP
34202**](https://www.nber.org/papers/w34202) is the standard
introduction to the topic for economists. Walks through how to build
agents with LangGraph, with worked examples (FRED data retrieval,
econometric tool builder). gsd-econ is, in some sense, what Korinek's
paper teaches economists to build for themselves — but persistent,
shared, and opinionated about empirical-economics methodology.

[**Dawid, Harting, Wang, Wang & Yi (2025), *Agentic Workflows for
Economic Research: Design and Implementation*, arXiv
2504.09736**](https://arxiv.org/abs/2504.09736) proposes a
methodology for agentic workflows in economics with specialized
agents, inter-agent communication, error escalation, and
human-in-the-loop checkpoints. Implementation on AutoGen. **Relation
to gsd-econ:** their paper is a design proposal with experimental
examples; gsd-econ is one possible concrete implementation of what
they argue for, on Claude Code / OpenCode instead of AutoGen, with
domain-specific methodology rules.

[**Shin (2026), *An Auditable AI Agent Loop for Empirical Economics:
A Case Study in Forecast Combination*, arXiv
2603.17381**](https://arxiv.org/abs/2603.17381) (Federal Reserve Bank
of Philadelphia) adapts Karpathy's autoresearch loop architecture to
empirical economics, with an immutable evaluator, an editable script
defining the search surface, an instruction contract, an audit log,
and a **post-search holdout evaluation** to distinguish robust
improvements from sample-specific discoveries. Shin's contribution is
narrower (evaluator-locked local search within a fixed empirical
workflow) but addresses something gsd-econ doesn't currently handle:
the researcher-degrees-of-freedom problem that emerges when AI
coding agents make specification search fast. **Direction for
gsd-econ:** Shin's audit-locked search is a natural addition for the
execute phase — see `docs/integration-shin.md` for an outline.

## Inspirations on the agent-harness side

[**Karpathy, *autoresearch* (2026)**](https://github.com/karpathy/autoresearch)
is the open-source reference architecture Shin builds on: a minimal
four-file harness (`prepare.py` = fixed evaluator, `train.py` =
editable surface, `program.md` = instruction contract,
`results.tsv` = audit log) for autonomous LLM training research on a
single GPU. The pattern — *fixed evaluator + editable surface +
written instruction contract + audit log* — generalizes well beyond
ML. gsd-econ doesn't currently use the autoresearch pattern directly,
but it's a sensible fit for evaluator-locked phases like
`/gsd-plan-empirics` followed by `/gsd-verify-replication`. See
`docs/integration-karpathy.md` for an outline.

[**Anthropic, *Get Shit Done (GSD)*
(2025–)**](https://github.com/gsd-build/get-shit-done) is the
spec-driven workflow framework that gsd-econ extends. GSD provides
the project-bootstrap, planning, and verifier machinery; gsd-econ
adds economics-specific commands, agents, and methodology rules on
top.

[**Dahis, *research-unit-tests*
(2025–)**](https://github.com/rdahis/research-unit-tests) is the
research-discipline test framework that gsd-econ vendorizes alongside
GSD. RUT contributes the test format and registry that
`/gsd-verify-replication` and the rules folder build on.

[**zeropaper, *polish-pass for academic papers*
(2025–)**](https://github.com/alejandroll10) inspired the multi-agent
polish-pass architecture (five parallel agents covering numbers,
cross-refs, citations, consistency, claims), adapted here for
economics-specific concerns.

[**wjn1996, *HeavySkill*
(2025)**](https://github.com/wjn1996/HeavySkill) (Apache-2.0)
inspired the `--heavy` aggregation pattern used in
`/gsd-referee-sim` and others: many light-tier agents run in
parallel, a heavy-tier deliberator synthesizes.

[**Yona, Geva & Matias (2026), *On the Use of Confidence-as-Agreement
in LLMs*, arXiv 2605.01428**](https://arxiv.org/abs/2605.01428)
inspired the `--meta-cog` flag: agreement across N independent
rollouts is used as a confidence signal. The same paper inspired
`rules/uncertainty-honesty.md`.

## What gsd-econ specifically adds

Given the above, the claims gsd-econ can credibly make are narrower
than "first economics research harness" — which would be false. The
honest claims:

1. **Forward construction, not just review.** Bäckman and Crawfurd's
   tools assume a finished paper. gsd-econ scaffolds the full
   lifecycle: `/gsd-new-paper` →  `/gsd-discuss-identification` →
   `/gsd-plan-empirics` →  `/gsd-pre-register` → execute →
   `/gsd-verify-replication` → `/gsd-polish-pass` →
   `/gsd-referee-sim` → `/gsd-submit-paper`.

2. **Encoded methodology rules.** The `rules/` folder
   (`identification.md`, `methodology-integrity.md`,
   `preregistration.md`, `uncertainty-honesty.md`,
   `data-handling.md`, …) is gsd-econ's domain-expertise layer. Other
   harnesses have rules; few have rules at this level of granularity
   for econometric identification specifically.

3. **Tiered model routing with explicit meta-cognition.** The
   `model_tiers` system (light/standard/heavy) lets users route the
   13 agents to different cost/capability points. The `--meta-cog`
   flag spawns parallel rollouts and uses agreement as a calibration
   signal.

4. **Cross-runtime support.** Works on both Claude Code (via
   symlinked agents) and OpenCode (via install-time frontmatter
   transformation with tier-to-model resolution). Most harnesses
   target one runtime.

If you're choosing a tool: use Bäckman's `/review-paper` if all you
need is a polished pre-submission referee report on a finished paper.
Use Crawfurd's skills if you want established review frameworks
wrapped as commands. Use gsd-econ if you want to scaffold a paper
from the design-brief stage onward and have it reviewed at every
phase. They compose; running Bäckman's `/review-paper` on a paper
written using gsd-econ is a reasonable workflow.
