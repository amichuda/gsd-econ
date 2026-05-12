# Getting started: v0.3 evaluation of gsd-econ on Breza et al. (2026)

This walks through running the gsd-econ framework on a real post-cutoff
economics paper across **three evaluation modes**, with the goal of
producing real evidence on whether the framework adds value.

> If you just want to try the framework on your own work, skip this
> doc and read [`INSTALL.md`](INSTALL.md) → [`README.md`](README.md) →
> [`docs/multiverse.md`](docs/multiverse.md). This file is the
> evaluation protocol, not a user tutorial.

Target paper:

> Emily Breza, Kevin Carney, Vijaya Raghavan, Kailash Rajah, Thara
> Rangaswamy, Gautam Rao, Frank Schilbach, Sobia Shadbar, and James
> Stratton (2026). "Financial Incentives, Health Screening, and
> Selection into Mental Health Care: Experimental Evidence from
> College Students in India." NBER Working Paper 34819.
> <https://www.nber.org/papers/w34819>

A 4-arm factorial RCT (N=340) in Chennai, India, testing how cash
incentives and personalized mental-health-screening feedback affect
therapy uptake. Pre-registered (AEARCTR-0015379 and NCT06887569).

Why this paper: methodology is squarely in dev-econ wheelhouse (dev
RCT, India, behavioral × health), it's post-cutoff (January 2026 first
version), it's pre-registered so there's ground truth for
plan-vs-paper comparison, and the team has strong replication norms.

## The three evaluation modes

| Mode | What it tests | Time | What it tells you |
|------|---------------|------|-------------------|
| **A. Greenfield** | Forward construction — does the framework help *build* a paper from a design brief? | 6-8 hours | Whether the framework's central design claim (forward construction, not just audit) holds up |
| **B. Audit** | Post-hoc review — does the framework help *audit* a finished paper? | 4-6 hours | Whether the framework adds value as a polish/referee-sim tool, the most common user workflow |
| **C. Multiverse** | Automated robustness (v0.3 contribution) — does `/gsd-multiverse` produce a useful specification curve? | 4-8 hours | Whether v0.3's multiverse machinery adds value, and how reliably the decision-logging agent catches contested choices |

Run **A first, then B, then C**, ideally on different days and in
separate chat sessions. The order matters:

- If you run B before A, what the framework tells you about the
  finished paper will leak into how you write the greenfield brief and
  contaminate Evaluation A.
- Evaluation C requires the paper's analysis code; if the replication
  archive isn't out yet, run C on a paper of your own with code you
  have. The mechanism is the same; the specific decisions differ.

If you only have time for one: run **A**. It's the harder and more
honest test.

---

## Honest expectations going in

- The framework is **v0.3.0**. It passes its own structural tests
  (~247 of them). It has not yet been run end-to-end on a real paper.
  Things will break.
- For A and B you'll skip `/gsd-verify-replication` because no
  replication archive exists for Breza et al. yet. Most framework
  value is in pre-execution discipline and post-writing audit anyway.
- Evaluation C's most likely failure mode: the decision-logging agent
  undercounts contested decisions. The rule file
  (`rules/decision-logging.md`) is well-reasoned but unvalidated.
  Expect to manually augment `decisions.jsonl` after the agent's
  initial pass. **Track how many you add by hand** — that's data
  point #1 from the eval.
- Realistic A outcome: a credible *first draft* of methodology
  documents with gaps, not an exact match to what Breza et al. did.
  Grading question: would this output, edited by a competent
  researcher, save meaningful time?
- Realistic B outcome: 50-65% recall on identification concerns
  you'd raise yourself, 55-75% precision. Polish-pass catches real
  issues mixed with noise.
- Realistic C outcome: a runnable multiverse with a specification
  curve and HTML report, but the grid is smaller than what you'd
  want because the agent missed some decisions.
- Total time: 15-20 hours over 3-5 working days for all three.
  8-12 if you only run A. 4-8 for C alone (after the prerequisites).

---

## Step 0: Block time

Schedule. Don't interleave with other work — the evaluation needs
sustained attention to be informative.

---

## Step 1: Install the framework (30 minutes)

