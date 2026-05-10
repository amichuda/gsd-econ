"""
Layer 2 — Test registry validation.

Verifies the YAML registry has the right schema, every entry resolves to a
real file, IDs are unique, and the values are in the canonical taxonomy.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import (
    VALID_CLARITIES,
    VALID_METHODOLOGIES,
    VALID_SCOPES,
    VALID_SEVERITIES,
)


REQUIRED_KEYS = {"id", "name", "methodology", "scope", "severity", "clarity", "path"}


def test_registry_loads(registry: list[dict[str, Any]]) -> None:
    assert isinstance(registry, list), "Registry top-level should be a list"
    assert len(registry) > 0, "Registry has no tests"


def test_registry_entries_have_required_keys(registry: list[dict[str, Any]]) -> None:
    for entry in registry:
        missing = REQUIRED_KEYS - entry.keys()
        assert not missing, (
            f"Test '{entry.get('id', '<unknown>')}' missing keys: {missing}"
        )


def test_registry_ids_are_unique(registry: list[dict[str, Any]]) -> None:
    ids = [t["id"] for t in registry]
    duplicates = [i for i in ids if ids.count(i) > 1]
    assert not duplicates, f"Duplicate test IDs: {set(duplicates)}"


def test_registry_methodologies_valid(registry: list[dict[str, Any]]) -> None:
    for t in registry:
        assert t["methodology"] in VALID_METHODOLOGIES, (
            f"Test '{t['id']}' has invalid methodology: {t['methodology']!r}"
        )


def test_registry_scopes_valid(registry: list[dict[str, Any]]) -> None:
    for t in registry:
        assert t["scope"] in VALID_SCOPES, (
            f"Test '{t['id']}' has invalid scope: {t['scope']!r}"
        )


def test_registry_severities_valid(registry: list[dict[str, Any]]) -> None:
    for t in registry:
        assert t["severity"] in VALID_SEVERITIES, (
            f"Test '{t['id']}' has invalid severity: {t['severity']!r}"
        )


def test_registry_clarities_valid(registry: list[dict[str, Any]]) -> None:
    for t in registry:
        assert t["clarity"] in VALID_CLARITIES, (
            f"Test '{t['id']}' has invalid clarity: {t['clarity']!r}"
        )


def test_registry_paths_resolve(registry: list[dict[str, Any]], repo_root: Path) -> None:
    for t in registry:
        path = repo_root / t["path"]
        assert path.is_file(), (
            f"Test '{t['id']}' references non-existent file: {t['path']}"
        )


def test_registry_id_matches_filename(
    registry: list[dict[str, Any]], repo_root: Path
) -> None:
    for t in registry:
        path = Path(t["path"])
        expected_stem = t["id"]
        assert path.stem == expected_stem, (
            f"Test '{t['id']}' filename {path.name} does not match id (expected {expected_stem}.md)"
        )


def test_registry_id_methodology_prefix_consistent(
    registry: list[dict[str, Any]],
) -> None:
    """
    Convention: test ID starts with its methodology tag (e.g., 'did-...', 'iv-...').
    Universal tests start with 'universal-'.
    """
    for t in registry:
        prefix = t["id"].split("-")[0]
        assert prefix == t["methodology"], (
            f"Test '{t['id']}' should start with its methodology tag "
            f"({t['methodology']}), got prefix {prefix!r}"
        )


def test_judgment_clarity_blockers_are_explicit(
    registry: list[dict[str, Any]],
) -> None:
    """
    Per design: judgment-clarity blockers exist, but should be rare and only
    when really intended. Surface for visibility.
    """
    judgment_blockers = [
        t for t in registry
        if t["clarity"] == "judgment" and t["severity"] == "blocker"
    ]
    # No assertion — just informational. We allow these but note their count.
    # Add an assert if you want to enforce a cap:
    assert len(judgment_blockers) <= 2, (
        f"Found {len(judgment_blockers)} judgment-clarity blockers; "
        "these defer to /gsd-referee-sim and should not be the default. "
        "Cap is 2; tighten if more are added."
    )
