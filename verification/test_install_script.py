"""
Layer 4 — install.sh behavior.

The single install.sh handles three modes:
- --project (default): full from-scratch install for a single paper
- --global: user-wide install of commands + agents
- --wire-only: re-link after `git pull` (no GSD/RUT changes)

Tests cover argument parsing, dry-run safety, real installs in each mode,
idempotency, and refusing to clobber existing user files.

Skips on Windows (install.sh is bash).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="install.sh requires bash",
)


@pytest.fixture
def install_script(repo_root: Path) -> Path:
    path = repo_root / "install.sh"
    assert path.is_file(), "install.sh must exist at the repo root"
    return path


# -----------------------------------------------------------------------------
# Help / parsing
# -----------------------------------------------------------------------------

def test_help_succeeds(install_script: Path) -> None:
    result = subprocess.run(
        ["bash", str(install_script), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"


def test_help_documents_all_three_modes(install_script: Path) -> None:
    result = subprocess.run(
        ["bash", str(install_script), "--help"],
        capture_output=True, text=True,
    )
    assert "--project" in result.stdout
    assert "--global" in result.stdout
    assert "--wire-only" in result.stdout


def test_help_documents_skip_flags(install_script: Path) -> None:
    result = subprocess.run(
        ["bash", str(install_script), "--help"],
        capture_output=True, text=True,
    )
    assert "--skip-gsd" in result.stdout
    assert "--skip-rut" in result.stdout


def test_unknown_flag_fails(install_script: Path) -> None:
    result = subprocess.run(
        ["bash", str(install_script), "--no-such-flag"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


# -----------------------------------------------------------------------------
# --dry-run for each mode
# -----------------------------------------------------------------------------

def test_dry_run_global_no_filesystem_changes(
    install_script: Path, tmp_path: Path
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--dry-run", "--yes",
         "--runtime", "claude"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, (
        f"--dry-run --global failed:\n{result.stdout}\n{result.stderr}"
    )
    assert not (fake_home / ".claude").exists(), "Dry-run created files"


def test_dry_run_project_no_filesystem_changes(
    install_script: Path, tmp_path: Path
) -> None:
    fake_project = tmp_path / "fake-project"
    fake_project.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=fake_project, check=True)

    result = subprocess.run(
        ["bash", str(install_script),
         "--project", str(fake_project),
         "--dry-run", "--yes",
         "--skip-gsd", "--skip-rut"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"--dry-run --project failed:\n{result.stdout}\n{result.stderr}"
    )
    assert not (fake_project / "vendor").exists()
    assert not (fake_project / ".planning").exists()


def test_dry_run_output_marks_planned_actions(install_script: Path, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--dry-run", "--yes",
         "--runtime", "claude"],
        capture_output=True, text=True, env=env,
    )
    assert "[dry-run]" in result.stdout, (
        "--dry-run should prefix planned commands with [dry-run]"
    )


# -----------------------------------------------------------------------------
# --global real install (no GSD/RUT involvement; just symlinks)
# -----------------------------------------------------------------------------

def test_global_creates_symlinks(install_script: Path, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--yes", "--runtime", "claude"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, (
        f"Global install failed:\n{result.stdout}\n{result.stderr}"
    )
    cmd_dir = fake_home / ".claude" / "commands"
    agent_dir = fake_home / ".claude" / "agents"
    assert cmd_dir.is_dir()
    assert agent_dir.is_dir()
    assert (cmd_dir / "gsd-new-paper.md").exists()
    assert (agent_dir / "identification-checker.md").exists()


def test_global_does_not_clobber_existing_files(
    install_script: Path, tmp_path: Path
) -> None:
    fake_home = tmp_path / "home"
    cmd_dir = fake_home / ".claude" / "commands"
    cmd_dir.mkdir(parents=True)
    pre_existing = cmd_dir / "gsd-new-paper.md"
    pre_existing.write_text("# my custom command\n")

    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--yes", "--runtime", "claude"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0
    assert not pre_existing.is_symlink()
    assert pre_existing.read_text() == "# my custom command\n"


def test_global_warns_on_clobber_attempt(install_script: Path, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    cmd_dir = fake_home / ".claude" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "gsd-new-paper.md").write_text("# existing\n")

    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--yes", "--runtime", "claude"],
        capture_output=True, text=True, env=env,
    )
    combined = result.stdout + result.stderr
    assert "leaving alone" in combined or "exists" in combined


def test_global_runtime_both_creates_both(
    install_script: Path, tmp_path: Path
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        ["bash", str(install_script), "--global", "--yes", "--runtime", "both"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0
    assert (fake_home / ".claude" / "agents").is_dir()
    assert (fake_home / ".opencode" / "agent").is_dir()


# -----------------------------------------------------------------------------
# --project real install (with --skip-gsd --skip-rut to avoid network calls)
# -----------------------------------------------------------------------------

@pytest.fixture
def fake_project_with_runtime(tmp_path: Path, repo_root: Path) -> Path:
    """A project dir with .opencode/ pre-created (simulating already-installed GSD)."""
    project = tmp_path / "fake-project"
    project.mkdir()
    (project / ".opencode" / "command").mkdir(parents=True)
    (project / ".opencode" / "agent").mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)
    return project


def _run_project_install(
    install_script: Path, project: Path, *extra_args: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(install_script),
         "--project", str(project),
         "--skip-gsd", "--skip-rut",
         "--yes",
         *extra_args],
        capture_output=True, text=True,
    )


def test_project_install_succeeds(install_script: Path, fake_project_with_runtime: Path) -> None:
    result = _run_project_install(install_script, fake_project_with_runtime)
    assert result.returncode == 0, (
        f"--project install failed:\n{result.stdout}\n{result.stderr}"
    )


def test_project_install_creates_command_symlinks(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    cmd_dir = fake_project_with_runtime / ".opencode" / "command"
    expected = ["gsd-new-paper.md", "gsd-discuss-identification.md",
                "gsd-plan-empirics.md", "gsd-verify-replication.md"]
    for cmd in expected:
        assert (cmd_dir / cmd).exists(), f"Expected symlink {cmd} not created"


def test_project_install_creates_agent_symlinks(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    agent_dir = fake_project_with_runtime / ".opencode" / "agent"
    expected = ["econ-researcher.md", "identification-checker.md",
                "replication-verifier.md", "referee-deliberator.md"]
    for agent in expected:
        assert (agent_dir / agent).exists(), f"Expected agent {agent} not linked"


def test_project_install_creates_planning_config(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    cfg = fake_project_with_runtime / ".planning" / "config.json"
    assert cfg.is_file()


def test_project_install_copies_templates(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    expected = ["PROJECT.md", "REQUIREMENTS.md", "METHODOLOGY.md",
                "ROADMAP.md", "STATE.md"]
    for name in expected:
        assert (fake_project_with_runtime / ".planning" / name).is_file(), (
            f"Template {name} should be copied"
        )


def test_project_install_idempotent(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    r1 = _run_project_install(install_script, fake_project_with_runtime)
    assert r1.returncode == 0
    r2 = _run_project_install(install_script, fake_project_with_runtime)
    assert r2.returncode == 0, (
        f"Second install failed (idempotency violated):\n{r2.stdout}\n{r2.stderr}"
    )


def test_project_install_preserves_existing_planning_files(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    planning = fake_project_with_runtime / ".planning"
    planning.mkdir(exist_ok=True)
    existing = planning / "PROJECT.md"
    existing.write_text("# My existing project\n\nDo not delete me.\n")

    _run_project_install(install_script, fake_project_with_runtime)

    assert "Do not delete me" in existing.read_text()


# -----------------------------------------------------------------------------
# --wire-only mode
# -----------------------------------------------------------------------------

def test_wire_only_succeeds_after_project_install(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    """wire-only should be the standard re-run path."""
    # First, do a full project install
    _run_project_install(install_script, fake_project_with_runtime)
    # Then re-run with --wire-only
    result = subprocess.run(
        ["bash", str(install_script),
         "--wire-only",
         "--project", str(fake_project_with_runtime),
         "--yes"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"--wire-only failed:\n{result.stdout}\n{result.stderr}"
    )


def test_wire_only_preserves_planning_files(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    project_md = fake_project_with_runtime / ".planning" / "PROJECT.md"
    project_md.write_text("# Real project content\n\nDon't lose this.\n")

    subprocess.run(
        ["bash", str(install_script),
         "--wire-only",
         "--project", str(fake_project_with_runtime),
         "--yes"],
        capture_output=True, text=True, check=True,
    )
    assert "Don't lose this" in project_md.read_text()


def test_project_install_copies_agents_md(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    agents_md = fake_project_with_runtime / "AGENTS.md"
    assert agents_md.is_file(), (
        "Project install should copy AGENTS.md into project root "
        "(it's the always-on rules file the runtime loads)"
    )


def test_project_install_copies_rules_folder(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    _run_project_install(install_script, fake_project_with_runtime)
    rules_dir = fake_project_with_runtime / "rules"
    assert rules_dir.is_dir()
    # At least one expected rule file
    assert (rules_dir / "identification.md").is_file()
    assert (rules_dir / "file-discipline.md").is_file()


def test_project_install_preserves_existing_agents_md(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    """A user with their own AGENTS.md should not have it clobbered."""
    existing = fake_project_with_runtime / "AGENTS.md"
    existing.write_text("# My existing project rules\n\nDo not lose this.\n")

    _run_project_install(install_script, fake_project_with_runtime)

    assert "Do not lose this" in existing.read_text(), (
        "Existing AGENTS.md must not be clobbered"
    )


def test_project_install_adds_missing_rules_into_existing_folder(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    """If the project has rules/ already but is missing some files, fill in only the missing ones."""
    rules_dir = fake_project_with_runtime / "rules"
    rules_dir.mkdir()
    custom_rule = rules_dir / "identification.md"
    custom_rule.write_text("# my custom identification rule\n")

    _run_project_install(install_script, fake_project_with_runtime)

    # Existing file preserved
    assert "my custom" in custom_rule.read_text()
    # But missing files should have been added
    assert (rules_dir / "file-discipline.md").is_file()


def test_wire_only_copies_missing_rules(
    install_script: Path, fake_project_with_runtime: Path
) -> None:
    """If a new rule file is added upstream, --wire-only should pick it up."""
    # Initial install
    _run_project_install(install_script, fake_project_with_runtime)
    # Simulate a missing rule file (delete it from the project)
    rule = fake_project_with_runtime / "rules" / "identification.md"
    rule.unlink()
    # Wire-only should restore it
    result = subprocess.run(
        ["bash", str(install_script),
         "--wire-only",
         "--project", str(fake_project_with_runtime),
         "--yes"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert rule.is_file(), "wire-only should restore missing rule files"


# -----------------------------------------------------------------------------
# Mode resolution / arg defaults
# -----------------------------------------------------------------------------

def test_no_mode_defaults_to_project(install_script: Path, tmp_path: Path) -> None:
    fake = tmp_path / "default"
    fake.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=fake, check=True)

    result = subprocess.run(
        ["bash", str(install_script),
         "--dry-run", "--yes",
         "--skip-gsd", "--skip-rut"],
        capture_output=True, text=True, cwd=fake,
    )
    assert result.returncode == 0
    assert "Mode:    project" in result.stdout


def test_install_fails_gracefully_without_runtime(
    install_script: Path, tmp_path: Path, repo_root: Path
) -> None:
    """If neither .opencode/ nor .claude/ exists, the project install should not silently no-op."""
    project = tmp_path / "no-runtime"
    project.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)

    # With --skip-gsd, no GSD core gets installed, so no runtime dir gets created.
    # The script should default to creating one (currently `claude`) per resolve_runtimes;
    # this is a tested behavior — the install proceeds with the default.
    result = subprocess.run(
        ["bash", str(install_script),
         "--project", str(project),
         "--skip-gsd", "--skip-rut",
         "--yes"],
        capture_output=True, text=True,
    )
    # The script has a documented fallback to "claude" when no runtime detected.
    # That's a reasonable behavior; the install succeeds and creates the dirs.
    assert result.returncode == 0
    # Either claude or opencode dir got created, depending on default
    has_runtime = (
        (project / ".claude").exists() or (project / ".opencode").exists()
    )
    assert has_runtime, "Install should create a runtime dir as fallback"