```bash
mkdir -p ~/src && cd ~/src
tar -xzf ~/Downloads/gsd-econ-publish-ready.tar.gz
cd gsd-econ
make verify              # ~247 tests, auto-uses uv if available
shellcheck install.sh    # lint
```

Both should pass. Then wire into your runtime:

```bash
# OpenCode users — the recommended v0.3 flow:
./install.sh --runtime opencode --interactive-models
# Walks you through provider + tier choices, generates a YAML, applies it.

# Or use a pre-made template (cheaper for evaluation runs):
./install.sh --runtime opencode \
    --models-config config/model-configs/openrouter-hybrid.yaml

# Claude Code users:
./install.sh --runtime claude --global
```

The hybrid OpenRouter template routes light/standard tiers through
DeepSeek V4 and heavy through Claude Opus. Total spend for a full
A+B+C evaluation should be ~$10-25 depending on how much you iterate.

---

# EVALUATION A: Greenfield mode

Test whether the framework, given only what the team knew at design
time, can produce credible methodology proposals.

## A.1: Set up the greenfield project (15 min)

```bash
mkdir -p ~/eval/breza-greenfield
cd ~/eval/breza-greenfield
git init
~/src/gsd-econ/install.sh --project --runtime opencode \
    --models-config ~/src/gsd-econ/config/model-configs/openrouter-hybrid.yaml
```

**No paper/ directory.** Do not put the published PDF anywhere the
framework can see it.

## A.2: Write your reference design list FIRST (90 min)

**Before running anything**, read the actual paper carefully in a
*different* directory, then write your own predictions of what design
choices a strong team would have made given only the brief below.

Save to `~/eval/breza-grading/reference-design.md`. Outside the
project directory. The framework cannot see this file.

For each design dimension, predict:

- **Experimental design.** Number of arms? Factorial vs sequential?
- **Randomization.** Individual vs cluster? Stratification variables?
- **Primary outcome.** Concrete measure? Window?
- **Secondary and mechanism outcomes.**
- **Sample size justification.** MDE under reasonable assumptions?
- **Primary specification.** Controls? Stratum FE?
- **Multiple testing.** Romano-Wolf? Westfall-Young?
- **SE structure.** Robust? Cluster? At what level?
- **Heterogeneity / targeting.** Operationalization?
- **PAP scope.** What's primary vs secondary vs exploratory?

The grading later compares three things: your predictions, the
framework's proposals, and the paper's actual choices.

## A.3: Bootstrap with the design brief

Open Claude Code or OpenCode in `~/eval/breza-greenfield/`. Paste the
prompt below verbatim.

### Greenfield prompt

