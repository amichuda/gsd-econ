---
description: Generate an AEA RCT registry / OSF / pre-analysis-plan from REQUIREMENTS.md and METHODOLOGY.md. Produces a registry-ready document plus a hash committed to STATE.md so deviations can be detected later.
allowed-tools: Read, Write, Edit, Bash
---

# /gsd-pre-register

Pre-registration is a deliberate act. Once you submit a PAP to a registry, the hypotheses, primary outcomes, and pre-specified analyses are locked. Deviations later have to be disclosed.

This command produces the document and the lock.

## Process

### Step 1 — Confirm intent

Ask the user explicitly:

> Pre-registration commits you publicly to the analyses below. Once submitted to a registry, you can still add analyses later, but they're labeled "exploratory" by default and any deviation from the pre-specified plan must be disclosed in the published paper. Confirm you want to proceed?

If no: stop. Tell user to come back when ready.

If yes: continue.

### Step 2 — Read source documents

Load:
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/METHODOLOGY.md`
- `.planning/ROADMAP.md`
- `.planning/research/literature-scout.md`

### Step 3 — Choose registry

Ask the user which registry:

- **AEA RCT Registry** — for field experiments, formal RCT structure
- **OSF** — flexible, accepts most designs including observational
- **AsPredicted** — fast, structured, less detail
- **EGAP** — for governance/political-economy field experiments
- **Other** — user provides format

Use the registry's required fields as the document structure.

### Step 4 — Generate the PAP

Sections to populate:

1. **Title** — paper title from PROJECT.md
2. **Authors** — coauthors from PROJECT.md
3. **Abstract** — 250–500 words. Research question + design + primary hypothesis + expected contribution.
4. **Hypotheses** — primary and secondary, distinguished. Each phrased as a falsifiable statement with the alternative.
5. **Outcomes** — primary outcome variable(s). Operational definitions. Construction from raw data. (If multiple primary outcomes, multiple-testing approach goes here.)
6. **Sample** — population, sampling frame, eligibility criteria, expected sample size.
7. **Treatment** — what the intervention is, dose, timing, randomization unit, stratification.
8. **Power** — minimum detectable effect, assumed ICC, alpha, power. Show the calculation.
9. **Estimation** — main specification(s). Cluster level. SE method. Inference (Bonferroni, Romano-Wolf, FDR, sharpened q-values, etc.).
10. **Subgroups / heterogeneity** — pre-specified subgroups, with the hypothesis for each. Distinguish from exploratory.
11. **Robustness** — pre-specified robustness checks.
12. **Attrition / missing data** — expected attrition, plan for handling, balance check.
13. **Compliance** — ITT vs LATE, instrumented analysis if relevant.
14. **Spillovers** — assumed away or modeled; if modeled, how.
15. **Deviations protocol** — explicit statement that deviations will be disclosed in the paper.

For non-RCT designs (DiD, RDD, IV with observational data), drop fields 7 and 12, repurpose 8 (power → identification diagnostics plan), keep the rest.

### Step 5 — Show to user

Show the full draft. Ask:

> Read carefully. This locks in the pre-specified analyses. Approve, request edits, or cancel.

Iterate until user approves.

### Step 6 — Save and hash

Save to `paper/preregistration.md` (or `.tex` if user prefers).

Compute SHA-256 hash of the file content. Append to `.planning/STATE.md`:

```markdown
## <ISO timestamp> — Pre-registration locked
File: paper/preregistration.md
SHA-256: <hash>
Registry target: <registry>
Status: drafted, not yet submitted
```

The hash is the integrity check. After submission, paste the registry URL into `METHODOLOGY.md`:

```yaml
prereg:
  required: true
  url: https://<registry-url>
  hash: <sha-256>
  submitted_at: <date>
```

### Step 7 — Submission instructions

The command does not submit to the registry — that's a manual step requiring user credentials. Print the user-facing instructions:

```
1. Go to <registry URL>.
2. Create a new pre-registration entry.
3. Paste the contents of paper/preregistration.md into the relevant fields.
4. Submit.
5. Once submitted, run:
   /gsd-pre-register --record-url <url>
   to update METHODOLOGY.md with the registry URL and submission date.
```

### Step 8 — Update tests

After registration is recorded:

- The test `experiment_field-pap-deviation-disclosed` becomes active for this project (verifier checks `prereg.url` is set; if so, requires a "Deviations from PAP" section in the manuscript).

Commit `git add . && git commit -m "chore: pre-registration drafted (hash <short-hash>)"`.

## Constraints

- **Do not auto-submit.** This command never sends data to an external registry. Submission requires the user's credentials and intentional act.
- **Do not pre-specify analyses you don't intend to run.** If the user is uncertain whether a robustness check is doable, mark it as "exploratory" or remove it. Pre-registration is not a wishlist.
- **Do not omit subgroups.** If the user doesn't pre-specify subgroups, every subgroup analysis later is exploratory. The user should know this trade-off — surface it.
- **Distinguish primary from secondary outcomes clearly.** Multiple primary outcomes require an explicit multiple-testing approach.
- **The hash is a contract.** Once recorded in STATE.md, it should never be edited. If the PAP changes after submission, that's a deviation to be disclosed in the paper.

## Output

- `paper/preregistration.md`
- Hash recorded in `.planning/STATE.md`
- Submission instructions printed
- Commit made
