from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from backtest import engine_full
    from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
    from portfolio.allocator import AllocationConfig, allocate_equal_weight
    from sector.sector_model import map_symbol_to_sector
    from integration.kis_client import KISClient
    from strategy.conditions import condition_snapshot, prepare_condition_frame
    from universe.ranking import rank_universe
    from universe.universe_selector import build_universe_snapshot, filter_universe_snapshot
except ModuleNotFoundError:  # pragma: no cover - unittest imports through src.app.
    from src.backtest import engine_full
    from src.backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
    from src.portfolio.allocator import AllocationConfig, allocate_equal_weight
    from src.sector.sector_model import map_symbol_to_sector
    from src.integration.kis_client import KISClient
    from src.strategy.conditions import condition_snapshot, prepare_condition_frame
    from src.universe.ranking import rank_universe
    from src.universe.universe_selector import build_universe_snapshot, filter_universe_snapshot

THEME_UNIVERSE_CSV = Path("data/raw/theme_universe_10x7.csv")
RAW_INTRADAY_ROOT = Path("data/raw/us_intraday")
THEME_UNIVERSE_SCOPE = "theme_10x7"
KIS_SYMBOL_EXCHANGE_HINTS = {
    "BA": "NYSE",
    "CRM": "NYSE",
    "EMR": "NYSE",
    "ESTC": "NYSE",
    "ETN": "NYSE",
    "F": "NYSE",
    "GD": "NYSE",
    "GE": "NYSE",
    "GEV": "NYSE",
    "GM": "NYSE",
    "IR": "NYSE",
    "LLY": "NYSE",
    "LMT": "NYSE",
    "NEE": "NYSE",
    "NET": "NYSE",
    "NOC": "NYSE",
    "NOW": "NYSE",
    "NVO": "NYSE",
    "ORCL": "NYSE",
    "PH": "NYSE",
    "PWR": "NYSE",
    "ROK": "NYSE",
    "RTX": "NYSE",
    "S": "NYSE",
    "SNOW": "NYSE",
    "TSM": "NYSE",
    "UBER": "NYSE",
    "VRT": "NYSE",
    "VST": "NYSE",
}


def load_theme_universe_symbols(path: Path = THEME_UNIVERSE_CSV) -> list[str]:
    if not path.exists():
        return list(DEFAULT_US_UNIVERSE)
    try:
        frame = pd.read_csv(path)
    except Exception:
        return list(DEFAULT_US_UNIVERSE)
    if "symbol" not in frame.columns:
        return list(DEFAULT_US_UNIVERSE)
    symbols = sorted({str(symbol).strip().upper() for symbol in frame["symbol"] if str(symbol).strip()})
    return symbols or list(DEFAULT_US_UNIVERSE)


def _load_env_file(path: Path) -> bool:
    if not path.exists():
        return False
    loaded = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value
            loaded = True
    return loaded


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_iso(ts: datetime | None = None) -> str:
    return (ts or _utc_now()).isoformat().replace("+00:00", "Z")


