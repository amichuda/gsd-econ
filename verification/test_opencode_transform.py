"""Tests for the OpenCode frontmatter transform.

The agent .md files are written in Claude Code frontmatter format
(`tools: Read, Bash, ...` as a comma-separated string). OpenCode
requires a YAML object (`tools:\n  read: true\n  bash: true`) with
lowercase keys and a `mode:` field. The install script transforms the
frontmatter at install time when the runtime is opencode.

This test exercises that transform and validates the output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _transform(repo_root: Path, agent_path: Path) -> str:
    """Run the transform script on agent_path; return transformed content."""
    script = repo_root / "scripts" / "transform-agent-frontmatter.py"
    if not script.exists():
        pytest.fail(f"Transform script not found at {script}")
    result = subprocess.run(
        [sys.executable, str(script), str(agent_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Transform failed for {agent_path.name}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


def test_transform_script_exists(repo_root: Path) -> None:
    """The transform script must exist and be executable."""
    script = repo_root / "scripts" / "transform-agent-frontmatter.py"
    assert script.exists(), f"Transform script missing at {script}"


def test_transform_all_agents_produces_opencode_format(repo_root: Path) -> None:
    """Every shipped agent must transform cleanly to OpenCode format."""
    agents_dir = repo_root / "agents"
    assert agents_dir.is_dir(), f"agents/ not found at {agents_dir}"
    md_files = sorted(agents_dir.glob("*.md"))
    assert md_files, "No agents found"

    for agent in md_files:
        transformed = _transform(repo_root, agent)
        # Must have frontmatter
        assert transformed.startswith("---\n"), f"{agent.name}: missing frontmatter"
        # mode: subagent must be present
        assert "mode: subagent" in transformed, (
            f"{agent.name}: missing 'mode: subagent' after transform"
        )
        # tools: must be an object, with lowercase keys
        if "tools:" in transformed:
            # Extract tools block
            lines = transformed.split("\n")
            tools_idx = next(
                (i for i, line in enumerate(lines) if line.startswith("tools:")),
                None,
            )
            assert tools_idx is not None
            # The line after "tools:" should be indented with "  key: true"
            next_line = lines[tools_idx + 1]
            assert next_line.startswith("  "), (
                f"{agent.name}: tools field is not an indented object after transform"
            )
            # No capital letters in tool keys
            tool_lines = []
            i = tools_idx + 1
            while i < len(lines) and lines[i].startswith("  "):
                tool_lines.append(lines[i])
                i += 1
            for tl in tool_lines:
                key = tl.strip().split(":")[0]
                assert key.islower(), (
                    f"{agent.name}: tool key '{key}' must be lowercase for OpenCode"
                )


def test_transform_preserves_body(repo_root: Path) -> None:
    """The body (system prompt) must be preserved unchanged."""
    sample = repo_root / "agents" / "polish-claims.md"
    if not sample.exists():
        pytest.skip("polish-claims.md not present")
    original = sample.read_text(encoding="utf-8")
    transformed = _transform(repo_root, sample)
    # Extract bodies (everything after the second `---\n`)
    def body(text: str) -> str:
        parts = text.split("---\n", 2)
        return parts[2] if len(parts) >= 3 else ""
    assert body(original) == body(transformed), (
        "Transform changed the body content; only frontmatter should change"
    )


def test_transform_drops_name_field(repo_root: Path) -> None:
    """OpenCode infers agent name from filename; the name field is dropped."""
    sample = repo_root / "agents" / "polish-claims.md"
    if not sample.exists():
        pytest.skip("polish-claims.md not present")
    transformed = _transform(repo_root, sample)
    # Extract frontmatter
    parts = transformed.split("---\n", 2)
    assert len(parts) >= 3
    fm = parts[1]
    # `name:` should not appear in transformed frontmatter
    assert not any(
        line.startswith("name:") for line in fm.split("\n")
    ), "Transform should drop the `name:` field (OpenCode uses filename)"


def test_transform_maps_websearch_to_webfetch(repo_root: Path) -> None:
    """WebSearch isn't universally available in OpenCode; map to WebFetch."""
    # Find an agent that uses WebSearch
    agents_dir = repo_root / "agents"
    candidates = []
    for agent in agents_dir.glob("*.md"):
        text = agent.read_text(encoding="utf-8")
        if "WebSearch" in text.split("---\n", 2)[1]:
            candidates.append(agent)
    if not candidates:
        pytest.skip("No agents use WebSearch")
    for agent in candidates:
        transformed = _transform(repo_root, agent)
        fm = transformed.split("---\n", 2)[1]
        assert "websearch:" not in fm.lower(), (
            f"{agent.name}: websearch should be mapped to webfetch for OpenCode"
        )
        assert "webfetch: true" in fm, (
            f"{agent.name}: webfetch should be present after mapping from websearch"
        )


