#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

RECOGNIZED_FILES = {"plot_manifest.json", "report_versions.json", "report.md"}
SECTION_HINTS = {"results", "methodology", "validation", "comparison", "testing"}
CHANGE_TYPES = {"plot_restyle", "plot_new", "text_fix", "section_rewrite", "style_fix", "gap_fill"}
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")
PLACEHOLDER_PATTERN = re.compile(r"\{[A-Za-z0-9_]+\}")
WORD_PATTERN = re.compile(r"\b[\w.-]+\b")
EVIDENCE_BLOCK_PATTERN = re.compile(r"<!--\s*EVIDENCE BLOCK:", re.IGNORECASE)
EVIDENCE_BLOCK_ID_PATTERN = re.compile(r"<!--\s*EVIDENCE BLOCK:\s*(ev-[A-Za-z0-9_-]+)\s*-->", re.IGNORECASE)
WORD_BUDGET_PATTERN = re.compile(r"<!--\s*WORD_BUDGET:\s*(\d+)\s*-->", re.IGNORECASE)
# Single-line $$..$$ display math (catches `$$x = y$$` written inline; allowed
# tokens between are anything except a $ or newline).
SINGLE_LINE_DISPLAY_MATH_PATTERN = re.compile(r"\$\$[^\$\n]+\$\$")
# Code fences and inline code spans get masked before unicode-math scanning so
# that examples-of-bad-syntax inside fenced blocks do not produce false errors.
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
# Unicode math characters that should be replaced with LaTeX equivalents in
# the report body. Each entry maps the offending character to its LaTeX form.
UNICODE_MATH_CHARS: dict[str, str] = {
    # Greek lowercase
    "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$",
    "ε": r"$\varepsilon$", "ζ": r"$\zeta$", "η": r"$\eta$", "θ": r"$\theta$",
    "ι": r"$\iota$", "κ": r"$\kappa$", "λ": r"$\lambda$", "μ": r"$\mu$",
    "ν": r"$\nu$", "ξ": r"$\xi$", "π": r"$\pi$", "ρ": r"$\rho$",
    "σ": r"$\sigma$", "τ": r"$\tau$", "υ": r"$\upsilon$", "φ": r"$\varphi$",
    "χ": r"$\chi$", "ψ": r"$\psi$", "ω": r"$\omega$",
    # Greek uppercase used in math
    "Γ": r"$\Gamma$", "Δ": r"$\Delta$", "Θ": r"$\Theta$", "Λ": r"$\Lambda$",
    "Ξ": r"$\Xi$", "Π": r"$\Pi$", "Σ": r"$\Sigma$", "Φ": r"$\Phi$",
    "Ψ": r"$\Psi$", "Ω": r"$\Omega$",
    # Number sets
    "ℝ": r"$\mathbb{R}$", "ℕ": r"$\mathbb{N}$", "ℤ": r"$\mathbb{Z}$",
    "ℚ": r"$\mathbb{Q}$", "ℂ": r"$\mathbb{C}$",
    # Operators
    "≈": r"$\approx$", "≠": r"$\neq$", "≤": r"$\leq$", "≥": r"$\geq$",
    "≪": r"$\ll$", "≫": r"$\gg$", "±": r"$\pm$", "∓": r"$\mp$",
    "×": r"$\times$", "·": r"$\cdot$", "÷": r"$\div$",
    "∝": r"$\propto$", "≡": r"$\equiv$", "≅": r"$\cong$", "∼": r"$\sim$",
    # Sets / logic
    "∈": r"$\in$", "∉": r"$\notin$", "⊂": r"$\subset$", "⊆": r"$\subseteq$",
    "⊃": r"$\supset$", "⊇": r"$\supseteq$", "∪": r"$\cup$", "∩": r"$\cap$",
    "∀": r"$\forall$", "∃": r"$\exists$", "∅": r"$\emptyset$",
    "¬": r"$\neg$", "∧": r"$\land$", "∨": r"$\lor$",
    # Arrows
    "→": r"$\to$", "←": r"$\leftarrow$", "↔": r"$\leftrightarrow$",
    "⇒": r"$\Rightarrow$", "⇐": r"$\Leftarrow$", "⇔": r"$\Leftrightarrow$",
    "↦": r"$\mapsto$",
    # Calculus / sums
    "∂": r"$\partial$", "∇": r"$\nabla$", "∫": r"$\int$",
    "∑": r"$\sum$", "∏": r"$\prod$", "√": r"$\sqrt{\cdot}$",
    # Constants / misc
    "∞": r"$\infty$", "ℏ": r"$\hbar$", "ℓ": r"$\ell$", "°": r"$^{\circ}$",
    # Common superscripts/subscripts
    "²": r"$^2$", "³": r"$^3$", "⁴": r"$^4$", "⁵": r"$^5$", "⁶": r"$^6$",
    "⁷": r"$^7$", "⁸": r"$^8$", "⁹": r"$^9$", "⁰": r"$^0$", "¹": r"$^1$",
    "ⁿ": r"$^n$",
    "₀": r"$_0$", "₁": r"$_1$", "₂": r"$_2$", "₃": r"$_3$", "₄": r"$_4$",
    "₅": r"$_5$", "₆": r"$_6$", "₇": r"$_7$", "₈": r"$_8$", "₉": r"$_9$",
    "ᵢ": r"$_i$", "ⱼ": r"$_j$", "ₖ": r"$_k$", "ₙ": r"$_n$",
    # Hat/bar/tilde combining marks rarely appear standalone, so omitted.
}
# "see figure"-style passive references that often signal an uninterpreted plot.
PASSIVE_FIGURE_PATTERN = re.compile(
    r"\b(see|refer to|as shown in|illustrated in|depicted in)\s+"
    r"(the\s+)?(figure|fig\.?|plot|chart|graph)(\s+(below|above|\d+))?",
    re.IGNORECASE,
)
# Bare numeric token used as a quick proxy for a quantitative observation.
QUANTITATIVE_HINT_PATTERN = re.compile(
    r"(?<![A-Za-z_])(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?(?![A-Za-z_])",
    re.IGNORECASE,
)
# Likely "list of figures" appendix table heading.
FIGURE_TABLE_HEADING_PATTERN = re.compile(
    r"^#{1,6}\s+.*\b(list of figures|figure inventory|all figures|figure index|table of figures)\b",
    re.IGNORECASE | re.MULTILINE,
)
REQUIRED_SECTION_GROUPS: dict[str, tuple[str, ...]] = {
    "background": ("research background", "background"),
    "analysis": ("analysis / discovery summary", "analysis framework", "discovery summary", "analysis summary"),
    "methodology": ("methodology", "method"),
    "results": ("results & visualization", "results and visualization", "results"),
    "conclusion": ("conclusion", "conclusions"),
}
RECOMMENDED_SECTION_GROUPS: dict[str, tuple[str, ...]] = {
    "implementation": ("implementation / experimental setup", "implementation", "experimental setup", "materials"),
    "validation": ("validation", "validation & limitations", "validation and limitations"),
}


