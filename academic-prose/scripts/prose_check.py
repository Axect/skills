#!/usr/bin/env python3
"""Candidate finder for English academic prose (Markdown, Typst, LaTeX, or plain text).

What it does, and nothing more:
  * Word counts per sentence after normalisation (whitespace tokens; inline math -> MATH and
    inline code or raw text -> CODE, one word each; citations and markup are removed). Typst
    is read in one pass (see _typst_scan); Markdown tables and Typst statements are skipped
    with a note; a Typst construct the pass cannot classify or close stops the run (exit 2).
  * Punctuation candidates: em/en dashes, colons (except inside a time, ratio, URL scheme,
    or path), semicolons. Whether a colon joins clauses is for the reader to decide.
  * Pattern candidates to judge in context: long sentences, sentences with several clause
    joins, comma-enclosed phrases, "with X -ing" constructions, trailing -ing clauses,
    stranded auxiliaries ("above which it cannot."), bare This/It openers, demonstrative +
    noun with a count of earlier lexical occurrences (not of referents), pronouns, repeated
    content words (limited inflection grouping), and word lists (hype, weak verbs, formality
    inflation, scope words, presumptive adverbs, stock connectors, colloquial and spatial
    wording).
  * --compare OLD NEW: surface differences in supported protected tokens. Math ($...$, \\(...\\),
    \\[...\\], equation-type environments) and quantity macros (\\SI, \\qty, \\num) verbatim from
    the raw source; citation keys (\\...cite...{}, #cite(<key>), @key, [n]); numbers with units,
    and negations, as tokens and, separately, with neighbouring words inside their sentence;
    hedges; scope words and bounds. Other markup macros are listed as "not compared".
    No difference does not prove that meaning, claim strength, or attachment was preserved.

It does not resolve antecedents, parse syntax, or judge meaning. A missing flag is not
evidence that a problem is absent. Exit codes: 0 done; 1 --strict found a dash or colon
candidate; 2 unreadable input, no prose found, or input that could not be fully analysed.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

LEX = {
    "hype": r"novel|groundbreaking|ground-breaking|revolution(?:ary|i[sz]e)?|unprecedented|pioneer(?:ing)?|"
            r"cutting-edge|state-of-the-art|transformative|game-chang\w*|paradigm shift|remarkabl[ey]|"
            r"crucial(?:ly)?|pivotal|paramount|perfect(?:ly)?|first-ever|seamless(?:ly)?|"
            r"to the best of our knowledge",
    "weak-verb": r"explor(?:e|es|ed|ing)|stud(?:y|ies|ied|ying)|investigat(?:e|es|ed|ing)|worked on|"
                 r"look(?:s|ed)? into",
    "inflation": r"utili[sz](?:e|es|ed|ing|ation)|leverag(?:e|es|ed|ing)|commenc(?:e|es|ed|ing)|"
                 r"endeavou?r(?:s|ed)?|facilitat(?:e|es|ed|ing)|ascertain\w*|in order to|"
                 r"due to the fact that|it is (?:worth|important to) not(?:e|ing)|"
                 r"plays? an? (?:key|important|central|crucial) role|serv(?:e|es|ed) as",
    "scope": r"exact(?:ly)?|cannot|always|never|all|every|any|only|none|guarantee[sd]?|"
             r"prov(?:e|es|ed|en)|recover(?:s|ed|y)?|fully|completely|entirely|unique(?:ly)?|"
             r"universal(?:ly)?|solve[sd]?|eliminat(?:e|es|ed)|optimal(?:ly)?|the first",
    "presumptive": r"clearly|obviously|trivially|of course|simply|naturally|evidently",
    "stock-connector": r"furthermore|moreover|notably|additionally|importantly|in essence|taken together|"
                       r"it is worth|delv(?:e|es|ing)|underscor(?:e|es|ed|ing)|tapestry|a testament",
    "contrast-frame": r"not (?:only|just|merely)\b[^.]{0,80}?\bbut|rather than",
    "colloquial": r"how far(?: back| up| down)?|how much of|look(?:s|ing)? (?:back|along|ahead)|must look|"
                  r"remember(?:s|ed)?|forget(?:s)?|wants? to|under the hood|boils? down|kicks? in",
    "spatial-wording": r"(?:locat|draw|trac|push|map)\w*\s+(?:the|these|this|its|their|a)?\s*"
                       r"(?:limits?|lines?|boundar\w+|frontiers?|edges?)",
}
LEX_RE = {k: re.compile(r"\b(?:%s)\b" % v, re.I) for k, v in LEX.items()}
# Defined technical terms that would otherwise trip the word lists. Extend with --allow.
TECH_TERMS = ["perfect sampling", "perfect matching", "exact diagonalization", "exact enumeration",
              "exactly solvable", "exact solution", "unique solution", "unique ergodicity",
              "universality class", "optimal transport", "optimal control"]

STOP = set("""a an the and or but nor of to in on at by for with from into onto over under about as
is are was were be been being am do does did done have has had having can could may might must shall
should will would this that these those it its they them their there here we our us i my me you your
he she his her which who whom whose what when where why how than then so such not no also only very
more most less least each every all any some both either neither one two own same other another
whether if because while although though since until upon within without between among per via
itself themselves ourselves""".split())
VERBISH = set("""is are was were be been has have had do does did can could may might must shall should
will would shows show showed suggests suggest means mean implies allows allow makes make leads lead
gives give holds hold remains remain""".split())

ABBREV = re.compile(r"\b(?:e\.g|i\.e|et al|al|Fig|Figs|Eq|Eqs|Ref|Refs|Sec|Secs|Ch|App|Tab|vs|cf|approx|"
                    r"resp|No|Nos|Dr|Mr|Mrs|Ms|Prof|St|Jr|Sr|Inc|Ltd|Co|Corp|etc)\.|\b[A-Z]\.(?=\s+[A-Z])")
DEMONSTRATIVE = re.compile(r"\b(this|these|those|that|such)\s+([A-Za-z][A-Za-z-]+)", re.I)
BARE_OPENER = re.compile(r"^(This|These|That|Those|It|They)\s+(%s)\b" % "|".join(sorted(VERBISH)))
PRONOUN = re.compile(r"\b(it|its|they|them|their)\b", re.I)
WITH_ING = re.compile(r"\bwith\s+(?:the|a|an|its|their|each|every|this|these)?\s*(?:[\w-]+\s+){1,6}?([a-z-]+ing)\b", re.I)
TRAIL_ING = re.compile(r",\s+(?!including\b|according\b|following\b|depending\b|assuming\b)([a-z]+ing)\b[^,.;]*[.!?]?$", re.I)
STRANDED = re.compile(r"\b(?:which|where|that|it|they|this|these)\s+(?:cannot|can|could|does|do|did|will|would|"
                      r"may|might|must|should|is|are|was|were)(?:\s+not|n't)?\s*[.!?]$", re.I)
CLAUSE_JOIN = re.compile(r",\s+(?:and|but|or|so|yet|while|whereas|which|who)\b|\b(?:whether|because|although|"
                         r"above which|below which|beyond which|in which|for which)\b|;", re.I)
PAREN_START = re.compile(r"^(?:a|an|the|which|who|whose|set|given|defined|determined|fixed|based|such as|"
                         r"including|especially|particularly|in particular|for example|for instance|e\.g\.|"
                         r"i\.e\.|unlike|like|as|not|rather than|together with|along with|[a-z]+ed|[a-z]+ing)\b", re.I)
DASH = re.compile(r"[\u2013\u2014]|(?<=\w)\s--\s(?=\w)|(?<=\w)---?(?=\w)")
COLON_EXEMPT = re.compile(r"\d:\d|https?:|[A-Za-z]:\\")


# ---------------------------------------------------------------- normalisation
TEX_LITERAL = re.compile(r"\\begin\{(verbatim|lstlisting|minted|Verbatim|comment)\*?\}.*?\\end\{\1\*?\}|"
                         r"\\(?:verb|lstinline)\*?(?:\[[^\]]*\])?([^\sA-Za-z{])(?:(?!\2).)*\2|\\url\{[^}]*\}|\\href\{[^}]*\}",
                         re.S)


def _tex_uncomment(text):
    """Strip LaTeX comments, leaving "%" inside verbatim material, \\verb, \\url, and \\href intact."""
    out, last = [], 0
    for m in TEX_LITERAL.finditer(text):
        out.append(re.sub(r"(?<!\\)%.*", "", text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(re.sub(r"(?<!\\)%.*", "", text[last:]))
    return "".join(out)


def strip_markup(text, suffix):
    """Return (prose, notices, incomplete). Inline math becomes the single token MATH.

    `incomplete` is True when part of the input could not be classified and was not analysed.
    """
    notices, incomplete = [], False
    if suffix == ".tex":
        # Verbatim material first: "%" or "$" inside it is literal and must not start a comment or math.
        text = _tex_uncomment(text)
        text = TEX_LITERAL.sub(lambda m: " " if m.group(1) or m.group(0).startswith("\\href") else " CODE ", text)
        text = re.sub(r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath|figure|table)\*?\}.*?"
                      r"\\end\{\1\*?\}", " ", text, flags=re.S)
        text = re.sub(r"(?<!\\)\$\$.*?\$\$|\\\[.*?\\\]", " ", text, flags=re.S)
        text = re.sub(r"(?<!\\)\$(?:[^$\\]|\\.)+\$|\\\(.*?\\\)", " MATH ", text, flags=re.S)
        text = re.sub(r"\\(?:SI|qty|SIrange|qtyrange)\*?(?:\[[^\]]*\])?\{([^}]*)\}(?:\{[^}]*\})+", r"\1 UNIT", text)
        text = re.sub(r"\\num\*?(?:\[[^\]]*\])?\{([^}]*)\}", r"\1", text)
        text = re.sub(r"~?\\(?:\w*cite\w*\*?|ref|eqref|autoref|cref|Cref|label)(?:\[[^\]]*\])*\{[^}]*\}", "", text)
        text = re.sub(r"\\(?:emph|textbf|textit|textsc|text|mathrm)\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\(?:begin|end)\{[^}]*\}|\\(?:section|subsection|paragraph)\*?\{[^}]*\}", " ", text)
        text = re.sub(r"\\[A-Za-z]+\*?", " ", text).replace("~", " ")
        text = re.sub(r"[{}]", "", text)
    elif suffix == ".typ":
        text, (n_code, n_raw), problem = _typst_scan(text)
        if n_code:
            notices.append(f"{n_code} Typst code statement(s) (#set/#show/#let/#import/#include) omitted from analysis")
        if n_raw:
            notices.append(f"{n_raw} Typst raw block(s) omitted from analysis")
        if problem:
            notices.append(problem + "; text after it was not analysed")
            incomplete = True
        # _typst_scan already replaced math, raw text, citations, labels, and emphasis markers;
        # no delimiter-based pass runs over its output, so protected spans are never reread.
    else:
        n_table = len(re.findall(r"^\s*\|.*\|\s*$", text, flags=re.M))
        if n_table:
            text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.M)
            notices.append(f"{n_table} Markdown table line(s) skipped, not analysed")
        # Block structure first (fences, indented code, headings, rules, HTML, quotes, lists),
        # then inline code, math, and comments inside one prose block at a time, so a delimiter
        # never pairs with one in another block.
        blocks, skipped, _ = _md_blocks(text)
        if skipped:
            notices.append(f"{skipped} Markdown code, heading, or HTML block(s) omitted from analysis")
        text = "\n\n".join(_md_inline(block) for block in blocks)
        # Within one line only: a bracket or parenthesis left open must not reach into later text.
        text = re.sub(r"!?\[([^\]\n]*)\]\([^)\s]*(?:[ \t]+\"[^\"\n]*\")?\)", r"\1", text)
        text = re.sub(r"\[\d+(?:\s*[,\u2013-]\s*\d+)*\]|\[@[^\]\n]*\]", "", text)
        text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\((?:S\d+)\)\s*", "", text)  # "(S1)" sentence labels used in briefs
    return re.sub(r"[ \t]+([.,;:!?])", r"\1", text), notices, incomplete


# Pandoc tex_math_dollars: "$" followed by non-space opens; "$" preceded by non-space and not
# followed by a digit closes; no blank line inside. So "$5 and $6" stays prose.
MD_INLINE_MATH = re.compile(r"(?<![\\$])\$(?=[^\s$])(?:[^$\\\n]|\\.|\n(?![ \t]*\n))+?(?<=[^\s\\])\$(?!\d)")


MD_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)$")
MD_ATX = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)")
MD_SETEXT = re.compile(r" {0,3}(?:=+|-+)[ \t]*$")
MD_RULE = re.compile(r" {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
# HTML block start of any type: types 1 to 6 by their opener, type 7 only as a complete tag alone on its line.
MD_HTML = re.compile(r" {0,3}(?:<(?:!--|\?|!|(?:script|pre|style|textarea)(?:[\s>]|$))|</?[A-Za-z][\w-]*(?:\s[^<>]*)?/?>[ \t]*$)")
# HTML block starts that may interrupt a paragraph (CommonMark types 1 to 6; type 7 may not).
MD_HTML_INTERRUPT = re.compile(
    r" {0,3}<(?:!--|\?|![A-Za-z]|!\[CDATA\[|(?:script|pre|style|textarea)(?:[\s>]|$)|/?(?:address|article|aside|base|"
    r"basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|"
    r"footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|"
    r"optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[\s/>]|$))", re.I)
MD_LIST = re.compile(r"( {0,3}(?:[-*+]|\d{1,9}[.)]))(?:[ \t]+|$)")
MD_QUOTE = re.compile(r" {0,3}> ?")


def _md_indent(line):
    """Column of the first non-space character (tabs to 4)."""
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def _md_list_item(line, interrupting):
    """List-item match, or None. While a paragraph is open, only a non-empty item, and for an
    ordered list only one numbered 1, can interrupt it (CommonMark)."""
    m = MD_LIST.match(line)
    if not m or not interrupting:
        return m
    if not line[m.end():].strip():
        return None
    marker = m.group(1).strip()
    return m if marker[0] in "-*+" or re.match(r"0*1[.)]$", marker) else None


def _md_html_end(line):
    """End-marker pattern of an HTML block of CommonMark types 1 to 5, else None."""
    t = line.lstrip()
    if re.match(r"<(?:script|pre|style|textarea)(?:[\s>]|$)", t, re.I):
        return re.compile(r"</(?:script|pre|style|textarea)>", re.I)
    for start, end in (("<!--", "-->"), ("<?", r"\?>"), ("<![CDATA[", r"\]\]>")):
        if t.startswith(start):
            return re.compile(end)
    if re.match(r"<![A-Za-z]", t):
        return re.compile(">")
    return None


def _md_fence_step(state, line):
    """Track fenced code across lines: returns the open fence (char, length) or None."""
    if state is None:
        m = MD_FENCE.match(line)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            return m.group(1)[0], len(m.group(1))
        return None
    char, length = state
    if re.match(r" {0,3}" + re.escape(char) + "{" + str(length) + r",}[ \t]*$", line):
        return None
    return state


def _md_list_item_lines(lines, i, m):
    """Collect the lines of the list item starting at lines[i] (marker match m), with the
    container prefix removed. A less indented line joins only as lazy continuation of an open
    paragraph, judged by parsing the item so far. Returns (item lines, next index)."""
    line = lines[i]
    first = line[m.end():]
    width = len(line[: m.end()].expandtabs(4))
    if not first.strip():
        width = len(m.group(1).expandtabs(4)) + 1
    item, i, blank_before = [first], i + 1, False
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            item.append("")
            blank_before = True
            i += 1
            continue
        if _md_indent(ln) >= width:
            item.append(ln.expandtabs(4)[width:])
            blank_before = False
            i += 1
            continue
        if (blank_before or _md_list_item(ln, False)
                or any(rx.match(ln) for rx in (MD_FENCE, MD_ATX, MD_RULE, MD_HTML_INTERRUPT, MD_QUOTE))
                or not _md_blocks("\n".join(item))[2]):
            break
        item.append("\u2060" + ln if MD_SETEXT.match(ln) else ln)
        i += 1
    return item, i


def _md_blocks(text):
    """Split Markdown into prose blocks, following CommonMark block rules for the blocks that
    matter here. Returns (prose blocks, number of skipped non-prose blocks, whether the text
    ends inside an open paragraph, which decides lazy continuation for an enclosing container).

    Containers first: a list item's lines (first-line content, lines indented to its content
    column, lazy continuation lines) and a block quote's lines (with lazy continuation) are
    unwrapped and parsed recursively, so their leaf blocks get the same rules. Leaf blocks:
    fenced code closes at the first fence of the same character at least as long as the opener
    (or runs to the end, as in CommonMark); indented code outside paragraphs; ATX and setext
    headings (an "=" or "-" underline under a paragraph; lazy lines are marked so they never
    form one); thematic breaks; HTML blocks with their CommonMark end conditions. Only a
    non-empty list item, and outside a list only one numbered 1, interrupts a paragraph.
    """
    lines = text.split("\n")
    blocks, cur, skipped, i, tail_open = [], [], 0, 0, False

    def flush():
        nonlocal tail_open
        if cur:
            blocks.append("\n".join(cur))
            cur.clear()
        tail_open = False

    def recurse(sub_lines):
        nonlocal skipped, tail_open
        sub, sub_skipped, sub_open = _md_blocks("\n".join(sub_lines))
        blocks.extend(sub)
        skipped += sub_skipped
        tail_open = sub_open

    while i < len(lines):
        line = lines[i]
        fence = _md_fence_step(None, line)
        if fence:
            flush()
            i += 1
            while i < len(lines) and _md_fence_step(fence, lines[i]):
                i += 1
            i, skipped = i + 1, skipped + 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        if not cur and _md_indent(line) >= 4:
            while i < len(lines) and (not lines[i].strip() or _md_indent(lines[i]) >= 4):
                i += 1
            skipped, tail_open = skipped + 1, False
            continue
        if MD_ATX.match(line):
            flush()
            i, skipped = i + 1, skipped + 1
            continue
        if cur and MD_SETEXT.match(line):
            cur.clear()  # the paragraph above is a heading
            i, skipped, tail_open = i + 1, skipped + 1, False
            continue
        if MD_RULE.match(line):
            flush()
            i += 1
            continue
        if MD_HTML_INTERRUPT.match(line) or (MD_HTML.match(line) and not cur):
            flush()
            end = _md_html_end(line)
            if end is None:  # types 6 and 7 end at a blank line
                while i < len(lines) and lines[i].strip():
                    i += 1
            else:  # types 1 to 5 end at the line that contains their end marker
                while i < len(lines) and not end.search(lines[i]):
                    i += 1
                i += 1
            skipped += 1
            continue
        if MD_QUOTE.match(line):
            flush()
            quoted = []
            # Quote lines, plus lazy continuation lines that join the quote's last paragraph.
            # A lazy line cannot be a setext underline, so it is marked to stay text in the recursion.
            while i < len(lines):
                if MD_QUOTE.match(lines[i]):
                    quoted.append(MD_QUOTE.sub("", lines[i], count=1))
                elif (quoted and lines[i].strip() and _md_blocks("\n".join(quoted))[2]
                      and not _md_list_item(lines[i], False)
                      and not any(rx.match(lines[i]) for rx in (MD_FENCE, MD_ATX, MD_RULE, MD_HTML_INTERRUPT))):
                    quoted.append("\u2060" + lines[i] if MD_SETEXT.match(lines[i]) else lines[i])
                else:
                    break
                i += 1
            recurse(quoted)
            continue
        m = _md_list_item(line, bool(cur))
        if m:
            flush()
            item, i = _md_list_item_lines(lines, i, m)
            recurse(item)
            continue
        cur.append(line)
        tail_open = True
        i += 1
    ends_open = tail_open
    flush()
    return blocks, skipped, ends_open


def _md_inline(block):
    """Code spans, then display and inline math, then HTML comments, within one block."""
    block = _md_code_spans(block)
    block = re.sub(r"(?<!\\)\$\$.*?\$\$", " ", block, flags=re.S)
    block = MD_INLINE_MATH.sub(" MATH ", block)
    return re.sub(r"<!--.*?-->", "", block, flags=re.S)


def _md_code_spans(text):
    """Replace Markdown code spans with CODE. A backslash-escaped backtick is literal text;
    a run of N backticks opens a span only if a run of exactly N backticks closes it in the
    same block (the caller passes one block); otherwise the run stays literal."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            out.append(text[i: i + 2])
            i += 2
            continue
        if c != "`":
            out.append(c)
            i += 1
            continue
        run = len(text[i:]) - len(text[i:].lstrip("`"))
        limit = n  # callers pass one block
        j, close = i + run, -1
        while True:
            j = text.find("`" * run, j, limit)
            if j < 0:
                break
            k = j + run
            while k < n and text[k] == "`":
                k += 1
            if k - j == run:
                close = k
                break
            j = k
        if close < 0:
            out.append(text[i: i + run])
            i += run
        else:
            out.append(" CODE ")
            i = close
    return "".join(out)


