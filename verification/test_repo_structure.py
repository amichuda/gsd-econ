"""
Layer 1 — Structural integrity.

Verifies that required directories and files exist and the repo's overall
shape matches what's documented.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REQUIRED_TOP_LEVEL_FILES = [
    "README.md",
    "LICENSE",
    "INSTALL.md",
    "CONTRIBUTING.md",
    "VERIFICATION.md",
    "AGENTS.md",
    ".gitignore",
    "Makefile",
    "install.sh",
]

REQUIRED_DIRECTORIES = [
    "docs",
    "commands",
    "agents",
    "skills/econ-research",
    "tests",
    "tests/core",
    "tests/community",
    "templates",
    "config",
    "scripts",
    "examples/example-paper",
    "verification",
    ".github/workflows",
]

REQUIRED_DOCS = [
    "docs/architecture.md",
    "docs/adapting-gsd.md",
    "docs/adopting-mid-project.md",
    "docs/model-tiers.md",
    "docs/verification-flow.md",
    "docs/writing-tests.md",
]

REQUIRED_TEMPLATES = [
    "templates/PROJECT.md.template",
    "templates/REQUIREMENTS.md.template",
    "templates/METHODOLOGY.md.template",
    "templates/ROADMAP.md.template",
    "templates/STATE.md.template",
    "templates/PHASE-CONTEXT.md.template",
]

REQUIRED_CONFIGS = [
    "config/config.json.example",
    "config/settings.json.example",
]

REQUIRED_SCRIPTS = [
    "install.sh",
    "scripts/run-tests.sh",
]


@pytest.mark.parametrize("filename", REQUIRED_TOP_LEVEL_FILES)
def test_required_top_level_file_exists(repo_root: Path, filename: str) -> None:
    assert (repo_root / filename).is_file(), f"Missing top-level file: {filename}"


@pytest.mark.parametrize("dirname", REQUIRED_DIRECTORIES)
def test_required_directory_exists(repo_root: Path, dirname: str) -> None:
    assert (repo_root / dirname).is_dir(), f"Missing directory: {dirname}"


@pytest.mark.parametrize("filename", REQUIRED_DOCS)
def test_required_doc_exists(repo_root: Path, filename: str) -> None:
    assert (repo_root / filename).is_file(), f"Missing doc: {filename}"


@pytest.mark.parametrize("filename", REQUIRED_TEMPLATES)
def test_required_template_exists(repo_root: Path, filename: str) -> None:
    assert (repo_root / filename).is_file(), f"Missing template: {filename}"


@pytest.mark.parametrize("filename", REQUIRED_CONFIGS)
def test_required_config_exists(repo_root: Path, filename: str) -> None:
    assert (repo_root / filename).is_file(), f"Missing config: {filename}"


@pytest.mark.parametrize("filename", REQUIRED_SCRIPTS)
def test_required_script_exists(repo_root: Path, filename: str) -> None:
    p = repo_root / filename
    assert p.is_file(), f"Missing script: {filename}"


def test_skill_aggregator_exists(repo_root: Path) -> None:
    assert (repo_root / "skills" / "econ-research" / "SKILL.md").is_file()


def test_test_registry_exists(repo_root: Path) -> None:
    assert (repo_root / "tests" / "registry.yaml").is_file()


def test_ci_workflow_exists(repo_root: Path) -> None:
    assert (repo_root / ".github" / "workflows" / "ci.yml").is_file()


def test_at_least_one_command(repo_root: Path) -> None:
    cmds = list((repo_root / "commands").glob("*.md"))
    assert len(cmds) >= 5, f"Expected at least 5 commands, found {len(cmds)}"


def test_at_least_one_agent(repo_root: Path) -> None:
    ags = list((repo_root / "agents").glob("*.md"))
    assert len(ags) >= 3, f"Expected at least 3 agents, found {len(ags)}"


def test_at_least_one_test(repo_root: Path) -> None:
    tests = list((repo_root / "tests" / "core").glob("*.md"))
    assert len(tests) >= 3, f"Expected at least 3 core tests, found {len(tests)}"


def test_no_stray_DS_Store(repo_root: Path) -> None:
    """macOS .DS_Store files shouldn't be checked in."""
    bad = list(repo_root.rglob(".DS_Store"))
    assert not bad, f"Found .DS_Store files: {bad}"
