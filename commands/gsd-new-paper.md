---
description: "Bootstrap a paper into the gsd-econ workflow. Supports two modes: --new (fresh project, framing interview + literature scout) and --adopt (mid-project retrofit, infers state from the existing manuscript and codebase). Auto-detects which mode to use unless overridden."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
arguments: "[--new | --adopt] [--manuscript <path>]"
---

# /gsd-new-paper

Single entry point for bringing a paper under gsd-econ. Two modes:

- **`--new`**: greenfield. You have a research question and maybe data; no manuscript yet. Runs a framing interview and literature scout, populates planning docs from templates.
- **`--adopt`**: brownfield. You have an existing manuscript draft, code, and partial results. Reads the manuscript and codebase to infer the methodology declaration; surfaces what's LOCKED vs OPEN; runs a baseline status report against the existing work.

If no mode flag is passed, the command auto-detects based on the project state.

## Auto-detection rules

Run these checks in order. The first match wins:

1. **`--adopt` if** any of: a `.tex`, `.qmd`, or `.Rmd` file exists with > 500 words of body text in a `paper/`, `manuscript/`, or top-level directory; OR a `tables/` directory contains compiled `.tex` tables; OR a `code/` or `R/` directory contains files with regression calls (`feols`, `lm`, `reghdfe`, `ivreg`, `regress`, `ols`).
2. **`--new` if** the project root is essentially empty (just a `.git/` and maybe a `README.md`).
3. **Ambiguous → ask**: present the user with what was found and let them confirm.

Tell the user explicitly which mode you've chosen and why before proceeding. They can override.

## Process — `--new` mode

Run the greenfield workflow.

### Step 1 — Initial framing (interview)

Ask the user, one or two questions per turn:

1. **Research question.** Phrase it as a single sentence answerable with empirical evidence.
2. **Contribution.** What would the abstract's "we show that..." sentence say?
3. **Target journal.** Top general / top field / specialty.
4. **Identification strategy.** What variation? DiD, RD, IV, RCT, OLS-with-controls, structural?
5. **Data.** Which dataset(s)? In hand, IRB review, or to be collected?
6. **Coauthors.** Who, division of labor.
7. **Timeline.** Submission target, conference deadlines, tenure clock.

Restate after each answer. Probe ambiguity (e.g., "I'm using DiD" but staggered with covariates → ask for the specific estimator).

### Step 2 — Literature scout

Spawn `econ-researcher`. Inputs: research question, contribution. Output: `.planning/research/literature-scout.md` with 5–15 published papers, 3–5 working papers, synthesis paragraph.

Wait for completion. Summarize findings to the user. Ask: does the contribution statement need refining given this landscape?

### Step 3 — Methodology declaration

Populate `.planning/METHODOLOGY.md` from the template. Confirm with user before saving.

### Step 4 — Project documents

Populate `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` from templates. ROADMAP defaults to the 9-phase empirical pipeline; adjust based on whether the paper is methodological vs applied.

### Step 5 — Sanity check

Show the user all four populated documents. Ask explicitly: "Anything to revise before we start phase 1?"

### Step 6 — Hand-off

Tell the user the next step is `/gsd-discuss-identification 1`. Commit.

---

## Process — `--adopt` mode

Existing project. Goal is to populate the planning docs from the manuscript and codebase, get a baseline test report, and pick up the workflow from the next decision point — without disturbing completed work.

### Step 1 — Inventory

Find the manuscript:
- Default search: `paper/*.tex`, `paper/*.qmd`, `manuscript/*.tex`, `*.tex` in root, then `*.qmd`, `*.Rmd`.
- If `--manuscript <path>` was passed, use that.
- If multiple candidates, ask the user which one.

Read the manuscript fully. Identify sections (abstract, intro, data, identification, results, robustness, conclusion).

Inventory the codebase:
- Glob for analysis scripts (`code/*.R`, `R/*.R`, `code/*.do`, `code/*.py`).
- Look for regression calls and what packages are used (`fixest`, `lfe`, `did`, `bacondecomp`, `ivreg`, `rdrobust`, `synthdid`, etc.).
- Inventory output: `tables/`, `figures/`, `output/`, etc.