```text
I'm starting a new empirical economics research project and want to
use gsd-econ to scaffold it. Please use /gsd-new-paper to bootstrap
the project from the brief below.

The brief contains the design context as of February 2025 — what the
research team knew before making methodology choices. Do NOT propose
specific methodology choices in the bootstrap step; just populate the
high-level .planning/PROJECT.md, .planning/REQUIREMENTS.md, and the
context portions of .planning/METHODOLOGY.md. Save specific design
choices (number of arms, randomization unit, outcome operationalization,
SE structure, etc.) for the discussion and planning phases that come
next.

If anything in the brief is underspecified — i.e., I haven't told you
something you'd need to know to design the study — flag it explicitly
and ask me, rather than picking a default and proceeding silently. The
metacognition rules in rules/uncertainty-honesty.md apply: don't fill
gaps with plausible-looking content; surface them.

# Design brief (Feb 2025, before any data collection)

## Substantive motivation

Young adults worldwide experience high rates of depression and
anxiety, but most do not take up mental health services even when
they're available. Both supply-side constraints (insufficient mental
health professionals) and demand-side underuse are documented. The
demand-side underuse is poorly understood: even when free,
evidence-based therapy is available, take-up is very low.

Two distinct mechanisms are plausible for low demand:
1. Financial / opportunity cost barriers.
2. Information frictions about one's own mental health status — many
   people don't recognize they have a treatable condition.

A policy concern with using financial incentives for mental health
care specifically is targeting: incentives might increase aggregate
uptake while attracting individuals with lower clinical need (who
can be swayed by money), thereby misallocating scarce therapist time.

## Research questions

1. Do small financial incentives increase therapy uptake among
   college students who have access to free mental health services?
2. Does providing personalized, screening-based feedback about one's
   own mental health status increase uptake, and does it improve
   targeting (biasing uptake toward those with higher symptom
   severity)?
3. How do these two interventions interact? Substitute or complement?

## Partner organizations and constraints

- **Implementation partner: SCARF** (Schizophrenia Research
  Foundation), a mental health NGO in Chennai. Will provide free
  therapy sessions to any student in the study who requests one.
  Capacity to handle roughly 100-150 therapy intakes over the study
  window.
- **Recruitment partner: an arts-and-science women's college in
  Chennai.** Recruitment classroom-by-classroom during college
  hours.
- **Recruitment mechanism.** All students present in an allocated
  classroom hear an introduction. Interested students consent and
  complete a baseline survey via Qualtrics on their phones.
  Eligibility: 18-30 years old.
- **Sample size constraint.** Realistic recruitment over the study
  window is expected to be 300-500 consenting participants.
- **Survey instrument.** A standardized screening tool for
  depression and anxiety. The PHQ-ADS (PHQ-9 + GAD-7 composite) is a
  candidate; the team is open to alternatives.

## Funding and approvals

- IRB approval being secured.
- Pre-registration will be filed at the AEA RCT Registry and
  ClinicalTrials.gov before data collection begins.
- MIT-internal research funds.

## What's deliberately not specified

- Number of treatment arms or what each arm receives.
- Whether to randomize at classroom or individual level.
- The specific primary outcome measure and timing.
- The financial incentive amount.
- Stratification structure.
- Power calculation parameters.
- Statistical specification, SE structure, or multiple-testing
  corrections.
- The structure of the targeting / heterogeneity analysis.

These are design decisions I want the framework to help me think
through in the discussion and planning phases, not assume in the
bootstrap.

## What I want from this session

Bootstrap the project per /gsd-new-paper. Populate the planning
documents with the substantive context only. Surface any gaps in
the brief that you'd need filled before proceeding to the design
discussion.
```

After pasting, review the generated planning documents. Note:
- Did it correctly populate context without sneaking in design
  decisions?
- Did it flag gaps it would need filled to proceed?
- Did it confabulate any specifics the brief didn't include?

The third question is the most diagnostic. Confabulation here means
the framework's metacognition rules aren't actually changing
behavior in real sessions.

## A.4-A.7: Continue the planning chain

Run in sequence, in the same session:

```
/gsd-discuss-identification --meta-cog
/gsd-plan-empirics 1 --meta-cog
/gsd-pre-register
```

After each command, compare the framework's output against your
reference predictions in `~/eval/breza-grading/reference-design.md`.
Note for each design dimension:
- **Match** — framework proposed what the paper does
- **Different but defensible** — framework's proposal is reasonable
  but the paper went another way
- **Worse** — framework's proposal is clearly less defensible than
  the paper's choice
- **Better** — framework's proposal is clearly stronger than the
  paper's choice (rare but real; note when it happens)
- **Confabulated** — framework asserted something without basis
- **Missed** — framework didn't address something a competent
  researcher would have

The Match / Different / Confabulated / Missed counts go in the final
grading document.

---

# EVALUATION B: Audit mode

Test post-hoc audit value on the finished paper. **Different day from
A. Fresh chat session.**

## B.1: Set up

```bash
mkdir -p ~/eval/breza-audit/paper
cd ~/eval/breza-audit
git init
# Download the paper PDF to paper/
~/src/gsd-econ/install.sh --project --runtime opencode \
    --models-config ~/src/gsd-econ/config/model-configs/openrouter-hybrid.yaml
```

## B.2: Write your reference critique list FIRST (60 min)

Same idea as A.2. Before running the framework, read the paper
critically and list every concern, polish issue, or referee question
you'd raise. Save to
`~/eval/breza-grading/reference-critique.md`.

Categories to think through:
- Identification threats specific to this design
- Pre-registration vs final-paper deviations
- Multiple-testing concerns given the factorial design
- Spillover concerns from classroom-level recruitment
- Generalizability claims you'd push back on
- Specific polish issues (table footnotes, cross-refs, citations)

