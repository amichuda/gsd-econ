"""
Layer 2 — Model-tier system contract.

Agents declare reasoning load (light/standard/heavy); user config maps tier
to actual model. These tests enforce:
- Every agent has a tier (covered in test_commands_agents.py too, here we
  add tier-distribution sanity)
- The tier system is documented
- The config example demonstrates the mapping
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import VALID_MODEL_TIERS, Document, parse_markdown


def test_model_tiers_doc_exists(repo_root: Path) -> None:
    doc = repo_root / "docs" / "model-tiers.md"
    assert doc.is_file(), (
        "docs/model-tiers.md must exist to document the tier system"
    )


def test_model_tiers_doc_lists_all_three_tiers(repo_root: Path) -> None:
    text = (repo_root / "docs" / "model-tiers.md").read_text(encoding="utf-8")
    for tier in VALID_MODEL_TIERS:
        assert tier in text, f"docs/model-tiers.md does not document tier {tier!r}"


def test_tier_distribution_not_all_heavy(agents: list[Document]) -> None:
    """
    Sanity check: not every agent should be 'heavy'. If they are, the user gets
    no benefit from the tier system. Some legitimately need heavy; some don't.
    """
    tiers = [doc.frontmatter.get("model_tier") for doc in agents]
    heavy_count = tiers.count("heavy")
    total = len(tiers)
    assert heavy_count < total, (
        f"All {total} agents declare model_tier=heavy. "
        "Tier system is meaningless if no agent uses light/standard. "
        "Reconsider: which agents do mechanical work (light) or routine synthesis (standard)?"
    )


def test_tier_distribution_has_at_least_one_heavy(agents: list[Document]) -> None:
    """Some agents legitimately need heavy reasoning. If none do, the system isn't doing serious work."""
    tiers = [doc.frontmatter.get("model_tier") for doc in agents]
    heavy_count = tiers.count("heavy")
    assert heavy_count >= 1, (
        "No agent declares model_tier=heavy. "
        "Identification-checker, econometrician, and referee-sim should be heavy. "
        "Did you accidentally downgrade?"
    )


def test_readme_or_install_mentions_model_tiers(repo_root: Path) -> None:
    """Users discover the tier system through the docs they read first."""
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8")
    combined = readme + install
    assert "model_tier" in combined or "model-tiers" in combined or "tier" in combined.lower(), (
        "README or INSTALL should mention the model-tier system somewhere "
        "so users know they can configure it. Link to docs/model-tiers.md."
    )
