from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.trader_brain_941_950_slot_capped_selection_replay import (
    CALENDAR_PATH,
    ENTRY_FEE_BPS,
    ENTRY_SLIPPAGE_BPS,
    EXIT_FEE_BPS,
    EXIT_SLIPPAGE_BPS,
    INITIAL_CAPITAL,
    PERIOD_END,
    PERIOD_START,
    annualized_return,
    date_part,
    load_prices,
    max_drawdown,
)


SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
BASELINE_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
REDESIGN_DIR = ROOT / "data/artifacts/task_961_970_external_audit_redesign"
L5_DIR = ROOT / "data/artifacts/task_981_990_l5_payoff_layer"
OUT_DIR = ROOT / "data/artifacts/task_991_1000_l5_policy_replay"

SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
RANKING_PATH = REDESIGN_DIR / "task969_shadow_trader_ranking.csv"
BASELINE_TRADES_PATH = BASELINE_DIR / "task943_slot_capped_replay_trades.csv"
BASELINE_SUMMARY_PATH = BASELINE_DIR / "task946_slot_capped_summary.csv"

POLICY_ID = "slot10_l5_payoff_trader_rank_v1"
SLOT_CAP = 10
AUTHORITY = "DIAGNOSTIC_L5_POLICY_REPLAY_ONLY"
FORBIDDEN_OUTCOME_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank exit_price"
ALLOWED_HARD_BLOCK_REASONS = "future_evidence;missing_required_lineage;source_backed_invalidation"

ACTION_POINTS = {"enter": 6, "monitor": 2, "wait": 0}
ACTION_PRIORITY = {"enter": 0, "monitor": 1, "wait": 2}
REFLECTEDNESS_POINTS = {
    "under_pressure_reset_proxy": 4,
    "positive_relative_motion_proxy": 3,
    "neutral_reflectedness_proxy": 1,
    "insufficient_history": 0,
    "highly_reflected_momentum_proxy": -4,
}
PAYOFF_POINTS = {
    "right_tail_contained_drawdown_proxy": 7,
    "right_tail_high_risk_proxy": 3,
    "linear_or_unclear_payoff_proxy": 1,
    "insufficient_history": 0,
    "left_tail_or_broken_trend_proxy": -5,
}
TIMING_POINTS = {
    "positive_motion_timing_proxy": 6,
    "pullback_after_positive_trend_proxy": 4,
    "neutral_timing_proxy": 1,
    "insufficient_history": 0,
    "possibly_extended_timing_proxy": -5,
}
EXPRESSION_POINTS = {
    "theme_leader_proxy": 8,
    "theme_alternative_proxy": 0,
}
LIQUIDITY_POINTS = {
    "liquid_proxy": 2,
    "thin_liquidity_review": -4,
}
RISK_POINTS = {
    "normal_review": 2,
    "crowded_theme_review": -5,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: str) -> float:
    if value in {"", None}:
        return 0.0
    return float(value)


def by_id(path: Path) -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(path)}


def load_l5_panels() -> dict[str, dict[str, dict[str, str]]]:
    return {
        "l5a": by_id(L5_DIR / "task983_l5a_reflectedness_panel.csv"),
        "l5b": by_id(L5_DIR / "task984_l5b_payoff_shape_panel.csv"),
        "l5c": by_id(L5_DIR / "task985_l5c_motion_timing_panel.csv"),
        "l5d": by_id(L5_DIR / "task986_l5d_best_expression_panel.csv"),
        "l5e": by_id(L5_DIR / "task987_l5e_portfolio_risk_budget_panel.csv"),
        "l5v": by_id(L5_DIR / "task988_l5v_validation_guard_panel.csv"),
    }