def _floor_5m(ts: datetime) -> datetime:
    minute = (ts.minute // 5) * 5
    return ts.replace(minute=minute, second=0, microsecond=0)


def _is_kis_rate_limit_error(exc: Exception) -> bool:
    message = str(exc)
    return "EGW00201" in message or "초당 거래건수" in message or "rate" in message.lower()


def _is_kis_empty_quote_error(exc: Exception) -> bool:
    return "Could not parse current price" in str(exc)


def _exchange_sequence(symbol: str, default_exchange: str) -> list[str]:
    preferred = KIS_SYMBOL_EXCHANGE_HINTS.get(symbol.upper(), default_exchange)
    sequence = [preferred, default_exchange, "NASD", "NYSE", "AMEX"]
    result: list[str] = []
    for exchange in sequence:
        normalized = str(exchange or "").strip().upper()
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _get_current_price_for_exchange(kis: KISClient, symbol: str, exchange: str) -> float:
    original_exchange = kis.exchange_code
    try:
        kis.exchange_code = exchange
        return float(kis.get_current_price(symbol))
    finally:
        kis.exchange_code = original_exchange


def _get_current_price_with_retry(
    kis: KISClient,
    symbol: str,
    *,
    max_attempts: int = 3,
    base_sleep_sec: float = 0.7,
) -> float:
    attempts = max(1, int(max_attempts))
    errors: list[str] = []
    for exchange in _exchange_sequence(symbol, kis.exchange_code):
        for attempt in range(1, attempts + 1):
            try:
                return _get_current_price_for_exchange(kis, symbol, exchange)
            except Exception as exc:
                errors.append(f"{exchange}:{exc}")
                if _is_kis_rate_limit_error(exc) and attempt < attempts:
                    time.sleep(max(0.0, float(base_sleep_sec)) * attempt)
                    continue
                if _is_kis_empty_quote_error(exc):
                    break
                raise
    raise RuntimeError(f"KIS price lookup failed across exchanges for {symbol}: {' | '.join(errors)}")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _init_tables(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS market_ticks (
                tick_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                last_price REAL NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
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
            CREATE TABLE IF NOT EXISTS indicator_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                bar_end_ts TEXT NOT NULL,
                close REAL,
                ma20 REAL,
                ma50 REAL,
                ma200 REAL,
                breakout_high_20 REAL,
                breakout_condition INTEGER NOT NULL,
                ma_condition INTEGER NOT NULL,
                entry_allowed INTEGER NOT NULL,
                data_fresh INTEGER NOT NULL,
                insufficient_history INTEGER NOT NULL,
                action TEXT NOT NULL,
                side TEXT NOT NULL,
                reason TEXT NOT NULL,
                score REAL NOT NULL,
                candidate_rank INTEGER NOT NULL,
                selected_for_portfolio INTEGER NOT NULL DEFAULT 0,
                source_price_ts TEXT,
                source_price REAL,
                source_type TEXT,
                freshness_age_sec REAL,
                stale_reason TEXT
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
        con.execute("CREATE INDEX IF NOT EXISTS idx_market_ticks_ts ON market_ticks(timestamp)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_bars_5m_symbol_ts ON market_bars_5m(symbol, bar_start_ts)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_indicators_created ON indicator_snapshots(created_at)")
        cols = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(indicator_snapshots)").fetchall()
        }
        if "selected_for_portfolio" not in cols:
            con.execute(
                "ALTER TABLE indicator_snapshots ADD COLUMN selected_for_portfolio INTEGER NOT NULL DEFAULT 0"
            )
        optional_cols = {
            "source_price_ts": "TEXT",
            "source_price": "REAL",
            "source_type": "TEXT",
            "freshness_age_sec": "REAL",
            "stale_reason": "TEXT",
        }
        for col, col_type in optional_cols.items():
            if col not in cols:
                con.execute(f"ALTER TABLE indicator_snapshots ADD COLUMN {col} {col_type}")
        con.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON data_collection_events(created_at)")
        con.commit()
    finally:
        con.close()


def _record_event(db_path: str, *, symbol: str, level: str, message: str) -> None:
    created_at = _utc_iso()
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


def _upsert_tick_and_bar(db_path: str, *, symbol: str, price: float, ts: datetime) -> None:
    symbol = symbol.upper()
    ts_iso = _utc_iso(ts)
    tick_id = f"{symbol}:{ts_iso}"
    bar_start = _floor_5m(ts)
    bar_end = bar_start.replace(second=59, microsecond=0) + pd.Timedelta(minutes=4)
    bar_start_iso = _utc_iso(bar_start)
    bar_end_iso = _utc_iso(bar_end.to_pydatetime() if hasattr(bar_end, "to_pydatetime") else bar_end)
    bar_id = f"{symbol}:{bar_start_iso}"

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO market_ticks(tick_id, timestamp, symbol, last_price, source, created_at)
            VALUES(?,?,?,?,?,?)
            """,
            (tick_id, ts_iso, symbol, float(price), "KIS_QUOTE", ts_iso),
        )
        row = con.execute("SELECT * FROM market_bars_5m WHERE bar_id = ?", (bar_id,)).fetchone()
        if row is None:
            con.execute(
                """
                INSERT INTO market_bars_5m(
                    bar_id, symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume, tick_count, source, last_updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    bar_id,
                    symbol,
                    bar_start_iso,
                    bar_end_iso,
                    float(price),
                    float(price),
                    float(price),
                    float(price),
                    0.0,
                    1,
                    "KIS_QUOTE",
                    ts_iso,
                ),
            )
        else:
            new_high = max(float(row["high"]), float(price))
            new_low = min(float(row["low"]), float(price))
            con.execute(
                """
                UPDATE market_bars_5m
                SET high = ?, low = ?, close = ?, tick_count = ?, last_updated_at = ?
                WHERE bar_id = ?
                """,
                (
                    new_high,
                    new_low,
                    float(price),
                    int(row["tick_count"]) + 1,
                    ts_iso,
                    bar_id,
                ),
            )
        con.commit()
    finally:
        con.close()


def _load_recent_bars(db_path: str, symbol: str, limit: int = 320) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT bar_start_ts AS timestamp, open, high, low, close, volume, symbol
            FROM market_bars_5m
            WHERE symbol = ?
            ORDER BY bar_start_ts DESC
            LIMIT ?
            """,
            (symbol.upper(), limit),
        ).fetchall()
    finally:
        con.close()
    if not rows:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "symbol"])
    df = pd.DataFrame([dict(r) for r in rows])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


def _safe_load_daily_bars(symbol: str, *, base_dir: Path) -> pd.DataFrame:
    try:
        return load_daily_bars(symbol, base_dir=base_dir)
    except FileNotFoundError:
        return pd.DataFrame()


def _load_raw_intraday_bars(symbol: str, *, raw_dir: Path = RAW_INTRADAY_ROOT, limit: int = 320) -> pd.DataFrame:
    path = raw_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if frame.empty or not required.issubset(set(frame.columns)):
        return pd.DataFrame()
    frame = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp")
    if frame.empty:
        return pd.DataFrame()
    frame = frame.tail(limit).reset_index(drop=True)
    frame["symbol"] = symbol.upper()
    return frame


def _latest_tick(db_path: str, symbol: str) -> dict[str, Any] | None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT timestamp, last_price, source
            FROM market_ticks
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (symbol.upper(),),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        con.close()


def _upsert_indicator_snapshots(db_path: str, created_at: str, ranked: list[dict[str, Any]]) -> None:
    con = sqlite3.connect(db_path)
    try:
        for idx, row in enumerate(ranked, start=1):
            snapshot_id = f"{created_at}:{row['symbol']}"
            con.execute(
                """
                INSERT OR REPLACE INTO indicator_snapshots(
                    snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200, breakout_high_20,
                    breakout_condition, ma_condition, entry_allowed, data_fresh, insufficient_history,
                    action, side, reason, score, candidate_rank, selected_for_portfolio,
                    source_price_ts, source_price, source_type, freshness_age_sec, stale_reason
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    snapshot_id,
                    created_at,
                    str(row["symbol"]),
                    str(row["bar_end_ts"]),
                    float(row["close"]),
                    float(row["ma20"]),
                    float(row["ma50"]),
                    float(row["ma200"]),
                    float(row["breakout_high_20"]),
                    1 if bool(row["breakout_condition"]) else 0,
                    1 if bool(row["ma_condition"]) else 0,
                    1 if bool(row["entry_allowed"]) else 0,
                    1 if bool(row["data_fresh"]) else 0,
                    1 if bool(row["insufficient_history"]) else 0,
                    str(row["action"]),
                    str(row["side"]),
                    str(row["reason"]),
                    float(row["score"]),
                    idx,
                    1 if bool(row.get("selected_for_portfolio")) else 0,
                    str(row.get("source_price_ts") or ""),
                    float(row.get("source_price") or 0.0),
                    str(row.get("source_type") or ""),
                    float(row.get("freshness_age_sec") or 0.0),
                    str(row.get("stale_reason") or ""),
                ),
            )
        con.commit()
    finally:
        con.close()