def result_template(path: Path) -> dict[str, Any]:
    return {
        "artifact": str(path),
        "status": "pass",
        "errors": [],
        "warnings": [],
    }


def report_root_for(path: Path) -> Path:
    if path.name == "plot_manifest.json" and path.parent.name == "plots":
        return path.parent.parent
    return path.parent


def resolve_local_path(target: str, base_dir: Path) -> Path | None:
    cleaned = target.strip()
    if not cleaned:
        return None
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1].strip()
    if " " in cleaned and not cleaned.startswith("/"):
        cleaned = cleaned.split(" ", 1)[0]
    if cleaned.startswith(("http://", "https://", "mailto:")):
        return None
    path = Path(cleaned)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plot_manifest(path: Path, data: Any) -> dict[str, Any]:
    result = result_template(path)
    report_root = report_root_for(path)
    if not isinstance(data, dict):
        result["status"] = "fail"
        result["errors"].append("plot_manifest.json must contain a JSON object")
        return result

    for field in ["generated_at", "total_plots", "plots"]:
        if field not in data:
            result["status"] = "fail"
            result["errors"].append(f"Missing top-level field: {field}")

    plots = data.get("plots", [])
    if not isinstance(plots, list):
        result["status"] = "fail"
        result["errors"].append("'plots' must be an array")
        return result

    seen_ids: set[str] = set()
    for index, plot in enumerate(plots):
        prefix = f"plots[{index}]"
        if not isinstance(plot, dict):
            result["status"] = "fail"
            result["errors"].append(f"{prefix} must be an object")
            continue

        for field in ["plot_id", "files", "description", "section_hint", "caption", "markdown_snippet"]:
            if field not in plot:
                result["status"] = "fail"
                result["errors"].append(f"{prefix}: missing field '{field}'")

        plot_id = plot.get("plot_id")
        if isinstance(plot_id, str):
            if plot_id in seen_ids:
                result["status"] = "fail"
                result["errors"].append(f"Duplicate plot_id: {plot_id}")
            seen_ids.add(plot_id)

        section_hint = plot.get("section_hint")
        if section_hint not in SECTION_HINTS:
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: invalid section_hint '{section_hint}'")

        caption = plot.get("caption")
        if not isinstance(caption, str) or not caption.strip():
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: caption must be a non-empty string")

        files = plot.get("files")
        if not isinstance(files, dict):
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: 'files' must be an object")
            continue

        png_path = files.get("png")
        if not isinstance(png_path, str) or not png_path:
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: missing PNG path")
        else:
            png_file = resolve_local_path(png_path, report_root)
            if png_file is None or not png_file.exists():
                result["status"] = "fail"
                result["errors"].append(f"{prefix}: PNG file not found at '{png_path}'")

        vector_found = False
        for extension in ("pdf", "svg"):
            vector_path = files.get(extension)
            if isinstance(vector_path, str) and vector_path:
                vector_found = True
                vector_file = resolve_local_path(vector_path, report_root)
                if vector_file is None or not vector_file.exists():
                    result["status"] = "fail"
                    result["errors"].append(f"{prefix}: {extension.upper()} file not found at '{vector_path}'")
        if not vector_found:
            result["warnings"].append(f"{prefix}: vector companion (.pdf or .svg) is missing")

        markdown_snippet = plot.get("markdown_snippet")
        if isinstance(markdown_snippet, str) and isinstance(png_path, str) and png_path not in markdown_snippet:
            result["warnings"].append(f"{prefix}: markdown_snippet does not reference the PNG path")

    if isinstance(data.get("total_plots"), int) and data.get("total_plots") != len(plots):
        result["status"] = "fail"
        result["errors"].append("total_plots does not match actual plot count")

    # Style-metadata audit: every entry should record `style`, `dpi`, and a
    # source script so downstream readers can confirm the plot was generated
    # under the documented scienceplots/Okabe-Ito conventions.
    for index, plot in enumerate(plots):
        if not isinstance(plot, dict):
            continue
        prefix = f"plots[{index}]"
        style_value = plot.get("style")
        if style_value is None:
            result["warnings"].append(
                f"{prefix}: no 'style' recorded; expected ['science', 'nature'] (or with 'no-latex')"
            )
        else:
            if not isinstance(style_value, list) or not all(isinstance(s, str) for s in style_value):
                result["warnings"].append(f"{prefix}: 'style' should be a list of strings")
            else:
                style_set = {s.lower() for s in style_value}
                if not ({"science", "nature", "ieee"} & style_set):
                    result["warnings"].append(
                        f"{prefix}: style {style_value!r} is not a scienceplots journal style; "
                        "expected science, nature, or ieee"
                    )
        dpi = plot.get("dpi")
        if dpi is not None and isinstance(dpi, int) and dpi < 300:
            result["warnings"].append(f"{prefix}: dpi={dpi} is below the 300-dpi journal standard")
        if "source_script" not in plot:
            result["warnings"].append(
                f"{prefix}: 'source_script' missing; reproducibility cannot be verified"
            )

    return result


