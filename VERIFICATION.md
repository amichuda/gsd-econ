# Verification

This document explains how `gsd-econ` is itself verified. The repo eats its own dog food: just as the framework gates papers on declarative tests, the framework's repo is gated on a structured test suite of its own.

## The five layers

Verification is layered by automation cost:

| Layer | What | How | Where |
|---|---|---|---|
| **1. Structural** | Files in right places, YAML/JSON parses, frontmatter valid | pytest, fast | `verification/test_repo_structure.py`, `test_config.py` |
| **2. Internal consistency** | Registry matches files, commands reference real agents, every test ID resolves | pytest, fast | `verification/test_registry.py`, `test_test_format.py`, `test_commands_agents.py`, `test_internal_refs.py` |
| **3. Documentation accuracy** | README and INSTALL claims match reality | pytest, fast | `verification/test_docs_accuracy.py` |
| **4. Functional** | `install.sh` runs, is idempotent, doesn't clobber | pytest with bash | `verification/test_install_script.py`, `test_shell_scripts.py` |
| **5. Behavioral** | LLM workflow produces the expected outputs on a real paper | manual | `verification/manual-checklist.md` |

Layers 1–4 run on every commit via GitHub Actions. The CI badge at the top of the README reflects their status.

Layer 5 is manual. Some things can't reasonably be auto-tested:

- Whether `/gsd-discuss-identification` actually asks the right questions for a DiD paper
- Whether `replication-verifier` correctly interprets a heuristic test
- Whether `referee-sim` produces a useful adversarial review

For these, we maintain a manual checklist that's run before each release. See [`verification/manual-checklist.md`](verification/manual-checklist.md).

## Run the suite locally

```bash
make verify
```

…or explicitly:

```bash
pip install -r verification/requirements.txt
pytest verification/ -v
```

For a quicker feedback loop during development:

```bash
make verify-fast   # skips install-script tests
```

## Interpreting failures

**Structural failure** — usually means a file got deleted or moved. Check the failing test name; it'll point at the missing artifact.

**Registry failure** — a test was added to `tests/core/` without registering it (or vice versa). The error message names the offending ID.

**Cross-reference failure** — a command mentions an agent name that doesn't exist in `agents/`, or a test ID that's not in any registry. Often a typo. Check the failing assertion's message for the specific reference.

**Doc accuracy failure** — README claims something specific (e.g., "8 tests") and the count no longer matches. Either update the README or add/remove the artifact.

**Install-script failure** — the script changed and broke the contract (creates symlinks, copies templates, idempotent, doesn't clobber existing planning docs). The test will tell you which contract is violated.

## What is not auto-tested

These are explicitly out of scope for the auto-suite — calling them out so you can decide if you trust the framework on them:

1. **LLM behavior.** No automated test verifies that the prompts inside `commands/` and `agents/` produce sensible outputs. This is by design — testing LLM behavior is non-deterministic, expensive, and fragile across model versions. The manual checklist covers this.

2. **Real paper end-to-end.** No CI run actually opens an OpenCode/Claude Code session, runs `/gsd-new-paper` on a fresh project, and checks that all 9 phases complete cleanly. This requires a real runtime, real API keys, and human judgment at each phase.

3. **Cross-runtime behavior.** Tests assume the install pattern works for both OpenCode and Claude Code, but only OpenCode is exercised in the install-script tests. Claude Code-specific paths are exercised manually.

4. **Compatibility across upstream versions.** The wired `agent_skills` paths assume a specific RUT directory layout. If RUT restructures, the integration breaks but tests still pass. Track upstream RUT releases manually.

5. **The actual research methodology in the test bodies.** The verification suite checks that test files have the right *format*. It does not verify that, say, the threshold for "first-stage F" in `iv-weak-instrument-robust-inference.md` cites the most current methodological paper. That's the test author's responsibility, surfaced through the contribution PR review.

## Manual checklist for releases

Before tagging a release (especially v1.0+), run through `verification/manual-checklist.md`. The checklist covers the things CI can't:

- One full session of `/gsd-new-paper` through `/gsd-submit-paper` on a toy project
- Each command produces the documented artifacts
- Each agent's output makes sense for typical inputs
- Replication smoke test on the example paper

The checklist takes 1–2 hours to run once. It's the difference between "tests pass" and "I'd put my own name on this for a real paper."

## CI

GitHub Actions runs the suite on every push and PR. The workflow is at [`.github/workflows/ci.yml`](.github/workflows/ci.yml). It:

1. Sets up Python and bash
2. Installs `pytest`, `pyyaml`, `shellcheck`
3. Runs `pytest verification/ -v`
4. Reports pass/fail to the PR

The badge in the README reflects the status of the most recent run on `main`.

## Adding new verification tests

The suite is itself a test artifact. As `gsd-econ` grows, the suite should too:

- New command? Add a check that it has frontmatter, Process, Constraints, and Output sections (already covered generically in `test_commands_agents.py`).
- New agent? Same.
- New test in `tests/core/`? The format check fires automatically.
- New invariant you want to enforce (e.g., "every blocker test must have a Fail handling section")? Add it to `verification/test_test_format.py`.

The principle: any claim made in the docs or any contract embedded in the structure should have at least one failing assertion if violated. If you find yourself saying "well, technically X must be true," write a test for X.
