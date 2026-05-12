"""Tests for the --models-config / --interactive-models flow.

Verifies that:
  1. All shipped templates in config/model-configs/ parse and apply correctly.
  2. The apply script writes both .planning/config.json and opencode.json.
  3. install.sh --models-config end-to-end produces correctly-resolved agents.
  4. install.sh --wire-only --models-config switches model configs while
     preserving other user fields.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run_install(install_script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run install.sh with given args. Returns the completed process."""
    cmd = ["bash", str(install_script), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ},
    )


def test_all_model_templates_parse(repo_root: Path) -> None:
    """Every shipped template must be valid YAML with the required schema."""
    yaml = pytest.importorskip("yaml")
    templates_dir = repo_root / "config" / "model-configs"
    assert templates_dir.is_dir(), "config/model-configs/ missing"
    yamls = sorted(templates_dir.glob("*.yaml"))
    assert yamls, "No YAML templates shipped"
    required = {"runtime", "provider", "tiers"}
    for path in yamls:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path.name} not a mapping"
        missing = required - set(data.keys())
        assert not missing, f"{path.name} missing keys {missing}"
        for tier in ("light", "standard", "heavy"):
            assert tier in data["tiers"], f"{path.name} missing tiers.{tier}"
            assert "/" in data["tiers"][tier], (
                f"{path.name}: tiers.{tier} must be provider-prefixed"
            )


def test_apply_script_writes_both_files(repo_root: Path) -> None:
    """apply-models-config.py must produce both .planning/config.json and opencode.json."""
    script = repo_root / "scripts" / "apply-models-config.py"
    assert script.exists()
    template = repo_root / "config" / "model-configs" / "openrouter-deepseek.yaml"
    assert template.exists()
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        result = subprocess.run(
            [sys.executable, str(script), str(template), str(project)],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, f"apply failed: {result.stderr}"
        assert (project / ".planning" / "config.json").exists()
        assert (project / "opencode.json").exists()

        config = json.loads((project / ".planning" / "config.json").read_text())
        assert config["model_tiers"]["heavy"] == "openrouter/deepseek/deepseek-v4-pro"

        opencode = json.loads((project / "opencode.json").read_text())
        assert opencode["model"] == "openrouter/deepseek/deepseek-v4-flash"
        assert "openrouter" in opencode["provider"]
        assert "AGENTS.md" in opencode["instructions"]


def test_install_with_models_config_resolves_agents(repo_root: Path) -> None:
    """install.sh --models-config end-to-end produces correctly-tiered agents."""
    install_script = repo_root / "install.sh"
    template = repo_root / "config" / "model-configs" / "openrouter-hybrid.yaml"
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        result = _run_install(
            install_script,
            "--project", str(project),
            "--runtime", "opencode",
            "--skip-gsd", "--skip-rut", "--yes",
            "--models-config", str(template),
        )
        assert result.returncode == 0, f"install failed: {result.stderr}\n{result.stdout}"

        # Heavy-tier agent should have Claude Opus (hybrid template)
        id_agent = (project / ".opencode" / "agent" / "identification-checker.md").read_text()
        assert "model: openrouter/anthropic/claude-opus-4-7" in id_agent, (
            f"Heavy tier not resolved correctly. Got frontmatter:\n{id_agent[:400]}"
        )

        # Light-tier agent should have DeepSeek Flash
        light_agent = (project / ".opencode" / "agent" / "polish-cross-refs.md").read_text()
        assert "model: openrouter/deepseek/deepseek-v4-flash" in light_agent

        # opencode.json should exist with provider block
        opencode = json.loads((project / "opencode.json").read_text())
        assert "openrouter" in opencode["provider"]


def test_wire_only_models_config_switches_correctly(repo_root: Path) -> None:
    """wire-only --models-config must switch agent models and update config.json
    without clobbering other user keys."""
    install_script = repo_root / "install.sh"
    deepseek = repo_root / "config" / "model-configs" / "openrouter-deepseek.yaml"
    hybrid = repo_root / "config" / "model-configs" / "openrouter-hybrid.yaml"

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)

        # Step 1: install with deepseek
        result = _run_install(
            install_script,
            "--project", str(project),
            "--runtime", "opencode",
            "--skip-gsd", "--skip-rut", "--yes",
            "--models-config", str(deepseek),
        )
        assert result.returncode == 0

        # Step 2: user adds a custom field to config.json
        config_path = project / ".planning" / "config.json"
        config = json.loads(config_path.read_text())
        config["user_added_field"] = "must-survive"
        config_path.write_text(json.dumps(config, indent=2))

        # Step 3: switch to hybrid via wire-only
        result = _run_install(
            install_script,
            "--wire-only", "--yes",
            "--models-config", str(hybrid),
            cwd=project,
        )
        assert result.returncode == 0, f"wire-only failed: {result.stderr}"

        # Step 4: verify model_tiers switched
        config_after = json.loads(config_path.read_text())
        assert config_after["model_tiers"]["heavy"] == "openrouter/anthropic/claude-opus-4-7"
        # User-added field must survive
        assert config_after.get("user_added_field") == "must-survive", (
            "wire-only --models-config clobbered a user-added field"
        )

        # Step 5: agents reflect the switch
        id_agent = (project / ".opencode" / "agent" / "identification-checker.md").read_text()
        assert "model: openrouter/anthropic/claude-opus-4-7" in id_agent


def test_apply_script_rejects_bare_model_strings(repo_root: Path) -> None:
    """The schema check must reject tier values without provider prefix."""
    script = repo_root / "scripts" / "apply-models-config.py"
    bad_yaml = (
        "runtime: opencode\n"
        "provider:\n"
        "  name: anthropic\n"
        "tiers:\n"
        "  light: claude-haiku-4-5\n"  # No provider/ prefix
        "  standard: claude-sonnet-4-6\n"
        "  heavy: claude-opus-4-7\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        bad_path = Path(tmp) / "bad.yaml"
        bad_path.write_text(bad_yaml)
        project = Path(tmp) / "project"
        project.mkdir()
        result = subprocess.run(
            [sys.executable, str(script), str(bad_path), str(project)],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode != 0, "Should have rejected bare model strings"
        assert "provider-prefixed" in result.stderr.lower()
