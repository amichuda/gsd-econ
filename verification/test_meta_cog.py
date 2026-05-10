"""
Layer 2 — `--meta-cog` and `--offload-policy` contracts.

Stage 1 (`--meta-cog`): the load-bearing judgment commands accept the flag,
which causes N=3 parallel invocations of the agent and disagreement-based
confidence rating. Implements the workflow-level version of the metacognition
proposal in Yona, Geva, and Matias (2026, arXiv:2605.01428).

Stage 2 (`--offload-policy`): /gsd-polish-pass accepts a policy flag that
controls how much triage gets offloaded from the user. Composes with
`--meta-cog`: aggressive offload without meta-cog should warn.
"""
from __future__ import annotations

from pathlib import Path

import pytest


# Commands that must accept --meta-cog
META_COG_COMMANDS = [
    "commands/gsd-plan-empirics.md",
    "commands/gsd-discuss-identification.md",
    "commands/gsd-referee-sim.md",
    "commands/gsd-polish-pass.md",
]


def test_meta_cog_documented_in_each_command(repo_root: Path) -> None:
    """Every command that accepts --meta-cog must document it in its body."""
    for cmd_path in META_COG_COMMANDS:
        text = (repo_root / cmd_path).read_text(encoding="utf-8")
        assert "--meta-cog" in text, (
            f"{cmd_path} must document the --meta-cog flag if it accepts it"
        )


def test_meta_cog_in_command_arguments(repo_root: Path) -> None:
    """The frontmatter `arguments` field should advertise --meta-cog."""
    for cmd_path in META_COG_COMMANDS:
        text = (repo_root / cmd_path).read_text(encoding="utf-8")
        # Take the frontmatter block (between the first two --- lines)
        if not text.startswith("---"):
            pytest.fail(f"{cmd_path} missing frontmatter")
        end = text.find("\n---", 4)
        frontmatter = text[:end]
        assert "--meta-cog" in frontmatter or "meta-cog" in frontmatter, (
            f"{cmd_path} frontmatter does not advertise --meta-cog "
            "(should be in the `arguments` field)"
        )


def test_meta_cog_cites_yona_paper(repo_root: Path) -> None:
    """Each --meta-cog mention should ground the technique in the source paper."""
    citations_per_command = {}
    for cmd_path in META_COG_COMMANDS:
        text = (repo_root / cmd_path).read_text(encoding="utf-8")
        citations_per_command[cmd_path] = (
            "2605.01428" in text
            or "Yona" in text
            or "meta-cognition.md" in text
        )
    missing = [c for c, has_cite in citations_per_command.items() if not has_cite]
    assert not missing, (
        f"These commands mention --meta-cog without citing the source: {missing}. "
        "Either link to docs/meta-cognition.md or cite Yona, Geva, Matias (2026, arXiv:2605.01428)."
    )


def test_meta_cog_documented_in_docs(repo_root: Path) -> None:
    """docs/meta-cognition.md must exist and explain the mechanism."""
    doc = repo_root / "docs" / "meta-cognition.md"
    assert doc.is_file(), "docs/meta-cognition.md must exist"
    text = doc.read_text(encoding="utf-8")
    # Must explain the disagreement-as-uncertainty mechanism
    assert "disagreement" in text.lower() or "agreement" in text.lower(), (
        "docs/meta-cognition.md must explain the disagreement-as-uncertainty mechanism"
    )
    # Must explain the cost
    assert "3×" in text or "3x" in text or "three" in text.lower(), (
        "docs/meta-cognition.md should be honest about the 3× cost"
    )
    # Must cite the paper
    assert "2605.01428" in text or "Yona" in text, (
        "docs/meta-cognition.md must cite the source paper"
    )


def test_meta_cog_doc_acknowledges_limits(repo_root: Path) -> None:
    """The doc must be honest about what --meta-cog doesn't fix."""
    text = (repo_root / "docs" / "meta-cognition.md").read_text(encoding="utf-8").lower()
    limit_indicators = ["limit", "not", "doesn't", "does not", "ceiling", "small"]
    found = sum(1 for word in limit_indicators if word in text)
    assert found >= 3, (
        "docs/meta-cognition.md should explicitly discuss what --meta-cog "
        "doesn't fix (discrimination gap, linguistic decisiveness, N=3 small)"
    )


def test_offload_policy_documented_in_polish_pass(repo_root: Path) -> None:
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8")
    assert "--offload-policy" in text, (
        "/gsd-polish-pass must document the --offload-policy flag"
    )


def test_offload_policy_has_three_levels(repo_root: Path) -> None:
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    for level in ["manual", "assisted", "aggressive"]:
        assert level in text, (
            f"/gsd-polish-pass should document the '{level}' offload policy level"
        )


def test_offload_policy_default_is_manual(repo_root: Path) -> None:
    """Default behavior must be manual triage to preserve the current contract."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    # Look for an explicit "default" near "manual"
    assert "manual" in text and "default" in text, (
        "/gsd-polish-pass must specify that the default offload policy is 'manual' "
        "(preserves the existing 'user always triages' contract)"
    )


def test_aggressive_without_meta_cog_warns(repo_root: Path) -> None:
    """If aggressive offload is set without meta-cog, the command should warn."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8").lower()
    # The command should describe a warning when aggressive is used alone
    assert "warn" in text and "aggressive" in text, (
        "/gsd-polish-pass should warn when --offload-policy aggressive is set "
        "without --meta-cog (aggressive offload on uncalibrated confidence is "
        "the failure mode the Yona paper warns against)"
    )


def test_offload_policy_logs_to_state(repo_root: Path) -> None:
    """The offload decision must go in STATE.md for the audit trail."""
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8")
    assert "STATE.md" in text, (
        "/gsd-polish-pass must log offload-policy decisions to STATE.md "
        "(audit trail discipline)"
    )


def test_meta_cog_doc_explains_offload_composition(repo_root: Path) -> None:
    """The doc must explain how the two flags compose."""
    text = (repo_root / "docs" / "meta-cognition.md").read_text(encoding="utf-8").lower()
    assert "offload" in text, (
        "docs/meta-cognition.md should explain how --meta-cog composes with "
        "--offload-policy"
    )
    assert "compose" in text or "with" in text, (
        "docs/meta-cognition.md should make composition explicit"
    )


def test_polish_pass_preserves_manual_triage_path(repo_root: Path) -> None:
    """
    Even with the new flags, the existing user-triage Step 4 must still exist.
    Adding offload doesn't remove the path that runs every finding past the user.
    """
    text = (repo_root / "commands" / "gsd-polish-pass.md").read_text(encoding="utf-8")
    # Step 4 (or its renumbered equivalent) should still describe user triage
    assert "user" in text.lower() and "triage" in text.lower(), (
        "/gsd-polish-pass must preserve the user-triage path even with offload-policy"
    )


def test_meta_cog_described_as_optional(repo_root: Path) -> None:
    """The flag must not become a default — it's opt-in due to cost."""
    for cmd_path in META_COG_COMMANDS:
        text = (repo_root / cmd_path).read_text(encoding="utf-8").lower()
        # Should describe the flag as optional / off by default
        assert "default off" in text or "opt in" in text or "optional" in text, (
            f"{cmd_path} should describe --meta-cog as optional / default-off "
            f"(it's a cost trade-off, shouldn't be silently on)"
        )
