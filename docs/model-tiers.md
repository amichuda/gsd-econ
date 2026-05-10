# Model tiers

Agents in `gsd-econ` declare the **reasoning load** they need (`light`, `standard`, or `heavy`). The user separately specifies which actual model serves each tier in their `config.json`. This decouples the agent author's knowledge of what reasoning is required from the user's choice of provider, model, and budget.

## The three tiers

| Tier | Reasoning load | Typical agents | Defaults to |
|------|---------------|----------------|-------------|
| `light` | Mechanical — pattern matching, glob/grep, lookup-and-compare | `replication-verifier`, `polish-cross-refs`, `polish-citations` | Haiku-class |
| `standard` | Synthesis — literature summarization, LaTeX formatting, structured comparison | `econ-researcher`, `tables-figures-builder`, `polish-numbers`, `polish-claims` | Sonnet-class |
| `heavy` | Deep reasoning — methodology evaluation, adversarial review, identification critique | `identification-checker`, `econometrician`, `referee-sim`, `polish-consistency` | Opus-class |

Defaults are guidance — the user maps tiers to whatever they actually want.

## How agents declare their tier

Every agent's frontmatter includes a `model_tier` field:

```yaml
---
name: identification-checker
description: Reviews planned empirical specifications against textbook threats...
tools: Read, Write, Glob, Grep
model_tier: heavy
---
```

The verification suite enforces that every agent has this field and that its value is one of `light` / `standard` / `heavy`.

## How users map tiers to models

In `.planning/config.json`:

```json
{
  "model_tiers": {
    "light":    "claude-haiku-4-5",
    "standard": "claude-sonnet-4-6",
    "heavy":    "claude-opus-4-7"
  }
}
```

Or for a budget-constrained run (everything on Sonnet):

```json
{
  "model_tiers": {
    "light":    "claude-haiku-4-5",
    "standard": "claude-sonnet-4-6",
    "heavy":    "claude-sonnet-4-6"
  }
}
```

Or for a quality-maximizing run (everything heavy):

```json
{
  "model_tiers": {
    "light":    "claude-opus-4-7",
    "standard": "claude-opus-4-7",
    "heavy":    "claude-opus-4-7"
  }
}
```

The runtime resolves an agent's model at spawn time: read agent's `model_tier`, look it up in `model_tiers`, use that model for the subagent dispatch.

## Why this matters

Without tiers, the user has to know which agents need which models. With dozens of agents — half of which they didn't write — that's a lot of context to keep. The tier system makes the agent author's judgment portable and the user's policy concise.

It also makes cost control explicit. "I'm running this on Haiku-only this week" is a one-line config change, not a fan-out edit across every agent file.

## Choosing a tier when you author an agent

Heuristics, not rules:

- **`light`** if the agent mostly reads files, looks up patterns, runs `grep`, or compares two things mechanically. The job is "find evidence" not "evaluate evidence." Test verifiers, cross-reference checkers, citation lookups.
- **`standard`** if the agent synthesizes (literature scout summarizing 10 papers; tables-builder producing house-style LaTeX). Reasoning is structured but the task is well-defined.
- **`heavy`** if the agent makes judgment calls a competent peer reviewer would make. Identification-checker, econometrician, referee-sim. These outputs survive peer review; don't compromise on the model.

When in doubt, start at `standard`. Promote to `heavy` if you find the agent producing shallow output on real cases.

## What about commands?

Commands (the slash-invoked top-level entry points like `/gsd-plan-empirics`) run in the orchestrator's main thread, inheriting whatever model the user launched the runtime with. They don't have a `model_tier`. If you want different reasoning depth for different *phases* of the workflow, that's what GSD's `model_profile` (per-phase: discuss/plan/execute/verify) is for — orthogonal to agent tiers.

The two systems compose:
- `model_profile` controls the orchestrator's model per phase
- `model_tiers` controls subagents' models per agent

## Migration note

If you fork `gsd-econ` and add new agents, add `model_tier` to their frontmatter. The verification suite will fail otherwise. If you want to override a built-in agent's tier (e.g., bump `replication-verifier` to `standard` because you don't trust Haiku for it), copy the agent file into your project, edit, and let your runtime's agent-loading rules pick the local copy first.
