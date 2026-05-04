---
name: md2pdf-typora
description: Convert Markdown to PDF using Typora's Whitey theme via pandoc + Chrome headless, replicating Typora's PDF export appearance
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Markdown to PDF (Typora-style)

Convert a Markdown file to PDF that closely matches Typora's PDF export with the **Whitey** theme. Uses pandoc for MD→HTML conversion and Chrome headless for HTML→PDF rendering.

## Usage

```
/md2pdf-typora <input.md> [options]
```

### Arguments

- `<input.md>` — Path to the input Markdown file (required)
- `--output <path>` — Output PDF path (default: same directory as input, `.pdf` extension)
- `--dropbox [subfolder]` — Copy PDF to `~/Dropbox/Magi/[subfolder]/`
- `--send-telegram` — Send compiled PDF via Telegram after compilation
- `--toc` — Include table of contents

## Pipeline

### Step 1: Pre-process Markdown

Before pandoc conversion, handle Typora-specific syntax and pandoc parser quirks that the input may not anticipate:

- **`[TOC]` handling**: Typora uses `[TOC]` as an inline TOC marker, but pandoc ignores it and leaves it as literal text. Always strip `[TOC]` from the input and use pandoc's `--toc` flag instead.
- **HR-then-heading normalization** (load-bearing): If a horizontal rule line `---` is *immediately* followed by a `## ` heading with no blank line between them, pandoc's reader can interpret the pair as a setext-style table fragment, swallowing the heading and several paragraphs into a single `<table><td>` cell. Symptoms: missing TOC entries for that section, AND the section's body content (especially pipe tables) renders as a single inline run-on paragraph in the PDF. This pattern is common in chunked-translation workflows where chunk N ends with `---` and chunk N+1 starts with `## `, then `cat`-merging skips the blank line. The pre-processor inserts a blank line between any `---` line and an immediately-following `## ` heading.

```bash
TMP_MD="${INPUT_DIR}/_typora_tmp.md"
# (a) strip Typora [TOC] markers
# (b) ensure a blank line between '---' HR and an immediately-following '## ' heading
python3 - "$INPUT" "$TMP_MD" << 'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
out = []
with open(src) as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if line.rstrip("\n").strip() == "[TOC]":
        continue  # strip Typora TOC marker
    out.append(line)
    if line.rstrip() == "---" and i + 1 < len(lines) and lines[i+1].lstrip().startswith("## "):
        out.append("\n")  # insert blank line so pandoc doesn't fuse '---'+heading into a table
with open(dst, "w") as f:
    f.writelines(out)
PYEOF
```

### Step 2: Prepare HTML

Use pandoc to convert the pre-processed Markdown to standalone HTML with:
- MathJax for math rendering
- The Whitey theme CSS embedded
- Syntax highlighting for code blocks
- `--toc --toc-depth=2` for table of contents (always enabled since `[TOC]` was stripped)

```bash
CSS_PATH="$HOME/.claude/skills/md2pdf-typora/typora-whitey.css"

cd "$INPUT_DIR"
pandoc "$(basename "$TMP_MD")" \
    -f markdown-yaml_metadata_block+tex_math_dollars \
    -o "$TMP_HTML" \
    --standalone \
    --mathjax \
    --css="$CSS_PATH" \
    --metadata title="$TITLE" \
    --highlight-style=pygments \
    --toc --toc-depth=2

# Force MathJax SVG output (replaces pandoc's default CHTML mode).
# CHTML depends on STIX-Web webfonts loaded from CDN; under Chrome headless,
# missing-glyph fallbacks render Greek letters (\phi, \theta etc.) as empty
# boxes and inline sub/superscripts wrap onto separate lines. SVG renders
# every glyph as a path with no font dependency, eliminating both failures.
sed -i 's|/tex-chtml-full.js|/tex-svg-full.js|g' "$TMP_HTML"
```

**Why `-f markdown-yaml_metadata_block+tex_math_dollars`**: pandoc's default markdown reader treats any colon (`:`) on an early line as a potential YAML key. Korean / non-English documents that open with a metadata blockquote like `> **도메인**: 물리학` raise spurious `YAML parse exception at line N, column M` errors and abort. Disabling the `yaml_metadata_block` extension bypasses this false positive without losing any other parsing capability — true YAML frontmatter (delimited by leading and trailing `---`) is rare in PDF inputs, and metadata is supplied via `--metadata title=...` instead. The companion `+tex_math_dollars` keeps `$...$`/`$$...$$` math active.

**Title extraction**: Use the first `# heading` in the file, or the filename if none exists.

