from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.calibration_bridge_builder import audit_csv_bridge_eligibility, eligibility_rows_to_dicts


DEFAULT_CANDIDATES = [
    Path("docs/reports/task_387_canonical_continuation_oos_overlay/canonical_oos_quality_panel.csv"),
    Path("docs/reports/task_391_intraday_canonical_oos_validation/split_lifecycle_panel.csv"),
    Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv"),
]


def build_audit(candidate_paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in candidate_paths:
        if path.exists():
            rows.append(audit_csv_bridge_eligibility(path))
    return eligibility_rows_to_dicts(rows)


def write_audit(rows: list[dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "candidate_path",
        "has_l3_bridge_key_flag",
        "has_outcome_key_flag",
        "has_outcome_value_flag",
        "eligible_bridge_row_count",
        "inferred_matching_required_flag",
        "allowed_for_calibration_flag",
        "available_bridge_columns",
        "available_outcome_columns",
        "missing_bridge_columns",
        "rejection_reason",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/reports/task_l3_calibration_rule_migration/l3_calibration_bridge_gap_audit.csv"),
    )
    parser.add_argument("--candidate", type=Path, action="append", default=[])
    args = parser.parse_args()
    rows = build_audit(args.candidate or DEFAULT_CANDIDATES)
    write_audit(rows, args.out)
    allowed = sum(int(row["allowed_for_calibration_flag"]) for row in rows)
    print(f"[L3_BRIDGE_AUDIT] candidates={len(rows)} allowed={allowed} out={args.out}")


if __name__ == "__main__":
    main()