## B.3-B.7: Run the audit commands

```
/gsd-new-paper --adopt            # bootstrap framework from existing paper
/gsd-discuss-identification --meta-cog
/gsd-polish-pass --meta-cog --offload-policy assisted
/gsd-referee-sim --heavy --n-referees 6 --meta-cog
```

After each, grade the output against your reference critique:
- **Caught** — framework surfaced something you also surfaced
- **Novel-true** — framework surfaced something you didn't, and it's
  a real concern (highest-value outcome)
- **Novel-false** — framework surfaced something that isn't a real
  concern (noise)
- **Missed** — you flagged it, framework didn't

The Caught + Novel-true / total ratio is the framework's recall;
Caught + Novel-true / (Caught + Novel-true + Novel-false) is its
precision.

## B.8: Note the polish-pass outcomes

Polish-pass produces specific edits. Track:
- How many edits were applied automatically (under the offload-policy)
- How many needed your triage
- How many were clearly wrong and rejected

These numbers are useful for the framework writeup.

---

# EVALUATION C: Multiverse mode (v0.3)

Test the specification-curve / automated-robustness machinery.

**Prerequisite:** access to analysis code that produces the headline
coefficient given parameter choices. If Breza et al.'s replication
archive isn't out yet, run C on one of your own papers with code you
have. Same mechanism, different specific decisions.

## C.1: Set up the multiverse project

If you've done Evaluation B and the paper PDF is already in
`~/eval/breza-audit/paper/`, you can reuse that project. Otherwise:

```bash
mkdir -p ~/eval/breza-multiverse
cd ~/eval/breza-multiverse
git init
~/src/gsd-econ/install.sh --project --runtime opencode \
    --models-config ~/src/gsd-econ/config/model-configs/openrouter-hybrid.yaml
# Drop:
#   paper/breza-2026-w34819.pdf           (the published paper)
#   paper/PAP-NCT06887569.pdf             (the pre-registration)
#   code/                                 (analysis code from rep archive)
#   data/                                 (analysis data — if available)
```

## C.2: Generate `decisions.jsonl` (60-90 min)

Open a chat in the project directory. Paste:

```text
Read paper/breza-2026-w34819.pdf, paper/PAP-NCT06887569.pdf, and the
analysis code in code/. Following the schema and guidance in
rules/decision-logging.md, populate decisions.jsonl at the project
root with every contested data-cleaning or methodology decision you
identify.

For each decision:
- Mark pap_committed: true if the PAP fixes it; otherwise false.
- Enumerate 1-3 defensible alternatives a competent referee might
  suggest.
- Provide a 1-3 sentence justification.

The bar for what to log is: "would a referee write a comment asking
about this choice?" If yes, log. If no (forced by data integrity,
type conversions, documented missing codes), don't log.

Pay particular attention to:
- Outcome window definition and timing
- Stratum FE structure
- SE clustering choice
- Multiple-testing correction
- Attrition / missing-data handling
- Switcher / non-compliance handling
- Heterogeneity analysis specifications

After producing decisions.jsonl, summarize: total decisions logged,
pap_committed=true vs false count, expected multiverse cell count
(product of |alternatives|+1 across all pap_committed=false rows).
```

When the agent finishes, **manually review `decisions.jsonl`**.
Compare against what you'd log yourself. The most likely v0.3 failure
mode is undercounting — agent recognizes 5 contested decisions when
there are really 15. Add anything missed by hand.

**Track for the writeup:**
- Number of decisions the agent logged unprompted
- Number you added by hand
- Categories of decisions it missed (cleaning? methodology? heterogeneity?)

## C.3: Write the evaluator (30-60 min)

The runner needs a Python function `evaluate(spec: dict) -> dict`
that returns the coefficient and SE for a parameter combination.

For Python analysis code, the evaluator looks like:

