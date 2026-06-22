from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_universe_daily_bars
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats
from sector.sector_model import build_sector_snapshot, map_symbol_to_sector


STRATEGY_ID = "D_PORTFOLIO_SECTOR_FILTER"

ENTRY_POLICY = "LIMITED_CHASE"
RISK_POLICY = "TIME_STOP_ONLY"
MAX_POSITIONS = 3
TOP_SECTORS = 2

RISK_PER_TRADE = 0.01
MAX_POSITION_SIZE = 0.30
PORTFOLIO_MAX_EXPOSURE = 1.00
PER_SYMBOL_CAP = 0.30
FRACTIONAL_KELLY_CAP = 0.25

CAPITAL_SCENARIOS = [
    ("A_BASE_10K", 10_000.0),
    ("B_STRESS_1K", 1_000.0),
]

COST_SCENARIOS = [
    ("LOW_COST", 0.0001, 0.0005),
    ("HIGH_COST", 0.0005, 0.0020),
]


@dataclass(frozen=True)
class CapitalTrade:
    symbol: str
    sector: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    stop_price: float
    exit_rule: str


@dataclass(frozen=True)
class ClosedPosition:
    symbol: str
    sector: str
    entry_time: datetime
    exit_time: datetime
    qty: int
    entry_price_eff: float
    exit_price_eff: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    exit_rule: str
    notional: float


def _f(v: float, digits: int = 6) -> float:
    return float(round(float(v), digits))


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a / b)


def _to_capital_trades(results: list[FullTradeResult]) -> list[CapitalTrade]:
    rows: list[CapitalTrade] = []
    for item in results:
        trade = item.trade
        meta = item.metadata or {}
        if trade.exit_time is None:
            continue
        entry_fill = float(trade.entry_fill_price or trade.entry_price)
        exit_fill = float(trade.exit_fill_price or trade.exit_price or entry_fill)
        stop_price = float(meta.get("stop_price") or max(entry_fill * 0.95, 0.01))
        entry_ts = pd.Timestamp(trade.entry_time)
        exit_ts = pd.Timestamp(trade.exit_time)
        if entry_ts.tzinfo is None:
            entry_ts = entry_ts.tz_localize("UTC")
        else:
            entry_ts = entry_ts.tz_convert("UTC")
        if exit_ts.tzinfo is None:
            exit_ts = exit_ts.tz_localize("UTC")
        else:
            exit_ts = exit_ts.tz_convert("UTC")
        rows.append(
            CapitalTrade(
                symbol=trade.symbol,
                sector=str(meta.get("sector") or map_symbol_to_sector(trade.symbol)),
                entry_time=entry_ts.to_pydatetime(),
                exit_time=exit_ts.to_pydatetime(),
                entry_price=max(entry_fill, 0.01),
                exit_price=max(exit_fill, 0.01),
                stop_price=max(stop_price, 0.01),
                exit_rule=str(meta.get("exit_rule") or "UNKNOWN"),
            )
        )
    return sorted(rows, key=lambda r: (r.entry_time, r.exit_time, r.symbol))


