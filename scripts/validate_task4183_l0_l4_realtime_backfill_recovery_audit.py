from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "TASK-4183"
OUT_DIR = Path("data/artifacts/task_4183_l0_l4_realtime_backfill_recovery_audit")
REPORT_DIR = Path("docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit")


REQUIRED = [
    Path("scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py"),
    Path("scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py"),
    OUT_DIR / "task_4183_recovery_audit_summary.json",
    OUT_DIR / "task_4183_level_verdicts.csv",
    OUT_DIR / "task_4183_scheduled_tasks.json",
    OUT_DIR / "task_4183_process_snapshot.json",
    OUT_DIR / "task_4183_db_latest_rows.json",
    OUT_DIR / "task_4183_artifact_snapshot.json",
    REPORT_DIR / "task_result_contract.yaml",
    REPORT_DIR / "report.md",
    REPORT_DIR / "artifact_manifest.csv",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    passes: list[str] = []
    failures: list[str] = []

    for path in REQUIRED:
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing: {path}")

    if failures:
        print("TASK-4182 VALIDATION")
        for item in failures:
            print(f"FAIL {item}")
        return 1

    summary = load_json(OUT_DIR / "task_4183_recovery_audit_summary.json")
    if summary.get("task_id") != TASK_ID:
        failures.append("summary task_id mismatch")
    if summary.get("diagnostic_only") != 1:
        failures.append("diagnostic_only flag not closed")
    for flag in ["trade_authority_flag", "broker_mutation_permitted_flag", "paper_promotion_permitted_flag", "real_capital_permitted_flag"]:
        if summary.get(flag) != 0:
            failures.append(f"{flag} opened")

    verdict_rows = list(csv.DictReader((OUT_DIR / "task_4183_level_verdicts.csv").open(encoding="utf-8")))
    levels = {row.get("level") for row in verdict_rows}
    if levels != {"L0", "L1", "L2", "L3", "L4"}:
        failures.append(f"unexpected level coverage: {sorted(levels)}")
    if not any("BLOCKER" in row.get("status", "") or row.get("status", "").startswith("STALE_OR_NOT_REALTIME") for row in verdict_rows):
        failures.append("audit did not surface any blocker/stale status; expected recovery audit to preserve uncertainty")

    scheduled = load_json(OUT_DIR / "task_4183_scheduled_tasks.json")
    if not isinstance(scheduled, list) or not scheduled:
        failures.append("scheduled task snapshot empty")
    if not any(row.get("TaskName") == "TraderBrainL0BackfillWorkerRecovery4148" for row in scheduled if isinstance(row, dict)):
        failures.append("backfill recovery scheduled task missing from snapshot")

    manifest_paths = {
        row["path"]
        for row in csv.DictReader((REPORT_DIR / "artifact_manifest.csv").open(encoding="utf-8"))
    }
    for path in REQUIRED:
        if str(path).replace("\\", "/") not in manifest_paths:
            failures.append(f"manifest missing {path}")

    print("TASK-4183 L0-L4 RECOVERY AUDIT VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    if failures:
        for item in failures:
            print(f"FAIL {item}")
        print("RESULT: FAIL")
        return 1
    print(f"PASS overall_verdict: {summary.get('overall_verdict')}")
    print("PASS safety flags closed")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
