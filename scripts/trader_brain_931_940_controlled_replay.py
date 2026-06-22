from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
OUT_DIR = ROOT / "data/artifacts/task_931_940_controlled_brain_replay"

TRADE_SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
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
AUTHORITY = "DIAGNOSTIC_CONTROLLED_BRAIN_REPLAY_ONLY"


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


def annualized_return(start_value: float, end_value: float, start_date: str, end_date: str) -> float:
    d0 = datetime.fromisoformat(start_date)
    d1 = datetime.fromisoformat(end_date)
    days = max((d1 - d0).days, 1)
    years = days / 365.25
    if start_value <= 0:
        return 0.0
    return ((end_value / start_value) ** (1.0 / years) - 1.0) * 100.0


def replay() -> dict[str, object]:
    specs = [row for row in read_csv(TRADE_SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    symbols = {row["symbol"] for row in specs} | {"QQQ"}
    prices = load_prices(symbols)

    by_entry: dict[str, list[dict[str, str]]] = defaultdict(list)
    for spec in specs:
        entry_date = date_part(spec["tradable_after_ts"])
        if PERIOD_START <= entry_date <= PERIOD_END:
            by_entry[entry_date].append(spec)

    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    fills: list[dict[str, object]] = []
    skips: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    exits_by_date: dict[str, list[dict[str, object]]] = defaultdict(list)

    for day in calendar:
        # Close first so same-day exit cash can fund new same-close entries.
        remaining_positions: list[dict[str, object]] = []
        for position in open_positions:
            if position["planned_exit_date"] == day:
                symbol = str(position["symbol"])
                exit_ref = prices.get(symbol, {}).get(day)
                if exit_ref is None:
                    position["exit_miss_count"] = int(position.get("exit_miss_count", 0)) + 1
                    remaining_positions.append(position)
                    continue
                exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
                shares = float(position["shares"])
                gross_exit_value = shares * exit_price
                exit_fee = gross_exit_value * (EXIT_FEE_BPS / 10000.0)
                net_exit_value = gross_exit_value - exit_fee
                cash += net_exit_value
                pnl = net_exit_value - float(position["entry_cash_spent"])
                fill = dict(position)
                fill.update(
                    {
                        "exit_date": day,
                        "exit_adj_close": f"{exit_ref:.6f}",
                        "exit_price_after_slippage": f"{exit_price:.6f}",
                        "exit_fee": f"{exit_fee:.6f}",
                        "net_exit_value": f"{net_exit_value:.6f}",
                        "pnl": f"{pnl:.6f}",
                        "return_pct": f"{((net_exit_value / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                        "fill_state": "closed",
                    }
                )
                fills.append(fill)
                exits_by_date[day].append(fill)
            else:
                remaining_positions.append(position)
        open_positions = remaining_positions

        cohort = by_entry.get(day, [])
        valid_orders: list[tuple[dict[str, str], float, float, float]] = []
        for spec in cohort:
            symbol = spec["symbol"]
            entry_ref = prices.get(symbol, {}).get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_ref = prices.get(symbol, {}).get(exit_date)
            if entry_ref is None:
                skips.append({**spec, "skip_date": day, "skip_reason": "missing_exact_entry_price", "authority": AUTHORITY})
                continue
            if exit_ref is None:
                skips.append({**spec, "skip_date": day, "skip_reason": "missing_exact_planned_exit_price", "authority": AUTHORITY})
                continue
            requested = float(spec["allocated_capital"])
            entry_price = entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)
            entry_fee = requested * (ENTRY_FEE_BPS / 10000.0)
            valid_orders.append((spec, requested, entry_price, entry_fee))

        requested_cash = sum(requested + entry_fee for _, requested, _, entry_fee in valid_orders)
        scale = min(1.0, cash / requested_cash) if requested_cash > 0 else 0.0
        if scale < 0:
            scale = 0.0

        for spec, requested, entry_price, _ in valid_orders:
            scaled_notional = requested * scale
            entry_fee = scaled_notional * (ENTRY_FEE_BPS / 10000.0)
            entry_cash_spent = scaled_notional + entry_fee
            if entry_cash_spent <= 0.000001:
                skips.append({**spec, "skip_date": day, "skip_reason": "no_available_cash_after_scaling", "authority": AUTHORITY})
                continue
            shares = scaled_notional / entry_price
            cash -= entry_cash_spent
            position = {
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
                "entry_adj_close": f"{(entry_price / (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)):.6f}",
                "entry_price_after_slippage": f"{entry_price:.6f}",
                "requested_capital": f"{requested:.6f}",
                "cash_scale_factor": f"{scale:.8f}",
                "entry_notional": f"{scaled_notional:.6f}",
                "entry_fee": f"{entry_fee:.6f}",
                "entry_cash_spent": f"{entry_cash_spent:.6f}",
                "shares": f"{shares:.10f}",
                "authority": AUTHORITY,
            }
            open_positions.append(position)

        market_value = 0.0
        for position in open_positions:
            symbol = str(position["symbol"])
            px = prices.get(symbol, {}).get(day)
            if px is not None:
                market_value += float(position["shares"]) * px
        equity = cash + market_value
        equity_rows.append(
            {
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{equity:.6f}",
                "open_positions": len(open_positions),
                "entries_submitted": len(cohort),
                "entries_valid": len(valid_orders),
                "entry_scale_factor": f"{scale:.8f}" if valid_orders else "",
                "exits_closed": len(exits_by_date.get(day, [])),
                "authority": AUTHORITY,
            }
        )

    # Force-close positions at period end only if they are still open due to a missed planned exit.
    final_day = calendar[-1]
    forced_rows: list[dict[str, object]] = []
    remaining_after_force: list[dict[str, object]] = []
    for position in open_positions:
        symbol = str(position["symbol"])
        exit_ref = prices.get(symbol, {}).get(final_day)
        if exit_ref is None:
            remaining_after_force.append(position)
            continue
        exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
        shares = float(position["shares"])
        gross_exit_value = shares * exit_price
        exit_fee = gross_exit_value * (EXIT_FEE_BPS / 10000.0)
        net_exit_value = gross_exit_value - exit_fee
        cash += net_exit_value
        pnl = net_exit_value - float(position["entry_cash_spent"])
        fill = dict(position)
        fill.update(
            {
                "exit_date": final_day,
                "exit_adj_close": f"{exit_ref:.6f}",
                "exit_price_after_slippage": f"{exit_price:.6f}",
                "exit_fee": f"{exit_fee:.6f}",
                "net_exit_value": f"{net_exit_value:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_pct": f"{((net_exit_value / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                "fill_state": "forced_closed_period_end",
            }
        )
        forced_rows.append(fill)
        fills.append(fill)
    open_positions = remaining_after_force

    if forced_rows:
        equity_rows.append(
            {
                "date": final_day,
                "cash": f"{cash:.6f}",
                "open_market_value": "0.000000",
                "equity": f"{cash:.6f}",
                "open_positions": len(open_positions),
                "entries_submitted": 0,
                "entries_valid": 0,
                "entry_scale_factor": "",
                "exits_closed": len(forced_rows),
                "authority": AUTHORITY,
            }
        )

    final_equity = float(equity_rows[-1]["equity"])
    equity_values = [float(row["equity"]) for row in equity_rows]
    start_date = equity_rows[0]["date"]
    end_date = equity_rows[-1]["date"]

    qqq_prices = prices["QQQ"]
    qqq_start_date = next(day for day in calendar if day in qqq_prices)
    qqq_end_date = max(day for day in calendar if day <= PERIOD_END and day in qqq_prices)
    qqq_final = INITIAL_CAPITAL * qqq_prices[qqq_end_date] / qqq_prices[qqq_start_date]

    summary = {
        "task_id": "Task931-940",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": AUTHORITY,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "trade_specs_input": len(specs),
        "closed_trades": len(fills),
        "skipped_orders": len(skips),
        "forced_closed_period_end": len(forced_rows),
        "open_positions_end": len(open_positions),
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(annualized_return(INITIAL_CAPITAL, final_equity, start_date, end_date), 6),
        "strategy_max_drawdown_pct": round(max_drawdown(equity_values), 6),
        "qqq_start_date": qqq_start_date,
        "qqq_end_date": qqq_end_date,
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start_date, qqq_end_date), 6),
        "benchmark_symbol": "QQQ",
        "entry_slippage_bps": ENTRY_SLIPPAGE_BPS,
        "exit_slippage_bps": EXIT_SLIPPAGE_BPS,
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "execution_model": "daily_adjusted_close_fractional_cash_limited",
        "cash_scaling_rule": "same_entry_date_orders_scaled_pro_rata_to_available_cash",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }

    by_split = []
    for split in sorted({row["split_id"] for row in fills}):
        split_rows = [row for row in fills if row["split_id"] == split]
        pnl = sum(float(row["pnl"]) for row in split_rows)
        spent = sum(float(row["entry_cash_spent"]) for row in split_rows)
        by_split.append(
            {
                "split_id": split,
                "closed_trades": len(split_rows),
                "entry_cash_spent": f"{spent:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                "authority": AUTHORITY,
            }
        )

    by_theme = []
    for theme in sorted({row["theme"] for row in fills}):
        theme_rows = [row for row in fills if row["theme"] == theme]
        pnl = sum(float(row["pnl"]) for row in theme_rows)
        spent = sum(float(row["entry_cash_spent"]) for row in theme_rows)
        by_theme.append(
            {
                "theme": theme,
                "closed_trades": len(theme_rows),
                "entry_cash_spent": f"{spent:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                "authority": AUTHORITY,
            }
        )

    fill_fields = [
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
        "requested_capital",
        "cash_scale_factor",
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
    write_csv(OUT_DIR / "task931_controlled_replay_trades.csv", fills, fill_fields)
    write_csv(
        OUT_DIR / "task932_controlled_replay_equity_curve.csv",
        equity_rows,
        ["date", "cash", "open_market_value", "equity", "open_positions", "entries_submitted", "entries_valid", "entry_scale_factor", "exits_closed", "authority"],
    )
    write_csv(OUT_DIR / "task933_controlled_replay_by_split.csv", by_split, ["split_id", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "authority"])
    write_csv(OUT_DIR / "task934_controlled_replay_by_theme.csv", by_theme, ["theme", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "authority"])
    skip_fields = list(skips[0].keys()) if skips else ["trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task935_controlled_replay_skipped_orders.csv", skips, skip_fields)
    write_csv(OUT_DIR / "task936_controlled_replay_summary.csv", [summary], list(summary.keys()))
    (OUT_DIR / "task936_controlled_replay_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    source_manifest = [
        {"source_name": "trade_specs", "path": str(TRADE_SPEC_PATH.as_posix()), "sha256": sha256(TRADE_SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "calendar", "path": str(CALENDAR_PATH.as_posix()), "sha256": sha256(CALENDAR_PATH), "authority": AUTHORITY},
    ]
    for symbol in sorted(symbols):
        path = DAILY_DIR / f"{symbol}.csv"
        if path.exists():
            source_manifest.append({"source_name": f"daily_{symbol}", "path": str(path.as_posix()), "sha256": sha256(path), "authority": AUTHORITY})
    write_csv(OUT_DIR / "task937_replay_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    gate = [
        {
            "gate_id": "Task940",
            "result_status": "diagnostic_replay_completed",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "does_not_mean": "strategy acceptance deployment readiness or real-capital permission",
            "next_action": "failure_decomposition_and_adapter_policy_review_before_any_strategy_claim",
            "authority": AUTHORITY,
        }
    ]
    write_csv(OUT_DIR / "task940_governance_closeout.csv", gate, ["gate_id", "result_status", "strategy_acceptance", "deployment_readiness", "real_capital", "does_not_mean", "next_action", "authority"])
    return summary


def main() -> None:
    summary = replay()
    print(
        "[TRADER_BRAIN_931_940_REPLAY_OK] "
        f"trades={summary['closed_trades']} skipped={summary['skipped_orders']} "
        f"strategy={summary['strategy_final_equity']} qqq={summary['qqq_final_equity']} "
        f"return={summary['strategy_total_return_pct']}%"
    )


if __name__ == "__main__":
    main()