def validate_report_versions(path: Path, data: Any) -> dict[str, Any]:
    result = result_template(path)
    if not isinstance(data, dict):
        result["status"] = "fail"
        result["errors"].append("report_versions.json must contain a JSON object")
        return result

    for field in ["schema_version", "current_version", "versions"]:
        if field not in data:
            result["status"] = "fail"
            result["errors"].append(f"Missing top-level field: {field}")

    versions = data.get("versions", [])
    if not isinstance(versions, list):
        result["status"] = "fail"
        result["errors"].append("'versions' must be an array")
        return result

    expected_version = 1
    for index, version in enumerate(versions):
        prefix = f"versions[{index}]"
        if not isinstance(version, dict):
            result["status"] = "fail"
            result["errors"].append(f"{prefix} must be an object")
            continue

        for field in ["version", "file", "created_at", "feedback_tier", "feedback_summary"]:
            if field not in version:
                result["status"] = "fail"
                result["errors"].append(f"{prefix}: missing field '{field}'")

        if version.get("version") != expected_version:
            result["status"] = "fail"
            result["errors"].append(
                f"{prefix}: expected version {expected_version}, got {version.get('version')}"
            )
        expected_version += 1

        tier = version.get("feedback_tier")
        if tier is not None and tier not in {1, 2, 3}:
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: feedback_tier must be null, 1, 2, or 3")

        changes = version.get("changes", [])
        if changes is not None and not isinstance(changes, list):
            result["status"] = "fail"
            result["errors"].append(f"{prefix}: changes must be an array when present")
        elif isinstance(changes, list):
            for change_index, change in enumerate(changes):
                if not isinstance(change, dict):
                    result["status"] = "fail"
                    result["errors"].append(f"{prefix}.changes[{change_index}] must be an object")
                    continue
                if change.get("type") not in CHANGE_TYPES:
                    result["status"] = "fail"
                    result["errors"].append(
                        f"{prefix}.changes[{change_index}]: invalid change type '{change.get('type')}'"
                    )
                if not change.get("reason"):
                    result["status"] = "fail"
                    result["errors"].append(f"{prefix}.changes[{change_index}]: missing reason")

    current_version = data.get("current_version")
    if isinstance(current_version, int) and versions and current_version != versions[-1].get("version"):
        result["status"] = "fail"
        result["errors"].append("current_version must match the latest version entry")

    return result


