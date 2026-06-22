from __future__ import annotations

import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return OHLCV frame with EMA/MACD/RSI columns added.

    Added columns:
    - ema20, ema50, ema200
    - macd, macd_signal, macd_hist
    - rsi14
    """
    if df.empty:
        return df.copy()
    if "close" not in df.columns:
        return df.copy()

    out = df.copy().sort_values("timestamp").reset_index(drop=True) if "timestamp" in df.columns else df.copy()
    close = pd.to_numeric(out["close"], errors="coerce")

    out["ema20"] = close.ewm(span=20, adjust=False).mean()
    out["ema50"] = close.ewm(span=50, adjust=False).mean()
    out["ema200"] = close.ewm(span=200, adjust=False).mean()

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    out["rsi14"] = pd.to_numeric(rsi, errors="coerce").fillna(50.0)

    return out
