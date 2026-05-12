#!/usr/bin/env python3
"""Interactive picker for gsd-econ model configuration.

Walks the user through a series of prompts to generate a models-config YAML.
Writes it to <output-path> (default: .planning/my-models.yaml). Caller is
expected to then pass that YAML to apply-models-config.py.

Usage:
    python3 scripts/pick-models-interactive.py [output-path]

If stdin isn't a TTY (e.g., running under CI), exits cleanly with a message
pointing at config/model-configs/ for non-interactive options.
"""
from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "config" / "model-configs"


# Curated list of common model strings, with rough pricing as of May 2026.
# These are starting points, not an exhaustive catalog. Users can pick
# "(custom)" to type their own.
PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "label": "Anthropic API (direct)",
        "api_key_env": "ANTHROPIC_API_KEY",
        "key_signup": "https://console.anthropic.com",
        "models": [
            ("anthropic/claude-haiku-4-5", "Claude Haiku 4.5", "$1 in / $5 out", "fast, cheap"),
            ("anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6", "$3 in / $15 out", "balanced"),
            ("anthropic/claude-opus-4-7", "Claude Opus 4.7", "$15 in / $75 out", "highest quality"),
        ],
        "recommended": {
            "light": "anthropic/claude-haiku-4-5",
            "standard": "anthropic/claude-sonnet-4-6",
            "heavy": "anthropic/claude-opus-4-7",
        },
    },
    "openrouter": {
        "label": "OpenRouter (routes to ~180 models from one API key)",
        "api_key_env": "OPENROUTER_API_KEY",
        "key_signup": "https://openrouter.ai/keys",
        "models": [
            ("openrouter/deepseek/deepseek-v4-flash", "DeepSeek V4 Flash", "$0.14 in / $0.28 out", "cheap, 1M context"),
            ("openrouter/deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", "$0.44 in / $0.87 out", "near-frontier coding"),
            ("openrouter/qwen/qwen3.6-plus", "Qwen 3.6 Plus", "$0.50 in / $2.00 out", "1M context, reasoning"),
            ("openrouter/anthropic/claude-haiku-4-5", "Claude Haiku 4.5 (via OR)", "$1 in / $5 out", "Anthropic via OR"),
            ("openrouter/anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6 (via OR)", "$3 in / $15 out", ""),
            ("openrouter/anthropic/claude-opus-4-7", "Claude Opus 4.7 (via OR)", "$15 in / $75 out", ""),
        ],
        "recommended": {
            "light": "openrouter/deepseek/deepseek-v4-flash",
            "standard": "openrouter/deepseek/deepseek-v4-flash",
            "heavy": "openrouter/deepseek/deepseek-v4-pro",
        },
    },
    "openai": {
        "label": "OpenAI API",
        "api_key_env": "OPENAI_API_KEY",
        "key_signup": "https://platform.openai.com/api-keys",
        "models": [
            ("openai/gpt-5.1", "GPT-5.1", "$2.50 in / $10 out", "general purpose"),
            ("openai/gpt-5.1-codex", "GPT-5.1 Codex", "$3 in / $12 out", "coding-tuned"),
            ("openai/gpt-5.1-mini", "GPT-5.1 Mini", "$0.25 in / $1.00 out", "cheap"),
        ],
        "recommended": {
            "light": "openai/gpt-5.1-mini",
            "standard": "openai/gpt-5.1",
            "heavy": "openai/gpt-5.1-codex",
        },
    },
    "ollama": {
        "label": "Local via Ollama (no API costs, requires hardware)",
        "api_key_env": None,
        "key_signup": "https://ollama.com/download",
        "models": [
            ("ollama/qwen3.6:30b", "Qwen 3.6 30B", "local", "needs ~24GB"),
            ("ollama/deepseek-r1:32b", "DeepSeek R1 32B", "local", "reasoning, needs ~24GB"),
            ("ollama/gemma3:27b", "Gemma 3 27B", "local", "needs ~20GB"),
            ("ollama/qwen3.6:14b", "Qwen 3.6 14B", "local", "fits in 16GB"),
        ],
        "recommended": {
            "light": "ollama/qwen3.6:14b",
            "standard": "ollama/qwen3.6:30b",
            "heavy": "ollama/deepseek-r1:32b",
        },
    },
}


