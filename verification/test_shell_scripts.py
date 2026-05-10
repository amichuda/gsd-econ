"""
Layer 1 — Shell script hygiene.

Every .sh script must have a shebang and use strict mode.
Optionally runs shellcheck if installed.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def _shell_scripts(repo_root: Path) -> list[Path]:
    """All shell scripts in scope: scripts/*.sh and root-level *.sh."""
    return sorted(
        list((repo_root / "scripts").glob("*.sh"))
        + list(repo_root.glob("*.sh"))
    )


def test_shell_scripts_have_shebang(repo_root: Path) -> None:
    for script in _shell_scripts(repo_root):
        first = script.read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("#!"), (
            f"{script.name}: missing shebang on first line"
        )
        assert "bash" in first or "sh" in first, (
            f"{script.name}: shebang should specify bash or sh"
        )


def test_shell_scripts_use_strict_mode(repo_root: Path) -> None:
    """All scripts should use 'set -euo pipefail' or at minimum 'set -e'."""
    for script in _shell_scripts(repo_root):
        text = script.read_text(encoding="utf-8")
        has_strict = (
            "set -euo pipefail" in text
            or "set -e" in text
        )
        assert has_strict, (
            f"{script.name}: should use 'set -euo pipefail' (or at least 'set -e') "
            "for strict error handling"
        )


def test_shell_scripts_executable(repo_root: Path) -> None:
    """Scripts should be marked executable on disk."""
    import os
    import stat
    for script in _shell_scripts(repo_root):
        mode = os.stat(script).st_mode
        is_exec = bool(mode & stat.S_IXUSR)
        # Note: this can fail on systems where git stripped the exec bit.
        # If it's a problem in CI, run `chmod +x scripts/*.sh` in the workflow.
        assert is_exec, (
            f"{script.name}: not marked executable. "
            "Run: chmod +x scripts/*.sh"
        )


@pytest.mark.skipif(
    shutil.which("shellcheck") is None,
    reason="shellcheck not installed; skipping deep shell linting",
)
def test_shell_scripts_pass_shellcheck(repo_root: Path) -> None:
    failures: list[str] = []
    for script in _shell_scripts(repo_root):
        result = subprocess.run(
            ["shellcheck", "--severity=warning", str(script)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(
                f"\n--- {script.name} ---\n{result.stdout}\n{result.stderr}"
            )
    assert not failures, "shellcheck found issues:\n" + "\n".join(failures)
