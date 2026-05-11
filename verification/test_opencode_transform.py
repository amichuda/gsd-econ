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