def section_matches(section_name: str, patterns: tuple[str, ...]) -> bool:
    normalized = section_name.casefold()
    return any(pattern in normalized for pattern in patterns)


def has_nearby_interpretation(lines: list[str], start_line: int) -> bool:
    for index in range(start_line, min(len(lines), start_line + 6)):
        candidate = lines[index].strip()
        if not candidate:
            continue
        if candidate.startswith("#") or candidate.startswith("!["):
            break
        if candidate.startswith("<!--"):
            continue
        if WORD_PATTERN.search(candidate):
            return True
    return False


def has_nearby_quantitative_observation(lines: list[str], start_line: int, window: int = 6) -> bool:
    """Return True if a numeric token appears within `window` lines of `start_line`.

    Used to flag passive figure references that are not paired with a concrete
    numeric observation in the same neighborhood. Section headings and image
    blocks terminate the search.
    """
    for index in range(start_line, min(len(lines), start_line + window)):
        candidate = lines[index].strip()
        if not candidate:
            continue
        if candidate.startswith("#") or candidate.startswith("!["):
            break
        if QUANTITATIVE_HINT_PATTERN.search(candidate):
            return True
    return False


DISPLAY_MATH_BLOCK_PATTERN = re.compile(r"\$\$.*?\$\$", re.DOTALL)
INLINE_MATH_PATTERN = re.compile(r"(?<!\$)\$(?!\$)([^\$\n]+?)(?<!\$)\$(?!\$)")


def _blank_match(match: "re.Match[str]") -> str:
    """Replace a regex match with whitespace of identical character length.

    Newlines inside the match are preserved so that line-number bookkeeping
    still works on the masked text.
    """
    span = match.group(0)
    return "".join(c if c == "\n" else " " for c in span)


