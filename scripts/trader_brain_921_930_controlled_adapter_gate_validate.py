from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
PREV = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"

REQUIRED_FILES = [
    "task921_adapter_eligibility_ledger.csv",
    "task922_symbol_resolved_adapter_rows.csv",
    "task923_side_policy_ledger.csv",
    "task924_entry_tradable_after_policy.csv",
    "task925_exit_invalidation_policy.csv",
    "task926_position_sizing_policy.csv",
    "task927_market_data_manifest_gate.csv",
    "task928_cost_slippage_benchmark_config.csv",
    "task929_controlled_trade_specs.csv",
    "task930_first_controlled_replay_gate.csv",
    "task921_930_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_EXECUTION_COLUMNS = {"entry_price", "exit_price", "shares", "final_capital", "return_pct", "pnl", "future_return", "realized_return", "score", "rank"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    adapter_inputs = rows(PREV / "task920_adapter_input_design_rows.csv")
    eligibility = rows(ART / "task921_adapter_eligibility_ledger.csv")
    symbol_resolved = rows(ART / "task922_symbol_resolved_adapter_rows.csv")
    side = rows(ART / "task923_side_policy_ledger.csv")
    entry = rows(ART / "task924_entry_tradable_after_policy.csv")
    exit_policy = rows(ART / "task925_exit_invalidation_policy.csv")
    position = rows(ART / "task926_position_sizing_policy.csv")
    market = rows(ART / "task927_market_data_manifest_gate.csv")
    cost = rows(ART / "task928_cost_slippage_benchmark_config.csv")
    specs = rows(ART / "task929_controlled_trade_specs.csv")
    gate = rows(ART / "task930_first_controlled_replay_gate.csv")
    summary = json.loads((ART / "task921_930_summary.json").read_text(encoding="utf-8"))

    panels = {
        "eligibility": eligibility,
        "symbol_resolved": symbol_resolved,
        "side": side,
        "entry": entry,
        "exit": exit_policy,
        "position": position,
        "market": market,
        "cost": cost,
        "specs": specs,
        "gate": gate,
    }
    for name, panel in panels.items():
        if not panel:
            errors.append(f"{name} panel empty")
        forbidden = FORBIDDEN_EXECUTION_COLUMNS & set(panel[0].keys())
        if forbidden:
            errors.append(f"{name} panel contains forbidden execution/result columns: {sorted(forbidden)}")

    if len(eligibility) != len(adapter_inputs):
        errors.append("eligibility ledger must cover every Task920 adapter input")
    if len(symbol_resolved) != len(adapter_inputs):
        errors.append("symbol resolver ledger must cover every Task920 adapter input")
    if len(side) != len(adapter_inputs) or len(entry) != len(adapter_inputs) or len(exit_policy) != len(adapter_inputs) or len(position) != len(adapter_inputs):
        errors.append("policy ledgers must cover every Task920 adapter input")

    adapter_ids = {row["adapter_input_id"] for row in adapter_inputs}
    eligible_ids = {row["adapter_input_id"] for row in eligibility if row["eligibility_state"] == "eligible_controlled_adapter_candidate"}
    blocked_ids = {row["adapter_input_id"] for row in eligibility if row["eligibility_state"] != "eligible_controlled_adapter_candidate"}
    if not eligible_ids:
        errors.append("there must be at least one eligible controlled adapter candidate")
    if not blocked_ids:
        errors.append("there must be blocked adapter rows to prove the gate is active")
    if any(row["adapter_input_id"] not in adapter_ids for row in eligibility):
        errors.append("eligibility row references unknown adapter input")

    for row in eligibility:
        if row["eligibility_state"] == "eligible_controlled_adapter_candidate":
            if not row["symbol"] or row["has_symbol"] != "1" or row["symbol_in_universe"] != "1":
                errors.append("eligible row must have symbol in universe")
                break
            if row["contradiction_state"] != "no_direct_contradiction":
                errors.append("eligible row must have no direct contradiction")
                break
            if int(row["unresolved_source_gap_count"]) > 2:
                errors.append("eligible row exceeds source gap budget")
                break
        elif not row["blocked_reason"]:
            errors.append("blocked eligibility row must state a reason")
            break

    side_by_id = {row["adapter_input_id"]: row for row in side}
    entry_by_id = {row["adapter_input_id"]: row for row in entry}
    exit_by_id = {row["adapter_input_id"]: row for row in exit_policy}
    position_by_id = {row["adapter_input_id"]: row for row in position}
    market_by_symbol = {row["symbol"]: row for row in market}

    if {row["side"] for row in side} - {"long", "skip"}:
        errors.append("side policy may only produce long or skip")
    if any(row["short_allowed"] != "0" for row in side):
        errors.append("short must remain disallowed")

    for adapter_id in eligible_ids:
        if side_by_id[adapter_id]["side"] != "long":
            errors.append("eligible adapter must receive long side")
            break
        if not entry_by_id[adapter_id]["tradable_after_ts"] or not entry_by_id[adapter_id]["entry_rule"]:
            errors.append("eligible adapter missing tradable-after or entry rule")
            break
        if parse_ts(entry_by_id[adapter_id]["tradable_after_ts"]) <= parse_ts(next(row["decision_asof_ts"] for row in eligibility if row["adapter_input_id"] == adapter_id)):
            errors.append("tradable-after must be after decision asof")
            break
        if not exit_by_id[adapter_id]["planned_exit_not_after_ts"] or not exit_by_id[adapter_id]["exit_rule"]:
            errors.append("eligible adapter missing exit rule")
            break
        if not position_by_id[adapter_id]["position_size_rule"] or float(position_by_id[adapter_id]["allocated_capital"]) <= 0:
            errors.append("eligible adapter missing positive position allocation")
            break

    if len(cost) != 1:
        errors.append("there must be one frozen cost/slippage/benchmark config")
    else:
        cfg = cost[0]
        if cfg["initial_capital"] != "1000.00" or cfg["benchmark_symbol"] != "QQQ" or cfg["split_oos_required"] != "1":
            errors.append("cost config must freeze 1000 initial capital, QQQ benchmark, and split/OOS requirement")

    if len(market) != 71:
        errors.append("market manifest must cover 70 universe symbols plus QQQ")
    if any(row["gate_status"] != "ready_for_controlled_replay_plan" for row in market):
        errors.append("all Task927 market rows should be ready from Task880 manifest for this gate")

    spec_adapter_ids = {row["adapter_input_id"] for row in specs}
    if spec_adapter_ids != eligible_ids:
        errors.append("trade specs must be generated exactly for eligible adapter rows")
    for row in specs:
        if row["side"] != "long":
            errors.append("trade specs must be long-only")
            break
        if row["trade_spec_state"] != "ready_for_controlled_replay_plan":
            errors.append("trade specs should be ready for controlled replay plan or absent")
            break
        if row["symbol"] not in market_by_symbol:
            errors.append("trade spec symbol missing from market manifest")
            break
        if row["market_data_manifest_id"] != "task880_theme_universe_10x7_daily_adjusted_manifest_v1":
            errors.append("trade spec uses unexpected market data manifest")
            break
        if row["cost_config_id"] != cost[0]["cost_config_id"] or row["slippage_config_id"] != cost[0]["slippage_config_id"]:
            errors.append("trade spec config FK mismatch")
            break
        if row["benchmark_id"] != cost[0]["benchmark_id"]:
            errors.append("trade spec benchmark FK mismatch")
            break
        if parse_ts(row["tradable_after_ts"]) <= parse_ts(row["decision_asof_ts"]):
            errors.append("trade spec tradable-after precedes decision asof")
            break
        if not row["source_graph_id"] or not row["candidate_bundle_id"] or not row["trader_decision_id"]:
            errors.append("trade spec missing lineage ids")
            break

    if len(gate) != 1:
        errors.append("Task930 gate must have one row")
    else:
        row = gate[0]
        if row["diagnostic_replay_status"] != "not_run_trade_spec_gate_only":
            errors.append("Task930 must not claim replay execution")
        for field in ["price_lookup_count", "trade_execution_count", "pnl_count", "engine_call_count"]:
            if row[field] != "0":
                errors.append(f"Task930 {field} must be zero")
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("standing statuses changed")

    expected = {
        "input_adapter_rows": len(adapter_inputs),
        "eligible_adapter_rows": len(eligible_ids),
        "symbol_resolved_rows": sum(1 for row in symbol_resolved if row["resolver_state"] == "symbol_resolved"),
        "long_side_rows": sum(1 for row in side if row["side"] == "long"),
        "market_data_symbols": len(market),
        "market_data_ready_symbols": sum(1 for row in market if row["gate_status"] == "ready_for_controlled_replay_plan"),
        "trade_specs_total": len(specs),
        "trade_specs_ready": sum(1 for row in specs if row["trade_spec_state"] == "ready_for_controlled_replay_plan"),
        "price_lookup_count": 0,
        "trade_execution_count": 0,
        "pnl_count": 0,
        "engine_call_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"summary mismatch for {key}: {summary.get(key)} != {value}")

    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary strategy acceptance changed")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary deployment readiness changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary real capital changed")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_921_930_GATE_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_921_930_GATE_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
