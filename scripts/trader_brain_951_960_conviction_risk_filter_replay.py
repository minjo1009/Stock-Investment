from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREV_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
OUT_DIR = ROOT / "data/artifacts/task_951_960_conviction_risk_filter_replay"

TRADE_SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
FEATURE_PATH = PREV_DIR / "task941_selection_feature_panel.csv"
DAILY_DIR = MARKET_DIR / "canonical_daily"
CALENDAR_PATH = MARKET_DIR / "calendar" / "data_derived_qqq_sessions_v1.csv"

INITIAL_CAPITAL = 1000.0
PERIOD_START = "2021-01-01"
PERIOD_END = "2026-03-31"
ENTRY_SLIPPAGE_BPS = 5.0
EXIT_SLIPPAGE_BPS = 5.0
ROUND_TRIP_COST_BPS = 10.0
ENTRY_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
EXIT_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
AUTHORITY = "DIAGNOSTIC_CONVICTION_RISK_FILTER_REPLAY_ONLY"

POLICIES = [
    {
        "policy_id": "theme_cap4_slot10_v1",
        "base_slot_cap": 10,
        "theme_cap": 4,
        "qqq_hurdle": False,
        "symbol_positive_momentum": False,
        "regime_throttle": False,
        "drawdown_throttle": False,
    },
    {
        "policy_id": "momentum_rank_cash_slot10_v1",
        "base_slot_cap": 10,
        "theme_cap": 10,
        "qqq_hurdle": False,
        "symbol_positive_momentum": False,
        "regime_throttle": False,
        "drawdown_throttle": False,
    },
    {
        "policy_id": "cash_qqq_hurdle_slot10_v1",
        "base_slot_cap": 10,
        "theme_cap": 10,
        "qqq_hurdle": True,
        "symbol_positive_momentum": True,
        "regime_throttle": False,
        "drawdown_throttle": False,
    },
    {
        "policy_id": "regime_theme_slot10_v1",
        "base_slot_cap": 10,
        "theme_cap": 2,
        "qqq_hurdle": True,
        "symbol_positive_momentum": True,
        "regime_throttle": True,
        "drawdown_throttle": False,
    },
    {
        "policy_id": "trader_veto_slot10_v1",
        "base_slot_cap": 10,
        "theme_cap": 2,
        "qqq_hurdle": True,
        "symbol_positive_momentum": True,
        "regime_throttle": True,
        "drawdown_throttle": True,
    },
]


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


def date_part(ts: str) -> str:
    return ts[:10]


