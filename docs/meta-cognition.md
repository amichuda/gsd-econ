# Metacognition in gsd-econ

This document explains the `--meta-cog` flag and the `--offload-policy` flag, what they do, what they don't do, and the limits of the workflow-level implementation.

## Background

Yona, Geva, and Matias (2026), [*Hallucinations Undermine Trust; Metacognition is a Way Forward*](https://arxiv.org/abs/2605.01428), argue that the path forward for trustworthy LLMs is not perfect factuality (which is unattainable due to a "discrimination gap" — models can't reliably tell which specific outputs are wrong) but **faithful uncertainty**: linguistic confidence calibrated to actual intrinsic confidence. For agentic systems specifically, the paper argues metacognition becomes "the control layer governing when to search and what to trust."

The paper's technical proposals — uncertainty-preserving alignment, internal-state probing, supervised fine-tuning for uncertainty expression — live in the model training pipeline. A workflow framework can't implement those. What a workflow framework *can* implement is the paper's Section 5 proposal: **estimate intrinsic uncertainty via repeated sampling and use it as a control signal**.

The `--meta-cog` flag in gsd-econ does exactly that.

## What `--meta-cog` does

When set, certain agents (the load-bearing judgment agents) are invoked N=3 times in parallel on the same input. The N independent runs are compared:

- Findings raised by all 3 runs are **high-confidence** — the agent's intrinsic uncertainty is low.
- Findings raised by 2 of 3 runs are **medium-confidence**.
- Findings raised by only 1 run are **low-confidence** — high disagreement, the agent isn't sure.

This implements "intrinsic uncertainty estimated via repeated sampling under temperature > 0" from the paper's Appendix B. It's not perfect calibration — N=3 is small and the runs aren't truly independent (they share architecture and training) — but it's *better* than single-pass self-rated confidence, which the paper specifically warns against.

## Where the flag is honored

Three commands invoke load-bearing judgment agents and accept `--meta-cog`:

- `/gsd-plan-empirics --meta-cog` — applies to the `identification-checker` step
- `/gsd-discuss-identification --meta-cog` — applies to the `identification-checker` step
- `/gsd-referee-sim --meta-cog` — applies to the `referee-deliberator` (in `--heavy` mode) or to each parallel referee (without `--heavy`)
- `/gsd-polish-pass --meta-cog` — applies to all five polish agents

In each case, the cost is roughly 3× tokens at the relevant step. Default off.

## When to use it

The flag is most valuable for:

- **High-stakes pre-submission decisions** where you want the framework's verdicts to be calibrated rather than just plausible.
- **Long-horizon judgments** the framework is making on your behalf without immediate human review (e.g., when running `/gsd-polish-pass --offload-policy aggressive`, where the framework auto-handles findings).
- **Replication or evaluation contexts** where you'll be reporting the framework's outputs to a third party (referee, journal, evaluator) and want defensible calibration.

It is *not* worth using for:

- Exploratory work, throwaway specs, "I'm just trying something" sessions.
- Cases where you'll triage every finding manually anyway (the calibration adds no value if you're going to read each one).
- Routine applications where the agent's job is mechanical (the paper's discrimination gap concern is about judgment, not computation).

## What `--meta-cog` does NOT do

Three honest limits worth knowing.

**It doesn't fix the discrimination gap at the underlying model layer.** The paper's central empirical finding is that current models top out at AUROC 0.70–0.85 for separating correct from incorrect answers. Repeated sampling helps surface disagreement when it exists, but if all N runs are confidently wrong in the same way (a known failure mode for shared-architecture models), the meta-cog signal misses it. The flag improves calibration on the margin; it doesn't solve the underlying capability problem.

**It doesn't measure linguistic decisiveness.** The paper's full framework requires both intrinsic uncertainty (which we estimate via N-sample disagreement) AND linguistic decisiveness (how confident the words sound), with a metric that aligns the two. We measure intrinsic uncertainty and use it to *gate* findings, but we don't quantify linguistic decisiveness or compute a `cMFG` score. Doing that would require an LLM-as-judge layer rating each generated assertion's decisiveness, which is buildable but adds another N× cost on top.

**N=3 is small.** The literature uses N=10 to N=20 for reliable semantic-entropy estimates. N=3 is a cost compromise — enough to detect strong disagreement, but not enough to estimate fine-grained uncertainty. The 3/3 vs 2/3 vs 1/3 categorization is a coarse signal; treat it accordingly. If you want more reliable calibration, the path is increasing N at the cost of tokens, not redesigning the mechanism.

## How `--meta-cog` composes with `--offload-policy`

The polish-pass command has a separate flag, `--offload-policy {manual|assisted|aggressive}`, that controls how much triage gets offloaded from the user to the framework.

- `manual` (default): every finding goes to user triage. Confidence ratings are visible but don't change behavior.
- `assisted`: low-confidence findings are auto-acknowledged (logged but not surfaced); medium-confidence go to user with a recommendation; high-confidence go to user without preselection.
- `aggressive`: low-confidence auto-dismissed; medium-confidence go to user; high-confidence auto-addressed (fix plans queued without user confirmation).

The two flags compose: `--offload-policy` is what's done with the confidence ratings; `--meta-cog` is whether those ratings are calibrated.

**If you set `--offload-policy aggressive` without `--meta-cog`, the framework warns you.** You're asking the framework to auto-handle findings based on a confidence rating that's the model's own single-pass self-assessment — exactly the uncalibrated signal the Yona paper says is unreliable. The warning is so the trade-off is explicit: you can proceed if you accept the risk.

The combination `--meta-cog --offload-policy aggressive` is the most opinionated configuration. It says: "I trust the framework's calibrated confidence enough to let it auto-handle high-confidence findings." This costs 3× tokens at the polish-agent step and saves you triage work in exchange for a small probability of the framework auto-handling something it shouldn't have. Reasonable for routine pre-submission passes; less reasonable for first-time submissions to a top journal.

## What the audit trail captures

When `--meta-cog` or `--offload-policy` is set, the orchestrator logs to STATE.md:

- The mode and policy that were active for this run
- For meta-cog: per-finding confidence ratings (3/3, 2/3, 1/3) and which runs flagged what
- For offload-policy: which findings were auto-handled, which were surfaced for triage, which were auto-dismissed

This is part of the framework's "honesty about what was decided by whom" discipline. A coauthor reading the STATE.md log six months later can see exactly which decisions the framework made versus the user, with what confidence, and why.

## Limitations and honest framing for users

The implementation here is the workflow-level operationalization of a research-level proposal. It's a real improvement over uncalibrated single-pass agents — disagreement-as-uncertainty is a robust signal — but it's not the same thing as the paper's full vision of metacognitively-aware models.

Specifically:
- Faithful uncertainty in the paper's strict sense requires alignment of *linguistic* and *intrinsic* uncertainty. We measure the latter; we don't enforce the former.
- The bootstrapping paradox the paper describes (SFT datasets are static; correct uncertainty is dynamic relative to the model's evolving knowledge) doesn't apply here because we're not fine-tuning. But a related concern does: the meta-cog signal is only as good as the parallel runs' actual independence, which depends on the underlying model's stochastic behavior at temperature.
- The discrimination gap (AUROC 0.70–0.85 ceiling) is a property of current frontier models. As models improve, the meta-cog signal will become more reliable. As models get worse on calibration (the paper documents this happening with RLHF), the signal degrades.

If you find yourself trusting `--meta-cog` more than you should — auto-handling things on aggressive policy that turn out to be wrong — back off to `assisted` or `manual`. The framework is a forcing function for honest discipline; it can't substitute for human judgment on high-stakes work.
