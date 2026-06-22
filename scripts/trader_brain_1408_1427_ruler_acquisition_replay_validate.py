from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay"
REPORT = ROOT / "docs/reports/task_1408_1427_ruler_acquisition_replay/task_1408_1427_ruler_acquisition_replay.md"

REQUIRED_FILES = [
    "task1408_ruler_expert_review_packet.csv",
    "task1409_scale_ruler_schema.csv",
    "task1410_companyfacts_denominator_panel.csv",
    "task1411_market_cap_proxy_panel.csv",
    "task1412_event_value_panel.csv",
    "task1413_materiality_ruler_panel.csv",
    "task1414_expectation_ruler_schema.csv",
    "task1415_public_guidance_revision_panel.csv",
    "task1416_analyst_pit_audit.csv",
    "task1417_expectation_ruler_panel.csv",
    "task1418_market_absorption_enhanced_panel.csv",
    "task1419_absorption_ruler_panel.csv",
    "task1420_exit_ruler_schema.csv",
    "task1421_source_receipt_exit_panel.csv",
    "task1422_price_path_risk_exit_panel.csv",
    "task1423_hold_extend_receipt_panel.csv",
    "task1424_integrated_ruler_panel.csv",
    "task1425_payoff_ranker_v3.csv",
    "task1426_policy_specs.csv",
    "task1426_replay_trades.csv",
    "task1426_replay_equity.csv",
    "task1426_replay_metrics.csv",
    "task1427_expert_post_audit.csv",
    "task1427_acceptance_gate.csv",
    "task1427_closeout.csv",
    "task1427_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_count(errors: list[str], path: Path, expected: int) -> list[dict[str, str]]:
    rows = read_csv(path)
    if len(rows) != expected:
        fail(errors, f"{path.name}: expected {expected} rows, found {len(rows)}")
    return rows


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = OUT_DIR / name
        if not path.exists():
            fail(errors, f"missing artifact: {name}")
    if not REPORT.exists():
        fail(errors, f"missing report: {REPORT}")
    if errors:
        for error in errors:
            print(f"[TASK1408_1427_ERROR] {error}")
        return 1

    denom = require_count(errors, OUT_DIR / "task1410_companyfacts_denominator_panel.csv", 3100)
    materiality = require_count(errors, OUT_DIR / "task1413_materiality_ruler_panel.csv", 3100)
    analyst = require_count(errors, OUT_DIR / "task1416_analyst_pit_audit.csv", 3100)
    absorption = require_count(errors, OUT_DIR / "task1419_absorption_ruler_panel.csv", 3100)
    integrated = require_count(errors, OUT_DIR / "task1424_integrated_ruler_panel.csv", 3100)
    rank = require_count(errors, OUT_DIR / "task1425_payoff_ranker_v3.csv", 3100)
    specs = require_count(errors, OUT_DIR / "task1426_policy_specs.csv", 1116)
    source_exit = require_count(errors, OUT_DIR / "task1421_source_receipt_exit_panel.csv", 1116)
    price_exit = require_count(errors, OUT_DIR / "task1422_price_path_risk_exit_panel.csv", 1116)
    metrics = require_count(errors, OUT_DIR / "task1426_replay_metrics.csv", 3)
    gate = require_count(errors, OUT_DIR / "task1427_acceptance_gate.csv", 1)

    by_policy: dict[str, int] = {}
    for row in specs:
        by_policy[row["policy_variant_id"]] = by_policy.get(row["policy_variant_id"], 0) + 1
        if row.get("assignment_uses_future_outcome") != "0":
            fail(errors, f"policy spec uses future outcome: {row.get('policy_spec_id')}")
    expected_specs = {"ruler_top3_v1": 186, "ruler_top5_v1": 310, "ruler_top10_v1": 620}
    if by_policy != expected_specs:
        fail(errors, f"policy selection counts mismatch: {by_policy}")

    mat_by_id = {row["candidate_source_id"]: row for row in materiality}
    denom_by_id = {row["candidate_source_id"]: row for row in denom}
    for cid, row in mat_by_id.items():
        if denom_by_id[cid]["denominator_source_gap"] == "1" and row["materiality_ruler_state"] != "materiality_source_gap":
            fail(errors, f"denominator gap raised materiality state: {cid}")
        if row.get("assignment_uses_future_outcome") != "0":
            fail(errors, f"materiality uses future outcome: {cid}")

    if not any(row["denominator_source_gap"] == "0" for row in denom):
        fail(errors, "no verified denominator rows found")
    if not any(row["materiality_ruler_state"] == "high_verified_materiality" for row in materiality):
        fail(errors, "no high verified materiality rows found")

    for row in analyst:
        if row["analyst_pit_available"] != "0" or row["analyst_pit_source_gap"] != "1":
            fail(errors, f"analyst PIT audit is not explicit gap: {row['candidate_source_id']}")
    for row in absorption:
        if row.get("assignment_uses_future_outcome") != "0":
            fail(errors, f"absorption assignment future flag nonzero: {row['candidate_source_id']}")
        if row["event_date"] and row["event_date"] > row["window_end_date"]:
            fail(errors, f"absorption window leaks beyond decision: {row['candidate_source_id']}")
    for row in integrated + rank:
        if row.get("assignment_uses_future_outcome") != "0":
            fail(errors, f"integrated/rank future flag nonzero: {row.get('candidate_source_id')}")

    if not source_exit or not price_exit:
        fail(errors, "exit panels empty")
    if not all(row["exit_family"] == "source_receipt_exit" for row in source_exit):
        fail(errors, "source exit panel has wrong exit_family")
    if not all(row["exit_family"] == "price_path_risk_exit" for row in price_exit):
        fail(errors, "price exit panel has wrong exit_family")
    if not any(row["source_receipt_exit_ready"] == "1" for row in source_exit):
        fail(errors, "no source receipt exits ready")
    if not any(row["price_path_risk_exit_ready"] == "1" for row in price_exit):
        fail(errors, "no price path exits ready")

    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            fail(errors, f"metric acceptance overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            fail(errors, f"metric deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            fail(errors, f"metric real capital overclaim: {row['policy_variant_id']}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        fail(errors, "acceptance gate overclaims status")

    footer = REPORT.read_text(encoding="utf-8")
    required_footer = "Test results do not modify strategy acceptance status."
    if required_footer not in footer:
        fail(errors, "report missing validation authority footer")

    if errors:
        for error in errors:
            print(f"[TASK1408_1427_ERROR] {error}")
        return 1
    print("[TASK1408_1427_OK] ruler acquisition replay artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
