from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
OUT_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"

INITIAL_CAPITAL = 1000.0
PERIOD_START = "2021-01-01"
PERIOD_END = "2026-03-31"
BENCHMARK_ID = "qqq_buy_hold_2021_2026q1_reference"
MARKET_DATA_MANIFEST_ID = "task880_theme_universe_10x7_daily_adjusted_manifest_v1"
CALENDAR_ID = "data_derived_qqq_sessions_v1"
ENTRY_RULE = "next_nasdaq_session_daily_adjusted_close_after_decision_asof_v1"
EXIT_RULE = "max_21_sessions_or_l4_invalidation_or_split_end_v1"
POSITION_RULE = "equal_weight_per_decision_cohort_cap_5pct_initial_capital_v1"
COST_CONFIG_ID = "task928_cost_config_zero_commission_10bps_round_trip_v1"
SLIPPAGE_CONFIG_ID = "task928_slippage_config_5bps_each_side_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def session_after(decision_asof_ts: str, sessions: list[str]) -> str:
    decision_date = parse_ts(decision_asof_ts).date().isoformat()
    for session in sessions:
        if session > decision_date:
            return session
    return ""


def session_offset(start_session: str, sessions: list[str], offset: int, split_id: str) -> str:
    split_end = {
        "development_2021_2024": "2024-12-31",
        "oos_1_2025": "2025-12-31",
        "oos_2_2026_q1": PERIOD_END,
    }.get(split_id, PERIOD_END)
    allowed = [session for session in sessions if start_session <= session <= split_end and session <= PERIOD_END]
    if not allowed:
        return ""
    index = min(offset, len(allowed) - 1)
    return allowed[index]


def blocked(*reasons: str) -> str:
    return ";".join(reason for reason in reasons if reason)


def load_inputs() -> dict[str, object]:
    candidates = read_csv(IN_DIR / "task919_l4_candidate_bundles_contradiction.csv")
    adapters = read_csv(IN_DIR / "task920_adapter_input_design_rows.csv")
    universe_rows = read_csv(UNIVERSE_PATH)
    daily_manifest = read_csv(MARKET_DIR / "daily_canonical_manifest.csv")
    actions_manifest = read_csv(MARKET_DIR / "corporate_action_adjustment_manifest.csv")
    calendar_rows = read_csv(MARKET_DIR / "calendar" / "data_derived_qqq_sessions_v1.csv")
    gate_rows = read_csv(MARKET_DIR / "market_data_gate_promotion_result.csv")
    return {
        "candidates": candidates,
        "adapters": adapters,
        "universe_rows": universe_rows,
        "daily_manifest": daily_manifest,
        "actions_manifest": actions_manifest,
        "calendar_rows": calendar_rows,
        "gate_rows": gate_rows,
    }