def _transform_with_config(repo_root: Path, agent_path: Path, config_path: Path) -> str:
    """Run the transform script with --config; return transformed content."""
    script = repo_root / "scripts" / "transform-agent-frontmatter.py"
    result = subprocess.run(
        [sys.executable, str(script), "--config", str(config_path),
         str(agent_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Transform with --config failed for {agent_path.name}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


def test_tier_resolution_emits_model_field(repo_root: Path) -> None:
    """When --config maps the tier to a model, transform must emit `model:`.

    This is the load-bearing behavior: without it, OpenCode subagents
    inherit the session model and the tier system is decorative.
    """
    config_example = repo_root / "config" / "config.json.example"
    assert config_example.exists(), "config.json.example missing"

    # Pick one agent per tier and verify resolution.
    by_tier: dict[str, Path] = {}
    for agent in (repo_root / "agents").glob("*.md"):
        text = agent.read_text(encoding="utf-8")
        fm = text.split("---\n", 2)[1] if "---\n" in text else ""
        for line in fm.split("\n"):
            if line.startswith("model_tier:"):
                tier = line.split(":", 1)[1].strip()
                by_tier.setdefault(tier, agent)
                break

    for tier in ("light", "standard", "heavy"):
        if tier not in by_tier:
            continue
        transformed = _transform_with_config(repo_root, by_tier[tier], config_example)
        fm = transformed.split("---\n", 2)[1]
        assert "model:" in fm, (
            f"Agent {by_tier[tier].name} (tier={tier}): no `model:` field "
            f"after transform with config. Tier resolution is broken."
        )
        # Sanity: the model line should not be empty.
        model_line = next(
            (line for line in fm.split("\n") if line.startswith("model:")),
            None,
        )
        assert model_line and model_line != "model:" and model_line != "model: ", (
            f"Agent {by_tier[tier].name}: `model:` is empty after resolution."
        )


def test_tier_resolution_skipped_without_config(repo_root: Path) -> None:
    """Without --config, no `model:` is emitted — agent inherits session default."""
    agents_dir = repo_root / "agents"
    sample = next(agents_dir.glob("*.md"), None)
    if sample is None:
        pytest.skip("No agents to test")
    transformed = _transform(repo_root, sample)
    fm = transformed.split("---\n", 2)[1]
    # If the source agent declares an explicit model: field, that's allowed.
    # Otherwise no model: should appear in transform output.
    source_fm = sample.read_text(encoding="utf-8").split("---\n", 2)[1]
    source_has_model = any(
        line.startswith("model:") and not line.startswith("model_tier:")
        for line in source_fm.split("\n")
    )
    if not source_has_model:
        for line in fm.split("\n"):
            assert not (line.startswith("model:") and not line.startswith("model_tier:")), (
                f"Without --config, transform should not emit `model:` "
                f"(it would force a specific model on the subagent and defeat "
                f"the design that lets it inherit). Got: {line}"
            )


def test_config_example_has_provider_prefixed_models(repo_root: Path) -> None:
    """config.json.example must use provider-prefixed model strings.

    OpenCode requires provider/model format (e.g., 'anthropic/claude-opus-4-7')
    not bare model names. Bare names worked under Claude Code but break OpenCode.
    """
    import json
    config_path = repo_root / "config" / "config.json.example"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    tiers = data.get("model_tiers", {})
    for tier, model in tiers.items():
        if tier.startswith("_"):  # comment fields
            continue
        assert isinstance(model, str), (
            f"Tier {tier} in config.json.example is not a string"
        )
        assert "/" in model, (
            f"Tier {tier} in config.json.example uses bare model name '{model}'; "
            "OpenCode requires provider-prefixed format like 'anthropic/...'"
        )