def score_row(row: dict[str, str], panels: dict[str, dict[str, dict[str, str]]]) -> dict[str, object]:
    trade_spec_id = row["trade_spec_id"]
    a = panels["l5a"][trade_spec_id]
    b = panels["l5b"][trade_spec_id]
    c = panels["l5c"][trade_spec_id]
    d = panels["l5d"][trade_spec_id]
    e = panels["l5e"][trade_spec_id]
    v = panels["l5v"][trade_spec_id]

    l4_points = int(row["shadow_rank_score"]) * 5
    action_points = ACTION_POINTS.get(row["trader_action"], -10)
    reflectedness_points = REFLECTEDNESS_POINTS.get(a["reflectedness_bucket"], 0)
    payoff_points = PAYOFF_POINTS.get(b["payoff_shape_bucket"], 0)
    timing_points = TIMING_POINTS.get(c["timing_state"], 0)
    expression_points = EXPRESSION_POINTS.get(d["best_expression_proxy_state"], 0)
    liquidity_points = LIQUIDITY_POINTS.get(d["liquidity_state"], 0)
    risk_points = RISK_POINTS.get(e["risk_budget_proxy_state"], 0)
    validation_points = 2 if v["feature_time_state"] == "pass" else -999

    total = (
        l4_points
        + action_points
        + reflectedness_points
        + payoff_points
        + timing_points
        + expression_points
        + liquidity_points
        + risk_points
        + validation_points
    )
    return {
        "l5_total_rank_score": total,
        "l4_shadow_points": l4_points,
        "l5_action_points": action_points,
        "l5_reflectedness_points": reflectedness_points,
        "l5_payoff_points": payoff_points,
        "l5_timing_points": timing_points,
        "l5_expression_points": expression_points,
        "l5_liquidity_points": liquidity_points,
        "l5_risk_points": risk_points,
        "l5_validation_points": validation_points,
        "reflectedness_bucket": a["reflectedness_bucket"],
        "payoff_shape_bucket": b["payoff_shape_bucket"],
        "timing_state": c["timing_state"],
        "best_expression_proxy_state": d["best_expression_proxy_state"],
        "liquidity_state": d["liquidity_state"],
        "risk_budget_proxy_state": e["risk_budget_proxy_state"],
        "feature_time_state": v["feature_time_state"],
        "ret_63d_prior": a["ret_63d_prior"],
        "relative_strength_vs_qqq_63d_prior": a["relative_strength_vs_qqq_63d_prior"],
        "avg_dollar_volume_20d_prior": d["avg_dollar_volume_20d_prior"],
    }


def policy_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        -int(row["l5_total_rank_score"]),
        ACTION_PRIORITY.get(str(row["trader_action"]), 99),
        -int(row["l5_payoff_points"]),
        -int(row["l5_timing_points"]),
        -int(row["l5_expression_points"]),
        -as_float(str(row["relative_strength_vs_qqq_63d_prior"])),
        -as_float(str(row["avg_dollar_volume_20d_prior"])),
        str(row["theme"]),
        str(row["symbol"]),
        str(row["trade_spec_id"]),
    )


def build_policy_selection(
    ranking_rows: list[dict[str, str]],
    panels: dict[str, dict[str, dict[str, str]]],
) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]]]:
    scored_rows: list[dict[str, object]] = []
    for row in ranking_rows:
        scored = score_row(row, panels)
        scored_rows.append(
            {
                **row,
                **scored,
                "policy_id": POLICY_ID,
                "policy_rule": "slot10_rank_by_l4_shadow_plus_l5_reflectedness_payoff_timing_expression_risk_validation",
                "forbidden_inputs": FORBIDDEN_OUTCOME_INPUTS,
                "authority": AUTHORITY,
            }
        )

    by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in scored_rows:
        by_entry[str(row["entry_date"])].append(row)

    ledger: list[dict[str, object]] = []
    selected_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry_date, group in sorted(by_entry.items()):
        eligible = [
            row for row in group
            if row["trader_action"] != "hard_block" and row["feature_time_state"] == "pass"
        ]
        blocked = [row for row in group if row not in eligible]
        ranked = sorted(eligible, key=policy_sort_key)
        selected_ids = {row["trade_spec_id"] for row in ranked[:SLOT_CAP]}
        for rank, row in enumerate(ranked, start=1):
            state = "selected" if row["trade_spec_id"] in selected_ids else "rejected_by_slot_cap"
            out = {
                **row,
                "selection_rank": rank,
                "selection_state": state,
                "blocked_reason": "" if state == "selected" else "slot_cap_filled_by_higher_l5_rank",
                "policy_sort_key": "|".join(str(item) for item in policy_sort_key(row)),
                "allowed_hard_block_reasons": ALLOWED_HARD_BLOCK_REASONS,
            }
            ledger.append(out)
            if state == "selected":
                selected_by_entry[entry_date].append(out)
        for row in blocked:
            ledger.append(
                {
                    **row,
                    "selection_rank": "",
                    "selection_state": "hard_blocked_or_failed_l5v",
                    "blocked_reason": "hard_block_action_or_l5v_feature_time_failure",
                    "policy_sort_key": "",
                    "allowed_hard_block_reasons": ALLOWED_HARD_BLOCK_REASONS,
                }
            )
    return ledger, selected_by_entry


