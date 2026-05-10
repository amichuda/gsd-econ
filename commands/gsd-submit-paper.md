---
description: Package a paper for submission. Replaces /gsd-ship for research workflows. Runs full RUT test battery, invokes referee-sim, builds replication archive, and produces the submission bundle.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: [target_journal]
---

# /gsd-submit-paper

Final phase. Produces the bundle you upload to a journal portal.

## Process

### Step 1 — Pre-flight checks

Read:
- `.planning/PROJECT.md` (target journal, if not in $ARGUMENTS)
- `.planning/METHODOLOGY.md`
- All `.planning/phases/*/VERIFICATION.md`
- `.planning/STATE.md`

Check:
- Every phase has a `VERIFICATION.md` with verdict PASS or PROVISIONAL-accepted.
- No open blockers in any phase.
- If `prereg.required: true`, `prereg.url` is set.
- Manuscript LaTeX compiles cleanly (run `pdflatex` and check exit code).
- Replication archive directory exists and is non-empty.

If any check fails, list what's missing and STOP. Do not proceed to packaging.

### Step 2 — Full test battery

Run `/gsd-test-paper --severity blocker --severity warning`. Block submission if any blockers fail. Surface warnings for user awareness — these don't block submission, but the user should know.

### Step 3 — Polish pass

Invoke `/gsd-polish-pass` to run the five polish agents (numbers, cross-refs, bibliography, consistency, claims). This is a final-pass audit catching cross-cutting bugs the per-phase RUT tests can't see.

If polish-pass returns NEEDS-REVISION:
- Show the user the SUMMARY.md
- Apply fix plans via `/gsd-execute-phase polish` (or surface for manual fix)
- Re-run polish-pass
- Repeat up to the polish-pass cap (default 2 rounds)

If after the cap there are still BLOCKER findings: stop. Surface the open blockers and ask the user to decide whether to override (acknowledge as known weakness) or address manually.

Block submission packaging if any polish BLOCKER remains open.

### Step 4 — Referee simulation

Spawn `referee-sim` agent with the full manuscript + `METHODOLOGY.md` + research literature. Instructions:

> You are an unusually competent and slightly grumpy referee for <target_journal>. You have read the paper. Write a referee report:
>
> 1. Summary (2 paragraphs) — what the paper does, what it claims.
> 2. Major comments (4–8) — substantive concerns about identification, interpretation, contribution, or methods.
> 3. Minor comments (5–10) — exposition, robustness, citations.
> 4. Recommendation — Reject / Major revision / Minor revision / Accept.
>
> Use the judgment-clarity tests in the merged registry as your checklist:
> - universal-contribution-is-new
> - universal-contribution-is-interesting
> - methodology-specific judgment tests
>
> Be specific. "Identification is unclear" is not a comment; "the exclusion restriction in equation 4 requires that <X>, but the paper does not address <Y> as a potential violation" is.

Save output to `.planning/submission/referee-sim-report.md`.

### Step 5 — Show referee-sim to user

Present the simulated referee report. Three options:

- **Address now** — pause submission, treat as a mini-R&R, run `/gsd-rr-response` with this report as input.
- **Acknowledge and proceed** — log the simulated report to `STATE.md` as known weaknesses; user accepts they may surface in real review.
- **Override** — user decides the simulated referee is wrong (rare; document why).

Do not auto-decide. The user owns this call.

### Step 6 — Build the bundle

If user proceeds, build:

```
submission/
├── manuscript.pdf                    # main text
├── manuscript.tex                    # source
├── online-appendix.pdf               # appendix material
├── online-appendix.tex
├── cover-letter.pdf                  # to editor
├── replication/
│   ├── README.md                     # how to run
│   ├── data/                         # public/derived data only
│   │   ├── README.md                 # data dictionary
│   │   └── ...
│   ├── code/                         # full pipeline
│   │   ├── 00_master.{R|do|py}       # master script
│   │   └── ...
│   ├── output/                       # generated tables and figures
│   └── requirements.{txt|renv.lock|...}  # env spec
└── declarations/
    ├── conflicts-of-interest.md
    ├── data-availability.md
    └── ai-use-disclosure.md          # disclose use of LLM tooling per journal policy
```

For each item, validate:

- **manuscript.pdf** — compiled cleanly, fonts embedded, page count within journal limits, anonymized if double-blind.
- **online-appendix.pdf** — same.
- **cover-letter.pdf** — addresses editor by name, states submission type (new submission / R&R), declares conflicts, lists suggested/excluded reviewers if applicable.
- **replication/** — runs end-to-end on a fresh machine. The `replication-verifier` should run a smoke test: clone-equivalent into a temp directory, run `00_master`, diff outputs against the committed tables.
- **data/** — restricted-access data is not bundled; instead include access instructions and a synthetic / public substitute for tutorial purposes. NEVER commit PII or restricted-use survey data to the replication archive.
- **ai-use-disclosure.md** — be honest about LLM-assisted analysis, drafting, and tooling. Most journals now require this.

### Step 7 — Final verification

Run the `universal-replication-reproduces-results` test against the bundled `replication/` directory. This is the single most important test — submission fails if the replication archive doesn't reproduce.

### Step 8 — Submission instructions

Print:

```
Submission bundle ready: submission/
Target journal: <target>
All blocker tests: PASS
Referee-sim concerns: <addressed|acknowledged|overridden>
Replication smoke test: PASS

Next steps (manual):
1. Review submission/cover-letter.pdf one more time.
2. Confirm coauthor sign-off.
3. Upload to <journal portal URL>.
4. After submission, run /gsd-submit-paper --record-id <portal-id> to log.
```

### Step 9 — Record

After user records the submission ID, append to STATE.md:

```markdown
## <ISO timestamp> — Submitted to <journal>
Submission ID: <id>
Bundle hash: <SHA-256 of submission/ directory>
Open issues acknowledged: <list from referee-sim>
Expected response: <approximate>
```

### Step 10 — Complete milestone

Run `/gsd-complete-milestone` (GSD core) to archive the work and tag the release. Tag format: `submitted-v<n>` (e.g., `submitted-v1` for initial submission, `submitted-v2` after R1 acceptance, etc.).

## Constraints

- **Do not bypass the blocker test gate.** If any blocker test fails, packaging stops. There is no `--force` flag.
- **Do not auto-resolve referee-sim concerns.** Even if the referee-sim raises concerns the user thinks are wrong, log them. Real referees may agree.
- **Do not include restricted-use data in the replication archive.** Validate `data/` against a deny list (PII patterns, IRB-restricted datasets, proprietary data identifiers). Surface concerns and stop if found.
- **Be honest in the AI-use disclosure.** This is increasingly journal-mandated. List the tools used (e.g., "Claude Code with gsd-econ for orchestration; LLM-assisted drafting of literature review; manual coauthor review of all final text"). Avoid both over-claiming AI involvement (some journals reject pure AI-generated text) and under-claiming (which is dishonest).
- **Anonymize for double-blind journals.** Strip author info, acknowledgments, and IRB protocol numbers from the manuscript PDF, but keep them in source for re-enabling later.

## Output

- `submission/` directory, complete and validated
- Replication smoke test PASS
- Referee-sim report logged
- Submission ID recorded after upload (manual step)
- Milestone completed and tagged
