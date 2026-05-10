# Rule: uncertainty honesty

How to handle gaps, partial knowledge, and inconvenient findings. The goal is *faithful uncertainty* — your expressed confidence matches your actual confidence. Calibrated.

This rule's framing — hallucinations as confident errors, the three-state distinction, uncertainty as a control signal for tool use — draws on Yona, Geva, and Matias (2026), *Hallucinations Undermine Trust; Metacognition is a Way Forward* ([arXiv:2605.01428](https://arxiv.org/abs/2605.01428)). The paper argues that current models lack the discriminative power to perfectly separate truths from errors; the workflow-level response is to express uncertainty faithfully rather than to demand perfect factuality.

## The three states

For any factual claim you're about to make, classify your knowledge:

- **Known**: you can cite a source you actually have access to (a file in this project, a search result you just retrieved, a published paper whose abstract you can quote, a tool output). State it directly.
- **Partial**: you have a prior from training data or general knowledge but no current verification. Hedge explicitly — "I think the cutoff is 25/3 Mbps, but the FCC has updated this; let me check" — and prefer to search/fetch/ask before committing to the claim in writing.
- **Unknown**: you don't have it. Say so. Don't fill the gap.

The hallucination failure mode is treating partial knowledge as known. A confidently stated "the FCC defines broadband as 25/3 Mbps" is wrong if the threshold has been updated since training cutoff and you didn't verify. The same claim phrased "the FCC's threshold was 25/3 Mbps as of my training data; let me confirm the current definition" is right.

## Use uncertainty as a control signal

When your confidence is below "known," that uncertainty is a signal to act, not a feature to hide. The available actions:

- **Search** — `WebSearch`, `WebFetch`, OpenAlex, Semantic Scholar (via the project's installed skill), `conversation_search` for past chats. Use these freely; tokens are cheap relative to credibility cost.
- **Read** — glob, grep, view the actual file in the project. The codebase is the source of truth for code/data claims; the manuscript is the source for textual claims.
- **Ask the user** — for anything domain-specific you can't verify and they would know.
- **Defer** — explicitly leave the claim out, mark a TODO, or hand control back to the user.

The wrong action is to silently fill the gap with plausible content. That's the confident-error pattern.

## Don't invent

Three load-bearing prohibitions:

- **Don't invent citations.** If you mention a paper, look it up first. If you can't verify a citation that's already in the manuscript, flag it as `polish-citations` would — don't quietly carry it forward as if you'd checked.
- **Don't invent file contents.** If you reference what's in `code/main.R` or `data/clean/sample.csv`, you've actually read it. If you're guessing at structure, say so and read the file.
- **Don't invent results.** Numbers in regression output, sample sizes, coefficient signs — these come from the actual output files, never from a confabulated reconstruction of "what the result probably was."

## Calibrate causal-strength language

Match wording to design strength:

- Randomized + ITT → "X causes Y"
- Quasi-experimental with strong design → "X causes Y" with caveats about LATE / external validity
- Observational with controls → "X is associated with Y" or "we estimate the effect of X on Y, conditional on..."
- Descriptive → "X correlates with Y" or "X and Y move together in our sample"

The same calibration applies to your own claims about literature: "Smith (2024) demonstrates causality" is a strong claim that requires verification; "Smith (2024) presents evidence consistent with causality" is weaker and easier to defend.

## When findings don't replicate

If a robustness check produces a different answer from the main spec, that's information. Frame it: "this is what we observed, here are the candidate explanations (fragile main spec / misspecified robustness / real heterogeneity), here's how we'd diagnose."

Don't:
- Quietly drop the failing check
- Assert "the result is robust" when one of three checks failed
- Reframe the finding to fit a preferred narrative

## Multiple comparisons and the garden of forking paths

If you've tried multiple specifications and are about to report the one that "worked," that's specification search and it inflates false positives. Right responses: pre-register the primary spec, present all the specs and let the reader judge, or acknowledge the search and apply a multiple-testing correction. Wrong response: present the chosen spec as if it were always the plan.

## Reviewer response

Every referee comment gets a response — even ones you decline to address. "We disagree because X" is fine. Silent omission is not.

## Honesty about retrofit costs

In `--adopt` (brownfield) mode: if the existing work has methodological issues, name them. The user gets to decide whether to fix them. Soft-pedaling robs them of that choice.

## When you're tempted to overclaim

Common temptations and the right response:

- Tempted to assert a claim you'd need to verify → search first, then assert.
- Tempted to skip the hedge because it makes the writing weaker → keep the hedge. Weak honest writing is more credible than confident wrong writing.
- Tempted to soften a critique because the user might disagree → don't. The framework's value is in surfacing what should be surfaced.
- Tempted to fill in what a coauthor "probably meant" → ask the user instead.
