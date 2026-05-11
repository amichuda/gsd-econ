#!/usr/bin/env bash
#
# gsd-econ install
#
# One script for everything. Choose:
#
#   bash install.sh --project [DIR]   # full per-project setup (default)
#   bash install.sh --global          # user-wide commands+agents
#   bash install.sh --wire-only       # only re-link/re-wire (after git pull)
#
# Run with --help for the full flag list.

set -euo pipefail

# -----------------------------------------------------------------------------
# Defaults / arg parsing
# -----------------------------------------------------------------------------

MODE=""              # project | global | wire-only
PROJECT_DIR=""
RUNTIME=""           # opencode | claude | both | (empty = auto)
SKIP_GSD=0
SKIP_RUT=0
DRY_RUN=0
ASSUME_YES=0

usage() {
    cat <<'EOF'
gsd-econ install

Usage:
  bash install.sh [--project [DIR] | --global | --wire-only] [options]

Modes:
  --project [DIR]      Full per-project install (default).
                       Sets up GSD core (--minimal), RUT submodule, and gsd-econ
                       overlay in DIR (default: current directory). The whole
                       workflow you need before opening the project in your
                       runtime.
  --global             User-wide install of commands and agents into
                       ~/.claude/ and/or ~/.opencode/. Per-project files
                       (.planning/, RUT submodule) are still bootstrapped
                       per-project; this just makes the overlay available
                       across projects.
  --wire-only          Re-link commands and agents and re-wire .planning/config
                       for an existing project. Use this after `git pull` in
                       a vendored gsd-econ. Implies --skip-gsd --skip-rut.

Options:
  --runtime RUNTIME    Force runtime: opencode, claude, or both.
                       Default: auto-detect (use what's installed).
  --skip-gsd           Skip GSD core install (assume already installed).
  --skip-rut           Skip RUT submodule (assume already added).
  --dry-run            Print what would be done; don't execute.
  --yes, -y            Skip confirmation prompts.
  -h, --help           Show this message.

Examples:

  # New project, all from scratch
  cd ~/papers/my-paper && git init
  bash /path/to/gsd-econ/install.sh

  # User-wide install for use across many papers
  bash /path/to/gsd-econ/install.sh --global

  # Update after `cd vendor/gsd-econ && git pull`
  bash vendor/gsd-econ/install.sh --wire-only

  # Already have GSD installed, just add the overlay
  bash install.sh --skip-gsd

EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            MODE="project"
            shift
            if [[ $# -gt 0 && "$1" != --* ]]; then
                PROJECT_DIR="$1"
                shift
            fi
            ;;
        --global)
            MODE="global"
            shift
            ;;
        --wire-only)
            MODE="wire-only"
            SKIP_GSD=1
            SKIP_RUT=1
            shift
            ;;
        --runtime)
            RUNTIME="$2"
            shift 2
            ;;
        --skip-gsd)
            SKIP_GSD=1
            shift
            ;;
        --skip-rut)
            SKIP_RUT=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --yes|-y)
            ASSUME_YES=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

# Default to project mode
if [[ -z "$MODE" ]]; then
    MODE="project"
fi

if [[ "$MODE" == "project" || "$MODE" == "wire-only" ]] && [[ -z "$PROJECT_DIR" ]]; then
    PROJECT_DIR="$(pwd)"
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# Where this script lives — used to find the gsd-econ source files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GSD_ECON_SRC="$SCRIPT_DIR"

run() {
    if [[ "$DRY_RUN" == 1 ]]; then
        echo "[dry-run] $*"
    else
        eval "$*"
    fi
}

