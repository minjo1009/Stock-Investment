from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import FullTradeResult, _validate_preconditions, analyze_regime, run_full_backtest_universe, summarize


@dataclass(frozen=True)
class Scenario:
    name: str
    fee_rate: float
    slippage_rate: float


REALISTIC_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(name="Scenario 4", fee_rate=0.0025, slippage_rate=0.0010),
    Scenario(name="Scenario 5", fee_rate=0.0025, slippage_rate=0.0020),
    Scenario(name="Scenario 6", fee_rate=0.0025, slippage_rate=0.0030),
)


def _pf_text(value: float) -> str:
    return "inf" if value == float("inf") else f"{value:.4f}"


def _survival_status(pf: float) -> str:
    if pf >= 1.2:
        return "PASS"
    if pf >= 1.0:
        return "WARNING"
    return "FAIL"


def _print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def _symbol_pnl(results: list[FullTradeResult]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["symbol", "net_pnl"])
    rows: list[dict[str, object]] = []
    for item in results:
        rows.append({"symbol": item.trade.symbol, "net_pnl": float(item.net_pnl)})
    df = pd.DataFrame(rows)
    return df.groupby("symbol", as_index=False).agg(net_pnl=("net_pnl", "sum")).sort_values("net_pnl", ascending=False)


def _avg_trade_return_and_cost_rate(results: list[FullTradeResult]) -> tuple[float, float]:
    if not results:
        return 0.0, 0.0

    returns: list[float] = []
    costs: list[float] = []
    for item in results:
        qty = float(item.trade.quantity)
        entry_fill = float(item.trade.entry_fill_price)
        exit_fill = float(item.trade.exit_fill_price)
        entry_notional = entry_fill * qty
        exit_notional = exit_fill * qty
        round_trip_notional = entry_notional + exit_notional
        if round_trip_notional <= 0:
            continue
        returns.append(float(item.net_pnl) / round_trip_notional)
        costs.append(float(item.cost) / round_trip_notional)

    if not returns:
        return 0.0, 0.0
    return (sum(returns) / len(returns)) * 100.0, (sum(costs) / len(costs)) * 100.0


