from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load_trades(path: str | Path = "data/backtest/trades.json") -> pd.DataFrame:
    """Load TradeResult records from exported quick-backtest JSON."""
    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(f"trades file not found: {json_path}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("trades", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    if not isinstance(rows, list) or not rows:
        raise ValueError("trades payload is empty")

    df = pd.DataFrame(rows)
    required = ["trade_id", "symbol", "entry_time", "actual_pnl", "holding_time"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"missing required trade columns: {', '.join(missing)}")

    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    if "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")

    numeric_cols = ["actual_pnl", "expected_pnl", "holding_time"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["entry_time", "actual_pnl"])
    if df.empty:
        raise ValueError("no valid trades after normalization")
    return df.sort_values("entry_time").reset_index(drop=True)


def analyze_by_symbol(trades: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        trades.groupby("symbol", as_index=False)
        .agg(
            total_pnl=("actual_pnl", "sum"),
            trade_count=("actual_pnl", "count"),
            win_count=("actual_pnl", lambda s: int((s > 0).sum())),
            avg_pnl=("actual_pnl", "mean"),
        )
        .sort_values("total_pnl", ascending=False)
        .reset_index(drop=True)
    )
    grouped["win_rate"] = (grouped["win_count"] / grouped["trade_count"]) * 100.0
    return grouped[["symbol", "total_pnl", "trade_count", "win_rate", "avg_pnl"]]


def analyze_by_time(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    month_key = trades["entry_time"].dt.strftime("%Y-%m")
    year_key = trades["entry_time"].dt.strftime("%Y")

    monthly = (
        trades.assign(year_month=month_key)
        .groupby("year_month", as_index=False)
        .agg(total_pnl=("actual_pnl", "sum"), trade_count=("actual_pnl", "count"))
        .sort_values("year_month")
        .reset_index(drop=True)
    )

    yearly = (
        trades.assign(year=year_key)
        .groupby("year", as_index=False)
        .agg(total_pnl=("actual_pnl", "sum"), trade_count=("actual_pnl", "count"))
        .sort_values("year")
        .reset_index(drop=True)
    )

    return monthly, yearly


def analyze_distribution(trades: pd.DataFrame) -> dict[str, float | int]:
    pnl = trades["actual_pnl"]
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    return {
        "win_trades_count": int((pnl > 0).sum()),
        "loss_trades_count": int((pnl < 0).sum()),
        "avg_win": float(wins.mean()) if not wins.empty else 0.0,
        "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
        "max_win": float(pnl.max()) if not pnl.empty else 0.0,
        "max_loss": float(pnl.min()) if not pnl.empty else 0.0,
    }


def analyze_holding_time(trades: pd.DataFrame) -> dict[str, float]:
    holding = pd.to_numeric(trades["holding_time"], errors="coerce").dropna()
    if holding.empty:
        return {
            "avg_holding_time": 0.0,
            "median_holding_time": 0.0,
            "holding_pnl_corr": 0.0,
        }

    aligned = trades.loc[holding.index, ["holding_time", "actual_pnl"]].copy()
    corr = aligned["holding_time"].corr(aligned["actual_pnl"]) if len(aligned) > 1 else 0.0
    corr_value = 0.0 if pd.isna(corr) else float(corr)
    return {
        "avg_holding_time": float(holding.mean()),
        "median_holding_time": float(holding.median()),
        "holding_pnl_corr": corr_value,
    }


def top_winners_losers(trades: pd.DataFrame, *, n: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    winners = trades.sort_values("actual_pnl", ascending=False).head(n)
    losers = trades.sort_values("actual_pnl", ascending=True).head(n)
    cols = ["trade_id", "symbol", "entry_time", "actual_pnl", "holding_time"]
    return winners[cols].reset_index(drop=True), losers[cols].reset_index(drop=True)


def worst_drawdown_period(trades: pd.DataFrame) -> dict[str, float | str]:
    if trades.empty:
        return {
            "max_drawdown": 0.0,
            "peak_time": "-",
            "trough_time": "-",
        }

    ordered = trades.sort_values("entry_time").reset_index(drop=True)
    equity = ordered["actual_pnl"].cumsum()
    running_peak = equity.cummax()
    drawdown = running_peak - equity
    idx = int(drawdown.idxmax())
    peak_idx = int(equity[: idx + 1].idxmax())

    return {
        "max_drawdown": float(drawdown.iloc[idx]),
        "peak_time": str(ordered.iloc[peak_idx]["entry_time"]),
        "trough_time": str(ordered.iloc[idx]["entry_time"]),
    }


def _print_dataframe(df: pd.DataFrame, *, max_rows: int = 20) -> None:
    if df.empty:
        print("(no rows)")
        return
    print(df.head(max_rows).to_string(index=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze quick backtest TradeResult output")
    parser.add_argument("--path", type=str, default="data/backtest/trades.json", help="Path to trades.json")
    parser.add_argument("--top", type=int, default=5, help="Top winners/losers rows")
    args = parser.parse_args(argv)

    trades = load_trades(args.path)

    symbol_perf = analyze_by_symbol(trades)
    monthly, yearly = analyze_by_time(trades)
    distribution = analyze_distribution(trades)
    holding = analyze_holding_time(trades)
    winners, losers = top_winners_losers(trades, n=max(1, args.top))
    dd = worst_drawdown_period(trades)

    print("=== SYMBOL PERFORMANCE ===")
    _print_dataframe(symbol_perf)
    print()

    print("=== MONTHLY PERFORMANCE ===")
    _print_dataframe(monthly)
    print()

    print("=== YEARLY PERFORMANCE ===")
    _print_dataframe(yearly)
    print()

    print("=== TRADE DISTRIBUTION ===")
    print(f"Win trades count: {distribution['win_trades_count']}")
    print(f"Loss trades count: {distribution['loss_trades_count']}")
    print(f"Avg win: {distribution['avg_win']:.4f}")
    print(f"Avg loss: {distribution['avg_loss']:.4f}")
    print(f"Max win: {distribution['max_win']:.4f}")
    print(f"Max loss: {distribution['max_loss']:.4f}")
    print()

    print("=== HOLDING TIME ANALYSIS ===")
    print(f"Avg holding time (sec): {holding['avg_holding_time']:.2f}")
    print(f"Median holding time (sec): {holding['median_holding_time']:.2f}")
    print(f"Holding time vs PnL corr: {holding['holding_pnl_corr']:.4f}")
    print()

    print("=== TOP WINNERS ===")
    _print_dataframe(winners, max_rows=max(1, args.top))
    print()

    print("=== TOP LOSERS ===")
    _print_dataframe(losers, max_rows=max(1, args.top))
    print()

    print("=== WORST DRAWDOWN PERIOD ===")
    print(f"Max drawdown: {dd['max_drawdown']:.4f}")
    print(f"Peak time: {dd['peak_time']}")
    print(f"Trough time: {dd['trough_time']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
