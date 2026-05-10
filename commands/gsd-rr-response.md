---
description: Revise and resubmit cycle. Each referee comment becomes a phase in a new milestone. Produces response letter, diff document, and tracks which RUT tests need re-running given changes.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: [referee_report.pdf | referee_report.txt]
---

# /gsd-rr-response

You are managing a revise & resubmit. The structure is:

- One **milestone** per R&R round (R1, R2, R3...)
- One **phase** per substantive referee comment (or coherent group of comments)
- One **plan** per concrete change required
- One **response letter section** per phase

## Process

### Step 1 — Ingest the referee report

If a path was provided ($ARGUMENTS), read it. Otherwise prompt the user to paste or provide a path.

If PDF: extract text. If multiple referee reports + editor letter, separate into distinct documents.

### Step 2 — Decompose into actionable items

For each referee, parse comments into a numbered list. Classify each as:

- **Major substantive** — disagreement with identification, demand for additional analysis, claim of error
- **Minor substantive** — request for additional robustness, clarification of mechanism, additional citations
- **Presentation** — exposition, table layout, prose
- **Wishful** — requests we don't intend to address (e.g., "this would be a different paper")

Show the classification to the user. Confirm or adjust.

### Step 3 — Map to phases

Group items into phases. Each phase will produce:
- Code changes (if any)
- Manuscript changes
- One section of the response letter

A typical R&R has 4–8 phases:
- 1 phase per major substantive item
- 1 phase grouping multiple minor items by topic
- 1 phase for presentation/typo cleanup
- 1 phase for the deviations-from-pre-analysis disclosure update (if PAP exists and changes were made)
- 1 phase for response letter assembly + submission package

Show the proposed milestone structure. User approves or revises.

### Step 4 — Initialize milestone

Use `/gsd-new-milestone` (GSD core) to create a new milestone directory. Name it `R1-<short-summary>` or similar.

Within the milestone:
- `R1-EDITOR-LETTER.md` — verbatim editor letter
- `R1-REFEREE-{1,2,3}.md` — verbatim referee reports
- `R1-CLASSIFICATION.md` — your decomposition from Step 2
- `R1-RESPONSE-MAP.md` — phase ↔ comment mapping table

### Step 5 — Per-phase workflow (loop)

For each phase, follow the standard cycle:

1. `/gsd-discuss-identification N` — if the phase changes identification (e.g., a referee challenged the IV exclusion restriction), this is non-trivial. Otherwise, falls back to standard discuss.
2. `/gsd-plan-empirics N` — plans the analytical changes.
3. `/gsd-execute-phase N` — executes.
4. `/gsd-verify-replication N` — verifies. Critically: if any LOCKED decision in METHODOLOGY.md changed, re-run all tests for the affected methodology, not just this phase's tests.

After each phase:

5. **Write response section** — In `paper/response-letter/RX-phase-N.md`:

```markdown
### Comment <referee>.<number>
> <verbatim quote of referee comment>

**Response.** <one or two paragraphs>

**Changes made.**
- <change 1, with section reference>
- <change 2, with section reference>
- <if no changes made: explanation of why we disagree, with evidence>

**Page references.** Section X, Tables Y, Figure Z.
```

Atomic commit: `commit -m "R1.N: respond to referee X comment Y"`.

### Step 6 — Assembly phase

The final phase produces the submission bundle:

- `response-letter.pdf` — assembled from all `paper/response-letter/RX-*.md`. Include editor cover, then per-referee blocks.
- `manuscript-clean.pdf` — the revised paper without track changes.
- `manuscript-tracked.pdf` — with track changes (LaTeX `latexdiff` or Word equivalent).
- Updated replication archive — every change in code/data must propagate to the public replication package.

### Step 7 — Final verification

Run `/gsd-test-paper --severity blocker` against the revised paper. All blockers must pass before submission. If any fail, the R&R is not ready — surface them.

If `prereg.url` is set in METHODOLOGY.md and any analyses changed:
- Verify a "Deviations from pre-analysis plan" section exists (test: `experiment_field-pap-deviation-disclosed`)
- The section discloses what changed, why, and which results are now exploratory

### Step 8 — Submit checklist

Print the submission checklist:

```
[ ] response-letter.pdf assembled
[ ] manuscript-clean.pdf compiles
[ ] manuscript-tracked.pdf shows all changes
[ ] All blocker RUT tests PASS (gsd-test-paper run)
[ ] Replication archive updated
[ ] PAP deviations disclosed (if applicable)
[ ] Online appendix synced with main text
[ ] Coauthors signed off
```

When all checked, run `/gsd-complete-milestone` (GSD core) to archive R1 and tag the submission.

## Constraints

- **Do not silently change pre-registered analyses.** If a referee asks for a change to a primary specification, that's a PAP deviation. Disclose it explicitly in the paper and the response letter.
- **Do not "respond" by waving away.** Every comment classified as "wishful" still gets a response section explaining why we're not addressing it. Editors notice silent omissions.
- **Do not assume coauthor sign-off.** The submit checklist is for the user to confirm; never claim coauthors approved without evidence.
- **Preserve the response letter format the editor expects.** Some journals require comment-by-comment numbered responses; some want a thematic narrative. Read the editor letter carefully and match.
- **Always re-run verification on touched methodology.** If you re-estimated a result, every RUT test for the affected methodology must re-run, not just the test for this comment.

## Output

- New milestone directory `R<N>-...`
- All referee comments classified and mapped to phases
- Phase work executed and verified
- Response letter assembled
- Tracked-changes manuscript
- Updated replication archive
- Submission checklist confirmed
