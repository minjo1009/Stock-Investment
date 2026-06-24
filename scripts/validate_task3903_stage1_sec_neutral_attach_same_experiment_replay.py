from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3903_stage1_sec_neutral_attach_same_experiment_replay"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
FRONTEND_SNAPSHOT = ROOT / "data/frontend_snapshots/current_backtest_snapshot.json"

REQUIRED = [
    ARTIFACT_DIR / "stage1_sec_neutral_attach_panel.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_replay_guard_rows.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_replay_trades.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_replay_equity.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_replay_metrics.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_comparison.csv",
    ARTIFACT_DIR / "original_top3_reference_metrics.csv",
    ARTIFACT_DIR / "stage1_sec_same_experiment_replay_summary.json",
    REPORT_DIR / "stage1_sec_neutral_attach_same_experiment_replay_report.md",
    REPORT_DIR / "task_3903_decision.csv",
    REPORT_DIR / "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def main() -> None:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            fail(failures, f"missing required artifact: {path}")
    if failures:
        for failure in failures:
            print(f"[TASK3903_VALIDATE_ERROR] {failure}")
        sys.exit(1)

    summary = json.loads((ARTIFACT_DIR / "stage1_sec_same_experiment_replay_summary.json").read_text(encoding="utf-8"))
    attach = rows(ARTIFACT_DIR / "stage1_sec_neutral_attach_panel.csv")
    metrics = rows(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_metrics.csv")
    comparison = rows(ARTIFACT_DIR / "stage1_sec_same_experiment_comparison.csv")
    trades = rows(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_trades.csv")
    top3 = rows(ARTIFACT_DIR / "original_top3_reference_metrics.csv")
    original = {row["policy_variant_id"]: row for row in rows(TASK2381 / "task2386_replay_metrics.csv")}
    frontend_snapshot = json.loads(FRONTEND_SNAPSHOT.read_text(encoding="utf-8")) if FRONTEND_SNAPSHOT.exists() else {}

    if summary.get("verdict") != "stage1_sec_neutral_attach_same_experiment_replay_complete":
        fail(failures, "unexpected verdict")
    if int(summary.get("full_l5_rows", 0)) != 3100:
        fail(failures, "full L5 rows should remain 3100")
    if int(summary.get("sec_attach_rows", 0)) != 3100:
        fail(failures, "SEC attach panel should cover 3100 rows")
    if int(summary.get("row_excluded_by_sec_gate", 1)) != 0:
        fail(failures, "SEC gate excluded rows")
    if int(summary.get("candidate_pool_preserved", 0)) != 1:
        fail(failures, "candidate pool was not preserved")
    if int(summary.get("same_experiment_parity_pass", 0)) != 1:
        fail(failures, "same-experiment parity did not pass")
    if int(summary.get("new_strategy_created", 1)) != 0:
        fail(failures, "new strategy was unexpectedly created")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        fail(failures, "strategy status changed")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        fail(failures, "deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        fail(failures, "real capital status changed")
    if frontend_snapshot.get("selectedTaskId") != "Task3903":
        fail(failures, "frontend current backtest snapshot was not updated for Task3903")
    if frontend_snapshot.get("metrics", {}).get("finalEquity") != float(summary.get("best_final_equity", 0)):
        fail(failures, "frontend current backtest snapshot final equity does not match Task3903")
    if frontend_snapshot.get("governance", {}).get("strategyAcceptance") != "NOT_ACCEPTED":
        fail(failures, "frontend snapshot changed strategy status")

    if len(metrics) != 3:
        fail(failures, f"expected 3 current policy metrics, got {len(metrics)}")
    if not top3:
        fail(failures, "missing original top3 reference")
    for idx, row in enumerate(attach, start=2):
        if row.get("row_excluded_by_sec_gate") != "0":
            fail(failures, f"attach row {idx} excluded by SEC gate")
        if row.get("feature_used_for_selector") != "0":
            fail(failures, f"attach row {idx} used SEC for selector")
        if row.get("feature_used_for_sizing") != "0":
            fail(failures, f"attach row {idx} used SEC for sizing")
        if row.get("feature_used_for_exit") != "0":
            fail(failures, f"attach row {idx} used SEC for exit")
        if row.get("missing_source_is_negative") != "0":
            fail(failures, f"attach row {idx} treats missing source as negative")
        if row.get("assignment_uses_future_outcome") != "0":
            fail(failures, f"attach row {idx} uses future outcome")
        if row.get("outcome_used_for_assignment") != "0":
            fail(failures, f"attach row {idx} uses outcome for assignment")

    for idx, row in enumerate(metrics, start=2):
        base = original.get(row["policy_variant_id"])
        if not base:
            fail(failures, f"metrics row {idx} unknown policy {row['policy_variant_id']}")
            continue
        for key in ("final_equity", "cagr", "max_drawdown", "trade_count"):
            if str(row.get(key)) != str(base.get(key)):
                fail(failures, f"metrics row {idx} {key} differs from Task2381")
        if row.get("same_experiment_as_task2381") != "1":
            fail(failures, f"metrics row {idx} missing same-experiment flag")
        if row.get("candidate_pool_preserved") != "1":
            fail(failures, f"metrics row {idx} missing candidate-pool flag")
        if row.get("assignment_uses_future_outcome") != "0":
            fail(failures, f"metrics row {idx} uses future outcome")
        if row.get("outcome_used_for_assignment") != "0":
            fail(failures, f"metrics row {idx} uses outcome assignment")
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            fail(failures, f"metrics row {idx} changed strategy status")
        if row.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            fail(failures, f"metrics row {idx} changed deployment status")
        if row.get("real_capital") != "FORBIDDEN":
            fail(failures, f"metrics row {idx} changed real capital status")

    for idx, row in enumerate(comparison, start=2):
        if row.get("same_experiment_parity_pass") != "1":
            fail(failures, f"comparison row {idx} parity failed")
    if len(trades) != 372:
        fail(failures, f"expected 372 trade rows across variants, got {len(trades)}")

    if failures:
        for failure in failures:
            print(f"[TASK3903_VALIDATE_ERROR] {failure}")
        sys.exit(1)
    print(
        "[TASK3903_STAGE1_SEC_NEUTRAL_ATTACH_SAME_EXPERIMENT_REPLAY_VALIDATE_OK] "
        f"full_l5={summary['full_l5_rows']} sec_attached={summary['sec_attached_asof_rows']} "
        f"excluded={summary['row_excluded_by_sec_gate']} best={summary['best_policy_variant_id']} "
        f"cagr={summary['best_cagr']} mdd={summary['best_max_drawdown']}"
    )
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
