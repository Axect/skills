# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber", "httpx", "feedparser"]
# ///
"""Extract a paper's text + metadata (+ real figures) from an arXiv ID/URL, a
PDF, a text file, or a local LaTeX source (a ``.tex`` file or a project dir).

Produces a single working directory containing ``source.md`` (a metadata front
block followed by the full extracted text) and prints a JSON summary to stdout
so the calling skill knows the slug, title, output paths, and source type.

When the paper's LaTeX source is available (arXiv e-print tarball, or a local
``.tex`` / project directory), the figures referenced by the source are
harvested into ``<out_dir>/figures/paper/`` as PNGs and indexed, with their
captions and labels, in ``<out_dir>/figures_manifest.json``. This lets the
review embed the paper's actual figures, not just generated infographics.

Usage:
    uv run extract_text.py <input> [--out-dir DIR]

<input> can be:
    - an arXiv id            2401.00001  /  2401.00001v2  /  hep-ph/0101001
    - an arXiv URL           https://arxiv.org/abs/2401.00001
    - a local PDF path       ./paper.pdf
    - a local text/markdown  ./notes.md  ./draft.txt
    - a local LaTeX source   ./main.tex  /  ./paper_project_dir/

If --out-dir is omitted it defaults to ./reviews/<slug>/ under the cwd.
"""

