from __future__ import annotations

import argparse

import pandas as pd

from backtest.analysis_exclusion import load_trades, with_regime


SYMBOL_TO_SECTOR: dict[str, str] = {
    "AAPL": "XLK",
    "MSFT": "XLK",
    "NVDA": "XLK",
    "AVGO": "XLK",
    "QCOM": "XLK",
    "AMD": "XLK",
    "GOOGL": "XLC",
    "META": "XLC",
    "NFLX": "XLC",
    "AMZN": "XLY",
    "TSLA": "XLY",
    "COST": "XLP",
}


def assign_sectors(trades: pd.DataFrame, *, mapping: dict[str, str] | None = None) -> pd.DataFrame:
    mapper = mapping or SYMBOL_TO_SECTOR
    out = trades.copy()
    out["sector"] = out["symbol"].map(mapper).fillna("UNMAPPED")
    return out


def analyze_sector_performance(trades: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        trades.groupby("sector", as_index=False)
        .agg(
            total_pnl=("actual_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            trade_count=("net_pnl", "count"),
            avg_pnl=("net_pnl", "mean"),
        )
        .sort_values("net_pnl", ascending=True)
        .reset_index(drop=True)
    )
    return grouped[["sector", "total_pnl", "net_pnl", "trade_count", "avg_pnl"]]


def analyze_sector_regime(trades: pd.DataFrame) -> pd.DataFrame:
    return (
        trades.groupby(["sector", "regime"], as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"))
        .sort_values(["sector", "regime"])
        .reset_index(drop=True)
    )


def identify_weak_sectors(sector_perf: pd.DataFrame) -> pd.DataFrame:
    weak = sector_perf[(sector_perf["net_pnl"] < 0) | (sector_perf["avg_pnl"] < 0)].copy()
    if weak.empty:
        return weak

    weak["reason"] = weak.apply(
        lambda row: ",".join(
            reason
            for reason, cond in (
                ("net_pnl<0", float(row["net_pnl"]) < 0),
                ("avg_pnl<0", float(row["avg_pnl"]) < 0),
            )
            if cond
        ),
        axis=1,
    )
    return weak[["sector", "net_pnl", "trade_count", "avg_pnl", "reason"]].sort_values("net_pnl").reset_index(drop=True)


def _profit_factor(pnls: pd.Series) -> float:
    wins = pnls[pnls > 0].sum()
    losses = pnls[pnls < 0].sum()
    if losses == 0:
        return float("inf")
    return float(wins / abs(losses))


def estimate_filter_effect(trades: pd.DataFrame, weak_sectors: pd.DataFrame) -> dict[str, float | int]:
    weak_set = set(weak_sectors["sector"].tolist())
    before = trades.copy()
    after = trades[~trades["sector"].isin(weak_set)].copy()

    before_pf = _profit_factor(before["net_pnl"]) if not before.empty else 0.0
    after_pf = _profit_factor(after["net_pnl"]) if not after.empty else 0.0

    return {
        "before_trades": int(len(before)),
        "after_trades": int(len(after)),
        "removed_trades": int(len(before) - len(after)),
        "before_pnl": float(before["net_pnl"].sum()) if not before.empty else 0.0,
        "after_pnl": float(after["net_pnl"].sum()) if not after.empty else 0.0,
        "before_pf": before_pf,
        "after_pf": after_pf,
    }


def _pf_text(value: float) -> str:
    return "inf" if value == float("inf") else f"{value:.4f}"


def _print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sector feasibility analysis without rerunning backtest")
    parser.add_argument("--path", type=str, default="data/backtest/trades.json")
    parser.add_argument("--data-dir", type=str, default="data/raw/us_daily")
    args = parser.parse_args(argv)

    trades = load_trades(args.path)
    trades = with_regime(trades, data_dir=args.data_dir)
    trades = assign_sectors(trades)

    sector_perf = analyze_sector_performance(trades)
    sector_regime = analyze_sector_regime(trades)
    weak = identify_weak_sectors(sector_perf)
    effect = estimate_filter_effect(trades, weak)

    print("=== SECTOR PERFORMANCE ===")
    _print_df(sector_perf)
    print()

    print("=== SECTOR REGIME BREAKDOWN ===")
    _print_df(sector_regime)
    print()

    print("=== WEAK SECTORS ===")
    _print_df(weak)
    print()

    print("=== FILTER EFFECT (ESTIMATE) ===")
    print(f"Before PF: {_pf_text(float(effect['before_pf']))}")
    print(f"After PF: {_pf_text(float(effect['after_pf']))}")
    print(f"Before PnL: {float(effect['before_pnl']):.4f}")
    print(f"After PnL: {float(effect['after_pnl']):.4f}")
    print(f"Before Trades: {int(effect['before_trades'])}")
    print(f"After Trades: {int(effect['after_trades'])}")
    print(f"Removed Trades: {int(effect['removed_trades'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
