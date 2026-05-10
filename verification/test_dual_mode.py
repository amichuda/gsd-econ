"""
Layer 2 — Single-entry-point contracts.

The gsd-econ design has exactly one bootstrap command (gsd-new-paper) that
handles both greenfield (--new) and brownfield (--adopt) workflows. These
tests enforce that contract: there's only one bootstrap command, and it
documents both modes substantively.
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_only_one_bootstrap_command(repo_root: Path) -> None:
    """No /gsd-adopt-paper, /gsd-init, etc. — only /gsd-new-paper."""
    cmd_dir = repo_root / "commands"
    bootstrap_like = [
        p.name for p in cmd_dir.glob("*.md")
        if any(kw in p.name for kw in ("new-paper", "adopt", "init", "bootstrap"))
    ]
    assert bootstrap_like == ["gsd-new-paper.md"], (
        f"Expected exactly one bootstrap command (gsd-new-paper.md). "
        f"Found: {bootstrap_like}. The single-entry-point contract is broken."
    )


def test_new_paper_documents_both_modes(repo_root: Path) -> None:
    body = (repo_root / "commands" / "gsd-new-paper.md").read_text(encoding="utf-8")
    assert "--new" in body, "gsd-new-paper.md must document the --new flag"
    assert "--adopt" in body, "gsd-new-paper.md must document the --adopt flag"


def test_new_paper_documents_auto_detection(repo_root: Path) -> None:
    body = (repo_root / "commands" / "gsd-new-paper.md").read_text(encoding="utf-8").lower()
    assert "auto-detect" in body or "auto detect" in body, (
        "gsd-new-paper.md must document the auto-detection behavior "
        "(what happens when no flag is passed)"
    )


def test_new_paper_has_separate_process_per_mode(repo_root: Path) -> None:
    """Both modes should have substantive Process documentation."""
    import re
    body = (repo_root / "commands" / "gsd-new-paper.md").read_text(encoding="utf-8")
    # Look for `Process — --new` and `Process — --adopt` (or similar)
    new_process = re.search(
        r"##\s+Process.*?(?:new|greenfield)", body, flags=re.IGNORECASE
    )
    adopt_process = re.search(
        r"##\s+Process.*?(?:adopt|brownfield)", body, flags=re.IGNORECASE
    )
    assert new_process, "gsd-new-paper.md should have a Process section for --new mode"
    assert adopt_process, "gsd-new-paper.md should have a Process section for --adopt mode"


def test_adopt_mode_documents_read_only_constraint(repo_root: Path) -> None:
    """The critical adopt-mode invariant: do not modify existing manuscript/code."""
    body = (repo_root / "commands" / "gsd-new-paper.md").read_text(encoding="utf-8").lower()
    assert "read-only" in body or "do not modify" in body, (
        "gsd-new-paper.md --adopt mode must explicitly state the read-only constraint "
        "over the existing manuscript and codebase"
    )


def test_adopting_doc_exists_and_links_back(repo_root: Path) -> None:
    """The brownfield doc must exist and the README must reference it."""
    doc = repo_root / "docs" / "adopting-mid-project.md"
    assert doc.is_file(), "docs/adopting-mid-project.md must exist"

    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "adopting-mid-project" in readme, (
        "README.md must link to docs/adopting-mid-project.md for discoverability"
    )
