from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import _validate_preconditions, analyze_regime, run_full_backtest_universe, summarize


@dataclass(frozen=True)
class Scenario:
    name: str
    slippage_rate: float
    fee_rate: float


DEFAULT_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(name="Scenario 0 (baseline)", slippage_rate=0.0, fee_rate=0.0),
    Scenario(name="Scenario 1 (0.05%)", slippage_rate=0.0005, fee_rate=0.0005),
    Scenario(name="Scenario 2 (0.10%)", slippage_rate=0.0010, fee_rate=0.0005),
    Scenario(name="Scenario 3 (0.20%)", slippage_rate=0.0020, fee_rate=0.0010),
)


def _pf_text(value: float) -> str:
    return "inf" if value == float("inf") else f"{value:.4f}"


def _pct_change(base: float, value: float) -> float | None:
    if base == 0:
        return None
    return ((value - base) / abs(base)) * 100.0


def _results_to_symbol_df(results: list, scenario_name: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for item in results:
        rows.append(
            {
                "scenario": scenario_name,
                "symbol": item.trade.symbol,
                "net_pnl": float(item.net_pnl),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["scenario", "symbol", "net_pnl"])
    df = pd.DataFrame(rows)
    return (
        df.groupby(["scenario", "symbol"], as_index=False)
        .agg(net_pnl=("net_pnl", "sum"))
        .sort_values(["scenario", "net_pnl"], ascending=[True, False])
        .reset_index(drop=True)
    )


def _print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def run_sensitivity(
    *,
    symbols: list[str],
    data_dir: Path,
    initial_equity: float,
    scenarios: tuple[Scenario, ...] = DEFAULT_SCENARIOS,
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
        symbol_df = _results_to_symbol_df(results, scenario.name)

        summary_rows.append(
            {
                "scenario": scenario.name,
                "slippage_rate": scenario.slippage_rate,
                "fee_rate": scenario.fee_rate,
                "total_pnl": metric.total_pnl,
                "net_pnl": metric.net_pnl,
                "win_rate": metric.win_rate,
                "profit_factor": metric.profit_factor,
                "max_drawdown": metric.max_drawdown,
                "sharpe": metric.sharpe_ratio,
                "trade_count": metric.trade_count,
            }
        )
        regime_map[scenario.name] = regime_df
        symbol_map[scenario.name] = symbol_df

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, regime_map, symbol_map


def print_report(summary_df: pd.DataFrame, regime_map: dict[str, pd.DataFrame], symbol_map: dict[str, pd.DataFrame]) -> None:
    baseline = summary_df.iloc[0]

    print("=== COST SENSITIVITY ===")
    for row in summary_df.itertuples(index=False):
        print(row.scenario)
        print(f"  PF: {_pf_text(float(row.profit_factor))}")
        print(f"  Net PnL: {float(row.net_pnl):.4f}")
        print(f"  Total PnL: {float(row.total_pnl):.4f}")
        print(f"  Win Rate: {float(row.win_rate):.2f}%")
        print(f"  Max Drawdown: {float(row.max_drawdown):.4f}")
        print(f"  Sharpe: {float(row.sharpe):.4f}")
        print()

    print("=== COMPARISON VS BASELINE ===")
    for row in summary_df.iloc[1:].itertuples(index=False):
        pf_base = float(baseline["profit_factor"])
        pf_now = float(row.profit_factor)
        pnl_base = float(baseline["net_pnl"])
        pnl_now = float(row.net_pnl)

        pf_change = _pct_change(pf_base, pf_now)
        pnl_change = _pct_change(pnl_base, pnl_now)

        pf_text = "n/a" if pf_change is None else f"{pf_change:.2f}%"
        pnl_text = "n/a" if pnl_change is None else f"{pnl_change:.2f}%"

        print(f"{row.scenario}")
        print(f"  PF change: {pf_text}")
        print(f"  Net PnL change: {pnl_text}")
        print()

    collapse = summary_df[summary_df["profit_factor"] < 1.0]
    if collapse.empty:
        print("Strategy collapse point (PF < 1): not reached in tested scenarios")
    else:
        first = collapse.iloc[0]
        print(f"Strategy collapse point (PF < 1): {first['scenario']} (PF={first['profit_factor']:.4f})")
    print()

    print("=== REGIME BREAKDOWN BY SCENARIO ===")
    for scenario in summary_df["scenario"].tolist():
        print(f"[{scenario}]")
        _print_df(regime_map[scenario])
        print()

    print("=== SYMBOL PNL CHANGE VS BASELINE ===")
    base_name = str(summary_df.iloc[0]["scenario"])
    base_df = symbol_map[base_name][["symbol", "net_pnl"]].rename(columns={"net_pnl": "baseline_net_pnl"})

    for scenario in summary_df["scenario"].tolist()[1:]:
        cur_df = symbol_map[scenario][["symbol", "net_pnl"]].rename(columns={"net_pnl": "scenario_net_pnl"})
        merged = base_df.merge(cur_df, on="symbol", how="outer").fillna(0.0)
        merged["delta"] = merged["scenario_net_pnl"] - merged["baseline_net_pnl"]
        merged = merged.sort_values("delta").reset_index(drop=True)
        print(f"[{scenario}]")
        _print_df(merged)
        print()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cost/slippage sensitivity analysis for full backtest")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE), help="Universe symbols")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR), help="Daily CSV directory")
    parser.add_argument("--initial-equity", type=float, default=100_000.0, help="Per-symbol base equity")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    data_dir = Path(args.data_dir)

    _validate_preconditions(symbols, base_dir=data_dir)

    summary_df, regime_map, symbol_map = run_sensitivity(
        symbols=symbols,
        data_dir=data_dir,
        initial_equity=args.initial_equity,
    )
    print_report(summary_df, regime_map, symbol_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
