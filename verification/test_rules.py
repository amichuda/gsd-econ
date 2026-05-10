"""
Layer 2 — Project rules contract.

The rules folder follows the OpenCode/Claude Code AGENTS.md convention with a
lazy-loaded rules/*.md pattern. Tests enforce:
- AGENTS.md exists at the repo root and references rules/ files
- Each rule file referenced in AGENTS.md actually exists
- Rule files are short (lazy-load is only useful if files are small)
- AGENTS.md has the expected always-on invariants
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REQUIRED_RULE_FILES = {
    "rules/identification.md",
    "rules/methodology-integrity.md",
    "rules/file-discipline.md",
    "rules/git-discipline.md",
    "rules/preregistration.md",
    "rules/data-handling.md",
    "rules/manuscript-discipline.md",
    "rules/uncertainty-honesty.md",
}


def test_agents_md_exists(repo_root: Path) -> None:
    path = repo_root / "AGENTS.md"
    assert path.is_file(), (
        "AGENTS.md must exist at the repo root. This is the always-on "
        "instructions file loaded by OpenCode, Claude Code, Codex, etc."
    )


def test_rules_folder_exists(repo_root: Path) -> None:
    rules_dir = repo_root / "rules"
    assert rules_dir.is_dir(), (
        "rules/ folder must exist. AGENTS.md uses lazy-load references "
        "into this folder."
    )


def test_all_required_rule_files_exist(repo_root: Path) -> None:
    missing = []
    for rule_path in REQUIRED_RULE_FILES:
        if not (repo_root / rule_path).is_file():
            missing.append(rule_path)
    assert not missing, (
        f"Missing required rule files: {missing}. "
        "Each rule file in AGENTS.md's lazy-load table must exist."
    )


def test_agents_md_references_all_rule_files(repo_root: Path) -> None:
    """Every rule file should be referenced from AGENTS.md."""
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    missing = []
    for rule_path in REQUIRED_RULE_FILES:
        # Filename without the rules/ prefix is enough; AGENTS.md should mention it
        if rule_path not in agents_text:
            missing.append(rule_path)
    assert not missing, (
        f"AGENTS.md does not reference these rule files: {missing}. "
        "If a rule file exists but isn't in AGENTS.md's table, the lazy-load "
        "trigger logic won't find it."
    )


def test_rule_files_are_short(repo_root: Path) -> None:
    """
    The point of lazy-loading is that each file is cheap to read on demand.
    A 500-line rule file negates the benefit. Cap at 100 lines per file.
    """
    too_long = []
    for rule_path in REQUIRED_RULE_FILES:
        path = repo_root / rule_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 100:
            too_long.append(f"{rule_path}: {line_count} lines")
    assert not too_long, (
        f"Rule files exceed 100 lines (lazy-load assumes small files):\n"
        + "\n".join(too_long)
        + "\nEither split the file, or reduce content."
    )


def test_agents_md_has_always_on_section(repo_root: Path) -> None:
    """AGENTS.md should distinguish always-on rules from lazy-loaded ones."""
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8").lower()
    assert "always-on" in text or "always on" in text, (
        "AGENTS.md should have an 'Always-on invariants' section "
        "distinguishing always-loaded rules from lazy-loaded ones"
    )
    assert "lazy" in text or "load" in text or "demand" in text, (
        "AGENTS.md should explain when lazy-loaded rules are loaded"
    )


def test_agents_md_has_escape_hatch(repo_root: Path) -> None:
    """The user must be able to override rules with explicit instructions."""
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8").lower()
    assert "override" in text or "escape hatch" in text, (
        "AGENTS.md should document that the user can override any rule "
        "with an explicit instruction. Rules are defaults, not locks."
    )


def test_rule_files_are_self_describing(repo_root: Path) -> None:
    """Each rule file should start with a heading that names the rule."""
    bad = []
    for rule_path in REQUIRED_RULE_FILES:
        path = repo_root / rule_path
        first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
        if not first_line.startswith("# "):
            bad.append(f"{rule_path}: first line is {first_line!r}, not an H1 heading")
    assert not bad, "\n".join(bad)


def test_no_duplicate_constraints_between_agents_md_and_rules(repo_root: Path) -> None:
    """
    AGENTS.md's always-on section should be distinct from rule file content.
    A signal of bad design: the same paragraph appears in AGENTS.md and a rule file.
    """
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    # Pull out distinctive sentences from AGENTS.md (anything starting with **)
    bold_phrases = re.findall(r"\*\*([^*]+)\*\*", agents_text)
    for rule_path in REQUIRED_RULE_FILES:
        rule_text = (repo_root / rule_path).read_text(encoding="utf-8")
        for phrase in bold_phrases:
            if len(phrase) > 30 and phrase in rule_text:
                pytest.fail(
                    f"Distinctive phrase {phrase!r} appears in both AGENTS.md "
                    f"and {rule_path}. Don't duplicate — AGENTS.md is always-on, "
                    f"rule files are lazy-loaded; same content in both is wasted tokens."
                )


def test_uncertainty_rule_distinguishes_known_partial_unknown(repo_root: Path) -> None:
    """
    The uncertainty rule should explicitly distinguish three knowledge states.
    Treating partial knowledge as known is the core hallucination failure mode.
    """
    text = (repo_root / "rules" / "uncertainty-honesty.md").read_text(encoding="utf-8").lower()
    states = ["known", "partial", "unknown"]
    missing = [s for s in states if s not in text]
    assert not missing, (
        f"rules/uncertainty-honesty.md should distinguish three knowledge states "
        f"(known / partial / unknown). Missing terms: {missing}."
    )


def test_uncertainty_rule_treats_uncertainty_as_action_signal(repo_root: Path) -> None:
    """
    The metacognition framing: uncertainty is a control signal that triggers
    search, fetch, or asking the user — not a feature to hide.
    """
    text = (repo_root / "rules" / "uncertainty-honesty.md").read_text(encoding="utf-8").lower()
    action_signals = ["search", "fetch", "ask", "verify"]
    found = [a for a in action_signals if a in text]
    assert len(found) >= 3, (
        f"rules/uncertainty-honesty.md should describe uncertainty as triggering "
        f"action (search/fetch/ask/verify). Found only: {found}"
    )


def test_uncertainty_rule_prohibits_inventing(repo_root: Path) -> None:
    """Specific prohibitions against inventing citations, file contents, results."""
    text = (repo_root / "rules" / "uncertainty-honesty.md").read_text(encoding="utf-8").lower()
    invent_terms = ["invent", "fabricat", "confabulat", "guess"]
    found = [t for t in invent_terms if t in text]
    assert found, (
        "rules/uncertainty-honesty.md should explicitly prohibit inventing/fabricating/"
        f"guessing content. Use any of: {invent_terms}"
    )


def test_agents_md_addresses_confident_errors(repo_root: Path) -> None:
    """
    AGENTS.md's calibrated-honesty invariant should frame the failure mode as
    confident errors, not just 'don't lie'. This is the metacognition framing.
    """
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8").lower()
    # At least one of these phrasings should appear
    framings = ["confident error", "calibrat", "metacog", "faithful uncertain"]
    found = [f for f in framings if f in text]
    assert found, (
        f"AGENTS.md should frame hallucination as confident-error / calibration / "
        f"metacognition rather than just 'be honest'. Use any of: {framings}"
    )


def test_uncertainty_rule_attributes_yona_paper(repo_root: Path) -> None:
    """
    The metacognition framing in the uncertainty rule draws on Yona, Geva, Matias
    (2026). The attribution must appear in the rule file itself so future readers
    know where the framing came from.
    """
    text = (repo_root / "rules" / "uncertainty-honesty.md").read_text(encoding="utf-8")
    assert "Yona" in text and "2605.01428" in text, (
        "rules/uncertainty-honesty.md must cite Yona, Geva, Matias (2026), "
        "arXiv:2605.01428, since the framing (confident errors, faithful "
        "uncertainty, control-layer metacognition) draws on that paper."
    )


def test_yona_paper_in_contributing_attribution(repo_root: Path) -> None:
    """The CONTRIBUTING.md prior-art section must list the Yona et al. paper."""
    text = (repo_root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "2605.01428" in text or "Yona" in text, (
        "CONTRIBUTING.md prior-art section must mention Yona et al. (2026), "
        "since rules/uncertainty-honesty.md draws on that paper."
    )


def test_yona_paper_in_citation_cff(repo_root: Path) -> None:
    """CITATION.cff references list should include the Yona et al. paper."""
    text = (repo_root / "CITATION.cff").read_text(encoding="utf-8")
    assert "2605.01428" in text or "Hallucinations Undermine Trust" in text, (
        "CITATION.cff references must include Yona et al. (2026) "
        "since the framework's uncertainty-handling rules draw on it."
    )
