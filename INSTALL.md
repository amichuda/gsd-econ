# Installation

`gsd-econ` is an overlay. It does not replace GSD or RUT — it sits on top of both. There's one install script (`install.sh`) at the repo root that handles everything: full per-project setup, user-wide install, and incremental updates.

---

## Prerequisites

- An LLM coding runtime: OpenCode, Claude Code, or another GSD-supported runtime (or installable via the script).
- `git`, `bash`, `node` (for `npx`), `python3` (for path computation in the install script).
- Optional but recommended: `jq` for clean config merging.

---

## The three install modes

### `--project` (default): full per-project install

```bash
git clone https://github.com/<your-username>/gsd-econ ~/src/gsd-econ
cd ~/papers/my-paper && git init

bash ~/src/gsd-econ/install.sh
# or: bash ~/src/gsd-econ/install.sh --project [DIR]
```

Does the whole setup for one paper:
1. Checks prerequisites
2. Installs GSD core with `--minimal` (skip with `--skip-gsd` if already installed)
3. Adds research-unit-tests as a git submodule (skip with `--skip-rut`)
4. Copies gsd-econ into `vendor/gsd-econ/`
5. Symlinks gsd-econ commands into the runtime's per-project command directory (`.opencode/command/` or `.claude/commands/`)
6. Symlinks agents into the runtime's per-project agent directory
7. Wires `.planning/config.json` with `agent_skills`, `model_tiers`, and workflow defaults (using `jq` to merge if a config already exists)
8. Copies bootstrap templates into `.planning/`

After this, run `/gsd-new-paper` in your runtime to start a paper.

### `--global`: user-wide install

```bash
bash ~/src/gsd-econ/install.sh --global
```

Symlinks gsd-econ commands and agents into the runtime's user-level config directory:
- Claude Code: `~/.claude/commands/`, `~/.claude/agents/` (or `~/.claude/skills/` for newer versions)
- OpenCode: `~/.opencode/command/`, `~/.opencode/agent/`

After a global install, gsd-econ commands are available in every project. Per-project setup (`.planning/` scaffold, RUT submodule, GSD core) still runs per-project — re-run `install.sh --project --skip-gsd` once you've installed GSD globally yourself.

### `--wire-only`: re-link after `git pull`

```bash
cd vendor/gsd-econ && git pull && cd ../..
bash vendor/gsd-econ/install.sh --wire-only
```

Re-symlinks commands and agents (so newly added ones become available) and re-merges `config.json` (so new defaults like `model_tiers` propagate). Doesn't touch GSD core, doesn't touch RUT, doesn't touch your `.planning/` files.

This is the standard "update gsd-econ" path.

---

## Project vs global, side by side

| | `--project` (default) | `--global` |
|---|---|---|
| Where commands live | `.opencode/command/` or `.claude/commands/` in the project | `~/.opencode/command/` or `~/.claude/commands/` |
| Where agents live | Same, per-project | Same, user-wide |
| `.planning/` scaffold | Created automatically | No (you bootstrap per-project later) |
| GSD core install | Yes, in the project | No (you do this per-project, or globally yourself) |
| RUT submodule | Yes, in `vendor/research-unit-tests` | No |
| Updates | `install.sh --wire-only` per project, after `git pull` of the vendored copy | `git pull` in your gsd-econ checkout — symlinks pick up changes |
| Customization | Easy: each project owns its own copy | Per-user: edit the gsd-econ checkout |
| Best for | Single-paper users, coauthors who want a self-contained copy | Researchers running many papers |

**Picking between them:** for your first gsd-econ project, use `--project` — everything is self-contained, easy to inspect. Once you've used it on 2+ papers, switch to `--global` for one place to update from. You can always start project-mode and switch later.

---

## Useful flags

| Flag | Effect |
|------|--------|
| `--project [DIR]` | Mode: full per-project install in DIR (default: current dir) |
| `--global` | Mode: user-wide install of commands+agents |
| `--wire-only` | Mode: re-link only (implies `--skip-gsd --skip-rut`) |
| `--runtime claude\|opencode\|both` | Force which runtime(s) to target (default: auto-detect) |
| `--skip-gsd` | Don't install GSD core |
| `--skip-rut` | Don't add the RUT submodule |
| `--dry-run` | Print what would happen without executing |
| `--yes`, `-y` | Skip all confirmation prompts |
| `--help`, `-h` | Full flag list |

