"""Relevance reranking, sentence extraction, and deduplication for reference-search."""

from __future__ import annotations

import math
import re
import string

from _common import WorkSummary

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CURRENT_YEAR = 2026
RECENCY_PEAK = CURRENT_YEAR - 3   # full score at or after this year
RECENCY_FLOOR = CURRENT_YEAR - 15  # zero score at or before this year

STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "with",
    "by", "from", "at", "is", "are", "be", "this", "that", "these", "those",
    "we", "our", "using", "use", "used", "via", "based", "it", "its", "not",
    "as", "has", "have", "been", "was", "were", "which", "their", "also",
    "into", "than", "more", "can", "do", "does",
})

MODE_PREFIXES: dict[str, str] = {
    "survey":        "Useful as broad framing",
    "baseline":      "Potential baseline / canonical comparison",
    "claim-support": "Potential evidence source",
    "evaluation":    "Potential benchmark reference",
    "method":        "Relevant method reference",
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "source":   0.50,
    "coverage": 0.35,
    "recency":  0.10,
    "citation": 0.05,
}


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def _strip_punctuation(token: str) -> str:
    """Remove leading/trailing punctuation but preserve hyphens and interior
    periods (acronyms like LCDM, f(R), N-body)."""
    return token.strip(string.punctuation.replace("-", "").replace(".", ""))


def tokenize(query: str) -> tuple[list[str], list[str]]:
    """Return (key_terms, phrases).

    Phrases from double-quoted substrings are extracted first; the remaining
    text is scanned for bigram/trigram candidates from consecutive
    non-stopword tokens.
    """
    phrases: list[str] = []

    # Extract explicit quoted phrases before other processing.
    quoted = re.findall(r'"([^"]+)"', query)
    for q in quoted:
        phrases.append(q.lower().strip())
    remainder = re.sub(r'"[^"]+"', " ", query)

    raw_tokens = remainder.split()
    cleaned: list[str] = []
    for tok in raw_tokens:
        tok = _strip_punctuation(tok)
        if not tok:
            continue
        low = tok.lower()
        if low in STOPWORDS:
            continue
        if len(low) < 2:
            continue
        cleaned.append(low)

    # Build bigrams and trigrams from cleaned non-stopword tokens.
    for n in (3, 2):
        for i in range(len(cleaned) - n + 1):
            phrase = " ".join(cleaned[i : i + n])
            # Avoid duplicating explicitly quoted phrases.
            if phrase not in phrases:
                phrases.append(phrase)

    # key_terms is the flat list of cleaned single tokens.
    key_terms = cleaned
    return key_terms, phrases


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def _word_boundary_match(term: str, text: str) -> bool:
    """True if `term` appears as a whole word in `text`."""
    return bool(re.search(r"\b" + re.escape(term) + r"\b", text))


def coverage(
    key_terms: list[str],
    phrases: list[str],
    text: str,
) -> tuple[float, list[str]]:
    """Return (coverage_score in [0,1], matched_terms list)."""
    text_lower = text.lower()
    matched: list[str] = []

    phrase_hits = 0
    for p in phrases:
        if p in text_lower:
            phrase_hits += 1
            if p not in matched:
                matched.append(p)

    term_hits = 0
    for t in key_terms:
        if _word_boundary_match(t, text_lower):
            term_hits += 1
            if t not in matched:
                matched.append(t)

    denom = max(len(phrases) * 1.5 + len(key_terms), 1)
    raw = (phrase_hits * 1.5 + term_hits) / denom
    score = max(0.0, min(1.0, raw))
    return score, matched


# ---------------------------------------------------------------------------
# Sentence extraction
# ---------------------------------------------------------------------------

def pick_relevant_sentence(
    key_terms: list[str],
    phrases: list[str],
    abstract: str,
) -> str:
    """Return the abstract sentence with the highest coverage score."""
    if not abstract or abstract.strip() in ("", "N/A"):
        return ""

    # Split on ". " or newlines; filter blanks.
    raw = re.split(r"\.\s+|\n", abstract)
    sentences = [s.strip() for s in raw if s.strip()]

    if not sentences:
        return ""

    if len(sentences) == 1:
        trunc = abstract.strip()[:250]
        if not trunc.endswith("."):
            trunc += "."
        return trunc

    best_sent = ""
    best_score = -1.0
    best_len = float("inf")

    for sent in sentences:
        sc, _ = coverage(key_terms, phrases, sent)
        if sc > best_score or (sc == best_score and len(sent) < best_len):
            best_score = sc
            best_sent = sent
            best_len = len(sent)

    result = best_sent.strip()
    if result and not result.endswith("."):
        result += "."
    return result


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _recency_score(year: int | None) -> float:
    if year is None:
        return 0.5
    if year >= RECENCY_PEAK:
        return 1.0
    if year <= RECENCY_FLOOR:
        return 0.0
    return (year - RECENCY_FLOOR) / (RECENCY_PEAK - RECENCY_FLOOR)


def _citation_score(cited_by_count: int) -> float:
    return min(1.0, math.log1p(cited_by_count) / 10.0)


# ---------------------------------------------------------------------------
# Rerank
# ---------------------------------------------------------------------------

