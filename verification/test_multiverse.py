"""Tests for the multiverse pipeline.

Covers:
1. decisions.jsonl schema enforcement (via the rule file's worked examples)
2. Methodology grid YAML schema and content validation
3. multiverse_runner.py end-to-end with synthetic data
4. The /gsd-multiverse command file references things that exist
5. The multiverse-reporter agent frontmatter is valid (PDF + HTML output)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Rule and command file presence
# ---------------------------------------------------------------------------


def test_decision_logging_rule_exists(repo_root: Path) -> None:
    """The decision-logging rule must exist and cover the load-bearing concepts."""
    rule = repo_root / "rules" / "decision-logging.md"
    assert rule.exists(), "rules/decision-logging.md is missing"
    text = rule.read_text(encoding="utf-8")
    # Must cover schema, what-to-log, what-not-to-log, multiverse interaction
    for concept in ["pap_committed", "alternatives", "decisions.jsonl", "What to log", "What NOT to log"]:
        assert concept in text, f"decision-logging.md missing concept: {concept}"


def test_decision_logging_rule_in_agents_md(repo_root: Path) -> None:
    """AGENTS.md must reference decision-logging in its lazy-load table."""
    agents_md = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "rules/decision-logging.md" in agents_md, (
        "decision-logging.md must be in AGENTS.md's rule table for lazy loading"
    )


def test_multiverse_command_exists(repo_root: Path) -> None:
    cmd = repo_root / "commands" / "gsd-multiverse.md"
    assert cmd.exists()
    text = cmd.read_text(encoding="utf-8")
    # Must reference the runner script and the rule file
    assert "multiverse_runner.py" in text
    assert "decision-logging.md" in text


def test_multiverse_reporter_agent_exists(repo_root: Path) -> None:
    """Single reporter agent produces both PDF and HTML."""
    agent = repo_root / "agents" / "multiverse-reporter.md"
    assert agent.exists()
    text = agent.read_text(encoding="utf-8")
    assert "---" in text  # has frontmatter
    assert "model_tier:" in text
    # Must mention both output types
    assert "PDF" in text or ".pdf" in text
    assert "HTML" in text or ".html" in text


def test_multiverse_reporter_referenced_by_command(repo_root: Path) -> None:
    """The /gsd-multiverse command should reference the reporter agent."""
    cmd_text = (repo_root / "commands" / "gsd-multiverse.md").read_text(encoding="utf-8")
    assert "multiverse-reporter" in cmd_text, (
        "/gsd-multiverse should reference the multiverse-reporter agent"
    )


# ---------------------------------------------------------------------------
# Methodology grid schema
# ---------------------------------------------------------------------------


def test_all_methodology_grids_parse(repo_root: Path) -> None:
    """Every grid YAML must parse and have the required schema."""
    yaml = pytest.importorskip("yaml")
    grids_dir = repo_root / "config" / "multiverse-grids"
    assert grids_dir.is_dir()
    yamls = sorted(grids_dir.glob("*.yaml"))
    assert yamls, "no methodology grids found"
    for path in yamls:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path.name} not a mapping"
        assert "design" in data, f"{path.name} missing 'design'"
        assert "axes" in data, f"{path.name} missing 'axes'"
        for axis_name, axis_spec in data["axes"].items():
            if not isinstance(axis_spec, dict):
                continue
            assert "alternatives" in axis_spec, (
                f"{path.name} axis '{axis_name}' missing 'alternatives'"
            )
            assert "default" in axis_spec, (
                f"{path.name} axis '{axis_name}' missing 'default'"
            )
            assert "description" in axis_spec, (
                f"{path.name} axis '{axis_name}' missing 'description'"
            )


def test_methodology_grids_have_citations(repo_root: Path) -> None:
    """Each axis should have at least one citation (or empty list with reason)."""
    yaml = pytest.importorskip("yaml")
    grids_dir = repo_root / "config" / "multiverse-grids"
    for path in grids_dir.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for axis_name, axis_spec in data.get("axes", {}).items():
            if not isinstance(axis_spec, dict):
                continue
            # citations field should be present (may be empty for trivial axes)
            assert "citations" in axis_spec, (
                f"{path.name} axis '{axis_name}' missing 'citations' field"
            )


def test_methodology_grids_default_is_in_alternatives(repo_root: Path) -> None:
    """Each axis's default value should appear in its alternatives list."""
    yaml = pytest.importorskip("yaml")
    grids_dir = repo_root / "config" / "multiverse-grids"
    for path in grids_dir.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for axis_name, axis_spec in data.get("axes", {}).items():
            if not isinstance(axis_spec, dict):
                continue
            default = axis_spec.get("default")
            alternatives = axis_spec.get("alternatives", [])
            if default is None or not alternatives:
                continue
            assert default in alternatives, (
                f"{path.name} axis '{axis_name}': default '{default}' not in "
                f"alternatives {alternatives}"
            )