TYP_IDENT = re.compile(r"[A-Za-z_][\w-]*")
TYP_STMT_KW = {"set", "show", "let", "import", "include"}
# Valid Typst keywords this scanner does not parse: met after "#", they stop the analysis.
TYP_STOP_KW = {"if", "else", "for", "in", "while", "break", "continue", "return", "context", "as", "and", "or", "not"}


def _typst_hash_kind(text, i):
    """Classify the "#" at i by its complete identifier: "stmt", "stop", "name", or "other"."""
    m = TYP_IDENT.match(text, i + 1)
    if not m:
        return "other"
    tok = m.group(0)
    return "stmt" if tok in TYP_STMT_KW else "stop" if tok in TYP_STOP_KW else "name"


def _typst_block_comment_end(text, i):
    """Index just past the (nested) block comment starting at i, or None if it never closes."""
    depth, j = 0, i
    while j < len(text):
        if text.startswith("/*", j):
            depth, j = depth + 1, j + 2
        elif text.startswith("*/", j):
            depth, j = depth - 1, j + 2
            if depth == 0:
                return j
        else:
            j += 1
    return None


def _typst_string_end(text, j):
    """Index just past the string literal whose opening quote is at j, or None."""
    k, n = j + 1, len(text)
    while k < n:
        if text[k] == "\\":
            k += 2
        elif text[k] == '"':
            return k + 1
        else:
            k += 1
    return None


