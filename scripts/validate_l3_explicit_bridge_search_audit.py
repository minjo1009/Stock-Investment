from __future__ import annotations

import csv
import sys
from pathlib import Path


AUDIT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_explicit_bridge_search_audit.csv")
BRIDGE_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_explicit_source_event_outcome_bridge.csv")


def validate() -> list[str]:
    errors: list[str] = []
    if not AUDIT_PATH.exists():
        errors.append(f"missing audit: {AUDIT_PATH}")
    if not BRIDGE_PATH.exists():
        errors.append(f"missing bridge artifact: {BRIDGE_PATH}")
    if errors:
        return errors

    audit_rows = _read_csv(AUDIT_PATH)
    bridge_rows = _read_csv(BRIDGE_PATH)
    bridge_ids: set[str] = set()
    for row in audit_rows:
        intersection = int(row.get("exact_lifecycle_intersection_count") or 0)
        allowed = int(row.get("allowed_for_calibration_flag") or 0)
        if allowed and intersection <= 0:
            errors.append(f"allowed bridge pair has no exact lifecycle intersection: {row.get('source_event_path')}")
        if not allowed and int(row.get("inferred_matching_required_flag") or 0) != 1:
            errors.append(f"non-allowed bridge pair must be marked inferred-required: {row.get('source_event_path')}")
    for row in bridge_rows:
        bridge_id = str(row.get("bridge_id") or "")
        if bridge_id in bridge_ids:
            errors.append(f"duplicate bridge_id: {bridge_id}")
        bridge_ids.add(bridge_id)
        for column in ("inferred_matching_used_flag", "trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(row.get(column) or 0) != 0:
                errors.append(f"{column} must remain 0 for bridge row {row.get('bridge_id')}")
        if not row.get("source_receipt_id") or not row.get("lifecycle_id"):
            errors.append(f"bridge row missing explicit source receipt or lifecycle id: {row.get('bridge_id')}")
    return errors


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_EXPLICIT_BRIDGE_SEARCH_ERROR] {error}")
        sys.exit(1)
    bridge_rows = len(_read_csv(BRIDGE_PATH))
    buildable_pairs = sum(
        1 for row in _read_csv(AUDIT_PATH) if int(row.get("allowed_for_calibration_flag") or 0) == 1
    )
    print(f"[L3_EXPLICIT_BRIDGE_SEARCH_OK] buildable_pairs={buildable_pairs} bridge_rows={bridge_rows}")


if __name__ == "__main__":
    main()