def run_realistic_scenarios(
    *,
    symbols: list[str],
    data_dir: Path,
    initial_equity: float,
    scenarios: tuple[Scenario, ...] = REALISTIC_SCENARIOS,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    summary_rows: list[dict[str, object]] = []
    regime_map: dict[str, pd.DataFrame] = {}
    symbol_map: dict[str, pd.DataFrame] = {}

    for scenario in scenarios:
        results = run_full_backtest_universe(
            symbols=symbols,
            base_dir=data_dir,
            initial_equity=initial_equity,
            fee_rate=scenario.fee_rate,
            slippage_rate=scenario.slippage_rate,
        )
        metric = summarize(results, initial_equity=initial_equity)
        regime_df = analyze_regime(results)
        symbol_df = _symbol_pnl(results)
        avg_return_pct, avg_cost_pct = _avg_trade_return_and_cost_rate(results)

        summary_rows.append(
            {
                "scenario": scenario.name,
                "fee_rate": scenario.fee_rate,
                "slippage_rate": scenario.slippage_rate,
                "total_pnl": float(metric.total_pnl),
                "net_pnl": float(metric.net_pnl),
                "win_rate": float(metric.win_rate),
                "profit_factor": float(metric.profit_factor),
                "max_drawdown": float(metric.max_drawdown),
                "sharpe": float(metric.sharpe_ratio),
                "avg_pnl_per_trade": float(metric.net_pnl / metric.trade_count) if metric.trade_count > 0 else 0.0,
                "trade_count": int(metric.trade_count),
                "avg_trade_return_pct": float(avg_return_pct),
                "avg_trade_cost_pct": float(avg_cost_pct),
            }
        )
        regime_map[scenario.name] = regime_df
        symbol_map[scenario.name] = symbol_df

    return pd.DataFrame(summary_rows), regime_map, symbol_map


def print_report(summary_df: pd.DataFrame, regime_map: dict[str, pd.DataFrame], symbol_map: dict[str, pd.DataFrame]) -> None:
    print("=== REALISTIC COST STRESS TEST (KIS) ===")
    for row in summary_df.itertuples(index=False):
        print(f"{row.scenario}: fee={float(row.fee_rate) * 100:.2f}% / slippage={float(row.slippage_rate) * 100:.2f}%")
        print(f"  TOTAL PNL: {float(row.total_pnl):.4f}")
        print(f"  NET PNL: {float(row.net_pnl):.4f}")
        print(f"  WIN RATE: {float(row.win_rate):.2f}%")
        print(f"  PROFIT FACTOR: {_pf_text(float(row.profit_factor))}")
        print(f"  MAX DRAWDOWN: {float(row.max_drawdown):.4f}")
        print(f"  SHARPE: {float(row.sharpe):.4f}")
        print(f"  AVG PNL per trade: {float(row.avg_pnl_per_trade):.4f}")
        print(f"  AVG TRADE RETURN (%): {float(row.avg_trade_return_pct):.4f}")
        print(f"  AVG TRADE COST (%): {float(row.avg_trade_cost_pct):.4f}")
        print()

    print("=== SURVIVAL CHECK ===")
    for row in summary_df.itertuples(index=False):
        pf = float(row.profit_factor)
        print(f"{row.scenario}:")
        print(f"PF: {_pf_text(pf)}")
        print(f"STATUS: {_survival_status(pf)}")
        print()

    collapse_pf = summary_df[summary_df["profit_factor"] < 1.0]
    collapse_net = summary_df[summary_df["net_pnl"] < 0.0]
    print("=== COLLAPSE THRESHOLD ===")
    if collapse_pf.empty:
        print("PF < 1 구간: 없음")
    else:
        first_pf = collapse_pf.iloc[0]
        print(f"PF < 1 구간: {first_pf['scenario']} (PF={first_pf['profit_factor']:.4f})")
    if collapse_net.empty:
        print("Net PnL 음수 전환: 없음")
    else:
        first_net = collapse_net.iloc[0]
        print(f"Net PnL 음수 전환: {first_net['scenario']} (Net PnL={first_net['net_pnl']:.4f})")
    print()

    print("=== BULL vs BEAR ===")
    for scenario in summary_df["scenario"].tolist():
        print(f"[{scenario}]")
        _print_df(regime_map[scenario])
        print()

    print("=== SYMBOL PNL CHANGE ===")
    base_name = str(summary_df.iloc[0]["scenario"])
    base_df = symbol_map[base_name].rename(columns={"net_pnl": "base_net_pnl"})
    for scenario in summary_df["scenario"].tolist()[1:]:
        cur_df = symbol_map[scenario].rename(columns={"net_pnl": "scenario_net_pnl"})
        merged = base_df.merge(cur_df, on="symbol", how="outer").fillna(0.0)
        merged["delta_net_pnl"] = merged["scenario_net_pnl"] - merged["base_net_pnl"]
        merged = merged.sort_values("delta_net_pnl").reset_index(drop=True)
        print(f"[{scenario} vs {base_name}]")
        _print_df(merged)
        print()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 050-2A: realistic KIS cost stress test")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE), help="Universe symbols")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR), help="Daily CSV directory")
    parser.add_argument("--initial-equity", type=float, default=100_000.0, help="Per-symbol base equity")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    data_dir = Path(args.data_dir)

    _validate_preconditions(symbols, base_dir=data_dir)
    summary_df, regime_map, symbol_map = run_realistic_scenarios(
        symbols=symbols,
        data_dir=data_dir,
        initial_equity=args.initial_equity,
    )
    print_report(summary_df, regime_map, symbol_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
