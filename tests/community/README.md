# Community tests

This is the place for **personal**, **work-in-progress**, or **lab-specific** tests that you don't want auto-loaded into the registry but want available on demand.

## Structure

```
community/
├── README.md          # this file
├── <username>/        # one subdirectory per author
│   ├── *.md           # tests
│   └── README.md      # description of the collection
```

## How to use community tests

By default, the verifier loads tests from:
- `vendor/research-unit-tests/registry.yaml` (upstream)
- `vendor/gsd-econ/tests/registry.yaml` (this repo's `core/`)

To include community tests, either:

**Option A: opt-in via METHODOLOGY.md**

Add to `METHODOLOGY.md`:

```yaml
test_inclusions:
  - <username>/<test-id>
```

The verifier will load that specific test even if it's not in any registry.

**Option B: register the whole collection**

Create a `community/<username>/registry.yaml` and reference it from the install script's `agent_skills` wiring. This loads the whole collection alongside the core registries.

## Promotion path

A test you write here can move:

1. **Stay private** — works for you, not generally useful.
2. **Promote to `gsd-econ/tests/core/`** — useful across multiple projects, broader econ relevance. Open a PR to this repo.
3. **Promote to upstream RUT** — broadly applicable, well-anchored. Open a PR to https://github.com/rdahis/research-unit-tests.

## Why a community area?

Tests can be opinionated. Universal tests (in `core/`) should reflect broad consensus; warning tests can be more opinionated. Community tests can be as opinionated as you like — they're scoped to your projects unless you opt them into the registry.

For example, you might have a test enforcing your lab's house style: "robustness section uses Romano-Wolf, not Bonferroni." That's a reasonable lab standard but too prescriptive for `core/`. It belongs here.
