from __future__ import annotations

import csv
import sys
from pathlib import Path


REPORT_DIR = Path("docs/reports/task_l3_calibration_rule_migration")
OUTCOME_PATH = REPORT_DIR / "l3_calibration_outcomes.csv"
BUCKET_PATH = REPORT_DIR / "l3_calibration_audit_buckets.csv"


def validate() -> list[str]:
    errors: list[str] = []
    if not OUTCOME_PATH.exists():
        errors.append(f"missing outcome table: {OUTCOME_PATH}")
    if not BUCKET_PATH.exists():
        errors.append(f"missing bucket table: {BUCKET_PATH}")
    if errors:
        return errors

    rows = _read_csv(OUTCOME_PATH)
    buckets = _read_csv(BUCKET_PATH)
    if not rows:
        errors.append("calibration outcome table is empty")
    if not buckets:
        errors.append("calibration audit bucket table is empty")
    row_ids: set[str] = set()
    non_missing = 0
    for row in rows:
        row_id = str(row.get("calibration_row_id") or "")
        if row_id in row_ids:
            errors.append(f"duplicate calibration_row_id: {row_id}")
        row_ids.add(row_id)
        for column in (
            "inferred_matching_used_flag",
            "label_used_in_assignment_flag",
            "outcome_used_in_assignment_flag",
            "trade_output_flag",
            "score_output_flag",
            "order_intent_flag",
        ):
            if int(row.get(column) or 0) != 0:
                errors.append(f"{column} must remain 0 for calibration row {row_id}")
        missing_label = int(row.get("missing_label_flag") or 0)
        if missing_label:
            if row.get("outcome_label") != "MISSING":
                errors.append(f"missing label row must use outcome_label=MISSING: {row_id}")
        else:
            non_missing += 1
            for column in ("outcome_bridge_key", "outcome_start_ts", "outcome_end_ts", "outcome_value"):
                if not str(row.get(column) or "").strip():
                    errors.append(f"non-missing row lacks {column}: {row_id}")
    if non_missing == 0:
        errors.append("calibration outcome table has no non-missing rows")
    calibrated = 0
    for bucket in buckets:
        status = str(bucket.get("calibration_status") or "")
        probability = str(bucket.get("calibrated_probability") or "").strip()
        if status == "CALIBRATED":
            calibrated += 1
            if not probability:
                errors.append(f"CALIBRATED bucket lacks calibrated_probability: {bucket}")
        elif probability:
            errors.append(f"non-CALIBRATED bucket has calibrated_probability: {bucket}")
    if calibrated == 0:
        errors.append("no calibrated diagnostic buckets were produced")
    return errors


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_CALIBRATION_TABLE_ERROR] {error}")
        sys.exit(1)
    rows = _read_csv(OUTCOME_PATH)
    non_missing = sum(1 for row in rows if int(row.get("missing_label_flag") or 0) == 0)
    buckets = _read_csv(BUCKET_PATH)
    calibrated = sum(1 for row in buckets if row.get("calibration_status") == "CALIBRATED")
    print(
        "[L3_CALIBRATION_TABLE_OK] "
        f"rows={len(rows)} non_missing={non_missing} buckets={len(buckets)} calibrated_buckets={calibrated}"
    )


if __name__ == "__main__":
    main()