def _typst_skip_comment(text, j):
    """If a comment starts at j, return the index after it (None if unclosed); else return j."""
    if text.startswith("/*", j):
        return _typst_block_comment_end(text, j)
    if text.startswith("//", j) and (j == 0 or text[j - 1] != ":"):
        while j < len(text) and text[j] != "\n":
            j += 1
    return j


def _typst_raw_end(text, i):
    """Index just past the raw text whose backtick run starts at i, or None if it never closes.

    One backtick opens inline raw, three or more open a raw block closed by a run of the same
    length; two backticks are an empty raw. Comment markers inside raw text are literal.
    """
    run = len(text[i:]) - len(text[i:].lstrip("`"))
    if run == 2:
        return i + 2
    j = i + run
    while True:
        j = text.find("`" * run, j)
        if j < 0:
            return None
        k = j + run
        while k < len(text) and text[k] == "`":
            k += 1
        if k - j == run:
            return k
        j = k


def _typst_math_end(text, i):
    """Index just past the math span whose "$" is at i, or None if it never closes.

    Inside math, escapes, strings, comments, and embedded "#" expressions are tracked.
    """
    j, n = i + 1, len(text)
    while j < n:
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            end = _typst_string_end(text, j)
        elif c == "#" and j + 1 < n and not text[j + 1].isspace():
            end = _typst_hash_end(text, j)
        elif c == "$":
            return j + 1
        else:
            end = _typst_skip_comment(text, j)
            if end == j:
                j += 1
                continue
        if end is None:
            return None
        j = end
    return None