def build() -> dict[str, object]:
    inputs = load_inputs()
    candidates = {row["candidate_bundle_id"]: row for row in inputs["candidates"]}  # type: ignore[index]
    adapters: list[dict[str, str]] = inputs["adapters"]  # type: ignore[assignment]
    universe_rows: list[dict[str, str]] = inputs["universe_rows"]  # type: ignore[assignment]
    daily_manifest_rows: list[dict[str, str]] = inputs["daily_manifest"]  # type: ignore[assignment]
    actions_manifest_rows: list[dict[str, str]] = inputs["actions_manifest"]  # type: ignore[assignment]
    calendar_rows: list[dict[str, str]] = inputs["calendar_rows"]  # type: ignore[assignment]
    gate_rows: list[dict[str, str]] = inputs["gate_rows"]  # type: ignore[assignment]

    universe_by_symbol = {row["symbol"].upper(): row for row in universe_rows}
    universe_symbols = set(universe_by_symbol)
    daily_by_symbol = {row["symbol"].upper(): row for row in daily_manifest_rows}
    actions_by_symbol = {row["symbol"].upper(): row for row in actions_manifest_rows}
    sessions = sorted(row["session_date"] for row in calendar_rows if PERIOD_START <= row["session_date"] <= PERIOD_END)
    market_gate_status = gate_rows[0]["market_data_gate_status"] if gate_rows else "missing"

    eligibility_rows: list[dict[str, object]] = []
    symbol_rows: list[dict[str, object]] = []
    side_rows: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    exit_rows: list[dict[str, object]] = []

    for adapter in adapters:
        candidate = candidates[adapter["candidate_bundle_id"]]
        symbol = adapter["symbol"].upper().strip()
        unresolved_gaps = [item for item in candidate["unresolved_source_gaps"].split(";") if item]
        reasons = []
        if not symbol:
            reasons.append("blocked_theme_level_no_symbol")
        if symbol and symbol not in universe_symbols:
            reasons.append("blocked_symbol_not_in_10x7_universe")
        if not adapter["source_graph_id"]:
            reasons.append("blocked_missing_source_graph_id")
        if not adapter["supporting_evidence_ids"]:
            reasons.append("blocked_missing_supporting_evidence")
        if candidate["contradiction_state"] != "no_direct_contradiction":
            reasons.append("blocked_l4_contradiction_present")
        if candidate["invalidation_relation_ids"]:
            reasons.append("blocked_l4_invalidation_relation_present")
        if len(unresolved_gaps) > 2:
            reasons.append("blocked_source_gap_budget_exceeded")

        eligible = not reasons
        eligibility_state = "eligible_controlled_adapter_candidate" if eligible else "blocked_before_adapter_policy"
        eligibility_rows.append(
            {
                "adapter_input_id": adapter["adapter_input_id"],
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "decision_asof_ts": adapter["decision_asof_ts"],
                "split_id": adapter["split_id"],
                "symbol": symbol,
                "theme": adapter["theme"],
                "has_symbol": "1" if symbol else "0",
                "symbol_in_universe": "1" if symbol in universe_symbols else "0",
                "has_source_graph_id": "1" if adapter["source_graph_id"] else "0",
                "has_supporting_evidence": "1" if adapter["supporting_evidence_ids"] else "0",
                "contradiction_state": candidate["contradiction_state"],
                "unresolved_source_gap_count": len(unresolved_gaps),
                "eligibility_state": eligibility_state,
                "blocked_reason": blocked(*reasons),
                "authority": "DIAGNOSTIC_ADAPTER_ELIGIBILITY_ONLY",
            }
        )

        symbol_state = "symbol_resolved" if symbol and symbol in universe_symbols else "blocked_symbol_resolution"
        symbol_rows.append(
            {
                "adapter_input_id": adapter["adapter_input_id"],
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "decision_asof_ts": adapter["decision_asof_ts"],
                "split_id": adapter["split_id"],
                "symbol": symbol,
                "theme": adapter["theme"],
                "role": universe_by_symbol.get(symbol, {}).get("role", ""),
                "resolver_state": symbol_state,
                "blocked_reason": "" if symbol_state == "symbol_resolved" else blocked("no_symbol" if not symbol else "", "symbol_not_in_universe" if symbol and symbol not in universe_symbols else ""),
                "authority": "DIAGNOSTIC_SYMBOL_RESOLUTION_ONLY",
            }
        )

        side = "long" if eligible else "skip"
        side_reason = "long_only_no_short_gate_and_no_l4_contradiction" if eligible else "skip_until_adapter_eligibility_passes"
        side_rows.append(
            {
                "adapter_input_id": adapter["adapter_input_id"],
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "decision_asof_ts": adapter["decision_asof_ts"],
                "symbol": symbol,
                "side": side,
                "side_policy_id": "long_only_skip_else_v1",
                "short_allowed": "0",
                "side_policy_reason": side_reason,
                "authority": "DIAGNOSTIC_SIDE_POLICY_ONLY",
            }
        )

        tradable_after = session_after(adapter["decision_asof_ts"], sessions) if symbol else ""
        entry_rows.append(
            {
                "adapter_input_id": adapter["adapter_input_id"],
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "decision_asof_ts": adapter["decision_asof_ts"],
                "symbol": symbol,
                "entry_rule": ENTRY_RULE if eligible else "",
                "tradable_after_ts": f"{tradable_after}T20:00:00Z" if eligible and tradable_after else "",
                "calendar_id": CALENDAR_ID if eligible else "",
                "entry_state": "entry_policy_assigned" if eligible and tradable_after else "blocked_no_entry_policy",
                "blocked_reason": "" if eligible and tradable_after else "not_eligible_or_no_future_session",
                "authority": "DIAGNOSTIC_ENTRY_POLICY_ONLY",
            }
        )

        planned_exit = session_offset(tradable_after, sessions, 21, adapter["split_id"]) if eligible and tradable_after else ""
        exit_rows.append(
            {
                "adapter_input_id": adapter["adapter_input_id"],
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "symbol": symbol,
                "exit_rule": EXIT_RULE if eligible else "",
                "planned_exit_not_after_ts": f"{planned_exit}T20:00:00Z" if planned_exit else "",
                "invalidation_conditions": candidate["invalidation_conditions"] if eligible else "",
                "exit_state": "exit_policy_assigned" if eligible and planned_exit else "blocked_no_exit_policy",
                "blocked_reason": "" if eligible and planned_exit else "not_eligible_or_no_exit_session",
                "authority": "DIAGNOSTIC_EXIT_POLICY_ONLY",
            }
        )

    eligible_ids = {row["adapter_input_id"] for row in eligibility_rows if row["eligibility_state"] == "eligible_controlled_adapter_candidate"}
    by_decision: dict[str, list[str]] = defaultdict(list)
    for row in side_rows:
        if row["adapter_input_id"] in eligible_ids and row["side"] == "long":
            by_decision[str(row["decision_asof_ts"])].append(str(row["adapter_input_id"]))

    position_rows: list[dict[str, object]] = []
    for row in side_rows:
        decision_asof = str(row["decision_asof_ts"])
        cohort_size = len(by_decision.get(decision_asof, []))
        if row["adapter_input_id"] in eligible_ids and cohort_size:
            allocation = min(INITIAL_CAPITAL * 0.05, INITIAL_CAPITAL / cohort_size)
            state = "position_policy_assigned"
            reason = ""
        else:
            allocation = 0.0
            state = "blocked_no_position_policy"
            reason = "not_long_eligible"
        position_rows.append(
            {
                "adapter_input_id": row["adapter_input_id"],
                "candidate_bundle_id": row["candidate_bundle_id"],
                "decision_asof_ts": decision_asof,
                "symbol": row["symbol"],
                "position_size_rule": POSITION_RULE if state == "position_policy_assigned" else "",
                "decision_cohort_long_count": cohort_size,
                "allocated_capital": f"{allocation:.6f}",
                "initial_capital": f"{INITIAL_CAPITAL:.2f}",
                "max_single_name_cap_pct": "5.00",
                "position_state": state,
                "blocked_reason": reason,
                "authority": "DIAGNOSTIC_POSITION_POLICY_ONLY",
            }
        )

    market_rows: list[dict[str, object]] = []
    for symbol in sorted(universe_symbols | {"QQQ"}):
        daily = daily_by_symbol.get(symbol, {})
        actions = actions_by_symbol.get(symbol, {})
        ready = (
            market_gate_status == "READY_FOR_THEME_UNIVERSE_CONTROLLED_REPLAY_PLAN"
            and daily.get("canonical_status") == "ok"
            and actions.get("actions_status") == "ok"
            and daily.get("date_end", "") >= PERIOD_END
        )
        market_rows.append(
            {
                "market_data_manifest_id": MARKET_DATA_MANIFEST_ID,
                "symbol": symbol,
                "daily_status": daily.get("canonical_status", "missing"),
                "daily_date_start": daily.get("date_start", ""),
                "daily_date_end": daily.get("date_end", ""),
                "daily_path": daily.get("path", ""),
                "daily_sha256": daily.get("sha256", ""),
                "corporate_actions_status": actions.get("actions_status", "missing"),
                "calendar_id": CALENDAR_ID,
                "gate_status": "ready_for_controlled_replay_plan" if ready else "blocked_market_data_manifest",
                "blocked_reason": "" if ready else "missing_or_incomplete_market_data_manifest",
                "authority": "DIAGNOSTIC_MARKET_DATA_MANIFEST_ONLY",
            }
        )
    market_by_symbol = {row["symbol"]: row for row in market_rows}

    cost_rows = [
        {
            "cost_config_id": COST_CONFIG_ID,
            "slippage_config_id": SLIPPAGE_CONFIG_ID,
            "benchmark_id": BENCHMARK_ID,
            "initial_capital": f"{INITIAL_CAPITAL:.2f}",
            "commission_model": "zero_commission_diagnostic",
            "round_trip_cost_bps": "10",
            "slippage_each_side_bps": "5",
            "benchmark_symbol": "QQQ",
            "benchmark_rule": "buy_and_hold_same_replay_window",
            "split_oos_required": "1",
            "authority": "DIAGNOSTIC_REPLAY_CONFIG_ONLY",
        }
    ]

    entry_by_id = {row["adapter_input_id"]: row for row in entry_rows}
    exit_by_id = {row["adapter_input_id"]: row for row in exit_rows}
    pos_by_id = {row["adapter_input_id"]: row for row in position_rows}
    side_by_id = {row["adapter_input_id"]: row for row in side_rows}
    adapter_by_id = {row["adapter_input_id"]: row for row in adapters}

    trade_specs: list[dict[str, object]] = []
    for adapter_id in sorted(eligible_ids):
        adapter = adapter_by_id[adapter_id]
        symbol = adapter["symbol"].upper().strip()
        entry = entry_by_id[adapter_id]
        exit_policy = exit_by_id[adapter_id]
        position = pos_by_id[adapter_id]
        side = side_by_id[adapter_id]
        market = market_by_symbol.get(symbol, {})
        tradable_date = str(entry["tradable_after_ts"])[:10]
        daily_start = str(market.get("daily_date_start", ""))
        daily_end = str(market.get("daily_date_end", ""))
        reasons = []
        if market.get("gate_status") != "ready_for_controlled_replay_plan":
            reasons.append("market_data_not_ready")
        if not tradable_date or tradable_date < daily_start:
            reasons.append("tradable_after_before_symbol_daily_start")
        if tradable_date > PERIOD_END or daily_end < PERIOD_END:
            reasons.append("outside_replay_period_or_manifest_end")
        if not entry["tradable_after_ts"] or not exit_policy["planned_exit_not_after_ts"]:
            reasons.append("entry_or_exit_policy_missing")
        if float(position["allocated_capital"]) <= 0:
            reasons.append("allocated_capital_missing")
        ready = not reasons
        trade_specs.append(
            {
                "trade_spec_id": f"TS929-{len(trade_specs)+1:07d}",
                "adapter_input_id": adapter_id,
                "candidate_bundle_id": adapter["candidate_bundle_id"],
                "trader_decision_id": adapter["trader_decision_id"],
                "source_graph_id": adapter["source_graph_id"],
                "decision_asof_ts": adapter["decision_asof_ts"],
                "split_id": adapter["split_id"],
                "theme": adapter["theme"],
                "symbol": symbol,
                "side": side["side"],
                "tradable_after_ts": entry["tradable_after_ts"],
                "planned_exit_not_after_ts": exit_policy["planned_exit_not_after_ts"],
                "entry_rule": entry["entry_rule"],
                "exit_rule": exit_policy["exit_rule"],
                "position_size_rule": position["position_size_rule"],
                "allocated_capital": position["allocated_capital"],
                "initial_capital": f"{INITIAL_CAPITAL:.2f}",
                "market_data_manifest_id": MARKET_DATA_MANIFEST_ID,
                "cost_config_id": COST_CONFIG_ID,
                "slippage_config_id": SLIPPAGE_CONFIG_ID,
                "benchmark_id": BENCHMARK_ID,
                "trade_spec_state": "ready_for_controlled_replay_plan" if ready else "blocked_before_replay",
                "blocked_reason": blocked(*reasons),
                "validation_authority": "DIAGNOSTIC_CONTROLLED_REPLAY_PLAN_ONLY",
            }
        )

    ready_specs = [row for row in trade_specs if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    blocked_specs = [row for row in trade_specs if row["trade_spec_state"] != "ready_for_controlled_replay_plan"]
    go_status = "go_for_first_controlled_replay_execution_next" if ready_specs else "no_go_no_ready_trade_specs"
    gate_rows_930 = [
        {
            "gate_id": "Task930",
            "controlled_replay_gate_status": go_status,
            "period_start": PERIOD_START,
            "period_end": PERIOD_END,
            "initial_capital": f"{INITIAL_CAPITAL:.2f}",
            "benchmark_id": BENCHMARK_ID,
            "eligible_adapter_rows": len(eligible_ids),
            "trade_specs_total": len(trade_specs),
            "trade_specs_ready": len(ready_specs),
            "trade_specs_blocked": len(blocked_specs),
            "price_lookup_count": 0,
            "trade_execution_count": 0,
            "pnl_count": 0,
            "engine_call_count": 0,
            "diagnostic_replay_status": "not_run_trade_spec_gate_only",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "run controlled replay only after owner accepts Task930 gate and audit packet",
            "authority": "DIAGNOSTIC_CONTROLLED_REPLAY_GATE_ONLY",
        }
    ]

    write_csv(
        OUT_DIR / "task921_adapter_eligibility_ledger.csv",
        eligibility_rows,
        [
            "adapter_input_id",
            "candidate_bundle_id",
            "decision_asof_ts",
            "split_id",
            "symbol",
            "theme",
            "has_symbol",
            "symbol_in_universe",
            "has_source_graph_id",
            "has_supporting_evidence",
            "contradiction_state",
            "unresolved_source_gap_count",
            "eligibility_state",
            "blocked_reason",
            "authority",
        ],
    )
    write_csv(
        OUT_DIR / "task922_symbol_resolved_adapter_rows.csv",
        symbol_rows,
        ["adapter_input_id", "candidate_bundle_id", "decision_asof_ts", "split_id", "symbol", "theme", "role", "resolver_state", "blocked_reason", "authority"],
    )
    write_csv(
        OUT_DIR / "task923_side_policy_ledger.csv",
        side_rows,
        ["adapter_input_id", "candidate_bundle_id", "decision_asof_ts", "symbol", "side", "side_policy_id", "short_allowed", "side_policy_reason", "authority"],
    )
    write_csv(
        OUT_DIR / "task924_entry_tradable_after_policy.csv",
        entry_rows,
        ["adapter_input_id", "candidate_bundle_id", "decision_asof_ts", "symbol", "entry_rule", "tradable_after_ts", "calendar_id", "entry_state", "blocked_reason", "authority"],
    )
    write_csv(
        OUT_DIR / "task925_exit_invalidation_policy.csv",
        exit_rows,
        ["adapter_input_id", "candidate_bundle_id", "symbol", "exit_rule", "planned_exit_not_after_ts", "invalidation_conditions", "exit_state", "blocked_reason", "authority"],
    )
    write_csv(
        OUT_DIR / "task926_position_sizing_policy.csv",
        position_rows,
        [
            "adapter_input_id",
            "candidate_bundle_id",
            "decision_asof_ts",
            "symbol",
            "position_size_rule",
            "decision_cohort_long_count",
            "allocated_capital",
            "initial_capital",
            "max_single_name_cap_pct",
            "position_state",
            "blocked_reason",
            "authority",
        ],
    )
    write_csv(
        OUT_DIR / "task927_market_data_manifest_gate.csv",
        market_rows,
        [
            "market_data_manifest_id",
            "symbol",
            "daily_status",
            "daily_date_start",
            "daily_date_end",
            "daily_path",
            "daily_sha256",
            "corporate_actions_status",
            "calendar_id",
            "gate_status",
            "blocked_reason",
            "authority",
        ],
    )
    write_csv(
        OUT_DIR / "task928_cost_slippage_benchmark_config.csv",
        cost_rows,
        [
            "cost_config_id",
            "slippage_config_id",
            "benchmark_id",
            "initial_capital",
            "commission_model",
            "round_trip_cost_bps",
            "slippage_each_side_bps",
            "benchmark_symbol",
            "benchmark_rule",
            "split_oos_required",
            "authority",
        ],
    )
    write_csv(
        OUT_DIR / "task929_controlled_trade_specs.csv",
        trade_specs,
        [
            "trade_spec_id",
            "adapter_input_id",
            "candidate_bundle_id",
            "trader_decision_id",
            "source_graph_id",
            "decision_asof_ts",
            "split_id",
            "theme",
            "symbol",
            "side",
            "tradable_after_ts",
            "planned_exit_not_after_ts",
            "entry_rule",
            "exit_rule",
            "position_size_rule",
            "allocated_capital",
            "initial_capital",
            "market_data_manifest_id",
            "cost_config_id",
            "slippage_config_id",
            "benchmark_id",
            "trade_spec_state",
            "blocked_reason",
            "validation_authority",
        ],
    )
    write_csv(
        OUT_DIR / "task930_first_controlled_replay_gate.csv",
        gate_rows_930,
        [
            "gate_id",
            "controlled_replay_gate_status",
            "period_start",
            "period_end",
            "initial_capital",
            "benchmark_id",
            "eligible_adapter_rows",
            "trade_specs_total",
            "trade_specs_ready",
            "trade_specs_blocked",
            "price_lookup_count",
            "trade_execution_count",
            "pnl_count",
            "engine_call_count",
            "diagnostic_replay_status",
            "strategy_acceptance",
            "deployment_readiness",
            "real_capital",
            "next_action",
            "authority",
        ],
    )

    summary = {
        "task_id": "Task921-930",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "DIAGNOSTIC_CONTROLLED_REPLAY_GATE_ONLY",
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": INITIAL_CAPITAL,
        "input_adapter_rows": len(adapters),
        "eligible_adapter_rows": len(eligible_ids),
        "symbol_resolved_rows": sum(1 for row in symbol_rows if row["resolver_state"] == "symbol_resolved"),
        "long_side_rows": sum(1 for row in side_rows if row["side"] == "long"),
        "market_data_symbols": len(market_rows),
        "market_data_ready_symbols": sum(1 for row in market_rows if row["gate_status"] == "ready_for_controlled_replay_plan"),
        "trade_specs_total": len(trade_specs),
        "trade_specs_ready": len(ready_specs),
        "trade_specs_blocked": len(blocked_specs),
        "controlled_replay_gate_status": go_status,
        "diagnostic_replay_status": "not_run_trade_spec_gate_only",
        "price_lookup_count": 0,
        "trade_execution_count": 0,
        "pnl_count": 0,
        "engine_call_count": 0,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (OUT_DIR / "task921_930_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task921_930_summary.csv", [summary], list(summary.keys()))
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_921_930_GATE_OK] "
        f"input={summary['input_adapter_rows']} eligible={summary['eligible_adapter_rows']} "
        f"ready_specs={summary['trade_specs_ready']} blocked_specs={summary['trade_specs_blocked']} "
        f"gate={summary['controlled_replay_gate_status']}"
    )


if __name__ == "__main__":
    main()
