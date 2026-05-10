# Writing custom tests

Two registries are merged at runtime: `vendor/research-unit-tests/registry.yaml` (upstream) and `vendor/gsd-econ/tests/registry.yaml` (this repo). You can add tests to either, but a sensible workflow is:

- **`gsd-econ/tests/community/<your-username>/`** — your private or work-in-progress tests. Not registered globally.
- **`gsd-econ/tests/core/`** — tests we'd plausibly PR upstream to RUT. Registered in this repo's registry.
- **Upstream RUT** — once a test in `gsd-econ/tests/core/` proves valuable across multiple papers, PR it.

## Test file format

A test is a Markdown file. Required sections:

```markdown
# <test name as a sentence>

**Methodology:** <one of: universal, did, rdd, iv, ols, synth, experiment_lab, experiment_field, theory, ml_prediction, survey>
**Scope:** <one of: paper, proposal, replication>
**Severity:** <one of: blocker, warning, info>
**Clarity:** <one of: deterministic, heuristic, judgment>

## Criterion

<One paragraph stating exactly what passing this test means. Be precise. Avoid weasel words.>

## How to check

<Step-by-step instructions an LLM agent can follow with no domain experience. Reference specific files, functions, or patterns the agent should look for.>

## Pass condition

<Crisp, testable statement. For deterministic clarity, this should be a literal yes/no observable. For heuristic, an objective anchor plus the human-judgment escape hatch. For judgment, the criterion the referee-sim should apply.>

## Fail handling

<What the fix plan should contain when this test fails. Optional but useful for blockers.>

## References

<Optional. Citations, papers, methodological references. Include arXiv / SSRN URLs where available.>
```

## Registry entry

After writing the test markdown, register it in `tests/registry.yaml`:

```yaml
- id: experiment_field-attrition-balance
  name: Differential attrition is balanced across treatment arms
  methodology: experiment_field
  scope: paper
  severity: blocker
  clarity: deterministic
  path: tests/core/experiment_field-attrition-balance.md
```

The `id` must match the filename (minus `.md`). The verifier loads tests by registry entry and resolves the path relative to the repo root.

## Choosing severity

A practical heuristic:

- **`blocker`** — if a top-five journal would reject the paper or a competent referee would not let it pass without addressing this, it's a blocker. Be conservative; blocker fails create real friction.
- **`warning`** — would improve the paper if addressed. Most reviewers would mention it but not refuse to recommend acceptance.
- **`info`** — best practice or stylistic. The author should know but it's not a defect.

When in doubt, start at `warning`. Promote to `blocker` after a paper or two of experience.

## Choosing clarity

- **`deterministic`** — a regex or a numerical check would suffice. "Tables report N." "First-stage F > 10." "p-values reported to two decimal places."
- **`heuristic`** — there's an objective anchor but human judgment is needed at the boundary. "Pre-trend coefficients are small and not jointly significant." (Small how? Joint test threshold?)
- **`judgment`** — needs domain expertise and contextual reasoning. "Contribution is interesting." "Identification strategy is credible." These should virtually never be blockers in the verifier; they live in the referee-sim.

## Examples

See the tests in `tests/core/` — particularly:

- `iv-exclusion-narrative-explicit.md` — example of a heuristic blocker (looks for prose, judges whether it discusses exclusion explicitly).
- `universal-clustered-ses-justified.md` — example of a deterministic warning (checks the methods section mentions clustering and the chosen level matches the variation).
- `experiment_field-pap-deviation-disclosed.md` — example of a deterministic blocker (looks for a PAP-deviations section if `prereg.url` is set in `METHODOLOGY.md`).

## Anti-patterns

Avoid these:

- **Tests that check style, not substance.** "Tables use booktabs" is not a unit test. Linting belongs elsewhere.
- **Tests with vague pass conditions.** "Identification is reasonable" — too judgment-y for any clarity level except `judgment`.
- **Tests that duplicate upstream RUT.** Check `vendor/research-unit-tests/registry.yaml` before authoring. If a near-duplicate exists, contribute a refinement to that test instead.
- **Tests that require code execution.** RUT tests are declarative — the agent reads and reasons. If your test fundamentally requires running R/Stata, the *check* belongs in the executor (a make target, a unit test in your code repo); RUT just specifies the criterion.

## Testing your test

Before adding to `core/`, run a smoke check:

```bash
bash scripts/run-tests.sh --test-id <your-test-id> --paper-dir examples/example-paper
```

This invokes the verifier in standalone mode against the example paper. You should see:

- The test loaded
- Evidence collected
- A verdict

If the verdict is `NEEDS-EVIDENCE` and the example paper has the relevant artifact, your "How to check" section probably points the agent at the wrong place. Iterate.

## Contributing back

If your test belongs in upstream RUT (universally applicable, well-anchored), open a PR there. If it's economics-specific or labor/development-flavored, open a PR here. Either way, include:

1. The test markdown
2. A registry entry
3. A short walkthrough of why this test is worth being a test (what failure mode it catches that wasn't caught before)
4. Optionally, an example of a published paper that would have benefited