---

## After install

Your project (after `--project` mode) should look roughly like:

```
my-paper/
├── .opencode/                    # or .claude/
│   ├── command/
│   │   ├── gsd-new-project.md          # from GSD core
│   │   ├── gsd-new-paper.md            # → vendor/gsd-econ/commands/
│   │   ├── gsd-discuss-identification.md
│   │   ├── gsd-plan-empirics.md
│   │   ├── gsd-verify-replication.md
│   │   ├── gsd-tables-figures.md
│   │   ├── gsd-pre-register.md
│   │   ├── gsd-rr-response.md
│   │   ├── gsd-polish-pass.md
│   │   ├── gsd-submit-paper.md
│   │   ├── gsd-test-paper.md
│   │   └── gsd-referee-sim.md
│   └── agent/
│       ├── econ-researcher.md
│       ├── identification-checker.md
│       ├── econometrician.md
│       ├── replication-verifier.md
│       ├── tables-figures-builder.md
│       ├── referee-sim.md
│       ├── referee-sim-light.md
│       ├── referee-deliberator.md
│       └── polish-*.md (5 polish agents)
├── .planning/
│   ├── config.json
│   ├── PROJECT.md          (after /gsd-new-paper)
│   ├── REQUIREMENTS.md
│   ├── METHODOLOGY.md
│   ├── ROADMAP.md
│   └── STATE.md
├── vendor/
│   ├── gsd-econ/                   # this repo (copied or submoduled)
│   └── research-unit-tests/        # rdahis's repo
└── (your code, data, paper drafts)
```

Open the project in your runtime and run:

```
/gsd-help
```

You should see both core GSD commands and gsd-econ overlay commands. Then:

```
/gsd-new-paper
```

This is the entry point for both new papers (`--new` mode) and mid-project adoption (`--adopt` mode); it auto-detects which.

---

## Updating

```bash
# If gsd-econ is vendored as a submodule
cd vendor/gsd-econ && git pull && cd ../..
bash vendor/gsd-econ/install.sh --wire-only

# If gsd-econ is your local checkout (--global users)
cd ~/src/gsd-econ && git pull
# Symlinks at ~/.claude/ pick up changes automatically; no re-run needed.

# To update GSD core
npx get-shit-done-cc@latest --opencode --local --minimal   # always with --minimal

# To update RUT
cd vendor/research-unit-tests && git pull && cd ../..
```

---

## Uninstalling

```bash
# Project install
git submodule deinit vendor/gsd-econ vendor/research-unit-tests
git rm vendor/gsd-econ vendor/research-unit-tests
# Manually remove .opencode/command/gsd-* and .opencode/agent/* symlinks
# (or just rm the symlinks; the targets are gone anyway)

# Global install
rm ~/.claude/commands/gsd-*.md ~/.claude/agents/{econ-researcher,identification-checker,econometrician,replication-verifier,tables-figures-builder,referee-sim*,referee-deliberator,polish-*}.md
# adjust path for opencode if applicable
```

Your `.planning/` directory and any work you've committed are untouched.

---

## Troubleshooting

**Commands not appearing after install.**
Restart the runtime. Some runtimes only enumerate command directories at startup.

**`agent_skills` not picked up.**
Verify `.planning/config.json` has the right paths. The install script writes them with `./vendor/...` — these resolve relative to the project root, which is GSD's working directory.

**RUT submodule empty.**
You probably cloned without `--recurse-submodules`. Run `git submodule update --init --recursive`.

**Paths don't resolve in containers.**
GSD has a known issue with `~` expansion in Docker. Set `CLAUDE_CONFIG_DIR=/abs/path/.claude` before running anything.

**`jq` not found, config didn't merge.**
Install jq (`brew install jq` or `sudo apt-get install jq`), then `install.sh --wire-only` to retry the merge. Or merge manually using `config/config.json.example` as the reference.
