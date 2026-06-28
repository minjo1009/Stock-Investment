from __future__ import annotations

import csv
import sys
from pathlib import Path


AUDIT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_task742_schema_search_audit.csv")


def validate() -> list[str]:
    errors: list[str] = []
    if not AUDIT_PATH.exists():
        return [f"missing audit: {AUDIT_PATH}"]
    rows = _read_csv(AUDIT_PATH)
    if not rows:
        return ["Task742 schema search audit is empty"]
    for row in rows:
        candidate = row.get("candidate_path") or ""
        allowed_packet = _int(row.get("allowed_as_task742_packet_artifact_flag"))
        allowed_calibration = _int(row.get("allowed_for_task742_calibration_flag"))
        packet_schema = _int(row.get("task742_packet_schema_flag"))
        output_count = _int(row.get("task742_output_column_count"))
        overlap = _int(row.get("source_event_overlap_with_canonical_bridge_count"))
        inferred_required = _int(row.get("inferred_matching_required_flag"))
        if allowed_packet and not packet_schema:
            errors.append(f"packet artifact allowed without Task742 packet schema: {candidate}")
        if packet_schema and output_count < 2:
            errors.append(f"Task742 packet schema requires at least two output columns: {candidate}")
        if allowed_calibration and not (allowed_packet and overlap > 0):
            errors.append(f"calibration allowed without exact packet and bridge overlap: {candidate}")
        if allowed_calibration and inferred_required:
            errors.append(f"calibration allowed row must not require inferred matching: {candidate}")
        if not allowed_calibration and not inferred_required:
            errors.append(f"blocked row must mark inferred matching required: {candidate}")
    return errors


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_TASK742_SCHEMA_SEARCH_ERROR] {error}")
        sys.exit(1)
    rows = _read_csv(AUDIT_PATH)
    packet_candidates = sum(_int(row.get("allowed_as_task742_packet_artifact_flag")) for row in rows)
    allowed = sum(_int(row.get("allowed_for_task742_calibration_flag")) for row in rows)
    print(f"[L3_TASK742_SCHEMA_SEARCH_OK] rows={len(rows)} packet_candidates={packet_candidates} allowed={allowed}")


if __name__ == "__main__":
    main()
