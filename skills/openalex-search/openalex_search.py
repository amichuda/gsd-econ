"""
openalex_search — helpers backing the openalex-search skill.

Usage:
    from openalex_search import find_recent_nber, find_evaluation_candidates

These functions wrap pyalex with the patterns documented in SKILL.md.
They're intended for use in scripts, notebooks, or invoked by agents
in the gsd-econ framework.

Honest scope: this is a thin wrapper around pyalex. The point is
discoverability of the patterns we found useful for econ research,
not a competing API surface.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


def _ensure_pyalex_configured() -> None:
    """Set the API key and email from environment variables if not already configured."""
    import pyalex

    if pyalex.config.api_key is None:
        api_key = os.environ.get("OPENALEX_API_KEY")
        if api_key:
            pyalex.config.api_key = api_key
    if pyalex.config.email is None:
        email = os.environ.get("OPENALEX_EMAIL")
        if email:
            pyalex.config.email = email


@lru_cache(maxsize=1)
def get_nber_source_id() -> str:
    """Look up NBER's OpenAlex source ID. Cached after first call.

    The lookup tries multiple candidate display-name patterns since OpenAlex
    may use slightly different names (e.g., NBER, the NBER working paper series).
    If multiple sources match, prefers the one with the most works (the
    main paper series).
    """
    _ensure_pyalex_configured()
    from pyalex import Sources

    results = Sources().search("National Bureau of Economic Research").get()
    if not results:
        raise RuntimeError(
            "OpenAlex returned no sources for 'National Bureau of Economic Research'. "
            "Check your network and API key configuration."
        )

    # Prefer exact match on display name; fall back to substring match
    candidates = []
    for source in results:
        name = source.get("display_name", "")
        if name == "National Bureau of Economic Research":
            return source["id"].replace("https://openalex.org/", "")
        if "National Bureau of Economic Research" in name or "NBER" in name:
            candidates.append(source)

    if not candidates:
        raise RuntimeError(
            "Could not find NBER in OpenAlex sources. "
            "Returned source names: "
            + ", ".join(repr(s.get("display_name")) for s in results[:5])
        )

    # Among substring matches, prefer the one with the most works
    candidates.sort(key=lambda s: s.get("works_count", 0), reverse=True)
    return candidates[0]["id"].replace("https://openalex.org/", "")


@lru_cache(maxsize=16)
def get_concept_id(query: str) -> str:
    """Look up an OpenAlex concept ID by search query. Cached."""
    _ensure_pyalex_configured()
    from pyalex import Concepts

    results = Concepts().search(query).get()
    if not results:
        raise RuntimeError(f"No concept found for query: {query!r}")
    return results[0]["id"].replace("https://openalex.org/", "")


def find_recent_nber(
    since: str = "2026-02-01",
    until: str | None = None,
    concept_query: str | None = None,
    per_page: int = 50,
) -> list[dict[str, Any]]:
    """Return recent NBER working papers matching the filters.

    Args:
        since: ISO date (YYYY-MM-DD); filters publication_date >= since
        until: ISO date; optional upper bound on publication date
        concept_query: e.g., "development economics" — filters by OpenAlex concept
        per_page: results per page (max 200)

    Returns:
        List of OpenAlex Work dicts.
    """
    _ensure_pyalex_configured()
    from pyalex import Works

    nber_id = get_nber_source_id()

    query = (
        Works()
        .filter(primary_location={"source": {"id": nber_id}})
        .filter(from_publication_date=since)
        .sort(publication_date="desc")
    )
    if until is not None:
        query = query.filter(to_publication_date=until)
    if concept_query is not None:
        concept_id = get_concept_id(concept_query)
        query = query.filter(concepts={"id": concept_id})

    return query.get(per_page=per_page)


def find_evaluation_candidates(
    since: str = "2026-02-01",
    concept_queries: tuple[str, ...] = ("development economics", "labor economics"),
    methodology_terms: tuple[str, ...] = (
        "randomized",
        "instrumental variable",
        "difference-in-differences",
        "regression discontinuity",
        "synthetic control",
    ),
    per_page: int = 50,
) -> list[dict[str, Any]]:
    """Find post-cutoff NBER papers in specified subfields whose abstracts mention
    identification keywords. Filters concept-tagged candidates by methodology
    keyword presence in the (auto-reconstructed) plaintext abstract.

    Args:
        since: ISO date for publication_date filter (default: 2026-02-01 — safety
            margin after Jan 2026 model cutoff)
        concept_queries: OpenAlex concepts to search across (one query per concept)
        methodology_terms: substrings to match in abstracts (case-insensitive)
        per_page: results per concept query

    Returns:
        Deduplicated list of candidate paper metadata.
    """
    candidates: dict[str, dict[str, Any]] = {}
    for concept in concept_queries:
        results = find_recent_nber(
            since=since, concept_query=concept, per_page=per_page
        )
        for paper in results:
            candidates[paper["id"]] = paper

    filtered = []
    for paper in candidates.values():
        abstract = paper.get("abstract") or ""
        if any(term.lower() in abstract.lower() for term in methodology_terms):
            filtered.append(paper)

    return filtered


def save_results(
    results: list[dict[str, Any]],
    query_description: str,
    output_dir: str = ".planning/research",
) -> Path:
    """Save results to the audit-trail directory with a timestamp.

    Returns the path to the saved file.
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / f"openalex-{timestamp}.json"
    payload = {
        "query_time": timestamp,
        "query_description": query_description,
        "result_count": len(results),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return output_path


def format_paper_summary(paper: dict[str, Any]) -> str:
    """Format a paper as a human-readable summary."""
    title = paper.get("display_name", "(no title)")
    date = paper.get("publication_date", "?")
    doi = paper.get("doi", "n/a")
    authors = paper.get("authorships", [])
    author_names = [a.get("author", {}).get("display_name", "?") for a in authors[:3]]
    if len(authors) > 3:
        author_names.append(f"and {len(authors) - 3} more")
    author_str = ", ".join(author_names) if author_names else "(no authors)"

    concepts = paper.get("concepts", [])[:3]
    concept_str = ", ".join(c.get("display_name", "?") for c in concepts)

    lines = [
        f"{date}: {title}",
        f"  Authors: {author_str}",
        f"  DOI: {doi}",
    ]
    if concept_str:
        lines.append(f"  Concepts: {concept_str}")
    return "\n".join(lines)
