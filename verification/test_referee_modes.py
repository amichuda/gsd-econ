"""
Layer 2 — /gsd-referee-sim K-parameterized contract.

The referee-sim command supports:
- A K parameter (--n-referees) controlling how many parallel referees run
- A --heavy mode toggling K light-tier referees + 1 heavy-tier deliberator,
  vs the default of K heavy-tier referees aggregated by cross-tabulation

These tests enforce that the contract is documented and the agents exist.
The architectural pattern in --heavy mode is inspired by HeavySkill
(https://github.com/wjn1996/HeavySkill); attribution must be present.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import Document, parse_markdown


def test_referee_sim_command_documents_k_parameter(repo_root: Path) -> None:
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8")
    assert "--n-referees" in text, (
        "/gsd-referee-sim must document --n-referees parameter"
    )
    # K is referenced in process and cost-guidance discussions
    assert " K " in text or "K=" in text or "K referees" in text.lower(), (
        "/gsd-referee-sim must use K notation when describing the parallel-referee count"
    )


def test_referee_sim_command_documents_heavy_mode(repo_root: Path) -> None:
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8")
    assert "--heavy" in text, "/gsd-referee-sim must document --heavy flag"


def test_referee_sim_command_describes_both_modes(repo_root: Path) -> None:
    """The command must explain when to use each mode."""
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8")
    text_lower = text.lower()
    # Both modes should be characterized
    assert "default mode" in text_lower or "default (no" in text_lower, (
        "/gsd-referee-sim should describe the default mode explicitly"
    )
    assert "heavy" in text_lower and "deliberator" in text_lower, (
        "/gsd-referee-sim should describe the heavy mode and the deliberator role"
    )


def test_referee_sim_command_warns_about_pathological_configs(repo_root: Path) -> None:
    """E.g., --heavy when light tier == heavy tier is wasted money. Must be flagged."""
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8").lower()
    assert "warn" in text or "warning" in text, (
        "/gsd-referee-sim should describe warnings for pathological configurations "
        "(e.g., --heavy with light tier == heavy tier)"
    )


def test_referee_sim_light_agent_exists(repo_root: Path) -> None:
    path = repo_root / "agents" / "referee-sim-light.md"
    assert path.is_file(), "agents/referee-sim-light.md must exist for --heavy mode"


def test_referee_sim_light_is_light_tier(repo_root: Path) -> None:
    doc = parse_markdown(repo_root / "agents" / "referee-sim-light.md")
    assert doc.frontmatter.get("model_tier") == "light", (
        "referee-sim-light must declare model_tier: light "
        "(the whole point of heavy mode is cheap parallel referees)"
    )


def test_referee_deliberator_agent_exists(repo_root: Path) -> None:
    path = repo_root / "agents" / "referee-deliberator.md"
    assert path.is_file(), "agents/referee-deliberator.md must exist for --heavy mode"


def test_referee_deliberator_is_heavy_tier(repo_root: Path) -> None:
    doc = parse_markdown(repo_root / "agents" / "referee-deliberator.md")
    assert doc.frontmatter.get("model_tier") == "heavy", (
        "referee-deliberator must declare model_tier: heavy "
        "(deliberation is the depth-stage of the heavy-skill pattern)"
    )


def test_referee_sim_default_remains_heavy_tier(repo_root: Path) -> None:
    """The original referee-sim agent (used in default mode) stays heavy."""
    doc = parse_markdown(repo_root / "agents" / "referee-sim.md")
    assert doc.frontmatter.get("model_tier") == "heavy", (
        "referee-sim (default mode) must remain model_tier: heavy"
    )


def test_command_references_both_referee_agents(repo_root: Path) -> None:
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8")
    assert "referee-sim-light" in text, (
        "/gsd-referee-sim must reference referee-sim-light for --heavy mode"
    )
    assert "referee-deliberator" in text, (
        "/gsd-referee-sim must reference referee-deliberator for --heavy mode"
    )


def test_heavy_skill_attribution_in_command(repo_root: Path) -> None:
    """HeavySkill must be cited where the pattern is described."""
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8")
    assert "HeavySkill" in text, (
        "/gsd-referee-sim must cite HeavySkill where the parallel-deliberator pattern "
        "is described (it's inspired by their work)"
    )
    assert "wjn1996" in text or "github.com/wjn1996" in text.lower(), (
        "/gsd-referee-sim should link to the HeavySkill repo when citing the inheritance"
    )


def test_heavy_skill_attribution_in_deliberator(repo_root: Path) -> None:
    """The deliberator agent itself acknowledges where the pattern came from."""
    text = (repo_root / "agents" / "referee-deliberator.md").read_text(encoding="utf-8")
    assert "HeavySkill" in text, (
        "agents/referee-deliberator.md must cite HeavySkill — "
        "the parallel-cheap-then-strong-deliberation pattern is theirs"
    )


def test_heavy_skill_attribution_in_contributing(repo_root: Path) -> None:
    """CONTRIBUTING.md is the primary attribution venue."""
    text = (repo_root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "HeavySkill" in text, (
        "CONTRIBUTING.md must list HeavySkill in 'Prior art and attribution'"
    )


def test_command_documents_cost_implications(repo_root: Path) -> None:
    """Users need to know that --heavy with all tiers on the same model is wasteful."""
    text = (repo_root / "commands" / "gsd-referee-sim.md").read_text(encoding="utf-8").lower()
    assert "cost" in text, "/gsd-referee-sim must discuss cost trade-offs"
    # The warning about light==heavy degenerate config must exist
    assert "light" in text and "heavy" in text, (
        "/gsd-referee-sim cost guidance must discuss the light/heavy trade-off explicitly"
    )