def _max_drawdown_pct(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    peak = equity_points[0][1]
    max_dd = 0.0
    for _ts, eq in equity_points:
        peak = max(peak, eq)
        if peak <= 0:
            continue
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    return float(max_dd * 100.0)


def _daily_sharpe(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    series = pd.Series(
        data=[value for _ts, value in equity_points],
        index=pd.to_datetime([ts for ts, _value in equity_points], utc=True),
    ).sort_index()
    daily = series.resample("1D").last().ffill().dropna()
    if len(daily) < 3:
        return 0.0
    rets = daily.pct_change().dropna()
    if rets.empty:
        return 0.0
    std = float(rets.std(ddof=0))
    if std <= 0:
        return 0.0
    return float((rets.mean() / std) * math.sqrt(252))


def _cagr(initial_capital: float, final_capital: float, start: datetime, end: datetime) -> float:
    if initial_capital <= 0 or final_capital <= 0:
        return -100.0
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1.0 / 365.25)
    return float(((final_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0)


def _simulate_capital(
    trades: list[CapitalTrade],
    *,
    initial_capital: float,
    fee_rate: float,
    slippage_rate: float,
    use_fractional_kelly: bool = False,
) -> dict[str, Any]:
    if not trades:
        return {
            "initial_capital": initial_capital,
            "final_capital": initial_capital,
            "total_return_pct": 0.0,
            "cagr": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "avg_trade_return_pct": 0.0,
            "trade_count": 0,
            "exposure_ratio": 0.0,
            "capital_utilization": 0.0,
            "equity_curve_trade": [],
            "equity_curve_daily": [],
            "closed_positions": [],
            "skipped_trades": 0,
        }

    kelly_mult = FRACTIONAL_KELLY_CAP if use_fractional_kelly else 1.0
    cash = float(initial_capital)
    active: list[dict[str, Any]] = []
    closed: list[ClosedPosition] = []
    exposure_samples: list[float] = []
    utilization_samples: list[float] = []
    equity_points: list[tuple[datetime, float]] = []
    skipped = 0

    def settle_until(ts: datetime) -> None:
        nonlocal cash
        matured = [p for p in active if p["exit_time"] <= ts]
        if not matured:
            return
        for pos in sorted(matured, key=lambda p: p["exit_time"]):
            exit_eff = pos["exit_price"] * (1.0 - slippage_rate)
            exit_notional = exit_eff * pos["qty"]
            exit_fee = exit_notional * fee_rate
            proceeds = exit_notional - exit_fee
            cash += proceeds
            gross = (exit_eff - pos["entry_eff"]) * pos["qty"]
            net = proceeds - pos["cash_out"]
            ret_pct = _safe_div(net, pos["cash_out"]) * 100.0
            closed.append(
                ClosedPosition(
                    symbol=pos["symbol"],
                    sector=pos["sector"],
                    entry_time=pos["entry_time"],
                    exit_time=pos["exit_time"],
                    qty=pos["qty"],
                    entry_price_eff=pos["entry_eff"],
                    exit_price_eff=exit_eff,
                    gross_pnl=gross,
                    net_pnl=net,
                    return_pct=ret_pct,
                    exit_rule=pos["exit_rule"],
                    notional=pos["entry_eff"] * pos["qty"],
                )
            )
            equity_now = cash + sum(p["entry_eff"] * p["qty"] for p in active if p is not pos)
            equity_points.append((pos["exit_time"], equity_now))
        active[:] = [p for p in active if p["exit_time"] > ts]

    for trade in trades:
        settle_until(trade.entry_time)

        open_notional = sum(p["entry_eff"] * p["qty"] for p in active)
        total_equity = cash + open_notional
        if total_equity <= 0:
            skipped += 1
            continue
        symbol_exposure = sum(p["entry_eff"] * p["qty"] for p in active if p["symbol"] == trade.symbol)
        risk_budget = total_equity * RISK_PER_TRADE * kelly_mult
        risk_per_share = max(trade.entry_price - trade.stop_price, trade.entry_price * 0.005)
        qty_by_risk = int(math.floor(_safe_div(risk_budget, risk_per_share)))
        max_symbol_notional = total_equity * PER_SYMBOL_CAP
        max_position_notional = total_equity * MAX_POSITION_SIZE
        remaining_portfolio_notional = max((total_equity * PORTFOLIO_MAX_EXPOSURE) - open_notional, 0.0)
        allowed_notional = min(max_position_notional, max_symbol_notional - symbol_exposure, remaining_portfolio_notional, cash)
        qty_by_notional = int(math.floor(_safe_div(allowed_notional, trade.entry_price)))
        qty = min(qty_by_risk, qty_by_notional)
        if qty < 1:
            skipped += 1
            continue

        entry_eff = trade.entry_price * (1.0 + slippage_rate)
        entry_notional = entry_eff * qty
        entry_fee = entry_notional * fee_rate
        cash_out = entry_notional + entry_fee
        if cash_out > cash:
            skipped += 1
            continue
        cash -= cash_out
        active.append(
            {
                "symbol": trade.symbol,
                "sector": trade.sector,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "entry_eff": entry_eff,
                "exit_price": trade.exit_price,
                "qty": qty,
                "cash_out": cash_out,
                "exit_rule": trade.exit_rule,
            }
        )
        current_open_notional = sum(p["entry_eff"] * p["qty"] for p in active)
        current_equity = cash + current_open_notional
        exposure_samples.append(_safe_div(current_open_notional, current_equity))
        utilization_samples.append(_safe_div(current_open_notional, initial_capital))
        equity_points.append((trade.entry_time, current_equity))

    settle_until(datetime(2260, 1, 1, tzinfo=timezone.utc))
    final_capital = float(cash)
    trade_count = len(closed)
    pnls = [p.net_pnl for p in closed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = float(sum(wins))
    gross_loss_abs = abs(float(sum(losses)))
    profit_factor = (gross_profit / gross_loss_abs) if gross_loss_abs > 0 else float("inf")
    win_rate = (_safe_div(len(wins), trade_count) * 100.0) if trade_count else 0.0
    avg_trade_return = float(statistics.fmean([p.return_pct for p in closed])) if closed else 0.0

    if not equity_points:
        equity_points = [(trades[0].entry_time, initial_capital), (trades[-1].exit_time, final_capital)]
    equity_points = sorted(equity_points, key=lambda x: x[0])
    daily_series = (
        pd.Series([v for _t, v in equity_points], index=pd.to_datetime([t for t, _v in equity_points], utc=True))
        .sort_index()
        .resample("1D")
        .last()
        .ffill()
    )
    daily_curve = [{"ts": str(ts.isoformat()), "equity": _f(v)} for ts, v in daily_series.items()]
    trade_curve = [{"ts": str(ts.isoformat()), "equity": _f(eq)} for ts, eq in equity_points]

    start_ts = trades[0].entry_time
    end_ts = trades[-1].exit_time
    out = {
        "initial_capital": _f(initial_capital, 2),
        "final_capital": _f(final_capital, 2),
        "total_return_pct": _f((_safe_div(final_capital - initial_capital, initial_capital)) * 100.0),
        "cagr": _f(_cagr(initial_capital, final_capital, start_ts, end_ts)),
        "sharpe": _f(_daily_sharpe(equity_points)),
        "max_drawdown_pct": _f(_max_drawdown_pct(equity_points)),
        "profit_factor": _f(profit_factor),
        "win_rate": _f(win_rate),
        "avg_trade_return_pct": _f(avg_trade_return),
        "trade_count": int(trade_count),
        "exposure_ratio": _f(statistics.fmean(exposure_samples) if exposure_samples else 0.0),
        "capital_utilization": _f(statistics.fmean(utilization_samples) if utilization_samples else 0.0),
        "equity_curve_trade": trade_curve,
        "equity_curve_daily": daily_curve,
        "closed_positions": [
            {
                "symbol": p.symbol,
                "sector": p.sector,
                "entry_time": str(pd.Timestamp(p.entry_time).isoformat()),
                "exit_time": str(pd.Timestamp(p.exit_time).isoformat()),
                "qty": int(p.qty),
                "entry_price_eff": _f(p.entry_price_eff),
                "exit_price_eff": _f(p.exit_price_eff),
                "gross_pnl": _f(p.gross_pnl),
                "net_pnl": _f(p.net_pnl),
                "return_pct": _f(p.return_pct),
                "exit_rule": p.exit_rule,
                "notional": _f(p.notional),
            }
            for p in closed
        ],
        "skipped_trades": int(skipped),
    }
    return out


def _status_for_metrics(metrics: dict[str, Any]) -> str:
    cagr = float(metrics["cagr"])
    mdd = float(metrics["max_drawdown_pct"])
    sharpe = float(metrics["sharpe"])
    ret = float(metrics["total_return_pct"])
    if ret < 0.0 or mdd > 40.0 or sharpe < 0.5:
        return "FAIL"
    weak_count = sum([cagr <= 15.0, mdd >= 25.0, sharpe <= 1.0])
    if weak_count == 0:
        return "PASS"
    return "WARNING"


def _failure_modes(metrics: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if float(metrics["max_drawdown_pct"]) > 35.0:
        findings.append("Drawdown clustering risk is high under capital constraints.")
    if float(metrics["capital_utilization"]) > 0.9:
        findings.append("Capital utilization is near full; over-leverage risk in concurrent moves.")
    if float(metrics["final_capital"]) < float(metrics["initial_capital"]) * 0.7:
        findings.append("Capital depletion risk detected.")
    if float(metrics["exposure_ratio"]) > 0.8:
        findings.append("Exposure concentration remains elevated.")
    if not findings:
        findings.append("No dominant capital-failure mode detected in this scenario.")
    return findings


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T093 - Capital-Based Portfolio Backtest")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- strategy_id: {report['strategy_id']}")
    lines.append(f"- primary_scenario: {report['primary_scenario']}")
    lines.append(f"- final_capital: {report['primary_metrics']['final_capital']}")
    lines.append(f"- total_return_pct: {report['primary_metrics']['total_return_pct']}")
    lines.append(f"- max_drawdown_pct: {report['primary_metrics']['max_drawdown_pct']}")
    lines.append(f"- sharpe: {report['primary_metrics']['sharpe']}")
    lines.append(f"- decision: {report['status']}")
    lines.append("")
    lines.append("## 2. Scenario Comparison")
    lines.append("| Scenario | Final Capital | Return % | MDD % | Sharpe | PF | Trades | Status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for row in report["scenario_rows"]:
        lines.append(
            f"| {row['scenario']} | {row['final_capital']:.2f} | {row['total_return_pct']:.4f} | "
            f"{row['max_drawdown_pct']:.4f} | {row['sharpe']:.6f} | {row['profit_factor']:.6f} | {row['trade_count']} | {row['status']} |"
        )
    lines.append("")
    lines.append("## 3. Equity Curve Analysis")
    lines.append(f"- trade_points: {len(report['primary_metrics']['equity_curve_trade'])}")
    lines.append(f"- daily_points: {len(report['primary_metrics']['equity_curve_daily'])}")
    lines.append(f"- recovery_comment: {report['equity_curve_comment']}")
    lines.append("")
    lines.append("## 4. Trade Distribution")
    lines.append(f"- win_rate: {report['primary_metrics']['win_rate']}")
    lines.append(f"- avg_trade_return_pct: {report['primary_metrics']['avg_trade_return_pct']}")
    lines.append(f"- tail_risk_comment: {report['tail_risk_comment']}")
    lines.append("")
    lines.append("## 5. Cost Impact")
    lines.append(f"- pnl_before_cost: {report['cost_impact']['pnl_before_cost']}")
    lines.append(f"- pnl_after_cost: {report['cost_impact']['pnl_after_cost']}")
    lines.append(f"- cost_impact_pct: {report['cost_impact']['cost_impact_pct']}")
    lines.append("")
    lines.append("## 6. Risk Evaluation")
    lines.append(f"- exposure_ratio: {report['primary_metrics']['exposure_ratio']}")
    lines.append(f"- capital_utilization: {report['primary_metrics']['capital_utilization']}")
    lines.append(f"- skipped_trades: {report['primary_metrics']['skipped_trades']}")
    for finding in report["failure_modes"]:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("## 7. Failure Modes")
    for finding in report["failure_modes"]:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("## 8. Decision")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- answer: {report['answer']}")
    lines.append("")
    lines.append("## 9. Final Answer")
    lines.append(f"Is the strategy profitable under realistic capital constraints? {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T093: Capital-based portfolio backtest")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_093/task_093_capital_backtest.md")
    parser.add_argument("--use-fractional-kelly", action="store_true")
    args = parser.parse_args(argv)

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    data_dir = Path(args.data_dir)

    frames = load_universe_daily_bars(symbols, base_dir=data_dir)
    sector_snapshot = build_sector_snapshot(frames)
    ranked_sectors = sorted(sector_snapshot.items(), key=lambda item: float(item[1]["strength_score"]), reverse=True)
    allowed_sectors = {name for name, _snapshot in ranked_sectors[: max(1, TOP_SECTORS)]}
    selected_symbols = [s for s in symbols if map_symbol_to_sector(s) in allowed_sectors]
    if not selected_symbols:
        selected_symbols = list(symbols)

    baseline_results, _stats = run_full_backtest_universe_with_stats(
        symbols=selected_symbols,
        base_dir=data_dir,
        initial_equity=100_000.0,
        fee_rate=0.0,
        slippage_rate=0.0,
        entry_policy=ENTRY_POLICY,
        risk_policy=RISK_POLICY,
        mode="portfolio",
        max_positions=MAX_POSITIONS,
    )
    trades = _to_capital_trades(baseline_results)

    scenario_rows: list[dict[str, Any]] = []
    scenario_details: dict[str, dict[str, Any]] = {}
    for cap_name, capital in CAPITAL_SCENARIOS:
        for cost_name, fee_rate, slip_rate in COST_SCENARIOS:
            scenario_name = f"{cap_name}_{cost_name}"
            metrics = _simulate_capital(
                trades,
                initial_capital=capital,
                fee_rate=fee_rate,
                slippage_rate=slip_rate,
                use_fractional_kelly=args.use_fractional_kelly,
            )
            status = _status_for_metrics(metrics)
            row = {
                "scenario": scenario_name,
                "initial_capital": metrics["initial_capital"],
                "final_capital": metrics["final_capital"],
                "total_return_pct": metrics["total_return_pct"],
                "cagr": metrics["cagr"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "profit_factor": metrics["profit_factor"],
                "win_rate": metrics["win_rate"],
                "avg_trade_return_pct": metrics["avg_trade_return_pct"],
                "trade_count": metrics["trade_count"],
                "exposure_ratio": metrics["exposure_ratio"],
                "capital_utilization": metrics["capital_utilization"],
                "status": status,
            }
            scenario_rows.append(row)
            scenario_details[scenario_name] = metrics

    primary_key = "A_BASE_10K_HIGH_COST"
    primary_metrics = scenario_details.get(primary_key, scenario_details[scenario_rows[0]["scenario"]])
    primary_status = next((row["status"] for row in scenario_rows if row["scenario"] == primary_key), scenario_rows[0]["status"])
    overall_status = "FAIL" if any(row["status"] == "FAIL" for row in scenario_rows) else ("PASS" if all(row["status"] == "PASS" for row in scenario_rows) else "WARNING")
    if primary_status == "FAIL":
        overall_status = "FAIL"
    answer = "YES" if overall_status == "PASS" else "NO"

    no_cost_primary = _simulate_capital(
        trades,
        initial_capital=10_000.0,
        fee_rate=0.0,
        slippage_rate=0.0,
        use_fractional_kelly=args.use_fractional_kelly,
    )
    high_cost_primary = scenario_details.get(primary_key, primary_metrics)
    pnl_before = float(no_cost_primary["final_capital"] - no_cost_primary["initial_capital"])
    pnl_after = float(high_cost_primary["final_capital"] - high_cost_primary["initial_capital"])
    cost_impact_pct = _safe_div((pnl_before - pnl_after), max(abs(pnl_before), 1e-9)) * 100.0
    failure_modes = _failure_modes(primary_metrics)

    report = {
        "task": "T093",
        "status": overall_status,
        "answer": answer,
        "strategy_id": STRATEGY_ID,
        "selected_symbols": selected_symbols,
        "selected_sectors": sorted(allowed_sectors),
        "config": {
            "entry_policy": ENTRY_POLICY,
            "risk_policy": RISK_POLICY,
            "max_positions": MAX_POSITIONS,
            "risk_per_trade": RISK_PER_TRADE,
            "max_position_size": MAX_POSITION_SIZE,
            "portfolio_max_exposure": PORTFOLIO_MAX_EXPOSURE,
            "per_symbol_cap": PER_SYMBOL_CAP,
            "fractional_kelly_enabled": bool(args.use_fractional_kelly),
            "fractional_kelly_cap": FRACTIONAL_KELLY_CAP,
        },
        "scenarios": scenario_details,
        "scenario_rows": scenario_rows,
        "primary_scenario": primary_key,
        "primary_metrics": primary_metrics,
        "cost_impact": {
            "pnl_before_cost": _f(pnl_before, 4),
            "pnl_after_cost": _f(pnl_after, 4),
            "cost_impact_pct": _f(cost_impact_pct),
            "low_cost_fee": COST_SCENARIOS[0][1],
            "low_cost_slippage": COST_SCENARIOS[0][2],
            "high_cost_fee": COST_SCENARIOS[1][1],
            "high_cost_slippage": COST_SCENARIOS[1][2],
        },
        "equity_curve_comment": (
            "Equity curve is evaluated on trade events and daily resample; drawdown/recovery are capital-based."
        ),
        "tail_risk_comment": (
            "Tail risk is assessed from realized trade distribution under constrained sizing and capped exposure."
        ),
        "failure_modes": failure_modes,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={overall_status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
