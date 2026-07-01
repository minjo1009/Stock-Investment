from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd

from src.data.env_loader import load_repo_env


DB_PATH = Path(os.environ.get("TRADING_DB_PATH", "trading.db"))
DEFAULT_INTERVAL = "5m"
DEFAULT_CHUNK_DAYS = 20
DEFAULT_RETRY_LIMIT = 3
MARKET_OPEN = dt_time(hour=14, minute=30)
MARKET_CLOSE = dt_time(hour=21, minute=0)
NY_TZ = ZoneInfo("America/New_York")
FULL_SESSION_MIN_BARS = 60
SUPPORTED_BAR_INTERVALS: dict[str, tuple[str, timedelta, str]] = {
    "5m": ("5Min", timedelta(minutes=5), "ALPACA_HISTORICAL_5M"),
    "1d": ("1Day", timedelta(days=1), "ALPACA_HISTORICAL_1D"),
}

REQUIRED_BAR_COLUMNS: tuple[str, ...] = (
    "symbol",
    "bar_start_ts",
    "bar_end_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "tick_count",
    "source",
)


@dataclass(frozen=True)
class IntradayBackfillConfig:
    provider_name: str
    db_path: Path
    interval: str
    symbols: tuple[str, ...]
    start_date: date
    end_date: date
    chunk_days: int = DEFAULT_CHUNK_DAYS
    retry_limit: int = DEFAULT_RETRY_LIMIT
    skip_existing: bool = True


class IntradayBarsProvider(ABC):
    @abstractmethod
    def fetch_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = DEFAULT_INTERVAL,
    ) -> pd.DataFrame:
        raise NotImplementedError


