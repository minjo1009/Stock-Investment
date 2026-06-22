from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1221_1227_collapse_guard_implementation"
REPORT = ROOT / "docs/reports/task_1221_1227_collapse_guard_implementation"

REQUIRED_FILES = [
    "task1221_listing_corporate_action_adapter.csv",
    "task1222_distress_evidence_panel.csv",
    "task1223_product_structure_classifier.csv",
    "task1224_l3_collapse_relation_edges.csv",
    "task1225_l4_collapse_candidate_cards.csv",
    "task1226_l5_collapse_guard_trade_specs.csv",
    "task1227_collapse_guard_replay_trades.csv",
    "task1227_collapse_guard_replay_equity.csv",
    "task1227_collapse_guard_metrics.csv",
    "task1227_collapse_guard_acceptance_gate.csv",
    "task1227_collapse_guard_closeout.csv",
    "task1227_collapse_guard_closeout.json",
    "artifact_manifest.csv",
]


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
    if not (REPORT / "task_1221_1227_collapse_guard_implementation.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1221_1227_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    listing = rows("task1221_listing_corporate_action_adapter.csv")
    distress = rows("task1222_distress_evidence_panel.csv")
    product = rows("task1223_product_structure_classifier.csv")
    edges = rows("task1224_l3_collapse_relation_edges.csv")
    l4 = rows("task1225_l4_collapse_candidate_cards.csv")
    specs = rows("task1226_l5_collapse_guard_trade_specs.csv")
    trades = rows("task1227_collapse_guard_replay_trades.csv")
    equity = rows("task1227_collapse_guard_replay_equity.csv")
    metrics = rows("task1227_collapse_guard_metrics.csv")
    gate = rows("task1227_collapse_guard_acceptance_gate.csv")
    closeout = rows("task1227_collapse_guard_closeout.csv")
    closeout_json = json.loads((ART / "task1227_collapse_guard_closeout.json").read_text(encoding="utf-8"))

    expected = 310
    for name, table in [
        ("listing", listing),
        ("distress", distress),
        ("product", product),
        ("edges", edges),
        ("l4", l4),
        ("specs", specs),
        ("trades", trades),
    ]:
        if len(table) != expected:
            errors.append(f"{name} must contain {expected} slot5 rows")
    if len(equity) != 62:
        errors.append("equity must contain 62 monthly rows")
    if len(metrics) != 1 or len(gate) != 1 or len(closeout) != 1:
        errors.append("metrics gate and closeout must each contain one row")

    future_tables = [
        ("listing", listing, "assignment_uses_future_outcome"),
        ("distress", distress, "assignment_uses_future_outcome"),
        ("product", product, "assignment_uses_future_outcome"),
        ("edges", edges, "assignment_uses_future_outcome"),
        ("l4", l4, "assignment_uses_future_outcome"),
        ("specs", specs, "assignment_uses_future_outcome"),
    ]
    for name, table, field in future_tables:
        if any(row[field] != "0" for row in table):
            errors.append(f"{name} must not use future outcome for assignment")
    if any(row["selection_promoted"] != "0" for row in l4 + specs):
        errors.append("L4/L5 rows must not promote selection")
    if not any(row["product_sleeve"] == "leveraged_or_complex_product" for row in product):
        errors.append("product classifier must identify at least one complex product")
    if not any(row["risk_bucket"] in {"watch", "product_sleeve", "distress_haircut"} for row in specs):
        errors.append("collapse guard must create non-clean risk buckets")
    if not any(row["exit_reason"] in {"entry_drawdown_stop", "peak_drawdown_stop"} for row in specs):
        errors.append("collapse guard must create at least one drawdown exit")
    if not any(row["exit_reason"] == "reentry_cooling_block" for row in specs):
        errors.append("collapse guard must create at least one reentry cooling block")
    if any(row["exit_uses_post_entry_price_path"] != "1" for row in specs):
        errors.append("L5 specs must disclose post-entry exit path use")

    metric = metrics[0] if metrics else {}
    if metric.get("policy_variant_id") != "collapse_guard_slot5_v1":
        errors.append("metric policy variant mismatch")
    if metric.get("beats_base_slot5") != "0":
        errors.append("current collapse guard should not be marked as beating base slot5")
    if metric.get("beats_benchmark") != "0":
        errors.append("current collapse guard should not be marked as beating QQQ")
    if float(metric.get("max_drawdown", "0")) > -0.30:
        errors.append("MDD target must not be treated as passed")
    for table_name, table in [("metrics", metrics), ("gate", gate), ("closeout", closeout)]:
        for row in table:
            if row["strategy_acceptance"] != "NOT_ACCEPTED":
                errors.append(f"{table_name} changed strategy acceptance")
            if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{table_name} changed deployment readiness")
            if row["real_capital"] != "FORBIDDEN":
                errors.append(f"{table_name} changed real capital")
    if closeout_json.get("replay_executed") != "1":
        errors.append("json closeout must record diagnostic replay executed")
    if closeout_json.get("selection_promoted") != "0":
        errors.append("json closeout must keep selection promotion off")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1221_1227_COLLAPSE_GUARD_IMPLEMENTATION_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1221_1227_COLLAPSE_GUARD_IMPLEMENTATION_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
