"""
Layer 2 — CITATION.cff existence and validity.

The CITATION.cff file enables GitHub's "Cite this repository" button and is
parseable by Zotero, Zenodo, etc. It must exist, be valid YAML, and follow
the CFF v1.2.0 schema (at least minimally).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


REQUIRED_CFF_FIELDS = {"cff-version", "message", "title", "authors"}


def test_citation_cff_exists(repo_root: Path) -> None:
    path = repo_root / "CITATION.cff"
    assert path.is_file(), (
        "CITATION.cff must exist at the repo root for GitHub's "
        "'Cite this repository' integration to work."
    )


def test_citation_cff_is_valid_yaml(repo_root: Path) -> None:
    path = repo_root / "CITATION.cff"
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        pytest.fail(f"CITATION.cff is not valid YAML: {e}")
    assert isinstance(data, dict), "CITATION.cff must be a YAML mapping"


def test_citation_cff_has_required_fields(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    missing = REQUIRED_CFF_FIELDS - data.keys()
    assert not missing, (
        f"CITATION.cff missing required CFF v1.2.0 fields: {missing}"
    )


def test_citation_cff_version_supported(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    assert data["cff-version"] == "1.2.0", (
        f"cff-version should be 1.2.0 (got {data['cff-version']}). "
        "GitHub's parser is built against this version."
    )


def test_citation_cff_license_matches_repo(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    assert data.get("license") == "MIT", (
        "CITATION.cff license field should match the LICENSE file (MIT). "
        "If you change the project license, update both."
    )


def test_citation_cff_authors_nonempty(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    authors = data.get("authors", [])
    assert isinstance(authors, list) and len(authors) >= 1, (
        "CITATION.cff must have at least one author. "
        "Edit the file to fill in your name before publishing."
    )


def test_citation_cff_attributes_upstream(repo_root: Path) -> None:
    """The references list should mention GSD and RUT (the projects we build on)."""
    data = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    refs = data.get("references", [])
    assert refs, (
        "CITATION.cff should list GSD and research-unit-tests under references — "
        "these are the projects gsd-econ depends on."
    )
    titles = " ".join(str(r.get("title", "")) for r in refs).lower()
    assert "get-shit-done" in titles or "gsd" in titles, (
        "CITATION.cff references should include get-shit-done (GSD)"
    )
    assert "research-unit-tests" in titles, (
        "CITATION.cff references should include research-unit-tests"
    )


@pytest.mark.skipif(
    shutil.which("cffconvert") is None,
    reason="cffconvert not installed; skipping formal schema validation",
)
def test_citation_cff_passes_formal_validation(repo_root: Path) -> None:
    """If cffconvert is installed, run its formal schema validation."""
    result = subprocess.run(
        ["cffconvert", "--validate"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"cffconvert --validate failed:\n{result.stdout}\n{result.stderr}\n"
        "Run `cffconvert --validate` locally to debug."
    )


def test_readme_links_to_citation(repo_root: Path) -> None:
    """README should reference CITATION.cff or the citation feature so users find it."""
    text = (repo_root / "README.md").read_text(encoding="utf-8").lower()
    assert "citation" in text or "cite" in text, (
        "README should mention how to cite this work "
        "(point users at CITATION.cff or describe the acknowledgment norm)."
    )
