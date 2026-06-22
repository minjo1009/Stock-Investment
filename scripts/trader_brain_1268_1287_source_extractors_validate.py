from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1268_1287_source_extractors"
REPORT = ROOT / "docs/reports/task_1268_1287_source_extractors"

REQUIRED_FILES = [
    "task1268_backtest_source_data_schema.csv",
    "task1269_sec_complete_submission_download_ledger.csv",
    "task1270_sec_exhibit_document_index.csv",
    "task1271_ir_ceo_exhibit_evidence.csv",
    "task1272_contract_order_exhibit_evidence.csv",
    "task1273_enhanced_l1_multisource_packets.csv",
    "task1274_enhanced_l2_multisource_interpretation.csv",
    "task1275_enhanced_l3_relation_edges.csv",
    "task1276_backtest_readiness_panel.csv",
    "task1277_remaining_source_gap_ledger.csv",
    "task1278_backtest_readiness_gate.csv",
    "task1287_closeout.csv",
    "task1287_closeout.json",
    "artifact_manifest.csv",
]

REQUIRED_FAMILIES = {
    "sec_survival",
    "ir_ceo_earnings_call",
    "contract_orders_customer",
    "analyst_institution",
    "policy_news_catalyst",
    "market_price_volume",
}


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1268_1287_source_extractors.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1268_1287_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    schema = rows("task1268_backtest_source_data_schema.csv")
    downloads = rows("task1269_sec_complete_submission_download_ledger.csv")
    docs = rows("task1270_sec_exhibit_document_index.csv")
    ir = rows("task1271_ir_ceo_exhibit_evidence.csv")
    contracts = rows("task1272_contract_order_exhibit_evidence.csv")
    l1 = rows("task1273_enhanced_l1_multisource_packets.csv")
    l2 = rows("task1274_enhanced_l2_multisource_interpretation.csv")
    l3 = rows("task1275_enhanced_l3_relation_edges.csv")
    readiness = rows("task1276_backtest_readiness_panel.csv")
    gaps = rows("task1277_remaining_source_gap_ledger.csv")
    gate = rows("task1278_backtest_readiness_gate.csv")
    closeout = rows("task1287_closeout.csv")
    closeout_json = json.loads((ART / "task1287_closeout.json").read_text(encoding="utf-8"))

    if {row["source_family"] for row in schema} != REQUIRED_FAMILIES:
        errors.append("source schema must cover all six source families")
    if sum(1 for row in downloads if row["download_status"] in {"downloaded", "cached"}) < 100:
        errors.append("must cache at least 100 complete SEC submissions")
    if len(docs) < 50:
        errors.append("must index at least 50 exhibit documents")
    if len(ir) < 20:
        errors.append("IR/CEO exhibit evidence too sparse")
    if len(contracts) < 20:
        errors.append("contract/order exhibit evidence too sparse")
    if len(l1) != 310 or len(l2) != 310 or len(readiness) != 310:
        errors.append("enhanced L1/L2/readiness panels must cover 310 selections")
    if len(l3) != 310 * 6:
        errors.append("enhanced L3 must contain six source-family edges per selection")
    if not any(row["source_family"] == "analyst_institution" and row["gap_state"] == "vendor_required" for row in gaps):
        errors.append("analyst institution vendor gap must be explicit")
    if any(row["missing_is_negative"] != "0" for row in schema):
        errors.append("schema must preserve missing-is-not-negative")
    if any(row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0" for row in ir + contracts + l1 + l2 + l3 + readiness):
        errors.append("extractor outputs must not directly allow selection/replay")
    if any(row["assignment_uses_future_outcome"] != "0" for row in l2 + l3):
        errors.append("L2/L3 must not use future outcomes")
    if not any(row["enhanced_composite_interpretation"] == "validated_growth_multisource_confirmed" for row in l2):
        errors.append("must produce at least one validated growth multisource interpretation")
    for row in [gate[0], closeout[0], closeout_json]:
        if str(row.get("replay_executed")) != "0":
            errors.append("replay must not be executed")
        if str(row.get("selection_promoted")) != "0":
            errors.append("selection must not be promoted")
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row.get("real_capital") != "FORBIDDEN":
            errors.append("real capital changed")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1268_1287_SOURCE_EXTRACTORS_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1268_1287_SOURCE_EXTRACTORS_OK] artifacts validated")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
