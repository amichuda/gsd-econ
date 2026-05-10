"""
Layer 3 — Documentation accuracy.

The docs make specific claims (counts, file lists, integration details). These
tests verify the claims match reality.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


def test_tests_readme_count_matches(repo_root: Path) -> None:
    """tests/README.md claims a count of tests in the repo. It should match."""
    readme = (repo_root / "tests" / "README.md").read_text(encoding="utf-8")
    actual = len(list((repo_root / "tests" / "core").glob("*.md")))

    # Look for "<n> in this repo" or "<n> tests in" patterns
    matches = re.findall(r"\b(\d+)\s+(?:more|tests?|core)", readme)
    if matches:
        # Take the largest reasonable count mentioned
        claimed = max(int(m) for m in matches if int(m) <= 30)
        assert claimed == actual, (
            f"tests/README.md mentions {claimed} tests but tests/core/ contains {actual}. "
            "Update the README claim or the test set."
        )


def test_license_year_present(repo_root: Path) -> None:
    license_text = (repo_root / "LICENSE").read_text(encoding="utf-8")
    # Some plausible year — sanity check that it's not a clearly broken template
    assert re.search(r"20\d\d", license_text), "LICENSE has no year"


def test_license_mentions_attribution(repo_root: Path) -> None:
    """LICENSE should attribute upstream GSD and RUT."""
    text = (repo_root / "LICENSE").read_text(encoding="utf-8")
    assert "get-shit-done" in text or "GSD" in text or "TÂCHES" in text, (
        "LICENSE should attribute upstream GSD"
    )
    assert "research-unit-tests" in text or "rdahis" in text, (
        "LICENSE should attribute upstream RUT"
    )


def test_install_md_mentions_three_layers(repo_root: Path) -> None:
    """INSTALL.md should walk through the three-layer install (GSD, RUT, gsd-econ)."""
    text = (repo_root / "INSTALL.md").read_text(encoding="utf-8").lower()
    assert "minimal" in text, "INSTALL.md should mention --minimal flag for GSD"
    assert "research-unit-tests" in text, "INSTALL.md should reference RUT"
    assert "submodule" in text, "INSTALL.md should explain submodule pattern"


def test_readme_mentions_both_upstream_projects(repo_root: Path) -> None:
    text = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "get-shit-done" in text or "GSD" in text, (
        "README should mention upstream GSD"
    )
    assert "research-unit-tests" in text or "rdahis" in text, (
        "README should mention upstream RUT"
    )


def test_readme_has_quick_start(repo_root: Path) -> None:
    text = (repo_root / "README.md").read_text(encoding="utf-8").lower()
    assert "quick start" in text or "getting started" in text, (
        "README should have a quick-start section"
    )


def test_verification_md_explains_layers(repo_root: Path) -> None:
    """VERIFICATION.md should explain the testing approach."""
    text = (repo_root / "VERIFICATION.md").read_text(encoding="utf-8").lower()
    # Should mention the layered approach and what's NOT tested
    assert "layer" in text or "structural" in text, (
        "VERIFICATION.md should describe the test layers"
    )
    assert "manual" in text or "not test" in text or "limitation" in text, (
        "VERIFICATION.md should explain what is NOT auto-tested"
    )
