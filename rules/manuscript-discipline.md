# Rule: manuscript discipline

Constraints on editing or generating manuscript text.

## Edits go through fix plans, not direct writes

Outside of `/gsd-execute-phase` tasks the user has approved, do not modify the manuscript. The polish-pass agents are read-only by design. The orchestrator coordinates findings; user-triaged fix plans drive the modifications.

## Don't generate full sections from scratch unless asked

If asked "draft a results paragraph for Table 3," do that. If asked "what should I work on next," don't draft a paragraph as part of the answer. The boundary between "user asked for prose" and "user asked for guidance" matters.

## Match the existing voice

If the existing manuscript uses past tense, your additions use past tense. If it says "we estimate," you say "we estimate" — not "the authors estimate." If it uses serial commas, you use serial commas. Stylistic consistency matters more than your preferences.

## Numbers in prose must trace to a source

Never write "we find a 12.4% increase" without checking that the source (a regression output, a computed transformation) actually says 12.4%. Drift between prose and tables is the bug class `polish-numbers` exists to catch — don't introduce new instances of it.

## Don't invent citations

If the user mentions a paper without giving a citation, look it up via Semantic Scholar, OpenAlex, or web search; do not fabricate the citation from a guess at the title and year. If you can't find it, ask. A fabricated citation is a serious credibility failure.

## Causal language must match design strength

Calibrate strength to identification:

- Randomized + intent-to-treat → "X causes Y"
- Quasi-experimental with strong design → "X causes Y" with appropriate caveats about LATE / external validity
- Observational with controls → "X is associated with Y" or "we estimate the effect of X on Y, conditional on..."
- Descriptive → "X correlates with Y" or "in our sample, X and Y move together"

Don't drift between strengths within a single manuscript. The abstract's "causes" should match the body's "causes." If the body says "associated with," the abstract should not say "causes."

## Don't soften inconvenient findings

If a robustness check fails, the manuscript reports that. The right response to "the result doesn't survive specification X" is not to omit specification X; it is to discuss what specification X is testing and why the result might not survive it.

## LaTeX hygiene

- Never break compilation. Always check that the manuscript compiles after a substantive edit.
- `\ref{}` and `\cite{}` must resolve. Undefined references (rendered as `??` in the PDF) are submission-blockers.
- Don't introduce new `\newcommand` or package imports without need; the existing preamble is the conventions.
- Tables and figures use `\label{}` immediately after `\caption{}`, not before.

## Don't claim coauthor approval you don't have

If a section was written by a coauthor, don't refactor it without flagging that you're doing so. The user can then decide whether to ping the coauthor before the change ships.
