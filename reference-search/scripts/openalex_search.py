"""Search OpenAlex and format results for citation-oriented workflows."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from typing import Any

BASE_URL = "https://api.openalex.org/works"
DEFAULT_SELECT = (
    "id,display_name,title,publication_year,cited_by_count,doi,primary_location,"
    "authorships,abstract_inverted_index,concepts"
)


@dataclass
class WorkSummary:
    title: str
    year: int | None
    cited_by_count: int
    authors: str
    identifier: str
    abstract: str
    relevance_note: str
    concepts: list[str]


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None, max_sentences: int = 2) -> str:
    if not inverted_index:
        return "N/A"
    size = max(pos for positions in inverted_index.values() for pos in positions) + 1
    tokens: list[str] = [""] * size
    for word, positions in inverted_index.items():
        for pos in positions:
            tokens[pos] = word
    full_text = " ".join(token for token in tokens if token)
    sentences = [part.strip() for part in full_text.split(". ") if part.strip()]
    return ". ".join(sentences[:max_sentences]) or full_text[:400] or "N/A"


def build_url(query: str, sort: str, limit: int, filter_str: str, select: str) -> str:
    params: dict[str, str] = {
        "search": query,
        "sort": sort,
        "per-page": str(limit),
        "select": select,
    }
    if filter_str:
        params["filter"] = filter_str
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def fetch_results(url: str, email: str | None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if email:
        headers["User-Agent"] = f"mailto:{email}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"URL error: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)


def format_authors(authorships: list[dict[str, Any]] | None) -> str:
    if not authorships:
        return "Unknown"
    names = [((entry.get("author") or {}).get("display_name") or "Unknown") for entry in authorships[:3]]
    if len(authorships) == 1:
        return names[0]
    if len(authorships) == 2:
        return " and ".join(names[:2])
    return f"{names[0]} et al."


def identifier_for(work: dict[str, Any]) -> str:
    doi = work.get("doi")
    if doi:
        return doi
    primary_location = work.get("primary_location") or {}
    source_url = primary_location.get("landing_page_url") or primary_location.get("pdf_url")
    if source_url:
        return source_url
    return work.get("id") or "N/A"


def top_concepts(work: dict[str, Any]) -> list[str]:
    concepts = work.get("concepts") or []
    ranked = sorted(
        (concept for concept in concepts if concept.get("display_name")),
        key=lambda item: item.get("score", 0),
        reverse=True,
    )
    return [concept["display_name"] for concept in ranked[:5]]


def make_relevance_note(query: str, mode: str, abstract: str, concepts: list[str], year: int | None) -> str:
    concept_text = ", ".join(concepts[:3]) if concepts else "related concepts unavailable"
    if abstract == "N/A":
        abstract_hint = "Abstract unavailable; relevance inferred from title and metadata."
    else:
        abstract_hint = abstract[:220].strip()
        if len(abstract) > 220:
            abstract_hint += "..."

    if mode == "survey":
        prefix = "Useful as broad framing"
    elif mode == "baseline":
        prefix = "Potential baseline or canonical comparison"
    elif mode == "claim-support":
        prefix = "Potential evidence source"
    elif mode == "evaluation":
        prefix = "Potential benchmark or evaluation reference"
    elif mode == "method":
        prefix = "Relevant method reference"
    else:
        prefix = "Relevant background reference"

    recency = f" Published in {year}." if year else ""
    return f"{prefix} for '{query}' via concepts: {concept_text}.{recency} {abstract_hint}".strip()


def summarize_results(query: str, mode: str, data: dict[str, Any]) -> list[WorkSummary]:
    results = data.get("results", [])
    summaries: list[WorkSummary] = []
    for work in results:
        title = work.get("display_name") or work.get("title") or "Untitled"
        year = work.get("publication_year")
        cited_by_count = work.get("cited_by_count") or 0
        authors = format_authors(work.get("authorships"))
        identifier = identifier_for(work)
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        concepts = top_concepts(work)
        relevance_note = make_relevance_note(query, mode, abstract, concepts, year)
        summaries.append(
            WorkSummary(
                title=title,
                year=year,
                cited_by_count=cited_by_count,
                authors=authors,
                identifier=identifier,
                abstract=abstract,
                relevance_note=relevance_note,
                concepts=concepts,
            )
        )
    return summaries


def dominant_themes(summaries: list[WorkSummary]) -> list[str]:
    counter: Counter[str] = Counter()
    for summary in summaries:
        for concept in summary.concepts[:3]:
            counter[concept] += 1
    return [concept for concept, _ in counter.most_common(3)]


def best_starting_point(summaries: list[WorkSummary]) -> str:
    if not summaries:
        return "No clear starting paper identified."
    best = max(summaries, key=lambda item: (item.cited_by_count, item.year or 0))
    year = best.year if best.year is not None else "?"
    return f"{best.title} ({year})"


def markdown_output(query: str, mode: str, filter_str: str, sort: str, summaries: list[WorkSummary]) -> str:
    lines = [
        f'## Reference Search: "{query}"',
        "",
        f"**Mode**: {mode}",
        f"**Filter**: {filter_str or 'none'}",
        f"**Sort**: {sort}",
        f"**Results reviewed**: {len(summaries)}",
        "",
        "### Recommended references",
    ]

    if not summaries:
        lines += ["_No results found._", "", "### Synthesis", "- Dominant themes: unavailable", "- Best starting point: unavailable", "- Caveat: search returned no results."]
        return "\n".join(lines)

    for index, summary in enumerate(summaries, 1):
        year = summary.year if summary.year is not None else "?"
        lines += [
            f"{index}. **{summary.title}** ({year}, cited: {summary.cited_by_count})",
            f"   - Authors: {summary.authors}",
            f"   - DOI/URL: {summary.identifier}",
            f"   - Why it matters: {summary.relevance_note}",
            "",
        ]

    themes = dominant_themes(summaries)
    caveat = "Search looks broad; manually verify claim fit before citing." if len(themes) <= 1 else "Relevance was inferred from retrieved metadata and abstract snippets."
    lines += [
        "### Synthesis",
        f"- Dominant themes: {', '.join(themes) if themes else 'unavailable'}",
        f"- Best starting point: {best_starting_point(summaries)}",
        f"- Caveat: {caveat}",
    ]
    return "\n".join(lines)


def json_output(query: str, mode: str, filter_str: str, sort: str, summaries: list[WorkSummary]) -> str:
    payload = {
        "query": query,
        "mode": mode,
        "filter": filter_str,
        "sort": sort,
        "count": len(summaries),
        "dominant_themes": dominant_themes(summaries),
        "best_starting_point": best_starting_point(summaries),
        "results": [summary.__dict__ for summary in summaries],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "--mode",
        choices=["background", "survey", "method", "baseline", "evaluation", "claim-support"],
        default="background",
        help="Citation use mode",
    )
    parser.add_argument(
        "--filter",
        dest="filter_str",
        default="publication_year:>2021,type:article|review",
        help="OpenAlex filter string",
    )
    parser.add_argument(
        "--sort",
        default="relevance_score:desc",
        help="Sort field (for example: relevance_score:desc or cited_by_count:desc)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of results (1-50)")
    parser.add_argument("--email", default=None, help="Email for the OpenAlex polite pool")
    parser.add_argument("--select", default=DEFAULT_SELECT, help="Comma-separated fields to request")
    parser.add_argument("--format", dest="fmt", choices=["json", "md"], default="md")
    args = parser.parse_args()

    limit = min(max(1, args.limit), 50)
    url = build_url(args.query, args.sort, limit, args.filter_str, args.select)
    data = fetch_results(url, args.email)
    summaries = summarize_results(args.query, args.mode, data)

    if args.fmt == "json":
        print(json_output(args.query, args.mode, args.filter_str, args.sort, summaries))
    else:
        print(markdown_output(args.query, args.mode, args.filter_str, args.sort, summaries))


if __name__ == "__main__":
    main()
