"""
Layer 1+2 — Config files: parseable JSON and contain required keys.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_config_json_example_is_valid_json(repo_root: Path) -> None:
    path = repo_root / "config" / "config.json.example"
    text = path.read_text(encoding="utf-8")
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        pytest.fail(f"config.json.example is not valid JSON: {e}")


def test_settings_json_example_is_valid_json(repo_root: Path) -> None:
    path = repo_root / "config" / "settings.json.example"
    text = path.read_text(encoding="utf-8")
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        pytest.fail(f"settings.json.example is not valid JSON: {e}")


def test_config_has_required_top_level_keys(repo_root: Path) -> None:
    path = repo_root / "config" / "config.json.example"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    required = {"workflow", "model_profile", "model_tiers", "agent_skills", "test_registries"}
    missing = required - cfg.keys()
    assert not missing, f"config.json.example missing keys: {missing}"


def test_config_model_tiers_has_all_three(repo_root: Path) -> None:
    """model_tiers must define all three tier levels."""
    path = repo_root / "config" / "config.json.example"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    tiers = cfg["model_tiers"]
    for required_tier in ("light", "standard", "heavy"):
        assert required_tier in tiers, (
            f"config.model_tiers missing tier {required_tier!r}. "
            "Must define light, standard, and heavy."
        )
        assert isinstance(tiers[required_tier], str) and tiers[required_tier], (
            f"config.model_tiers.{required_tier} must be a non-empty model identifier"
        )


def test_config_workflow_has_discuss_mode(repo_root: Path) -> None:
    """The whole point of overriding GSD config is to set discuss_mode=discuss."""
    path = repo_root / "config" / "config.json.example"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    assert cfg["workflow"].get("discuss_mode") == "discuss", (
        "config.json.example should set workflow.discuss_mode = 'discuss' "
        "(never 'assumptions' for research workflows)"
    )


def test_config_agent_skills_references_rut(repo_root: Path) -> None:
    """agent_skills should wire RUT into the verifier."""
    path = repo_root / "config" / "config.json.example"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    verifier_skills = cfg["agent_skills"].get("verifier", [])
    assert any("research-unit-tests" in s for s in verifier_skills), (
        "config.agent_skills.verifier should include research-unit-tests path"
    )


def test_config_test_registries_includes_rut_and_gsd_econ(repo_root: Path) -> None:
    path = repo_root / "config" / "config.json.example"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    paths = cfg["test_registries"]["paths"]
    has_rut = any("research-unit-tests" in p for p in paths)
    has_gsd_econ = any("gsd-econ" in p for p in paths)
    assert has_rut, "test_registries should include the RUT registry path"
    assert has_gsd_econ, "test_registries should include the gsd-econ registry path"