def rerank(
    query: str,
    summaries: list[WorkSummary],
    *,
    weights: dict[str, float] | None = None,
    drop_below_coverage: float = 0.0,
) -> list[WorkSummary]:
    """Score, annotate, and sort summaries; optionally filter by coverage."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    key_terms, phrases = tokenize(query)
    results: list[WorkSummary] = []

    for s in summaries:
        combined_text = s.title + ". " + (s.abstract or "")
        cov_score, matched = coverage(key_terms, phrases, combined_text)

        if cov_score < drop_below_coverage:
            continue

        rec = _recency_score(s.year)
        cit = _citation_score(s.cited_by_count)

        s.final_score = (
            w["source"]   * s.source_score
            + w["coverage"] * cov_score
            + w["recency"]  * rec
            + w["citation"] * cit
        )
        s.matched_terms = matched
        s.matched_sentence = pick_relevant_sentence(key_terms, phrases, s.abstract or "")
        results.append(s)

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Relevance note
# ---------------------------------------------------------------------------

def build_relevance_note(
    query: str,
    mode: str,
    summary: WorkSummary,
) -> str:
    """Compose a human-useful note, set summary.relevance_note, and return it."""
    prefix = MODE_PREFIXES.get(mode, "Relevant reference")
    key_terms, phrases = tokenize(query)
    total = len(key_terms) + len(phrases)

    matched = summary.matched_terms
    n = len(matched)

    venue_part = f" / {summary.venue}" if summary.venue else ""

    if matched:
        term_list = ", ".join(matched[:5])
        match_part = f" Matched {n}/{total} key terms ({term_list})."
    else:
        match_part = ""

    note = f"{prefix}.{match_part} Source: {summary.source}{venue_part}."

    if summary.matched_sentence:
        sentence_line = f'\nFrom abstract: "{summary.matched_sentence}"'
        # Trim to keep total note < 500 chars.
        if len(note) + len(sentence_line) < 500:
            note += sentence_line
        else:
            # Truncate sentence to fit.
            budget = 497 - len(note) - len('\nFrom abstract: "..."')
            if budget > 20:
                trunc = summary.matched_sentence[:budget] + "..."
                note += f'\nFrom abstract: "{trunc}"'

    summary.relevance_note = note
    return note


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _norm_title(title: str) -> str:
    low = title.lower()
    # Remove all punctuation, collapse whitespace.
    low = re.sub(r"[^\w\s]", " ", low)
    return re.sub(r"\s+", " ", low).strip()


def dedup(summaries: list[WorkSummary]) -> list[WorkSummary]:
    """Remove duplicates; prefer higher source_score; keep original order."""
    from _common import extract_arxiv_id, normalize_doi

    seen_arxiv: dict[str, int] = {}   # arxiv_id -> index in `out`
    seen_doi:   dict[str, int] = {}   # doi -> index in `out`
    seen_title: dict[str, int] = {}   # norm_title -> index in `out`
    out: list[WorkSummary | None] = []

    for s in summaries:
        arxiv = s.arxiv_id or extract_arxiv_id(s.identifier)
        doi = normalize_doi(s.identifier)
        nt = _norm_title(s.title)

        # Find if this entry duplicates anything already in `out`.
        dup_idx: int | None = None
        if arxiv and arxiv in seen_arxiv:
            dup_idx = seen_arxiv[arxiv]
        elif doi and doi in seen_doi:
            dup_idx = seen_doi[doi]
        elif nt in seen_title:
            dup_idx = seen_title[nt]

        if dup_idx is not None:
            existing = out[dup_idx]
            # Prefer inspire source for HEP papers; otherwise prefer higher score.
            if existing is not None:
                prefer_new = (
                    (s.source == "inspire" and existing.source != "inspire")
                    or (
                        s.source == existing.source
                        and s.source_score > existing.source_score
                    )
                    or (
                        s.source != "inspire"
                        and existing.source != "inspire"
                        and s.source_score > existing.source_score
                    )
                )
                if prefer_new:
                    out[dup_idx] = s
            # Update lookup tables so they still point to dup_idx.
            if arxiv:
                seen_arxiv[arxiv] = dup_idx
            if doi:
                seen_doi[doi] = dup_idx
            seen_title[nt] = dup_idx
        else:
            idx = len(out)
            out.append(s)
            if arxiv:
                seen_arxiv[arxiv] = idx
            if doi:
                seen_doi[doi] = idx
            seen_title[nt] = idx

    return [s for s in out if s is not None]


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        WorkSummary(
            title="Dark matter halo mass function from large N-body simulations",
            year=2023, cited_by_count=42, authors="Smith et al.",
            identifier="https://doi.org/10.1234/xyz",
            abstract=(
                "We measure the halo mass function over a wide mass range. "
                "Our N-body simulations span 10 Gpc/h boxes. "
                "Calibration matches Planck cosmology within 2%."
            ),
            source="openalex", source_score=0.9,
        ),
        WorkSummary(
            title="A study of bovine respiratory disease",
            year=2020, cited_by_count=3, authors="Jones",
            identifier="https://doi.org/10.5678/abc",
            abstract="Cattle in feedlots are susceptible to respiratory disease.",
            source="openalex", source_score=0.4,
        ),
    ]
    reranked = rerank("halo mass function N-body simulation", samples)
    for r in reranked:
        print(f"[{r.final_score:.2f}] {r.title[:60]}")
        print(f"  matched: {r.matched_terms}")
        print(f"  sentence: {r.matched_sentence}")
        print()
