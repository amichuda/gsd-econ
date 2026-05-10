"""
Layer 2 — Command and agent file format.

Every command and agent must have YAML frontmatter with required fields.
"""
from __future__ import annotations

import pytest

from conftest import Document, has_section


# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------

def test_commands_have_frontmatter(commands: list[Document]) -> None:
    for doc in commands:
        assert doc.frontmatter, f"Command {doc.name}: no YAML frontmatter"


def test_commands_have_description(commands: list[Document]) -> None:
    for doc in commands:
        desc = doc.frontmatter.get("description", "")
        assert desc, f"Command {doc.name}: missing description"
        assert len(desc) >= 50, (
            f"Command {doc.name}: description too short ({len(desc)} chars). "
            "Should be a substantive one-liner."
        )


def test_commands_have_allowed_tools(commands: list[Document]) -> None:
    for doc in commands:
        assert "allowed-tools" in doc.frontmatter, (
            f"Command {doc.name}: missing allowed-tools field"
        )


def test_commands_have_process_section(commands: list[Document]) -> None:
    """Each command's body should have a Process or Steps section."""
    for doc in commands:
        ok = has_section(doc.body, "Process") or has_section(doc.body, "Steps")
        assert ok, f"Command {doc.name}: missing ## Process or ## Steps section"


def test_commands_have_constraints_section(commands: list[Document]) -> None:
    """Constraints section is mandatory — surfaces what NOT to do."""
    for doc in commands:
        assert has_section(doc.body, "Constraints"), (
            f"Command {doc.name}: missing ## Constraints section"
        )


def test_commands_have_output_section(commands: list[Document]) -> None:
    for doc in commands:
        assert has_section(doc.body, "Output"), (
            f"Command {doc.name}: missing ## Output section"
        )


def test_command_filenames_start_with_gsd(commands: list[Document]) -> None:
    """All gsd-econ commands follow the gsd-* naming pattern."""
    for doc in commands:
        assert doc.path.name.startswith("gsd-"), (
            f"Command {doc.path.name} does not follow gsd-* naming"
        )


def test_commands_body_substantive(commands: list[Document]) -> None:
    """Command body should be at least 1500 chars — these are detailed prompts."""
    for doc in commands:
        assert len(doc.body) >= 1500, (
            f"Command {doc.name}: body too short ({len(doc.body)} chars). "
            "Commands should contain specific, actionable instructions."
        )


# -----------------------------------------------------------------------------
# Agents
# -----------------------------------------------------------------------------

def test_agents_have_frontmatter(agents: list[Document]) -> None:
    for doc in agents:
        assert doc.frontmatter, f"Agent {doc.name}: no YAML frontmatter"


def test_agents_have_name(agents: list[Document]) -> None:
    for doc in agents:
        assert "name" in doc.frontmatter, f"Agent {doc.name}: missing name field"


def test_agent_name_matches_filename(agents: list[Document]) -> None:
    for doc in agents:
        fm_name = doc.frontmatter["name"]
        assert fm_name == doc.name, (
            f"Agent {doc.path.name}: frontmatter name={fm_name!r} does not match filename"
        )


def test_agents_have_description(agents: list[Document]) -> None:
    for doc in agents:
        desc = doc.frontmatter.get("description", "")
        assert desc, f"Agent {doc.name}: missing description"
        assert len(desc) >= 50, (
            f"Agent {doc.name}: description too short ({len(desc)} chars)"
        )


def test_agents_have_tools(agents: list[Document]) -> None:
    for doc in agents:
        assert "tools" in doc.frontmatter, f"Agent {doc.name}: missing tools field"


def test_agents_have_model_tier(agents: list[Document]) -> None:
    """Every agent must declare its reasoning-load tier."""
    for doc in agents:
        assert "model_tier" in doc.frontmatter, (
            f"Agent {doc.name}: missing model_tier field. "
            "Add 'model_tier: light|standard|heavy' to frontmatter. "
            "See docs/model-tiers.md."
        )


def test_agents_model_tier_values_valid(agents: list[Document]) -> None:
    from conftest import VALID_MODEL_TIERS
    for doc in agents:
        tier = doc.frontmatter.get("model_tier")
        assert tier in VALID_MODEL_TIERS, (
            f"Agent {doc.name}: model_tier={tier!r} is not one of "
            f"{sorted(VALID_MODEL_TIERS)}"
        )


def test_agents_body_substantive(agents: list[Document]) -> None:
    for doc in agents:
        assert len(doc.body) >= 1500, (
            f"Agent {doc.name}: body too short ({len(doc.body)} chars)"
        )
