#!/usr/bin/env python3
"""Patch pandoc's standalone HTML so Chrome headless prints it like Typora.

Called with explicit argv paths, so nothing here depends on shell variable
interpolation. The previous heredoc form silently received the literal strings
"$CSS_PATH" and "$TMP_HTML" and died on FileNotFoundError, which meant none of
the print CSS was ever applied and every PDF came out with the on-screen theme
(19px body, 960px max-width) squeezed onto a 794px A4 page.

What this does, and why each step is load-bearing:

* Inline the theme CSS. Pandoc emits ``<link rel="stylesheet" href="...">``,
  and while Chrome can sometimes resolve an absolute path under ``file://``,
  it is not reliable and gives no control over cascade order.

* Put the theme, the print overrides and the element fixes in ONE style block
  that replaces the link. Pandoc emits its own ``<style>`` block BEFORE the
  link, so appending to the first ``</style>`` (what the old code did) landed
  the overrides ahead of the theme and let the theme win.

* Drop pandoc's ``<header id="title-block-header">`` wrapper together with the
  duplicate ``<h1 class="title">`` inside it, otherwise the title appears twice
  and an empty header keeps its margins.

* Move the TOC below the document's own H1. If the document has no H1 the TOC
  is placed right after ``<body>`` instead of being dropped, which is what the
  old unguarded ``replace('</h1>', ...)`` did.

* Size table columns only for 2 and 3 column tables. The old CSS assigned
  22%/22%/56% to the first three columns of *every* table under
  ``table-layout: fixed``, so a 6 or 7 column table gave its first three
  columns the entire width and collapsed the rest to nothing.

* Verify the result. Any assertion below failing means the PDF would have been
  wrong, and a loud failure beats a silently ugly document.
"""
from __future__ import annotations

import re
import sys

PRINT_CSS = """
/* ---- print layout overrides (Typora-like on paper) ------------------ */
@page {{ size: {paper}; margin: 18mm 14mm 20mm 14mm; }}
html {{ font-size: {font_px}px !important; }}
/* The theme paints html/body #fefefe for screen reading. On paper that is a
   faint grey panel covering the whole text block, with hard edges against the
   pure-white @page margin, and it wastes toner. Typora's own export paints
   nothing. */
html, body {{ background: transparent !important; }}
body {{ max-width: none !important; margin: 0 !important; padding: 0 !important;
       line-height: 1.45 !important; text-align: left !important; }}
h1 {{ font-size: 1.9em !important; margin-top: 0.8em !important; }}
h2 {{ font-size: 1.5em !important; margin-top: 1.2em !important;
     page-break-after: avoid; }}
h3 {{ font-size: 1.2em !important; page-break-after: avoid; }}
h4 {{ font-size: 1.05em !important; page-break-after: avoid; }}
p, li {{ orphans: 2; widows: 2; }}

/* Tables. Fixed layout with no per-column widths distributes evenly, which
   never overflows regardless of column count. Width hints are applied only to
   the narrow cases where an even split reads badly. */
table {{ table-layout: fixed !important; width: 100% !important;
        font-size: 0.86em !important; word-break: keep-all;
        overflow-wrap: anywhere; page-break-inside: auto; }}
table th, table td {{ padding: 5px 7px !important; line-height: 1.35 !important;
                     vertical-align: top !important; word-break: keep-all;
                     overflow-wrap: anywhere; }}
table thead {{ display: table-header-group; }}
table tr {{ page-break-inside: avoid; }}
/* exactly 2 columns */
table:has(tr > *:nth-child(2)):not(:has(tr > *:nth-child(3))) :is(th, td):nth-child(1)
  {{ width: 28%; }}
table:has(tr > *:nth-child(2)):not(:has(tr > *:nth-child(3))) :is(th, td):nth-child(2)
  {{ width: 72%; }}
/* exactly 3 columns */
table:has(tr > *:nth-child(3)):not(:has(tr > *:nth-child(4))) :is(th, td):nth-child(1)
  {{ width: 22%; }}
table:has(tr > *:nth-child(3)):not(:has(tr > *:nth-child(4))) :is(th, td):nth-child(2)
  {{ width: 22%; }}
table:has(tr > *:nth-child(3)):not(:has(tr > *:nth-child(4))) :is(th, td):nth-child(3)
  {{ width: 56%; }}

pre {{ white-space: pre-wrap !important; word-wrap: break-word !important;
      font-size: 0.85em !important; page-break-inside: avoid; }}
/* break-all everywhere splits short identifiers mid-word in running text
   (`morton` came out as "mort" / "on"). Break only when a token genuinely
   cannot fit, and keep the aggressive rule for narrow table cells. */
code {{ word-break: normal; overflow-wrap: break-word; }}
table code, pre code {{ word-break: break-all; overflow-wrap: anywhere; }}
blockquote {{ page-break-inside: avoid; margin: 0.8em 0; padding: 0.4em 0.9em;
             border-left: 3px solid #bbb; }}
ul, ol {{ margin: 0.4em 0 0.4em 1.2em; padding-left: 0.4em; }}
li {{ margin-bottom: 0.15em; }}
{hr_css}
nav#TOC {{ font-size: 0.85em; line-height: 1.35; page-break-after: always; }}
nav#TOC ul {{ list-style: none; padding-left: 1em; margin: 0.2em 0; }}

/* Images never exceed the text column and never straddle a page break. */
img {{ max-width: 100% !important; height: auto !important; display: block;
      margin: 0.8em auto; page-break-inside: avoid; }}

/* MathJax SVG. Without nowrap, inline math splits a symbol from its
   subscript across a line break. */
mjx-container {{ white-space: nowrap; }}
mjx-container[display="true"] {{ margin: 0.6em 0 !important;
                                page-break-inside: avoid !important; }}
mjx-container[display="true"] > svg,
mjx-container[display="true"] > mjx-math {{ max-width: 100%; }}
"""