def _build_indicator_input(
    *,
    symbol: str,
    bars_5m: pd.DataFrame,
    base_dir: Path,
    latest_price: float,
    now: datetime,
) -> pd.DataFrame:
    if len(bars_5m) >= 60:
        return bars_5m.copy()

    daily = _safe_load_daily_bars(symbol, base_dir=base_dir)
    if daily.empty and latest_price > 0:
        return pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp(now),
                    "open": latest_price,
                    "high": latest_price,
                    "low": latest_price,
                    "close": latest_price,
                    "volume": 0.0,
                    "symbol": symbol,
                }
            ]
        )
    if daily.empty:
        raw_intraday = _load_raw_intraday_bars(symbol)
        if not raw_intraday.empty and latest_price > 0:
            appended = pd.DataFrame(
                [
                    {
                        "timestamp": pd.Timestamp(now),
                        "open": latest_price,
                        "high": latest_price,
                        "low": latest_price,
                        "close": latest_price,
                        "volume": 0.0,
                        "symbol": symbol,
                    }
                ]
            )
            return pd.concat([raw_intraday, appended], ignore_index=True).sort_values("timestamp").reset_index(drop=True)
        if not raw_intraday.empty:
            return raw_intraday
        return bars_5m.copy()
    daily = daily[["timestamp", "open", "high", "low", "close", "volume", "symbol"]].copy()
    appended = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp(now),
                "open": latest_price,
                "high": latest_price,
                "low": latest_price,
                "close": latest_price,
                "volume": 0.0,
                "symbol": symbol,
            }
        ]
    )
    merged = pd.concat([daily, appended], ignore_index=True)
    merged["timestamp"] = pd.to_datetime(merged["timestamp"], utc=True, errors="coerce")
    merged = merged.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return merged


