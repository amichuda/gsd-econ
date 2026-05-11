"""Regression tests for wire_config: user edits to config.json must be preserved.

Bug history:
  v0.1.0 used `jq -s '.[0] * .[1]'` to merge the upstream example *over*
  the user's config — meaning every install.sh --wire-only would clobber
  user-tuned fields like model_tiers. Result: users who switched to
  OpenRouter/DeepSeek would silently get their tiers reverted to Anthropic
  on next wire-only, with no warning.

Fix: wire_config now never modifies an existing config. It only writes
config.json on a fresh install (when the file is absent).

These tests ensure that fix stays in place.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
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


def test_wire_only_preserves_user_edits_to_model_tiers(repo_root: Path) -> None:
    """The exact regression: user edits model_tiers, runs wire-only, edits must survive.

    Reproduces the scenario:
      1. Fresh install creates config from example (Anthropic models).
      2. User edits config.json to use OpenRouter/DeepSeek model strings.
      3. User runs install.sh --wire-only.
      4. Expected: model_tiers in config.json still has the user's values.
      5. Expected: agent files have model: openrouter/... after re-resolution.
    """
    install_script = repo_root / "install.sh"
    assert install_script.exists()

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)

        # Step 1: fresh install
        result = _run_install(
            install_script,
            "--project", str(project),
            "--runtime", "opencode",
            "--skip-gsd", "--skip-rut", "--yes",
        )
        assert result.returncode == 0, (
            f"Fresh install failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        config_path = project / ".planning" / "config.json"
        assert config_path.exists(), "Fresh install didn't create config.json"

        # Step 2: user edits config.json to OpenRouter
        config = json.loads(config_path.read_text(encoding="utf-8"))
        user_tiers = {
            "_comment": "User-customized OpenRouter routing",
            "light": "openrouter/deepseek/deepseek-v4-flash",
            "standard": "openrouter/deepseek/deepseek-v4-flash",
            "heavy": "openrouter/deepseek/deepseek-v4-pro",
        }
        config["model_tiers"] = user_tiers
        # Also add a non-tier field to verify the whole config is preserved
        config["user_added_field"] = "must-survive-wire-only"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        # Step 3: wire-only must be invoked from within the project
        # (it auto-detects PROJECT_DIR from cwd).
        result = _run_install(
            install_script,
            "--wire-only", "--yes",
            cwd=project,
        )
        assert result.returncode == 0, (
            f"wire-only failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Step 4: config.json still has user's model_tiers
        config_after = json.loads(config_path.read_text(encoding="utf-8"))
        assert config_after.get("model_tiers") == user_tiers, (
            "wire-only clobbered user's model_tiers.\n"
            f"Expected: {user_tiers}\n"
            f"Got:      {config_after.get('model_tiers')}"
        )
        assert config_after.get("user_added_field") == "must-survive-wire-only", (
            "wire-only removed a user-added field. wire_config must be "
            "purely additive on existing configs."
        )

        # Step 5: agent files reflect the user's model choices
        agent_path = project / ".opencode" / "agent" / "identification-checker.md"
        assert agent_path.exists(), (
            "identification-checker.md missing after wire-only"
        )
        agent_text = agent_path.read_text(encoding="utf-8")
        # heavy tier → openrouter/deepseek/deepseek-v4-pro
        assert "model: openrouter/deepseek/deepseek-v4-pro" in agent_text, (
            "Heavy-tier agent didn't get the user's openrouter model after wire-only.\n"
            f"Agent frontmatter:\n{agent_text[:500]}"
        )

        light_agent = project / ".opencode" / "agent" / "polish-cross-refs.md"
        light_text = light_agent.read_text(encoding="utf-8")
        assert "model: openrouter/deepseek/deepseek-v4-flash" in light_text, (
            "Light-tier agent didn't get the user's openrouter model after wire-only."
        )


def test_fresh_install_creates_config_from_example(repo_root: Path) -> None:
    """A first-time install must create config.json from the example."""
    install_script = repo_root / "install.sh"
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        result = _run_install(
            install_script,
            "--project", str(project),
            "--runtime", "opencode",
            "--skip-gsd", "--skip-rut", "--yes",
        )
        assert result.returncode == 0
        config_path = project / ".planning" / "config.json"
        assert config_path.exists()
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert "model_tiers" in config, "Fresh install config missing model_tiers"


def test_wire_only_does_not_touch_existing_config_file_contents(repo_root: Path) -> None:
    """wire-only must leave config.json byte-identical when it exists."""
    install_script = repo_root / "install.sh"
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        result = _run_install(
            install_script,
            "--project", str(project),
            "--runtime", "opencode",
            "--skip-gsd", "--skip-rut", "--yes",
        )
        assert result.returncode == 0

        config_path = project / ".planning" / "config.json"
        # Make a custom config (different from the example) and snapshot it
        custom = {
            "version": 1,
            "model_tiers": {
                "light": "x/y",
                "standard": "x/z",
                "heavy": "x/w",
            },
            "weird_user_field": [1, 2, 3],
        }
        config_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")
        before = config_path.read_text(encoding="utf-8")

        result = _run_install(install_script, "--wire-only", "--yes", cwd=project)
        assert result.returncode == 0

        after = config_path.read_text(encoding="utf-8")
        assert before == after, (
            "wire-only modified config.json byte-content. "
            "It must be purely read-only on existing configs."
        )
