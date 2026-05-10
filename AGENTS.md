# gsd-econ project rules

This file is loaded into every session in a gsd-econ project. It contains the
small set of cross-cutting invariants that hold regardless of which command or
agent is active. More specific rules live in `rules/` and are loaded on demand.

## Always-on invariants (never violate)

These hold in every session, every command, every agent.

1. **Code, data, and manuscript are read-only by default.** Files under `code/`,
   `paper/`, `data/`, and `data/raw/` should not be modified except by an
   explicit execute-phase task that the user has approved. The `data/raw/`
   directory specifically is *never* modified — period. Cleaned data goes to
   `data/clean/`.

2. **The user triages; you don't auto-execute consequential decisions.**
   Identification choices, fix plans, referee-sim concerns, polish-pass
   findings — all require explicit user approval before being acted upon. If
   in doubt about whether something is consequential, surface it.

3. **Every state change is logged.** Phase advances, fix plans applied,
   acknowledged blockers, disputed referee concerns — these go in
   `.planning/STATE.md` with a timestamp. STATE.md is the audit trail.

4. **Atomic commits, one logical change per commit.** No "WIP" omnibus commits.
   A regression spec, a robustness column, a paragraph rewrite, a figure
   regeneration — each gets its own commit with a meaningful message.

5. **Calibrated honesty, not confident guessing.** When you don't know, say so. When you're partially confident, hedge with explicit uncertainty (not weasel words — actual confidence levels: "I think this is X, but I'd want to verify because Y"). Hallucinations are *confident errors* — incorrect information delivered without appropriate qualification — and they're the failure mode that erodes the framework's credibility fastest. Distinguish three states explicitly: known (verified from a source you can cite), partial (you have prior probability but no current verification), unknown (you don't have it). When the answer is partial or unknown, prefer to *search, fetch, or ask the user* rather than to fill the gap with plausible content. This is metacognition as a control layer — your awareness of your own uncertainty governs whether to answer, search, or escalate.

6. **Surface known weaknesses without softening.** When a methodology has known weaknesses (e.g., naive TWFE for staggered DiD), surface them; don't soft-pedal because the work is already done.

## Lazy-loaded rules

When you encounter situations matching the trigger, read the corresponding
rule file. Use the Read tool; do not load all of these at session start.

| Rule file | When to load |
|-----------|--------------|
| `rules/identification.md` | When discussing identification, planning empirical specs, or evaluating an existing identification strategy |
| `rules/methodology-integrity.md` | When choosing or modifying an estimator, SE structure, or inference procedure |
| `rules/file-discipline.md` | Before any write, edit, or delete operation on project files |
| `rules/git-discipline.md` | Before committing, force-pushing, or rewriting history |
| `rules/preregistration.md` | When working on pre-registration, PAP, or PAP-deviation disclosures |
| `rules/data-handling.md` | When working with data files (raw, cleaned, derived) |
| `rules/manuscript-discipline.md` | When editing the manuscript or generating manuscript text |
| `rules/uncertainty-honesty.md` | Before any factual claim about a paper, dataset, method, or finding you haven't directly verified in this session — and any time you're tempted to overclaim, paper over a gap, or soften an inconvenient finding |

## Project layout assumptions

A typical gsd-econ project has this structure:

- `.planning/` — workflow state: PROJECT.md, METHODOLOGY.md, ROADMAP.md, STATE.md, phase folders
- `data/raw/` — source data (read-only, period)
- `data/clean/` — cleaned data (output of cleaning code)
- `code/` — analysis code
- `paper/` — manuscript LaTeX or Quarto sources
- `output/` — regression outputs, intermediate artifacts (regenerable)
- `tables/` — compiled tables (regenerable)
- `figures/` — compiled figures (regenerable)
- `vendor/gsd-econ/` — this overlay (when vendored)
- `vendor/research-unit-tests/` — RUT submodule

If a project's layout differs substantially, ask the user before assuming.

## Escape hatch

The user can override any rule with an explicit instruction in chat. If a user
says "go ahead and modify the manuscript directly this once," do it — but log
the override to STATE.md. Rules are defaults that protect the workflow, not
locks that prevent the user from doing what they want.
