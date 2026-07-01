from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4128"
SLUG = "task_4128_l0_l1_six_stage_end_to_end_closeout_audit"
REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
SUMMARY_PATH = REPORT_DIR / "l0_l1_six_stage_closeout_summary.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "validation_results.md",
        SUMMARY_PATH,
        REPORT_DIR / "task_4128_stage_status_audit.csv",
        REPORT_DIR / "task_4128_safety_boundary_audit.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors
    summary = read_json(SUMMARY_PATH)
    if summary.get("task_id") != TASK_ID:
        errors.append("summary task_id must be TASK-4128")
    if summary.get("six_stage_closeout_status") != "COMPLETE_PARTIAL_L2_CONTEXT_HANDOFF_READY":
        errors.append(f"unexpected closeout status: {summary.get('six_stage_closeout_status')}")
    if int(summary.get("stage_count", 0) or 0) != 6:
        errors.append("stage_count must be 6")
    if int(summary.get("stage_status_pass_count", 0) or 0) != 6:
        errors.append("all six stage statuses must pass")
    if int(summary.get("safety_boundary_pass_count", 0) or 0) != int(summary.get("safety_boundary_count", -1) or -1):
        errors.append("all safety boundaries must pass")
    if int(summary.get("stage5_full_coverage_complete", 0) or 0) != 1:
        errors.append("Stage 5 full coverage must be complete")
    if int(summary.get("stage5_coverage_complete_count", 0) or 0) != int(summary.get("stage5_coverage_source_count", -1) or -1):
        errors.append("Stage 5 source coverage must be complete")
    if summary.get("stage6_l2_handoff_decision") != "PARTIAL_CONTEXT_ONLY_HANDOFF_READY":
        errors.append("Stage 6 L2 handoff must be partial context-only ready")
    if int(summary.get("stage6_l2_context_admitted_rows", 0) or 0) <= 0:
        errors.append("Stage 6 L2 context admitted rows must be positive")
    if int(summary.get("stage6_blocked_rows", 0) or 0) <= 0:
        errors.append("Stage 6 blocked rows must remain visible")
    if int(summary.get("stage6_strict_gate_pass_rows", 1)) != 0:
        errors.append("Stage 6 strict gate rows must remain 0")
    if int(summary.get("stage6_trade_feature_allowed_rows", 1)) != 0:
        errors.append("Stage 6 trade feature rows must remain 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    stage_rows = read_csv(REPORT_DIR / "task_4128_stage_status_audit.csv")
    if len(stage_rows) != 6:
        errors.append("stage status audit must have six rows")
    for row in stage_rows:
        if row.get("status_match") != "1":
            errors.append(f"stage status mismatch: stage {row.get('stage')}")
    safety_rows = read_csv(REPORT_DIR / "task_4128_safety_boundary_audit.csv")
    for row in safety_rows:
        if row.get("pass") != "1":
            errors.append(f"safety boundary failed: {row.get('boundary')}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_L1_SIX_STAGE_CLOSEOUT_ERROR] {error}")
        return 1
    print("[L0_L1_SIX_STAGE_CLOSEOUT_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
