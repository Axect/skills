# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber", "httpx", "feedparser"]
# ///
"""Extract a paper's text + metadata from an arXiv ID/URL, a PDF, or a text file.

Produces a single working directory containing ``source.md`` (a metadata front
block followed by the full extracted text) and prints a JSON summary to stdout
so the calling skill knows the slug, title, output paths, and source type.

Usage:
    uv run extract_text.py <input> [--out-dir DIR]

<input> can be:
    - an arXiv id            2401.00001  /  2401.00001v2  /  hep-ph/0101001
    - an arXiv URL           https://arxiv.org/abs/2401.00001
    - a local PDF path       ./paper.pdf
    - a local text/markdown  ./notes.md  ./draft.txt

If --out-dir is omitted it defaults to ./reviews/<slug>/ under the cwd.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ARXIV_NEW = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
ARXIV_OLD = re.compile(r"^[a-z-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$")
ARXIV_IN_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?(?:[?#].*)?$")


def slugify(text: str) -> str:
    s = re.sub(r"[^\w.-]+", "_", text.strip())
    return s.strip("_")[:80] or "review"


def title_from_text(text: str) -> str:
    """Prefer a leading YAML front-matter ``title:``; fall back to the first H1."""
    if text.lstrip().startswith("---"):
        body = text.lstrip()[3:]
        end = body.find("\n---")
        if end != -1:
            front = body[:end]
            m = re.search(r"^title:\s*(.+)$", front, flags=re.MULTILINE)
            if m:
                return m.group(1).strip().strip("\"'")
    m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if m:
        return re.sub(r"\s*\{#.*\}\s*$", "", m.group(1)).strip()
    return ""


def detect_kind(arg: str) -> str:
    low = arg.lower()
    if "arxiv.org/" in low:
        return "arxiv"
    if ARXIV_NEW.match(arg) or ARXIV_OLD.match(arg):
        return "arxiv"
    p = Path(arg)
    if p.suffix.lower() == ".pdf":
        return "pdf"
    if p.suffix.lower() in (".md", ".txt", ".markdown", ".text"):
        return "text"
    # Fall back: existing file -> treat by content, else assume arxiv-ish token
    if p.exists():
        return "pdf" if p.suffix.lower() == ".pdf" else "text"
    raise SystemExit(f"Cannot determine input type for: {arg!r}")


def arxiv_id_from(arg: str) -> str:
    m = ARXIV_IN_URL.search(arg)
    if m:
        return m.group(1)
    return arg


def fetch_arxiv(arxiv_id: str, out_dir: Path) -> dict:
    import feedparser
    import httpx

    meta = {"arxiv_id": arxiv_id, "title": "", "authors": [], "categories": [], "published": ""}

    # trust_env=False avoids socks:// proxy errors in some environments.
    with httpx.Client(trust_env=False, timeout=30, follow_redirects=True) as client:
        try:
            api = client.get(
                "https://export.arxiv.org/api/query",
                params={"id_list": arxiv_id, "max_results": 1},
            )
            feed = feedparser.parse(api.text)
            if feed.entries:
                e = feed.entries[0]
                meta["title"] = re.sub(r"\s+", " ", e.get("title", "")).strip()
                meta["authors"] = [a.get("name", "") for a in e.get("authors", [])]
                meta["categories"] = [t.get("term", "") for t in e.get("tags", [])]
                meta["published"] = e.get("published", "")[:10]
        except Exception as exc:  # metadata is best-effort
            print(f"[warn] arXiv metadata fetch failed: {exc}", file=sys.stderr)

        pdf_path = out_dir / "source.pdf"
        url = f"https://arxiv.org/pdf/{arxiv_id}"
        r = client.get(url)
        r.raise_for_status()
        pdf_path.write_bytes(r.content)

    text = extract_pdf_text(pdf_path)
    return {"meta": meta, "text": text}


def extract_pdf_text(pdf_path: Path) -> str:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
    return "\n\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="arXiv id/URL, PDF path, or text/markdown path")
    ap.add_argument("--out-dir", default=None, help="working directory (default ./reviews/<slug>)")
    args = ap.parse_args()

    kind = detect_kind(args.input)

    meta = {"arxiv_id": "", "title": "", "authors": [], "categories": [], "published": ""}
    if kind == "arxiv":
        arxiv_id = arxiv_id_from(args.input)
        slug = slugify(arxiv_id)
    elif kind == "pdf":
        slug = slugify(Path(args.input).stem)
    else:
        slug = slugify(Path(args.input).stem)

    out_dir = Path(args.out_dir) if args.out_dir else Path.cwd() / "reviews" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    if kind == "arxiv":
        got = fetch_arxiv(arxiv_id_from(args.input), out_dir)
        meta.update(got["meta"])
        text = got["text"]
    elif kind == "pdf":
        text = extract_pdf_text(Path(args.input))
        meta["title"] = Path(args.input).stem
    else:
        text = Path(args.input).read_text(encoding="utf-8", errors="replace")
        meta["title"] = title_from_text(text) or Path(args.input).stem

    source_md = out_dir / "source.md"
    header_lines = ["---"]
    for k in ("arxiv_id", "title", "published"):
        if meta.get(k):
            header_lines.append(f"{k}: {meta[k]}")
    if meta.get("authors"):
        header_lines.append("authors: " + "; ".join(meta["authors"]))
    if meta.get("categories"):
        header_lines.append("categories: " + ", ".join(meta["categories"]))
    header_lines.append(f"source_type: {kind}")
    header_lines.append("---\n")
    source_md.write_text("\n".join(header_lines) + text, encoding="utf-8")

    summary = {
        "slug": slug,
        "kind": kind,
        "title": meta.get("title", ""),
        "authors": meta.get("authors", []),
        "categories": meta.get("categories", []),
        "published": meta.get("published", ""),
        "arxiv_id": meta.get("arxiv_id", ""),
        "out_dir": str(out_dir),
        "source_md": str(source_md),
        "n_chars": len(text),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