```python
# code/multiverse_evaluator.py
import pandas as pd
import statsmodels.formula.api as smf

def evaluate(spec: dict) -> dict:
    df = pd.read_stata("data/clean/analysis.dta")

    # Apply cleaning decisions
    if spec.get("d004") == "drop_switchers":
        df = df[df.switched_college == 0]
    elif spec.get("d004") == "include_post_switch_arm":
        df.loc[df.switched_college == 1, "arm"] = (
            df.loc[df.switched_college == 1, "post_switch_arm"]
        )

    # Apply outcome-window decision
    if spec.get("d001") == "8_weeks_exclusive":
        df["attended"] = (df.days_to_appt < 56) & (df.days_to_appt > 0)
    elif spec.get("d001") == "6_weeks_inclusive":
        df["attended"] = df.days_to_appt <= 42

    # Build the regression formula
    formula = "attended ~ incentive + screening + incentive_x_screening"
    if spec.get("stratum_fe") == "severity_bin_x_year":
        formula += " + C(severity_bin):C(year)"
    elif spec.get("stratum_fe") == "severity_bin_only":
        formula += " + C(severity_bin)"

    # Apply SE choice
    if spec.get("se_clustering") == "robust_individual":
        result = smf.ols(formula, data=df).fit(cov_type="HC1")
    elif spec.get("se_clustering") == "cluster_clinic_slot":
        result = smf.ols(formula, data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df.clinic_slot}
        )

    return {
        "coefficient": result.params["incentive"],
        "se": result.bse["incentive"],
        "p_value": result.pvalues["incentive"],
        "n_obs": int(result.nobs),
    }
```

For Stata code, subprocess out:

```python
import subprocess, re

def evaluate(spec: dict) -> dict:
    args = " ".join(f"{k}={v}" for k, v in spec.items())
    result = subprocess.run(
        ["stata", "-b", "do", "code/run_one_spec.do", args],
        capture_output=True, text=True,
    )
    coef = float(re.search(r"COEF=(\S+)", result.stdout).group(1))
    se = float(re.search(r"SE=(\S+)", result.stdout).group(1))
    return {"coefficient": coef, "se": se}
```

The evaluator is the most project-specific piece. Plan for 30-60
minutes to write and verify.

**Sanity check before running the full multiverse:** call the
evaluator with the all-defaults spec and confirm the coefficient
matches the paper's headline number. If it doesn't, the evaluator
has a bug and the multiverse will be meaningless.

## C.4: Dry-run, then real run

```bash
cd ~/eval/breza-multiverse

# See the proposed grid
uv run --group dev python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --grid ~/src/gsd-econ/config/multiverse-grids/rct.yaml \
    --evaluator code/multiverse_evaluator.py \
    --dry-run
```

This prints the grid: how many axes, how many cells, what each axis
varies. Decide on sampling mode:
- < 100 cells → `--mode full`
- 100-1000 → `--mode full` overnight, or `--mode main_effects` for
  fast check
- \> 1000 → `--mode main_effects` for the diagnostic, then
  `--mode sample --max-cells 1000` if you want broader coverage

Real run:

```bash
uv run --group dev python3 ~/src/gsd-econ/scripts/multiverse_runner.py \
    --decisions decisions.jsonl \
    --grid ~/src/gsd-econ/config/multiverse-grids/rct.yaml \
    --evaluator code/multiverse_evaluator.py \
    --output multiverse_results.csv \
    --mode main_effects \
    --summarize
```

Or call it via the framework command:

```
/gsd-multiverse --grid rct --mode main_effects --summarize
```

Either way produces `multiverse_results.csv`. Verify it looks
reasonable (columns match the logged axes, coefficients are in a
plausible range).

## C.5: Generate the reports

Spawn the `multiverse-reporter` agent:

```
Use the multiverse-reporter agent to produce the PDF specification
curve and the interactive HTML report from multiverse_results.csv.
```

Three outputs land:
- `output/figures/multiverse_curve.pdf` — publication-quality curve
- `output/multiverse_report.html` — self-contained interactive report
  (open in any browser, no server)
- `output/tables/multiverse_audit.tex` — booktabs audit table

Open the HTML report. The summary card at the top is the headline
diagnostic. The three patterns to watch for:

- **Stable**: coefficient varies modestly across cells (e.g., 0.080
  to 0.110 around 0.094). Good news; report curve in supplementary
  material.
