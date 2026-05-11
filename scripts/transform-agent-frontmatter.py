#!/usr/bin/env python3
"""Transform agent frontmatter from Claude Code format to OpenCode format.

Reads a markdown file with Claude-style YAML frontmatter on stdin (or as
argv[1] → argv[2]) and writes an OpenCode-compatible version.

Claude Code format (source):
    ---
    name: polish-claims
    description: "..."
    tools: Read, Bash, Glob, Grep, WebSearch, WebFetch, Write
    model_tier: standard
    ---

OpenCode format (target):
    ---
    description: "..."
    mode: subagent
    model: anthropic/claude-sonnet-4-6     # resolved from model_tier if config.json found
    tools:
      read: true
      bash: true
      glob: true
      grep: true
      webfetch: true
      write: true
    model_tier: standard
    ---

Key differences handled:
- `tools` becomes a YAML object with lowercase keys, not a comma-string.
- `mode: subagent` is added (OpenCode requires it for non-primary agents).
- `name` is dropped (OpenCode infers it from filename; redundant).
- `WebSearch` maps to a no-op since OpenCode's `websearch` is gated behind
  the OpenCode provider or OPENCODE_ENABLE_EXA env var — we emit `webfetch`
  instead (which the agent prompts use as a fallback anyway).
- `model_tier` is gsd-econ-specific. If a config.json is provided via
  --config and contains a `model_tiers` block mapping this tier to a
  model string, that string is emitted as `model:` so OpenCode actually
  routes the subagent to the right model. Without --config, no `model:`
  is emitted and the subagent inherits the session default.

Usage:
    python3 transform-agent-frontmatter.py <input.md> <output.md>
    python3 transform-agent-frontmatter.py --config <config.json> <input.md> <output.md>
    cat agent.md | python3 transform-agent-frontmatter.py - -
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Map Claude Code tool names → OpenCode tool names.
# OpenCode tool names are lowercase. WebSearch maps to webfetch because
# OpenCode's native websearch tool requires the OpenCode provider or an
# explicit env var; webfetch is universally available.
TOOL_NAME_MAP = {
    "read": "read",
    "write": "write",
    "edit": "edit",
    "bash": "bash",
    "glob": "glob",
    "grep": "grep",
    "webfetch": "webfetch",
    "websearch": "webfetch",   # see note above
    "task": "task",
    "todowrite": "todowrite",
    "todoread": "todoread",
    "notebookread": "read",    # OpenCode has no notebook-specific tool
    "notebookedit": "edit",
}


def load_model_tiers(config_path: Path | None) -> dict[str, str]:
    """Load model_tiers mapping from a gsd-econ config.json, if provided.

    Returns an empty dict if config_path is None, missing, or has no tiers.
    """
    if config_path is None or not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    tiers = data.get("model_tiers", {})
    if not isinstance(tiers, dict):
        return {}
    # Drop _comment and other non-tier keys.
    return {
        k: v for k, v in tiers.items()
        if not k.startswith("_") and isinstance(v, str)
    }


def transform_frontmatter(content: str, model_tiers: dict[str, str] | None = None) -> str:
    """Return content with frontmatter rewritten for OpenCode.

    If model_tiers is provided and the agent declares a model_tier present
    in the map, an explicit `model:` field is emitted so OpenCode routes
    the subagent to the right model rather than inheriting the session
    default.
    """
    model_tiers = model_tiers or {}
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        # No frontmatter — return unchanged.
        return content

    fm_text, body = match.group(1), match.group(2)
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []

    # Simple line-based parse — we don't need full YAML since the source
    # files use a flat key:value structure (sometimes with quoted values
    # that span the line but never multi-line).
    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        kv = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
        if kv:
            if current_key is not None:
                fields[current_key] = " ".join(current_value).strip()
            current_key = kv.group(1)
            current_value = [kv.group(2)]
        elif current_key is not None:
            # Continuation line (rare in our files)
            current_value.append(line.strip())
    if current_key is not None:
        fields[current_key] = " ".join(current_value).strip()

    # Transform tools field
    new_tools_lines: list[str] = []
    if "tools" in fields:
        tools_str = fields.pop("tools")
        # Split on commas, normalize each.
        raw_tools = [t.strip().lower() for t in tools_str.split(",") if t.strip()]
        # Map and dedupe, preserving order.
        seen: set[str] = set()
        mapped: list[str] = []
        for t in raw_tools:
            target = TOOL_NAME_MAP.get(t, t)
            if target not in seen:
                seen.add(target)
                mapped.append(target)
        if mapped:
            new_tools_lines.append("tools:")
            for t in mapped:
                new_tools_lines.append(f"  {t}: true")

    # Drop `name` — OpenCode infers from filename.
    fields.pop("name", None)

    # Resolve model from model_tier if a tier mapping was provided.
    # Don't overwrite an explicit `model:` field if the source already has one.
    tier = fields.get("model_tier", "").strip()
    has_explicit_model = "model" in fields and fields["model"].strip()
    resolved_model: str | None = None
    if tier and tier in model_tiers and not has_explicit_model:
        resolved_model = model_tiers[tier]

    # Compose new frontmatter.
    out: list[str] = ["---"]
    # description first (OpenCode requires it)
    if "description" in fields:
        out.append(f"description: {fields.pop('description')}")
    # mode (required by OpenCode for non-primary agents)
    out.append(f"mode: {fields.pop('mode', 'subagent')}")
    # model (resolved from tier or explicit)
    if has_explicit_model:
        out.append(f"model: {fields.pop('model')}")
    elif resolved_model is not None:
        out.append(f"model: {resolved_model}")
    # tools
    out.extend(new_tools_lines)
    # Any remaining fields (model_tier, temperature, etc.)
    for k, v in fields.items():
        out.append(f"{k}: {v}")
    out.append("---")

    return "\n".join(out) + "\n" + body


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a gsd-econ .planning/config.json; used to resolve model_tier → model.",
    )
    parser.add_argument("input", help="Input markdown file, or '-' for stdin.")
    parser.add_argument("output", help="Output markdown file, or '-' for stdout.")
    args = parser.parse_args(argv[1:])

    if args.input == "-":
        content = sys.stdin.read()
    else:
        content = Path(args.input).read_text(encoding="utf-8")

    model_tiers = load_model_tiers(args.config)
    out = transform_frontmatter(content, model_tiers)

    if args.output == "-":
        sys.stdout.write(out)
    else:
        Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