class AlpacaHistoricalBarsProvider(IntradayBarsProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str = "https://data.alpaca.markets/v2/stocks/bars",
        feed: str = "iex",
        adjustment: str = "raw",
        page_limit: int = 10_000,
    ) -> None:
        load_repo_env()
        self.api_key = api_key or os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
        self.secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
        self.base_url = base_url
        self.feed = feed
        self.adjustment = adjustment
        self.page_limit = page_limit

    def fetch_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = DEFAULT_INTERVAL,
    ) -> pd.DataFrame:
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
        normalized_interval = normalize_bar_interval(interval)
        if normalized_interval not in SUPPORTED_BAR_INTERVALS:
            raise ValueError(f"unsupported interval: {interval}")

        timeframe, _, _ = SUPPORTED_BAR_INTERVALS[normalized_interval]
        start_ts = interval_start_ts(start_date, normalized_interval)
        end_ts = interval_end_ts(end_date, normalized_interval)
        page_token: str | None = None
        rows: list[dict[str, Any]] = []

        while True:
            params = {
                "symbols": symbol.upper(),
                "timeframe": timeframe,
                "start": start_ts,
                "end": end_ts,
                "limit": str(self.page_limit),
                "adjustment": self.adjustment,
                "feed": self.feed,
            }
            if page_token:
                params["page_token"] = page_token
            payload = self._request_json(params)
            symbol_rows = payload.get("bars", {}).get(symbol.upper(), [])
            rows.extend(symbol_rows)
            page_token = payload.get("next_page_token")
            if not page_token:
                break

        return self._normalize_rows(symbol.upper(), rows, interval=normalized_interval)

    def _request_json(self, params: dict[str, str]) -> dict[str, Any]:
        query = urlencode(params)
        request = Request(
            f"{self.base_url}?{query}",
            headers={
                "APCA-API-KEY-ID": self.api_key or "",
                "APCA-API-SECRET-KEY": self.secret_key or "",
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _normalize_rows(symbol: str, rows: Iterable[dict[str, Any]], *, interval: str = DEFAULT_INTERVAL) -> pd.DataFrame:
        normalized_interval = normalize_bar_interval(interval)
        if normalized_interval not in SUPPORTED_BAR_INTERVALS:
            raise ValueError(f"unsupported interval: {interval}")
        _, bar_duration, source = SUPPORTED_BAR_INTERVALS[normalized_interval]
        normalized: list[dict[str, Any]] = []
        for row in rows:
            bar_start = pd.to_datetime(row.get("t"), utc=True, errors="coerce")
            if pd.isna(bar_start):
                continue
            bar_start_dt = bar_start.to_pydatetime() if hasattr(bar_start, "to_pydatetime") else bar_start
            bar_end_dt = bar_start_dt + bar_duration - timedelta(seconds=1)
            normalized.append(
                {
                    "symbol": symbol,
                    "bar_start_ts": _utc_iso(bar_start_dt),
                    "bar_end_ts": _utc_iso(bar_end_dt),
                    "open": float(row.get("o", 0.0)),
                    "high": float(row.get("h", 0.0)),
                    "low": float(row.get("l", 0.0)),
                    "close": float(row.get("c", 0.0)),
                    "volume": float(row.get("v", 0.0)),
                    "tick_count": int(row.get("n", 0) or 0),
                    "source": source,
                }
            )
        df = pd.DataFrame(normalized, columns=list(REQUIRED_BAR_COLUMNS))
        return ensure_bar_schema(df)


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat().replace("+00:00", "Z")


def normalize_bar_interval(interval: str) -> str:
    value = str(interval or "").strip().lower()
    aliases = {
        "5min": "5m",
        "5minute": "5m",
        "5minutes": "5m",
        "1day": "1d",
        "1d": "1d",
        "daily": "1d",
        "day": "1d",
    }
    return aliases.get(value, value)


def interval_start_ts(day: date, interval: str) -> str:
    normalized_interval = normalize_bar_interval(interval)
    if normalized_interval == "1d":
        return _utc_iso(datetime.combine(day, dt_time.min, tzinfo=UTC))
    return session_start_ts(day)


def interval_end_ts(day: date, interval: str) -> str:
    normalized_interval = normalize_bar_interval(interval)
    if normalized_interval == "1d":
        return _utc_iso(datetime.combine(day + timedelta(days=1), dt_time.min, tzinfo=UTC) - timedelta(seconds=1))
    return session_end_ts(day)


def session_start_ts(day: date) -> str:
    local_open = datetime.combine(day, dt_time(hour=9, minute=30), tzinfo=NY_TZ)
    return _utc_iso(local_open)


def session_end_ts(day: date) -> str:
    local_close = datetime.combine(day, dt_time(hour=16, minute=0), tzinfo=NY_TZ)
    return _utc_iso(local_close)


def ensure_market_bars_table(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS market_bars_5m (
                bar_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                bar_start_ts TEXT NOT NULL,
                bar_end_ts TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                tick_count INTEGER NOT NULL,
                source TEXT NOT NULL,
                last_updated_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS data_collection_events (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_bars_5m_symbol_ts ON market_bars_5m(symbol, bar_start_ts)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON data_collection_events(created_at)")
        con.commit()
    finally:
        con.close()


def ensure_bar_schema(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=list(REQUIRED_BAR_COLUMNS))
    df = frame.copy()
    for col in REQUIRED_BAR_COLUMNS:
        if col not in df.columns:
            if col == "tick_count":
                df[col] = 0
            elif col == "source":
                df[col] = "UNKNOWN"
            else:
                df[col] = math.nan
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["bar_start_ts"] = pd.to_datetime(df["bar_start_ts"], utc=True, errors="coerce")
    df["bar_end_ts"] = pd.to_datetime(df["bar_end_ts"], utc=True, errors="coerce")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["tick_count"] = pd.to_numeric(df["tick_count"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["symbol", "bar_start_ts", "bar_end_ts", "open", "high", "low", "close", "volume"]).copy()
    if df.empty:
        return pd.DataFrame(columns=list(REQUIRED_BAR_COLUMNS))
    df["bar_start_ts"] = df["bar_start_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["bar_end_ts"] = df["bar_end_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["source"] = df["source"].astype(str)
    df = df.sort_values(["symbol", "bar_start_ts"]).drop_duplicates(subset=["symbol", "bar_start_ts"], keep="last")
    return df.loc[:, list(REQUIRED_BAR_COLUMNS)].reset_index(drop=True)


def upsert_market_bars(db_path: Path, frame: pd.DataFrame) -> int:
    bars = ensure_bar_schema(frame)
    if bars.empty:
        return 0
    ensure_market_bars_table(db_path)
    now = _utc_iso(datetime.now(UTC))
    rows = [
        (
            f"{row.symbol}:{row.bar_start_ts}",
            row.symbol,
            row.bar_start_ts,
            row.bar_end_ts,
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            float(row.volume),
            int(row.tick_count),
            row.source,
            now,
        )
        for row in bars.itertuples(index=False)
    ]
    con = sqlite3.connect(db_path)
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO market_bars_5m(
                bar_id, symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume, tick_count, source, last_updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        con.commit()
    finally:
        con.close()
    return len(rows)


def record_data_collection_event(db_path: Path, *, symbol: str, level: str, message: str) -> None:
    ensure_market_bars_table(db_path)
    created_at = _utc_iso(datetime.now(UTC))
    event_id = f"{symbol}:{created_at}:{level}"
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO data_collection_events(event_id, created_at, symbol, level, message)
            VALUES(?,?,?,?,?)
            """,
            (event_id, created_at, symbol, level, message),
        )
        con.commit()
    finally:
        con.close()


def load_market_bars_5m(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame(columns=["symbol", "bar_start_ts", "bar_end_ts", "bar_date", "source"])
    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume, tick_count, source
            FROM market_bars_5m
            ORDER BY symbol, bar_start_ts
            """,
            con,
        )
    finally:
        con.close()
    if df.empty:
        return pd.DataFrame(columns=["symbol", "bar_start_ts", "bar_end_ts", "bar_date", "source"])
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["bar_start_ts"] = pd.to_datetime(df["bar_start_ts"], utc=True, errors="coerce")
    df["bar_end_ts"] = pd.to_datetime(df["bar_end_ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["symbol", "bar_start_ts", "bar_end_ts"]).reset_index(drop=True)
    df["bar_date"] = df["bar_start_ts"].dt.strftime("%Y-%m-%d")
    return df


def covered_dates_by_symbol(db_path: Path, *, min_bars: int = FULL_SESSION_MIN_BARS) -> dict[str, set[str]]:
    df = load_market_bars_5m(db_path)
    if df.empty:
        return {}
    counts = (
        df.groupby(["symbol", "bar_date"], dropna=False)
        .size()
        .reset_index(name="bar_count")
    )
    counts = counts[counts["bar_count"] >= int(min_bars)].copy()
    result: dict[str, set[str]] = {}
    for symbol, scoped in counts.groupby("symbol"):
        result[str(symbol)] = set(scoped["bar_date"].astype(str))
    return result


def split_contiguous_date_blocks(dates: Iterable[date], *, max_span_days: int) -> list[tuple[date, date]]:
    ordered = sorted(set(dates))
    if not ordered:
        return []
    blocks: list[tuple[date, date]] = []
    block_start = ordered[0]
    block_end = ordered[0]
    for current in ordered[1:]:
        contiguous = (current - block_end).days <= 1
        within_span = (current - block_start).days < max_span_days
        if contiguous and within_span:
            block_end = current
            continue
        blocks.append((block_start, block_end))
        block_start = current
        block_end = current
    blocks.append((block_start, block_end))
    return blocks


def fetch_with_retries(
    provider: IntradayBarsProvider,
    *,
    symbol: str,
    start_date: date,
    end_date: date,
    interval: str,
    retry_limit: int,
    sleep_seconds: float = 1.0,
) -> pd.DataFrame:
    attempts = max(int(retry_limit), 1)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return provider.fetch_bars(symbol, start_date, end_date, interval)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= attempts:
                break
            time.sleep(sleep_seconds)
    if last_error is None:
        raise RuntimeError("intraday fetch failed without an explicit exception")
    raise last_error
