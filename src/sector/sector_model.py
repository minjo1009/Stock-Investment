from __future__ import annotations

import pandas as pd

from backtest.analysis_sector import SYMBOL_TO_SECTOR


def map_symbol_to_sector(symbol: str) -> str:
    return SYMBOL_TO_SECTOR.get(str(symbol).strip().upper(), "UNMAPPED")


def build_sector_snapshot(frames: dict[str, pd.DataFrame], *, lookback: int = 20) -> dict[str, dict[str, float | int]]:
    sector_rows: dict[str, list[dict[str, float]]] = {}
    for symbol, frame in sorted(frames.items()):
        if frame.empty:
            continue
        sector = map_symbol_to_sector(symbol)
        ordered = frame.sort_values("timestamp").reset_index(drop=True)
        window = ordered.tail(max(lookback, 5))
        close = window["close"].astype(float)

        if len(close) < 2:
            momentum = 0.0
            volatility = 0.0
        else:
            momentum = float(close.iloc[-1] / close.iloc[0] - 1.0) if float(close.iloc[0]) > 0 else 0.0
            volatility = float(close.pct_change().std(ddof=0))
            if pd.isna(volatility):
                volatility = 0.0
        sector_rows.setdefault(sector, []).append({"momentum": momentum, "volatility": volatility})

    snapshot: dict[str, dict[str, float | int]] = {}
    for sector, rows in sector_rows.items():
        df = pd.DataFrame(rows)
        snapshot[sector] = {
            "sector_return_20d": float(df["momentum"].mean()),
            "sector_volatility": float(df["volatility"].mean()),
            "strength_score": float(df["momentum"].mean() - 0.5 * df["volatility"].mean()),
            "symbol_count": int(len(rows)),
        }

    ranked = sorted(snapshot.items(), key=lambda item: float(item[1]["strength_score"]), reverse=True)
    for rank, (sector, values) in enumerate(ranked, start=1):
        values["sector_strength_rank"] = rank
    return snapshot
