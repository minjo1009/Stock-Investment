from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


DEFAULT_DIR = Path("data/artifacts/task_4176_l4_diagnostic_blocker_taxonomy_scanner_v1")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    failures: list[str] = []
    taxonomy = args.artifact_dir / "task_4176_l4_relation_taxonomy_v1.csv"
    scanner = args.artifact_dir / "task_4176_l4_contradiction_scanner_v1.csv"
    summary_path = args.artifact_dir / "task_4176_l4_scanner_summary.json"
    for path in [taxonomy, scanner, summary_path]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if failures:
        print("\n".join(f"FAIL {item}" for item in failures))
        return 1
    taxonomy_rows = list(csv.DictReader(taxonomy.open(encoding="utf-8")))
    scanner_rows = list(csv.DictReader(scanner.open(encoding="utf-8")))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not taxonomy_rows:
        failures.append("empty taxonomy")
    if not scanner_rows:
        failures.append("empty scanner")
    if not any(row.get("diagnostic_taxonomy_status") == "SUPPORTED_V1" for row in taxonomy_rows):
        failures.append("no supported relation families")
    if not any(str(row.get("contradiction_scan_status", "")).startswith("SCANNED_") for row in scanner_rows):
        failures.append("no scanned rows")
    if any(str(row.get("no_contradiction_claimed")) not in {"0", "False", "false", ""} for row in scanner_rows):
        failures.append("scanner claims no contradiction")
    if any(str(row.get("negative_evidence_allowed")) not in {"0", "False", "false", ""} for row in scanner_rows + taxonomy_rows):
        failures.append("negative evidence allowed")
    if int(summary.get("scanned_supported_family_rows", 0) or 0) <= 0:
        failures.append("summary scanned_supported_family_rows is zero")
    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print(f"PASS taxonomy_families={len(taxonomy_rows)}")
    print(f"PASS scanner_rows={len(scanner_rows)}")
    print(f"PASS scanned_supported_family_rows={summary.get('scanned_supported_family_rows')}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
