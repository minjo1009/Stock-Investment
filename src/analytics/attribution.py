from __future__ import annotations

from typing import Any

import pandas as pd


def group_net_pnl_by(results: list[Any], key: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        trade = item.trade
        metadata = item.metadata if isinstance(item.metadata, dict) else {}
        if key == "symbol":
            bucket = trade.symbol
        elif key == "regime":
            bucket = item.regime
        else:
            bucket = metadata.get(key, "UNKNOWN")
        rows.append({"bucket": bucket, "net_pnl": float(item.net_pnl)})
    if not rows:
        return pd.DataFrame(columns=["bucket", "net_pnl"])
    df = pd.DataFrame(rows)
    return df.groupby("bucket", as_index=False).agg(net_pnl=("net_pnl", "sum")).sort_values("net_pnl")


def drawdown_segments_from_results(results: list[Any], top_n: int = 3) -> list[dict[str, Any]]:
    if not results:
        return []
    frame = pd.DataFrame(
        [
            {
                "exit_time": item.trade.exit_time,
                "symbol": item.trade.symbol,
                "net_pnl": float(item.net_pnl),
                "exit_rule": (item.metadata or {}).get("exit_rule", "UNKNOWN"),
                "regime": item.regime,
            }
            for item in results
        ]
    )
    frame["exit_time"] = pd.to_datetime(frame["exit_time"], utc=True, errors="coerce")
    frame = frame.sort_values("exit_time").reset_index(drop=True)
    frame["equity"] = frame["net_pnl"].cumsum()
    frame["peak"] = frame["equity"].cummax()
    frame["drawdown"] = frame["peak"] - frame["equity"]

    segments: list[dict[str, Any]] = []
    for row in frame.nlargest(top_n, "drawdown").itertuples(index=False):
        trough_time = row.exit_time
        subset = frame[frame["exit_time"] <= trough_time]
        peak_idx = subset["equity"].idxmax()
        peak_time = frame.loc[peak_idx, "exit_time"]
        seg = frame[(frame["exit_time"] >= peak_time) & (frame["exit_time"] <= trough_time)]
        segments.append(
            {
                "peak_time": str(peak_time),
                "trough_time": str(trough_time),
                "drawdown": float(row.drawdown),
                "trade_count": int(len(seg)),
                "symbol_losses": seg.groupby("symbol", as_index=False)["net_pnl"].sum().sort_values("net_pnl").head(5).to_dict(orient="records"),
                "exit_rule_losses": seg.groupby("exit_rule", as_index=False)["net_pnl"].sum().sort_values("net_pnl").to_dict(orient="records"),
                "regime_losses": seg.groupby("regime", as_index=False)["net_pnl"].sum().sort_values("net_pnl").to_dict(orient="records"),
            }
        )
    return segments