Inventory data — but **read-only**:
- List `data/` subdirectories. Don't read raw data files (privacy, size).
- Note the apparent panel structure if visible from clean data filenames.

Build a brief inventory report and show it to the user. Confirm what you found is correct.

### Step 2 — Infer methodology declaration

From the manuscript's identification section and codebase signals, infer:

- **Primary methodology**: package usage is the strongest signal. `did::att_gt` → `did`; `fixest::feols` with `i(rel_time, treat)` event-study → `did`; `ivreg`, `ivreg2`, `feols(... | ... | ... ~ ...)` → `iv`; `rdrobust`, `rdd` → `rdd`; `randomization` keywords + balance tables → `experiment_field`; `lm`/`reghdfe` only with rich controls → `ols`.
- **Secondary methodologies**: anything used for robustness (often OLS as baseline; IV as robustness for a DiD paper, etc.).
- **Scope**: `paper` by default (we're adopting a paper-in-progress).
- **Target journal**: ask the user (or read from a cover letter draft if present).
- **Pre-registration**: search for "pre-registration", "AEA Registry", "OSF", "AsPredicted" mentions in the manuscript. If found, ask user for the URL; if not found and methodology suggests RCT, ask whether one exists.
- **Cluster level / SE method**: extract from regression calls or table footnotes.
- **Sample restrictions**: extract from data / methods section prose.

Show the inferred declaration to the user as a draft `METHODOLOGY.md`. They edit, you save.

### Step 3 — Literature scout

Spawn `econ-researcher` before reconstructing requirements. Inputs:
- Manuscript abstract and introduction, if present
- Inferred research question and contribution from Step 2
- Inferred methodology declaration from Step 2
- Existing bibliography/citations from the manuscript, if visible

Output: `.planning/research/literature-scout.md` with 5–15 published papers, 3–5 working papers, synthesis paragraph, and notes on whether the existing manuscript's contribution claim still looks distinct.

Wait for completion. Summarize findings to the user. Ask: does the contribution statement or inferred methodology need refining given this landscape?

If the user explicitly chooses to defer the scout, write a stub `.planning/research/literature-scout.md` that states the scout was deferred, records why, and warns that downstream commands will have weaker literature context. Do not silently proceed with the file missing.

### Step 4 — Reconstruct REQUIREMENTS.md from the existing paper

This is the trickiest part. Walk through the manuscript with the user, asking:

- "The abstract claims [X]. Is that the primary hypothesis, or are there others?"
- "Table 3 shows the main result. Is that the primary specification, or one of several?"
- "I see robustness in Section 5: [list]. Are these locked, or are some still being explored?"
- "What's NOT in the paper that you'd still consider? (For the OPEN list.)"

Populate REQUIREMENTS.md with:
- Hypotheses → mostly LOCKED (since they're already in the manuscript)
- Primary outcomes → LOCKED
- Sample → LOCKED
- Specification choices → LOCKED for what's in the main results, OPEN for anything the user is still revisiting

**Be honest about LOCKED.** If the user wants to flag something as OPEN that's already in the manuscript, that's a decision to revisit — surface this as a meaningful choice with downstream implications (might require a re-estimation phase, might require disclosure if pre-registered).

### Step 5 — Backfill ROADMAP.md

Don't backfill completed phases in detail. Use this minimal pattern:

```markdown
## Phase 1 — Data acquisition and cleaning [COMPLETED PRE-ADOPTION]
Brief: <one-line summary of what exists>
Artifacts: <data/clean/*.parquet, etc.>

## Phase 2 — Stylized facts [COMPLETED PRE-ADOPTION]
...

## Phase 3 — Identification diagnostics [COMPLETED PRE-ADOPTION]
...

## Phase N — <next thing> [CURRENT]
Goal: <what comes next>
...
```

Ask the user where they actually are. Common answers:
- "Robustness round before resubmission" → current phase = robustness, prior all completed
- "Drafting intro" → current phase = manuscript writing
- "Replication archive" → jump straight to phase 9
- "Just got referee reports" → don't use new-paper; redirect to `/gsd-rr-response`

### Step 6 — Initialize STATE.md with adoption record

Append an explicit adoption marker:

```markdown
## <ISO timestamp> — gsd-econ adoption (brownfield)
Project state at adoption:
- Manuscript: <path>, ~<word count> words
- Phases completed pre-adoption: 1 through <N>
- Current phase: <N+1> — <name>
- Inferred methodology: <primary>, secondary <list>
- Pre-registration: <none | URL>
- Notable: <any LOCKED-from-OPEN flags the user surfaced in Step 4>
```

This is the audit trail for what existed when adoption happened. Critical for honesty later: a referee asking "when did you commit to specification X?" can be answered with "before adoption, see commit history" without false claims.

### Step 7 — Baseline test report

Run `/gsd-test-paper --severity blocker --severity warning` against the existing manuscript and codebase. This produces `.planning/test-runs/<ISO>-test-paper.md` showing:

- Which RUT tests pass (encouraging — you've already done good work)
- Which fail (the retrofit gaps — these are real but bounded)
- Which need evidence (artifacts the framework expects but doesn't find)

Surface the blockers explicitly. **Do not auto-generate fix plans for pre-adoption work.** That's the user's call: some failures are real defects to fix; some are framework artifacts that don't actually matter for this paper.

For each failure, present three options:

- **Address**: this is a real gap, treat as a fix-plan in the current phase
- **Acknowledge**: log to STATE.md as known, won't fix this round (e.g., the framework wants Conley SEs; the paper has cluster SEs and the user judges that's fine)
- **Exclude**: add to `METHODOLOGY.test_exclusions` with a written justification

### Step 8 — Hand-off

Based on Step 5's answer about current phase, point the user at the right next command:

- Robustness or new analysis → `/gsd-discuss-identification <N>`
- Drafting → continue manually; recommend `/gsd-test-paper` periodically
- Replication archive → `/gsd-submit-paper`
- Referee response → stop, go to `/gsd-rr-response`

Commit. Final message: "gsd-econ adoption complete. Existing work preserved; framework engaged from phase <N+1> onward."

---

## Constraints (both modes)

- **Never invent literature you didn't search for.** If `econ-researcher` fails, say so explicitly and ask the user to provide seed citations.
- **Never invent decisions on the user's behalf.** Suggest, don't decide. The user owns identification choices.
- **Never fill `prereg.url` automatically.** Pre-registration is a deliberate act with a separate command.
- **One question per turn** unless the user is clearly batching.

## Constraints (`--adopt` mode specifically)

- **Do not modify code or manuscript files during adoption.** Read-only over the existing work. The only writes are to `.planning/`.
- **Do not retrospectively run fix plans for pre-adoption work.** The point of adoption is to engage the workflow going forward, not to relitigate completed phases. The user can choose to address gaps; you don't auto-loop.
- **Do not claim phases are COMPLETED that the user hasn't confirmed.** ROADMAP backfill is provisional until the user signs off.
- **Do not silently overwrite if `.planning/` already exists.** If a previous gsd-econ install left planning docs, ask before merging or replacing.
- **Do not silently skip the literature scout.** If the user defers it, write an explicit deferred-scout stub at `.planning/research/literature-scout.md`.
- **Do not infer pre-registration from absence of evidence.** If you can't find a PAP reference, ask.
- **Be honest about retrofit costs.** If the existing manuscript uses naive TWFE for staggered DiD, surface this clearly. Do not soft-pedal it because the work is already done.

## Output (`--new` mode)

- `.planning/PROJECT.md`, `REQUIREMENTS.md`, `METHODOLOGY.md`, `ROADMAP.md`, `STATE.md`
- `.planning/research/literature-scout.md`
- Clean commit
- Pointer to `/gsd-discuss-identification 1`

## Output (`--adopt` mode)

- `.planning/PROJECT.md`, `REQUIREMENTS.md`, `METHODOLOGY.md`, `ROADMAP.md` populated from inferred state
- `.planning/research/literature-scout.md` populated by `econ-researcher` or an explicit deferred-scout stub
- `.planning/STATE.md` with explicit adoption marker
- `.planning/test-runs/<ISO>-test-paper.md` baseline report
- Triage of any blockers surfaced (addressed / acknowledged / excluded)
- Clean commit with message `chore: adopt gsd-econ (brownfield, current phase: N)`
- Pointer to the appropriate next command based on current phase
