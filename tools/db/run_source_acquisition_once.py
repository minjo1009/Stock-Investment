from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

from .apply_management_schema import _create_schema
from .common import ACTIVE_DB, ROOT, rel, sha256_file, utc_now


RAW_DIR = ROOT / "data" / "raw" / "source_acquisition_runtime"
DEFAULT_SYMBOLS = ("AAPL", "MSFT", "NVDA", "AMD", "QQQ")
DEFAULT_MACRO_SERIES = ("DFF", "DGS10")
FAMILY_TO_JOB = {
    "daily_ohlcv": "daily_ohlcv_refresh",
    "macro_rates": "macro_rates_refresh",
    "market_bars_5m": "market_bars_5m_refresh",
    "market_ticks_intraday": "market_ticks_intraday_refresh",
    "sec_events": "sec_events_refresh",
}


@dataclass(frozen=True)
class AcquisitionResult:
    source_family: str
    status: str
    skipped_reason: str
    row_count: int = 0
    receipt_id: str = ""
    raw_path: str = ""
    input_hash: str = ""
    lease_token: str = ""


def _bucket_ts() -> str:
    now = datetime.now(UTC)
    minute = (now.minute // 5) * 5
    return now.replace(minute=minute, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _guard(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys=ON")
    control = con.execute(
        "SELECT run_mode, kill_switch_active FROM control_state WHERE control_key='default'"
    ).fetchone()
    if not control or control[0] != "DIAGNOSTIC_ONLY" or int(control[1]) != 1:
        raise RuntimeError("CONTROL_STATE_BLOCKED")
    active = con.execute("SELECT db_path FROM db_authority_manifest WHERE status='ACTIVE'").fetchall()
    if len(active) != 1 or active[0][0] != "trading.db":
        raise RuntimeError("ACTIVE_DB_AUTHORITY_BLOCKED")


def _ensure_runtime_market_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS market_ticks (
            tick_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            last_price REAL NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

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
        );

        CREATE INDEX IF NOT EXISTS idx_market_ticks_ts ON market_ticks(timestamp);
        CREATE INDEX IF NOT EXISTS idx_bars_5m_symbol_ts ON market_bars_5m(symbol, bar_start_ts);
        """
    )


def _ensure_source_scheduler_hardening_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_scheduler_leases (
            lease_key TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            lease_token TEXT NOT NULL,
            state_hash TEXT NOT NULL,
            acquired_at TEXT NOT NULL,
            heartbeat_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            released_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('HELD','RELEASED','STALE_STOLEN'))
        );

        CREATE TABLE IF NOT EXISTS source_acquisition_input_fingerprints (
            fingerprint_id TEXT PRIMARY KEY,
            job_name TEXT NOT NULL,
            source_family TEXT NOT NULL,
            bucket_ts TEXT NOT NULL,
            provider TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('SUCCESS','SKIPPED','FAILURE')),
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            notes TEXT NOT NULL,
            UNIQUE(job_name, bucket_ts, input_hash)
        );

        CREATE INDEX IF NOT EXISTS idx_source_scheduler_leases_expires
            ON source_scheduler_leases(expires_at, status);
        CREATE INDEX IF NOT EXISTS idx_source_acq_input_fingerprints_job_bucket
            ON source_acquisition_input_fingerprints(job_name, bucket_ts, source_family);
        """
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat().replace("+00:00", "Z")
    if pd.isna(value):
        return None
    return value


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _content_rows_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    if frame.empty:
        return digest.hexdigest()
    normalized = frame.copy()
    normalized.columns = [str(col) for col in normalized.columns]
    normalized = normalized.sort_index(axis=1)
    digest.update(("columns|" + "|".join(normalized.columns) + "\n").encode("utf-8"))
    for row in normalized.astype(object).where(pd.notnull(normalized), "").itertuples(index=False, name=None):
        digest.update(("|".join(str(value) for value in row) + "\n").encode("utf-8"))
    return digest.hexdigest()


def _source_lease_key(family: str, bucket: str) -> str:
    return f"source-acq:{FAMILY_TO_JOB[family]}:{bucket}"


def _acquire_source_lease(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    state_hash: str,
    ttl_seconds: int = 600,
) -> tuple[bool, str, str]:
    now = utc_now()
    expires_at = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
    lease_key = _source_lease_key(family, bucket)
    row = con.execute(
        """
        SELECT lease_token, expires_at, status
        FROM source_scheduler_leases
        WHERE lease_key=?
        """,
        (lease_key,),
    ).fetchone()
    if row and row[2] == "HELD" and str(row[1]) > now:
        return False, str(row[0]), "LEASE_HELD"
    lease_token = uuid.uuid4().hex
    con.execute(
        """
        INSERT INTO source_scheduler_leases(
            lease_key, owner_id, lease_token, state_hash, acquired_at,
            heartbeat_at, expires_at, released_at, status
        )
        VALUES (?, 'tools.db.run_source_acquisition_once', ?, ?, ?, ?, ?, NULL, 'HELD')
        ON CONFLICT(lease_key) DO UPDATE SET
            owner_id=excluded.owner_id,
            lease_token=excluded.lease_token,
            state_hash=excluded.state_hash,
            acquired_at=excluded.acquired_at,
            heartbeat_at=excluded.heartbeat_at,
            expires_at=excluded.expires_at,
            released_at=NULL,
            status='HELD'
        """,
        (lease_key, lease_token, state_hash, now, now, expires_at),
    )
    return True, lease_token, ""


def _release_source_lease(con: sqlite3.Connection, *, family: str, bucket: str, lease_token: str) -> None:
    con.execute(
        """
        UPDATE source_scheduler_leases
        SET released_at=?, status='RELEASED'
        WHERE lease_key=? AND lease_token=? AND status='HELD'
        """,
        (utc_now(), _source_lease_key(family, bucket), lease_token),
    )


def _input_fingerprint_seen(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    input_hash: str,
) -> bool:
    return (
        con.execute(
            """
            SELECT 1
            FROM source_acquisition_input_fingerprints
            WHERE job_name=? AND bucket_ts=? AND input_hash=? AND status='SUCCESS'
            LIMIT 1
            """,
            (FAMILY_TO_JOB[family], bucket, input_hash),
        ).fetchone()
        is not None
    )


def _record_input_fingerprint(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    provider: str,
    input_hash: str,
    status: str,
    raw_path: str,
    receipt_id: str,
    notes: str,
) -> None:
    now = utc_now()
    fingerprint_id = f"source-input:{FAMILY_TO_JOB[family]}:{bucket}:{input_hash[:16]}"
    con.execute(
        """
        INSERT INTO source_acquisition_input_fingerprints(
            fingerprint_id, job_name, source_family, bucket_ts, provider,
            input_hash, status, first_seen_at, last_seen_at, raw_path,
            receipt_id, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_name, bucket_ts, input_hash) DO UPDATE SET
            last_seen_at=excluded.last_seen_at,
            notes=excluded.notes
        """,
        (
            fingerprint_id,
            FAMILY_TO_JOB[family],
            family,
            bucket,
            provider,
            input_hash,
            status,
            now,
            now,
            raw_path,
            receipt_id,
            notes,
        ),
    )


def _write_raw(
    source_family: str,
    provider: str,
    bucket: str,
    payload: dict[str, Any],
    *,
    full_frame: pd.DataFrame,
    stable_input_hash: str | None = None,
) -> tuple[Path, str, str]:
    capture = payload.get("capture_ts") or utc_now()
    day = capture[:10].replace("-", "/")
    raw_dir = RAW_DIR / source_family / provider / day
    raw_dir.mkdir(parents=True, exist_ok=True)
    content_hash = stable_input_hash or _content_rows_hash(full_frame)
    prefix = content_hash[:16]
    rows_path = raw_dir / f"{bucket.replace(':', '').replace('-', '')}_{prefix}_rows.csv"
    full_frame.to_csv(rows_path, index=False)
    rows_sha = sha256_file(rows_path)
    metadata = dict(payload)
    metadata["full_raw_path"] = rel(rows_path)
    metadata["full_raw_sha256"] = rows_sha
    metadata["full_raw_row_count"] = int(len(full_frame))
    metadata["observation_content_sha256"] = content_hash
    metadata["preview_rows"] = [
        {key: _json_safe(value) for key, value in row.items()}
        for row in full_frame.head(25).to_dict(orient="records")
    ]
    metadata["truncated_raw_rows"] = 0
    path = raw_dir / f"{bucket.replace(':', '').replace('-', '')}_{prefix}_metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return path, sha256_file(path), content_hash


def _write_scheduler_ledger(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    status: str,
    skipped_reason: str,
    validation: dict[str, Any],
) -> None:
    now = utc_now()
    job_name = FAMILY_TO_JOB[family]
    ledger_id = f"source-acq:{job_name}:{bucket}:{status}:{_digest_text(job_name + bucket + status)[:12]}"
    con.execute(
        """
        INSERT OR REPLACE INTO scheduler_run_ledger(
            run_ledger_id, cadence, expected_bucket_ts, actual_start_at, actual_finish_at,
            owner_id, lease_token, status, lag_seconds, skipped_reason,
            validation_refs_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, 'tools.db.run_source_acquisition_once', ?, ?, 0, ?, ?, ?)
        """,
        (
            ledger_id,
            job_name,
            bucket,
            now,
            now,
            f"source-acquisition:{bucket}",
            status,
            skipped_reason,
            json.dumps(validation, sort_keys=True),
            now,
        ),
    )


def _write_failure_scheduler_ledger(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    exc: BaseException,
) -> None:
    _write_scheduler_ledger(
        con,
        family=family,
        bucket=bucket,
        status="FAILURE",
        skipped_reason=f"EXCEPTION:{type(exc).__name__}",
        validation={
            "source_family": family,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:500],
            "missing_source_is_negative": 0,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
        },
    )


def _policy_max_lag_seconds(con: sqlite3.Connection, family: str) -> int:
    row = con.execute(
        "SELECT max_lag_seconds FROM source_freshness_policy WHERE source_family=?",
        (family,),
    ).fetchone()
    return int(row[0]) if row else 86400


def _freshness_status(con: sqlite3.Connection, family: str, source_ts: str) -> str:
    parsed = _parse_ts(source_ts)
    if parsed is None:
        return "MISSING"
    max_lag_seconds = _policy_max_lag_seconds(con, family)
    if (datetime.now(UTC) - parsed).total_seconds() <= max_lag_seconds:
        return "CURRENT_OR_RECENT"
    return "STALE"


def _write_evidence(
    con: sqlite3.Connection,
    *,
    family: str,
    provider: str,
    source_key: str,
    source_ts: str,
    capture_ts: str,
    raw_path: Path,
    raw_sha: str,
    stable_input_hash: str,
    source_time_basis: str,
    row_count: int,
    target_table: str,
    target_key: str,
    transform_name: str,
) -> tuple[str, str, str]:
    receipt_id = f"receipt:{family}:provider:{_digest_text(provider + source_key + source_ts + stable_input_hash)[:16]}"
    ref_id = f"ref:{family}:provider:{stable_input_hash[:16]}"
    edge_id = f"edge:{family}:provider:{_digest_text(receipt_id + target_table + target_key)[:16]}"
    con.execute(
        """
        INSERT OR REPLACE INTO source_receipts(
            receipt_id, provider, source_family, source_key, source_ts, capture_ts,
            available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
            strict_gate_allowed, proxy_allowed, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        """,
        (
            receipt_id,
            provider,
            family,
            source_key,
            source_ts,
            capture_ts,
            capture_ts,
            rel(raw_path),
            raw_sha,
            source_time_basis,
            capture_ts,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'provider_raw_payload', ?, ?, ?, ?, ?, 'provider acquisition raw payload metadata with full_raw_path; secrets excluded')
        """,
        (ref_id, f"{family}:{provider}:{source_key}", stable_input_hash, raw_path.stat().st_size, family, capture_ts),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?,
                'provider raw payload normalized into governed source table')
        """,
        (
            edge_id,
            family,
            receipt_id,
            ref_id,
            target_table,
            target_key,
            transform_name,
            stable_input_hash,
            _digest_text(f"{target_table}|{target_key}|{row_count}|{source_ts}|{raw_sha}"),
            capture_ts,
        ),
    )
    max_lag_seconds = _policy_max_lag_seconds(con, family)
    freshness_status = _freshness_status(con, family, source_ts)
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?,
                'provider acquisition evidence attached; gates remain closed until source-time certification')
        """,
        (
            family,
            provider,
            f"trading.db:{target_table}",
            source_ts,
            capture_ts,
            capture_ts,
            max(1, max_lag_seconds // 60),
            freshness_status,
            receipt_id,
            capture_ts,
        ),
    )
    return receipt_id, ref_id, edge_id


def _normalize_yfinance(raw: pd.DataFrame, symbol: str, *, interval: str) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(col[0]).strip().lower().replace(" ", "_") for col in frame.columns]
    else:
        frame.columns = [str(col).strip().lower().replace(" ", "_") for col in frame.columns]
    frame = frame.reset_index()
    frame.columns = [str(col).strip().lower().replace(" ", "_") for col in frame.columns]
    if "datetime" in frame.columns:
        frame = frame.rename(columns={"datetime": "timestamp"})
    if "date" in frame.columns:
        frame = frame.rename(columns={"date": "timestamp"})
    if "adj close" in frame.columns and "adj_close" not in frame.columns:
        frame = frame.rename(columns={"adj close": "adj_close"})
    if "timestamp" not in frame.columns:
        return pd.DataFrame()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close", "adj_close", "volume", "dividends", "stock_splits"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"]).copy()
    frame["symbol"] = symbol.upper()
    frame["provider"] = "yfinance"
    frame["interval"] = interval
    return frame.sort_values("timestamp").reset_index(drop=True)


def _fixture_frame(fixture_dir: Path | None, family: str) -> pd.DataFrame:
    if not fixture_dir:
        return pd.DataFrame()
    for suffix in (".csv", ".json"):
        path = fixture_dir / f"{family}{suffix}"
        if path.exists():
            return pd.read_csv(path) if suffix == ".csv" else pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    return pd.DataFrame()


def _fetch_yfinance(symbols: tuple[str, ...], *, interval: str, period: str, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    try:
        import yfinance as yf
    except ImportError:
        return pd.DataFrame(), "YFINANCE_NOT_INSTALLED"
    rows: list[pd.DataFrame] = []
    for symbol in symbols:
        raw = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
        frame = _normalize_yfinance(raw, symbol, interval=interval)
        if not frame.empty:
            rows.append(frame)
    if not rows:
        return pd.DataFrame(), "PROVIDER_RETURNED_EMPTY"
    return pd.concat(rows, ignore_index=True), ""


def _upsert_market_bars(con: sqlite3.Connection, frame: pd.DataFrame, raw_path: Path, raw_sha: str, capture_ts: str) -> int:
    rows = []
    for row in frame.to_dict(orient="records"):
        ts = pd.to_datetime(row.get("timestamp"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        start = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (ts + pd.Timedelta(minutes=5) - pd.Timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        symbol = str(row.get("symbol") or "").upper()
        rows.append(
            (
                f"{symbol}:{start}",
                symbol,
                start,
                end,
                float(row.get("open") or 0.0),
                float(row.get("high") or 0.0),
                float(row.get("low") or 0.0),
                float(row.get("close") or 0.0),
                float(row.get("volume") or 0.0),
                0,
                "YFINANCE_5M_PROVIDER",
                capture_ts,
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO market_bars_5m(
            bar_id, symbol, bar_start_ts, bar_end_ts, open, high, low, close,
            volume, tick_count, source, last_updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _upsert_market_ticks(con: sqlite3.Connection, frame: pd.DataFrame, capture_ts: str) -> int:
    if frame.empty:
        return 0
    latest = frame.sort_values(["symbol", "timestamp"]).groupby("symbol", as_index=False).tail(1)
    rows = []
    for row in latest.to_dict(orient="records"):
        ts = pd.to_datetime(row.get("timestamp"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        ts_iso = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        symbol = str(row.get("symbol") or "").upper()
        rows.append((f"{symbol}:{ts_iso}:yfinance", ts_iso, symbol, float(row.get("close") or 0.0), "YFINANCE_LATEST_5M", capture_ts))
    con.executemany(
        """
        INSERT OR REPLACE INTO market_ticks(tick_id, timestamp, symbol, last_price, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _upsert_daily(con: sqlite3.Connection, frame: pd.DataFrame, raw_path: Path, raw_sha: str, capture_ts: str) -> int:
    rows = []
    for row in frame.to_dict(orient="records"):
        ts = pd.to_datetime(row.get("timestamp") or row.get("session_date"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        session_date = ts.strftime("%Y-%m-%d")
        source_ts = f"{session_date}T21:00:00Z"
        rows.append(
            (
                str(row.get("provider") or "yfinance"),
                str(row.get("symbol") or "").upper(),
                session_date,
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("adj_close"),
                row.get("volume"),
                row.get("dividends", 0.0),
                row.get("stock_splits", row.get("splits", 0.0)),
                source_ts,
                capture_ts,
                capture_ts,
                "daily_session_close_provider_timestamp",
                rel(raw_path),
                raw_sha,
                capture_ts,
                capture_ts,
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO daily_ohlcv(
            provider, symbol, session_date, open, high, low, close, adj_close,
            volume, dividends, splits, source_ts, capture_ts, available_to_brain_ts,
            source_time_basis, raw_path, raw_sha256, inserted_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _fetch_macro(series_ids: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    rows: list[pd.DataFrame] = []
    for series_id in series_ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        try:
            frame = pd.read_csv(url)
        except Exception:
            continue
        if frame.empty or series_id not in frame.columns:
            continue
        frame = frame.rename(columns={"observation_date": "observation_date", series_id: "value"})
        frame["series_id"] = series_id
        rows.append(frame[["series_id", "observation_date", "value"]])
    if not rows:
        return pd.DataFrame(), "PROVIDER_RETURNED_EMPTY"
    return pd.concat(rows, ignore_index=True), ""


def _upsert_macro(con: sqlite3.Connection, frame: pd.DataFrame, raw_path: Path, raw_sha: str, capture_ts: str) -> int:
    rows = []
    for row in frame.to_dict(orient="records"):
        obs = str(row.get("observation_date") or "")[:10]
        if not obs:
            continue
        rows.append(
            (
                str(row.get("provider") or "fred_csv"),
                str(row.get("series_id") or ""),
                obs,
                str(row.get("vintage_ts") or "PROVIDER_CURRENT_NO_VINTAGE"),
                None if str(row.get("value") or ".") == "." else row.get("value"),
                str(row.get("units") or ""),
                f"{obs}T21:00:00Z",
                capture_ts,
                capture_ts,
                str(row.get("source_time_basis") or "provider_current_observation_no_vintage"),
                rel(raw_path),
                raw_sha,
                capture_ts,
                capture_ts,
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO macro_rates(
            provider, series_id, observation_date, vintage_ts, value, units, source_ts,
            capture_ts, available_to_brain_ts, source_time_basis, raw_path, raw_sha256,
            inserted_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _fetch_sec_events(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    if not user_agent:
        return pd.DataFrame(), "SEC_USER_AGENT_MISSING"
    request = Request(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            mapping = json.loads(response.read().decode("utf-8"))
    except Exception:
        return pd.DataFrame(), "SEC_COMPANY_TICKERS_FETCH_FAILED"
    rows: list[dict[str, Any]] = []
    by_ticker = {str(v.get("ticker") or "").upper(): v for v in mapping.values() if isinstance(v, dict)}
    for symbol in symbols:
        entry = by_ticker.get(symbol.upper())
        if not entry:
            continue
        cik = str(entry.get("cik_str") or "").zfill(10)
        sub_req = Request(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers={"User-Agent": user_agent, "Accept": "application/json"},
        )
        try:
            with urlopen(sub_req, timeout=30) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            continue
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])[:20]
        accessions = recent.get("accessionNumber", [])[:20]
        filing_dates = recent.get("filingDate", [])[:20]
        acceptances = recent.get("acceptanceDateTime", [])[:20]
        reports = recent.get("reportDate", [])[:20]
        for idx, form in enumerate(forms):
            accession = accessions[idx] if idx < len(accessions) else ""
            filed_at = filing_dates[idx] if idx < len(filing_dates) else ""
            accepted_raw = acceptances[idx] if idx < len(acceptances) else ""
            accepted_at = (
                pd.to_datetime(accepted_raw, utc=True, errors="coerce").strftime("%Y-%m-%dT%H:%M:%SZ")
                if accepted_raw
                else ""
            )
            rows.append(
                {
                    "provider": "sec_submissions_api",
                    "cik": cik,
                    "ticker": symbol.upper(),
                    "accession_no": accession,
                    "form_type": str(form),
                    "filed_at": filed_at,
                    "accepted_at": accepted_at,
                    "period_of_report": reports[idx] if idx < len(reports) else "",
                    "event_type": "filing_index",
                    "source_url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                }
            )
    if not rows:
        return pd.DataFrame(), "PROVIDER_RETURNED_EMPTY"
    return pd.DataFrame(rows), ""


def _upsert_sec(con: sqlite3.Connection, frame: pd.DataFrame, raw_path: Path, raw_sha: str, capture_ts: str) -> int:
    rows = []
    for row in frame.to_dict(orient="records"):
        accepted = str(row.get("accepted_at") or row.get("source_ts") or "")
        filed = str(row.get("filed_at") or row.get("filing_date") or "")
        source_ts = accepted or (f"{filed}T00:00:00Z" if filed else capture_ts)
        accession = str(row.get("accession_no") or row.get("accession_number") or "")
        if not accession:
            accession = _digest_text(json.dumps(row, sort_keys=True, default=str))[:16]
        rows.append(
            (
                str(row.get("provider") or "sec_submissions_api"),
                str(row.get("cik") or ""),
                str(row.get("ticker") or row.get("symbol") or "").upper(),
                accession,
                str(row.get("form_type") or "UNKNOWN"),
                filed,
                accepted,
                str(row.get("period_of_report") or row.get("report_date") or ""),
                str(row.get("event_type") or row.get("event_family") or "filing_index"),
                str(row.get("source_url") or row.get("primary_document_raw_path") or row.get("raw_path") or ""),
                source_ts,
                capture_ts,
                capture_ts,
                "sec_accepted_at_or_filed_at",
                rel(raw_path),
                raw_sha,
                "sec_events_v1",
                capture_ts,
                capture_ts,
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO sec_events(
            provider, cik, ticker, accession_no, form_type, filed_at, accepted_at,
            period_of_report, event_type, source_url, source_ts, capture_ts,
            available_to_brain_ts, source_time_basis, raw_path, raw_sha256,
            parser_version, inserted_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _acquire_family(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    symbols: tuple[str, ...],
    macro_series: tuple[str, ...],
    fixture_dir: Path | None,
    allow_network: bool,
) -> AcquisitionResult:
    state_hash = _digest_text(
        json.dumps(
            {
                "family": family,
                "bucket": bucket,
                "symbols": list(symbols),
                "macro_series": list(macro_series),
                "fixture_dir": str(fixture_dir) if fixture_dir else "",
                "allow_network": allow_network,
            },
            sort_keys=True,
        )
    )
    acquired, lease_token, lease_reason = _acquire_source_lease(
        con,
        family=family,
        bucket=bucket,
        state_hash=state_hash,
    )
    if not acquired:
        _write_scheduler_ledger(
            con,
            family=family,
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=lease_reason,
            validation={
                "source_family": family,
                "lease_held": 1,
                "missing_source_is_negative": 0,
                "input_hash_checked": 0,
            },
        )
        return AcquisitionResult(family, "SKIPPED", lease_reason, lease_token=lease_token)
    try:
        result = _acquire_family_locked(
            con,
            family=family,
            bucket=bucket,
            symbols=symbols,
            macro_series=macro_series,
            fixture_dir=fixture_dir,
            allow_network=allow_network,
        )
        return AcquisitionResult(
            result.source_family,
            result.status,
            result.skipped_reason,
            result.row_count,
            result.receipt_id,
            result.raw_path,
            result.input_hash,
            lease_token,
        )
    finally:
        _release_source_lease(con, family=family, bucket=bucket, lease_token=lease_token)


def _acquire_family_locked(
    con: sqlite3.Connection,
    *,
    family: str,
    bucket: str,
    symbols: tuple[str, ...],
    macro_series: tuple[str, ...],
    fixture_dir: Path | None,
    allow_network: bool,
) -> AcquisitionResult:
    capture_ts = utc_now()
    frame = _fixture_frame(fixture_dir, family)
    skipped_reason = ""
    provider = "fixture"
    if frame.empty:
        provider = "yfinance" if family in {"market_bars_5m", "market_ticks_intraday", "daily_ohlcv"} else "fred_csv" if family == "macro_rates" else "sec_submissions_api"
        if family == "market_bars_5m":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="5m", period="5d", allow_network=allow_network)
        elif family == "market_ticks_intraday":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="5m", period="1d", allow_network=allow_network)
        elif family == "daily_ohlcv":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="1d", period="10d", allow_network=allow_network)
        elif family == "macro_rates":
            frame, skipped_reason = _fetch_macro(macro_series, allow_network=allow_network)
        elif family == "sec_events":
            frame, skipped_reason = _fetch_sec_events(symbols, allow_network=allow_network)
    if frame.empty:
        reason = skipped_reason or "NO_PROVIDER_ROWS"
        _write_scheduler_ledger(
            con,
            family=family,
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"source_family": family, "missing_source_is_negative": 0, "allow_network": int(allow_network)},
        )
        return AcquisitionResult(family, "SKIPPED", reason)
    stable_input_hash = _content_rows_hash(frame)
    if _input_fingerprint_seen(con, family=family, bucket=bucket, input_hash=stable_input_hash):
        _write_scheduler_ledger(
            con,
            family=family,
            bucket=bucket,
            status="SKIPPED",
            skipped_reason="DUPLICATE_INPUT_HASH",
            validation={
                "source_family": family,
                "input_hash": stable_input_hash,
                "duplicate_input_hash": 1,
                "db_mutation": 0,
                "missing_source_is_negative": 0,
            },
        )
        _record_input_fingerprint(
            con,
            family=family,
            bucket=bucket,
            provider=provider,
            input_hash=stable_input_hash,
            status="SKIPPED",
            raw_path="",
            receipt_id="",
            notes="duplicate input hash skipped before raw/upsert/evidence mutation",
        )
        return AcquisitionResult(family, "SKIPPED", "DUPLICATE_INPUT_HASH", input_hash=stable_input_hash)

    payload = {
        "source_family": family,
        "provider": provider,
        "status": "success",
        "row_count": int(len(frame)),
        "capture_ts": capture_ts,
        "available_to_brain_ts": capture_ts,
        "request": {"symbols": list(symbols), "macro_series": list(macro_series), "fixture": bool(fixture_dir)},
        "secrets_excluded": True,
        "diagnostic_only": True,
    }
    raw_path, raw_sha, stable_input_hash = _write_raw(
        family,
        provider,
        bucket,
        payload,
        full_frame=frame,
        stable_input_hash=stable_input_hash,
    )
    if family == "market_bars_5m":
        row_count = _upsert_market_bars(con, frame, raw_path, raw_sha, capture_ts)
        target_table = "market_bars_5m"
        source_ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").max().strftime("%Y-%m-%dT%H:%M:%SZ")
        source_time_basis = "provider_bar_start_ts"
    elif family == "market_ticks_intraday":
        row_count = _upsert_market_ticks(con, frame, capture_ts)
        target_table = "market_ticks"
        source_ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").max().strftime("%Y-%m-%dT%H:%M:%SZ")
        source_time_basis = "provider_latest_bar_timestamp_as_quote_proxy"
    elif family == "daily_ohlcv":
        row_count = _upsert_daily(con, frame, raw_path, raw_sha, capture_ts)
        target_table = "daily_ohlcv"
        source_ts = f"{str(pd.to_datetime(frame.get('timestamp', frame.get('session_date')), utc=True, errors='coerce').max().date())}T21:00:00Z"
        source_time_basis = "daily_session_close_provider_timestamp"
    elif family == "macro_rates":
        row_count = _upsert_macro(con, frame, raw_path, raw_sha, capture_ts)
        target_table = "macro_rates"
        source_ts = f"{str(pd.to_datetime(frame['observation_date'], errors='coerce').max().date())}T21:00:00Z"
        source_time_basis = "provider_current_observation_no_vintage"
    else:
        row_count = _upsert_sec(con, frame, raw_path, raw_sha, capture_ts)
        target_table = "sec_events"
        accepted_col = frame["accepted_at"] if "accepted_at" in frame.columns else pd.Series([capture_ts])
        max_accepted = pd.to_datetime(accepted_col, utc=True, errors="coerce").max()
        source_ts = capture_ts if pd.isna(max_accepted) else max_accepted.strftime("%Y-%m-%dT%H:%M:%SZ")
        source_time_basis = "sec_accepted_at_or_filed_at"

    if row_count <= 0:
        _write_scheduler_ledger(
            con,
            family=family,
            bucket=bucket,
            status="SKIPPED",
            skipped_reason="NORMALIZED_ZERO_ROWS",
            validation={"raw_path": rel(raw_path), "raw_sha256": raw_sha},
        )
        return AcquisitionResult(family, "SKIPPED", "NORMALIZED_ZERO_ROWS", 0, raw_path=rel(raw_path), input_hash=stable_input_hash)

    receipt_id, _ref_id, edge_id = _write_evidence(
        con,
        family=family,
        provider=provider,
        source_key=f"{provider}:{family}:{bucket}",
        source_ts=source_ts,
        capture_ts=capture_ts,
        raw_path=raw_path,
        raw_sha=raw_sha,
        stable_input_hash=stable_input_hash,
        source_time_basis=source_time_basis,
        row_count=row_count,
        target_table=target_table,
        target_key=family,
        transform_name=f"{family}_provider_acquisition",
    )
    _write_scheduler_ledger(
        con,
        family=family,
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={
            "receipt_id": receipt_id,
            "edge_id": edge_id,
            "row_count": row_count,
            "raw_path": rel(raw_path),
            "raw_sha256": raw_sha,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
            "allow_network": int(allow_network),
        },
    )
    _record_input_fingerprint(
        con,
        family=family,
        bucket=bucket,
        provider=provider,
        input_hash=stable_input_hash,
        status="SUCCESS",
        raw_path=rel(raw_path),
        receipt_id=receipt_id,
        notes="source acquisition success input hash recorded for duplicate hardening",
    )
    return AcquisitionResult(family, "SUCCESS", "", row_count, receipt_id, rel(raw_path), stable_input_hash)


def run_once(
    *,
    db_path: Path = ACTIVE_DB,
    apply: bool = False,
    families: tuple[str, ...] = tuple(FAMILY_TO_JOB),
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    macro_series: tuple[str, ...] = DEFAULT_MACRO_SERIES,
    fixture_dir: Path | None = None,
    allow_network: bool = False,
    bucket: str | None = None,
) -> dict[str, Any]:
    unknown = sorted(set(families).difference(FAMILY_TO_JOB))
    if unknown:
        raise ValueError(f"unknown source families: {', '.join(unknown)}")
    bucket_ts = bucket or _bucket_ts()
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        _guard(con)
        if not apply:
            return {
                "status": "DRY_RUN_OK_NO_MUTATION",
                "bucket_ts": bucket_ts,
                "families": list(families),
                "allow_network": allow_network,
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        _create_schema(con)
        _ensure_runtime_market_tables(con)
        _ensure_source_scheduler_hardening_tables(con)
        results: list[AcquisitionResult] = []
        for family in families:
            try:
                with con:
                    results.append(
                        _acquire_family(
                            con,
                            family=family,
                            bucket=bucket_ts,
                            symbols=symbols,
                            macro_series=macro_series,
                            fixture_dir=fixture_dir,
                            allow_network=allow_network,
                        )
                    )
            except Exception as exc:
                with con:
                    _write_failure_scheduler_ledger(con, family=family, bucket=bucket_ts, exc=exc)
                results.append(
                    AcquisitionResult(
                        source_family=family,
                        status="FAILURE",
                        skipped_reason=f"EXCEPTION:{type(exc).__name__}",
                    )
                )
        return {
            "status": "APPLIED_DIAGNOSTIC_ONLY",
            "bucket_ts": bucket_ts,
            "success_count": sum(1 for result in results if result.status == "SUCCESS"),
            "skipped_count": sum(1 for result in results if result.status == "SKIPPED"),
            "failure_count": sum(1 for result in results if result.status == "FAILURE"),
            "results": [result.__dict__ for result in results],
            "allow_network": allow_network,
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    finally:
        con.close()


def _items(values: list[str] | None, default: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(value).strip().upper() for value in values or default if str(value).strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one governed source acquisition loop.")
    parser.add_argument("--apply", action="store_true", help="Mutate DB; omitted means dry-run.")
    parser.add_argument("--allow-network", action="store_true", help="Allow provider network calls.")
    parser.add_argument("--family", action="append", choices=sorted(FAMILY_TO_JOB), help="Source family to run.")
    parser.add_argument("--symbol", action="append", help="Symbol to fetch.")
    parser.add_argument("--macro-series", action="append", help="Macro/FRED series id.")
    parser.add_argument("--fixture-dir", type=Path)
    parser.add_argument("--bucket")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = run_once(
        apply=args.apply,
        families=tuple(args.family or FAMILY_TO_JOB.keys()),
        symbols=_items(args.symbol, DEFAULT_SYMBOLS),
        macro_series=_items(args.macro_series, DEFAULT_MACRO_SERIES),
        fixture_dir=args.fixture_dir,
        allow_network=args.allow_network,
        bucket=args.bucket,
    )
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
