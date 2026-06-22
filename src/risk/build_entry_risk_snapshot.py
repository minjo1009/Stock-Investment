from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


TASK_ID = "T603-6"
REPORT_DIR = Path("docs/reports/task_603_6_acceptance_promotion_program/program_b_entry_risk")
SNAPSHOT_TABLE = "entry_risk_snapshot"
MATCHING_POLICY = "EXACT_POSITION_ID_FROM_POSITION_LIFECYCLE_ONLY"
REAL_CAPITAL_STATUS = "FORBIDDEN"

REQUIRED_SNAPSHOT_COLUMNS = [
    "snapshot_id",
    "position_id",
    "symbol",
    "entry_time",
    "entry_price",
    "atr14",
    "stop_price",
    "take_profit_price",
    "vwap",
    "volume_ratio",
    "market_regime",
    "created_at",
]
EXTRA_SNAPSHOT_COLUMNS = [
    "source_block",
    "source_block_reason",
    "atr_source_status",
    "stop_tp_source_status",
    "vwap_source_status",
    "volume_ratio_source_status",
    "market_regime_source_status",
    "ohlc_bar_count",
    "matching_policy",
    "real_capital_status",
]
SNAPSHOT_COLUMNS = REQUIRED_SNAPSHOT_COLUMNS + EXTRA_SNAPSHOT_COLUMNS


@dataclass(frozen=True)
class EntryRiskRules:
    atr_period: int = 14
    stop_atr_multiple: float = 2.0
    take_profit_atr_multiple: float = 4.0


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _upper(value: object) -> str:
    return _text(value).upper()


def _float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def _positive_float(value: object) -> float | None:
    parsed = _float(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _iso(ts: pd.Timestamp | None) -> str | None:
    if ts is None:
        return None
    return ts.isoformat().replace("+00:00", "Z")


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _read_table(con: sqlite3.Connection, table: str) -> pd.DataFrame:
    if not _table_exists(con, table):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", con)


def _first_existing_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in frame.columns:
            return column
    return None


def _empty_snapshot_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=SNAPSHOT_COLUMNS)