def _compute_row(symbol: str, indicator_input_df: pd.DataFrame, now: datetime) -> dict[str, Any]:
    frame = prepare_condition_frame(indicator_input_df)
    if frame.empty:
        return {
            "symbol": symbol,
            "bar_end_ts": _utc_iso(now),
            "close": 0.0,
            "ma20": 0.0,
            "ma50": 0.0,
            "ma200": 0.0,
            "breakout_high_20": 0.0,
            "breakout_condition": False,
            "ma_condition": False,
            "entry_allowed": False,
            "data_fresh": False,
            "insufficient_history": True,
            "action": "HOLD",
            "side": "NONE",
            "reason": "INSUFFICIENT_DATA",
            "score": -1.0,
            "source_price_ts": _utc_iso(now),
            "source_price": 0.0,
            "source_type": "INSUFFICIENT_DATA",
            "freshness_age_sec": 0.0,
            "stale_reason": "INSUFFICIENT_DATA",
        }
    idx = len(frame) - 1
    snap = condition_snapshot(frame, idx)
    row = frame.iloc[idx]
    bar_ts = pd.to_datetime(row.get("timestamp"), utc=True, errors="coerce")
    if pd.isna(bar_ts):
        bar_ts = now
    age_minutes = (now - bar_ts.to_pydatetime()).total_seconds() / 60.0
    freshness_age_sec = (now - bar_ts.to_pydatetime()).total_seconds()
    data_fresh = age_minutes <= 15.0
    insufficient = len(frame) < 60

    close = _safe_float(row.get("close"))
    ma20 = _safe_float(row.get("ma20"))
    ma50 = _safe_float(row.get("ma50"))
    ma200 = _safe_float(row.get("ma200"))
    breakout_high_20 = _safe_float(row.get("breakout_high_20"))
    breakout = bool(snap.get("breakout_condition"))
    ma_cond = bool(snap.get("ma_condition"))
    entry_allowed = bool(data_fresh and not insufficient and breakout and ma_cond)

    breakout_strength = ((close - breakout_high_20) / breakout_high_20) if breakout_high_20 > 0 else 0.0
    trend_strength = ((ma20 - ma50) / ma50) if ma50 > 0 else 0.0
    score = (breakout_strength * 0.7) + (trend_strength * 0.3)
    if not data_fresh:
        score -= 1.0
    if insufficient:
        score -= 1.0

    reason_parts: list[str] = []
    if breakout:
        reason_parts.append("BREAKOUT")
    if ma_cond:
        reason_parts.append("MA_TREND")
    if not data_fresh:
        reason_parts.append("STALE")
    if insufficient:
        reason_parts.append("INSUFFICIENT_DATA")
    if not reason_parts:
        reason_parts.append("NO_ENTRY")
    return {
        "symbol": symbol,
        "bar_end_ts": _utc_iso(bar_ts.to_pydatetime()),
        "close": close,
        "ma20": ma20,
        "ma50": ma50,
        "ma200": ma200,
        "breakout_high_20": breakout_high_20,
        "breakout_condition": breakout,
        "ma_condition": ma_cond,
        "entry_allowed": entry_allowed,
        "data_fresh": data_fresh,
        "insufficient_history": insufficient,
        "action": "ENTER" if entry_allowed else "HOLD",
        "side": "BUY" if entry_allowed else "NONE",
        "reason": " + ".join(reason_parts),
        "score": score,
        "source_price_ts": _utc_iso(bar_ts.to_pydatetime()),
        "source_price": close,
        "source_type": "KIS_CURRENT_PRICE_APPENDED" if data_fresh else "HISTORICAL_DAILY",
        "freshness_age_sec": max(0.0, float(freshness_age_sec)),
        "stale_reason": "" if data_fresh else f"BAR_AGE_MINUTES_{age_minutes:.1f}",
    }


