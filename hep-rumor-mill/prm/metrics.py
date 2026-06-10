"""Aggregate per-author paper records into metrics and compute cohort distributions.

Paper rows come from three sources (inspire, openalex, ss). Deduplication is done by
normalised title + year; inspire records take precedence for citations and venue data.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from . import db

# --------------------------------------------------------------------------- #
# Journal tier table
# --------------------------------------------------------------------------- #
# Each key maps to a list of canonical substrings (case-insensitive match on venue string).
JOURNAL_TIERS: dict[str, list[str]] = {
    "A": [
        "Phys.Rev.Lett.",
        "Physical review letters",
        "Nature Physics",
        "Nature Communications",
        "Nature",
        "Science",
        "Phys.Rev.X",
        "Rev.Mod.Phys.",
        # ML flagship conferences
        "NeurIPS",
        "Conference on Neural Information Processing Systems",
        "ICML",
        "International Conference on Machine Learning",
        "ICLR",
        "International Conference on Learning Representations",
    ],
    "B": [
        "JHEP",
        "Journal of High Energy Physics",
        "Phys.Rev.D",
        "Physical review. D",
        "JCAP",
        "Journal of Cosmology and Astroparticle Physics",
        "Eur.Phys.J.C",
        "Nucl.Phys.B",
        "Phys.Lett.B",
        "SciPost Phys.",
        "Astrophys.J.",
        "Mon.Not.Roy.Astron.Soc.",
        "Class.Quant.Grav.",
        "Phys.Rev.Res.",
    ],
}

# Substrings that mark an arXiv-only / preprint venue.
_PREPRINT_MARKERS = ("arxiv", "arxiv.org")


def venue_tier(venue: str | None) -> str:
    """Return 'A', 'B', 'C', or 'preprint' for a venue string.

    None, empty string, or an arXiv URL/name returns 'preprint'.
    Matching is case-insensitive substring over JOURNAL_TIERS lists.
    Anything that does not match A or B returns 'C'.
    """
    if not venue:
        return "preprint"
    v_lower = venue.lower()
    for marker in _PREPRINT_MARKERS:
        if marker in v_lower:
            return "preprint"
    for tier, substrings in JOURNAL_TIERS.items():
        for sub in substrings:
            if sub.lower() in v_lower:
                return tier
    return "C"


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
_NON_ALNUM = re.compile(r"[^a-z0-9]")


def _norm_title(t: str | None) -> str:
    """Lowercase and strip non-alphanumeric characters for deduplication."""
    if not t:
        return ""
    return _NON_ALNUM.sub("", t.lower())


def _h_index(citations: list[int]) -> int:
    """Standard h-index: largest h such that >= h papers each have >= h citations."""
    sorted_cites = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(sorted_cites, start=1):
        if c >= i:
            h = i
        else:
            break
    return h


def _top_venues(papers: list[dict], n: int = 8) -> list[list[Any]]:
    """Return [[venue, count], ...] for the n most common non-empty venues."""
    counter: Counter = Counter()
    for p in papers:
        v = p.get("venue") or ""
        if v:
            counter[v] += 1
    return [[v, c] for v, c in counter.most_common(n)]


_HEP_PREFIXES = ("hep-", "gr-qc", "astro", "nucl")
# Physics-family tokens: any field containing one of these is physics, never interdisciplinary.
# Covers arXiv categories and OpenAlex's coarse fields ("Physics and Astronomy").
_PHYSICS_TOKENS = ("physics", "astronom", "astrophys", "cosmolog", "gravit", "particle",
                   "nuclear", "quantum field", "high energy", "optics")
# Adjacent fields: genuine cross-disciplinary neighbours of a HEP theorist (computation / ML /
# data / quantitative-other). Mathematics and mathematical physics are deliberately NOT here:
# math / math-ph are standard for formal hep-th and would over-flag ordinary theorists. The
# signal we want is "does physics outside physics-and-math", e.g. ML/CS/stats/bio.
_ADJACENT_FIELDS = ("computer science", "machine learning", "artificial intelligence",
                    "statistics", "data science", "information science",
                    "computational")
# Distant fields: when these show up under a HEP person's ORCID they almost always mean an
# OpenAlex author-conflation (a different same-named person merged into the cluster), not a
# real cross-over. They are dropped before metrics and counted toward a conflation flag.
_DISTANT_FIELDS = ("biolog", "biochem", "chemistry", "crystallograph", "medicine", "medical",
                   "neuroscience", "economics", "econometrics", "materials science",
                   "environmental", "geolog", "psychology", "social science", "sociology",
                   "linguistics", "agricultur", "veterinary", "dentistry", "nursing")
_ML_SUBS = [s.lower() for s in JOURNAL_TIERS["A"]
            if any(kw in s.lower() for kw in ("neurips", "icml", "iclr", "neural", "machine", "learning", "representations"))]


def field_class(field: str | None, venue: str | None = None) -> str:
    """Classify a paper as 'physics' | 'adjacent' | 'distant' | 'unknown'.

    'adjacent' (CS/ML/maths/stats) is the genuine interdisciplinary signal for a HEP person.
    'distant' (bio/chem/crystallography/economics/...) under a HEP author's ORCID is almost
    always an OpenAlex author-conflation artefact and gets dropped before metrics.
    """
    if venue:
        v = venue.lower()
        if any(sub in v for sub in _ML_SUBS):
            return "adjacent"
    if not field:
        return "unknown"
    f = field.lower()
    if any(tok in f for tok in _PHYSICS_TOKENS) or f.startswith(_HEP_PREFIXES):
        return "physics"
    if any(tok in f for tok in _ADJACENT_FIELDS):
        return "adjacent"
    if any(tok in f for tok in _DISTANT_FIELDS):
        return "distant"
    return "unknown"


def split_conflation(works: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split OpenAlex/SS works into (kept, dropped). Dropped = 'distant'-field works, treated
    as author-conflation noise. Kept = physics / adjacent / unknown."""
    kept, dropped = [], []
    for w in works:
        if field_class(w.get("field"), w.get("venue")) == "distant":
            dropped.append(w)
        else:
            kept.append(w)
    return kept, dropped


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def compute_metrics(conn, recid: int, *, current_year: int) -> dict:
    """Compute and persist metrics for one author. Returns the metrics dict.

    Papers from all sources are deduplicated by (normalised title, year). When
    inspire and another source share the same paper, the inspire row wins for
    citations and venue. Cross-discipline breakdowns per non-inspire source are
    stored separately in `cross_disc`.
    """
    all_papers = db.get_papers(conn, recid)
    author = db.get_author(conn, recid)

    # --- Persist venue_tier for every paper row ----------------------------- #
    for p in all_papers:
        tier = venue_tier(p.get("venue"))
        db.update_paper_tier(conn, recid, p["source"], p["paper_id"], tier)
    conn.commit()

    # --- Deduplicate across sources; inspire preferred --------------------- #
    # Group by (norm_title, year). Collect one representative per group.
    inspire_papers = [p for p in all_papers if p["source"] == "inspire"]
    other_papers = [p for p in all_papers if p["source"] != "inspire"]

    # Build index of inspire records keyed by dedup key.
    dedup: dict[tuple[str, Any], dict] = {}
    for p in inspire_papers:
        key = (_norm_title(p.get("title")), p.get("year"))
        dedup[key] = p

    # Merge non-inspire records; only add if key not already present.
    for p in other_papers:
        key = (_norm_title(p.get("title")), p.get("year"))
        if key not in dedup:
            dedup[key] = p

    deduped = list(dedup.values())

    # --- Core metrics over deduped union ------------------------------------ #
    n_papers = len(deduped)
    n_first_author = sum(
        1 for p in inspire_papers if p.get("author_pos") == 1
    )
    # Large-collaboration inflation: InspireHEP papers with very long author lists (big
    # experimental / collaboration papers) inflate paper and citation counts. Surface the share
    # so the reader does not read a collaboration member as a prolific lead author.
    n_large_collab = sum(
        1 for p in inspire_papers if (p.get("n_authors") or 0) > 50
    )
    cite_list = [p.get("citations") or 0 for p in deduped]
    total_citations = sum(cite_list)
    h = _h_index(cite_list)

    top_v = _top_venues(deduped)

    # Field mix: collect all field values from all sources.
    field_counter: Counter = Counter()
    for p in all_papers:
        f = p.get("field") or ""
        if f:
            field_counter[f.lower()] += 1

    # years_since_phd
    phd_year = author.get("phd_year") if author else None
    years_since_phd = (current_year - phd_year) if phd_year else None

    # Interdisciplinary flag: true if either signal fires.
    #  (a) the author's own InspireHEP arxiv_categories include a non-physics category (cs, eess,
    #      stat, math, q-bio, econ, q-fin). This is robust even for a sparse publication record.
    #  (b) a MATERIAL share of papers are in adjacent fields (CS/ML/maths/stats) or ML venues.
    #      Distant-field works were already dropped at enrich as conflation noise, so they cannot
    #      inflate this. Require >= 2 adjacent papers and >= 15% of the record.
    cats = (author.get("arxiv_cats") or "") if author else ""
    cat_tokens = {c.strip().lower().split(".")[0] for c in cats.split(",") if c.strip()}
    # cs, eess, stat, q-bio, econ, q-fin only. math / math-ph excluded on purpose: they are
    # normal for formal hep-th and would over-flag ordinary theorists as interdisciplinary.
    interdisc_cats = bool(cat_tokens & {"cs", "eess", "stat", "q-bio", "econ", "q-fin"})
    adjacent_count = sum(
        1 for p in deduped
        if field_class(p.get("field"), p.get("venue")) == "adjacent"
    )
    interdisc_papers = adjacent_count >= 2 and n_papers > 0 and adjacent_count / n_papers >= 0.15
    interdisciplinary = int(interdisc_cats or interdisc_papers)

    # --- Per-source cross-discipline breakdown ------------------------------ #
    cross_disc: dict[str, dict] = {}
    for src in ("openalex", "orcid", "ss"):
        src_papers = [p for p in all_papers if p["source"] == src]
        if not src_papers:
            continue
        src_cites = [p.get("citations") or 0 for p in src_papers]
        cross_disc[src] = {
            "n_papers": len(src_papers),
            "total_citations": sum(src_cites),
            "h_index": _h_index(src_cites),
            "top_venues": _top_venues(src_papers),
        }

    m: dict = {
        "recid": recid,
        "n_papers": n_papers,
        "n_first_author": n_first_author,
        "n_large_collab": n_large_collab,
        "total_citations": total_citations,
        "h_index": h,
        "top_venues": top_v,
        "field_mix": dict(field_counter),
        "years_since_phd": years_since_phd,
        "interdisciplinary": interdisciplinary,
        "cross_disc": cross_disc,
    }
    db.upsert_metrics(conn, m)
    return m