def _normalize_bars(market_bars_5m: pd.DataFrame | None) -> pd.DataFrame:
    if market_bars_5m is None or market_bars_5m.empty:
        return pd.DataFrame()
    frame = market_bars_5m.copy()
    if "symbol" not in frame.columns:
        return pd.DataFrame()
    ts_column = _first_existing_column(frame, ["bar_end_ts", "timestamp", "created_at", "datetime", "date", "time"])
    if ts_column is None:
        return pd.DataFrame()
    frame["symbol"] = frame["symbol"].fillna("").astype(str).str.upper()
    frame["source_ts"] = pd.to_datetime(frame[ts_column], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close", "volume", "vwap", "volume_ratio", "relative_volume", "rel_volume", "rvol"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.loc[frame["symbol"].ne("") & frame["source_ts"].notna()].reset_index(drop=True)


def _normalize_timed_source(
    source: pd.DataFrame | None,
    timestamp_candidates: list[str],
) -> pd.DataFrame:
    if source is None or source.empty or "symbol" not in source.columns:
        return pd.DataFrame()
    frame = source.copy()
    ts_column = _first_existing_column(frame, timestamp_candidates)
    if ts_column is None:
        return pd.DataFrame()
    frame["symbol"] = frame["symbol"].fillna("").astype(str).str.upper()
    frame["source_ts"] = pd.to_datetime(frame[ts_column], utc=True, errors="coerce")
    return frame.loc[frame["symbol"].ne("") & frame["source_ts"].notna()].reset_index(drop=True)


def _atr14_for_entry(
    bars: pd.DataFrame,
    symbol: str,
    entry_ts: pd.Timestamp | None,
    *,
    period: int,
) -> tuple[float | None, int, str]:
    if entry_ts is None:
        return None, 0, "ATR_SOURCE_BLOCK_ENTRY_TIME_MISSING"
    if bars.empty:
        return None, 0, "ATR_SOURCE_BLOCK_NO_MARKET_BARS_5M_SOURCE"
    missing_columns = [column for column in ("high", "low", "close") if column not in bars.columns]
    if missing_columns:
        return None, 0, "ATR_SOURCE_BLOCK_OHLC_COLUMNS_MISSING"

    scoped = bars.loc[bars["symbol"].eq(symbol) & (bars["source_ts"] <= entry_ts)].copy()
    if scoped.empty:
        return None, 0, "ATR_SOURCE_BLOCK_NO_SYMBOL_BARS_BEFORE_ENTRY"
    for column in ("high", "low", "close"):
        scoped[column] = pd.to_numeric(scoped[column], errors="coerce")
    scoped = scoped.dropna(subset=["high", "low", "close", "source_ts"]).sort_values("source_ts")
    bar_count = int(len(scoped))
    required_bars = period + 1
    if bar_count < required_bars:
        return None, bar_count, "ATR_SOURCE_BLOCK_INSUFFICIENT_OHLC_BARS"

    window = scoped.tail(required_bars).copy()
    prev_close = window["close"].shift(1)
    true_range = pd.concat(
        [
            window["high"] - window["low"],
            (window["high"] - prev_close).abs(),
            (window["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1).iloc[1:]
    true_range = pd.to_numeric(true_range, errors="coerce").dropna()
    if len(true_range) < period:
        return None, bar_count, "ATR_SOURCE_BLOCK_INSUFFICIENT_TRUE_RANGE"
    atr = float(true_range.tail(period).mean())
    if pd.isna(atr) or atr <= 0:
        return None, bar_count, "ATR_SOURCE_BLOCK_INVALID_NONPOSITIVE_ATR"
    return round(atr, 6), bar_count, "OK"


def _latest_numeric_source_value(
    sources: list[tuple[str, pd.DataFrame]],
    symbol: str,
    entry_ts: pd.Timestamp | None,
    columns: list[str],
    source_name: str,
    *,
    require_positive: bool,
) -> tuple[float | None, str]:
    if entry_ts is None:
        return None, f"{source_name}_SOURCE_BLOCK_ENTRY_TIME_MISSING"
    any_source = False
    any_column = False
    for table_name, source in sources:
        if source.empty:
            continue
        any_source = True
        present_columns = [column for column in columns if column in source.columns]
        if not present_columns:
            continue
        any_column = True
        scoped = source.loc[source["symbol"].eq(symbol) & (source["source_ts"] <= entry_ts)].copy()
        if scoped.empty:
            continue
        scoped = scoped.sort_values("source_ts")
        for column in present_columns:
            values = pd.to_numeric(scoped[column], errors="coerce")
            if require_positive:
                values = values.where(values > 0)
            else:
                values = values.where(values.notna())
            usable = scoped.loc[values.notna()].copy()
            if not usable.empty:
                value = float(pd.to_numeric(usable.iloc[-1][column], errors="coerce"))
                return round(value, 6), f"OK:{table_name}.{column}"
    if not any_source:
        return None, f"{source_name}_SOURCE_BLOCK_NO_SOURCE"
    if not any_column:
        return None, f"{source_name}_SOURCE_BLOCK_COLUMN_MISSING"
    return None, f"{source_name}_SOURCE_BLOCK_NO_VALUE_BEFORE_ENTRY"


def _latest_text_source_value(
    sources: list[tuple[str, pd.DataFrame]],
    symbol: str,
    entry_ts: pd.Timestamp | None,
    columns: list[str],
    source_name: str,
) -> tuple[str | None, str]:
    if entry_ts is None:
        return None, f"{source_name}_SOURCE_BLOCK_ENTRY_TIME_MISSING"
    any_source = False
    any_column = False
    for table_name, source in sources:
        if source.empty:
            continue
        any_source = True
        present_columns = [column for column in columns if column in source.columns]
        if not present_columns:
            continue
        any_column = True
        scoped = source.loc[source["symbol"].eq(symbol) & (source["source_ts"] <= entry_ts)].copy()
        if scoped.empty:
            continue
        scoped = scoped.sort_values("source_ts")
        for column in present_columns:
            values = scoped[column].map(_text)
            usable = scoped.loc[values.ne("")].copy()
            if not usable.empty:
                return _text(usable.iloc[-1][column]), f"OK:{table_name}.{column}"
    if not any_source:
        return None, f"{source_name}_SOURCE_BLOCK_NO_SOURCE"
    if not any_column:
        return None, f"{source_name}_SOURCE_BLOCK_COLUMN_MISSING"
    return None, f"{source_name}_SOURCE_BLOCK_NO_VALUE_BEFORE_ENTRY"


def build_entry_risk_snapshot(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
    market_bars_5m: pd.DataFrame | list[dict[str, Any]] | None = None,
    indicator_snapshots: pd.DataFrame | list[dict[str, Any]] | None = None,
    *,
    rules: EntryRiskRules = EntryRiskRules(),
    created_at: str | None = None,
) -> pd.DataFrame:
    lifecycle = pd.DataFrame(position_lifecycle).copy()
    if lifecycle.empty:
        return _empty_snapshot_frame()

    bars = _normalize_bars(pd.DataFrame(market_bars_5m) if market_bars_5m is not None else pd.DataFrame())
    indicators = _normalize_timed_source(
        pd.DataFrame(indicator_snapshots) if indicator_snapshots is not None else pd.DataFrame(),
        ["created_at", "bar_end_ts", "source_price_ts", "timestamp"],
    )
    feature_sources = [("market_bars_5m", bars), ("indicator_snapshots", indicators)]
    created = created_at or utc_now()
    rows: list[dict[str, Any]] = []

    for index, position in lifecycle.reset_index(drop=True).iterrows():
        position_id = _text(position.get("position_id")) or f"ROW|{index + 1}"
        symbol = _upper(position.get("symbol"))
        entry_ts = _timestamp(position.get("entry_time"))
        entry_price = _positive_float(position.get("entry_price"))

        atr14, ohlc_bar_count, atr_status = _atr14_for_entry(
            bars,
            symbol,
            entry_ts,
            period=rules.atr_period,
        )
        if atr14 is not None and entry_price is not None:
            stop_price = round(entry_price - (rules.stop_atr_multiple * atr14), 6)
            take_profit_price = round(entry_price + (rules.take_profit_atr_multiple * atr14), 6)
            stop_tp_status = "OK"
        else:
            stop_price = None
            take_profit_price = None
            if entry_price is None:
                stop_tp_status = "STOP_TP_SOURCE_BLOCK_ENTRY_PRICE_MISSING"
            elif not atr_status.startswith("OK"):
                stop_tp_status = f"STOP_TP_SOURCE_BLOCK_{atr_status}"
            else:
                stop_tp_status = "STOP_TP_SOURCE_BLOCK_UNKNOWN"

        vwap, vwap_status = _latest_numeric_source_value(
            feature_sources,
            symbol,
            entry_ts,
            ["vwap", "entry_vwap", "vw_at_entry"],
            "VWAP",
            require_positive=True,
        )
        volume_ratio, volume_status = _latest_numeric_source_value(
            feature_sources,
            symbol,
            entry_ts,
            ["volume_ratio", "relative_volume", "rel_volume", "rvol"],
            "VOLUME_RATIO",
            require_positive=False,
        )
        market_regime, market_regime_status = _latest_text_source_value(
            feature_sources,
            symbol,
            entry_ts,
            ["market_regime", "regime", "market_state"],
            "MARKET_REGIME",
        )

        statuses = [atr_status, stop_tp_status, vwap_status, volume_status, market_regime_status]
        source_block_reasons = [status for status in statuses if not status.startswith("OK")]
        rows.append(
            {
                "snapshot_id": f"ENTRY_RISK|{position_id}",
                "position_id": position_id,
                "symbol": symbol,
                "entry_time": _iso(entry_ts),
                "entry_price": entry_price,
                "atr14": atr14,
                "stop_price": stop_price,
                "take_profit_price": take_profit_price,
                "vwap": vwap,
                "volume_ratio": volume_ratio,
                "market_regime": market_regime,
                "created_at": created,
                "source_block": int(bool(source_block_reasons)),
                "source_block_reason": ";".join(source_block_reasons),
                "atr_source_status": atr_status,
                "stop_tp_source_status": stop_tp_status,
                "vwap_source_status": vwap_status,
                "volume_ratio_source_status": volume_status,
                "market_regime_source_status": market_regime_status,
                "ohlc_bar_count": ohlc_bar_count,
                "matching_policy": MATCHING_POLICY,
                "real_capital_status": REAL_CAPITAL_STATUS,
            }
        )

    return pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS)


def ensure_entry_risk_snapshot_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS entry_risk_snapshot (
            snapshot_id TEXT PRIMARY KEY,
            position_id TEXT,
            symbol TEXT,
            entry_time TEXT,
            entry_price REAL,
            atr14 REAL,
            stop_price REAL,
            take_profit_price REAL,
            vwap REAL,
            volume_ratio REAL,
            market_regime TEXT,
            created_at TEXT,
            source_block INTEGER,
            source_block_reason TEXT,
            atr_source_status TEXT,
            stop_tp_source_status TEXT,
            vwap_source_status TEXT,
            volume_ratio_source_status TEXT,
            market_regime_source_status TEXT,
            ohlc_bar_count INTEGER,
            matching_policy TEXT,
            real_capital_status TEXT
        )
        """
    )
    existing = {row[1] for row in con.execute("PRAGMA table_info(entry_risk_snapshot)").fetchall()}
    column_types = {
        "snapshot_id": "TEXT",
        "position_id": "TEXT",
        "symbol": "TEXT",
        "entry_time": "TEXT",
        "entry_price": "REAL",
        "atr14": "REAL",
        "stop_price": "REAL",
        "take_profit_price": "REAL",
        "vwap": "REAL",
        "volume_ratio": "REAL",
        "market_regime": "TEXT",
        "created_at": "TEXT",
        "source_block": "INTEGER",
        "source_block_reason": "TEXT",
        "atr_source_status": "TEXT",
        "stop_tp_source_status": "TEXT",
        "vwap_source_status": "TEXT",
        "volume_ratio_source_status": "TEXT",
        "market_regime_source_status": "TEXT",
        "ohlc_bar_count": "INTEGER",
        "matching_policy": "TEXT",
        "real_capital_status": "TEXT",
    }
    for column, column_type in column_types.items():
        if column not in existing:
            con.execute(f"ALTER TABLE entry_risk_snapshot ADD COLUMN {column} {column_type}")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entry_risk_snapshot_position ON entry_risk_snapshot(position_id)")


def write_entry_risk_snapshot(con: sqlite3.Connection, snapshots: pd.DataFrame) -> None:
    ensure_entry_risk_snapshot_table(con)
    con.execute("DELETE FROM entry_risk_snapshot")
    if snapshots.empty:
        return
    frame = snapshots.reindex(columns=SNAPSHOT_COLUMNS).copy()
    values = [
        [None if pd.isna(value) else value for value in row]
        for row in frame.itertuples(index=False, name=None)
    ]
    placeholders = ",".join(["?"] * len(SNAPSHOT_COLUMNS))
    columns = ",".join(SNAPSHOT_COLUMNS)
    con.executemany(
        f"INSERT OR REPLACE INTO entry_risk_snapshot ({columns}) VALUES ({placeholders})",
        values,
    )


def build_entry_risk_snapshot_from_db(
    db_path: Path | str,
    *,
    rules: EntryRiskRules = EntryRiskRules(),
    write_table: bool = True,
    report_dir: Path | None = REPORT_DIR,
) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        market_bars_5m = _read_table(con, "market_bars_5m")
        indicator_snapshots = _read_table(con, "indicator_snapshots")
        snapshots = build_entry_risk_snapshot(
            position_lifecycle,
            market_bars_5m,
            indicator_snapshots,
            rules=rules,
        )
        if write_table:
            write_entry_risk_snapshot(con, snapshots)
            con.commit()
    finally:
        con.close()
    if report_dir is not None:
        write_entry_risk_snapshot_report(report_dir, snapshots)
    return snapshots


def write_entry_risk_snapshot_report(report_dir: Path, snapshots: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    total = int(len(snapshots))
    atr_ok = int(snapshots["atr_source_status"].astype(str).eq("OK").sum()) if not snapshots.empty else 0
    stop_populated = int(snapshots["stop_price"].notna().sum()) if not snapshots.empty else 0
    tp_populated = int(snapshots["take_profit_price"].notna().sum()) if not snapshots.empty else 0
    source_block = int(pd.to_numeric(snapshots.get("source_block", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not snapshots.empty else 0
    atr_blockers = [line for line in _status_lines(snapshots, "atr_source_status") if not line.startswith("OK=")]
    stop_tp_blockers = [line for line in _status_lines(snapshots, "stop_tp_source_status") if not line.startswith("OK=")]
    optional_blockers = _optional_status_lines(snapshots)
    lines = [
        "## Problem",
        "",
        "T603-6 Program B needs an entry risk snapshot table for every exact `position_lifecycle.position_id` without changing strategy, entry, universe, alpha, or live capital behavior.",
        "STOP and take-profit prices must come from real ATR14 source evidence only; missing OHLC evidence must remain null/source-blocked instead of approximated.",
        "",
        "## Evidence",
        "",
        f"- snapshot_rows={total}",
        f"- atr14_source_ok={atr_ok}",
        f"- stop_price_populated={stop_populated}",
        f"- take_profit_price_populated={tp_populated}",
        f"- source_block_rows={source_block}",
        f"- matching_policy={MATCHING_POLICY}",
        f"- real_capital_status={REAL_CAPITAL_STATUS}",
        "",
        "## Root Cause",
        "",
        "ATR14 is available only when `market_bars_5m` has at least 15 same-symbol OHLC bars at or before the entry timestamp.",
        "VWAP, volume ratio, and market regime are not inferred from adjacent fields; if no explicit source column exists, those fields remain null/source-blocked.",
        "",
        "## Fix Candidate",
        "",
        "Maintain the new `entry_risk_snapshot` builder and add actual source columns or source tables for VWAP, volume ratio, and market regime when those feeds are approved.",
        "For ATR or entry-price blockers, backfill real OHLC bars or exact entry-price source evidence before rerunning this task; do not use ATR approximations or symbol/date/price/time fallback.",
        "",
        "## Acceptance Impact",
        "",
        f"- Required table columns: {', '.join(REQUIRED_SNAPSHOT_COLUMNS)}",
        f"- ATR blockers: {'; '.join(atr_blockers) if atr_blockers else 'none'}",
        f"- STOP/TP blockers: {'; '.join(stop_tp_blockers) if stop_tp_blockers else 'none'}",
        f"- Optional source blockers: {'; '.join(optional_blockers) if optional_blockers else 'none'}",
        "Snapshot acceptance is decided by the validator metrics: snapshot_coverage, stop_price_populated, and take_profit_price_populated.",
    ]
    (report_dir / "entry_risk_snapshot_report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _status_lines(frame: pd.DataFrame, column: str) -> list[str]:
    if frame.empty or column not in frame.columns:
        return []
    counts = frame[column].fillna("").astype(str).value_counts().sort_index()
    return [f"{status}={int(count)}" for status, count in counts.items() if status]


def _optional_status_lines(frame: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    for column in ("vwap_source_status", "volume_ratio_source_status", "market_regime_source_status"):
        for line in _status_lines(frame, column):
            lines.append(f"{column}:{line}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    snapshots = build_entry_risk_snapshot_from_db(args.db_path, report_dir=args.report_dir)
    stop_count = int(snapshots["stop_price"].notna().sum()) if not snapshots.empty else 0
    tp_count = int(snapshots["take_profit_price"].notna().sum()) if not snapshots.empty else 0
    print(
        pd.DataFrame(
            [
                {
                    "snapshot_rows": int(len(snapshots)),
                    "stop_price_populated_count": stop_count,
                    "take_profit_price_populated_count": tp_count,
                    "real_capital_status": REAL_CAPITAL_STATUS,
                }
            ]
        ).to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