# Typora renders --- as a thin rule and does not break the page there, so that
# is the default. --break-on-hr restores the old forced-break behaviour.
# These are substituted into PRINT_CSS after .format() has already collapsed
# its doubled braces, so they use single braces.
HR_KEEP = """hr { border: 0; border-top: 1px solid #ddd; margin: 1.4em 0;
     height: 0; page-break-after: auto; }"""
HR_BREAK = """hr { page-break-after: always; visibility: hidden;
     height: 0; margin: 0; border: 0; }"""

LINK_RE = re.compile(r'<link\s+rel="stylesheet"\s+href="[^"]*\.css"\s*/?>')
HEADER_RE = re.compile(r'<header\s+id="title-block-header">.*?</header>\s*', re.DOTALL)
TITLE_H1_RE = re.compile(r'<h1\s+class="title">.*?</h1>\s*', re.DOTALL)
TOC_RE = re.compile(r'<nav\s+id="TOC"[^>]*>.*?</nav>\s*', re.DOTALL)
MATHJAX_RE = re.compile(r'(cdn\.jsdelivr\.net/npm/mathjax@3/es5/)tex-[a-z-]+\.js')


def patch(html: str, css: str, *, paper: str, font_px: int, break_on_hr: bool) -> str:
    print_css = PRINT_CSS.format(
        paper=paper, font_px=font_px,
        hr_css=(HR_BREAK if break_on_hr else HR_KEEP),
    )

    style_block = f"<style>\n/* ==== theme ==== */\n{css}\n{print_css}\n</style>"

    # 1) theme + overrides as one block, in the link's position so it cascades
    #    after pandoc's own style block. A lambda replacement keeps backslashes
    #    in the CSS from being read as regex group references.
    html, n_link = LINK_RE.subn(lambda _m: style_block, html, count=1)
    if n_link == 0:
        raise SystemExit("patch_html: pandoc emitted no stylesheet <link> to replace; "
                         "was --css passed to pandoc?")

    # 2) MathJax CHTML depends on webfonts that Chrome headless often fails to
    #    load, which turns Greek letters into empty boxes. SVG has no font
    #    dependency.
    html = MATHJAX_RE.sub(r"\1tex-svg-full.js", html)

    # 3) pandoc's duplicate title, wrapper included
    html = HEADER_RE.sub("", html)
    html = TITLE_H1_RE.sub("", html)

    # 4) TOC below the document's own H1, or right after <body> if it has none
    m = TOC_RE.search(html)
    if m:
        toc = m.group(0)
        html = html[:m.start()] + html[m.end():]
        h1_end = html.find("</h1>")
        if h1_end != -1:
            cut = h1_end + len("</h1>")
            html = html[:cut] + "\n" + toc + html[cut:]
        else:
            html = re.sub(r"(<body[^>]*>)", lambda mm: mm.group(1) + "\n" + toc,
                          html, count=1)

    # 5) fail loudly rather than print a wrong document
    if LINK_RE.search(html):
        raise SystemExit("patch_html: a stylesheet <link> survived patching")
    if "/* ==== theme ==== */" not in html:
        raise SystemExit("patch_html: theme CSS was not inlined")
    if "table-layout: fixed" not in html:
        raise SystemExit("patch_html: print CSS was not inlined")
    if 'class="title"' in html:
        raise SystemExit("patch_html: duplicate title survived")
    if m and 'id="TOC"' not in html:
        raise SystemExit("patch_html: TOC was removed but never reinserted")
    return html


def main() -> int:
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} <theme.css> <file.html> "
              f"[paper] [font_px] [break_on_hr]", file=sys.stderr)
        return 2
    css_path, html_path = sys.argv[1], sys.argv[2]
    paper = sys.argv[3] if len(sys.argv) > 3 else "A4"
    font_px = int(sys.argv[4]) if len(sys.argv) > 4 else 14
    break_on_hr = (len(sys.argv) > 5 and sys.argv[5] == "1")

    with open(css_path, encoding="utf-8") as f:
        css = f.read()
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    html = patch(html, css, paper=paper, font_px=font_px, break_on_hr=break_on_hr)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"patch_html: ok (paper={paper}, font={font_px}px, "
          f"hr_break={'yes' if break_on_hr else 'no'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