def cohort_stats(metric_dicts: list[dict]) -> dict:
    """Summarise a collection of metrics dicts into cohort-level statistics.

    Returns medians, quartiles, min/max for citations, papers, h_index, and
    years_since_phd; aggregated field_mix counts; and the fraction labelled
    interdisciplinary. Each numeric sub-dict is computed over non-None values.
    """

    def _stat(values: list) -> dict:
        vals = sorted(v for v in values if v is not None)
        n = len(vals)
        if n == 0:
            return {"median": None, "q1": None, "q3": None, "min": None, "max": None}
        median = vals[n // 2] if n % 2 == 1 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        q1 = vals[n // 4]
        q3 = vals[(3 * n) // 4]
        return {"median": median, "q1": q1, "q3": q3, "min": vals[0], "max": vals[-1]}

    agg_fields: Counter = Counter()
    for m in metric_dicts:
        fm = m.get("field_mix") or {}
        for field, cnt in fm.items():
            agg_fields[field] += cnt

    n_inter = sum(1 for m in metric_dicts if m.get("interdisciplinary"))
    inter_frac = n_inter / len(metric_dicts) if metric_dicts else 0.0

    return {
        "n": len(metric_dicts),
        "citations": _stat([m.get("total_citations") for m in metric_dicts]),
        "papers": _stat([m.get("n_papers") for m in metric_dicts]),
        "h_index": _stat([m.get("h_index") for m in metric_dicts]),
        "years_since_phd": _stat([m.get("years_since_phd") for m in metric_dicts]),
        "field_mix": dict(agg_fields),
        "interdisciplinary_frac": inter_frac,
    }


def percentile_of(value: float | int | None,
                  population: list[float | int]) -> float | None:
    """Return the fraction of population <= value, expressed as 0..100.

    Returns None if value is None or population is empty.
    """
    if value is None:
        return None
    if not population:
        return None
    count = sum(1 for v in population if v <= value)
    return 100.0 * count / len(population)
