from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, load_daily_bars


def load_trades(path: str | Path = "data/backtest/trades.json") -> pd.DataFrame:
    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(f"trades file not found: {json_path}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    rows = payload.get("trades", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise ValueError("trades payload is empty")

    df = pd.DataFrame(rows)
    required = ["trade_id", "symbol", "entry_time", "actual_pnl"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["actual_pnl"] = pd.to_numeric(df["actual_pnl"], errors="coerce")
    if "net_pnl" in df.columns:
        df["net_pnl"] = pd.to_numeric(df["net_pnl"], errors="coerce")
    else:
        df["net_pnl"] = df["actual_pnl"]
    df = df.dropna(subset=["entry_time", "actual_pnl", "net_pnl"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("no valid trades after normalization")
    return df


def _infer_regime_for_trade(symbol: str, entry_time: pd.Timestamp, *, base_dir: Path) -> str:
    try:
        prices = load_daily_bars(symbol, base_dir=base_dir)
    except Exception:
        return "UNKNOWN"
    if prices.empty:
        return "UNKNOWN"

    prices = prices[["timestamp", "close"]].copy()
    prices["ma200"] = prices["close"].rolling(200).mean()
    dt = pd.Timestamp(entry_time)
    row = prices[prices["timestamp"] <= dt].tail(1)
    if row.empty:
        return "UNKNOWN"
    close_value = float(row.iloc[0]["close"])
    ma200 = row.iloc[0]["ma200"]
    if pd.isna(ma200):
        return "UNKNOWN"
    return "BULL" if close_value >= float(ma200) else "BEAR"


def with_regime(trades: pd.DataFrame, *, data_dir: str | Path = DEFAULT_BASE_DIR) -> pd.DataFrame:
    out = trades.copy()
    if "regime" in out.columns and out["regime"].notna().any():
        out["regime"] = out["regime"].astype(str).str.upper()
        return out

    base_dir = Path(data_dir)
    out["regime"] = [
        _infer_regime_for_trade(str(sym), ts, base_dir=base_dir)
        for sym, ts in zip(out["symbol"], out["entry_time"], strict=False)
    ]
    return out


def analyze_symbol_performance(trades: pd.DataFrame) -> pd.DataFrame:
    total_loss = abs(trades[trades["net_pnl"] < 0]["net_pnl"].sum())

    grouped = (
        trades.groupby("symbol", as_index=False)
        .agg(
            total_pnl=("actual_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            trade_count=("net_pnl", "count"),
            win_count=("net_pnl", lambda s: int((s > 0).sum())),
            avg_pnl=("net_pnl", "mean"),
        )
        .sort_values("net_pnl", ascending=True)
        .reset_index(drop=True)
    )
    grouped["win_rate"] = (grouped["win_count"] / grouped["trade_count"]) * 100.0
    grouped["pnl_per_trade"] = grouped["net_pnl"] / grouped["trade_count"]

    if total_loss > 0:
        grouped["loss_contribution_pct"] = grouped["net_pnl"].apply(
            lambda value: (abs(value) / total_loss) * 100.0 if value < 0 else 0.0
        )
    else:
        grouped["loss_contribution_pct"] = 0.0

    return grouped[
        [
            "symbol",
            "total_pnl",
            "net_pnl",
            "trade_count",
            "win_rate",
            "avg_pnl",
            "pnl_per_trade",
            "loss_contribution_pct",
        ]
    ]


def analyze_symbol_regime(trades: pd.DataFrame) -> pd.DataFrame:
    return (
        trades.groupby(["symbol", "regime"], as_index=False)
        .agg(total_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"))
        .sort_values(["symbol", "regime"])
        .reset_index(drop=True)
    )


def identify_exclusion_candidates(symbol_perf: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in symbol_perf.itertuples(index=False):
        reasons: list[str] = []
        if float(row.net_pnl) < 0:
            reasons.append("net_pnl<0")
        if int(row.trade_count) >= 5:
            reasons.append("trade_count>=5")
        if float(row.win_rate) < 35.0:
            reasons.append("win_rate<35")
        if float(row.avg_pnl) < 0:
            reasons.append("avg_pnl<0")

        if len(reasons) >= 2:
            rows.append(
                {
                    "symbol": row.symbol,
                    "net_pnl": row.net_pnl,
                    "trade_count": row.trade_count,
                    "win_rate": row.win_rate,
                    "avg_pnl": row.avg_pnl,
                    "reason": ",".join(reasons),
                }
            )

    return pd.DataFrame(rows).sort_values("net_pnl").reset_index(drop=True) if rows else pd.DataFrame()


def analyze_regime_weakness(trades: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        trades.groupby("regime", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"), win_count=("net_pnl", lambda s: int((s > 0).sum())))
        .sort_values("regime")
        .reset_index(drop=True)
    )
    grouped["win_rate"] = (grouped["win_count"] / grouped["trade_count"]) * 100.0
    return grouped[["regime", "net_pnl", "trade_count", "win_rate"]]


def _print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze structural exclusion candidates by symbol and regime")
    parser.add_argument("--path", type=str, default="data/backtest/trades.json")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    args = parser.parse_args(argv)

    trades = load_trades(args.path)
    trades = with_regime(trades, data_dir=args.data_dir)

    symbol_perf = analyze_symbol_performance(trades)
    regime_breakdown = analyze_symbol_regime(trades)
    candidates = identify_exclusion_candidates(symbol_perf)
    regime_perf = analyze_regime_weakness(trades)

    print("=== WORST SYMBOLS ===")
    _print_df(symbol_perf.sort_values("net_pnl").head(10))
    print()

    print("=== REGIME BREAKDOWN ===")
    _print_df(regime_breakdown)
    print()

    print("=== REGIME PERFORMANCE ===")
    _print_df(regime_perf)
    print()

    print("=== EXCLUSION CANDIDATES ===")
    _print_df(candidates)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
