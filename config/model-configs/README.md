# Model configuration templates

Ready-to-use model configurations for gsd-econ. Pick one, copy it to your
project, edit if needed, and pass to install.sh via `--models-config`:

```bash
./install.sh --runtime opencode --models-config config/model-configs/openrouter-deepseek.yaml
```

Or interactively pick one (and customize) with:

```bash
./install.sh --runtime opencode --interactive-models
```

The interactive flag walks you through a menu that generates a config
file at `.planning/my-models.yaml`, then runs the install using it.

## Available templates

| File | Provider | Cost / eval | Best for |
|------|----------|-------------|----------|
| `anthropic-direct.yaml` | Anthropic API | ~$30-60 | Highest quality, real paper submission work |
| `openrouter-hybrid.yaml` | OpenRouter (DeepSeek light/standard, Claude Opus heavy) | ~$5-15 | Production work that still wants meaningful cost savings |
| `openrouter-deepseek.yaml` | OpenRouter (DeepSeek V4 all tiers) | ~$0.50-1.50 | Cost-conscious evaluation runs, high-volume agentic work |
| `ollama-local.yaml` | Local Ollama | $0 | Sensitive data, offline work, or running fully local |

Cost estimates are for a single full evaluation of a Breza-paper-size
project (roughly: bootstrap, identification discussion with --meta-cog,
plan-empirics with --meta-cog, polish-pass, referee-sim --heavy with
6 referees). Real costs depend on paper length, agent fan-out, and how
many iterations you do.

## Schema

```yaml
runtime: opencode                # "opencode" or "claude" or "both"

provider:
  name: openrouter               # "anthropic" | "openrouter" | "openai" | "ollama" | "custom"
  api_key_env: OPENROUTER_API_KEY
  # base_url: "..."              # required for "custom" and "ollama"
  # app_referer: "..."           # optional, OpenRouter-specific
  # app_title: "..."             # optional, OpenRouter-specific

tiers:
  light:    provider/model-string
  standard: provider/model-string
  heavy:    provider/model-string

session_default: provider/model-string

permissions:
  edit: ask                      # "ask" | "allow" | "deny"
  webfetch: allow
  bash:
    "<command-pattern>": ask|allow|deny
```

## Writing your own

Copy the closest template, edit the model strings and permissions to taste,
and save somewhere outside the gsd-econ source directory (e.g.,
`~/my-gsd-models.yaml`).

To find available model strings:

```bash
# After installing OpenCode:
opencode models list                                  # all configured providers
opencode models list anthropic                        # filter by provider
opencode models list openrouter                       # OpenRouter's full catalog
```

Or check the provider's website directly:
- OpenRouter: <https://openrouter.ai/models>
- Anthropic: <https://docs.claude.com/en/docs/about-claude/models>
- OpenAI: <https://platform.openai.com/docs/models>
- Ollama: <https://ollama.com/library>

## Updating after install

If you change your mind about which models to use:

1. Edit the YAML file you originally passed (or pick a different template).
2. Re-run `install.sh --wire-only --models-config <file>` from inside the
   project directory. This re-resolves agent files but **preserves** any
   other edits you've made to `.planning/config.json`.

The previous workflow (edit `.planning/config.json` directly, then re-run
wire-only) still works for ad-hoc tweaks, but using a separate models-config
file is cleaner because it's a single source of truth that can be
version-controlled and shared across projects.
