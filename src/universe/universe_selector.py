from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class UniverseFilterConfig:
    min_avg_dollar_volume: float = 25_000_000.0
    min_volatility: float = 0.012


def build_universe_snapshot(frames: dict[str, pd.DataFrame], *, lookback: int = 20) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for symbol, frame in sorted(frames.items()):
        if frame.empty:
            continue
        ordered = frame.sort_values("timestamp").reset_index(drop=True)
        window = ordered.tail(max(lookback, 5)).copy()
        close = window["close"].astype(float)
        volume = window["volume"].astype(float)
        avg_dollar_volume = float((close * volume).mean())
        volatility = float(close.pct_change().std(ddof=0))

        momentum_window = ordered.tail(max(lookback, 2))
        if len(momentum_window) < 2:
            momentum = 0.0
        else:
            start = float(momentum_window["close"].iloc[0])
            end = float(momentum_window["close"].iloc[-1])
            momentum = (end / start - 1.0) if start > 0 else 0.0

        rows.append(
            {
                "symbol": symbol,
                "avg_dollar_volume": avg_dollar_volume,
                "volatility": volatility if pd.notna(volatility) else 0.0,
                "momentum": momentum if pd.notna(momentum) else 0.0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=["symbol", "avg_dollar_volume", "volatility", "momentum"])
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def filter_universe_snapshot(
    snapshot: pd.DataFrame,
    *,
    config: UniverseFilterConfig | None = None,
) -> pd.DataFrame:
    cfg = config or UniverseFilterConfig()
    if snapshot.empty:
        return snapshot.copy()

    mask = (snapshot["avg_dollar_volume"] >= cfg.min_avg_dollar_volume) & (snapshot["volatility"] >= cfg.min_volatility)
    filtered = snapshot.loc[mask].copy()
    return filtered.sort_values("symbol").reset_index(drop=True)
