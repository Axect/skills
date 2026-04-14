#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".png", ".pdf", ".svg"}
SECTION_HINTS = ["results", "methodology", "validation", "comparison", "testing"]


def sanitize_plot_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized:
        normalized = "plot"
    if not normalized[0].isalpha():
        normalized = f"plot_{normalized}"
    return normalized


def infer_section_hint(name: str) -> str:
    lowered = name.lower()
    keyword_map = {
        "method": "methodology",
        "pipeline": "methodology",
        "ablation": "comparison",
        "compare": "comparison",
        "comparison": "comparison",
        "benchmark": "comparison",
        "test": "testing",
        "validation": "validation",
        "error": "validation",
        "result": "results",
        "metric": "results",
        "summary": "results",
    }
    for keyword, hint in keyword_map.items():
        if keyword in lowered:
            return hint
    return "results"


def load_metadata(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "plots" in raw and isinstance(raw["plots"], list):
        items = raw["plots"]
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("plot_id") or item.get("stem") or item.get("name") or "").strip()
            if key:
                result[key] = item
        return result
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    raise ValueError("Metadata file must be an object or an object with a 'plots' array")


def relpath(path: Path, base: Path) -> Path:
    return path.resolve().relative_to(base.resolve())


def safe_relpath(path: Path, base: Path) -> str:
    try:
        return relpath(path, base).as_posix()
    except Exception:
        return path.resolve().as_posix()


def build_manifest(plots_dir: Path, report_root: Path, metadata_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Path]] = defaultdict(dict)
    for child in sorted(plots_dir.iterdir()):
        if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
            grouped[child.stem][child.suffix.lower().lstrip(".")] = child

    plots: list[dict[str, Any]] = []
    for stem in sorted(grouped):
        files = grouped[stem]
        if "png" not in files:
            continue

        plot_id = sanitize_plot_id(stem)
        meta = metadata_map.get(stem) or metadata_map.get(plot_id) or {}
        timestamp = max(path.stat().st_mtime for path in files.values())
        generation_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

        file_payload = {ext: safe_relpath(path, report_root) for ext, path in sorted(files.items())}
        section_hint = str(meta.get("section_hint") or infer_section_hint(stem))
        if section_hint not in SECTION_HINTS:
            section_hint = "results"

        png_path = file_payload["png"]
        description = str(meta.get("description") or stem.replace("_", " ").strip().capitalize())
        caption = str(meta.get("caption") or description)

        entry: dict[str, Any] = {
            "plot_id": plot_id,
            "files": file_payload,
            "description": description,
            "section_hint": section_hint,
            "caption": caption,
            "markdown_snippet": f"![{caption}]({png_path})",
            "generation_date": str(meta.get("generation_date") or generation_date),
        }

        optional_fields = [
            "source_context",
            "source_script",
            "source_function",
            "style",
            "dpi",
        ]
        for field in optional_fields:
            if field in meta and meta[field] is not None:
                entry[field] = meta[field]

        plots.append(entry)

    return {
        "schema_version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_plots": len(plots),
        "plots": plots,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build plot_manifest.json from an existing plots directory")
    parser.add_argument("plots_dir", help="Directory containing plot image files")
    parser.add_argument("--report-root", help="Base directory used for relative plot paths", default=None)
    parser.add_argument("--output", help="Path to the manifest file", default=None)
    parser.add_argument("--metadata", help="Optional JSON file with plot metadata overrides", default=None)
    args = parser.parse_args()

    plots_dir = Path(args.plots_dir).resolve()
    if not plots_dir.is_dir():
        raise SystemExit(f"Plots directory not found: {plots_dir}")

    report_root = Path(args.report_root).resolve() if args.report_root else plots_dir.parent.resolve()
    output_path = Path(args.output).resolve() if args.output else plots_dir / "plot_manifest.json"
    metadata_path = Path(args.metadata).resolve() if args.metadata else None
    metadata_map = load_metadata(metadata_path)

    manifest = build_manifest(plots_dir, report_root, metadata_map)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output_path} with {manifest['total_plots']} plot entries")


if __name__ == "__main__":
    main()