- **Fragile to a single axis**: one axis drives most variation
  (e.g., switcher handling spans 0.07 to 0.13). The paper should
  call out that specific choice prominently and present the result
  both ways.
- **Diffusely fragile**: coefficient varies widely with no clear
  single-axis driver. The paper should report the range
  acknowledging the headline is one defensible cell within a wide
  distribution.

The "most-influential single axis" diagnostic is the most useful in
practice. If it surfaces a cleaning decision the agent only logged
because *you* added it in C.2, that's evidence the agent
undercounted — log this for the v0.3.1 retrospective.

## C.6: Grade

In `~/eval/breza-grading/evaluation-C.md`:

- **Agent recall on decisions.** Of the decisions you'd log yourself,
  how many did the agent log automatically? How many did you add
  by hand? What kinds did it miss?
- **Multiverse output usability.** Are the PDF and HTML reports
  usable as-is? What would you change?
- **Findings.** What did the multiverse reveal about the paper that
  a standard robustness section would have missed (if anything)?
- **Time spent.** Total hours across C.1-C.5.

Save the `multiverse_report.html` and `multiverse_results.csv` as
artifacts. If the evaluation is positive, both are excellent material
for a LinkedIn writeup or methods paper.

---

## Final synthesis

After all three evaluations, write the consolidated report in
`~/eval/breza-grading/EVALUATION.md`:

- **A:** does the framework help *build* a paper?
- **B:** does the framework help *audit* a paper?
- **C:** does the framework help *robustness-test* a paper?
- Distinguish **coverage value** (caught things you would have caught
  anyway, faster) from **discovery value** (caught things you'd have
  missed entirely).
- Specific successes and failures per mode.
- Bugs and design issues to file as GitHub issues.
- Verdict per mode: (a) clear value, would use again; (b) some value
  but needs iteration; (c) little value for the cost.

This is the deliverable. Once it's in hand:

1. File any blocking bugs as GitHub issues against the public repo.
2. Decide whether to publish v1.0 (clear value across at least two
  modes), iterate on v0.3.1 (some value with specific fixable
  issues), or shelve.
3. Write the LinkedIn / blog post if value was demonstrated.

---

## On the LinkedIn writeup after C

Evaluation C produces visible artifacts: a specification-curve PDF,
an interactive HTML report, a `decisions.jsonl` documenting every
contested choice. These are concrete and shareable.

The post format that would work:

> Built and tested gsd-econ v0.3 on Breza et al. (2026). The
> framework's specification-curve multiverse runs every defensible
> combination of cleaning + methodology choices automatically — N
> cells total, ~M minutes of compute. Found that the headline
> coefficient [survives / is fragile to switcher_handling / etc].
> Three thoughts on what works and what doesn't. Link to the
> interactive HTML report so you can browse the multiverse yourself.

If the evaluation is positive, that post has real signal. If
negative, an honest "here's what I built, here's what worked, here's
what didn't" post is also worth writing — the
empirical-economics-AI-agent space has plenty of "look what I built"
content and not enough honest assessment.

---

## What to do if things go off the rails

Most likely failure modes per evaluation:

**A:**
- Framework confabulates design choices despite the brief saying not
  to. Significant v0 finding; log as a metacognition failure.
- Greenfield bootstrap takes a wrong turn early and the rest of the
  session compounds. Stop, fix planning docs by hand, retry.

**B:**
- `--adopt` generates nonsense. Edit `.planning/` files by hand and
  retry.
- Polish-pass outputs look like nonsense from the PDF. Try
  `pdftotext` first and point the agent at the `.txt` file.

**C:**
- **Most likely:** decision-logging agent undercounts. Augment by
  hand. Track the gap.
- Evaluator returns wrong coefficient for the headline spec. Debug
  before running the full multiverse — if the headline doesn't
  match, the whole sweep is meaningless.
- Multiverse runs but coefficient is unchanging — likely a bug where
  the evaluator isn't using the spec values. Sanity-check by running
  two cells with very different parameter values and verifying the
  coefficients differ.

If a command fails in a way the framework should handle better,
that's a real finding — write it up as a GitHub issue.
