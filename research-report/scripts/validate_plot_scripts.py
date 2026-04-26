#!/usr/bin/env python3
"""Static auditor for plot generation scripts.

Walks `plots/` (and optionally other source directories) and statically checks
every Python file that produces matplotlib output for compliance with the
local plot-style conventions defined in `_plot_style.py`.

Detected violations (matched against the 23-pitfall table in SKILL.md):

ERRORS
- imports `matplotlib` / calls `plt.savefig` but does not import `_plot_style`
  or `scienceplots` (silent fallback to default matplotlib).
- `plt.style.use(['science', ...])` is called WITHOUT `'no-latex'` while
  `text.usetex` is also set to `False` later in the file (pitfall #21).
- `plt.savefig(...)` is called only with a `.png` path (no PDF/SVG companion).
- `plt.show()` appears (blocks pipelines).
- `transparent=True` is passed to `plt.savefig`.
- Hardcoded `dpi` argument below 300.
- Calls `apply_style()` but follows it with explicit `font.family`,
  `font.size`, or `text.usetex` overrides via `rcParams.update` /
  `rcParams[...] = ...` (re-introduces silent fallback).

WARNINGS
- Uses `figsize=(...)` with a width that is not one of the standard
  Nature column widths (3.5, 5.0, 7.0, 7.2 inches).
- Sets a string label / title via `ax.set_xlabel`, `set_ylabel`,
  `set_title`, or `legend(label=...)` without a corresponding
  `assert_english(...)` call somewhere in the file.
- Hardcodes `font.family` / `font.size`.
- Saves only PNG (no PDF), but does not call `save_figure()` (which would
  emit both formats).

Usage:
  python validate_plot_scripts.py {output_dir} [--strict] [--json]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

NATURE_WIDTHS = {3.5, 5.0, 7.0, 7.2}
LABEL_METHODS = {"set_xlabel", "set_ylabel", "set_title", "suptitle"}
RCPARAM_FORBIDDEN_KEYS = {"font.family", "font.size", "text.usetex"}


def relpath(p: Path, root: Path) -> str:
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(p.resolve())


def is_plot_script(text: str) -> bool:
    """Return True if a file likely produces a matplotlib figure."""
    if "matplotlib" not in text:
        return False
    return any(token in text for token in ("savefig", "save_figure", "plt.show", "FigureCanvas"))


def get_attr_path(node: ast.AST) -> str | None:
    """Return a dotted path for `Attribute(Attribute(... Name))` chains."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def style_use_arg_strings(call: ast.Call) -> list[str] | None:
    """Extract the list of style names passed to plt.style.use(...)."""
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, (ast.List, ast.Tuple)):
        out: list[str] = []
        for element in arg.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                out.append(element.value)
        return out
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return [arg.value]
    return None


def keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def is_constant(node: ast.AST | None, value: Any) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def collect_savefig_calls(tree: ast.Module) -> list[tuple[ast.Call, str | None]]:
    """Return (call_node, first_positional_string_arg) for plt.savefig / fig.savefig."""
    out: list[tuple[ast.Call, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        path = get_attr_path(node.func)
        if not path:
            continue
        if path.endswith(".savefig"):
            first_arg: str | None = None
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                first_arg = node.args[0].value
            out.append((node, first_arg))
    return out


def audit_script(path: Path, output_root: Path) -> dict[str, Any]:
    rel = relpath(path, output_root)
    result: dict[str, Any] = {"file": rel, "status": "pass", "errors": [], "warnings": []}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["status"] = "fail"
        result["errors"].append(f"Cannot read file: {exc}")
        return result

    if not is_plot_script(text):
        result["status"] = "skip"
        return result

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        result["status"] = "fail"
        result["errors"].append(f"Syntax error: {exc}")
        return result

    imports_scienceplots = "scienceplots" in text
    imports_plot_style = bool(re.search(r"\bfrom\s+_plot_style\s+import\b", text)) or bool(
        re.search(r"\bimport\s+_plot_style\b", text)
    )

    if not (imports_scienceplots or imports_plot_style):
        result["status"] = "fail"
        result["errors"].append(
            "imports matplotlib/savefig but does not import `_plot_style` or `scienceplots`; "
            "figures will silently fall back to default matplotlib"
        )

    style_chains: list[list[str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            path_str = get_attr_path(node.func)
            if path_str and path_str.endswith("style.use"):
                args = style_use_arg_strings(node)
                if args is not None:
                    style_chains.append(args)

    text_usetex_set_false = bool(
        re.search(r"text\.usetex[^\n]{0,30}False\b", text)
    )
    has_apply_style = bool(re.search(r"\bapply_style\s*\(", text))

    if style_chains:
        worst = max(style_chains, key=len)
        is_journal_chain = any(s.lower() in {"science", "nature", "ieee"} for s in worst)
        chain_has_no_latex = "no-latex" in worst
        if is_journal_chain and not chain_has_no_latex and text_usetex_set_false:
            result["status"] = "fail"
            result["errors"].append(
                "plt.style.use(['science'/'nature'/'ieee'...]) is called WITHOUT 'no-latex' "
                "while text.usetex is also set to False — pitfall #21 (silent DejaVu fallback). "
                "Either route through `apply_style(use_latex=False)` or add 'no-latex' to the chain."
            )
        if is_journal_chain and not has_apply_style:
            result["warnings"].append(
                "Hand-rolled plt.style.use(['science', ...]) without going through `apply_style()`; "
                "the helper auto-probes for LaTeX and inserts 'no-latex' on systems without TeX, "
                "preventing pitfall #21"
            )

    rcparam_overrides_present = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            path_str = get_attr_path(node.func)
            if path_str and (path_str.endswith("rcParams.update") or path_str == "rcParams.update"):
                if node.args and isinstance(node.args[0], ast.Dict):
                    keys = [k.value for k in node.args[0].keys if isinstance(k, ast.Constant)]
                    bad = [k for k in keys if k in RCPARAM_FORBIDDEN_KEYS]
                    if bad and has_apply_style:
                        result["status"] = "fail"
                        result["errors"].append(
                            f"rcParams.update overrides {bad} after apply_style() — "
                            "this re-introduces pitfall #21/#23"
                        )
                    rcparam_overrides_present = rcparam_overrides_present or bool(bad)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
            attr_path = get_attr_path(node.value)
            if attr_path and attr_path.endswith("rcParams"):
                if isinstance(node.slice, ast.Constant) and node.slice.value in RCPARAM_FORBIDDEN_KEYS:
                    if has_apply_style:
                        result["status"] = "fail"
                        result["errors"].append(
                            f"rcParams['{node.slice.value}'] = ... after apply_style() — "
                            "drop the override and let `apply_style()` decide LaTeX/font config"
                        )
                    rcparam_overrides_present = True

    savefig_calls = collect_savefig_calls(tree)
    saw_show = bool(re.search(r"\bplt\.show\s*\(", text))
    if saw_show:
        result["status"] = "fail"
        result["errors"].append("plt.show() blocks automation pipelines; remove or guard with __main__")

    png_paths = 0
    pdf_paths = 0
    svg_paths = 0
    for call, first_arg in savefig_calls:
        if first_arg is not None:
            lowered = first_arg.lower()
            if lowered.endswith(".png"):
                png_paths += 1
            elif lowered.endswith(".pdf"):
                pdf_paths += 1
            elif lowered.endswith(".svg"):
                svg_paths += 1
        transparent = keyword_value(call, "transparent")
        if is_constant(transparent, True):
            result["status"] = "fail"
            result["errors"].append(
                "savefig(transparent=True) drops the white background — keep the default for journal figures"
            )
        dpi = keyword_value(call, "dpi")
        if isinstance(dpi, ast.Constant) and isinstance(dpi.value, (int, float)) and dpi.value < 300:
            result["status"] = "fail"
            result["errors"].append(f"savefig(dpi={dpi.value}) is below the 300-dpi journal standard")

    uses_save_figure = bool(re.search(r"\bsave_figure\s*\(", text))
    if savefig_calls and not uses_save_figure:
        if pdf_paths == 0 and svg_paths == 0:
            result["status"] = "fail"
            result["errors"].append(
                "savefig() only emits PNG; emit a PDF (or SVG) companion or call save_figure() instead"
            )

    figsize_widths_seen: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            figsize = keyword_value(node, "figsize")
            if isinstance(figsize, (ast.Tuple, ast.List)) and figsize.elts:
                first = figsize.elts[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, (int, float)):
                    figsize_widths_seen.append(float(first.value))
    for width in figsize_widths_seen:
        if not any(abs(width - target) < 0.05 for target in NATURE_WIDTHS):
            result["warnings"].append(
                f"figsize width={width} in is non-standard; prefer FIGSIZE_SINGLE (3.5), "
                "FIGSIZE_ONE_HALF (5.0), FIGSIZE_DOUBLE (7.0), or FIGSIZE_PANEL_WIDE (7.2) from _plot_style"
            )

    has_assert_english = "assert_english" in text
    has_label_call = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            path_str = get_attr_path(node.func)
            if path_str and any(path_str.endswith("." + name) for name in LABEL_METHODS):
                has_label_call = True
                break
    if has_label_call and not has_assert_english:
        result["warnings"].append(
            "set_xlabel/ylabel/title/suptitle is called without `assert_english(...)`; "
            "non-ASCII characters will silently render as missing-glyph boxes"
        )

    if savefig_calls and "_plot_style" not in text and "scienceplots" not in text:
        # Already failed above; no extra check.
        pass

    if result["errors"]:
        result["status"] = "fail"

    return result


def discover_scripts(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for sub in ("plots", "src", "scripts", "notebooks"):
        sub_path = root / sub
        if sub_path.is_dir():
            candidates.extend(sub_path.rglob("*.py"))
    candidates.extend(root.glob("*.py"))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit plot generation scripts for style compliance")
    parser.add_argument("output_dir", help="Report root containing plots/ and src/")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args()

    root = Path(args.output_dir).resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    scripts = discover_scripts(root)
    results = [audit_script(path, root) for path in scripts]
    audited = [r for r in results if r["status"] != "skip"]
    failed = [r for r in audited if r["status"] == "fail"]
    if args.strict:
        failed.extend(r for r in audited if r["status"] == "pass" and r["warnings"])

    payload = {
        "status": "fail" if failed else "pass",
        "total_python_files": len(results),
        "audited": len(audited),
        "failed": len(failed),
        "results": audited,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for item in audited:
            marker = "FAIL" if item["status"] == "fail" else "PASS"
            print(f"{marker}  {item['file']}")
            for error in item["errors"]:
                print(f"  - ERROR: {error}")
            for warning in item["warnings"]:
                print(f"  - WARN: {warning}")
        print(
            f"\nSummary: {payload['status'].upper()} "
            f"({payload['audited']}/{payload['total_python_files']} audited, {payload['failed']} failed)"
        )

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
