# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "scholarly",
# ]
# ///
"""Generate bibtex entries by routing each query to the best source.

HEP queries → InspireHEP. Non-HEP queries → Google Scholar via `scholarly`
(optional dependency) with CrossRef DOI bibtex as the publisher fallback.

Classification is automatic: a query is HEP iff InspireHEP returns a match
for it. arXiv IDs additionally check the arXiv API for hep-*/nucl-*
categories as a strong pre-signal. Use --hep / --no-hep to override.

Source-native bibtex keys are preserved verbatim; this script does NOT
rewrite keys or fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

INSPIRE_BASE = "https://inspirehep.net/api/literature"
CROSSREF_WORK = "https://api.crossref.org/works"
ARXIV_API = "http://export.arxiv.org/api/query"

ARXIV_RE = re.compile(
    r"^(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7})$",
    re.IGNORECASE,
)
ARXIV_URL_RE = re.compile(
    r"https?://arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7})",
    re.IGNORECASE,
)
DOI_RE = re.compile(
    r"^(?:doi:|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)$",
    re.IGNORECASE,
)

HEP_ARXIV_PREFIXES = ("hep-", "nucl-")
TIMEOUT = 30


@dataclass
class FetchResult:
    bibtex: str | None
    source: str
    note: str = ""


def detect_input(s: str) -> tuple[str, str]:
    """Return (kind, canonical_value). kind in {arxiv, doi, title}."""
    s = s.strip()
    m = ARXIV_URL_RE.search(s)
    if m:
        return ("arxiv", m.group(1))
    m = ARXIV_RE.match(s)
    if m:
        return ("arxiv", m.group(1))
    m = DOI_RE.match(s)
    if m:
        return ("doi", m.group(1))
    return ("title", s)


def _http_get(url: str, accept: str = "application/json") -> str | None:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "bibtex-gen/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"  ! HTTP {e.code} from {url}: {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"  ! URL error for {url}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ! Unexpected error for {url}: {e}", file=sys.stderr)
        return None


def fetch_inspirehep(query: str) -> FetchResult:
    """Hit InspireHEP with format=bibtex. Returns bibtex text or None."""
    params = urllib.parse.urlencode({"q": query, "format": "bibtex", "size": 1})
    url = f"{INSPIRE_BASE}?{params}"
    body = _http_get(url, accept="application/x-bibtex")
    if body is None:
        return FetchResult(None, "inspirehep", "request failed")
    body = body.strip()
    if not body or not body.lstrip().startswith("@"):
        return FetchResult(None, "inspirehep", "no bibtex returned")
    return FetchResult(body, "inspirehep")


def fetch_crossref(doi: str) -> FetchResult:
    """Hit CrossRef's DOI→bibtex transform endpoint."""
    safe_doi = urllib.parse.quote(doi, safe="/.-_()")
    url = f"{CROSSREF_WORK}/{safe_doi}/transform/application/x-bibtex"
    body = _http_get(url, accept="application/x-bibtex")
    if body is None:
        return FetchResult(None, "crossref", "request failed")
    body = body.strip()
    if not body.startswith("@"):
        return FetchResult(None, "crossref", "no bibtex returned")
    return FetchResult(body, "crossref")


def crossref_doi_lookup(query: str) -> str | None:
    """Resolve a free-text query to its top-ranked DOI via CrossRef search."""
    params = urllib.parse.urlencode({"query": query, "rows": 1})
    url = f"{CROSSREF_WORK}?{params}"
    body = _http_get(url, accept="application/json")
    if body is None:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    items = data.get("message", {}).get("items", []) or []
    if not items:
        return None
    return items[0].get("DOI")


def fetch_scholar(query: str) -> FetchResult:
    """Use `scholarly` to fetch the top Google Scholar hit and its bibtex.

    `scholarly` is an optional dependency. When missing, return a sentinel so
    the caller can fall through to CrossRef.
    """
    try:
        from scholarly import scholarly  # type: ignore
    except ImportError:
        return FetchResult(None, "scholar", "scholarly not installed")
    try:
        search = scholarly.search_pubs(query)
        pub = next(search, None)
    except Exception as e:
        return FetchResult(None, "scholar", f"search failed: {e}")
    if not pub:
        return FetchResult(None, "scholar", "no results")
    try:
        bibtex = scholarly.bibtex(pub)
    except Exception as e:
        return FetchResult(None, "scholar", f"bibtex fetch failed: {e}")
    if not bibtex or not bibtex.lstrip().startswith("@"):
        return FetchResult(None, "scholar", "non-bibtex response")
    return FetchResult(bibtex.strip(), "scholar")