def _typst_code_scan(text, i, mode):
    """Scan Typst code from i, tracking strings, comments, nesting, and [...] content blocks.

    mode "stmt": return (index, terminator) at the first top-level ";" or newline (or end of text).
    mode "group": text[i] is "(", "[", or "{"; return (index just past its match, "").
    In code, strings are literals and brackets nest. Inside a [...] content block the text is
    markup: quotes and parentheses are ordinary characters, escapes, raw text, and comments
    apply, and a nested "#" expression is scanned recursively. Returns None when a boundary
    cannot be found.
    """
    stack, j, n = [], i, len(text)
    while j < n:
        c = text[j]
        if stack and stack[-1] == "[":
            if c == "\\":
                j += 2
                continue
            if c in "`$":
                end = _typst_raw_end(text, j) if c == "`" else _typst_math_end(text, j)
                if end is None:
                    return None
                j = end
                continue
            k = _typst_skip_comment(text, j)
            if k is None:
                return None
            if k != j:
                j = k
                continue
            if c == "#" and j + 1 < n and not text[j + 1].isspace():
                end = _typst_hash_end(text, j)
                if end is None:
                    return None
                j = end
                continue
            if c == "[":
                stack.append("[")
            elif c == "]":
                stack.pop()
                if mode == "group" and not stack:
                    return j + 1, ""
            j += 1
            continue
        k = _typst_skip_comment(text, j)
        if k is None:
            return None
        if k != j:
            j = k
            continue
        if c == "`":
            end = _typst_raw_end(text, j)
            if end is None:
                return None
            j = end
            continue
        if c == '"':
            end = _typst_string_end(text, j)
            if end is None:
                return None
            j = end
            continue
        if c in "([{":
            stack.append(c)
        elif c in ")]}":
            if not stack:
                if mode == "stmt":
                    return j, c  # closer of an enclosing block: the statement ends here
                return None
            stack.pop()
            if mode == "group" and not stack:
                return j + 1, ""
        elif mode == "stmt" and not stack and c in ";\n":
            return j, c
        j += 1
    if mode == "stmt" and not stack:
        return n, ""
    return None


