from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1508_1517_bottleneck_verification"
REPORT = ROOT / "docs/reports/task_1508_1517_bottleneck_verification/task_1508_1517_bottleneck_verification.md"

REQUIRED = [
    "task1509_candidate_scheduled_return_panel.csv",
    "task1510_rank_bucket_return_summary.csv",
    "task1511_selected_l5_delta_panel.csv",
    "task1512_l5_delta_summary.csv",
    "task1513_scheduled_only_replay_trades.csv",
    "task1513_scheduled_only_replay_equity.csv",
    "task1513_scheduled_only_replay_metrics.csv",
    "task1516_bottleneck_verdict.csv",
    "task1517_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (OUT_DIR / name).exists():
            errors.append(f"missing artifact: {name}")
    if not REPORT.exists():
        errors.append(f"missing report: {REPORT}")
    if errors:
        for error in errors:
            print(f"[TASK1508_1517_ERROR] {error}")
        return 1

    returns = read_csv(OUT_DIR / "task1509_candidate_scheduled_return_panel.csv")
    buckets = read_csv(OUT_DIR / "task1510_rank_bucket_return_summary.csv")
    deltas = read_csv(OUT_DIR / "task1511_selected_l5_delta_panel.csv")
    l5_summary = read_csv(OUT_DIR / "task1512_l5_delta_summary.csv")
    scheduled_metrics = read_csv(OUT_DIR / "task1513_scheduled_only_replay_metrics.csv")
    verdict = read_csv(OUT_DIR / "task1516_bottleneck_verdict.csv")

    if len(returns) != 3100:
        errors.append(f"expected 3100 candidate return rows, found {len(returns)}")
    if len(buckets) != 5:
        errors.append(f"expected 5 rank bucket rows, found {len(buckets)}")
    if len(deltas) != 1116:
        errors.append(f"expected 1116 L5 delta rows, found {len(deltas)}")
    if len(scheduled_metrics) != 3:
        errors.append(f"expected 3 scheduled-only metric rows, found {len(scheduled_metrics)}")
    required_checks = {"l2_l3_rank_signal", "l5_exit_delta", "slot_breadth_and_holding", "overall_bottleneck"}
    checks = {row["check_name"] for row in verdict}
    if not required_checks <= checks:
        errors.append(f"missing verdict checks: {sorted(required_checks - checks)}")

    for row in returns + deltas:
        if row.get("outcome_used_for_assignment") != "0" or row.get("outcome_used_for_audit_only") != "1":
            errors.append(f"outcome audit flag misuse: {row.get('return_row_id') or row.get('l5_delta_id')}")
    for row in scheduled_metrics:
        if row.get("outcome_used_for_assignment") != "0" or row.get("outcome_used_for_audit_only") != "1":
            errors.append(f"scheduled metric audit flag misuse: {row['policy_variant_id']}")
    overall = next(row for row in verdict if row["check_name"] == "overall_bottleneck")
    if "L5_IS_A_MAJOR_BOTTLENECK" not in overall["verdict"]:
        errors.append(f"unexpected overall verdict: {overall['verdict']}")
    rank_signal = next(row for row in verdict if row["check_name"] == "l2_l3_rank_signal")
    if rank_signal["verdict"] != "partial_pass":
        errors.append(f"unexpected rank signal verdict: {rank_signal['verdict']}")
    l5_exit = next(row for row in verdict if row["check_name"] == "l5_exit_delta")
    if l5_exit["verdict"] != "fail":
        errors.append(f"unexpected L5 exit verdict: {l5_exit['verdict']}")

    l5_reasons = {row["exit_reason"] for row in l5_summary}
    if not {"scheduled_exit", "hard_source_invalidation_receipt", "price_path_5d_market_rejection"} <= l5_reasons:
        errors.append("L5 summary missing expected exit reason families")
    report_text = REPORT.read_text(encoding="utf-8")
    if "L5가 큰 병목인 건 맞다." not in report_text:
        errors.append("report missing plain-language bottleneck conclusion")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1508_1517_ERROR] {error}")
        return 1
    print("[TASK1508_1517_OK] bottleneck verification artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
