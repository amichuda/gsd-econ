---
name: openalex-search
description: "Search OpenAlex for academic papers using the pyalex Python library. Specialized for finding economics papers — particularly NBER working papers — by JEL code, date range, methodology keywords, and other filters. Use when the user wants to find recent papers matching specific criteria for literature review, evaluation, or replication candidates."
license: MIT
---

# openalex-search

A skill for programmatic search of OpenAlex via the pyalex Python library. OpenAlex is an open index of ~250M scholarly works with a clean REST API and CC0 data licensing. This skill wraps the common search patterns relevant to empirical economics research.

## When to use this skill

- Finding recent papers in a specific subfield (e.g., "development economics RCTs posted in the last six months")
- Identifying NBER working papers by JEL code and date
- Looking up a specific paper by DOI or title to get full metadata
- Building a candidate list of papers to use for evaluation (e.g., the framework evaluation discussed in `docs/meta-cognition.md`)
- Replicating literature scout output that the `econ-researcher` agent typically produces, when more direct programmatic search is needed

## When NOT to use this skill

- For pre-cutoff papers where you just need a citation — the `econ-researcher` agent's web search is fine.
- For deep semantic understanding of a paper's contribution — OpenAlex gives you metadata and abstract; you still have to read the paper.
- When you need to verify a citation matches a specific claim — use the `polish-citations` agent's existing logic, which handles claim verification.

## Setup

```bash
pip install pyalex
```

OpenAlex requires an API key as of **February 13, 2026**. Without one, you're capped at 100 credits/day, which OpenAlex describes as for "testing/demos only." For real use, get a free key at <https://openalex.org/> and set it:

```python
import pyalex
pyalex.config.api_key = "your-key-here"
pyalex.config.email = "you@example.com"  # also recommended; gets you the "polite pool" with faster responses
```

Best practice: load both from environment variables, never hard-code them.

```python
import os
import pyalex
pyalex.config.api_key = os.environ.get("OPENALEX_API_KEY")
pyalex.config.email = os.environ.get("OPENALEX_EMAIL")
```

## Core patterns

### Find recent NBER working papers by JEL code

NBER's OpenAlex source ID needs to be looked up the first time (the API uses internal IDs, not names). The skill caches it after first lookup.

```python
from pyalex import Sources, Works

# One-time: find NBER's source ID
nber_sources = Sources().search("National Bureau of Economic Research").get()
# NBER's main source has display_name == "National Bureau of Economic Research" (working paper series)
nber_id = None
for s in nber_sources:
    if "National Bureau of Economic Research" in s.get("display_name", ""):
        nber_id = s["id"].replace("https://openalex.org/", "")
        break

# Now search for recent NBER papers
recent_nber = (
    Works()
    .filter(primary_location={"source": {"id": nber_id}})
    .filter(from_publication_date="2026-02-01")
    .sort(publication_date="desc")
    .get(per_page=25)
)

for paper in recent_nber:
    print(f"{paper['publication_date']}: {paper['display_name']}")
```

### Search by keyword and methodology

OpenAlex's `search` is full-text against title and abstract.

```python
from pyalex import Works

# Development economics RCT papers, recent
results = (
    Works()
    .search("randomized controlled trial development economics")
    .filter(from_publication_date="2026-02-01")
    .filter(to_publication_date="2026-05-10")
    .sort(publication_date="desc")
    .get(per_page=50)
)
```

### Filter by JEL code

OpenAlex doesn't expose JEL codes directly. Two workarounds:

1. **Concept filter:** OpenAlex tags works with concepts that roughly map to JEL areas. Look up concept IDs first:
   ```python
   from pyalex import Concepts
   dev_econ = Concepts().search("development economics").get()
   labor_econ = Concepts().search("labor economics").get()
   # Use the first result's id
   ```
2. **Full-text on JEL string in abstract:** less precise but no concept lookup needed.

Combine with NBER source filter for "NBER WPs in development":

```python
from pyalex import Works
results = (
    Works()
    .filter(primary_location={"source": {"id": nber_id}})
    .filter(concepts={"id": dev_econ_concept_id})
    .filter(from_publication_date="2026-02-01")
    .get(per_page=50)
)
```

### Get the plaintext abstract

OpenAlex stores abstracts as inverted indexes (token → positions). pyalex converts on the fly:

```python
work = Works()["W2741809807"]  # by OpenAlex ID
abstract = work["abstract"]  # auto-reconstructed plaintext
```

### Look up a paper by DOI

```python
work = Works()["https://doi.org/10.3386/w34836"]  # NBER DOIs use the w<number> pattern
```

### Paginate large result sets