def _typst_expr_parts(text, i):
    """(end, name, content-group spans) of a named expression such as #f(...)[...]; None if unclosed."""
    m = TYP_IDENT.match(text, i + 1)
    name, j, content = m.group(0), m.end(), []
    while j < len(text):
        f = re.match(r"\.[A-Za-z_][\w-]*", text[j:])
        if f:
            j += f.end()
        elif text[j] in "([":
            r = _typst_code_scan(text, j, "group")
            if r is None:
                return None
            if text[j] == "[":
                content.append((j + 1, r[0] - 1))
            j = r[0]
        else:
            break
    return j, name, content


def _typst_expr_end(text, i):
    """End of a named expression such as #name, #a.b, #f(...)[...]; None if a group never closes."""
    parts = _typst_expr_parts(text, i)
    return None if parts is None else parts[0]


def _typst_hash_end(text, i):
    """End of the embedded expression or statement introduced by the "#" at i.

    None when the form is unsupported (control-flow keywords and anything not listed) or its
    extent cannot be determined.
    """
    kind = _typst_hash_kind(text, i)
    if kind == "stmt":
        r = _typst_code_scan(text, i, "stmt")
        return None if r is None else r[0] + (1 if r[1] == ";" else 0)
    if kind == "name":
        return _typst_expr_end(text, i)
    if kind == "stop":
        return None
    nxt = text[i + 1] if i + 1 < len(text) else ""
    if nxt == '"':
        return _typst_string_end(text, i + 1)
    if nxt and nxt in "([{":
        r = _typst_code_scan(text, i + 1, "group")
        return r[0] if r else None
    return None


TYP_TEXT_FUNCS = {"emph", "strong", "text", "smallcaps", "underline", "overline", "strike", "highlight", "sub",
                  "super", "footnote"}
TYP_DROP_FUNCS = {"cite", "ref", "label", "h", "v"}
TYP_BREAK_FUNCS = {"linebreak", "parbreak", "pagebreak", "colbreak"}


def _typst_scan(text):
    """Turn Typst markup into prose for analysis. Returns (prose, (n_code, n_raw), problem).

    Single pass, no later regex over its output: every unescaped "#" is classified before any
    comment delimiter after it is read. Statements (#set/#show/#let/#import/#include) are
    dropped; text functions (#emph[...], #strong[...], ...) contribute their scanned content;
    citations, references, labels, and spacing calls are dropped; breaks become paragraph or
    line breaks; any other expression becomes the placeholder "#EXPR" (count provisional).
    Math becomes "MATH", inline raw "CODE", raw blocks and headings are dropped, emphasis
    markers are removed, and escapes yield their character. If a construct cannot be
    classified or its end found, scanning stops and `problem` says so.
    """
    out, i, n, n_code, n_raw = [], 0, len(text), 0, 0
    at_line_start = True

    def stop(k):
        return ("".join(out), (n_code, n_raw),
                f"could not determine where the Typst construct at line {text.count(chr(10), 0, k) + 1} ends "
                "with the supported scanner")

    while i < n:
        c = text[i]
        if at_line_start and c in " \t":
            out.append(c)
            i += 1
            continue
        if at_line_start and re.match(r"=+\s", text[i:]):
            while i < n and text[i] != "\n":  # heading line
                i += 1
            i += 1
            continue
        if c == "#" and i + 1 < n and not text[i + 1].isspace():
            kind = _typst_hash_kind(text, i)
            if kind == "stmt":
                r = _typst_code_scan(text, i, "stmt")
                if r is None:
                    return stop(i)
                end, term = r
                n_code += 1
                if term == ";":
                    i, at_line_start = end + 1, False
                elif term == "\n" and at_line_start:
                    i = end + 1  # a whole code line: drop its newline so no blank line splits the paragraph
                else:
                    i = end
                continue
            if kind == "name":
                parts = _typst_expr_parts(text, i)
                if parts is None:
                    return stop(i)
                end, name, content = parts
                if name in TYP_TEXT_FUNCS and content:
                    a, b = content[-1]
                    inner, (ic, ir), problem = _typst_scan(text[a:b])
                    n_code, n_raw = n_code + ic, n_raw + ir
                    if problem:
                        return stop(a)
                    out.append(inner)
                elif name in TYP_BREAK_FUNCS:
                    out.append("\n\n" if name != "linebreak" else " ")
                elif name not in TYP_DROP_FUNCS:
                    out.append(" #EXPR ")
                i, at_line_start = end, False
                continue
            end = _typst_hash_end(text, i)
            if end is None:
                return stop(i)
            out.append(" #EXPR ")
            i, at_line_start = end, False
            continue
        at_line_start = False
        if c == "\\" and i + 1 < n:
            out.append(" " if text[i + 1] == "\n" else text[i + 1])
            i += 2
            continue
        if c == "`":
            end = _typst_raw_end(text, i)
            if end is None:
                return stop(i)
            if text.startswith("```", i):
                n_raw += 1  # raw block: omitted from prose analysis
            else:
                out.append(" CODE ")
            i = end
            continue
        if c == "$":
            end = _typst_math_end(text, i)
            if end is None:
                return stop(i)
            out.append(" MATH ")
            i = end
            continue
        if text.startswith("/*", i):
            end = _typst_block_comment_end(text, i)
            if end is None:
                return stop(i)
            i = end
            continue
        if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
            while i < n and text[i] != "\n":
                i += 1
            continue
        m = re.match(r"@[A-Za-z_][\w:-]*|<[A-Za-z_][\w:.-]*>", text[i:]) if c in "@<" and (i == 0 or not text[i - 1].isalnum()) else None
        if m:
            i += m.end()  # citation, reference, or label
            continue
        if c in "*_":
            i += 1  # strong / emphasis markers
            continue
        out.append(c)
        if c == "\n":
            at_line_start = True
        i += 1
    return "".join(out), (n_code, n_raw), ""


