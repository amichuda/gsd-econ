"""
Layer 2 — Polish-pass contract.

The polish-pass is a fan-out of N parallel agents writing to a known directory
structure, aggregated by /gsd-polish-pass. These tests enforce:
- The five expected polish agents exist
- Each is light or standard or heavy tier (orchestrator schedules accordingly)
- The /gsd-polish-pass command exists and references all five
- /gsd-submit-paper invokes /gsd-polish-pass
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import Document, parse_markdown


EXPECTED_POLISH_AGENTS = {
    "polish-numbers",
    "polish-cross-refs",
    "polish-citations",
    "polish-consistency",
    "polish-claims",
}


def test_all_polish_agents_exist(repo_root: Path) -> None:
    agents_dir = repo_root / "agents"
    found = {p.stem for p in agents_dir.glob("polish-*.md")}
    missing = EXPECTED_POLISH_AGENTS - found
    extra = found - EXPECTED_POLISH_AGENTS
    assert not missing, f"Missing polish agents: {missing}"
    # Don't fail on extra — additions are fine — but warn loudly via failure
    # if naming convention violated
    for name in found:
        assert name.startswith("polish-"), f"Polish agent {name} doesn't follow polish-* naming"


def test_polish_agents_have_tier(repo_root: Path) -> None:
    """All polish agents must declare a tier (just like other agents)."""
    for stem in EXPECTED_POLISH_AGENTS:
        doc = parse_markdown(repo_root / "agents" / f"{stem}.md")
        assert "model_tier" in doc.frontmatter, (
            f"Polish agent {stem}: missing model_tier"
        )


def test_polish_pass_command_exists(repo_root: Path) -> None:
    cmd = repo_root / "commands" / "gsd-polish-pass.md"
    assert cmd.is_file(), "commands/gsd-polish-pass.md must exist"


def test_polish_pass_command_references_all_polish_agents(repo_root: Path) -> None:
    """The orchestrator command should mention each polish agent by name."""
    cmd_text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8")
    for agent in EXPECTED_POLISH_AGENTS:
        assert agent in cmd_text, (
            f"/gsd-polish-pass command does not reference {agent}. "
            "The orchestrator must spawn all polish agents."
        )


def test_submit_paper_invokes_polish_pass(repo_root: Path) -> None:
    """/gsd-submit-paper must invoke /gsd-polish-pass before final."""
    text = (repo_root / "commands" / "gsd-submit-paper.md").read_text(encoding="utf-8")
    assert "/gsd-polish-pass" in text or "gsd-polish-pass" in text, (
        "/gsd-submit-paper must invoke /gsd-polish-pass as part of the pre-submission flow"
    )


def test_polish_pass_documents_round_cap(repo_root: Path) -> None:
    """Polish pass should cap rounds to prevent endless loops."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    assert "round" in text and ("cap" in text or "default" in text or "limit" in text), (
        "/gsd-polish-pass should document a round cap to prevent endless loops"
    )


def test_polish_pass_documents_user_triage(repo_root: Path) -> None:
    """User must triage findings — never auto-execute fixes."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    triage_terms = ["triage", "address", "acknowledge", "dispute"]
    found = [t for t in triage_terms if t in text]
    assert len(found) >= 3, (
        f"/gsd-polish-pass should document user triage with options like "
        f"address/acknowledge/dispute. Found only: {found}"
    )


def test_polish_pass_disclaims_modifying_manuscript(repo_root: Path) -> None:
    """Polish agents and the orchestrator must not modify the manuscript directly."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    assert "do not modify" in text or "read-only" in text, (
        "/gsd-polish-pass should explicitly state it doesn't modify the manuscript "
        "(fixes go through user-triaged plans)"
    )
