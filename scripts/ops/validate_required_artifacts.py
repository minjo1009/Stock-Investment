from __future__ import annotations

import argparse
import csv
import sys

from ops_common import ROOT, artifact_manifest_path, get_task, print_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        task = get_task(args.task)
    except Exception as exc:
        return print_result("REQUIRED ARTIFACTS VALIDATION", [], [], [str(exc)])

    required = task.get("required_artifacts", [])
    for path in required:
        if not (ROOT / path).exists():
            failures.append(f"required artifact missing: {path}")
    if not failures:
        passes.append(f"required_artifacts_exist: {len(required)}")

    manifest = artifact_manifest_path(task)
    if not manifest or not manifest.exists():
        failures.append("artifact_manifest.csv missing")
        return print_result("REQUIRED ARTIFACTS VALIDATION", passes, warnings, failures)

    with manifest.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    fields = rows[0].keys() if rows else []
    expected_fields = {"path", "type", "purpose", "created_or_modified", "task_id"}
    if not expected_fields.issubset(set(fields)):
        failures.append("artifact_manifest.csv missing required columns")
    manifest_paths = {row.get("path") for row in rows}
    for path in required:
        if path not in manifest_paths:
            failures.append(f"required artifact not listed in manifest: {path}")
    validation_path = next((p for p in required if p.endswith("validation_results.md")), None)
    report_path = next((p for p in required if p.endswith("report.md")), None)
    if not validation_path or not (ROOT / validation_path).exists():
        failures.append("validation_results.md missing")
    if not report_path or not (ROOT / report_path).exists():
        failures.append("report.md missing")
    passes.append(f"manifest_rows: {len(rows)}")
    return print_result("REQUIRED ARTIFACTS VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