def paragraphs(text):
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(line.strip() for line in block.strip().splitlines())
        if re.search(r"[A-Za-z]{2,}", block):
            out.append(block)
    return out


def sentences(par):
    protected = ABBREV.sub(lambda m: m.group(0).replace(".", "\u2024"), par)
    parts = re.split(r"(?:(?<=[.!?])|(?<=[.!?][\"'\u201d\u2019)\]]))\s+(?=[\"'\u201c\u2018(\[]?[A-Za-z0-9])", protected)
    return [p.replace("\u2024", ".").strip() for p in parts if p.strip()]


def lemma(word):
    w = word.lower().strip("'\u2019\".,;:!?()[]{}")
    for suf, rep in (("ies", "y"), ("is", ""), ("es", ""), ("ing", ""), ("ed", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss"):
            w = w[: -len(suf)] + rep
            break
    return w.rstrip("e") if len(w) > 4 else w


def related(a, b):
    la, lb = lemma(a), lemma(b)
    if la == lb:
        return True
    short, long_ = sorted((la, lb), key=len)
    return len(short) >= 4 and long_.startswith(short) and len(long_) - len(short) <= 3


# ---------------------------------------------------------------- checks
def comma_interruptions(sent):
    pieces = sent.split(",")
    if len(pieces) < 3:
        return []
    short_items = sum(1 for p in pieces[1:-1] if len(p.split()) <= 3)
    if short_items >= 2 and re.search(r",\s+(?:and|or)\s", sent):
        return []  # looks like a list
    hits = []
    for i in range(1, len(pieces) - 1):
        seg, before, after = pieces[i].strip(), ",".join(pieces[:i]).strip(), pieces[i + 1].strip()
        if not (1 <= len(seg.split()) <= 15) or len(before.split()) < 2:
            continue
        if re.match(r"^(and|or|but|so|yet)\b", after, re.I) or re.match(r"^(and|or|but)\b", seg, re.I):
            continue
        if PAREN_START.match(seg):
            hits.append(seg)
    return hits


def lexicon_hits(sent, allow):
    masked = sent
    for term in allow:
        masked = re.sub(re.escape(term), lambda m: "\u2591" * len(m.group(0)), masked, flags=re.I)
    out = []
    for kind, rx in LEX_RE.items():
        hits = sorted({m.group(0) for m in rx.finditer(masked)})
        if hits:
            out.append((kind, ", ".join(hits)))
    return out


def check_paragraph(par, max_words, allow):
    sents = sentences(par)
    report = {"sentences": []}
    seen = []
    for i, s in enumerate(sents, 1):
        words = s.split()
        flags = []
        body = re.sub(r"https?://\S+", "", s)
        if len(words) > max_words:
            flags.append(("long", f"{len(words)} words > {max_words} (warning, not a split order)"))
        joins = CLAUSE_JOIN.findall(body)
        if len(words) > 20 and len(joins) >= 2:
            flags.append(("propositions", f"{len(words)} words with {len(joins)} clause joins; count the claims"))
        for m in DASH.finditer(s):
            flags.append(("dash", repr(m.group(0))))
        exempt = {i for m in COLON_EXEMPT.finditer(body) for i in range(m.start(), m.end()) if body[i] == ":"}
        for m in re.finditer(r":", body):
            if m.start() not in exempt:
                flags.append(("colon", body[max(0, m.start() - 30): m.end()]))
        for m in re.finditer(r";", body):
            flags.append(("semicolon", body[max(0, m.start() - 30): m.end()]))
        for seg in comma_interruptions(s):
            flags.append(("comma-enclosed-phrase", seg + " (does it split subject-verb or verb-object?)"))
        for m in WITH_ING.finditer(s):
            flags.append(("with-ing", m.group(0)))
        m = TRAIL_ING.search(s)
        if m:
            flags.append(("trailing-ing", m.group(0).strip(", ")))
        m = STRANDED.search(s)
        if m:
            flags.append(("stranded-auxiliary", m.group(0)))
        m = BARE_OPENER.match(s)
        if m:
            flags.append(("bare-opener", m.group(0)))
        for m in DEMONSTRATIVE.finditer(s):
            det, noun = m.group(1), m.group(2)
            if det.lower() == "that" and m.start() > 0:
                continue
            if noun.lower() in STOP or noun.lower() in VERBISH:
                continue
            n = sum(1 for w in seen if related(noun, w))
            note = {0: "no earlier occurrence of the word", 1: "1 earlier occurrence of the word"}.get(
                n, f"{n} earlier occurrences of the word, not necessarily distinct referents")
            flags.append(("demonstrative", f"'{det} {noun}': {note} (check the referent)"))
        prons = [m.group(0) for m in PRONOUN.finditer(s)]
        if prons:
            flags.append(("pronoun", ", ".join(prons) + " (name the antecedent)"))
        flags += lexicon_hits(s, allow)
        if re.search(r"\\[A-Za-z]|#[a-z]+[\[(]|#EXPR|\{|\}", s):
            flags.append(("unparsed-markup", "markup left in this sentence; counts and flags may be off"))
        report["sentences"].append({"n": i, "words": len(words), "text": s, "flags": flags,
                                    "provisional_count": any(k == "unparsed-markup" for k, _ in flags)})
        seen += re.findall(r"[A-Za-z][A-Za-z-]+", s)
    content = [w for w in re.findall(r"[A-Za-z][A-Za-z-]+", par) if w.lower() not in STOP and len(w) >= 4 and w not in ("MATH", "CODE", "EXPR")]
    groups = {}
    for w in content:
        groups.setdefault(lemma(w), []).append(w)
    report["repeats"] = sorted(((k, len(v), sorted(set(v))) for k, v in groups.items() if len(v) >= 2),
                               key=lambda t: (-t[1], t[0]))
    report["word_counts"] = [s["words"] for s in report["sentences"]]
    report["total_words"] = sum(report["word_counts"])
    return report


# ---------------------------------------------------------------- compare
MATH_RAW = re.compile(r"\\begin\{(?:equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?"
                      r"\\end\{(?:equation|align|gather|multline|eqnarray|displaymath)\*?\}|"
                      r"(?<!\\)\$\$.*?\$\$|(?<!\\)\$(?:[^$\\]|\\.)+\$|\\\(.*?\\\)|\\\[.*?\\\]", re.S)
CITE_RAW = re.compile(r"\\\w*cite\w*\*?(?:\[[^\]]*\])*\{([^}]*)\}|#cite\(<([^>]+)>[^)]*\)|(?<![\w.\\])@([A-Za-z][\w:-]*)|"
                      r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]")
QTY_RAW = re.compile(r"\\(?:SI|qty|SIrange|qtyrange|num)\*?(?:\[[^\]]*\])?(?:\{[^}]*\})+")
# LaTeX constructs that carry no protected content of their own (their text is analysed as prose).
TEX_HANDLED = re.compile(r"\\(?:(?:emph|textbf|textit|textsc|text|mathrm|footnote)\{|(?:ref|eqref|autoref|cref|Cref|label)\{|"
                         r"(?:begin|end)\{[^}]*\}|(?:section|subsection|subsubsection|paragraph)\*?\{|item\b|par\b)")
TEX_CONSTRUCT = re.compile(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])*(?:\{[^}]*\})*")
KNOWN_TYP = set("cite emph strong text smallcaps underline set show let import include".split())
UNIT = r"(?:\s?(?:%|percent|ms|s|min|h|K|eV|keV|MeV|GeV|TeV|m|cm|mm|nm|kg|g|Hz|kHz|MHz|GHz|dB|sigma|σ|x|×))?"
NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:[eE][-+]?\d+)?" + UNIT + r"(?![\w])")
NEG = re.compile(r"\b(?:not|no|never|none|neither|nor|cannot|without)\b|n't\b", re.I)
HEDGE = re.compile(r"\b(?:may|might|could|suggests?|likely|unlikely|approximately|roughly|appears?|seems?|"
                   r"indicates?|possibly|partly|partially|largely|mostly|typically|often)\b", re.I)
