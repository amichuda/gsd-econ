# gsd-econ tests

This directory contains RUT-format tests authored as part of gsd-econ. They complement (not replace) upstream `research-unit-tests`.

## Layout

```
tests/
├── registry.yaml          # this repo's test index
├── core/                  # tests we'd plausibly PR upstream
│   └── *.md
└── community/             # private/personal/work-in-progress tests
    └── <username>/*.md
```

## Why two registries?

The verifier merges this registry with `vendor/research-unit-tests/registry.yaml` at runtime. Tests in `core/` are domain-specific to empirical economics in ways the upstream registry doesn't yet cover (Conley SEs, attrition balance, PAP-deviation disclosure). Tests in `community/<username>/` are private; they're not auto-loaded unless the user opts in.

## Format

See [`docs/writing-tests.md`](../docs/writing-tests.md) for the full format spec. Short version:

```markdown
# <name>

**Methodology:** <tag>
**Scope:** <paper | proposal | replication>
**Severity:** <blocker | warning | info>
**Clarity:** <deterministic | heuristic | judgment>

## Criterion
<what passing means>

## How to check
<operational instructions>

## Pass condition
<the contract>

## Fail handling
<optional: what fix plan should contain>

## References
<optional citations>
```

Then register in `registry.yaml`.

## Contribution path

If a test in `core/` proves valuable across multiple papers, PR it to upstream RUT. The path is:

1. Author in `community/<your-username>/`
2. Use it on a few projects
3. If broadly useful, promote to `core/` here
4. After more usage, PR to https://github.com/rdahis/research-unit-tests

## Tests in this repo

Run-by-default core tests:

| ID | Methodology | Severity | Clarity |
|----|-------------|----------|---------|
| `iv-exclusion-narrative-explicit` | iv | blocker | heuristic |
| `iv-weak-instrument-robust-inference` | iv | blocker | deterministic |
| `did-conley-ses-when-spatial` | did | warning | heuristic |
| `experiment_field-attrition-balance` | experiment_field | blocker | deterministic |
| `experiment_field-pap-deviation-disclosed` | experiment_field | blocker | deterministic |
| `universal-clustered-ses-justified` | universal | warning | deterministic |
| `universal-multiple-testing-corrected` | universal | warning | heuristic |
| `universal-sample-restrictions-stated` | universal | blocker | deterministic |

These 8 fill gaps in the upstream registry as of writing (rdahis's RUT had 8 core tests on first commit; this repo adds 8 more focused on identification narrative, inference under correlation, and pre-registration discipline).