def replay(
    specs_by_id: dict[str, dict[str, str]],
    selected_by_entry: dict[str, list[dict[str, object]]],
    prices: dict[str, dict[str, float]],
    calendar: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    skips: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    entry_decisions: list[dict[str, object]] = []

    for day in calendar:
        remaining: list[dict[str, object]] = []
        exits_closed = 0
        for position in open_positions:
            if position["planned_exit_date"] == day:
                symbol = str(position["symbol"])
                exit_ref = prices.get(symbol, {}).get(day)
                if exit_ref is None:
                    remaining.append(position)
                    continue
                exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
                gross_exit = float(position["shares"]) * exit_price
                exit_fee = gross_exit * (EXIT_FEE_BPS / 10000.0)
                net_exit = gross_exit - exit_fee
                cash += net_exit
                pnl = net_exit - float(position["entry_cash_spent"])
                trade = dict(position)
                trade.update(
                    {
                        "exit_date": day,
                        "exit_adj_close": f"{exit_ref:.6f}",
                        "exit_price_after_slippage": f"{exit_price:.6f}",
                        "exit_fee": f"{exit_fee:.6f}",
                        "net_exit_value": f"{net_exit:.6f}",
                        "pnl": f"{pnl:.6f}",
                        "return_pct": f"{((net_exit / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                        "fill_state": "closed",
                    }
                )
                trades.append(trade)
                exits_closed += 1
            else:
                remaining.append(position)
        open_positions = remaining

        available_slots = max(SLOT_CAP - len(open_positions), 0)
        policy_candidates = selected_by_entry.get(day, [])
        selected = policy_candidates[:available_slots]
        deferred = policy_candidates[available_slots:]
        for order, decision in enumerate(selected, start=1):
            entry_decisions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": decision["trade_spec_id"],
                    "entry_date": day,
                    "symbol": decision["symbol"],
                    "theme": decision["theme"],
                    "l5_total_rank_score": decision["l5_total_rank_score"],
                    "trader_action": decision["trader_action"],
                    "entry_decision_state": "entered",
                    "entry_order": order,
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "",
                    "authority": AUTHORITY,
                }
            )
        for decision in deferred:
            entry_decisions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": decision["trade_spec_id"],
                    "entry_date": day,
                    "symbol": decision["symbol"],
                    "theme": decision["theme"],
                    "l5_total_rank_score": decision["l5_total_rank_score"],
                    "trader_action": decision["trader_action"],
                    "entry_decision_state": "deferred_by_live_slot_cap",
                    "entry_order": "",
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "slot_cap_already_occupied_by_open_positions",
                    "authority": AUTHORITY,
                }
            )

        valid_orders: list[tuple[dict[str, str], dict[str, object], float, float]] = []
        for decision in selected:
            spec = specs_by_id[str(decision["trade_spec_id"])]
            symbol = spec["symbol"]
            entry_ref = prices.get(symbol, {}).get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_ref = prices.get(symbol, {}).get(exit_date)
            if entry_ref is None:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "missing_exact_entry_price", "authority": AUTHORITY})
                continue
            if exit_ref is None:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "missing_exact_planned_exit_price", "authority": AUTHORITY})
                continue
            entry_price = entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)
            valid_orders.append((spec, decision, entry_ref, entry_price))

        per_slot_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, decision, entry_ref, entry_price in valid_orders:
            entry_fee = per_slot_cash * (ENTRY_FEE_BPS / 10000.0)
            entry_notional = max(per_slot_cash - entry_fee, 0.0)
            entry_cash_spent = entry_notional + entry_fee
            if entry_cash_spent <= 0.000001:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "no_available_cash", "authority": AUTHORITY})
                continue
            shares = entry_notional / entry_price
            cash -= entry_cash_spent
            open_positions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": spec["trade_spec_id"],
                    "adapter_input_id": spec["adapter_input_id"],
                    "candidate_bundle_id": spec["candidate_bundle_id"],
                    "trader_decision_id": spec["trader_decision_id"],
                    "source_graph_id": spec["source_graph_id"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "split_id": spec["split_id"],
                    "theme": spec["theme"],
                    "symbol": spec["symbol"],
                    "side": spec["side"],
                    "l5_total_rank_score": decision["l5_total_rank_score"],
                    "trader_action": decision["trader_action"],
                    "reflectedness_bucket": decision["reflectedness_bucket"],
                    "payoff_shape_bucket": decision["payoff_shape_bucket"],
                    "timing_state": decision["timing_state"],
                    "best_expression_proxy_state": decision["best_expression_proxy_state"],
                    "risk_budget_proxy_state": decision["risk_budget_proxy_state"],
                    "entry_date": day,
                    "planned_exit_date": date_part(spec["planned_exit_not_after_ts"]),
                    "entry_adj_close": f"{entry_ref:.6f}",
                    "entry_price_after_slippage": f"{entry_price:.6f}",
                    "entry_notional": f"{entry_notional:.6f}",
                    "entry_fee": f"{entry_fee:.6f}",
                    "entry_cash_spent": f"{entry_cash_spent:.6f}",
                    "shares": f"{shares:.10f}",
                    "authority": AUTHORITY,
                }
            )

        market_value = 0.0
        for position in open_positions:
            px = prices.get(str(position["symbol"]), {}).get(day)
            if px is not None:
                market_value += float(position["shares"]) * px
        equity_rows.append(
            {
                "policy_id": POLICY_ID,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "entry_candidates": len(selected_by_entry.get(day, [])),
                "entries_selected": len(selected),
                "exits_closed": exits_closed,
                "authority": AUTHORITY,
            }
        )

    final_day = calendar[-1]
    forced_count = 0
    for position in list(open_positions):
        symbol = str(position["symbol"])
        exit_ref = prices.get(symbol, {}).get(final_day)
        if exit_ref is None:
            continue
        exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
        gross_exit = float(position["shares"]) * exit_price
        exit_fee = gross_exit * (EXIT_FEE_BPS / 10000.0)
        net_exit = gross_exit - exit_fee
        cash += net_exit
        pnl = net_exit - float(position["entry_cash_spent"])
        trade = dict(position)
        trade.update(
            {
                "exit_date": final_day,
                "exit_adj_close": f"{exit_ref:.6f}",
                "exit_price_after_slippage": f"{exit_price:.6f}",
                "exit_fee": f"{exit_fee:.6f}",
                "net_exit_value": f"{net_exit:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_pct": f"{((net_exit / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                "fill_state": "forced_closed_period_end",
            }
        )
        trades.append(trade)
        forced_count += 1
    open_positions.clear()
    if forced_count:
        equity_rows.append(
            {
                "policy_id": POLICY_ID,
                "date": final_day,
                "cash": f"{cash:.6f}",
                "open_market_value": "0.000000",
                "equity": f"{cash:.6f}",
                "open_positions": 0,
                "entry_candidates": 0,
                "entries_selected": 0,
                "exits_closed": forced_count,
                "authority": AUTHORITY,
            }
        )

    equity_values = [float(row["equity"]) for row in equity_rows]
    final_equity = equity_values[-1]
    qqq = prices["QQQ"]
    qqq_start = next(day for day in calendar if day in qqq)
    qqq_end = max(day for day in calendar if day in qqq)
    qqq_final = INITIAL_CAPITAL * qqq[qqq_end] / qqq[qqq_start]
    strategy_cagr = annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"]))
    strategy_mdd = max_drawdown(equity_values)
    summary = {
        "policy_id": POLICY_ID,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "slot_cap": SLOT_CAP,
        "policy_preselected_entries": sum(len(rows) for rows in selected_by_entry.values()),
        "selected_entries": sum(1 for row in entry_decisions if row["entry_decision_state"] == "entered"),
        "deferred_by_live_slot_cap": sum(1 for row in entry_decisions if row["entry_decision_state"] == "deferred_by_live_slot_cap"),
        "closed_trades": len(trades),
        "skipped_orders": len(skips),
        "forced_closed_period_end": forced_count,
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(strategy_cagr, 6),
        "strategy_max_drawdown_pct": round(strategy_mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "meets_cagr_30": "1" if strategy_cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if strategy_mdd >= -30.0 else "0",
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return entry_decisions, trades, skips, equity_rows, summary


def bucket_attribution_rows(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for field in [
        "payoff_shape_bucket",
        "timing_state",
        "best_expression_proxy_state",
        "risk_budget_proxy_state",
        "reflectedness_bucket",
    ]:
        groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            groups[str(trade[field])].append(trade)
        for bucket, bucket_trades in sorted(groups.items()):
            spent = sum(float(row["entry_cash_spent"]) for row in bucket_trades)
            pnl = sum(float(row["pnl"]) for row in bucket_trades)
            rows.append(
                {
                    "policy_id": POLICY_ID,
                    "evaluation_axis": field,
                    "bucket": bucket,
                    "closed_trades": len(bucket_trades),
                    "entry_cash_spent": f"{spent:.6f}",
                    "pnl": f"{pnl:.6f}",
                    "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                    "evaluation_use_mode": "post_replay_failure_decomposition_only_never_selection_input",
                    "authority": AUTHORITY,
                }
            )
    return rows


def tail_trade_rows(trades: list[dict[str, object]], count: int = 15) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    ordered_losers = sorted(trades, key=lambda row: float(row["pnl"]))[:count]
    ordered_winners = sorted(trades, key=lambda row: -float(row["pnl"]))[:count]
    for tail_name, tail_rows in [("largest_losers", ordered_losers), ("largest_winners", ordered_winners)]:
        for rank, row in enumerate(tail_rows, start=1):
            out.append(
                {
                    "policy_id": POLICY_ID,
                    "tail_group": tail_name,
                    "tail_rank": rank,
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "theme": row["theme"],
                    "entry_date": row["entry_date"],
                    "exit_date": row["exit_date"],
                    "pnl": row["pnl"],
                    "return_pct": row["return_pct"],
                    "l5_total_rank_score": row["l5_total_rank_score"],
                    "payoff_shape_bucket": row["payoff_shape_bucket"],
                    "timing_state": row["timing_state"],
                    "best_expression_proxy_state": row["best_expression_proxy_state"],
                    "risk_budget_proxy_state": row["risk_budget_proxy_state"],
                    "evaluation_use_mode": "post_replay_failure_decomposition_only_never_selection_input",
                    "authority": AUTHORITY,
                }
            )
    return out


def build() -> dict[str, object]:
    specs = [row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    ranking_rows = read_csv(RANKING_PATH)
    panels = load_l5_panels()
    selection_ledger, selected_by_entry = build_policy_selection(ranking_rows, panels)
    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})
    entry_decisions, trades, skips, equity, replay_summary = replay(specs_by_id, selected_by_entry, prices, calendar)

    baseline_summary = next(row for row in read_csv(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")
    baseline_trades = [row for row in read_csv(BASELINE_TRADES_PATH) if row["slot_cap"] == "10"]
    baseline_ids = {row["trade_spec_id"] for row in baseline_trades}
    replay_ids = {row["trade_spec_id"] for row in trades}

    policy = {
        "policy_id": POLICY_ID,
        "source_ranking_path": RANKING_PATH.relative_to(ROOT).as_posix(),
        "source_ranking_sha256": sha256(RANKING_PATH),
        "l5_source_dir": L5_DIR.relative_to(ROOT).as_posix(),
        "slot_cap": SLOT_CAP,
        "rank_rule": "l4_shadow_score_plus_l5_reflectedness_payoff_timing_expression_liquidity_risk_validation",
        "eligibility_rule": "exclude_only_trader_action_hard_block_or_l5v_feature_time_failure",
        "cost_slippage_rule": "Task941_same_5bps_entry_5bps_exit_10bps_round_trip",
        "forbidden_inputs": FORBIDDEN_OUTCOME_INPUTS,
        "pre_registered_before_replay": "1",
        "authority": AUTHORITY,
    }
    comparison = {
        "comparison_id": "task991_1000_l5_policy_vs_task941_slot10",
        "baseline_final_equity": baseline_summary["strategy_final_equity"],
        "baseline_cagr_pct": baseline_summary["strategy_cagr_pct"],
        "baseline_mdd_pct": baseline_summary["strategy_max_drawdown_pct"],
        "baseline_beats_qqq": baseline_summary["beats_qqq"],
        "l5_policy_final_equity": replay_summary["strategy_final_equity"],
        "l5_policy_cagr_pct": replay_summary["strategy_cagr_pct"],
        "l5_policy_mdd_pct": replay_summary["strategy_max_drawdown_pct"],
        "l5_policy_beats_qqq": replay_summary["beats_qqq"],
        "beats_task941_slot10": "1" if float(replay_summary["strategy_final_equity"]) > float(baseline_summary["strategy_final_equity"]) else "0",
        "baseline_trade_count": len(baseline_ids),
        "l5_policy_trade_count": len(replay_ids),
        "overlap_count": len(baseline_ids & replay_ids),
        "l5_only_count": len(replay_ids - baseline_ids),
        "baseline_only_count": len(baseline_ids - replay_ids),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }

    by_split_rows: list[dict[str, object]] = []
    for split in sorted({str(row["split_id"]) for row in trades}):
        split_rows = [row for row in trades if row["split_id"] == split]
        spent = sum(float(row["entry_cash_spent"]) for row in split_rows)
        pnl = sum(float(row["pnl"]) for row in split_rows)
        by_split_rows.append(
            {
                "policy_id": POLICY_ID,
                "split_id": split,
                "closed_trades": len(split_rows),
                "entry_cash_spent": f"{spent:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                "authority": AUTHORITY,
            }
        )

    bucket_rows = bucket_attribution_rows(trades)
    tail_rows = tail_trade_rows(trades)
    source_manifest = [
        {"source_name": "task969_shadow_trader_ranking", "path": RANKING_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(RANKING_PATH), "authority": AUTHORITY},
        {"source_name": "task929_controlled_trade_specs", "path": SPEC_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "task981_990_l5_source_context", "path": (L5_DIR / "task981_l5_source_context_manifest.csv").relative_to(ROOT).as_posix(), "sha256": sha256(L5_DIR / "task981_l5_source_context_manifest.csv"), "authority": AUTHORITY},
        {"source_name": "task982_l5_layer_contract", "path": (L5_DIR / "task982_l5_layer_contract.csv").relative_to(ROOT).as_posix(), "sha256": sha256(L5_DIR / "task982_l5_layer_contract.csv"), "authority": AUTHORITY},
        {"source_name": "task983_988_l5_feature_panels", "path": L5_DIR.relative_to(ROOT).as_posix(), "sha256": sha256(L5_DIR / "artifact_manifest.csv"), "authority": AUTHORITY},
        {"source_name": "task941_baseline_summary", "path": BASELINE_SUMMARY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_SUMMARY_PATH), "authority": AUTHORITY},
        {"source_name": "task941_baseline_trades", "path": BASELINE_TRADES_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_TRADES_PATH), "authority": AUTHORITY},
        {"source_name": "calendar", "path": CALENDAR_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(CALENDAR_PATH), "authority": AUTHORITY},
    ]
    closeout = {
        "gate_id": "Task1000",
        "policy_id": POLICY_ID,
        "verdict": "controlled_l5_policy_replay_executed_diagnostic_only",
        "beats_task941_slot10": comparison["beats_task941_slot10"],
        "beats_qqq": replay_summary["beats_qqq"],
        "meets_cagr_30": replay_summary["meets_cagr_30"],
        "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
        "next_action": "decompose_l5_policy_result_before_any_policy_change",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task991_l5_expert_policy_freeze.csv", [policy], list(policy.keys()))
    write_csv(OUT_DIR / "task992_pre_registered_l5_policy.csv", [policy], list(policy.keys()))
    selection_fields = [
        "policy_id", "trade_spec_id", "decision_asof_ts", "entry_date", "split_id", "symbol", "theme",
        "thesis_cluster_key", "shadow_rank_score", "trader_action", "action_reason",
        "l5_total_rank_score", "l4_shadow_points", "l5_action_points", "l5_reflectedness_points",
        "l5_payoff_points", "l5_timing_points", "l5_expression_points", "l5_liquidity_points",
        "l5_risk_points", "l5_validation_points", "reflectedness_bucket", "payoff_shape_bucket",
        "timing_state", "best_expression_proxy_state", "liquidity_state", "risk_budget_proxy_state",
        "feature_time_state", "ret_63d_prior", "relative_strength_vs_qqq_63d_prior",
        "avg_dollar_volume_20d_prior", "selection_rank", "selection_state", "blocked_reason",
        "policy_sort_key", "allowed_hard_block_reasons", "forbidden_inputs", "authority",
    ]
    write_csv(OUT_DIR / "task993_l5_policy_selection_ledger.csv", selection_ledger, selection_fields)
    write_csv(OUT_DIR / "task994_l5_replay_entry_decision_ledger.csv", entry_decisions, [
        "policy_id", "trade_spec_id", "entry_date", "symbol", "theme", "l5_total_rank_score",
        "trader_action", "entry_decision_state", "entry_order", "open_positions_before_entry",
        "available_slots", "blocked_reason", "authority",
    ])
    trade_fields = [
        "policy_id", "trade_spec_id", "adapter_input_id", "candidate_bundle_id", "trader_decision_id",
        "source_graph_id", "decision_asof_ts", "split_id", "theme", "symbol", "side",
        "l5_total_rank_score", "trader_action", "reflectedness_bucket", "payoff_shape_bucket",
        "timing_state", "best_expression_proxy_state", "risk_budget_proxy_state",
        "entry_date", "planned_exit_date", "entry_adj_close", "entry_price_after_slippage",
        "entry_notional", "entry_fee", "entry_cash_spent", "shares", "exit_date", "exit_adj_close",
        "exit_price_after_slippage", "exit_fee", "net_exit_value", "pnl", "return_pct",
        "fill_state", "authority",
    ]
    write_csv(OUT_DIR / "task995_l5_replay_trades.csv", trades, trade_fields)
    write_csv(OUT_DIR / "task996_l5_replay_equity.csv", equity, ["policy_id", "date", "cash", "open_market_value", "equity", "open_positions", "entry_candidates", "entries_selected", "exits_closed", "authority"])
    skip_fields = list(skips[0].keys()) if skips else ["policy_id", "trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task997_l5_skipped_orders.csv", skips, skip_fields)
    write_csv(OUT_DIR / "task998_l5_replay_summary.csv", [replay_summary], list(replay_summary.keys()))
    (OUT_DIR / "task998_l5_replay_summary.json").write_text(json.dumps(replay_summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task999_l5_replay_by_split.csv", by_split_rows, ["policy_id", "split_id", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "authority"])
    write_csv(OUT_DIR / "task999_l5_vs_task941_attribution.csv", [comparison], list(comparison.keys()))
    write_csv(OUT_DIR / "task999_l5_bucket_attribution_evaluation_only.csv", bucket_rows, ["policy_id", "evaluation_axis", "bucket", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "evaluation_use_mode", "authority"])
    write_csv(OUT_DIR / "task999_l5_tail_trades_evaluation_only.csv", tail_rows, ["policy_id", "tail_group", "tail_rank", "trade_spec_id", "symbol", "theme", "entry_date", "exit_date", "pnl", "return_pct", "l5_total_rank_score", "payoff_shape_bucket", "timing_state", "best_expression_proxy_state", "risk_budget_proxy_state", "evaluation_use_mode", "authority"])
    write_csv(OUT_DIR / "task1000_l5_policy_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    write_csv(OUT_DIR / "task1000_l5_policy_governance_closeout.csv", [closeout], list(closeout.keys()))

    summary = {
        "task_id": "Task991-1000",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_id": POLICY_ID,
        "authority": AUTHORITY,
        "input_ranking_rows": len(ranking_rows),
        "policy_selection_rows": len(selection_ledger),
        "policy_preselected_entries": replay_summary["policy_preselected_entries"],
        "selected_entries": replay_summary["selected_entries"],
        "closed_trades": replay_summary["closed_trades"],
        "strategy_final_equity": replay_summary["strategy_final_equity"],
        "strategy_cagr_pct": replay_summary["strategy_cagr_pct"],
        "strategy_max_drawdown_pct": replay_summary["strategy_max_drawdown_pct"],
        "beats_task941_slot10": comparison["beats_task941_slot10"],
        "beats_qqq": replay_summary["beats_qqq"],
        "meets_cagr_30": replay_summary["meets_cagr_30"],
        "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_csv(OUT_DIR / "task991_1000_summary.csv", [summary], list(summary.keys()))
    (OUT_DIR / "task991_1000_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_991_1000_L5_POLICY_REPLAY_OK] "
        f"equity={summary['strategy_final_equity']} cagr={summary['strategy_cagr_pct']} "
        f"mdd={summary['strategy_max_drawdown_pct']} beats_baseline={summary['beats_task941_slot10']} "
        f"beats_qqq={summary['beats_qqq']}"
    )


if __name__ == "__main__":
    main()