BOUND = re.compile(r"\b(?:at most|at least|more than|less than|fewer than|up to|no more than|no less than)\b", re.I)


def _cites(raw):
    keys = []
    for m in CITE_RAW.finditer(raw):
        if m.group(1):
            keys += [k.strip() for k in m.group(1).split(",")]
        elif m.group(2) or m.group(3):
            keys.append(m.group(2) or m.group(3))
        elif m.group(4):
            for part in re.split(r"\s*,\s*", m.group(4)):
                if re.search(r"[\u2013-]", part):
                    a, b = re.split(r"\s*[\u2013-]\s*", part)
                    keys += [f"[{n}]" for n in range(int(a), int(b) + 1)]
                else:
                    keys.append(f"[{part}]")
    return Counter(keys)


def _unassessed(raw, suffix):
    """Constructs that are neither compared nor handled as non-protected markup, verbatim."""
    found = []
    if suffix == ".tex":
        consumed = [m.span() for rx in (MATH_RAW, CITE_RAW, QTY_RAW) for m in rx.finditer(raw)]
        for m in re.finditer(r"\\[A-Za-z]+", raw):
            if any(a <= m.start() < b for a, b in consumed) or TEX_HANDLED.match(raw, m.start()):
                continue
            found.append(TEX_CONSTRUCT.match(raw, m.start()).group(0))
    elif suffix == ".typ":
        for m in re.finditer(r"#([a-z][\w-]*)[(\[][^\n]{0,60}", raw):
            if m.group(1) not in KNOWN_TYP:
                found.append(m.group(0))
    return Counter(found)


def _sentences_of(raw, suffix):
    prose, notices, incomplete = strip_markup(raw, suffix)
    return [s for p in paragraphs(prose) for s in sentences(p)], notices, incomplete


def _token_and_context(sents, rx, before, after):
    """Matched tokens, and each token with neighbouring words inside its own sentence."""
    tokens, contexts = Counter(), Counter()
    for s in sents:
        for m in rx.finditer(s):
            tok = m.group(0).lower()
            left = s[: m.start()].split()[-before:]
            right = s[m.end():].split()[:after]
            tokens[tok] += 1
            contexts[(tok, " ".join(left + ["[" + m.group(0) + "]"] + right).lower().strip(".,;:"))] += 1
    return tokens, contexts