def load_prices(symbols: set[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for symbol in sorted(symbols):
        path = DAILY_DIR / f"{symbol}.csv"
        prices: dict[str, float] = {}
        if path.exists():
            for row in read_csv(path):
                day = row["timestamp"]
                if PERIOD_START <= day <= PERIOD_END:
                    prices[day] = float(row["adj_close"])
        out[symbol] = prices
    return out


def max_drawdown(equity_values: list[float]) -> float:
    peak = -math.inf
    max_dd = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1.0)
    return max_dd * 100.0


def current_drawdown(equity_values: list[float]) -> float:
    if not equity_values:
        return 0.0
    peak = max(equity_values)
    if peak <= 0:
        return 0.0
    return (equity_values[-1] / peak - 1.0) * 100.0


def annualized_return(start_value: float, end_value: float, start_date: str, end_date: str) -> float:
    d0 = datetime.fromisoformat(start_date)
    d1 = datetime.fromisoformat(end_date)
    years = max((d1 - d0).days, 1) / 365.25
    return ((end_value / start_value) ** (1.0 / years) - 1.0) * 100.0


def prior_session(entry_date: str, sessions: list[str]) -> str:
    idx = sessions.index(entry_date)
    if idx <= 0:
        return ""
    return sessions[idx - 1]


def trailing_return(prices: dict[str, float], sessions: list[str], asof_date: str, lookback: int) -> float | None:
    if asof_date not in sessions:
        return None
    idx = sessions.index(asof_date)
    if idx - lookback < 0:
        return None
    start = sessions[idx - lookback]
    if start not in prices or asof_date not in prices or prices[start] <= 0:
        return None
    return (prices[asof_date] / prices[start]) - 1.0


def sma_gap(prices: dict[str, float], sessions: list[str], asof_date: str, lookback: int) -> float | None:
    if asof_date not in sessions:
        return None
    idx = sessions.index(asof_date)
    if idx - lookback + 1 < 0:
        return None
    window = [prices.get(day) for day in sessions[idx - lookback + 1 : idx + 1]]
    if any(value is None for value in window):
        return None
    avg = sum(float(value) for value in window) / lookback
    if avg <= 0:
        return None
    return (prices[asof_date] / avg) - 1.0


def regime_state(qqq_ret_63: float | None, qqq_sma_126_gap: float | None) -> str:
    if qqq_ret_63 is None or qqq_sma_126_gap is None:
        return "regime_unknown"
    if qqq_ret_63 > 0.03 and qqq_sma_126_gap > 0:
        return "risk_on"
    if qqq_ret_63 < -0.03 or qqq_sma_126_gap < -0.03:
        return "risk_off"
    return "neutral"


def build_enriched_features(features: list[dict[str, str]], prices: dict[str, dict[str, float]], sessions: list[str]) -> list[dict[str, object]]:
    qqq_prices = prices["QQQ"]
    out: list[dict[str, object]] = []
    for row in features:
        entry_date = row["entry_date"]
        asof_date = prior_session(entry_date, sessions) if entry_date in sessions else ""
        symbol = row["symbol"]
        sym_prices = prices.get(symbol, {})
        sym_ret_63 = trailing_return(sym_prices, sessions, asof_date, 63) if asof_date else None
        sym_ret_126 = trailing_return(sym_prices, sessions, asof_date, 126) if asof_date else None
        qqq_ret_63 = trailing_return(qqq_prices, sessions, asof_date, 63) if asof_date else None
        qqq_ret_126 = trailing_return(qqq_prices, sessions, asof_date, 126) if asof_date else None
        sym_sma_126_gap = sma_gap(sym_prices, sessions, asof_date, 126) if asof_date else None
        qqq_sma_126_gap = sma_gap(qqq_prices, sessions, asof_date, 126) if asof_date else None
        rel_ret_63 = None if sym_ret_63 is None or qqq_ret_63 is None else sym_ret_63 - qqq_ret_63
        rel_ret_126 = None if sym_ret_126 is None or qqq_ret_126 is None else sym_ret_126 - qqq_ret_126
        conviction_points = int(row["thesis_priority"]) + int(row["source_family_count"]) + int(row["positive_relation_count"])
        conviction_points -= int(row["unresolved_source_gap_count"])
        if rel_ret_63 is not None and rel_ret_63 > 0:
            conviction_points += 1
        if sym_ret_63 is not None and sym_ret_63 > 0:
            conviction_points += 1
        if sym_sma_126_gap is not None and sym_sma_126_gap > 0:
            conviction_points += 1
        enriched = dict(row)
        enriched.update(
            {
                "price_context_asof_date": asof_date,
                "symbol_ret_63": "" if sym_ret_63 is None else f"{sym_ret_63:.8f}",
                "symbol_ret_126": "" if sym_ret_126 is None else f"{sym_ret_126:.8f}",
                "qqq_ret_63": "" if qqq_ret_63 is None else f"{qqq_ret_63:.8f}",
                "qqq_ret_126": "" if qqq_ret_126 is None else f"{qqq_ret_126:.8f}",
                "relative_ret_63_vs_qqq": "" if rel_ret_63 is None else f"{rel_ret_63:.8f}",
                "relative_ret_126_vs_qqq": "" if rel_ret_126 is None else f"{rel_ret_126:.8f}",
                "symbol_sma_126_gap": "" if sym_sma_126_gap is None else f"{sym_sma_126_gap:.8f}",
                "qqq_sma_126_gap": "" if qqq_sma_126_gap is None else f"{qqq_sma_126_gap:.8f}",
                "regime_state": regime_state(qqq_ret_63, qqq_sma_126_gap),
                "conviction_points": conviction_points,
                "price_context_rule": "uses_prior_session_only_no_future_price",
                "authority": AUTHORITY,
            }
        )
        out.append(enriched)
    return out


def feature_passes_policy(feature: dict[str, object], policy: dict[str, object], current_dd: float) -> tuple[bool, str]:
    reasons = []
    rel_63 = None if feature["relative_ret_63_vs_qqq"] == "" else float(feature["relative_ret_63_vs_qqq"])
    sym_63 = None if feature["symbol_ret_63"] == "" else float(feature["symbol_ret_63"])
    if int(feature["conviction_points"]) < 2:
        reasons.append("conviction_points_below_2")
    if policy["qqq_hurdle"] and rel_63 is not None and rel_63 <= 0:
        reasons.append("failed_qqq_relative_momentum_hurdle")
    if policy["symbol_positive_momentum"] and sym_63 is not None and sym_63 <= 0:
        reasons.append("failed_positive_symbol_momentum_hurdle")
    if policy["regime_throttle"] and feature["regime_state"] == "risk_off" and int(feature["conviction_points"]) < 4:
        reasons.append("risk_off_requires_conviction_4")
    if policy["drawdown_throttle"] and current_dd <= -20.0 and int(feature["conviction_points"]) < 4:
        reasons.append("drawdown_throttle_requires_conviction_4")
    if policy["drawdown_throttle"] and current_dd <= -27.0 and (rel_63 is None or rel_63 <= 0.05):
        reasons.append("deep_drawdown_requires_5pct_relative_momentum")
    return not reasons, ";".join(reasons)


def feature_sort_key(feature: dict[str, object]) -> tuple[object, ...]:
    rel_63 = -999.0 if feature["relative_ret_63_vs_qqq"] == "" else float(feature["relative_ret_63_vs_qqq"])
    sym_63 = -999.0 if feature["symbol_ret_63"] == "" else float(feature["symbol_ret_63"])
    return (
        -int(feature["conviction_points"]),
        -int(feature["thesis_priority"]),
        -int(feature["source_family_count"]),
        -rel_63,
        -sym_63,
        int(feature["unresolved_source_gap_count"]),
        str(feature["theme"]),
        str(feature["symbol"]),
        str(feature["trade_spec_id"]),
    )


def active_slot_cap(policy: dict[str, object], regime: str, current_dd: float) -> int:
    cap = int(policy["base_slot_cap"])
    if policy["regime_throttle"]:
        if regime == "neutral":
            cap = min(cap, 7)
        elif regime == "risk_off":
            cap = min(cap, 5)
    if policy["drawdown_throttle"]:
        if current_dd <= -27.0:
            cap = min(cap, 3)
        elif current_dd <= -20.0:
            cap = min(cap, 5)
    return cap


def replay_policy(policy: dict[str, object], specs_by_id: dict[str, dict[str, str]], features_by_entry: dict[str, list[dict[str, object]]], prices: dict[str, dict[str, float]], sessions: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    policy_id = str(policy["policy_id"])
    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    skips: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []

    for day in sessions:
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

        equity_values_so_far = [float(row["equity"]) for row in equity_rows]
        dd = current_drawdown(equity_values_so_far)
        day_features = features_by_entry.get(day, [])
        regime = str(day_features[0]["regime_state"]) if day_features else "no_signal"
        cap = active_slot_cap(policy, regime, dd)
        available_slots = max(cap - len(open_positions), 0)
        theme_counts: dict[str, int] = defaultdict(int)
        for position in open_positions:
            theme_counts[str(position["theme"])] += 1

        passed: list[dict[str, object]] = []
        for feature in sorted(day_features, key=feature_sort_key):
            ok, reason = feature_passes_policy(feature, policy, dd)
            if not ok:
                decisions.append({**feature, "policy_id": policy_id, "active_slot_cap": cap, "selection_state": "rejected_by_veto", "selection_order": "", "blocked_reason": reason})
                continue
            if theme_counts[str(feature["theme"])] >= int(policy["theme_cap"]):
                decisions.append({**feature, "policy_id": policy_id, "active_slot_cap": cap, "selection_state": "rejected_by_theme_cap", "selection_order": "", "blocked_reason": "theme_cap_filled"})
                continue
            if len(passed) >= available_slots:
                decisions.append({**feature, "policy_id": policy_id, "active_slot_cap": cap, "selection_state": "rejected_by_slot_cap", "selection_order": "", "blocked_reason": "slot_cap_filled"})
                continue
            passed.append(feature)
            theme_counts[str(feature["theme"])] += 1
            decisions.append({**feature, "policy_id": policy_id, "active_slot_cap": cap, "selection_state": "selected", "selection_order": len(passed), "blocked_reason": ""})

        valid_orders: list[tuple[dict[str, str], float, float]] = []
        for feature in passed:
            spec = specs_by_id[str(feature["trade_spec_id"])]
            entry_ref = prices.get(spec["symbol"], {}).get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_ref = prices.get(spec["symbol"], {}).get(exit_date)
            if entry_ref is None:
                skips.append({**spec, "policy_id": policy_id, "skip_date": day, "skip_reason": "missing_exact_entry_price", "authority": AUTHORITY})
                continue
            if exit_ref is None:
                skips.append({**spec, "policy_id": policy_id, "skip_date": day, "skip_reason": "missing_exact_planned_exit_price", "authority": AUTHORITY})
                continue
            valid_orders.append((spec, entry_ref, entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)))

        per_order_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, entry_ref, entry_price in valid_orders:
            entry_fee = per_order_cash * (ENTRY_FEE_BPS / 10000.0)
            entry_notional = max(per_order_cash - entry_fee, 0.0)
            entry_cash_spent = entry_notional + entry_fee
            if entry_cash_spent <= 0.000001:
                skips.append({**spec, "policy_id": policy_id, "skip_date": day, "skip_reason": "no_available_cash", "authority": AUTHORITY})
                continue
            shares = entry_notional / entry_price
            cash -= entry_cash_spent
            open_positions.append(
                {
                    "policy_id": policy_id,
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
                "policy_id": policy_id,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "active_slot_cap": cap,
                "regime_state": regime,
                "current_drawdown_before_entry_pct": f"{dd:.6f}",
                "entry_candidates": len(day_features),
                "entries_selected": len(passed),
                "exits_closed": exits_closed,
                "authority": AUTHORITY,
            }
        )

    final_day = sessions[-1]
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
                "policy_id": policy_id,
                "date": final_day,
                "cash": f"{cash:.6f}",
                "open_market_value": "0.000000",
                "equity": f"{cash:.6f}",
                "open_positions": 0,
                "active_slot_cap": 0,
                "regime_state": "forced_close",
                "current_drawdown_before_entry_pct": "",
                "entry_candidates": 0,
                "entries_selected": 0,
                "exits_closed": forced_count,
                "authority": AUTHORITY,
            }
        )

    equity_values = [float(row["equity"]) for row in equity_rows]
    final_equity = equity_values[-1]
    qqq = prices["QQQ"]
    qqq_start = next(day for day in sessions if day in qqq)
    qqq_end = max(day for day in sessions if day in qqq)
    qqq_final = INITIAL_CAPITAL * qqq[qqq_end] / qqq[qqq_start]
    cagr = annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"]))
    mdd = max_drawdown(equity_values)
    summary = {
        "policy_id": policy_id,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "selected_entries": sum(1 for row in decisions if row["selection_state"] == "selected"),
        "rejected_by_veto": sum(1 for row in decisions if row["selection_state"] == "rejected_by_veto"),
        "rejected_by_theme_cap": sum(1 for row in decisions if row["selection_state"] == "rejected_by_theme_cap"),
        "rejected_by_slot_cap": sum(1 for row in decisions if row["selection_state"] == "rejected_by_slot_cap"),
        "closed_trades": len(trades),
        "skipped_orders": len(skips),
        "forced_closed_period_end": forced_count,
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(cagr, 6),
        "strategy_max_drawdown_pct": round(mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "meets_cagr_30": "1" if cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if mdd >= -30.0 else "0",
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return decisions, trades, skips, equity_rows, summary


def build() -> dict[str, object]:
    specs = [row for row in read_csv(TRADE_SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    base_features = read_csv(FEATURE_PATH)
    prior_slot_rows = read_csv(PREV_DIR / "task946_slot_capped_summary.csv")
    baseline_slot10 = next(row for row in prior_slot_rows if row["slot_cap"] == "10")
    sessions = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})
    enriched_features = build_enriched_features(base_features, prices, sessions)
    features_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for feature in enriched_features:
        features_by_entry[str(feature["entry_date"])].append(feature)

    all_decisions: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_skips: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for policy in POLICIES:
        decisions, trades, skips, equity, summary = replay_policy(policy, specs_by_id, features_by_entry, prices, sessions)
        all_decisions.extend(decisions)
        all_trades.extend(trades)
        all_skips.extend(skips)
        all_equity.extend(equity)
        summaries.append(summary)

    best_by_target = sorted(
        summaries,
        key=lambda row: (
            row["meets_cagr_30"] == "1",
            row["meets_mdd_minus30"] == "1",
            row["beats_qqq"] == "1",
            float(row["strategy_cagr_pct"]),
            float(row["strategy_max_drawdown_pct"]),
        ),
        reverse=True,
    )[0]
    closeout = [
        {
            "gate_id": "Task960",
            "tested_policies": ";".join(str(row["policy_id"]) for row in summaries),
            "best_policy_id": best_by_target["policy_id"],
            "best_policy_final_equity": best_by_target["strategy_final_equity"],
            "best_policy_cagr_pct": best_by_target["strategy_cagr_pct"],
            "best_policy_mdd_pct": best_by_target["strategy_max_drawdown_pct"],
            "best_policy_beats_qqq": best_by_target["beats_qqq"],
            "best_policy_meets_cagr_30": best_by_target["meets_cagr_30"],
            "best_policy_meets_mdd_minus30": best_by_target["meets_mdd_minus30"],
            "baseline_slot10_final_equity": baseline_slot10["strategy_final_equity"],
            "baseline_slot10_cagr_pct": baseline_slot10["strategy_cagr_pct"],
            "baseline_slot10_mdd_pct": baseline_slot10["strategy_max_drawdown_pct"],
            "best_policy_beats_baseline_slot10": "1" if float(best_by_target["strategy_final_equity"]) > float(baseline_slot10["strategy_final_equity"]) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "review target gap and avoid acceptance until split stability and source quality improve",
            "authority": AUTHORITY,
        }
    ]

    feature_fields = [
        "trade_spec_id",
        "adapter_input_id",
        "candidate_bundle_id",
        "decision_asof_ts",
        "entry_date",
        "split_id",
        "theme",
        "symbol",
        "candidate_thesis_type",
        "thesis_priority",
        "source_family_count",
        "support_relation_count",
        "positive_relation_count",
        "source_gap_relation_count",
        "negative_or_noise_relation_count",
        "unresolved_source_gap_count",
        "contradiction_state",
        "selection_key",
        "price_context_asof_date",
        "symbol_ret_63",
        "symbol_ret_126",
        "qqq_ret_63",
        "qqq_ret_126",
        "relative_ret_63_vs_qqq",
        "relative_ret_126_vs_qqq",
        "symbol_sma_126_gap",
        "qqq_sma_126_gap",
        "regime_state",
        "conviction_points",
        "price_context_rule",
        "does_not_use",
        "authority",
    ]
    write_csv(OUT_DIR / "task951_failure_and_target_gap.csv", summaries, list(summaries[0].keys()))
    write_csv(OUT_DIR / "task952_conviction_price_context_panel.csv", enriched_features, feature_fields)
    decision_fields = feature_fields + ["policy_id", "active_slot_cap", "selection_state", "selection_order", "blocked_reason"]
    write_csv(OUT_DIR / "task953_cash_qqq_regime_decision_ledger.csv", all_decisions, decision_fields)
    trade_fields = [
        "policy_id",
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
        "entry_date",
        "planned_exit_date",
        "entry_adj_close",
        "entry_price_after_slippage",
        "entry_notional",
        "entry_fee",
        "entry_cash_spent",
        "shares",
        "exit_date",
        "exit_adj_close",
        "exit_price_after_slippage",
        "exit_fee",
        "net_exit_value",
        "pnl",
        "return_pct",
        "fill_state",
        "authority",
    ]
    write_csv(OUT_DIR / "task959_conviction_risk_replay_trades.csv", all_trades, trade_fields)
    write_csv(
        OUT_DIR / "task958_conviction_risk_equity_curves.csv",
        all_equity,
        [
            "policy_id",
            "date",
            "cash",
            "open_market_value",
            "equity",
            "open_positions",
            "active_slot_cap",
            "regime_state",
            "current_drawdown_before_entry_pct",
            "entry_candidates",
            "entries_selected",
            "exits_closed",
            "authority",
        ],
    )
    skip_fields = list(all_skips[0].keys()) if all_skips else ["policy_id", "trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task957_conviction_risk_skipped_orders.csv", all_skips, skip_fields)
    write_csv(OUT_DIR / "task959_conviction_risk_replay_summary.csv", summaries, list(summaries[0].keys()))
    (OUT_DIR / "task959_conviction_risk_replay_summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    source_manifest = [
        {"source_name": "task929_controlled_trade_specs", "path": str(TRADE_SPEC_PATH.as_posix()), "sha256": sha256(TRADE_SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "task941_selection_features", "path": str(FEATURE_PATH.as_posix()), "sha256": sha256(FEATURE_PATH), "authority": AUTHORITY},
        {"source_name": "calendar", "path": str(CALENDAR_PATH.as_posix()), "sha256": sha256(CALENDAR_PATH), "authority": AUTHORITY},
    ]
    write_csv(OUT_DIR / "task956_conviction_risk_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    write_csv(
        OUT_DIR / "task960_conviction_risk_governance_closeout.csv",
        closeout,
        [
            "gate_id",
            "tested_policies",
            "best_policy_id",
            "best_policy_final_equity",
            "best_policy_cagr_pct",
            "best_policy_mdd_pct",
            "best_policy_beats_qqq",
            "best_policy_meets_cagr_30",
            "best_policy_meets_mdd_minus30",
            "baseline_slot10_final_equity",
            "baseline_slot10_cagr_pct",
            "baseline_slot10_mdd_pct",
            "best_policy_beats_baseline_slot10",
            "strategy_acceptance",
            "deployment_readiness",
            "real_capital",
            "next_action",
            "authority",
        ],
    )
    summary = {
        "task_id": "Task951-960",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": AUTHORITY,
        "input_trade_specs": len(specs),
        "tested_policy_count": len(POLICIES),
        "best_policy_id": best_by_target["policy_id"],
        "best_policy_final_equity": best_by_target["strategy_final_equity"],
        "best_policy_cagr_pct": best_by_target["strategy_cagr_pct"],
        "best_policy_mdd_pct": best_by_target["strategy_max_drawdown_pct"],
        "best_policy_beats_qqq": best_by_target["beats_qqq"],
        "best_policy_meets_cagr_30": best_by_target["meets_cagr_30"],
        "best_policy_meets_mdd_minus30": best_by_target["meets_mdd_minus30"],
        "baseline_slot10_final_equity": baseline_slot10["strategy_final_equity"],
        "baseline_slot10_cagr_pct": baseline_slot10["strategy_cagr_pct"],
        "baseline_slot10_mdd_pct": baseline_slot10["strategy_max_drawdown_pct"],
        "best_policy_beats_baseline_slot10": "1" if float(best_by_target["strategy_final_equity"]) > float(baseline_slot10["strategy_final_equity"]) else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (OUT_DIR / "task951_960_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task951_960_summary.csv", [summary], list(summary.keys()))
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_951_960_CONVICTION_RISK_OK] "
        f"best_policy={summary['best_policy_id']} "
        f"equity={summary['best_policy_final_equity']} "
        f"cagr={summary['best_policy_cagr_pct']} "
        f"mdd={summary['best_policy_mdd_pct']}"
    )


if __name__ == "__main__":
    main()
