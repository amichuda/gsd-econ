"""
Shared fixtures and helpers for the gsd-econ verification suite.

These tests verify the gsd-econ repo itself: structural integrity,
internal consistency, documentation accuracy, and the install script.
They do NOT verify LLM behavior — that's covered by the manual checklist
in verification/manual-checklist.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml


# -----------------------------------------------------------------------------
# Repo location
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The gsd-econ repo root (parent of verification/)."""
    return Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# Canonical taxonomies
# -----------------------------------------------------------------------------

VALID_METHODOLOGIES = {
    "universal",
    "did",
    "rdd",
    "iv",
    "ols",
    "synth",
    "experiment_lab",
    "experiment_field",
    "theory",
    "ml_prediction",
    "survey",
}

VALID_SCOPES = {"paper", "proposal", "replication"}
VALID_SEVERITIES = {"blocker", "warning", "info"}
VALID_CLARITIES = {"deterministic", "heuristic", "judgment"}
VALID_MODEL_TIERS = {"light", "standard", "heavy"}


# -----------------------------------------------------------------------------
# Frontmatter parsing
# -----------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Document:
    path: Path
    frontmatter: dict[str, Any]
    body: str

    @property
    def name(self) -> str:
        return self.path.stem


def parse_markdown(path: Path) -> Document:
    """Parse a markdown file with YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if m:
        frontmatter = yaml.safe_load(m.group(1)) or {}
        body = text[m.end():]
    else:
        frontmatter = {}
        body = text
    return Document(path=path, frontmatter=frontmatter, body=body)


# -----------------------------------------------------------------------------
# Registry loading
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def registry(repo_root: Path) -> list[dict[str, Any]]:
    """Parsed tests/registry.yaml."""
    path = repo_root / "tests" / "registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["tests"]


@pytest.fixture(scope="session")
def registry_ids(registry: list[dict[str, Any]]) -> set[str]:
    return {t["id"] for t in registry}


# -----------------------------------------------------------------------------
# Globs for the various artifact types
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def commands(repo_root: Path) -> list[Document]:
    return [parse_markdown(p) for p in sorted((repo_root / "commands").glob("*.md"))]


@pytest.fixture(scope="session")
def agents(repo_root: Path) -> list[Document]:
    return [parse_markdown(p) for p in sorted((repo_root / "agents").glob("*.md"))]


@pytest.fixture(scope="session")
def core_tests(repo_root: Path) -> list[Document]:
    return [parse_markdown(p) for p in sorted((repo_root / "tests" / "core").glob("*.md"))]


@pytest.fixture(scope="session")
def templates(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "templates").glob("*.md.template"))


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def parse_metadata_block(body: str) -> dict[str, str]:
    """
    RUT tests use bolded metadata lines instead of YAML frontmatter, like:
        **Methodology:** did
        **Scope:** paper
    Returns lowercased keys → values.
    """
    out: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^\*\*([\w ]+):\*\*\s+(.+?)\s*$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def has_section(body: str, header: str) -> bool:
    """
    Check whether a markdown body contains a given ## section header.
    Matches both exact ('## Process') and prefix ('## Process — new mode') forms,
    so commands that split sections by mode/variant still satisfy the contract.
    """
    pattern = rf"^##\s+{re.escape(header)}\b"
    return bool(re.search(pattern, body, flags=re.MULTILINE))
