#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_changes(change_values: list[str]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for raw in change_values:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise SystemExit("Each --change value must be a JSON object")
        if "type" not in parsed or "reason" not in parsed:
            raise SystemExit("Each change object requires at least 'type' and 'reason'")
        changes.append(parsed)
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a new entry to report_versions.json")
    parser.add_argument("report_root", help="Directory containing report.md")
    parser.add_argument("--summary", required=True, help="Short description of what changed")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], default=None, help="Feedback tier for this update")
    parser.add_argument(
        "--change",
        action="append",
        default=[],
        help="Structured change object as JSON. Repeatable.",
    )
    args = parser.parse_args()

    report_root = Path(args.report_root).resolve()
    report_path = report_root / "report.md"
    manifest_path = report_root / "report_versions.json"

    if not report_path.exists():
        raise SystemExit(f"report.md not found in {report_root}")

    changes = load_changes(args.change)
    now = datetime.now(timezone.utc).isoformat()

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise SystemExit("report_versions.json must contain a JSON object")
    else:
        manifest = {
            "schema_version": "1.1.0",
            "current_version": 0,
            "versions": [],
        }

    current_version = int(manifest.get("current_version", 0))
    versions = manifest.setdefault("versions", [])
    if not isinstance(versions, list):
        raise SystemExit("report_versions.json: 'versions' must be an array")

    if current_version >= 1 and versions:
        archive_path = report_root / f"report_v{current_version}.md"
        latest = versions[-1]
        if isinstance(latest, dict) and latest.get("file") == "report.md" and archive_path.exists():
            latest["file"] = archive_path.name

    new_version = current_version + 1
    versions.append(
        {
            "version": new_version,
            "file": "report.md",
            "created_at": now,
            "feedback_tier": args.tier,
            "feedback_summary": args.summary,
            "changes": changes,
        }
    )

    manifest["schema_version"] = "1.1.0"
    manifest["current_version"] = new_version
    manifest["versions"] = versions
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Recorded report version {new_version} in {manifest_path}")


if __name__ == "__main__":
    main()
