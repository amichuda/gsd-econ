# Rule: pre-registration

Constraints on PAPs, pre-registration documents, and PAP-deviation handling.

## PAPs are commitments, not wishlists

The pre-analysis plan specifies the analyses you commit to running. It is not a place to enumerate every possible specification you might ever want. If a robustness check is uncertain, mark it as "exploratory" or omit it. Pre-specifying analyses you don't intend to run is a credibility cost when reviewers compare PAP to paper.

## Subgroups not pre-specified are exploratory, period

If a subgroup analysis isn't in the PAP, every reporting of that subgroup analysis later is exploratory — flag it as such in the paper, the response letter, and any presentation. Don't paper over the distinction.

## PAP deviations require disclosure

Any deviation from the PAP — including changes that referees specifically asked for — must be disclosed in:

1. The paper itself (a "deviations from PAP" subsection or footnote)
2. The response letter to the editor (if mid-revision)
3. STATE.md as an audit-trail entry

A PAP deviation that's not disclosed is a credibility failure that erodes the value of pre-registration entirely. Don't quietly drop a primary specification because it doesn't work; if it doesn't work, that is a finding that goes in the paper.

## Don't auto-submit

`/gsd-pre-register` never sends data to an external registry (AEA RCT Registry, OSF, AsPredicted, etc.). Submission requires the user's credentials and an intentional act on the registry's website. The command produces a draft document; the user submits.

## Don't infer from absence

If you can't find a PAP reference in the project, ask the user before assuming there isn't one. The PAP may be at a URL not in the repo; or the project may legitimately not be pre-registered (some retrospective work isn't); or there may be one that hasn't been linked yet.

## Pre-registration is a deliberate act

Don't auto-fill `prereg.url` in METHODOLOGY.md or PROJECT.md. If the user pre-registered, they tell you the URL. Filling it from a guess is worse than leaving it blank.

## Treat pre-registered analyses as primary

Even if a non-pre-registered specification produces a more elegant result, the pre-registered specification stays the primary one. Move other findings to a "secondary analyses" or "exploratory" section. Don't reorder for storytelling.
