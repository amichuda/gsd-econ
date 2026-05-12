# Decision logging

This rule applies during the execute phase and anywhere else an agent
makes contested judgment calls about data cleaning, variable
construction, or methodology.

The goal is to make robustness analysis cheap by capturing *what could
have been done differently* at the moment a decision is made — before
the result is known. The output is a `decisions.jsonl` file in the
project root that downstream commands (`/gsd-multiverse`,
`/gsd-verify-replication`) read.

This is part of what distinguishes a transparent empirical analysis
from a confident one. Authors who pre-register specifications constrain
themselves on the regression side; logged cleaning decisions extend
that discipline to the data-construction side, which is where most
unrecorded researcher degrees of freedom actually live.

## When to log

Log a decision when **all** of these are true:

1. **It changes downstream results in a meaningful way.** A renamed
   column doesn't qualify. Recoding the documented missing code 9999
   to NA doesn't qualify. Filtering out observations based on a cutoff
   does qualify, because moving the cutoff would change the estimate.

2. **A competent referee could plausibly suggest an alternative.** "We
   dropped the four students who switched colleges mid-study" is
   contested — a referee might want to see the result with them
   included under their original arm. "We dropped observations where
   the participant ID didn't match the consent form" is not contested,
   because data integrity issues have a forced answer.