import argparse
import gzip
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ARXIV_NEW = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
ARXIV_OLD = re.compile(r"^[a-z-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$")
ARXIV_IN_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?(?:[?#].*)?$")

# Graphics extensions LaTeX figures commonly reference.
GRAPHICS_EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps")
RASTER_EXTS = (".png", ".jpg", ".jpeg")
MAX_FIGURES = 40  # cap conversions to avoid pathological source trees


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


def title_from_tex(tex: str) -> str:
    m = re.search(r"\\title\s*(?:\[[^\]]*\])?\s*\{", tex)
    if m:
        raw = extract_braced(tex, m.end() - 1)
        if raw:
            # strip latex commands / comments, collapse whitespace
            raw = re.sub(r"%.*", "", raw)
            raw = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", raw)
            raw = raw.replace("{", " ").replace("}", " ")
            return re.sub(r"\s+", " ", raw).strip()
    return ""


def detect_kind(arg: str) -> str:
    low = arg.lower()
    if "arxiv.org/" in low:
        return "arxiv"
    if ARXIV_NEW.match(arg) or ARXIV_OLD.match(arg):
        return "arxiv"
    p = Path(arg)
    if p.is_dir():
        return "latex"
    if p.suffix.lower() == ".tex":
        return "latex"
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


# ----------------------------------------------------------------------------
# LaTeX figure harvesting
# ----------------------------------------------------------------------------

def extract_braced(text: str, open_idx: int) -> str:
    """Return the content of a brace group whose opening ``{`` is at open_idx.

    Handles nested braces (e.g. math, \\frac{}{}). Returns "" if unbalanced.
    """
    if open_idx >= len(text) or text[open_idx] != "{":
        return ""
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1 : i]
    return ""


def _clean_caption(raw: str) -> str:
    """Best-effort flatten of a LaTeX caption to plain text."""
    s = re.sub(r"%.*", "", raw)
    # drop \label{...} inside captions
    s = re.sub(r"\\label\s*\{[^}]*\}", "", s)
    # \cite{...}, \ref{...} -> drop
    s = re.sub(r"\\(?:cite|ref|eqref|citep|citet)\s*\{[^}]*\}", "", s)
    # \textbf{x}/\emph{x}/\text{x} -> x  (a couple of passes for light nesting)
    for _ in range(3):
        s = re.sub(r"\\[a-zA-Z]+\*?\s*\{([^{}]*)\}", r"\1", s)
    # remaining bare commands -> space
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def strip_tex_comments(tex: str) -> str:
    """Remove LaTeX line comments (unescaped % to end of line)."""
    return re.sub(r"(?<!\\)%.*", "", tex)


def parse_tex_figures(tex: str) -> list[dict]:
    """Parse figure environments into per-graphic {graphic, caption, label}.

    Within a block each ``\\includegraphics`` is paired with the nearest
    following ``\\caption`` (so subfigure subcaptions map correctly); if none
    follows, the block's last caption (the outer one) is used. Commented-out
    LaTeX is ignored.
    """
    tex = strip_tex_comments(tex)
    records: list[dict] = []
    for fm in re.finditer(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", tex, flags=re.DOTALL):
        block = fm.group(1)
        graphics = [
            (m.start(), m.group(1).strip())
            for m in re.finditer(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}", block)
        ]
        if not graphics:
            continue
        captions = [
            (m.start(), _clean_caption(extract_braced(block, m.end() - 1)))
            for m in re.finditer(r"\\caption\s*(?:\[[^\]]*\])?\s*\{", block)
        ]
        lm = re.search(r"\\label\s*\{([^}]*)\}", block)
        label = lm.group(1).strip() if lm else ""

        for pos, ref in graphics:
            caption = ""
            after = [c for cp, c in captions if cp > pos]
            if after:
                caption = after[0]
            elif captions:
                caption = captions[-1][1]
            records.append({"graphic": ref, "caption": caption, "label": label})
    return records


def _resolve_graphic(ref: str, src_dir: Path, all_graphics: dict[str, Path]) -> Path | None:
    """Resolve an \\includegraphics path (often extensionless) to a real file."""
    ref = ref.lstrip("./").strip()
    cand = (src_dir / ref)
    # exact (with ext)
    if cand.suffix.lower() in GRAPHICS_EXTS and cand.exists():
        return cand
    # try adding known extensions
    for ext in GRAPHICS_EXTS:
        if (src_dir / (ref + ext)).exists():
            return src_dir / (ref + ext)
    # match by basename stem against harvested graphics
    stem = Path(ref).name.lower()
    if stem in all_graphics:
        return all_graphics[stem]
    stem_noext = Path(ref).stem.lower()
    for key, p in all_graphics.items():
        if Path(key).stem == stem_noext:
            return p
    return None


def convert_to_png(src: Path, dst: Path) -> Path | None:
    """Render/copy a graphics file to PNG at dst (a .png path).

    Returns the path actually written, or None on failure. ``.png`` is copied
    as-is; other rasters and vectors are converted to ``dst`` when a tool is
    available. If no converter exists, a non-png raster is copied verbatim
    (keeping its extension) and that path is returned.
    """
    ext = src.suffix.lower()
    if ext == ".png":
        try:
            shutil.copyfile(src, dst)
            return dst
        except Exception as exc:
            print(f"[warn] copy failed for {src.name}: {exc}", file=sys.stderr)
            return None

    # pdf -> pdftoppm is the cleanest
    if ext == ".pdf" and shutil.which("pdftoppm"):
        try:
            subprocess.run(
                ["pdftoppm", "-png", "-r", "150", "-singlefile", str(src), str(dst.with_suffix(""))],
                check=True, capture_output=True, timeout=120,
            )
            if dst.exists():
                return dst
        except Exception as exc:
            print(f"[warn] pdftoppm failed for {src.name}: {exc}", file=sys.stderr)

    # general raster/vector -> imagemagick or ghostscript
    for tool in ("magick", "convert"):
        if shutil.which(tool):
            try:
                subprocess.run(
                    [tool, "-density", "150", str(src), "-background", "white",
                     "-alpha", "remove", str(dst)],
                    check=True, capture_output=True, timeout=120,
                )
                if dst.exists():
                    return dst
            except Exception as exc:
                print(f"[warn] {tool} failed for {src.name}: {exc}", file=sys.stderr)

    if ext in (".pdf", ".eps", ".ps") and shutil.which("gs"):
        try:
            subprocess.run(
                ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", "-r150",
                 f"-sOutputFile={dst}", str(src)],
                check=True, capture_output=True, timeout=120,
            )
            if dst.exists():
                return dst
        except Exception as exc:
            print(f"[warn] gs failed for {src.name}: {exc}", file=sys.stderr)

    # last resort: a raster we could not transcode -> copy verbatim
    if ext in RASTER_EXTS:
        try:
            out = dst.with_suffix(ext)
            shutil.copyfile(src, out)
            return out
        except Exception as exc:
            print(f"[warn] copy failed for {src.name}: {exc}", file=sys.stderr)

    return None


def harvest_figures(src_dir: Path, out_dir: Path) -> list[dict]:
    """Convert source graphics to PNG and index them with tex captions/labels."""
    paper_dir = out_dir / "figures" / "paper"

    # gather all graphics files in the source tree
    all_graphics: dict[str, Path] = {}
    for p in sorted(src_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in GRAPHICS_EXTS:
            all_graphics.setdefault(p.name.lower(), p)

    if not all_graphics:
        return []

    # parse captions/labels from every .tex
    fig_records: list[dict] = []
    for tex_path in sorted(src_dir.rglob("*.tex")):
        try:
            fig_records.extend(parse_tex_figures(tex_path.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            continue

    # build resolved-graphic -> (caption, label), in tex order
    meta_by_file: dict[Path, dict] = {}
    used: set[Path] = set()
    ordered: list[Path] = []
    for rec in fig_records:
        resolved = _resolve_graphic(rec["graphic"], src_dir, all_graphics)
        if resolved is None:
            continue
        used.add(resolved)
        if resolved not in ordered:
            ordered.append(resolved)
        # first non-empty caption wins
        if resolved not in meta_by_file or (not meta_by_file[resolved]["caption"] and rec["caption"]):
            meta_by_file[resolved] = {"caption": rec["caption"], "label": rec["label"]}
    for p in all_graphics.values():
        if p not in ordered:
            ordered.append(p)

    if len(ordered) > MAX_FIGURES:
        print(f"[warn] {len(ordered)} figures found; converting first {MAX_FIGURES}.", file=sys.stderr)
        ordered = ordered[:MAX_FIGURES]

    paper_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    seen_png: set[str] = set()
    for src in ordered:
        stem = slugify(src.stem)
        png_name = f"{stem}.png"
        # avoid collisions
        n = 1
        while png_name in seen_png:
            png_name = f"{stem}_{n}.png"
            n += 1
        seen_png.add(png_name)
        dst = paper_dir / png_name
        out = convert_to_png(src, dst)
        info = meta_by_file.get(src, {"caption": "", "label": ""})
        manifest.append({
            "src": str(src.relative_to(src_dir)) if src.is_relative_to(src_dir) else src.name,
            "png": f"figures/paper/{out.name}" if out is not None else "",
            "label": info["label"],
            "caption": info["caption"],
            "used_in_tex": src in used,
            "converted": out is not None,
        })

    (out_dir / "figures_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


# ----------------------------------------------------------------------------
# LaTeX source assembly (local .tex / dir)
# ----------------------------------------------------------------------------

def _find_main_tex(src_dir: Path) -> Path | None:
    candidates = [p for p in src_dir.rglob("*.tex")
                  if "\\documentclass" in p.read_text(encoding="utf-8", errors="replace")[:4000]]
    if not candidates:
        return None
    # prefer shallowest, then shortest name
    candidates.sort(key=lambda p: (len(p.relative_to(src_dir).parts), len(p.name)))
    return candidates[0]


def assemble_latex_text(src_dir: Path) -> str:
    """Build a readable text body from a LaTeX project (expand \\input/\\include)."""
    main = _find_main_tex(src_dir)
    if main is None:
        # no documentclass: concatenate all .tex sorted
        parts = []
        for p in sorted(src_dir.rglob("*.tex")):
            parts.append(f"\n\n% ===== {p.relative_to(src_dir)} =====\n")
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
        return "".join(parts)

    visited: set[Path] = set()

    def expand(path: Path) -> str:
        if path in visited or not path.exists():
            return ""
        visited.add(path)
        text = path.read_text(encoding="utf-8", errors="replace")

        def repl(m: re.Match) -> str:
            ref = m.group(1).strip()
            child = src_dir / ref
            if child.suffix.lower() != ".tex":
                child = child.with_suffix(".tex")
            if not child.exists():
                # try relative to including file's dir
                child2 = path.parent / Path(ref)
                if child2.suffix.lower() != ".tex":
                    child2 = child2.with_suffix(".tex")
                child = child2
            return expand(child) if child.exists() else m.group(0)

        return re.sub(r"\\(?:input|include)\s*\{([^}]*)\}", repl, text)

    return expand(main)


def fetch_arxiv_source(arxiv_id: str, out_dir: Path) -> Path | None:
    """Download and extract the arXiv e-print source tarball. Returns src dir."""
    import httpx

    try:
        with httpx.Client(trust_env=False, timeout=60, follow_redirects=True) as client:
            r = client.get(f"https://arxiv.org/e-print/{arxiv_id}")
            r.raise_for_status()
            data = r.content
    except Exception as exc:
        print(f"[warn] arXiv e-print fetch failed: {exc}", file=sys.stderr)
        return None

    if data[:5] == b"%PDF-":
        print("[warn] arXiv e-print is a PDF (no LaTeX source).", file=sys.stderr)
        return None

    src_dir = out_dir / "source"
    src_dir.mkdir(parents=True, exist_ok=True)

    def _safe_extract(tf: tarfile.TarFile) -> None:
        base = src_dir.resolve()
        safe = []
        for member in tf.getmembers():
            target = (src_dir / member.name).resolve()
            if not str(target).startswith(str(base) + "/") and target != base:
                print(f"[warn] skipping unsafe tar member: {member.name}", file=sys.stderr)
                continue
            safe.append(member)
        try:
            tf.extractall(src_dir, members=safe, filter="data")
        except TypeError:  # filter kwarg unavailable on older Python
            tf.extractall(src_dir, members=safe)

    # try tar (possibly gz-compressed)
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as tf:
            _safe_extract(tf)
        return src_dir
    except tarfile.ReadError:
        pass

    # try single gzip-compressed file (usually a lone .tex)
    try:
        decompressed = gzip.decompress(data)
        (src_dir / "main.tex").write_bytes(decompressed)
        return src_dir
    except Exception as exc:
        print(f"[warn] could not unpack arXiv source: {exc}", file=sys.stderr)
        return None


# ----------------------------------------------------------------------------
# arXiv metadata + PDF text
# ----------------------------------------------------------------------------

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
    ap.add_argument("input", help="arXiv id/URL, PDF path, text/markdown path, or LaTeX .tex/dir")
    ap.add_argument("--out-dir", default=None, help="working directory (default ./reviews/<slug>)")
    args = ap.parse_args()

    kind = detect_kind(args.input)

    meta = {"arxiv_id": "", "title": "", "authors": [], "categories": [], "published": ""}
    if kind == "arxiv":
        slug = slugify(arxiv_id_from(args.input))
    elif kind == "latex":
        p = Path(args.input)
        slug = slugify(p.name if p.is_dir() else p.stem)
    else:
        slug = slugify(Path(args.input).stem)

    out_dir = Path(args.out_dir) if args.out_dir else Path.cwd() / "reviews" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    figures: list[dict] = []

    if kind == "arxiv":
        arxiv_id = arxiv_id_from(args.input)
        got = fetch_arxiv(arxiv_id, out_dir)
        meta.update(got["meta"])
        text = got["text"]
        # additive: try to also pull the source tarball for real figures
        src_dir = fetch_arxiv_source(arxiv_id, out_dir)
        if src_dir is not None:
            figures = harvest_figures(src_dir, out_dir)
    elif kind == "pdf":
        text = extract_pdf_text(Path(args.input))
        meta["title"] = Path(args.input).stem
    elif kind == "latex":
        p = Path(args.input)
        src_dir = p if p.is_dir() else p.parent
        text = assemble_latex_text(src_dir)
        meta["title"] = title_from_tex(text) or (p.name if p.is_dir() else p.stem)
        figures = harvest_figures(src_dir, out_dir)
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

    n_converted = sum(1 for f in figures if f.get("converted"))
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
        "n_figures": n_converted,
        "figures_dir": str(out_dir / "figures" / "paper") if n_converted else "",
        "figures_manifest": str(out_dir / "figures_manifest.json") if figures else "",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
