#!/usr/bin/env bash
# Markdown -> PDF in Typora's Whitey style, via pandoc + Chrome headless.
#
# This is a real script on purpose. The pipeline used to live as a bash+python
# template inside SKILL.md that the caller retyped every run, and the retyping
# was the instability: the python stage was pasted under a quoted heredoc
# (<< 'PYEOF'), so "$CSS_PATH" and "$TMP_HTML" reached python as literal text,
# the stage died on FileNotFoundError, and every PDF was printed with the
# on-screen theme (19px body, 960px max-width) crushed onto a 794px A4 page.
# Run this file instead of reconstructing the steps.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CSS_PATH="$SKILL_DIR/typora-whitey.css"

usage() {
    cat <<'EOF'
usage: md2pdf.sh <input.md> [options]

  --output <path>        output PDF path (default: alongside the input)
  --dropbox [subfolder]  also copy into ~/Dropbox/Magi/<subfolder>/
  --no-toc               omit the table of contents (default: include)
  --toc                  accepted for compatibility; the TOC is on by default
  --break-on-hr          force a page break at every --- rule
                         (default: render --- as a thin rule, as Typora does)
  --paper <A4|Letter>    page size (default: A4)
  --font <px>            root font size (default: 14)
  --keep-html            keep the intermediate HTML for debugging
EOF
}

[[ $# -ge 1 ]] || { usage; exit 2; }
case "$1" in -h|--help) usage; exit 0 ;; esac

INPUT="$1"; shift
OUTPUT=""
DROPBOX_SUB=""
WANT_DROPBOX=0
WANT_TOC=1
BREAK_ON_HR=0
PAPER="A4"
FONT_PX=14
KEEP_HTML=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)       OUTPUT="${2:?--output needs a path}"; shift 2 ;;
        --dropbox)      WANT_DROPBOX=1
                        if [[ ${2:-} && ${2:0:2} != "--" ]]; then DROPBOX_SUB="$2"; shift 2
                        else shift; fi ;;
        --no-toc)       WANT_TOC=0; shift ;;
        --toc)          WANT_TOC=1; shift ;;
        --break-on-hr)  BREAK_ON_HR=1; shift ;;
        --paper)        PAPER="${2:?--paper needs A4 or Letter}"; shift 2 ;;
        --font)         FONT_PX="${2:?--font needs a number}"; shift 2 ;;
        --keep-html)    KEEP_HTML=1; shift ;;
        --send-telegram) echo "note: --send-telegram is handled by the caller, not this script" >&2; shift ;;
        *) echo "unknown option: $1" >&2; usage; exit 2 ;;
    esac
done

[[ -f "$INPUT" ]] || { echo "input not found: $INPUT" >&2; exit 1; }
[[ -f "$CSS_PATH" ]] || { echo "theme CSS not found: $CSS_PATH" >&2; exit 1; }
for tool in pandoc python3; do
    command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 1; }
done
# README promises any Chromium-family browser, so resolve rather than hardcode.
CHROME=""
for cand in google-chrome-stable google-chrome chromium chromium-browser; do
    if command -v "$cand" >/dev/null; then CHROME="$cand"; break; fi
done
[[ -n "$CHROME" ]] || {
    echo "no Chromium-family browser on PATH (tried google-chrome-stable, google-chrome, chromium, chromium-browser)" >&2
    exit 1
}
case "$PAPER" in A4|Letter) ;; *) echo "--paper must be A4 or Letter" >&2; exit 2 ;; esac

INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
BASENAME="$(basename "$INPUT" .md)"
OUTPUT_PDF="${OUTPUT:-$INPUT_DIR/$BASENAME.pdf}"

# Intermediates live beside the input so that relative image paths such as
# figures/paper/foo.png resolve under file:// exactly as pandoc resolved them.
TMP_MD="$INPUT_DIR/.md2pdf_$BASENAME.md"
TMP_HTML="$INPUT_DIR/.md2pdf_$BASENAME.html"
cleanup() {
    rm -f "$TMP_MD"
    [[ $KEEP_HTML -eq 1 ]] || rm -f "$TMP_HTML"
}
trap cleanup EXIT

TITLE="$(grep -m1 '^# ' "$INPUT" | sed 's/^#[[:space:]]*//' || true)"
[[ -n "$TITLE" ]] || TITLE="$BASENAME"

# --- 1. preprocess ---------------------------------------------------------
python3 "$SKILL_DIR/scripts/preprocess_md.py" "$INPUT" "$TMP_MD"

# --- 2. markdown -> standalone HTML ---------------------------------------
# -markdown-yaml_metadata_block: pandoc's default reader treats an early-line
# colon as a YAML key, so Korean docs opening with `> **도메인**: 물리학` abort
# with a spurious YAML parse exception. +tex_math_dollars keeps $...$ math.
PANDOC_ARGS=(
    "$(basename "$TMP_MD")"
    -f markdown-yaml_metadata_block+tex_math_dollars
    -o "$TMP_HTML"
    --standalone
    --mathjax
    --css="$CSS_PATH"
    --metadata title="$TITLE"
    --highlight-style=pygments
)
[[ $WANT_TOC -eq 1 ]] && PANDOC_ARGS+=(--toc --toc-depth=2)
( cd "$INPUT_DIR" && pandoc "${PANDOC_ARGS[@]}" )

# --- 3. patch HTML (inline CSS, print layout, TOC position, MathJax SVG) ---
python3 "$SKILL_DIR/scripts/patch_html.py" \
    "$CSS_PATH" "$TMP_HTML" "$PAPER" "$FONT_PX" "$BREAK_ON_HR"

# --- 4. HTML -> PDF -------------------------------------------------------
# The budget covers the Google Fonts CDN plus the ~1 MB MathJax SVG bundle;
# documents with little math finish well before it elapses.
"$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-pdf-header-footer \
    --virtual-time-budget=30000 \
    --print-to-pdf="$OUTPUT_PDF" \
    "file://$TMP_HTML" 2>/dev/null

# --- 5. verify ------------------------------------------------------------
[[ -s "$OUTPUT_PDF" ]] || { echo "chrome produced no PDF: $OUTPUT_PDF" >&2; exit 1; }
SIZE="$(du -h "$OUTPUT_PDF" | cut -f1)"
PAGES="?"
if command -v pdfinfo >/dev/null; then
    PAGES="$(pdfinfo "$OUTPUT_PDF" 2>/dev/null | awk '/^Pages:/{print $2}')"
    [[ ${PAGES:-0} -ge 1 ]] || { echo "PDF has no pages: $OUTPUT_PDF" >&2; exit 1; }
fi
echo "PDF created: $OUTPUT_PDF ($SIZE, $PAGES pages)"

if [[ $WANT_DROPBOX -eq 1 ]]; then
    DEST="$HOME/Dropbox/Magi${DROPBOX_SUB:+/$DROPBOX_SUB}"
    mkdir -p "$DEST"
    cp "$OUTPUT_PDF" "$DEST/"
    echo "copied to: $DEST/$(basename "$OUTPUT_PDF")"
fi

[[ $KEEP_HTML -eq 1 ]] && echo "kept HTML: $TMP_HTML"
exit 0