3. **The decision isn't pre-registered.** PAP-committed decisions are
   constraints, not multiverse axes. Log them with
   `pap_committed: true` so the multiverse runner knows to hold them
   fixed. Logging them is still useful for transparency and for
   downstream consumers (the multiverse command can show "here are the
   PAP commitments, here are the free axes").

## What to log

Every logged decision is one JSON object on one line of
`decisions.jsonl`. The schema is:

```json
{
  "id": "d042",
  "phase": "cleaning",
  "type": "filter",
  "variable": "weight_change_kg",
  "decision": "abs <= 5",
  "alternatives": ["abs <= 10", "abs <= 3", "no filter"],
  "justification": "Weight changes >5kg between weekly visits suggest measurement error or different person; conservative threshold for the population.",
  "pap_committed": false,
  "n_affected": 23,
  "timestamp": "2026-05-12T14:30:00Z",
  "agent": "econometrician"
}
```

Required fields: `id`, `phase`, `type`, `decision`, `justification`,
`pap_committed`. Other fields are recommended but optional.

### Field guidance

- **`id`**: short string, unique within the project. Use `d###`
  format. Increment from the highest existing id when adding new
  decisions.
- **`phase`**: one of `cleaning`, `construction`, `methodology`,
  `inference`. `cleaning` is row/observation-level work;
  `construction` is variable definition; `methodology` is regression
  specification; `inference` is SE structure, multiple-testing, etc.
- **`type`**: short tag describing what kind of decision this is.
  Common values: `filter`, `recoding`, `missing_data`,
  `variable_construction`, `time_window`, `outlier_handling`,
  `se_clustering`, `stratum_fe`, `controls`, `estimator_choice`,
  `multiple_testing`. Add new types as needed.
- **`variable`**: the variable name being decided on. Null for
  decisions that aren't variable-specific (e.g., choice of estimator).
- **`decision`**: a short string describing the chosen option, written
  so a human can parse it without context. "abs <= 5" is fine if the
  `variable` field tells you what's being filtered.
- **`alternatives`**: array of strings, each in the same format as
  `decision`. **Each alternative must be a choice a competent
  researcher could defend.** Don't pad with absurd alternatives just
  to lengthen the list. Three is a sensible target; one is acceptable
  if only one alternative is defensible; zero alternatives means the
  decision should not have been logged in the first place (it wasn't
  contested).
- **`justification`**: 1-3 sentences explaining why this choice. State
  the reasoning, not just the choice. "Conservative threshold for the
  population" is better than "best for our sample." If the
  justification references prior literature, cite it inline.
- **`pap_committed`**: boolean. `true` if the PAP fixes this choice.
  When `true`, the multiverse runner will hold the decision at the
  committed value rather than vary it. If unsure, check the PAP
  document; if no PAP exists, default to `false`.
- **`n_affected`**: integer, optional. Number of observations or rows
  affected by this decision. Useful context for the multiverse output
  ("this choice affects 23 observations out of 340").
- **`timestamp`**: ISO 8601 datetime, optional. The multiverse runner
  uses this to reconstruct the order decisions were made in.
- **`agent`**: name of the agent that logged the decision, optional.

## What NOT to log

These categories of decisions are explicitly excluded. Logging them
pollutes the multiverse with implausible specifications and wastes
compute.

1. **Documented missing codes.** If 9999 means missing per the data
   dictionary, recoding it to NA is forced. Don't log.

2. **Data integrity exclusions.** If a row has a participant ID that
   doesn't match the consent form, dropping it is forced. If a date
   is structurally impossible (e.g., a follow-up survey dated before
   the baseline), dropping or correcting is forced.

3. **Trivial restructurings.** Renaming columns, reshaping wide to
   long, joining tables. These don't change downstream estimates.

4. **Type conversions.** Casting strings to numerics, parsing dates.
   Forced by the analysis software.

5. **Pre-registered specifications.** Log these with
   `pap_committed: true`, but don't generate spurious alternatives for
   them — the alternatives field should be empty or a single
   "non-PAP-committed alternative for transparency" if any reasonable
   reviewer would consider one.

6. **Mechanical choices forced by sample size.** If a fixed effect has
   a singleton cell, dropping that cell is forced (or use a different
   stratum definition, which is itself a logged decision). Don't log
   the singleton drop separately.

When in doubt, ask: **would a referee write a comment asking about
this choice?** If yes, log. If no, don't.

## Where the file lives

`decisions.jsonl` lives in the project root. It is append-only during
the execute phase — agents add lines, never modify or delete
existing ones. Once a decision is logged, it stays in the log even
if the agent later changes its mind; in that case, log a new
decision that supersedes the earlier one, and reference the earlier
`id` in the justification ("supersedes d017: realized the original
cutoff excluded a valid subset").

The log is plain JSON Lines so it's diffable, greppable, and
inspectable without any framework support. A referee can read it
directly.

## How the multiverse runner uses it

`/gsd-multiverse` reads `decisions.jsonl`, filters to decisions where
`pap_committed: false` and `alternatives` is non-empty, presents the
proposed grid to the author for pruning, then runs the analysis once
per cell of the resulting cross-product.

The author can:
- Drop axes that they consider not contested in retrospect.
- Drop alternatives that don't actually need testing.
- Add axes the agent missed.
- Compose with a methodology grid from `config/multiverse-grids/`.

The output is a specification curve showing the headline estimate
across all specifications, plus an audit table that becomes the
paper's supplementary material.

## Edge cases

**Multiple decisions interacting.** Two decisions might be logically
linked: if you choose "include switchers in original arm" for
`d004`, you also need a decision about how to handle their post-switch
observations (`d004b`). Log them as separate decisions but reference
the link in the justifications. The multiverse runner will let the
author mark them as a joint axis if needed.

**Continuous parameter spaces.** A bandwidth choice in RDD is
continuous, not discrete. The logged alternatives should be specific
candidate values (e.g., [0.05, 0.10, 0.15, 0.20]), not "any value in
[0.01, 0.50]". The multiverse runs over the discrete grid; sensitivity
to bandwidth is shown by spanning the candidates.

**Decisions that depend on data inspection.** Some choices only make
sense after you've looked at the distribution. "We winsorized at the
99th percentile" is a decision made after seeing the right tail. Log
it with alternatives that reference what you saw ("99th percentile",
"95th percentile", "winsorize only the top 3 observations"). The
multiverse will test sensitivity even though the *initial* choice was
data-driven; that's exactly what makes it useful.

**Computational cost.** If logging N decisions with average K
alternatives implies a multiverse of K^N specifications, and K^N >
1000, the runner falls back to fractional factorial sampling rather
than full enumeration. The decision log doesn't need to be aware of
this; the runner handles it.

## Honest limits

The framework can only flag what the agent recognizes as contested.
Decisions baked into upstream data — how the dataset was constructed
before it reached the analysis pipeline — are invisible to it. If the
survey company excluded all respondents who answered "prefer not to
answer" on a particular question, that's not in the agent's logs
because the agent never saw the excluded rows. Document upstream
exclusions in `data-handling.md` or `METHODOLOGY.md`; the decision
log is for analysis-side choices only.

The multiverse also can't second-guess the PAP. A pre-registered
specification might be defensible at registration but suboptimal in
retrospect. The decision log doesn't open PAP commitments back up;
that's deliberate. Robustness is for the unconstrained choices, not
for re-litigating commitments.
