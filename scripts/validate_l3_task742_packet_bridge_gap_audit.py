from __future__ import annotations

import csv
import sys
from pathlib import Path


AUDIT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_task742_packet_bridge_gap_audit.csv")


def validate() -> list[str]:
    errors: list[str] = []
    if not AUDIT_PATH.exists():
        return [f"missing audit: {AUDIT_PATH}"]
    rows = _read_csv(AUDIT_PATH)
    if not rows:
        errors.append("Task742 packet bridge audit is empty")
        return errors
    for row in rows:
        allowed = int(row.get("allowed_for_task742_calibration_flag") or 0)
        has_packet = int(row.get("has_packet_key_flag") or 0)
        has_outcome_key = int(row.get("has_outcome_key_flag") or 0)
        has_outcome_value = int(row.get("has_outcome_value_flag") or 0)
        if allowed and not (has_packet and has_outcome_key and has_outcome_value):
            errors.append(f"allowed row lacks explicit packet/outcome fields: {row.get('candidate_path')}")
        if not allowed and int(row.get("inferred_matching_required_flag") or 0) != 1:
            errors.append(f"blocked row must mark inferred matching required: {row.get('candidate_path')}")
    return errors


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_TASK742_BRIDGE_GAP_ERROR] {error}")
        sys.exit(1)
    rows = _read_csv(AUDIT_PATH)
    allowed = sum(int(row.get("allowed_for_task742_calibration_flag") or 0) for row in rows)
    print(f"[L3_TASK742_BRIDGE_GAP_OK] candidates={len(rows)} allowed={allowed}")


if __name__ == "__main__":
    main()