confirm() {
    local prompt="$1"
    if [[ "$ASSUME_YES" == 1 ]]; then
        return 0
    fi
    read -r -p "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

log() {
    echo "→ $*"
}

warn() {
    echo "⚠ $*" >&2
}

err() {
    echo "✗ $*" >&2
    exit 1
}

# Compute relative path from $1 to $2, portably (realpath --relative-to is GNU-only)
rel_path() {
    local from="$1"
    local to="$2"
    python3 -c "import os; print(os.path.relpath('$to', '$from'))"
}

# -----------------------------------------------------------------------------
# Prereq checks
# -----------------------------------------------------------------------------

check_prereqs() {
    log "Checking prerequisites..."
    local missing=()

    command -v git >/dev/null 2>&1 || missing+=("git")
    command -v bash >/dev/null 2>&1 || missing+=("bash")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")

    # node/npx only needed if we're installing GSD core
    if [[ "$SKIP_GSD" == 0 && "$MODE" == "project" ]]; then
        command -v node >/dev/null 2>&1 || missing+=("node")
        command -v npx >/dev/null 2>&1 || missing+=("npx")
    fi

    if ! command -v jq >/dev/null 2>&1; then
        warn "jq not found — config merging will be manual. Install jq for cleaner installs."
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        err "Missing required commands: ${missing[*]}
  Install them and retry. On macOS:  brew install ${missing[*]}
  On Ubuntu/Debian:                   sudo apt-get install ${missing[*]}"
    fi

    log "Prerequisites OK."
}

# -----------------------------------------------------------------------------
# Runtime detection
# -----------------------------------------------------------------------------

detect_runtimes_global() {
    local found=()
    [[ -d "$HOME/.claude" ]] && found+=("claude")
    [[ -d "$HOME/.opencode" ]] && found+=("opencode")
    echo "${found[*]}"
}

detect_runtimes_project() {
    local target="$1"
    local found=()
    [[ -d "$target/.claude" ]] && found+=("claude")
    [[ -d "$target/.opencode" ]] && found+=("opencode")
    echo "${found[*]}"
}

resolve_runtimes() {
    local detected="$1"
    if [[ -n "$RUNTIME" ]]; then
        if [[ "$RUNTIME" == "both" ]]; then
            echo "claude opencode"
        else
            echo "$RUNTIME"
        fi
    elif [[ -n "$detected" ]]; then
        echo "$detected"
    else
        echo "claude"   # safe default
    fi
}

# Resolve command and agent dirs for a given runtime in either project or global mode
resolve_dirs() {
    local rt="$1"
    local scope="$2"   # project | global
    local base
    if [[ "$scope" == "global" ]]; then
        base="$HOME"
    else
        base="$PROJECT_DIR"
    fi
    case "$rt" in
        claude)
            CMD_DIR="$base/.claude/commands"
            # Newer Claude Code uses .claude/skills/
            if [[ -d "$base/.claude/skills" ]]; then
                CMD_DIR="$base/.claude/skills"
            fi
            AGENT_DIR="$base/.claude/agents"
            ;;
        opencode)
            CMD_DIR="$base/.opencode/command"
            AGENT_DIR="$base/.opencode/agent"
            ;;
        *)
            err "Unknown runtime: $rt"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# Symlinking — used by both modes
# -----------------------------------------------------------------------------