# ---------------------------------------------------------------------------
# Runner end-to-end
# ---------------------------------------------------------------------------


def _make_simple_evaluator(path: Path) -> None:
    """Write a deterministic evaluator that varies coefficient by spec."""
    path.write_text("""
def evaluate(spec):
    # Deterministic coefficient based on spec values
    base = 0.10
    for key, val in sorted(spec.items()):
        base += 0.001 * (hash(f"{key}={val}") % 100)
    return {"coefficient": base, "se": 0.02, "p_value": 0.04, "n_obs": 340}
""", encoding="utf-8")


def test_runner_imports_clean(repo_root: Path) -> None:
    """The runner must be runnable as a script (verify with --help)."""
    runner = repo_root / "scripts" / "multiverse_runner.py"
    assert runner.exists()
    result = subprocess.run(
        [sys.executable, str(runner), "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"runner --help failed: {result.stderr}"
    assert "multiverse" in result.stdout.lower(), (
        "runner --help should mention multiverse"
    )


def test_runner_dry_run_with_decisions_only(repo_root: Path) -> None:
    """Runner --dry-run with just a decisions log must print the grid without errors."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        decisions = tmp / "decisions.jsonl"
        decisions.write_text(
            '{"id": "d001", "phase": "cleaning", "type": "filter", "decision": "abs<=5", '
            '"alternatives": ["abs<=10", "no filter"], "justification": "test", '
            '"pap_committed": false}\n'
            '{"id": "d002", "phase": "methodology", "type": "se", "decision": "robust", '
            '"alternatives": ["cluster"], "justification": "test", "pap_committed": false}\n',
            encoding="utf-8",
        )
        evaluator = tmp / "evaluator.py"
        _make_simple_evaluator(evaluator)
        result = subprocess.run(
            [sys.executable, str(runner),
             "--decisions", str(decisions),
             "--evaluator", str(evaluator),
             "--dry-run"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, f"dry-run failed: {result.stderr}"
        assert "Multiverse:" in result.stdout
        assert "d001" in result.stdout
        assert "d002" in result.stdout


def test_runner_skips_pap_committed_decisions(repo_root: Path) -> None:
    """Decisions with pap_committed=true must not become multiverse axes."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        decisions = tmp / "decisions.jsonl"
        decisions.write_text(
            '{"id": "d001", "phase": "cleaning", "type": "filter", "decision": "abs<=5", '
            '"alternatives": ["abs<=10"], "justification": "test", "pap_committed": false}\n'
            '{"id": "d_locked", "phase": "methodology", "type": "se", "decision": "robust", '
            '"alternatives": ["cluster"], "justification": "PAP commits this", '
            '"pap_committed": true}\n',
            encoding="utf-8",
        )
        evaluator = tmp / "evaluator.py"
        _make_simple_evaluator(evaluator)
        result = subprocess.run(
            [sys.executable, str(runner),
             "--decisions", str(decisions),
             "--evaluator", str(evaluator),
             "--dry-run"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
        assert "d001" in result.stdout
        assert "d_locked" not in result.stdout, (
            "PAP-committed decision leaked into the multiverse grid"
        )


def test_runner_end_to_end_writes_csv(repo_root: Path) -> None:
    """Full run should produce a CSV with one row per cell of the grid."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        decisions = tmp / "decisions.jsonl"
        decisions.write_text(
            '{"id": "d001", "decision": "a", "alternatives": ["b", "c"], '
            '"justification": "t", "pap_committed": false}\n'
            '{"id": "d002", "decision": "x", "alternatives": ["y"], '
            '"justification": "t", "pap_committed": false}\n',
            encoding="utf-8",
        )
        evaluator = tmp / "evaluator.py"
        _make_simple_evaluator(evaluator)
        output = tmp / "results.csv"
        result = subprocess.run(
            [sys.executable, str(runner),
             "--decisions", str(decisions),
             "--evaluator", str(evaluator),
             "--output", str(output),
             "--mode", "full",
             "--quiet"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, f"runner failed: {result.stderr}"
        assert output.exists()
        # Expect 3 * 2 = 6 specifications
        lines = output.read_text().strip().split("\n")
        assert len(lines) == 7, f"expected 6 data rows + header, got {len(lines)}"


def test_runner_main_effects_mode(repo_root: Path) -> None:
    """main_effects mode should produce 1 + sum(alts - 1) cells."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        decisions = tmp / "decisions.jsonl"
        # 3 axes with 3, 2, 2 values: main-effects = 1 + 2 + 1 + 1 = 5 cells
        decisions.write_text(
            '{"id": "d1", "decision": "a", "alternatives": ["b", "c"], '
            '"justification": "t", "pap_committed": false}\n'
            '{"id": "d2", "decision": "x", "alternatives": ["y"], '
            '"justification": "t", "pap_committed": false}\n'
            '{"id": "d3", "decision": "p", "alternatives": ["q"], '
            '"justification": "t", "pap_committed": false}\n',
            encoding="utf-8",
        )
        evaluator = tmp / "evaluator.py"
        _make_simple_evaluator(evaluator)
        output = tmp / "results.csv"
        result = subprocess.run(
            [sys.executable, str(runner),
             "--decisions", str(decisions),
             "--evaluator", str(evaluator),
             "--output", str(output),
             "--mode", "main_effects",
             "--quiet"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
        lines = output.read_text().strip().split("\n")
        # 1 (all defaults) + (3-1) + (2-1) + (2-1) = 5 cells
        assert len(lines) == 6, (
            f"expected 5 main-effects cells + header, got {len(lines) - 1}"
        )


def test_runner_handles_evaluator_errors(repo_root: Path) -> None:
    """If the evaluator raises, the runner should record the error and continue."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        decisions = tmp / "decisions.jsonl"
        decisions.write_text(
            '{"id": "d1", "decision": "a", "alternatives": ["b"], '
            '"justification": "t", "pap_committed": false}\n',
            encoding="utf-8",
        )
        evaluator = tmp / "evaluator.py"
        evaluator.write_text(
            "def evaluate(spec):\n"
            "    if spec.get('d1') == 'b':\n"
            "        raise ValueError('synthetic error')\n"
            "    return {'coefficient': 0.1, 'se': 0.02}\n",
            encoding="utf-8",
        )
        output = tmp / "results.csv"
        result = subprocess.run(
            [sys.executable, str(runner),
             "--decisions", str(decisions),
             "--evaluator", str(evaluator),
             "--output", str(output),
             "--mode", "full",
             "--quiet"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
        text = output.read_text()
        assert "synthetic error" in text or "ValueError" in text, (
            "runner should record evaluator errors, not crash on them"
        )


def test_runner_uses_methodology_grid(repo_root: Path) -> None:
    """Runner can load and use a methodology grid YAML."""
    pytest.importorskip("yaml")
    runner = repo_root / "scripts" / "multiverse_runner.py"
    rct_grid = repo_root / "config" / "multiverse-grids" / "rct.yaml"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        evaluator = tmp / "evaluator.py"
        _make_simple_evaluator(evaluator)
        result = subprocess.run(
            [sys.executable, str(runner),
             "--grid", str(rct_grid),
             "--evaluator", str(evaluator),
             "--dry-run"],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
        assert "se_clustering" in result.stdout
        assert "stratum_fe" in result.stdout


# ---------------------------------------------------------------------------
# Version bookkeeping (CHANGELOG, CITATION, pyproject)
# ---------------------------------------------------------------------------


def test_version_bumped_to_0_3(repo_root: Path) -> None:
    """v0.3 should be reflected in CITATION.cff and pyproject.toml."""
    citation = (repo_root / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "version: 0.3.0" in citation or 'version: "0.3.0"' in citation
    assert 'version = "0.3.0"' in pyproject


def test_changelog_documents_0_3(repo_root: Path) -> None:
    """CHANGELOG should exist and document v0.3 features."""
    changelog = repo_root / "CHANGELOG.md"
    assert changelog.exists(), "CHANGELOG.md missing"
    text = changelog.read_text(encoding="utf-8")
    assert "0.3.0" in text
    # Must mention the major v0.3 features
    for feature in ["multiverse", "decision-logging", "decisions.jsonl"]:
        assert feature in text.lower() or feature in text, (
            f"CHANGELOG missing mention of {feature}"
        )