**Image handling**: Pandoc resolves relative image paths from the input file's directory. Always run pandoc from the input file's directory:
```bash
cd "$(dirname "$INPUT")" && pandoc "$(basename "$TMP_MD")" ...
```

**Why SVG over CHTML**: CHTML (pandoc's default) requires Chrome headless to download and apply MathJax web fonts before printing. In practice this fails silently — Greek letters become `□` boxes, and inline math like `$\theta_{\mathrm{UV}}$` wraps with `θ` on one line and `_UV` on the next. SVG mode renders every symbol as inline `<svg>` path data, so the PDF is glyph-correct regardless of font cache state. SVG output is also slightly larger (~10-30%) but immune to network/cache flakiness.

### Step 3: Patch HTML (CSS, TOC position, print layout)

This is the critical post-processing step. Pandoc's output has several issues that must be fixed:

1. **Inline CSS**: Pandoc's `--css` adds a `<link>` tag that Chrome headless can't resolve. Replace it with an inline `<style>` block.
2. **Remove duplicate title**: Pandoc generates `<h1 class="title">` from `--metadata title` AND keeps the body `<h1>` from the markdown `# heading`. Remove the metadata title h1 to avoid duplication.
3. **Move TOC after body h1**: Pandoc places `<nav id="TOC">` before all body content (including the `<h1>`). Extract the TOC nav block and re-insert it after the first body `</h1>` so it appears below the title, matching Typora's `[TOC]` behavior.
4. **Print layout overrides** (load-bearing): The Whitey theme's body `max-width: 960px` and base `font-size: 19px` were tuned for on-screen reading and *overflow* both A4 (794px) and Letter (816px) page widths. Without overrides, content silently extends past the printable area, wide tables collapse with overflowing cells, equations push past the right margin, and code blocks scroll off the page. The patch CSS pins `@page { size: A4 }`, sets `body { max-width: none }`, switches tables to `table-layout: fixed` with explicit column widths and `word-break` so multi-line cells wrap correctly, prevents page breaks inside equations / blockquotes / table rows, and keeps headings attached to their following content (`page-break-after: avoid`).
5. **Inline-math no-wrap**: MathJax SVG produces `<mjx-container>` for each formula. Without `white-space: nowrap`, inline math like `$\theta_{\mathrm{UV}}$` can wrap mid-expression, splitting `θ` from its subscript across lines. The patch CSS pins each container to one line.

```python
python3 << 'PYEOF'
import re

css_path = "$CSS_PATH"
html_path = "$TMP_HTML"

with open(css_path) as f:
    css = f.read()
with open(html_path) as f:
    html = f.read()

# Print-layout overrides (kept inside the same <style> block as Whitey CSS so
# they cascade after the theme rules and win without `!important` battles).
print_css = """
@page { size: A4; margin: 18mm 14mm 20mm 14mm; }
html { font-size: 14px !important; }
body { max-width: none !important; margin: 0 !important; padding: 0 !important;
       line-height: 1.45 !important; text-align: left !important; }
h1 { font-size: 1.9em !important; margin-top: 0.8em !important; }
h2 { font-size: 1.5em !important; margin-top: 1.2em !important;
     page-break-after: avoid; }
h3 { font-size: 1.2em !important; page-break-after: avoid; }
h4 { font-size: 1.05em !important; page-break-after: avoid; }
p, li { orphans: 2; widows: 2; }
/* Tables: fixed layout + column widths + cell wrap so wide content
   (especially CJK paragraphs) does not overflow the page width. */
table { table-layout: fixed !important; width: 100% !important;
        font-size: 0.88em !important; word-break: keep-all;
        overflow-wrap: anywhere; page-break-inside: auto; }
table th, table td { padding: 5px 7px !important; line-height: 1.35 !important;
                     vertical-align: top !important;
                     word-break: keep-all; overflow-wrap: anywhere; }
table thead { display: table-header-group; }
table tr { page-break-inside: avoid; }
/* 3-column tables (e.g. 'this concept | is not | distinguishing feature') */
table th:first-child, table td:first-child { width: 22%; }
table th:nth-child(2), table td:nth-child(2) { width: 22%; }
table th:nth-child(3), table td:nth-child(3) { width: 56%; }
/* 2-column tables (e.g. key/value glossaries): override the 3-col widths */
table:not(:has(thead th:nth-child(3))) th:first-child,
table:not(:has(thead th:nth-child(3))) td:first-child { width: 28%; }
table:not(:has(thead th:nth-child(3))) th:nth-child(2),
table:not(:has(thead th:nth-child(3))) td:nth-child(2) { width: 72%; }
pre { white-space: pre-wrap !important; word-wrap: break-word !important;
      font-size: 0.85em !important; page-break-inside: avoid; }
code { word-break: break-all; overflow-wrap: anywhere; }
blockquote { page-break-inside: avoid; margin: 0.8em 0; padding: 0.4em 0.9em;
             border-left: 3px solid #bbb; }
ul, ol { margin: 0.4em 0 0.4em 1.2em; padding-left: 0.4em; }
li { margin-bottom: 0.15em; }
hr { page-break-after: always; visibility: hidden;
     height: 0; margin: 0; border: 0; }
nav#TOC { font-size: 0.85em; line-height: 1.35; page-break-after: always; }
nav#TOC ul { list-style: none; padding-left: 1em; margin: 0.2em 0; }
"""

# 1) Inline CSS — Whitey theme followed by print overrides
html = re.sub(
    r'<link rel="stylesheet" href="[^"]*typora-whitey\.css"[^>]*/>',
    f'<style>\n{css}\n{print_css}\n</style>', html
)

# 2) Add image scaling + MathJax SVG inline-math no-wrap CSS
html = html.replace('</style>', """
img {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 0.8em auto;
  page-break-inside: avoid;
}
mjx-container {
  white-space: nowrap;
}
mjx-container[display="true"] {
  margin: 0.6em 0 !important;
  page-break-inside: avoid !important;
}
mjx-container[display="true"] > svg,
mjx-container[display="true"] > mjx-math {
  max-width: 100%;
}
</style>""", 1)

# 3) Remove pandoc's duplicate title h1 (has class="title")
html = re.sub(r'<h1 class="title">[^<]*</h1>\s*', '', html)

# 4) Move TOC nav block to after the first body </h1>
toc_match = re.search(r'(<nav\s+id="TOC"[^>]*>.*?</nav>)', html, re.DOTALL)
if toc_match:
    toc_block = toc_match.group(1)
    html = html.replace(toc_block, '', 1)
    html = html.replace('</h1>', '</h1>\n' + toc_block, 1)

with open(html_path, 'w') as f:
    f.write(html)
PYEOF
```

### Step 4: Render PDF with Chrome headless

```bash
google-chrome-stable \
    --headless=new \
    --disable-gpu \
    --no-pdf-header-footer \
    --virtual-time-budget=30000 \
    --print-to-pdf="$OUTPUT_PDF" \
    "file://$TMP_HTML" 2>/dev/null
```

**Chrome PDF options**:
- `--no-pdf-header-footer` — removes default header/footer with URL and date
- `--virtual-time-budget=30000` — gives 30 seconds for Google Fonts CDN + MathJax SVG bundle (~1 MB) to fully load and typeset every formula before printing. Documents with hundreds of math expressions are still well within budget; documents with very few math expressions never wait the full 30s in practice.
- Page size is set to A4 by the patched `@page { size: A4 }` rule (Step 3). Chrome's command-line default is Letter; the CSS rule overrides it. To switch to Letter, change `size: A4` to `size: Letter` in the print CSS — do not pass `--print-to-pdf-paper-size`, which is brittle across Chrome versions.

**IMPORTANT: HTML must be in the same directory as the input markdown** so that relative image paths (e.g., `plots/foo.png`) resolve correctly. Do NOT write HTML to `/tmp/`.

### Step 5: Verify and deliver

1. Check the PDF was created and report file size
2. If `--dropbox` was specified:
   ```bash
   DROPBOX_BASE="$HOME/Dropbox/Magi"
   mkdir -p "$DROPBOX_BASE/$SUBFOLDER"
   cp "$OUTPUT_PDF" "$DROPBOX_BASE/$SUBFOLDER/"
   ```
3. If `--send-telegram` was specified, send via Telegram reply tool
4. Clean up temporary files (HTML and pre-processed MD)

## Complete Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$1"
BASENAME="$(basename "${INPUT}" .md)"
INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
CSS_PATH="$HOME/.claude/skills/md2pdf-typora/typora-whitey.css"
TMP_MD="${INPUT_DIR}/_typora_tmp.md"
TMP_HTML="${INPUT_DIR}/_typora_tmp.html"
OUTPUT_PDF="${OUTPUT:-${INPUT_DIR}/${BASENAME}.pdf}"

# Extract title from first H1
TITLE=$(grep -m1 '^# ' "$INPUT" | sed 's/^# //' || echo "$BASENAME")

# Step 1: Pre-process — strip Typora's [TOC] AND insert blank line between
# any '---' HR and an immediately-following '## ' heading (otherwise pandoc
# fuses them into a setext-style table that swallows the heading + body).
python3 - "$INPUT" "$TMP_MD" << 'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
out = []
with open(src) as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if line.rstrip("\n").strip() == "[TOC]":
        continue
    out.append(line)
    if line.rstrip() == "---" and i + 1 < len(lines) and lines[i+1].lstrip().startswith("## "):
        out.append("\n")
with open(dst, "w") as f:
    f.writelines(out)
PYEOF

# Step 2: MD → HTML (run from input dir for relative image paths).
# `-f markdown-yaml_metadata_block` disables YAML metadata block detection so
# that Korean / non-English documents whose body lines contain ':' do not
# raise spurious YAML parse errors. `+tex_math_dollars` keeps `$...$` math.
cd "$INPUT_DIR"
pandoc "$(basename "$TMP_MD")" \
    -f markdown-yaml_metadata_block+tex_math_dollars \
    -o "$TMP_HTML" \
    --standalone \
    --mathjax \
    --css="$CSS_PATH" \
    --metadata title="$TITLE" \
    --highlight-style=pygments \
    --toc --toc-depth=2

# Force MathJax SVG output (eliminates CHTML font-fallback bugs).
sed -i 's|/tex-chtml-full.js|/tex-svg-full.js|g' "$TMP_HTML"

# Step 3: Patch HTML — inline CSS + print-layout overrides, fix TOC position,
# scale images, no-wrap inline math.
python3 << 'PYEOF'
import re

css_path = "$CSS_PATH"
html_path = "$TMP_HTML"

with open(css_path) as f: css = f.read()
with open(html_path) as f: html = f.read()

print_css = """
@page { size: A4; margin: 18mm 14mm 20mm 14mm; }
html { font-size: 14px !important; }
body { max-width: none !important; margin: 0 !important; padding: 0 !important;
       line-height: 1.45 !important; text-align: left !important; }
h1 { font-size: 1.9em !important; margin-top: 0.8em !important; }
h2 { font-size: 1.5em !important; margin-top: 1.2em !important; page-break-after: avoid; }
h3 { font-size: 1.2em !important; page-break-after: avoid; }
h4 { font-size: 1.05em !important; page-break-after: avoid; }
p, li { orphans: 2; widows: 2; }
table { table-layout: fixed !important; width: 100% !important;
        font-size: 0.88em !important; word-break: keep-all; overflow-wrap: anywhere;
        page-break-inside: auto; }
table th, table td { padding: 5px 7px !important; line-height: 1.35 !important;
                     vertical-align: top !important; word-break: keep-all;
                     overflow-wrap: anywhere; }
table thead { display: table-header-group; }
table tr { page-break-inside: avoid; }
table th:first-child, table td:first-child { width: 22%; }
table th:nth-child(2), table td:nth-child(2) { width: 22%; }
table th:nth-child(3), table td:nth-child(3) { width: 56%; }
table:not(:has(thead th:nth-child(3))) th:first-child,
table:not(:has(thead th:nth-child(3))) td:first-child { width: 28%; }
table:not(:has(thead th:nth-child(3))) th:nth-child(2),
table:not(:has(thead th:nth-child(3))) td:nth-child(2) { width: 72%; }
pre { white-space: pre-wrap !important; word-wrap: break-word !important;
      font-size: 0.85em !important; page-break-inside: avoid; }
code { word-break: break-all; overflow-wrap: anywhere; }
blockquote { page-break-inside: avoid; margin: 0.8em 0; padding: 0.4em 0.9em;
             border-left: 3px solid #bbb; }
ul, ol { margin: 0.4em 0 0.4em 1.2em; padding-left: 0.4em; }
li { margin-bottom: 0.15em; }
hr { page-break-after: always; visibility: hidden; height: 0; margin: 0; border: 0; }
nav#TOC { font-size: 0.85em; line-height: 1.35; page-break-after: always; }
nav#TOC ul { list-style: none; padding-left: 1em; margin: 0.2em 0; }
"""

# Inline CSS (Whitey + print overrides)
html = re.sub(r'<link rel="stylesheet" href="[^"]*typora-whitey\.css"[^>]*/>',
              f'<style>\n{css}\n{print_css}\n</style>', html)

# Image scaling + MathJax SVG inline-math no-wrap, attached after the main <style>
html = html.replace('</style>', """
img { max-width: 100% !important; height: auto !important; display: block;
      margin: 0.8em auto; page-break-inside: avoid; }
mjx-container { white-space: nowrap; }
mjx-container[display="true"] { margin: 0.6em 0 !important;
                                  page-break-inside: avoid !important; }
mjx-container[display="true"] > svg,
mjx-container[display="true"] > mjx-math { max-width: 100%; }
</style>""", 1)

# Remove pandoc's duplicate title h1
html = re.sub(r'<h1 class="title">[^<]*</h1>\s*', '', html)

# Move TOC after body h1
toc_match = re.search(r'(<nav\s+id="TOC"[^>]*>.*?</nav>)', html, re.DOTALL)
if toc_match:
    toc_block = toc_match.group(1)
    html = html.replace(toc_block, '', 1)
    html = html.replace('</h1>', '</h1>\n' + toc_block, 1)

with open(html_path, 'w') as f: f.write(html)
PYEOF

# Step 4: HTML → PDF
google-chrome-stable \
    --headless=new \
    --disable-gpu \
    --no-pdf-header-footer \
    --virtual-time-budget=30000 \
    --print-to-pdf="$OUTPUT_PDF" \
    "file://$TMP_HTML" 2>/dev/null

# Cleanup
rm -f "$TMP_HTML" "$TMP_MD"

echo "PDF created: $OUTPUT_PDF ($(du -h "$OUTPUT_PDF" | cut -f1))"
```

## Notes

- The Whitey theme uses **IBM Plex Serif** (Latin) + **MaruBuri** (Korean) for body text, **Roboto Slab** for headings, **JetBrains Mono** for code
- h1 and h2 are center-aligned with h2 having a centered underline decoration in the on-screen theme; the print-CSS overrides reduce h2 to flush-left at a smaller size to maximise printable area
- Body text alignment is switched from justify to left in the print CSS, since justified Korean / monospace text produces wide inter-word gaps and bad rivers in Chrome's print engine
- Fonts are loaded from Google Fonts CDN — Chrome needs network access during rendering
- Math is rendered by **MathJax SVG** (`tex-svg-full.js`, loaded from CDN). The pipeline rewrites pandoc's default CHTML reference to SVG because CHTML silently fails when STIX-Web webfonts are unavailable to Chrome headless (Greek letters become `□` boxes; inline sub/superscripts wrap onto separate lines). SVG renders every glyph as inline path data and is robust against font-cache state.
- For offline use, download MathJax SVG locally (`mathjax@3/es5/tex-svg-full.js` plus dependencies) and adjust the `sed` patch to point at the local URL.
- The CSS file is at `~/.claude/skills/md2pdf-typora/typora-whitey.css`

## Failure modes the pipeline now defends against

These were caught in production and are now handled by the pre-processor / pandoc flags / print CSS by default:

1. **Chunk-merge `---` followed by `## ` heading on the next line, no blank line between them.** Symptom: missing TOC entries for the affected sections AND the section's body content (especially the first table after the heading) renders as a single inline run-on paragraph, sometimes spanning multiple paragraphs welded into one cell. Root cause: pandoc parses `---\n## ...` as a setext-style table fragment. Fix: Step 1 pre-processor inserts a blank line.
2. **`YAML parse exception at line N, column M` from pandoc on Korean / non-English documents.** Symptom: pandoc aborts with an opaque error before any HTML is produced. Root cause: pandoc's default `markdown` reader treats early-line `:` (very common in Korean blockquotes like `> **도메인**: 물리학`) as a YAML key. Fix: Step 2 invokes pandoc with `-f markdown-yaml_metadata_block+tex_math_dollars` to disable the YAML metadata block extension while keeping `$...$` math.
3. **Wide tables overflow page width.** Symptom: the rightmost column of a 3-column table (especially Confusion-Neighbors-style "this | is not | distinguishing feature" tables with long Korean cells) extends past the right margin and gets clipped, or the row wraps in unexpected ways. Root cause: the Whitey CSS body `max-width: 960px` is wider than A4 (794px), and tables default to `table-layout: auto` which sizes columns from content. Fix: Step 3 print CSS sets `body { max-width: none }`, `table { table-layout: fixed }`, explicit column-width allocations, and `word-break: keep-all; overflow-wrap: anywhere` so Korean text wraps cleanly inside cells.
4. **Equations / blockquotes / code blocks split across page breaks.** Fix: Step 3 print CSS sets `page-break-inside: avoid` on each.
5. **Headings stranded at the bottom of a page with no body content following.** Fix: Step 3 print CSS sets `page-break-after: avoid` on `h2`/`h3`/`h4`.
