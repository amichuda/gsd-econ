"""
Layer 2 — Internal cross-references.

Verifies that commands reference agents that exist, agents reference tests
that exist, configs reference valid paths, etc. Catches typos and broken refs.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from conftest import Document


# -----------------------------------------------------------------------------
# Agent references in commands
# -----------------------------------------------------------------------------

AGENT_REF_RE = re.compile(
    r"`([\w-]+)`\s+agent|spawn(?:ing|s)?\s+(?:the\s+)?`?([\w-]+)`?\s+agent",
    re.IGNORECASE,
)


def _extract_agent_refs(text: str) -> set[str]:
    """Extract agent names referenced in command bodies."""
    refs: set[str] = set()
    for m in AGENT_REF_RE.finditer(text):
        ref = m.group(1) or m.group(2)
        if ref:
            refs.add(ref.strip("`"))
    return refs


KNOWN_NON_AGENTS = {
    # Phrases that match the regex but aren't agent references
    "the", "the-orchestrator", "orchestrator", "executor", "the-planner",
    "planner", "the-verifier", "verifier", "this", "that", "an", "a",
    "user", "the-user", "the-executor",
    # GSD core agents we use but don't ship
    "researcher", "plan-checker", "plan_check",
}


def test_commands_reference_real_agents(
    commands: list[Document], agents: list[Document]
) -> None:
    agent_names = {doc.name for doc in agents}
    for cmd in commands:
        refs = _extract_agent_refs(cmd.body)
        for ref in refs:
            ref_lower = ref.lower()
            if ref_lower in KNOWN_NON_AGENTS:
                continue
            if "-" not in ref and "_" not in ref:
                # Probably a generic phrase, not an agent name
                continue
            # If a referenced "agent" looks like an agent name (multi-word slug)
            # but isn't in our agents/, fail
            if ref not in agent_names and ref_lower not in KNOWN_NON_AGENTS:
                pytest.fail(
                    f"Command {cmd.name} references agent {ref!r} which "
                    f"does not exist in agents/. Known agents: {sorted(agent_names)}"
                )


# -----------------------------------------------------------------------------
# Test ID references in commands
# -----------------------------------------------------------------------------

# Look for test IDs like `did-parallel-trends-plot` or `universal-tables-have-n-obs`
# in command bodies. These should match a real registry entry (either upstream
# RUT or this repo's registry).
TEST_ID_RE = re.compile(r"`([a-z_]+(?:-[a-z_]+)+)`")

# Upstream RUT tests (from the upstream registry as of 2025). We don't ship
# these but we reference them. Keep this list in sync with upstream when it
# changes — this test catches drift.
UPSTREAM_RUT_TEST_IDS = {
    "universal-tables-have-n-obs",
    "universal-replication-reproduces-results",
    "universal-contribution-is-new",
    "universal-contribution-is-interesting",
    "did-parallel-trends-plot",
    "did-staggered-heterogeneous-effects",
    "iv-first-stage-f-stat",
    "rdd-bandwidth-sensitivity",
    "rdd-manipulation-test",
    "experiment_field-balance-table",
}


def test_command_test_ids_resolve(
    commands: list[Document], registry_ids: set[str]
) -> None:
    """Test IDs referenced in commands should match either our registry or upstream RUT."""
    all_known_ids = registry_ids | UPSTREAM_RUT_TEST_IDS
    for cmd in commands:
        for m in TEST_ID_RE.finditer(cmd.body):
            candidate = m.group(1)
            # Only treat as test ID if it has a methodology-tag prefix
            prefix = candidate.split("-")[0]
            valid_prefixes = {
                "universal", "did", "rdd", "iv", "ols", "synth",
                "experiment_lab", "experiment_field", "theory",
                "ml_prediction", "survey",
            }
            if prefix not in valid_prefixes:
                continue
            assert candidate in all_known_ids, (
                f"Command {cmd.name} references test {candidate!r} which is not "
                f"in this repo's registry nor in upstream RUT. "
                f"If it's a new test, add it to tests/registry.yaml. "
                f"If it's a typo, fix it."
            )


# -----------------------------------------------------------------------------
# File path references in docs
# -----------------------------------------------------------------------------

def test_install_md_paths_resolve(repo_root: Path) -> None:
    """Paths mentioned in INSTALL.md as part of this repo should exist."""
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8")
    # Look for `vendor/gsd-econ/<path>` references — these are paths within
    # this repo (just prefixed with vendor/ for the install instructions).
    pattern = re.compile(r"`vendor/gsd-econ/([\w./-]+)`")
    for m in pattern.finditer(install):
        relpath = m.group(1)
        full = repo_root / relpath
        assert full.exists(), (
            f"INSTALL.md references vendor/gsd-econ/{relpath} which does not exist. "
            "Either add the file or update the docs."
        )


def test_readme_file_tree_files_exist(repo_root: Path) -> None:
    """
    The README contains a file tree. Every file (not directory) shown there
    should exist. We extract paths heuristically.
    """
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    # Match lines in the file tree that look like file paths (have an extension
    # or are LICENSE/README without extension)
    in_tree = False
    referenced_files: set[str] = set()
    for line in readme.splitlines():
        if "```" in line:
            in_tree = not in_tree
            continue
        if not in_tree:
            continue
        # crude: lines that contain a filename with an extension
        # Match longer extensions first (e.g., .json.example, .md.template)
        m = re.search(
            r"([\w.-]+\.(md\.template|json\.example|md|sh|jsonl|json|yaml|yml|tex|csv))",
            line,
        )
        if m:
            referenced_files.add(m.group(1))

    # Some references are upstream files we don't ship, or files generated
    # at project-runtime inside user projects (not in the framework repo).
    upstream_only = {
        "README.md",  # ambiguous; we have one but tree references upstream too
        "decisions.jsonl",  # generated per-project by execute-phase agents
        "multiverse_results.csv",  # generated per-project by /gsd-multiverse
    }
    referenced_files -= upstream_only

    # We don't enforce that every referenced file exists at exactly the path
    # in the tree (the tree is illustrative) — instead, check that the file
    # *name* exists somewhere in the repo.
    repo_files = {p.name for p in repo_root.rglob("*") if p.is_file()}
    for fname in referenced_files:
        assert fname in repo_files, (
            f"README file tree references {fname!r} but no such file exists "
            f"anywhere in the repo. Update the tree or add the file."
        )
