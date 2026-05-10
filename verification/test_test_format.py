"""
Layer 2 — RUT test format compliance.

Every test in tests/core/ must follow the RUT format: required metadata fields
in the header, required sections in the body, values consistent with the
registry entry.
"""
from __future__ import annotations

from typing import Any

import pytest

from conftest import (
    VALID_CLARITIES,
    VALID_METHODOLOGIES,
    VALID_SCOPES,
    VALID_SEVERITIES,
    Document,
    has_section,
    parse_metadata_block,
)


REQUIRED_METADATA_FIELDS = {"methodology", "scope", "severity", "clarity"}
REQUIRED_SECTIONS = ["Criterion", "How to check", "Pass condition"]


def test_at_least_one_core_test(core_tests: list[Document]) -> None:
    assert len(core_tests) >= 3


def test_core_tests_have_metadata_block(core_tests: list[Document]) -> None:
    for doc in core_tests:
        meta = parse_metadata_block(doc.body)
        missing = REQUIRED_METADATA_FIELDS - meta.keys()
        assert not missing, f"Test {doc.name}: missing metadata fields {missing}"


def test_core_tests_metadata_values_valid(core_tests: list[Document]) -> None:
    for doc in core_tests:
        meta = parse_metadata_block(doc.body)
        assert meta["methodology"] in VALID_METHODOLOGIES, (
            f"Test {doc.name}: invalid methodology {meta['methodology']!r}"
        )
        assert meta["scope"] in VALID_SCOPES, (
            f"Test {doc.name}: invalid scope {meta['scope']!r}"
        )
        assert meta["severity"] in VALID_SEVERITIES, (
            f"Test {doc.name}: invalid severity {meta['severity']!r}"
        )
        assert meta["clarity"] in VALID_CLARITIES, (
            f"Test {doc.name}: invalid clarity {meta['clarity']!r}"
        )


def test_core_tests_have_required_sections(core_tests: list[Document]) -> None:
    for doc in core_tests:
        for section in REQUIRED_SECTIONS:
            assert has_section(doc.body, section), (
                f"Test {doc.name}: missing required section '## {section}'"
            )


def test_core_tests_match_registry(
    core_tests: list[Document], registry: list[dict[str, Any]]
) -> None:
    """The metadata block in each test file should match the registry entry."""
    by_id = {t["id"]: t for t in registry}
    for doc in core_tests:
        registry_entry = by_id.get(doc.name)
        assert registry_entry is not None, (
            f"Test {doc.name} exists in tests/core/ but not in registry.yaml"
        )
        meta = parse_metadata_block(doc.body)
        for field in REQUIRED_METADATA_FIELDS:
            assert meta[field] == registry_entry[field], (
                f"Test {doc.name}: metadata {field}={meta[field]!r} "
                f"does not match registry {field}={registry_entry[field]!r}"
            )


def test_registry_entries_have_files(
    core_tests: list[Document], registry: list[dict[str, Any]]
) -> None:
    """Every registry entry should have a corresponding markdown file."""
    file_ids = {doc.name for doc in core_tests}
    for entry in registry:
        assert entry["id"] in file_ids, (
            f"Registry entry {entry['id']} has no file in tests/core/"
        )


def test_core_tests_have_substantive_criterion(core_tests: list[Document]) -> None:
    """Criterion section should be at least 1 sentence (40 chars), not empty."""
    import re
    for doc in core_tests:
        m = re.search(
            r"^##\s+Criterion\s*\n(.+?)(?=^##\s+|\Z)",
            doc.body,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert m, f"Test {doc.name}: no Criterion section content"
        content = m.group(1).strip()
        assert len(content) >= 40, (
            f"Test {doc.name}: Criterion section too short ({len(content)} chars)"
        )


def test_core_tests_have_substantive_how_to_check(core_tests: list[Document]) -> None:
    import re
    for doc in core_tests:
        m = re.search(
            r"^##\s+How to check\s*\n(.+?)(?=^##\s+|\Z)",
            doc.body,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert m, f"Test {doc.name}: no How to check section"
        content = m.group(1).strip()
        assert len(content) >= 80, (
            f"Test {doc.name}: 'How to check' too short ({len(content)} chars). "
            "Operational instructions should be specific."
        )
