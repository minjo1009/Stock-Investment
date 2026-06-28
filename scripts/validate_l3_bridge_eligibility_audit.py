from __future__ import annotations

import csv
import sys
from pathlib import Path


AUDIT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_calibration_bridge_gap_audit.csv")


def validate(path: Path = AUDIT_PATH) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing bridge audit: {path}"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        errors.append("bridge audit has no rows")
    for row in rows:
        allowed = int(row.get("allowed_for_calibration_flag", 0))
        inferred = int(row.get("inferred_matching_required_flag", 0))
        if allowed and inferred:
            errors.append(f"{row.get('candidate_path')}: allowed row still requires inferred matching")
        if allowed and not row.get("available_bridge_columns", "").strip():
            errors.append(f"{row.get('candidate_path')}: allowed row lacks bridge columns")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_BRIDGE_AUDIT_ERROR] {error}")
        sys.exit(1)
    print("[L3_BRIDGE_AUDIT_OK]")


if __name__ == "__main__":
    main()