def fidelity(old_raw, old_suffix, new_raw, new_suffix):
    """Return (differences, unassessed constructs, notes, incomplete)."""
    if old_suffix == ".tex":
        old_raw = _tex_uncomment(old_raw)
    if new_suffix == ".tex":
        new_raw = _tex_uncomment(new_raw)
    old_s, old_notes, old_inc = _sentences_of(old_raw, old_suffix)
    new_s, new_notes, new_inc = _sentences_of(new_raw, new_suffix)
    old_p, new_p = " ".join(old_s), " ".join(new_s)
    seen_any = []

    def diff(a, b):
        seen_any.append(bool(a or b))
        return {"only_in_old": sorted((a - b).elements()), "only_in_new": sorted((b - a).elements())}

    out = {
        "math spans (verbatim)": diff(Counter(m.group(0) for m in MATH_RAW.finditer(old_raw)),
                                      Counter(m.group(0) for m in MATH_RAW.finditer(new_raw))),
        "citation keys": diff(_cites(old_raw), _cites(new_raw)),
        "quantity macros (verbatim)": diff(Counter(m.group(0) for m in QTY_RAW.finditer(old_raw)),
                                           Counter(m.group(0) for m in QTY_RAW.finditer(new_raw))),
        "hedges": diff(Counter(m.group(0).lower() for m in HEDGE.finditer(old_p)),
                       Counter(m.group(0).lower() for m in HEDGE.finditer(new_p))),
        "scope words and bounds": diff(Counter(m.group(0).lower() for rx in (LEX_RE["scope"], BOUND) for m in rx.finditer(old_p)),
                                       Counter(m.group(0).lower() for rx in (LEX_RE["scope"], BOUND) for m in rx.finditer(new_p))),
    }
    for name, rx, before, after in (("numbers with units", NUMBER, 2, 1), ("negations", NEG, 2, 2)):
        ta, ca = _token_and_context(old_s, rx, before, after)
        tb, cb = _token_and_context(new_s, rx, before, after)
        out[name] = diff(ta, tb)
        changed = set(ta - tb) | set(tb - ta)
        out[name + ": same token, new context (review)"] = {
            "only_in_old": sorted(c for (t, c) in (ca - cb).elements() if t not in changed),
            "only_in_new": sorted(c for (t, c) in (cb - ca).elements() if t not in changed)}
    ua, ub = _unassessed(old_raw, old_suffix), _unassessed(new_raw, new_suffix)
    unassessed = {"both": sorted((ua & ub).elements()), "old_only": sorted((ua - ub).elements()),
                  "new_only": sorted((ub - ua).elements())}
    notes = [f"old: {n}" for n in old_notes] + [f"new: {n}" for n in new_notes]
    if not any(seen_any):
        notes.append("no supported comparison items found in either input")
    return out, unassessed, notes, old_inc or new_inc


# ---------------------------------------------------------------- io
def show(path, reports):
    print(f"== {path}")
    for p, r in enumerate(reports, 1):
        marks = [f"{s['words']}*" if any(k == "unparsed-markup" for k, _ in s["flags"]) else str(s["words"])
                 for s in r["sentences"]]
        print(f"\n-- paragraph {p}: {len(r['word_counts'])} sentences, {r['total_words']} words; "
              f"per sentence {' / '.join(marks)}" + ("  (* provisional: markup left in sentence)" if "*" in "".join(marks) else ""))
        for s, mark in zip(r["sentences"], marks):
            print(f"  S{s['n']} ({mark}w) {s['text'][:90]}{'...' if len(s['text']) > 90 else ''}")
            for kind, detail in s["flags"]:
                print(f"      [{kind}] {detail}")
        if r["repeats"]:
            print("  repeated content words: " + "; ".join(f"{'/'.join(v)} x{n}" for _, n, v in r["repeats"]))
    print("\n  (candidates only: judge each in context; a missing flag does not mean the text is clean)")


def load(path):
    if path == "-":
        return sys.stdin.read(), ".txt"
    p = Path(path)
    return p.read_text(encoding="utf-8"), p.suffix.lower()


def safe_load(path):
    try:
        return load(path)
    except (OSError, UnicodeDecodeError) as e:
        print(f"== {path}: cannot read ({e.__class__.__name__}: {e})", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 epilog="Word count: whitespace tokens after normalisation; inline math = 1 word.")
    ap.add_argument("files", nargs="*", help="files to check, '-' for stdin")
    ap.add_argument("--para", type=int, help="check only paragraph N (1-based, after markup removal)")
    ap.add_argument("--max-words", type=int, default=30, help="long-sentence warning threshold (default 30)")
    ap.add_argument("--allow", action="append", default=[], help="technical term to exempt from word lists (repeatable)")
    ap.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"), help="surface diff of supported protected tokens")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 if an unexempted dash or colon candidate remains")
    a = ap.parse_args()

    if a.compare:
        old, new = safe_load(a.compare[0]), safe_load(a.compare[1])
        if old is None or new is None:
            return 2
        diff, unassessed, notes, incomplete = fidelity(old[0], old[1], new[0], new[1])
        for n in notes:
            print(f"note: {n}", file=sys.stderr)
        if a.json:
            print(json.dumps({"comparison": diff, "unassessed": unassessed, "notes": notes, "incomplete": incomplete},
                             indent=1, ensure_ascii=False))
        else:
            print("Surface comparison of supported protected tokens. No difference here does not prove that meaning,")
            print("claim strength, or the scope of each citation and negation was preserved; check those by reading.")
            for k, v in diff.items():
                print(f"  {k}")
                print(f"      only in old: {v['only_in_old'] or 'none'}")
                print(f"      only in new: {v['only_in_new'] or 'none'}")
            print("  not compared (unsupported constructs; 'both' means present in both, not unchanged in meaning)")
            for side in ("both", "old_only", "new_only"):
                print(f"      {side}: {unassessed[side] or 'none'}")
        return 2 if incomplete else 0
    if not a.files:
        ap.error("give files or --compare OLD NEW")
    allow = TECH_TERMS + a.allow
    bad, failed = False, False
    for f in a.files:
        loaded = safe_load(f)
        if loaded is None:
            failed = True
            continue
        prose, notices, incomplete = strip_markup(*loaded)
        for n in notices:
            print(f"note ({f}): {n}", file=sys.stderr)
        failed |= incomplete
        pars = paragraphs(prose)
        if a.para:
            pars = pars[a.para - 1: a.para]
        if not pars:
            print(f"== {f}: no prose found after markup removal", file=sys.stderr)
            failed = True
            continue
        reports = [check_paragraph(p, a.max_words, allow) for p in pars]
        if a.json:
            print(json.dumps({"file": f, "notes": notices, "incomplete": incomplete, "paragraphs": reports},
                             indent=1, ensure_ascii=False))
        else:
            show(f, reports)
        bad |= any(k in ("dash", "colon") for r in reports for s in r["sentences"] for k, _ in s["flags"])
    if failed:
        return 2
    return 1 if a.strict and bad else 0


if __name__ == "__main__":
    sys.exit(main())
