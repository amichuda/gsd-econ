"""
Layer 2 — openalex-search skill structure and Python helpers.

The skill is a `skills/openalex-search/` directory with a SKILL.md describing
the patterns and a Python helper module. Tests enforce:

- The skill files exist
- SKILL.md is well-structured (frontmatter, sections)
- The Python module is importable in principle (syntactic check; we don't
  actually import pyalex during tests because that would require pyalex
  installed AND an API key for any non-trivial call)
- Documentation is honest about limits and the API key requirement
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


SKILL_DIR = "skills/openalex-search"


def test_skill_dir_exists(repo_root: Path) -> None:
    path = repo_root / SKILL_DIR
    assert path.is_dir(), f"{SKILL_DIR}/ must exist"


def test_skill_md_exists(repo_root: Path) -> None:
    path = repo_root / SKILL_DIR / "SKILL.md"
    assert path.is_file(), f"{SKILL_DIR}/SKILL.md must exist"


def test_skill_md_has_frontmatter(repo_root: Path) -> None:
    """SKILL.md must have YAML frontmatter with name, description, license."""
    text = (repo_root / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end > 0, "SKILL.md frontmatter must close with `---`"
    frontmatter = text[4:end]
    assert "name:" in frontmatter, "frontmatter must declare `name:`"
    assert "description:" in frontmatter, "frontmatter must declare `description:`"
    assert "license:" in frontmatter, "frontmatter must declare `license:`"


def test_skill_md_mentions_pyalex(repo_root: Path) -> None:
    """The skill is built on pyalex, so SKILL.md must say so explicitly."""
    text = (repo_root / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "pyalex" in text, "SKILL.md must mention pyalex (the library it wraps)"


def test_skill_md_discloses_api_key_requirement(repo_root: Path) -> None:
    """Users must know the API key requirement before they hit a quota error."""
    text = (repo_root / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "API key" in text or "api_key" in text, (
        "SKILL.md must disclose the OpenAlex API key requirement"
    )
    assert "February" in text or "2026" in text, (
        "SKILL.md should note when the API key requirement took effect"
    )


def test_skill_md_documents_limits(repo_root: Path) -> None:
    """The skill must be honest about what it doesn't do."""
    text = (repo_root / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").lower()
    indicators = ["limit", "does not", "doesn't", "not"]
    found = sum(1 for w in indicators if w in text)
    assert found >= 3, "SKILL.md should be honest about limitations"


def test_python_module_exists(repo_root: Path) -> None:
    path = repo_root / SKILL_DIR / "openalex_search.py"
    assert path.is_file(), f"{SKILL_DIR}/openalex_search.py must exist"


def test_python_module_parses(repo_root: Path) -> None:
    """The helper module must be syntactically valid Python."""
    path = repo_root / SKILL_DIR / "openalex_search.py"
    source = path.read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"openalex_search.py has a syntax error: {e}")


def test_python_module_exposes_core_functions(repo_root: Path) -> None:
    """The module must define the helper functions the SKILL.md documents."""
    path = repo_root / SKILL_DIR / "openalex_search.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    defined_funcs = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    expected = {
        "get_nber_source_id",
        "find_recent_nber",
        "find_evaluation_candidates",
        "save_results",
    }
    missing = expected - defined_funcs
    assert not missing, f"Missing helper functions: {missing}"


def test_python_module_saves_to_audit_trail(repo_root: Path) -> None:
    """save_results should write to .planning/research/ (audit-trail discipline)."""
    source = (repo_root / SKILL_DIR / "openalex_search.py").read_text(encoding="utf-8")
    assert ".planning/research" in source, (
        "save_results should default to writing into .planning/research/ "
        "for the audit trail"
    )


def test_skill_uses_env_vars_for_credentials(repo_root: Path) -> None:
    """API key and email should be read from environment, never hard-coded."""
    source = (repo_root / SKILL_DIR / "openalex_search.py").read_text(encoding="utf-8")
    assert "OPENALEX_API_KEY" in source, (
        "module should read API key from OPENALEX_API_KEY environment variable"
    )
    assert "os.environ" in source, "module should use os.environ for credentials"


def test_requirements_file_exists(repo_root: Path) -> None:
    path = repo_root / SKILL_DIR / "requirements.txt"
    assert path.is_file(), f"{SKILL_DIR}/requirements.txt must exist"
    text = path.read_text(encoding="utf-8")
    assert "pyalex" in text, "requirements.txt must list pyalex"


def test_skill_md_includes_full_example(repo_root: Path) -> None:
    """SKILL.md must have a complete worked example, not just snippets."""
    text = (repo_root / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    # Heuristic: at least one Python code block longer than 20 lines
    in_code = False
    longest = 0
    current = 0
    for line in text.splitlines():
        if line.startswith("```python"):
            in_code = True
            current = 0
        elif line.startswith("```") and in_code:
            longest = max(longest, current)
            in_code = False
        elif in_code:
            current += 1
    assert longest >= 20, (
        f"SKILL.md should include at least one substantial Python example "
        f"(longest block was {longest} lines)"
    )