def mask_code_and_comments(text: str) -> str:
    """Mask fenced code, inline code, and HTML comments with same-length whitespace.

    Used by validators that should not flag examples-of-bad-syntax living
    inside code blocks or HTML comments. Newlines are preserved so line
    numbers stay accurate after masking.
    """
    masked = CODE_FENCE_PATTERN.sub(_blank_match, text)
    masked = INLINE_CODE_PATTERN.sub(_blank_match, masked)
    masked = HTML_COMMENT_PATTERN.sub(_blank_match, masked)
    return masked


def mask_math(text: str) -> str:
    """Additionally mask LaTeX math regions ($$..$$ and $..$).

    Use this on top of `mask_code_and_comments` when scanning for
    template-placeholder patterns or other braces-sensitive checks, so that
    legitimate LaTeX braces such as `\\frac{1}{N}` or `\\hat{y}_i` are not
    misclassified as unresolved template placeholders.
    """
    masked = DISPLAY_MATH_BLOCK_PATTERN.sub(_blank_match, text)
    masked = INLINE_MATH_PATTERN.sub(_blank_match, masked)
    return masked


def split_sections(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """Group lines into (start_index, heading_text, body_lines) tuples.

    Lines preceding the first heading are assigned to a synthetic preamble
    section labelled `__preamble__` so word-budget warnings ignore them.
    """
    sections: list[tuple[int, str, list[str]]] = []
    current_heading = "__preamble__"
    current_start = 0
    current_body: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        match = HEADING_PATTERN.match(line.strip())
        if match:
            sections.append((current_start, current_heading, current_body))
            current_heading = match.group(2).strip()
            current_start = line_number
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_start, current_heading, current_body))
    return sections


