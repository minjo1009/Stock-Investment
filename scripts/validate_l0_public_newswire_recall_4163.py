from __future__ import annotations

import csv
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4163_gn_filtering_recall_audit"
SUMMARY_PATH = ARTIFACT_DIR / "recall_reclassification_summary.json"
OVERLAY_PATH = ARTIFACT_DIR / "l0_public_newswire_recall_overlay.csv"
REPORT_PATH = ARTIFACT_DIR / "validator_report.json"


def read_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_overlay_sample(path: Path, limit: int = 20000) -> tuple[int, int, set[str], int]:
    if not path.exists():
        return 0, 0, set(), 0
    total = 0
    authority_nonzero = 0
    task_id_mismatch = 0
    statuses: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            statuses.add(str(row.get("new_entity_mapping_status", "")))
            if str(row.get("authority_flag", "0")) not in {"", "0"}:
                authority_nonzero += 1
            if EXPECTED_TASK_ID and row.get("task_id") != EXPECTED_TASK_ID:
                task_id_mismatch += 1
            if total >= limit:
                break
    return total, authority_nonzero, statuses, task_id_mismatch


EXPECTED_TASK_ID = ""


def main() -> int:
    global EXPECTED_TASK_ID
    parser = argparse.ArgumentParser(description="Validate L0 public newswire recall overlay artifacts.")
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--expected-task-id", default="")
    args = parser.parse_args()
    EXPECTED_TASK_ID = args.expected_task_id
    summary_path = args.artifact_dir / "recall_reclassification_summary.json"
    overlay_path = args.artifact_dir / "l0_public_newswire_recall_overlay.csv"
    report_path = args.artifact_dir / "validator_report.json"
    failures: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []
    summary = read_summary(summary_path)
    if not summary:
        failures.append("missing recall reclassification summary")
    else:
        if args.expected_task_id and summary.get("task_id") != args.expected_task_id:
            failures.append(f"unexpected task_id: {summary.get('task_id')}")
        if summary.get("schema_version") != "l0_public_newswire_recall_overlay_v1":
            failures.append("unexpected summary schema_version")
        if int(summary.get("latest_shard_files_processed", 0) or 0) <= 0:
            failures.append("no latest shard files processed")
        else:
            passes.append(f"processed_files={summary.get('latest_shard_files_processed')}")
        safety = summary.get("safety", {})
        for key in ("raw_mutation_count", "broker_mutation_count", "live_order_count", "paper_promotion_count", "real_capital_flag_count"):
            if int(safety.get(key, 0) or 0) != 0:
                failures.append(f"safety flag nonzero: {key}={safety.get(key)}")
        total_recall = sum(int(row.get("recall_review_rows", 0) or 0) for row in summary.get("file_summaries", []))
        total_changed = sum(int(row.get("status_changed_rows", 0) or 0) for row in summary.get("file_summaries", []))
        if total_recall <= 0:
            failures.append("no recall review rows found")
        else:
            passes.append(f"recall_review_rows={total_recall}")
        if total_changed <= 0:
            warnings.append("no status changes found in reclassification")
        else:
            passes.append(f"status_changed_rows={total_changed}")

    overlay_rows, authority_nonzero, statuses, task_id_mismatch = read_overlay_sample(overlay_path)
    if overlay_rows <= 0:
        failures.append("missing or empty recall overlay csv")
    else:
        passes.append(f"overlay_rows_sampled={overlay_rows}")
    if authority_nonzero:
        failures.append(f"overlay authority_flag nonzero rows in sample: {authority_nonzero}")
    if task_id_mismatch:
        failures.append(f"overlay task_id mismatch rows in sample: {task_id_mismatch}")
    if "ENTITY_CANDIDATE_REVIEW" not in statuses:
        warnings.append("ENTITY_CANDIDATE_REVIEW not present in sampled overlay statuses")
    else:
        passes.append("ENTITY_CANDIDATE_REVIEW present")

    report = {"passes": passes, "warnings": warnings, "failures": failures}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if failures:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