def ask_choice(prompt: str, options: list[tuple[str, str]], default_idx: int | None = None) -> str:
    """Display a numbered menu and return the user's selected key.

    options is a list of (key, label) tuples.
    """
    print(f"\n{prompt}")
    for i, (_, label) in enumerate(options, 1):
        marker = " (default)" if default_idx is not None and i == default_idx + 1 else ""
        print(f"  {i}. {label}{marker}")
    while True:
        default_str = f" [{default_idx + 1}]" if default_idx is not None else ""
        try:
            raw = input(f"Choice{default_str}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)
        if not raw and default_idx is not None:
            return options[default_idx][0]
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        print(f"  Please enter a number 1-{len(options)}.")


def ask_model_for_tier(provider_key: str, tier: str, default: str) -> str:
    """Ask the user which model to use for a given tier."""
    provider = PROVIDERS[provider_key]
    models = provider["models"]

    print(f"\n--- {tier.upper()} tier model ---")
    tier_hint = {
        "light": "high-volume parallel work (polish-pass, referee fan-out). Optimize for cost.",
        "standard": "default orchestration work. Balance cost and quality.",
        "heavy": "discriminating reasoning (identification, deliberation). Optimize for quality.",
    }[tier]
    print(f"({tier_hint})")

    options = [(m[0], f"{m[1]:<35} {m[2]:<25} {m[3]}") for m in models]
    options.append(("__custom__", "(enter a custom model string)"))

    default_idx = next(
        (i for i, (k, _) in enumerate(options) if k == default),
        0,
    )
    choice = ask_choice(f"Model for {tier} tier:", options, default_idx=default_idx)

    if choice == "__custom__":
        try:
            return input(f"  Enter model string (e.g., {provider_key}/some-model): ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
    return choice


def write_yaml(path: Path, runtime: str, provider_key: str, tiers: dict, session_default: str) -> None:
    """Write the YAML out by string concatenation (avoiding the PyYAML dependency
    here, since this script may run before deps are installed)."""
    provider = PROVIDERS[provider_key]
    lines = [
        "# Generated by pick-models-interactive.py",
        f"# Edit this file and re-run install.sh --wire-only --models-config <path>",
        f"# to change model choices later.",
        "",
        f"runtime: {runtime}",
        "",
        "provider:",
        f"  name: {provider_key}",
    ]
    if provider.get("api_key_env"):
        lines.append(f"  api_key_env: {provider['api_key_env']}")
    if provider_key == "ollama":
        lines.append('  base_url: "http://localhost:11434/v1"')
    if provider_key == "openrouter":
        lines.append('  app_referer: "https://github.com/amichuda/gsd-econ"')
        lines.append('  app_title: "gsd-econ"')
    lines.extend([
        "",
        "tiers:",
        f"  light:    {tiers['light']}",
        f"  standard: {tiers['standard']}",
        f"  heavy:    {tiers['heavy']}",
        "",
        f"session_default: {session_default}",
        "",
        "permissions:",
        "  edit: ask",
        "  webfetch: allow",
        "  bash:",
        '    "git *": allow',
        '    "make *": allow',
        '    "uv *": allow',
        '    "ls *": allow',
        '    "cat *": allow',
        '    "rg *": allow',
        '    "grep *": allow',
        '    "find *": allow',
        '    "python3 *": allow',
        '    "Rscript *": allow',
        '    "stata -b *": allow',
        '    "rm -rf *": deny',
        '    "sudo *": deny',
        '    "*": ask',
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    output_path = Path(argv[1]) if len(argv) >= 2 else Path(".planning/my-models.yaml")

    if not sys.stdin.isatty():
        print(
            "Interactive picker requires a TTY. For non-interactive installs, use\n"
            "one of the ready-made templates:\n"
            f"  {TEMPLATES_DIR}/anthropic-direct.yaml\n"
            f"  {TEMPLATES_DIR}/openrouter-hybrid.yaml\n"
            f"  {TEMPLATES_DIR}/openrouter-deepseek.yaml\n"
            f"  {TEMPLATES_DIR}/ollama-local.yaml\n"
            "Pass the path via --models-config <file>.",
            file=sys.stderr,
        )
        return 2

    print("=" * 60)
    print("gsd-econ model configuration")
    print("=" * 60)
    print()
    print("This walks you through picking models for each agent tier.")
    print("Your choices are written to a YAML file you can edit later.")
    print()

    # Step 1: runtime
    runtime = ask_choice(
        "Which runtime are you using?",
        [
            ("opencode", "OpenCode"),
            ("claude", "Claude Code"),
            ("both", "Both (apply to both runtimes)"),
        ],
        default_idx=0,
    )

    # Step 2: provider
    provider_key = ask_choice(
        "Which model provider?",
        [(k, v["label"]) for k, v in PROVIDERS.items()],
        default_idx=1,  # default to openrouter
    )

    # Step 3: tiers
    rec = PROVIDERS[provider_key]["recommended"]
    print()
    print(f"Suggested defaults for {PROVIDERS[provider_key]['label']}:")
    print(f"  light    → {rec['light']}")
    print(f"  standard → {rec['standard']}")
    print(f"  heavy    → {rec['heavy']}")
    print()
    accept = ask_choice(
        "Use these defaults, or pick each tier manually?",
        [("defaults", "Use the suggested defaults"), ("manual", "Pick each tier manually")],
        default_idx=0,
    )

    if accept == "defaults":
        tiers = dict(rec)
    else:
        tiers = {
            "light": ask_model_for_tier(provider_key, "light", rec["light"]),
            "standard": ask_model_for_tier(provider_key, "standard", rec["standard"]),
            "heavy": ask_model_for_tier(provider_key, "heavy", rec["heavy"]),
        }

    # Step 4: session default
    print()
    session_default = ask_choice(
        "Session-default model (the orchestrator that invokes subagents):",
        [
            (tiers["light"], f"Same as light ({tiers['light']})"),
            (tiers["standard"], f"Same as standard ({tiers['standard']})"),
            (tiers["heavy"], f"Same as heavy ({tiers['heavy']})"),
        ],
        default_idx=2,  # heavy is the most defensible default
    )

    # Step 5: API key reminder
    api_key_env = PROVIDERS[provider_key].get("api_key_env")
    if api_key_env:
        signup_url = PROVIDERS[provider_key].get("key_signup", "")
        print()
        print("=" * 60)
        print(f"API key setup")
        print("=" * 60)
        print(f"You will need an API key in environment variable {api_key_env}.")
        if signup_url:
            print(f"Get one at: {signup_url}")
        print(f"Then add to your shell startup (~/.zshrc or ~/.bashrc):")
        print(f"  export {api_key_env}=...")
        print()

    # Write file.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(output_path, runtime, provider_key, tiers, session_default)

    print(f"\n✓ Wrote {output_path}")
    print()
    print("Next steps:")
    print(f"  1. (If you haven't already) set {api_key_env or '(no key needed for Ollama)'}")
    print(f"  2. Re-run install.sh to apply:")
    print(f"     ./install.sh --runtime {runtime} --models-config {output_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
