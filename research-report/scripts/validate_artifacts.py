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

    placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(text)))
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

    if not image_targets:
        result["warnings"].append("No inline plot/image references found in report.md")

    if image_targets and not EVIDENCE_BLOCK_PATTERN.search(text):
        result["warnings"].append("No EVIDENCE BLOCK comments found; optional but helpful for dense reports")

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
