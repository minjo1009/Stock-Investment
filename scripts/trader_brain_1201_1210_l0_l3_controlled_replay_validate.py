from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
REPORT = ROOT / "docs/reports/task_1201_1210_l0_l3_controlled_replay"

REQUIRED_FILES = [
    "task1201_preregistration_gate.csv",
    "task1202_l4_candidate_cards.csv",
    "task1203_l5_trade_specs.csv",
    "task1204_price_gate.csv",
    "task1205_slot_selections.csv",
    "task1206_replay_trades.csv",
    "task1206_replay_equity.csv",
    "task1207_replay_metrics.csv",
    "task1207_cost_sensitivity.csv",
    "task1208_failure_attribution.csv",
    "task1209_acceptance_gate.csv",
    "task1210_l0_l3_controlled_replay_closeout.csv",
    "task1210_l0_l3_controlled_replay_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require_columns(errors: list[str], name: str, table: list[dict[str, str]], required: set[str]) -> None:
    if not table:
        errors.append(f"{name} has no rows")
        return
    missing = required - set(table[0])
    if missing:
        errors.append(f"{name} missing columns: {sorted(missing)}")


def valid_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1201_1210_l0_l3_controlled_replay.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1201_1210_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    prereg = rows("task1201_preregistration_gate.csv")
    cards = rows("task1202_l4_candidate_cards.csv")
    specs = rows("task1203_l5_trade_specs.csv")
    price_gate = rows("task1204_price_gate.csv")
    selections = rows("task1205_slot_selections.csv")
    trades = rows("task1206_replay_trades.csv")
    equity = rows("task1206_replay_equity.csv")
    metrics = rows("task1207_replay_metrics.csv")
    cost_sensitivity = rows("task1207_cost_sensitivity.csv")
    attribution = rows("task1208_failure_attribution.csv")
    acceptance = rows("task1209_acceptance_gate.csv")
    closeout = rows("task1210_l0_l3_controlled_replay_closeout.csv")
    closeout_json = json.loads((ART / "task1210_l0_l3_controlled_replay_closeout.json").read_text(encoding="utf-8"))

    require_columns(
        errors,
        "cards",
        cards,
        {"l4_candidate_card_id", "decision_asof_ts", "symbol", "candidate_rank", "assignment_uses_future_outcome"},
    )
    require_columns(
        errors,
        "specs",
        specs,
        {"trade_spec_id", "l4_candidate_card_id", "entry_after_date", "exit_on_or_before_date", "symbol", "assignment_uses_future_outcome"},
    )
    require_columns(
        errors,
        "price_gate",
        price_gate,
        {"trade_spec_id", "entry_date", "entry_price", "exit_date", "exit_price", "price_gate_pass", "future_price_used_for_assignment"},
    )
    require_columns(
        errors,
        "selections",
        selections,
        {"policy_variant_id", "selection_id", "trade_spec_id", "decision_asof_ts", "symbol", "entry_price", "exit_price", "assignment_uses_future_outcome"},
    )
    require_columns(
        errors,
        "trades",
        trades,
        {"policy_variant_id", "trade_id", "trade_spec_id", "symbol", "derived_theme", "entry_date", "exit_date", "net_return", "round_trip_cost_bps"},
    )
    require_columns(
        errors,
        "metrics",
        metrics,
        {"policy_variant_id", "final_equity", "cagr", "max_drawdown", "benchmark_final_equity", "beats_benchmark"},
    )
    if errors:
        return errors

    if len(prereg) != 1 or prereg[0]["controlled_replay_authorized"] != "1":
        errors.append("controlled replay must be authorized by one Task1201 preregistration row")
    if len(cards) != 3150:
        errors.append("L4 cards must equal top50 candidates across 63 decision dates")
    if len(specs) != 3100:
        errors.append("L5 specs must exclude the final no-next-decision month")
    if len(price_gate) != len(specs):
        errors.append("price gate must cover every trade spec")
    if sum(1 for row in price_gate if row["price_gate_pass"] == "1") != len(specs):
        errors.append("all current Task1203 specs should pass the available price gate")
    if len(selections) != 1116:
        errors.append("slot selections must contain 1116 rows for slot 3 5 and 10")
    if len(trades) != len(selections):
        errors.append("replay trades must match slot selections")
    if len(equity) != 186:
        errors.append("equity panel must contain 62 decision periods for each of 3 variants")
    if len(metrics) != 3:
        errors.append("metrics must contain slot 3 5 and 10 variants")
    if len(cost_sensitivity) != 12:
        errors.append("cost sensitivity must contain 4 cost levels for 3 variants")
    if len(attribution) <= 0:
        errors.append("failure attribution must exist")
    if len(acceptance) != 1:
        errors.append("acceptance gate must have one row")
    if len(closeout) != 1:
        errors.append("closeout must have one row")

    future_fields = [
        ("cards", cards, "assignment_uses_future_outcome"),
        ("specs", specs, "assignment_uses_future_outcome"),
        ("price_gate", price_gate, "future_price_used_for_assignment"),
        ("selections", selections, "assignment_uses_future_outcome"),
    ]
    for name, table, field in future_fields:
        if any(row[field] != "0" for row in table):
            errors.append(f"{name} must not use future outcome for assignment")

    promoted = {row["selection_promoted"] for row in selections}
    if promoted != {"0"}:
        errors.append("slot selections must not be promoted")
    if any(not row["trade_spec_id"] or not row["derived_theme"] for row in trades):
        errors.append("trades must preserve trade_spec_id and derived_theme attribution")
    if len({row["trade_id"] for row in trades}) != len(trades):
        errors.append("trade_id must be unique")
    if len({row["selection_id"] for row in selections}) != len(selections):
        errors.append("selection_id must be unique")
    spec_ids = {row["trade_spec_id"] for row in specs}
    if any(row["trade_spec_id"] not in spec_ids for row in selections):
        errors.append("selection trade_spec_id must reference Task1203 specs")
    if any(row["trade_spec_id"] not in spec_ids for row in trades):
        errors.append("trade trade_spec_id must reference Task1203 specs")
    for row in price_gate:
        if row["price_gate_pass"] == "1":
            if not valid_float(row["entry_price"]) or not valid_float(row["exit_price"]):
                errors.append("passing price gate rows must have numeric prices")
                break
            if date.fromisoformat(row["entry_date"]) > date.fromisoformat(row["exit_date"]):
                errors.append("entry_date must be on or before exit_date")
                break
    if any(not valid_float(row["net_return"]) for row in trades):
        errors.append("trade net_return must be numeric")

    metric_by_variant = {row["policy_variant_id"]: row for row in metrics}
    expected_variants = {"l0_l3_slot3_v1", "l0_l3_slot5_v1", "l0_l3_slot10_v1"}
    if set(metric_by_variant) != expected_variants:
        errors.append("metrics variants mismatch")
    if metric_by_variant:
        best = max(metrics, key=lambda row: float(row["final_equity"]))
        if best["policy_variant_id"] != "l0_l3_slot5_v1":
            errors.append("current diagnostic best variant should be slot5")
        if float(best["benchmark_final_equity"]) <= 0:
            errors.append("benchmark final equity must be positive")
        if best["beats_benchmark"] != "1":
            errors.append("best variant should beat QQQ in current diagnostic replay")

    gate = acceptance[0] if acceptance else {}
    if gate.get("target_cagr_30pct_pass") != "0":
        errors.append("30pct CAGR target must not be marked as passed")
    if gate.get("target_mdd_minus30pct_pass") != "0":
        errors.append("-30pct MDD target must not be marked as passed")
    for table_name, table in [("metrics", metrics), ("cost_sensitivity", cost_sensitivity), ("acceptance", acceptance), ("closeout", closeout)]:
        for row in table:
            if row["strategy_acceptance"] != "NOT_ACCEPTED":
                errors.append(f"{table_name} changed strategy acceptance")
            if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{table_name} changed deployment readiness")
            if row["real_capital"] != "FORBIDDEN":
                errors.append(f"{table_name} changed real capital")

    if closeout_json.get("diagnostic_replay_executed") != "1":
        errors.append("json closeout must record diagnostic replay executed")
    if closeout_json.get("selection_promoted") != "0":
        errors.append("json closeout must keep selection promotion off")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1201_1210_L0_L3_CONTROLLED_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1201_1210_L0_L3_CONTROLLED_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