def validate_report_markdown(path: Path) -> dict[str, Any]:
    result = result_template(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result["status"] = "fail"
        result["errors"].append("File not found")
        return result

    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        result["status"] = "fail"
        result["errors"].append("report.md is empty")
        return result

    if not non_empty_lines[0].startswith("# "):
        result["status"] = "fail"
        result["errors"].append("report.md should begin with a level-1 title")

    text_no_code = mask_code_and_comments(text)
    text_no_code_or_math = mask_math(text_no_code)
    placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(text_no_code_or_math)))
    if placeholders:
        result["status"] = "fail"
        preview = ", ".join(placeholders[:8])
        suffix = " ..." if len(placeholders) > 8 else ""
        result["errors"].append(f"Unresolved template placeholders remain: {preview}{suffix}")

    headings = []
    for line_number, line in enumerate(lines, start=1):
        match = HEADING_PATTERN.match(line.strip())
        if match:
            headings.append((line_number, len(match.group(1)), match.group(2).strip()))

    if not headings:
        result["status"] = "fail"
        result["errors"].append("No markdown headings found")
        return result

    heading_names = [heading for _, _, heading in headings]
    for group_name, patterns in REQUIRED_SECTION_GROUPS.items():
        if not any(section_matches(heading, patterns) for heading in heading_names):
            result["status"] = "fail"
            result["errors"].append(f"Missing required report section group: {group_name}")

    for group_name, patterns in RECOMMENDED_SECTION_GROUPS.items():
        if not any(section_matches(heading, patterns) for heading in heading_names):
            result["warnings"].append(f"Recommended section group is missing: {group_name}")

    word_count = len(WORD_PATTERN.findall(text))
    if word_count < 250:
        result["warnings"].append("Report is short (<250 words); confirm the narrative is complete")

    # ── Math conventions ────────────────────────────────────────────────────
    # Single-line $$..$$ should still be detected — scan the code-masked text
    # but BEFORE math masking, since math masking would otherwise blank it.
    single_line_display = list(SINGLE_LINE_DISPLAY_MATH_PATTERN.finditer(text_no_code))
    for match in single_line_display:
        line_number = text_no_code.count("\n", 0, match.start()) + 1
        snippet = match.group(0)
        if len(snippet) > 80:
            snippet = snippet[:77] + "..."
        result["status"] = "fail"
        result["errors"].append(
            f"Single-line display math at line {line_number} (`{snippet}`) — "
            "put `$$` on its own line with the equation between"
        )

    # Unicode math should be flagged in prose only — math regions are allowed
    # to look like `$\alpha$` (which is correct LaTeX). So scan the
    # code-AND-math-masked text.
    unicode_hits: dict[str, list[int]] = {}
    for line_index, masked_line in enumerate(text_no_code_or_math.splitlines(), start=1):
        for char in masked_line:
            if char in UNICODE_MATH_CHARS:
                unicode_hits.setdefault(char, []).append(line_index)
    if unicode_hits:
        examples = []
        for char, line_numbers in list(unicode_hits.items())[:5]:
            replacement = UNICODE_MATH_CHARS[char]
            first_lines = ", ".join(str(n) for n in line_numbers[:3])
            examples.append(f"`{char}`→{replacement} (line(s) {first_lines})")
        suffix = " ..." if len(unicode_hits) > 5 else ""
        result["status"] = "fail"
        result["errors"].append(
            "Unicode math symbols in report body; use LaTeX equivalents: "
            + "; ".join(examples)
            + suffix
        )

    # ── Anti-pattern: figure-only appendix table ───────────────────────────
    for match in FIGURE_TABLE_HEADING_PATTERN.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        result["warnings"].append(
            f"Anti-pattern at line {line_number}: a 'list of figures' / 'figure inventory' heading is "
            "discouraged. Embed each figure inline next to the paragraph that interprets it."
        )

    # ── Image references ───────────────────────────────────────────────────
    image_targets: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        for match in IMAGE_PATTERN.finditer(line):
            alt = match.group("alt").strip()
            target = match.group("target").strip()
            image_targets.append(target)
            if not alt:
                result["warnings"].append(f"Image at line {line_number} has empty alt text")
            if target.startswith(("http://", "https://")):
                result["warnings"].append(f"Image at line {line_number} uses a remote URL: {target}")
                continue
            if Path(target).is_absolute():
                result["warnings"].append(f"Image at line {line_number} uses an absolute path: {target}")
            resolved = resolve_local_path(target, path.parent)
            if resolved is None or not resolved.exists():
                result["status"] = "fail"
                result["errors"].append(f"Image at line {line_number} points to a missing file: {target}")
            if not has_nearby_interpretation(lines, line_number):
                result["warnings"].append(
                    f"Image at line {line_number} is not followed by nearby interpretation text"
                )
            if not has_nearby_quantitative_observation(lines, line_number):
                result["warnings"].append(
                    f"Image at line {line_number} lacks a nearby quantitative observation; "
                    "embed concrete numbers (deltas, percentages, R^2, runtimes) next to the figure"
                )

    if not image_targets:
        result["warnings"].append("No inline plot/image references found in report.md")

    if image_targets and not EVIDENCE_BLOCK_PATTERN.search(text):
        result["warnings"].append("No EVIDENCE BLOCK comments found; optional but helpful for dense reports")

    # ── Passive figure references without nearby numbers ───────────────────
    for line_number, line in enumerate(lines, start=1):
        if PASSIVE_FIGURE_PATTERN.search(line) and not has_nearby_quantitative_observation(lines, line_number):
            result["warnings"].append(
                f"Line {line_number}: passive figure reference (`{line.strip()[:80]}`) without a nearby "
                "quantitative observation; replace with a sentence that quotes specific numbers from the figure"
            )

    # ── Word-budget hints (`<!-- WORD_BUDGET: 600 -->` after a heading) ────
    for start_line, heading, body in split_sections(lines):
        if heading == "__preamble__":
            continue
        budget: int | None = None
        for body_line in body[:5]:
            match = WORD_BUDGET_PATTERN.search(body_line)
            if match:
                budget = int(match.group(1))
                break
        if budget is None:
            continue
        word_count = sum(len(WORD_PATTERN.findall(line)) for line in body)
        if word_count > int(budget * 1.1):
            result["warnings"].append(
                f"Section '{heading}' (line {start_line}) exceeds word budget by >10%: "
                f"{word_count}/{budget} words"
            )

    # ── Evidence-block IDs: each declared `ev-X` should appear at most once ─
    evidence_ids = EVIDENCE_BLOCK_ID_PATTERN.findall(text)
    duplicates = {ev for ev in evidence_ids if evidence_ids.count(ev) > 1}
    if duplicates:
        result["warnings"].append(
            f"Duplicate EVIDENCE BLOCK ids: {', '.join(sorted(duplicates))}"
        )

    manifest_path = path.parent / "plots" / "plot_manifest.json"
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
        except json.JSONDecodeError as exc:
            result["status"] = "fail"
            result["errors"].append(f"plot_manifest.json is invalid JSON: {exc}")
        else:
            manifest_png_paths: set[str] = set()
            manifest_all_paths: set[str] = set()
            for plot in manifest.get("plots", []) if isinstance(manifest, dict) else []:
                if not isinstance(plot, dict):
                    continue
                files = plot.get("files", {})
                if not isinstance(files, dict):
                    continue
                for extension, value in files.items():
                    if isinstance(value, str) and value:
                        manifest_all_paths.add(value)
                        if extension == "png":
                            manifest_png_paths.add(value)

            referenced_local = {
                target for target in image_targets if not target.startswith(("http://", "https://"))
            }
            orphaned = sorted(manifest_png_paths - referenced_local)
            if orphaned:
                preview = ", ".join(orphaned[:5])
                suffix = " ..." if len(orphaned) > 5 else ""
                result["warnings"].append(
                    f"Manifest plots not referenced in report.md: {preview}{suffix}"
                )

            undocumented = sorted(
                target
                for target in referenced_local
                if target.startswith("plots/") and target not in manifest_all_paths
            )
            if undocumented:
                preview = ", ".join(undocumented[:5])
                suffix = " ..." if len(undocumented) > 5 else ""
                result["warnings"].append(
                    f"Report references plot files missing from plot_manifest.json: {preview}{suffix}"
                )
    else:
        result["warnings"].append("plots/plot_manifest.json not found; cross-reference checks were skipped")

    return result


