"""Multi-source academic reference search with domain-aware routing.

Routes queries to InspireHEP (HEP family), OpenAlex (precision-filtered), and
Semantic Scholar (supplementary) based on inferred domain, then merges, dedups,
and reranks results by query coverage + recency + citations.

Output JSON keeps `results[].identifier` and `results[].title` so that the
companion `bibtex-gen --from-search` consumer continues to work.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import WorkSummary  # noqa: E402
from domain import all_domains, infer_domain, is_hep, topic_ids_for  # noqa: E402
from relevance import (  # noqa: E402
    build_relevance_note,
    dedup,
    rerank,
)
from source_inspirehep import search as inspire_search  # noqa: E402
from source_openalex import search as openalex_search  # noqa: E402
from source_semantic_scholar import search as s2_search  # noqa: E402

DEFAULT_MIN_SCORE = 0.05
DEFAULT_MIN_COVERAGE = 0.10


def _gather(
    query: str,
    *,
    mode: str,
    source: str,
    domain: str | None,
    limit: int,
    email: str | None,
    min_score: float,
    topic_ids: list[str] | None,
) -> tuple[list[WorkSummary], list[str]]:
    """Run the configured source plan; return (summaries, sources_used)."""
    used: list[str] = []
    out: list[WorkSummary] = []

    if source == "openalex":
        used.append("openalex")
        out += openalex_search(
            query, mode=mode, limit=limit, email=email,
            min_score=min_score, topic_ids=topic_ids,
        )
        return out, used

    if source == "inspire":
        used.append("inspire")
        out += inspire_search(query, mode=mode, limit=limit, email=email)
        return out, used

    if source == "semscholar":
        used.append("semscholar")
        out += s2_search(query, mode=mode, limit=limit, email=email, min_score=min_score)
        return out, used

    if source == "all":
        used += ["inspire", "openalex", "semscholar"]
        out += inspire_search(query, mode=mode, limit=limit, email=email)
        out += openalex_search(
            query, mode=mode, limit=limit, email=email,
            min_score=min_score, topic_ids=topic_ids,
        )
        out += s2_search(query, mode=mode, limit=limit, email=email, min_score=min_score)
        return out, used

    # source == "auto"
    if is_hep(domain):
        used.append("inspire")
        inspire_hits = inspire_search(query, mode=mode, limit=limit, email=email)
        out += inspire_hits
        if len(inspire_hits) < max(1, limit // 2):
            used.append("openalex")
            out += openalex_search(
                query, mode=mode, limit=limit, email=email,
                min_score=min_score, topic_ids=topic_ids,
            )
        return out, used

    used.append("openalex")
    openalex_hits = openalex_search(
        query, mode=mode, limit=limit, email=email,
        min_score=min_score, topic_ids=topic_ids,
    )
    out += openalex_hits
    if len(openalex_hits) < max(1, limit // 2):
        used.append("semscholar")
        out += s2_search(query, mode=mode, limit=limit, email=email, min_score=min_score)
    return out, used


def _dominant_themes(summaries: list[WorkSummary]) -> list[str]:
    counter: Counter[str] = Counter()
    for s in summaries:
        for c in s.concepts[:3]:
            counter[c] += 1
    return [c for c, _ in counter.most_common(3)]


def _best_starting_point(summaries: list[WorkSummary]) -> str:
    if not summaries:
        return "No clear starting paper identified."
    best = max(summaries, key=lambda s: (s.cited_by_count, s.year or 0))
    year = best.year if best.year is not None else "?"
    return f"{best.title} ({year})"


def _markdown_output(
    query: str,
    mode: str,
    domain: str | None,
    sources_used: list[str],
    summaries: list[WorkSummary],
) -> str:
    lines = [
        f'## Reference Search: "{query}"',
        "",
        f"**Mode**: {mode}",
        f"**Domain**: {domain or 'unspecified'}",
        f"**Sources**: {', '.join(sources_used) or 'none'}",
        f"**Results**: {len(summaries)}",
        "",
        "### Recommended references",
    ]
    if not summaries:
        lines += [
            "_No results found._",
            "",
            "### Synthesis",
            "- Dominant themes: unavailable",
            "- Best starting point: unavailable",
            "- Caveat: search returned no results.",
        ]
        return "\n".join(lines)

    for i, s in enumerate(summaries, 1):
        year = s.year if s.year is not None else "?"
        lines += [
            f"{i}. **{s.title}** ({year}, cited: {s.cited_by_count}, score: {s.final_score:.2f})",
            f"   - Authors: {s.authors}",
            f"   - Source: {s.source}" + (f" / {s.venue}" if s.venue else ""),
            f"   - DOI/URL: {s.identifier}",
            f"   - Why it matters: {s.relevance_note}",
            "",
        ]

    themes = _dominant_themes(summaries)
    caveat = (
        "Search looks broad; manually verify claim fit before citing."
        if len(themes) <= 1
        else "Relevance was inferred from retrieved metadata and abstract snippets."
    )
    lines += [
        "### Synthesis",
        f"- Dominant themes: {', '.join(themes) if themes else 'unavailable'}",
        f"- Best starting point: {_best_starting_point(summaries)}",
        f"- Caveat: {caveat}",
    ]
    return "\n".join(lines)


def _json_output(
    query: str,
    mode: str,
    domain: str | None,
    sources_used: list[str],
    summaries: list[WorkSummary],
) -> str:
    payload = {
        "query": query,
        "mode": mode,
        "domain": domain,
        "sources_used": sources_used,
        "count": len(summaries),
        "dominant_themes": _dominant_themes(summaries),
        "best_starting_point": _best_starting_point(summaries),
        "results": [s.to_dict() for s in summaries],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "--mode",
        choices=["background", "survey", "method", "baseline", "evaluation", "claim-support"],
        default="background",
    )
    parser.add_argument(
        "--source",
        choices=["auto", "openalex", "inspire", "semscholar", "all"],
        default="auto",
        help="Source routing (default: auto — domain-driven)",
    )
    parser.add_argument(
        "--domain",
        default="auto",
        help=f"Domain key or 'auto' for keyword inference. Known: {', '.join(all_domains())}",
    )
    parser.add_argument("--limit", type=int, default=8, help="Number of results to return (1–50)")
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help=f"Drop results with source_score below this (default: {DEFAULT_MIN_SCORE})",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=DEFAULT_MIN_COVERAGE,
        help=(
            f"Drop results whose query-term coverage is below this (default: "
            f"{DEFAULT_MIN_COVERAGE}). Set 0 to disable noise filtering."
        ),
    )
    parser.add_argument("--email", default=None, help="Email for polite-pool User-Agent")
    parser.add_argument(
        "--topic-id",
        action="append",
        default=None,
        help="OpenAlex topic ID (Txxxx). Repeatable. Overrides domain-inferred IDs.",
    )
    parser.add_argument("--format", dest="fmt", choices=["md", "json"], default="md")
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Skip relevance reranking (return source order). Diagnostic only.",
    )
    args = parser.parse_args()

    limit = min(max(1, args.limit), 50)

    if args.domain == "auto":
        domain = infer_domain(args.query)
    elif args.domain in ("", "none"):
        domain = None
    else:
        domain = args.domain

    topic_ids = args.topic_id if args.topic_id else topic_ids_for(domain)

    raw, used = _gather(
        args.query,
        mode=args.mode,
        source=args.source,
        domain=domain,
        limit=limit,
        email=args.email,
        min_score=args.min_score,
        topic_ids=topic_ids,
    )

    deduped = dedup(raw)

    if args.no_rerank:
        ranked = deduped
        for s in ranked:
            s.final_score = s.source_score
    else:
        ranked = rerank(
            args.query,
            deduped,
            drop_below_coverage=args.min_coverage,
        )

    ranked = ranked[:limit]
    for s in ranked:
        build_relevance_note(args.query, args.mode, s)

    if args.fmt == "json":
        print(_json_output(args.query, args.mode, domain, used, ranked))
    else:
        print(_markdown_output(args.query, args.mode, domain, used, ranked))


if __name__ == "__main__":
    main()
