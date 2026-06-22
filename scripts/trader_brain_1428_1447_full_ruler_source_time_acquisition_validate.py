from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition"
REPORT = ROOT / "docs/reports/task_1428_1447_full_ruler_source_time_acquisition/task_1428_1447_full_ruler_source_time_acquisition.md"

REQUIRED = [
    "task1428_source_time_schema.csv",
    "task1429_candidate_cik_download_plan.csv",
    "task1430_sec_companyfacts_download_ledger.csv",
    "task1431_source_time_panel.csv",
    "task1432_coverage_comparison.csv",
    "task1432_full_companyfacts_denominator_panel.csv",
    "task1433_full_market_cap_proxy_panel.csv",
    "task1434_full_materiality_ruler_panel.csv",
    "task1435_expectation_ruler_time_checked_panel.csv",
    "task1436_absorption_ruler_time_checked_panel.csv",
    "task1437_source_receipt_exit_time_checked_panel.csv",
    "task1438_price_path_exit_time_checked_panel.csv",
    "task1444_integrated_ruler_panel_v2.csv",
    "task1445_payoff_ranker_v4.csv",
    "task1446_policy_specs.csv",
    "task1446_replay_trades.csv",
    "task1446_replay_equity.csv",
    "task1446_replay_metrics.csv",
    "task1447_acceptance_gate.csv",
    "task1447_closeout.csv",
    "task1447_closeout.json",
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
            print(f"[TASK1428_1447_ERROR] {error}")
        return 1

    plan = read_csv(OUT_DIR / "task1429_candidate_cik_download_plan.csv")
    ledger = read_csv(OUT_DIR / "task1430_sec_companyfacts_download_ledger.csv")
    source_time = read_csv(OUT_DIR / "task1431_source_time_panel.csv")
    denom = read_csv(OUT_DIR / "task1432_full_companyfacts_denominator_panel.csv")
    materiality = read_csv(OUT_DIR / "task1434_full_materiality_ruler_panel.csv")
    rank = read_csv(OUT_DIR / "task1445_payoff_ranker_v4.csv")
    specs = read_csv(OUT_DIR / "task1446_policy_specs.csv")
    metrics = read_csv(OUT_DIR / "task1446_replay_metrics.csv")
    coverage = read_csv(OUT_DIR / "task1432_coverage_comparison.csv")
    gate = read_csv(OUT_DIR / "task1447_acceptance_gate.csv")

    if len(plan) != 280:
        errors.append(f"expected 280 CIK plan rows, found {len(plan)}")
    if len(ledger) != 280:
        errors.append(f"expected 280 download ledger rows, found {len(ledger)}")
    bad_downloads = [row for row in ledger if row["download_state"] not in {"downloaded", "cached_existing"}]
    if bad_downloads:
        errors.append(f"companyfacts download failures: {len(bad_downloads)}")
    if len(source_time) != 3100 or len(denom) != 3100 or len(materiality) != 3100 or len(rank) != 3100:
        errors.append("expected 3100 rows for source_time/denom/materiality/rank panels")

    denom_by_id = {row["candidate_source_id"]: row for row in denom}
    for row in materiality:
        cid = row["candidate_source_id"]
        if denom_by_id[cid]["denominator_source_gap"] == "1" and row["materiality_ruler_state"] != "materiality_source_gap":
            errors.append(f"denominator gap raised materiality: {cid}")
        if row["assignment_uses_future_outcome"] != "0":
            errors.append(f"materiality future flag nonzero: {cid}")

    source_time_pass = sum(1 for row in source_time if row["assignment_time_pass"] == "1")
    if source_time_pass < 3000:
        errors.append(f"source time pass too low: {source_time_pass}")
    for row in source_time:
        if row["source_time_state"] != "source_gap" and row["available_to_brain_ts"] > row["decision_asof_ts"][:10]:
            errors.append(f"future source-time row: {row['candidate_source_id']}")

    spec_counts: dict[str, int] = {}
    for row in specs:
        spec_counts[row["policy_variant_id"]] = spec_counts.get(row["policy_variant_id"], 0) + 1
        if row["assignment_uses_future_outcome"] != "0":
            errors.append(f"future assignment in spec: {row['policy_spec_id']}")
    if spec_counts != {"ruler_top3_v1": 186, "ruler_top5_v1": 310, "ruler_top10_v1": 620}:
        errors.append(f"unexpected policy counts: {spec_counts}")

    if len(metrics) != 3:
        errors.append(f"expected 3 metrics rows, found {len(metrics)}")
    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['policy_variant_id']}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")

    coverage_map = {row["coverage_area"]: row for row in coverage}
    if int(float(coverage_map["verified_denominator_rows"]["after_task1447"])) < 3000:
        errors.append("verified denominator coverage did not expand above 3000 rows")
    if float(coverage_map["ruler_top3_v1_cagr"]["after_task1447"]) >= 0.30:
        errors.append("unexpected acceptance-like CAGR; review gate before any claim")

    text = REPORT.read_text(encoding="utf-8")
    if "Test results do not modify strategy acceptance status." not in text:
        errors.append("report missing validation authority footer")

    if errors:
        for error in errors:
            print(f"[TASK1428_1447_ERROR] {error}")
        return 1
    print("[TASK1428_1447_OK] full ruler source-time acquisition artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