```python
from pyalex import Works
from itertools import chain

query = (
    Works()
    .search("randomized controlled trial")
    .filter(from_publication_date="2026-02-01")
)
for record in chain(*query.paginate(per_page=200, n_max=1000)):
    process(record)
```

## A complete worked example: finding evaluation candidates

This is the realistic use case for the framework's v0 evaluation: find a post-cutoff NBER working paper in development or labor economics that has a public replication archive.

```python
import os
import pyalex
from pyalex import Sources, Works, Concepts

pyalex.config.api_key = os.environ["OPENALEX_API_KEY"]
pyalex.config.email = os.environ["OPENALEX_EMAIL"]

# Step 1: find NBER source ID (cache this; it's stable)
nber = Sources().search("National Bureau of Economic Research").get()
nber_id = next(
    s["id"].replace("https://openalex.org/", "")
    for s in nber
    if s.get("display_name") == "National Bureau of Economic Research"
)

# Step 2: find concept IDs for the subfields we want
dev_econ = Concepts().search("development economics").get()[0]
labor_econ = Concepts().search("labor economics").get()[0]

# Step 3: query for post-cutoff NBER WPs in those subfields
candidates = []
for concept in [dev_econ, labor_econ]:
    cid = concept["id"].replace("https://openalex.org/", "")
    results = (
        Works()
        .filter(primary_location={"source": {"id": nber_id}})
        .filter(concepts={"id": cid})
        .filter(from_publication_date="2026-02-01")
        .sort(publication_date="desc")
        .get(per_page=50)
    )
    candidates.extend(results)

# Step 4: filter for papers with abstracts mentioning identification keywords
methodology_terms = [
    "randomized",
    "instrumental variable",
    "difference-in-differences",
    "regression discontinuity",
    "synthetic control",
]
filtered = []
for paper in candidates:
    abstract = paper.get("abstract", "") or ""
    if any(term.lower() in abstract.lower() for term in methodology_terms):
        filtered.append(paper)

# Step 5: print candidate list
for paper in filtered:
    print(f"  {paper['publication_date']}: {paper['display_name']}")
    print(f"    DOI: {paper.get('doi', 'n/a')}")
    print(f"    Concepts: {[c['display_name'] for c in paper.get('concepts', [])[:3]]}")
    print()
```

## Limitations to know

OpenAlex tagging is imperfect — papers can be missing concept tags, or have tags that don't quite match their substance. The query above is a *starting point*, not a final filter. Plan to read 15-30 candidates' abstracts to find 3-5 that match what you actually want.

OpenAlex's abstract field is sometimes empty, sometimes a stub. For NBER papers, the canonical source for full metadata is NBER's own weekly-updated metadata feed at `https://www.nber.org/research/data/nber-working-papers-and-chapters-metadata`. If you find OpenAlex's coverage of recent NBER papers thin, switch to that feed (CSV download, parse with pandas).

There's no JEL filter in OpenAlex directly; the concept-based proxy is approximate. If JEL filtering is critical, the NBER metadata feed has authoritative JEL codes.

API rate limits matter for batch queries. 100 requests/sec is the hard ceiling; the credit-per-day quotas depend on your plan. Use `paginate()` with reasonable `per_page` (50-200) rather than many small queries.

## Output discipline

When this skill returns candidate papers, save the results to `.planning/research/openalex-<timestamp>.json` so the audit trail captures what was retrieved and when. This matters because OpenAlex updates regularly — the same query a month from now will return different results.

```python
import json
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).isoformat()
output_path = f".planning/research/openalex-{timestamp}.json"
with open(output_path, "w") as f:
    json.dump({"query_time": timestamp, "results": filtered}, f, indent=2)
```

This is the same audit-trail discipline as the rest of the framework — any data retrieval from an external source gets timestamped and saved.

## Honest scope of what this skill does

It searches a metadata index. It does not:
- Read the full text of papers (download the PDF yourself, or use the `polish-citations` agent's web-fetch logic).
- Run an identification critique on retrieved papers (that's `identification-checker`'s job).
- Filter by replication-archive availability (no metadata field for this; check the paper's first page or author website).
- Detect duplicate publications across venues (some NBER WPs become journal articles; OpenAlex sometimes lists both).

The skill is a *targeted search* — get me a candidate list. Everything after that is the human's call or another agent's job.

## References

- pyalex library: <https://github.com/J535D165/pyalex>
- OpenAlex API docs: <https://docs.openalex.org/>
- OpenAlex filter reference: <https://docs.openalex.org/api-entities/works/filter-works>
- NBER's authoritative metadata feed (alternative source): <https://www.nber.org/research/data/nber-working-papers-and-chapters-metadata>
- Rate limit and authentication info: <https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication>