def arxiv_categories(arxiv_id: str) -> list[str]:
    """Return list of arXiv category terms for an arXiv ID; empty on failure."""
    params = urllib.parse.urlencode({"id_list": arxiv_id})
    url = f"{ARXIV_API}?{params}"
    body = _http_get(url, accept="application/atom+xml")
    if not body:
        return []
    return re.findall(r'<category[^>]*term="([^"]+)"', body)


def is_hep_arxiv(categories: list[str]) -> bool:
    return any(c.lower().startswith(HEP_ARXIV_PREFIXES) for c in categories)


def classify(query: str, kind: str, value: str) -> tuple[bool, str]:
    """Return (is_hep, reason)."""
    if kind == "arxiv":
        cats = arxiv_categories(value)
        if cats and is_hep_arxiv(cats):
            return (True, f"arXiv categories include HEP: {cats}")
        if cats:
            # Still probe InspireHEP — some non-hep-* records are indexed there.
            pass

    probe = fetch_inspirehep(query)
    if probe.bibtex:
        return (True, "InspireHEP returned a match")
    return (False, "InspireHEP returned no match")


def generate_bibtex(query: str, force_hep: bool | None) -> tuple[FetchResult, str]:
    """Run the routing pipeline for a single query.

    Returns (final_result, classification_reason).
    """
    kind, value = detect_input(query)

    if force_hep is True:
        is_hep, reason = True, "forced via --hep"
    elif force_hep is False:
        is_hep, reason = False, "forced via --no-hep"
    else:
        is_hep, reason = classify(query, kind, value)

    if is_hep:
        result = fetch_inspirehep(query)
        if result.bibtex:
            return (result, reason)
        # InspireHEP failed despite classification — fall through.
        print(
            f"  ! InspireHEP returned no bibtex for '{query}' "
            f"despite HEP classification; falling back to non-HEP path.",
            file=sys.stderr,
        )

    # Non-HEP path: Scholar → CrossRef.
    scholar = fetch_scholar(query)
    if scholar.bibtex:
        return (scholar, reason)
    if scholar.note and scholar.note != "scholarly not installed":
        print(f"  ! Scholar: {scholar.note}", file=sys.stderr)

    doi = value if kind == "doi" else None
    if not doi:
        doi = crossref_doi_lookup(query)
    if doi:
        crossref = fetch_crossref(doi)
        if crossref.bibtex:
            return (crossref, reason)
        if crossref.note:
            print(f"  ! CrossRef: {crossref.note}", file=sys.stderr)

    return (FetchResult(None, "none", "all sources exhausted"), reason)


def load_batch(path: str) -> list[str]:
    out: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            out.append(stripped)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help="Queries: arXiv ID, DOI, or paper title. Repeat for multiple.",
    )
    parser.add_argument(
        "--batch",
        help="Path to a file with one query per line (# for comments).",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Append bibtex entries to this .bib file (default: stdout).",
    )
    parser.add_argument(
        "--hep",
        action="store_true",
        help="Force HEP routing (skip classification, go straight to InspireHEP).",
    )
    parser.add_argument(
        "--no-hep",
        action="store_true",
        help="Force non-HEP routing (skip InspireHEP, use Scholar → CrossRef).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds to sleep between batch queries (default 0.5 to be polite).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print classification reason for each entry.",
    )
    args = parser.parse_args()

    if args.hep and args.no_hep:
        parser.error("--hep and --no-hep are mutually exclusive")

    queries: list[str] = list(args.queries)
    if args.batch:
        queries.extend(load_batch(args.batch))

    if not queries:
        parser.print_help()
        return 1

    force_hep: bool | None
    if args.hep:
        force_hep = True
    elif args.no_hep:
        force_hep = False
    else:
        force_hep = None

    entries: list[str] = []
    failures: list[str] = []
    for i, q in enumerate(queries):
        if args.verbose:
            print(f"-- [{i + 1}/{len(queries)}] {q}", file=sys.stderr)
        result, reason = generate_bibtex(q, force_hep)
        if result.bibtex:
            if args.verbose:
                print(f"   source={result.source}; reason={reason}", file=sys.stderr)
            entries.append(result.bibtex.strip())
        else:
            failures.append(q)
            print(f"   ✗ no bibtex for: {q}  ({result.note})", file=sys.stderr)
        if args.sleep and i < len(queries) - 1:
            time.sleep(args.sleep)

    text = "\n\n".join(entries) + ("\n" if entries else "")
    if args.output:
        with open(args.output, "a", encoding="utf-8") as fh:
            fh.write(text)
        print(
            f"Appended {len(entries)} bibtex entr"
            f"{'y' if len(entries) == 1 else 'ies'} to {args.output}",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(text)

    if failures:
        print(f"\nFailed: {len(failures)} / {len(queries)} queries returned no bibtex.", file=sys.stderr)
        for q in failures:
            print(f"  - {q}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
