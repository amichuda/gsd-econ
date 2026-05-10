# Verification suite

Tests that validate the gsd-econ repo itself.

## Run locally

```bash
pip install -r verification/requirements.txt
pytest verification/ -v
```

Or via Make:

```bash
make verify          # all tests
make verify-fast     # skip install-script tests (~2x faster)
```

## What's tested

| File | Layer | What it checks |
|------|-------|----------------|
| `test_repo_structure.py` | 1 | Required files and directories exist |
| `test_registry.py` | 2 | Test registry schema, ID uniqueness, paths resolve |
| `test_test_format.py` | 2 | RUT test markdown format, registry/file consistency |
| `test_commands_agents.py` | 2 | Command and agent frontmatter, required sections |
| `test_internal_refs.py` | 2 | Cross-references between commands, agents, tests |
| `test_docs_accuracy.py` | 3 | README/INSTALL claims match reality |
| `test_config.py` | 2 | config.json.example schema |
| `test_install_script.py` | 4 | install.sh runs and is idempotent |
| `test_shell_scripts.py` | 1 | Shell scripts have shebang + strict mode |
| `manual-checklist.md` | 5 | Manual LLM-behavior checklist (run before releases) |

See `../VERIFICATION.md` for the full philosophy.