def _build_canonical_runtime_rows(
    *,
    symbols: list[str],
    base_dir: Path,
    db_path: str,
    now: datetime,
    max_positions: int = 3,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Build runtime snapshot rows with the same logic as backtest selection/entry.

    This intentionally reuses backtest universe/ranking/allocation + engine_full entry signal.
    """
    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        frame = _safe_load_daily_bars(symbol, base_dir=base_dir)
        if frame.empty:
            continue
        frames[symbol] = frame

    ranked = pd.DataFrame()
    if frames:
        snapshot = build_universe_snapshot(frames)
        filtered = filter_universe_snapshot(snapshot)
        ranked = rank_universe(filtered)
    selected_symbols = ranked["symbol"].head(max(1, int(max_positions))).tolist() if not ranked.empty else []
    if not selected_symbols:
        selected_symbols = sorted(frames.keys())[: max(1, int(max_positions))]

    allocations = allocate_equal_weight(
        selected_symbols,
        config=AllocationConfig(max_positions=max_positions, max_exposure_per_symbol=1.0),
    )
    allocation_by_symbol = {
        str(item["symbol"]): float(item["allocation_pct"])
        for item in allocations
    }

    score_by_symbol: dict[str, float] = {}
    if not ranked.empty:
        for _, row in ranked.iterrows():
            score_by_symbol[str(row["symbol"])] = float(row.get("score", 0.0))

    rows: list[dict[str, Any]] = []
    for rank_idx, symbol in enumerate(sorted({s.upper() for s in symbols}), start=1):
        tick = _latest_tick(db_path, symbol)
        latest_price = _safe_float(tick.get("last_price") if tick else None, default=0.0)
        bars_5m = _load_recent_bars(db_path, symbol)
        raw_intraday = _load_raw_intraday_bars(symbol)
        if latest_price > 0:
            indicator_input = _build_indicator_input(
                symbol=symbol,
                bars_5m=bars_5m,
                base_dir=base_dir,
                latest_price=latest_price,
                now=now,
            )
        elif symbol not in frames and bars_5m.empty and raw_intraday.empty:
            computed = _compute_row(symbol, pd.DataFrame(), now)
            computed["reason"] = "MISSING_SOURCE"
            computed["source_type"] = "MISSING_SOURCE"
            computed["source_price_ts"] = ""
            computed["freshness_age_sec"] = 0.0
            computed["stale_reason"] = "MISSING_SOURCE"
            rows.append(
                {
                    "symbol": symbol,
                    "bar_end_ts": computed["bar_end_ts"],
                    "close": computed["close"],
                    "ma20": computed["ma20"],
                    "ma50": computed["ma50"],
                    "ma200": computed["ma200"],
                    "breakout_high_20": computed["breakout_high_20"],
                    "breakout_condition": computed["breakout_condition"],
                    "ma_condition": computed["ma_condition"],
                    "entry_allowed": False,
                    "data_fresh": False,
                    "insufficient_history": True,
                    "action": "HOLD",
                    "side": "NONE",
                    "reason": "MISSING_SOURCE",
                    "score": -999.0,
                    "candidate_rank": rank_idx,
                    "selected_for_portfolio": False,
                    "sector": map_symbol_to_sector(symbol),
                    "source_price_ts": "",
                    "source_price": 0.0,
                    "source_type": "MISSING_SOURCE",
                    "freshness_age_sec": 0.0,
                    "stale_reason": "MISSING_SOURCE",
                }
            )
            continue
        elif symbol in frames:
            indicator_input = frames[symbol]
        elif not raw_intraday.empty:
            indicator_input = raw_intraday
        else:
            indicator_input = bars_5m
        computed = _compute_row(symbol, indicator_input, now)
        if symbol not in frames and not raw_intraday.empty and latest_price <= 0:
            computed["source_type"] = "RAW_INTRADAY_HISTORY"
            if not computed["data_fresh"]:
                computed["stale_reason"] = "RAW_INTRADAY_HISTORY_STALE"
        frame = prepare_condition_frame(indicator_input)
        if frame.empty:
            continue

        selected_for_portfolio = symbol in selected_symbols
        entry_allowed = bool(computed["entry_allowed"] and selected_for_portfolio)
        side = "BUY" if entry_allowed else "NONE"
        action = "ENTER" if entry_allowed else "HOLD"
        reason = str(computed["reason"])

        if selected_for_portfolio:
            if not computed["data_fresh"]:
                reason = "STALE"
            elif not entry_allowed:
                reason = "NO_ENTRY"
        else:
            entry_allowed = False
            side = "NONE"
            action = "HOLD"
            reason = "NOT_SELECTED_BY_PORTFOLIO"

        rows.append(
            {
                "symbol": symbol,
                "bar_end_ts": computed["bar_end_ts"],
                "close": computed["close"],
                "ma20": computed["ma20"],
                "ma50": computed["ma50"],
                "ma200": computed["ma200"],
                "breakout_high_20": computed["breakout_high_20"],
                "breakout_condition": computed["breakout_condition"],
                "ma_condition": computed["ma_condition"],
                "entry_allowed": bool(entry_allowed),
                "data_fresh": bool(computed["data_fresh"]),
                "insufficient_history": bool(computed["insufficient_history"]),
                "action": action,
                "side": side,
                "reason": reason,
                "score": float(score_by_symbol.get(symbol, -1.0)),
                "candidate_rank": rank_idx,
                "selected_for_portfolio": selected_for_portfolio,
                "sector": map_symbol_to_sector(symbol),
                "source_price_ts": computed["source_price_ts"],
                "source_price": computed["source_price"],
                "source_type": computed["source_type"],
                "freshness_age_sec": computed["freshness_age_sec"],
                "stale_reason": computed["stale_reason"],
            }
        )

    rows.sort(key=lambda x: float(x.get("score", -1.0)), reverse=True)
    selected_sectors = sorted({map_symbol_to_sector(s) for s in selected_symbols})
    return rows, selected_symbols, selected_sectors


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 089 - Market Data / 5m Bars / Indicator Snapshots")
    lines.append("")
    lines.append(f"- timestamp: {payload['timestamp']}")
    lines.append(f"- universe_scope: {payload.get('universe_scope', '')}")
    lines.append(f"- expected_universe_count: {payload.get('expected_universe_count', payload['symbol_count'])}")
    lines.append(f"- evaluated_symbols: {payload['evaluated_count']}/{payload['symbol_count']}")
    lines.append(f"- enter_candidates: {payload['enter_candidates']}")
    lines.append(f"- selected_symbols: {payload.get('selected_symbols', [])}")
    lines.append(f"- selected_sectors: {payload.get('selected_sectors', [])}")
    lines.append(f"- data_fresh_ratio: {payload['data_fresh_ratio']:.4f}")
    lines.append(f"- missing_bar_ratio: {payload['missing_bar_ratio']:.4f}")
    lines.append("")
    lines.append("## Top Candidates")
    for row in payload.get("top_candidates", []):
        lines.append(
            f"- {row['symbol']} | action={row['action']} | score={row['score']:.6f} | "
            f"fresh={row['data_fresh']} | reason={row['reason']}"
        )
    if not payload.get("top_candidates"):
        lines.append("- (none)")
    lines.append("")
    lines.append("## Warnings")
    for msg in payload.get("warnings", []):
        lines.append(f"- {msg}")
    if not payload.get("warnings"):
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 089: collect 5m market bars and indicator snapshots")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--env-file", type=str, default="config/kis_paper.env")
    parser.add_argument("--symbols", type=str, default="")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_089/task_089_market_signal_refresh.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_089/task_089_market_signal_refresh.md")
    parser.add_argument("--base-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--quote-pacing-sec", type=float, default=0.35)
    parser.add_argument("--quote-retry-attempts", type=int, default=4)
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    _init_tables(args.db_path)
    now = _utc_now()

    explicit_symbols = bool(args.symbols.strip())
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] if explicit_symbols else load_theme_universe_symbols()
    universe_scope = "explicit_symbols" if explicit_symbols else THEME_UNIVERSE_SCOPE
    created_at = _utc_iso(now)
    warnings: list[str] = []

    try:
        kis = KISClient.from_env()
    except Exception as exc:
        ranked, selected_symbols, selected_sectors = _build_canonical_runtime_rows(
            symbols=symbols,
            base_dir=Path(args.base_dir),
            db_path=args.db_path,
            now=now,
            max_positions=3,
        )
        _upsert_indicator_snapshots(args.db_path, created_at=created_at, ranked=ranked)
        evaluated = len(ranked)
        fresh_count = sum(1 for r in ranked if bool(r.get("data_fresh")))
        missing_count = sum(1 for r in ranked if bool(r.get("source_type") == "MISSING_SOURCE"))
        enter_candidates = [r for r in ranked if bool(r.get("entry_allowed"))]
        payload = {
            "timestamp": created_at,
            "db_path": args.db_path,
            "universe_scope": universe_scope,
            "expected_universe_count": len(symbols),
            "symbol_count": len(symbols),
            "evaluated_count": evaluated,
            "enter_candidates": len(enter_candidates),
            "selected_symbols": selected_symbols,
            "selected_sectors": selected_sectors,
            "data_fresh_ratio": (fresh_count / evaluated) if evaluated else 0.0,
            "missing_bar_ratio": (missing_count / evaluated) if evaluated else 1.0,
            "top_candidates": ranked[:10],
            "warnings": [f"KIS_CLIENT_INIT_FAILED: {exc}"],
            "failures": [str(exc)],
        }
        out_json = Path(args.json_out)
        out_md = Path(args.md_out)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        out_md.write_text(_to_markdown(payload), encoding="utf-8")
        print(f"written_json={out_json}")
        print(f"written_md={out_md}")
        print(f"enter_candidates={len(enter_candidates)}")
        return 0

    failures: list[str] = []
    for idx, symbol in enumerate(symbols):
        if idx > 0 and args.quote_pacing_sec > 0:
            time.sleep(float(args.quote_pacing_sec))
        try:
            price = _get_current_price_with_retry(
                kis,
                symbol,
                max_attempts=args.quote_retry_attempts,
                base_sleep_sec=max(0.35, float(args.quote_pacing_sec)),
            )
            _upsert_tick_and_bar(args.db_path, symbol=symbol, price=float(price), ts=now)
        except Exception as exc:
            failures.append(f"{symbol}:{exc}")
            _record_event(args.db_path, symbol=symbol, level="WARN", message=f"refresh failed: {exc}")

    ranked, selected_symbols, selected_sectors = _build_canonical_runtime_rows(
        symbols=symbols,
        base_dir=Path(args.base_dir),
        db_path=args.db_path,
        now=now,
        max_positions=3,
    )
    _upsert_indicator_snapshots(args.db_path, created_at=created_at, ranked=ranked)

    evaluated = len(ranked)
    fresh_count = sum(1 for r in ranked if bool(r.get("data_fresh")))
    missing_count = sum(1 for r in ranked if bool(r.get("insufficient_history")))
    enter_candidates = [r for r in ranked if bool(r.get("entry_allowed"))]
    for row in ranked:
        if row["insufficient_history"]:
            warnings.append(f"{row['symbol']}:INSUFFICIENT_HISTORY")

    payload = {
        "timestamp": created_at,
        "db_path": args.db_path,
        "universe_scope": universe_scope,
        "expected_universe_count": len(symbols),
        "symbol_count": len(symbols),
        "evaluated_count": evaluated,
        "enter_candidates": len(enter_candidates),
        "selected_symbols": selected_symbols,
        "selected_sectors": selected_sectors,
        "data_fresh_ratio": (fresh_count / evaluated) if evaluated else 0.0,
        "missing_bar_ratio": (missing_count / evaluated) if evaluated else 1.0,
        "top_candidates": ranked[:10],
        "warnings": sorted(set(warnings)),
        "failures": failures,
    }
    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    out_md.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={out_json}")
    print(f"written_md={out_md}")
    print(f"enter_candidates={len(enter_candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