# Symlink every .md in $1 into $2, refusing to clobber non-symlinks
symlink_dir_contents() {
    local src_dir="$1"
    local dst_dir="$2"
    run "mkdir -p '$dst_dir'"
    for f in "$src_dir"/*.md; do
        [[ -f "$f" ]] || continue
        local name target
        name=$(basename "$f")
        target="$dst_dir/$name"
        if [[ -e "$target" && ! -L "$target" ]]; then
            warn "$target exists and is not a symlink — leaving alone."
            continue
        fi
        if [[ "$DRY_RUN" == 1 ]]; then
            echo "[dry-run] ln -sf '$f' '$target'"
        else
            ln -sf "$f" "$target"
            echo "  ✓ $name"
        fi
    done
}

# Place agent files for a specific runtime.
# For "claude": symlinks (frontmatter is Claude Code format natively).
# For "opencode": copies with frontmatter transformed via the python helper,
#                 since OpenCode requires a different YAML schema for tools.
#                 Also resolves model_tier -> model from .planning/config.json
#                 if available (so subagents actually route to their tier's
#                 model rather than inheriting the session default).
# Args: $1 = src_dir, $2 = dst_dir, $3 = runtime (claude|opencode)
place_agents() {
    local src_dir="$1"
    local dst_dir="$2"
    local runtime="$3"

    if [[ "$runtime" == "claude" ]]; then
        symlink_dir_contents "$src_dir" "$dst_dir"
        return 0
    fi

    # OpenCode path: copy with frontmatter transform.
    local transform_script="$GSD_ECON_SRC/scripts/transform-agent-frontmatter.py"
    if [[ ! -f "$transform_script" ]]; then
        err "OpenCode frontmatter transform script not found at $transform_script"
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        err "python3 is required to install agents for OpenCode (frontmatter transform)."
    fi

    # If a .planning/config.json exists in the project, pass it to the transform
    # so model_tier resolves to an explicit `model:` field. Without this, every
    # subagent inherits the session default model — the tier system is dead.
    local config_arg=""
    if [[ -n "${PROJECT_DIR:-}" && -f "$PROJECT_DIR/.planning/config.json" ]]; then
        config_arg="--config $PROJECT_DIR/.planning/config.json"
        log "  Using $PROJECT_DIR/.planning/config.json for tier→model resolution."
    elif [[ -f "$GSD_ECON_SRC/config/config.json.example" ]]; then
        # Global mode (no project) — fall back to the example config so the
        # default tier mapping (claude-haiku-4-5 / sonnet-4-6 / opus-4-7) is
        # present. Users override per-project later by running install.sh
        # --wire-only inside the project.
        config_arg="--config $GSD_ECON_SRC/config/config.json.example"
        log "  Global mode — using config.json.example for default tier→model resolution."
        log "  Override per-project by editing .planning/config.json then running install.sh --wire-only."
    else
        warn "  No config.json found; agents will inherit the session model."
        warn "  After creating/editing .planning/config.json, re-run with --wire-only."
    fi

    run "mkdir -p '$dst_dir'"
    for f in "$src_dir"/*.md; do
        [[ -f "$f" ]] || continue
        local name target
        name=$(basename "$f")
        target="$dst_dir/$name"
        # Refuse to clobber non-transformed files (heuristic: skip if file
        # exists and is not one we previously wrote).
        if [[ -e "$target" && ! -L "$target" ]]; then
            # Check if it looks like a previously-transformed file
            if ! head -10 "$target" 2>/dev/null | grep -q "mode: subagent"; then
                warn "$target exists and doesn't look like a transformed agent — leaving alone."
                continue
            fi
        fi
        # If it's a symlink (left over from a prior claude install), remove it.
        [[ -L "$target" ]] && rm -f "$target"
        if [[ "$DRY_RUN" == 1 ]]; then
            echo "[dry-run] python3 '$transform_script' $config_arg '$f' '$target'"
        else
            # shellcheck disable=SC2086  # we want $config_arg word-split
            python3 "$transform_script" $config_arg "$f" "$target" || \
                err "Failed to transform agent $name for OpenCode"
            echo "  ✓ $name (frontmatter transformed for OpenCode)"
        fi
    done
}

# -----------------------------------------------------------------------------
# Config wiring (project only)
# -----------------------------------------------------------------------------

wire_config() {
    local planning_dir="$PROJECT_DIR/.planning"
    local config_file="$planning_dir/config.json"
    run "mkdir -p '$planning_dir'"
    log "Configuring $config_file"
    if [[ ! -f "$config_file" ]]; then
        if [[ "$DRY_RUN" == 1 ]]; then
            echo "[dry-run] cp '$GSD_ECON_SRC/config/config.json.example' '$config_file'"
        else
            cp "$GSD_ECON_SRC/config/config.json.example" "$config_file"
            echo "  ✓ Created $config_file"
        fi
    elif command -v jq >/dev/null 2>&1; then
        if [[ "$DRY_RUN" == 1 ]]; then
            echo "[dry-run] jq merge $config_file with example"
        else
            local tmp
            tmp=$(mktemp)
            jq -s '.[0] * .[1]' "$config_file" "$GSD_ECON_SRC/config/config.json.example" > "$tmp"
            mv "$tmp" "$config_file"
            echo "  ✓ Merged via jq"
        fi
    else
        warn "jq not found; cannot auto-merge config."
        warn "Manually merge agent_skills, test_registries, model_tiers, workflow"
        warn "from $GSD_ECON_SRC/config/config.json.example into $config_file"
    fi
}

copy_templates() {
    local planning_dir="$PROJECT_DIR/.planning"
    log "Copying templates into $planning_dir/ (only if absent)"
    run "mkdir -p '$planning_dir' '$planning_dir/templates'"

    local templates=(
        "PROJECT.md.template:PROJECT.md"
        "REQUIREMENTS.md.template:REQUIREMENTS.md"
        "METHODOLOGY.md.template:METHODOLOGY.md"
        "ROADMAP.md.template:ROADMAP.md"
        "STATE.md.template:STATE.md"
    )
    for pair in "${templates[@]}"; do
        local src="${pair%%:*}"
        local dst="${pair##*:}"
        local target="$planning_dir/$dst"
        if [[ ! -f "$target" ]]; then
            if [[ "$DRY_RUN" == 1 ]]; then
                echo "[dry-run] cp '$GSD_ECON_SRC/templates/$src' '$target'"
            else
                cp "$GSD_ECON_SRC/templates/$src" "$target"
                echo "  ✓ $dst"
            fi
        else
            echo "  ⚠ $dst already exists — preserved"
        fi
    done

    # Phase context template stays in templates/ (per-phase copy by discuss command)
    if [[ ! -f "$planning_dir/templates/PHASE-CONTEXT.md.template" ]]; then
        run "cp '$GSD_ECON_SRC/templates/PHASE-CONTEXT.md.template' '$planning_dir/templates/'"
    fi
}

copy_rules() {
    log "Copying AGENTS.md and rules/ into project root (preserves existing)"

    # Top-level AGENTS.md
    local target="$PROJECT_DIR/AGENTS.md"
    if [[ ! -f "$target" ]]; then
        if [[ "$DRY_RUN" == 1 ]]; then
            echo "[dry-run] cp '$GSD_ECON_SRC/AGENTS.md' '$target'"
        else
            cp "$GSD_ECON_SRC/AGENTS.md" "$target"
            echo "  ✓ AGENTS.md"
        fi
    else
        echo "  ⚠ AGENTS.md already exists at project root — preserved"
        echo "    To pull in gsd-econ rules, append the lazy-load table from:"
        echo "    $GSD_ECON_SRC/AGENTS.md"
    fi

    # rules/ folder
    local rules_dst="$PROJECT_DIR/rules"
    if [[ ! -d "$rules_dst" ]]; then
        run "mkdir -p '$rules_dst'"
        for rule_file in "$GSD_ECON_SRC"/rules/*.md; do
            [[ -f "$rule_file" ]] || continue
            local name
            name=$(basename "$rule_file")
            local rule_target="$rules_dst/$name"
            if [[ "$DRY_RUN" == 1 ]]; then
                echo "[dry-run] cp '$rule_file' '$rule_target'"
            else
                cp "$rule_file" "$rule_target"
                echo "  ✓ rules/$name"
            fi
        done
    else
        log "rules/ folder already exists at project root — copying only missing files"
        for rule_file in "$GSD_ECON_SRC"/rules/*.md; do
            [[ -f "$rule_file" ]] || continue
            local name
            name=$(basename "$rule_file")
            local rule_target="$rules_dst/$name"
            if [[ ! -f "$rule_target" ]]; then
                if [[ "$DRY_RUN" == 1 ]]; then
                    echo "[dry-run] cp '$rule_file' '$rule_target'"
                else
                    cp "$rule_file" "$rule_target"
                    echo "  ✓ rules/$name (added)"
                fi
            fi
        done
    fi
}

# -----------------------------------------------------------------------------
# Mode: project (full from-scratch install)
# -----------------------------------------------------------------------------

do_project_install() {
    log "Project-level install into: $PROJECT_DIR"
    run "mkdir -p '$PROJECT_DIR'"
    cd "$PROJECT_DIR" 2>/dev/null || err "Cannot enter $PROJECT_DIR"

    # Step 0 — git init if needed (skip in wire-only mode; assume the repo's set up)
    if [[ "$MODE" != "wire-only" && ! -d ".git" ]]; then
        if confirm "Project is not a git repo. Initialize one?"; then
            run "git init -q"
        else
            err "Aborting: gsd-econ requires a git repo (submodules need it)."
        fi
    fi

    # Step 1 — install GSD core
    if [[ "$SKIP_GSD" == 0 ]]; then
        local rt
        rt="$(resolve_runtimes "$(detect_runtimes_project "$PROJECT_DIR")")"
        log "Installing GSD core (--minimal) for runtime(s): $rt"
        for r in $rt; do
            local flag
            case "$r" in
                claude)   flag="--claude" ;;
                opencode) flag="--opencode" ;;
                *) warn "Unknown runtime: $r — skipping"; continue ;;
            esac
            run "npx -y get-shit-done-cc@latest $flag --local --minimal"
        done
    else
        log "Skipping GSD core install (--skip-gsd)."
    fi

    # Step 2 — vendor gsd-econ if not already present
    if [[ ! -d "vendor/gsd-econ" ]]; then
        log "Adding gsd-econ to vendor/..."
        run "mkdir -p vendor"
        if [[ -f "$GSD_ECON_SRC/install.sh" && -f "$GSD_ECON_SRC/tests/registry.yaml" ]]; then
            log "Copying gsd-econ from $GSD_ECON_SRC..."
            run "cp -r '$GSD_ECON_SRC' 'vendor/gsd-econ'"
            run "rm -rf 'vendor/gsd-econ/.git'"
        else
            err "Cannot find gsd-econ source files.
  Run from a gsd-econ checkout: bash /path/to/gsd-econ/install.sh
  Or add as submodule manually: git submodule add <gsd-econ-url> vendor/gsd-econ"
        fi
    else
        log "vendor/gsd-econ already present — skipping vendor copy."
    fi

    # Step 3 — RUT submodule
    if [[ "$SKIP_RUT" == 0 && ! -d "vendor/research-unit-tests" ]]; then
        log "Adding research-unit-tests submodule..."
        run "git submodule add -q https://github.com/rdahis/research-unit-tests vendor/research-unit-tests"
        run "git submodule update --init --recursive"
    elif [[ -d "vendor/research-unit-tests" ]]; then
        log "vendor/research-unit-tests already present — skipping."
    else
        log "Skipping RUT submodule (--skip-rut)."
    fi

    # Step 4 — wire config first so place_agents can read model_tiers
    # (OpenCode subagents need an explicit `model:` from config.json's tier
    # mapping; otherwise they inherit the session default and tiering is dead).
    wire_config
    copy_templates
    copy_rules

    # Step 5 — wire commands and agents
    local rt
    rt="$(resolve_runtimes "$(detect_runtimes_project "$PROJECT_DIR")")"
    for r in $rt; do
        resolve_dirs "$r" "project"
        log "Linking commands into $CMD_DIR/"
        symlink_dir_contents "$GSD_ECON_SRC/commands" "$CMD_DIR"
        log "Linking agents into $AGENT_DIR/"
        place_agents "$GSD_ECON_SRC/agents" "$AGENT_DIR" "$r"
    done

    # Step 6 — final message
    cat <<EOF

✓ gsd-econ project install complete.

Next steps:
  1. Open $PROJECT_DIR in your runtime (claude, opencode).
  2. Run /gsd-help — confirm gsd-econ commands appear.
  3. Run /gsd-new-paper to bootstrap a new paper, or /gsd-new-paper --adopt
     if this directory already contains an in-progress manuscript.

Updates: re-run with bash install.sh --wire-only (after git pull).

Tip: edit .planning/config.json to choose which models map to the light /
standard / heavy tiers (see docs/model-tiers.md).
EOF
}

# -----------------------------------------------------------------------------
# Mode: global (user-wide commands+agents)
# -----------------------------------------------------------------------------

do_global_install() {
    log "Global install"
    log "Source: $GSD_ECON_SRC"

    if [[ ! -f "$GSD_ECON_SRC/tests/registry.yaml" ]]; then
        err "This script must be run from a gsd-econ checkout for global mode.
  Clone gsd-econ first, then run: bash /path/to/gsd-econ/install.sh --global"
    fi

    local rt
    rt="$(resolve_runtimes "$(detect_runtimes_global)")"
    log "Target runtime(s): $rt"

    for r in $rt; do
        resolve_dirs "$r" "global"
        log "Linking commands into $CMD_DIR/"
        symlink_dir_contents "$GSD_ECON_SRC/commands" "$CMD_DIR"
        log "Linking agents into $AGENT_DIR/"
        place_agents "$GSD_ECON_SRC/agents" "$AGENT_DIR" "$r"
    done

    cat <<EOF

✓ gsd-econ global install complete.

Commands and agents are now available in every project for the runtime(s) you
installed. Each project still needs:
  - GSD core: npx get-shit-done-cc@latest --<runtime> --local --minimal
  - research-unit-tests submodule
  - .planning/ scaffold

To bootstrap a project on top of the global install, from inside the project:
  bash $GSD_ECON_SRC/install.sh                 # full project setup
  bash $GSD_ECON_SRC/install.sh --skip-gsd      # if GSD already installed

Updates: cd $GSD_ECON_SRC && git pull. Symlinks pick up automatically.

Tip: edit ~/.claude/config.json (or your runtime's user-level config) for
global model_tiers defaults; per-project .planning/config.json overrides.
EOF
}

# -----------------------------------------------------------------------------
# Mode: wire-only (re-link after git pull)
# -----------------------------------------------------------------------------

do_wire_only() {
    log "Wire-only re-install (no GSD/RUT changes)"
    log "Project: $PROJECT_DIR"

    cd "$PROJECT_DIR" 2>/dev/null || err "Cannot enter $PROJECT_DIR"

    if [[ ! -d "vendor/gsd-econ" && ! -f "$GSD_ECON_SRC/tests/registry.yaml" ]]; then
        err "No gsd-econ source available.
  Either run from a gsd-econ checkout, or this project must have vendor/gsd-econ already."
    fi

    # If project has vendor/gsd-econ, prefer that as the source for symlinks
    # (so updates via `cd vendor/gsd-econ && git pull` flow through naturally).
    local source_dir="$GSD_ECON_SRC"
    if [[ -d "vendor/gsd-econ" ]]; then
        source_dir="$PROJECT_DIR/vendor/gsd-econ"
        log "Using vendored source: $source_dir"
    fi

    local rt
    rt="$(resolve_runtimes "$(detect_runtimes_project "$PROJECT_DIR")")"
    if [[ -z "$rt" ]]; then
        err "No runtime detected (.opencode/ or .claude/). Initialize GSD first."
    fi

    # Re-merge config first so place_agents can read updated model_tiers
    # (idempotent via jq) and re-copy any new rule files.
    GSD_ECON_SRC="$source_dir" wire_config
    GSD_ECON_SRC="$source_dir" copy_rules

    for r in $rt; do
        resolve_dirs "$r" "project"
        log "Re-linking commands into $CMD_DIR/"
        symlink_dir_contents "$source_dir/commands" "$CMD_DIR"
        log "Re-linking agents into $AGENT_DIR/"
        place_agents "$source_dir/agents" "$AGENT_DIR" "$r"
    done

    cat <<EOF

✓ wire-only re-install complete.

Anything new in the gsd-econ commands or agents directories is now linked.
Existing .planning/ files were preserved.
EOF
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

cat <<EOF
gsd-econ install
================
Mode:    $MODE
EOF
[[ "$MODE" == "project" || "$MODE" == "wire-only" ]] && echo "Target:  $PROJECT_DIR"
[[ "$DRY_RUN" == 1 ]] && echo "Dry run: yes"
echo

check_prereqs

case "$MODE" in
    project)   do_project_install ;;
    global)    do_global_install ;;
    wire-only) do_wire_only ;;
    *) err "Unknown mode: $MODE" ;;
esac
