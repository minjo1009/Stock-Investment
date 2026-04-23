from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd


DEFAULT_US_UNIVERSE: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "NFLX",
    "COST",
    "AVGO",
    "QCOM",
)

DEFAULT_BASE_DIR = Path("data/raw/us_daily")
REQUIRED_COLUMNS: tuple[str, ...] = ("timestamp", "open", "high", "low", "close", "volume", "symbol")


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_daily_bars(symbol: str, *, base_dir: str | Path = DEFAULT_BASE_DIR) -> pd.DataFrame:
    """Load one symbol's daily OHLCV CSV into a normalized DataFrame.

    Required schema:
    - timestamp, open, high, low, close, volume, symbol
    Optional:
    - adj_close
    """
    normalized_symbol = _normalize_symbol(symbol)
    csv_path = Path(base_dir) / f"{normalized_symbol}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"daily data not found: {csv_path}")

    df = pd.read_csv(csv_path)
    return _normalize_daily_dataframe(df, symbol=normalized_symbol)


def load_universe_daily_bars(
    symbols: list[str],
    *,
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> dict[str, pd.DataFrame]:
    """Load multiple symbols into {symbol: DataFrame}."""
    result: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        normalized_symbol = _normalize_symbol(symbol)
        result[normalized_symbol] = load_daily_bars(normalized_symbol, base_dir=base_dir)
    return result


def load_bars_for_quick_backtest(
    *,
    symbol: str,
    csv_path: str | None = None,
    years: int = 2,
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> list[Bar]:
    """Compatibility helper for quick backtest engine.

    Priority:
    1) Explicit CSV path
    2) Symbol CSV from base_dir
    3) Deterministic local sample fallback
    """
    years = max(1, years)

    if csv_path:
        path = Path(csv_path)
        if path.exists():
            df = pd.read_csv(path)
            normalized = _normalize_daily_dataframe(df, symbol=_normalize_symbol(symbol))
            clipped = _clip_df_years(normalized, years=years)
            return _to_bars(clipped)

    try:
        df = load_daily_bars(symbol, base_dir=base_dir)
        clipped = _clip_df_years(df, years=years)
        return _to_bars(clipped)
    except (FileNotFoundError, ValueError):
        return _generate_sample_bars(years=years)


def _normalize_daily_dataframe(df: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    if df.empty:
        raise ValueError("daily CSV is empty")

    out = df.copy()
    out.columns = [str(col).strip().lower() for col in out.columns]

    if "adj close" in out.columns and "adj_close" not in out.columns:
        out = out.rename(columns={"adj close": "adj_close"})
    if "date" in out.columns and "timestamp" not in out.columns:
        out = out.rename(columns={"date": "timestamp"})
    if "datetime" in out.columns and "timestamp" not in out.columns:
        out = out.rename(columns={"datetime": "timestamp"})

    if "symbol" not in out.columns:
        out["symbol"] = symbol

    missing = [col for col in REQUIRED_COLUMNS if col not in out.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    out["symbol"] = out["symbol"].astype(str).str.upper()
    out = out[out["symbol"] == symbol].copy()
    if out.empty:
        raise ValueError(f"no rows for symbol={symbol}")

    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")
    out = out.dropna(subset=["timestamp"])
    if out.empty:
        raise ValueError("all timestamps are invalid")

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=numeric_cols)

    out = out.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    out = out.reset_index(drop=True)
    if out.empty:
        raise ValueError("no valid OHLCV rows after normalization")

    select_cols = ["timestamp", "open", "high", "low", "close", "volume", "symbol"]
    if "adj_close" in out.columns:
        select_cols.append("adj_close")
    return out[select_cols]


def _clip_df_years(df: pd.DataFrame, *, years: int) -> pd.DataFrame:
    years = max(1, years)
    cutoff = df["timestamp"].max() - pd.Timedelta(days=365 * years)
    clipped = df[df["timestamp"] >= cutoff].copy()
    return clipped if not clipped.empty else df


def _to_bars(df: pd.DataFrame) -> list[Bar]:
    bars: list[Bar] = []
    for row in df.itertuples(index=False):
        ts = row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        else:
            ts = ts.astimezone(UTC)
        bars.append(
            Bar(
                timestamp=ts,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
        )
    return bars


def _normalize_symbol(symbol: str) -> str:
    value = str(symbol).strip().upper()
    if not value:
        raise ValueError("symbol is required")
    return value


def _generate_sample_bars(*, years: int) -> list[Bar]:
    years = max(1, years)
    total_days = years * 252
    today = datetime.now(UTC).date()
    start = today - timedelta(days=int(total_days * 1.6))

    trade_dates: list[date] = []
    cursor = start
    while len(trade_dates) < total_days:
        if cursor.weekday() < 5:
            trade_dates.append(cursor)
        cursor += timedelta(days=1)

    prev_close = 100.0
    bars: list[Bar] = []
    for idx, day in enumerate(trade_dates):
        drift = 0.0011
        wave = 0.006 * ((idx % 18) - 9) / 9.0
        breakout_boost = 0.032 if idx % 29 == 0 and idx > 40 else 0.0
        shock = -0.025 if idx % 67 == 0 and idx > 0 else 0.0
        ret = drift + wave + shock + breakout_boost

        open_px = max(1.0, prev_close * (1 + (0.0015 * ((idx % 7) - 3) / 3.0)))
        close_px = max(1.0, prev_close * (1 + ret))
        high_pad = 0.001 if breakout_boost > 0 else (0.008 + 0.002 * ((idx % 5) / 5.0))
        low_pad = 0.008 + 0.002 * (((idx + 2) % 5) / 5.0)
        high_px = max(open_px, close_px) * (1 + high_pad)
        low_px = min(open_px, close_px) * (1 - low_pad)
        volume = 1_600_000 + (idx % 20) * 40_000

        bars.append(
            Bar(
                timestamp=datetime(day.year, day.month, day.day, tzinfo=UTC),
                open=open_px,
                high=high_px,
                low=low_px,
                close=close_px,
                volume=float(volume),
            )
        )
        prev_close = close_px

    return bars