def validate_file(path: Path) -> dict[str, Any]:
    if path.name == "report.md":
        return validate_report_markdown(path)

    try:
        data = load_json(path)
    except FileNotFoundError:
        result = result_template(path)
        result["status"] = "fail"
        result["errors"].append("File not found")
        return result
    except json.JSONDecodeError as exc:
        result = result_template(path)
        result["status"] = "fail"
        result["errors"].append(f"Invalid JSON: {exc}")
        return result

    if path.name == "plot_manifest.json":
        return validate_plot_manifest(path, data)
    if path.name == "report_versions.json":
        return validate_report_versions(path, data)

    result = result_template(path)
    result["status"] = "fail"
    result["errors"].append(f"Unsupported artifact: {path.name}")
    return result


def discover_paths(input_paths: list[str]) -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()
    for raw in input_paths:
        path = Path(raw).resolve()
        if path.is_dir():
            direct_candidates = [path / "report.md", path / "report_versions.json", path / "plots" / "plot_manifest.json"]
            for candidate in direct_candidates:
                if candidate.exists() and candidate.name in RECOGNIZED_FILES and candidate not in seen:
                    discovered.append(candidate)
                    seen.add(candidate)
            for candidate in sorted(path.rglob("*.json")):
                if candidate.name in RECOGNIZED_FILES and candidate not in seen:
                    discovered.append(candidate)
                    seen.add(candidate)
        elif path not in seen:
            discovered.append(path)
            seen.add(path)
    return discovered


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate report artifact JSON files and report.md bodies")
    parser.add_argument("paths", nargs="+", help="Artifact files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args()

    results = [validate_file(path) for path in discover_paths(args.paths)]
    failed = sum(1 for item in results if item["status"] == "fail")
    payload = {
        "status": "fail" if failed else "pass",
        "total": len(results),
        "failed": failed,
        "results": results,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for item in results:
        print(f"{item['status'].upper():4}  {item['artifact']}")
        for error in item["errors"]:
            print(f"  - ERROR: {error}")
        for warning in item["warnings"]:
            print(f"  - WARN: {warning}")
    print(f"\nSummary: {payload['status'].upper()} ({payload['total']} artifacts, {payload['failed']} failed)")


if __name__ == "__main__":
    main()
