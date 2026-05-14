"""Shared dataclasses and helpers for reference-search source modules."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WorkSummary:
    """Normalized record produced by every source.

    Fields kept compatible with bibtex-gen --from-search (it reads
    `identifier` and `title` only).
    """

    title: str
    year: int | None
    cited_by_count: int
    authors: str
    identifier: str  # DOI URL preferred; landing page or arXiv URL as fallback
    abstract: str
    concepts: list[str] = field(default_factory=list)  # topic / concept display names
    source: str = "openalex"  # "openalex" | "inspire" | "semscholar"
    source_score: float = 0.0  # raw or normalized relevance score from source
    venue: str | None = None
    arxiv_id: str | None = None
    relevance_note: str = ""  # filled in by relevance.build_relevance_note
    final_score: float = 0.0  # filled in by relevance.rerank
    matched_terms: list[str] = field(default_factory=list)
    matched_sentence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def http_get_json(
    url: str,
    *,
    email: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """GET a JSON endpoint with polite-pool User-Agent when email is provided.

    Caller is responsible for catching urllib.error.* if it wants to recover;
    on uncaught error this prints to stderr and re-raises.
    """
    req_headers = {"Accept": "application/json"}
    if email:
        req_headers["User-Agent"] = f"mailto:{email}"
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"[http] {url}\n  HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        raise
    except urllib.error.URLError as exc:
        print(f"[http] {url}\n  URL error: {exc.reason}", file=sys.stderr)
        raise
    except json.JSONDecodeError as exc:
        print(f"[http] {url}\n  JSON parse error: {exc}", file=sys.stderr)
        raise


def extract_arxiv_id(text: str | None) -> str | None:
    """Find a bare arXiv ID inside a string (URL, DOI, free text)."""
    if not text:
        return None
    import re

    m = re.search(r"\b(\d{4}\.\d{4,5})(v\d+)?\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})\b", text)
    if m:
        return m.group(1)
    return None


def normalize_doi(text: str | None) -> str | None:
    """Return a https://doi.org/... URL if a DOI is recognizable, else None."""
    if not text:
        return None
    import re

    m = re.search(r"10\.\d{4,9}/[^\s\"'<>)]+", text)
    if not m:
        return None
    return f"https://doi.org/{m.group(0)}"
