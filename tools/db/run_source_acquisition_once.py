from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import pandas as pd

from .apply_management_schema import _create_schema
from .common import ACTIVE_DB, ROOT, rel, sha256_file, utc_now
from .news_l0_l1 import FAMILY_DEFAULT_PROVIDER, NEWS_SOURCE_FAMILIES, normalize_news_records


RAW_DIR = ROOT / "data" / "raw" / "source_acquisition_runtime"
NEWS_USER_AGENT = "Minjo Stock-Investment source acquisition minjo1009@naver.com"
NEWS_REQUEST_TIMEOUT_SECONDS = 20
NEWS_REQUEST_INTERVAL_SECONDS = 0.5
OFFICIAL_NEWS_ITEM_LIMIT_PER_ENDPOINT = 8
GDELT_MAX_RECORDS = 1
GDELT_TIMESPAN = "15m"
GDELT_REQUEST_INTERVAL_SECONDS = 5.5
GDELT_COOLDOWN_SECONDS = 300
GDELT_BLOCK_STATE = ROOT / "data" / "artifacts" / "gdelt_access_block_state.json"
MARKETAUX_ENV_FILE = ROOT / "configs" / "local" / "marketaux.env"
MARKETAUX_DAILY_REQUEST_LIMIT = 90
MARKETAUX_ARTICLES_PER_REQUEST_LIMIT = 3
MARKETAUX_USAGE_LEDGER = ROOT / "data" / "artifacts" / "marketaux_usage_ledger.json"
SEC_COMPANY_TICKERS_CACHE = ROOT / "data" / "raw" / "fundamental" / "sec_companyfacts" / "company_tickers.json"
SEC_BULK_SUBMISSIONS_ZIP = ROOT / "data" / "raw" / "task_1161_1170_sec_bulk_submissions" / "submissions.zip"
SEC_LIVE_BLOCK_STATE = ROOT / "data" / "artifacts" / "sec_live_access_block_state.json"
SEC_RSS_ENTRY_LIMIT = 40
SEC_REQUEST_INTERVAL_SECONDS = 1.1
SEC_LIVE_COOLDOWN_SECONDS = 600
SEC_LIVE_COOLDOWN_ESCALATION_SECONDS = (600, 1800, 21600, 86400)
SEC_EDGARTOOLS_RATE_LIMIT_PER_SEC = 1
SEC_BROWSER_COMPAT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)
SEC_UNDECLARED_TOOL_TEXT = "Undeclared Automated Tool"
SEC_RATE_THRESHOLD_TEXT = "Request Rate Threshold Exceeded"
SEC_PROVIDER_PRIORITY = {
    "sec_live_delta": 0,
    "sec_rss_delta": 1,
    "sec_bulk_baseline": 2,
    "sec_submissions_cache": 3,
}
OFFICIAL_RSS_FEEDS = (
    {
        "provider": "apple_newsroom_rss",
        "endpoint": "apple_newsroom",
        "url": "https://www.apple.com/newsroom/rss-feed.rss",
        "tickers": "AAPL",
        "entities": "Apple Inc",
        "publisher": "Apple",
        "event_type": "company_ir_newsroom",
    },
    {
        "provider": "federal_reserve_press_all_rss",
        "endpoint": "fed_press_all",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "tickers": "",
        "entities": "Federal Reserve Board",
        "publisher": "Federal Reserve Board",
        "event_type": "official_macro_press_release",
    },
    {
        "provider": "bea_news_release_rss",
        "endpoint": "bea_news_release_feed",
        "url": "https://apps.bea.gov/rss/rss.xml",
        "tickers": "",
        "entities": "U.S. Bureau of Economic Analysis",
        "publisher": "U.S. Bureau of Economic Analysis",
        "event_type": "official_macro_release",
    },
)
OFFICIAL_IR_PAGES = (
    {
        "provider": "apple_investor_relations_html",
        "endpoint": "apple_investor_relations",
        "url": "https://investor.apple.com/investor-relations/default.aspx",
        "tickers": "AAPL",
        "entities": "Apple Inc",
        "publisher": "Apple Investor Relations",
        "event_type": "company_ir_page_snapshot",
    },
)
BLS_LATEST_SERIES = (
    {"series_id": "CUSR0000SA0", "name": "Consumer Price Index for All Urban Consumers", "entity": "U.S. Bureau of Labor Statistics"},
    {"series_id": "LNS14000000", "name": "Unemployment Rate", "entity": "U.S. Bureau of Labor Statistics"},
)
TREASURY_FISCALDATA_ENDPOINTS = (
    {
        "provider": "treasury_fiscaldata_avg_interest_rates",
        "endpoint": "avg_interest_rates",
        "url": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?sort=-record_date&page%5Bsize%5D=3&format=json",
        "entity": "U.S. Treasury Fiscal Data",
    },
)
DEFAULT_SYMBOLS = ("AAPL", "MSFT", "NVDA", "AMD", "QQQ")
DEFAULT_MACRO_SERIES = ("DFF", "DGS10")
FAMILY_TO_JOB = {
    "daily_ohlcv": "daily_ohlcv_refresh",
    "macro_rates": "macro_rates_refresh",
    "market_bars_5m": "market_bars_5m_refresh",
    "market_ticks_intraday": "market_ticks_intraday_refresh",
    "official_public_releases": "official_public_releases_refresh",
    "gdelt_news_events": "gdelt_news_events_refresh",
    "marketaux_news_free": "marketaux_news_free_refresh",
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


def _provider_receipt_id(
    *,
    family: str,
    provider: str,
    source_key: str,
    source_ts: str,
    stable_input_hash: str,
) -> str:
    return f"receipt:{family}:provider:{_digest_text(provider + source_key + source_ts + stable_input_hash)[:16]}"


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


def _ensure_news_event_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS news_event_l0 (
            raw_item_id TEXT PRIMARY KEY,
            source_family TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_item_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            canonical_url TEXT NOT NULL,
            title TEXT NOT NULL,
            body_or_summary TEXT,
            publication_ts TEXT,
            collection_ts TEXT NOT NULL,
            publisher TEXT,
            author TEXT,
            language TEXT,
            raw_hash TEXT NOT NULL,
            raw_receipt_id TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            terms_or_license_note TEXT NOT NULL,
            provider_metadata_json TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS news_story_cluster (
            dedupe_group_id TEXT PRIMARY KEY,
            canonical_event_hash TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            primary_entity TEXT,
            primary_ticker TEXT,
            publication_date TEXT,
            source_count INTEGER NOT NULL,
            providers_seen_json TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS news_event_entity_map (
            map_id TEXT PRIMARY KEY,
            raw_item_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            entity_name_raw TEXT,
            entity_type TEXT NOT NULL,
            ticker TEXT,
            mapping_method TEXT NOT NULL,
            mapping_confidence REAL NOT NULL,
            is_primary_subject INTEGER NOT NULL,
            needs_review INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS news_event_l1_evidence (
            event_id TEXT PRIMARY KEY,
            raw_item_id TEXT NOT NULL,
            dedupe_group_id TEXT NOT NULL,
            source_family TEXT NOT NULL,
            provider TEXT NOT NULL,
            publication_time TEXT,
            event_time TEXT,
            normalized_title TEXT NOT NULL,
            normalized_summary TEXT,
            event_type TEXT NOT NULL,
            event_subtype TEXT,
            affected_tickers_json TEXT NOT NULL,
            affected_entities_json TEXT NOT NULL,
            entity_roles_json TEXT NOT NULL,
            keywords_json TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            confidence REAL NOT NULL,
            freshness_status TEXT NOT NULL,
            evidence_score REAL NOT NULL,
            contradiction_flag INTEGER NOT NULL,
            missing_fields_json TEXT NOT NULL,
            quality_flags_json TEXT NOT NULL,
            provider_lineage_json TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            blocker_code TEXT,
            blocker_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_news_event_l0_family_time
            ON news_event_l0(source_family, publication_ts);
        CREATE INDEX IF NOT EXISTS idx_news_event_l1_family_status
            ON news_event_l1_evidence(source_family, promotion_status);
        CREATE INDEX IF NOT EXISTS idx_news_event_entity_ticker
            ON news_event_entity_map(ticker);
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
    receipt_id = _provider_receipt_id(
        family=family,
        provider=provider,
        source_key=source_key,
        source_ts=source_ts,
        stable_input_hash=stable_input_hash,
    )
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


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _upsert_news_events(
    con: sqlite3.Connection,
    *,
    family: str,
    provider: str,
    frame: pd.DataFrame,
    raw_path: Path,
    raw_sha: str,
    capture_ts: str,
    raw_receipt_id: str,
) -> tuple[int, str]:
    bundle = normalize_news_records(
        _frame_records(frame),
        source_family=family,
        provider=provider,
        capture_ts=capture_ts,
        raw_path=rel(raw_path),
        raw_sha=raw_sha,
        raw_receipt_id=raw_receipt_id,
    )
    for row in bundle.raw_items:
        con.execute(
            """
            INSERT INTO news_event_l0(
                raw_item_id, source_family, provider, provider_item_id, source_url,
                canonical_url, title, body_or_summary, publication_ts, collection_ts,
                publisher, author, language, raw_hash, raw_receipt_id, raw_path,
                terms_or_license_note, provider_metadata_json, inserted_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(raw_item_id) DO UPDATE SET
                source_family=excluded.source_family,
                provider=excluded.provider,
                provider_item_id=excluded.provider_item_id,
                source_url=excluded.source_url,
                canonical_url=excluded.canonical_url,
                title=excluded.title,
                body_or_summary=excluded.body_or_summary,
                publication_ts=excluded.publication_ts,
                collection_ts=excluded.collection_ts,
                publisher=excluded.publisher,
                author=excluded.author,
                language=excluded.language,
                raw_hash=excluded.raw_hash,
                raw_receipt_id=excluded.raw_receipt_id,
                raw_path=excluded.raw_path,
                terms_or_license_note=excluded.terms_or_license_note,
                provider_metadata_json=excluded.provider_metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                row["raw_item_id"],
                row["source_family"],
                row["provider"],
                row["provider_item_id"],
                row["source_url"],
                row["canonical_url"],
                row["title"],
                row["body_or_summary"],
                row["publication_ts"],
                row["collection_ts"],
                row["publisher"],
                row["author"],
                row["language"],
                row["raw_hash"],
                row["raw_receipt_id"],
                row["raw_path"],
                row["terms_or_license_note"],
                row["provider_metadata_json"],
                capture_ts,
                capture_ts,
            ),
        )
    for row in bundle.clusters:
        con.execute(
            """
            INSERT INTO news_story_cluster(
                dedupe_group_id, canonical_event_hash, normalized_title,
                primary_entity, primary_ticker, publication_date, source_count,
                providers_seen_json, first_seen_at, last_seen_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dedupe_group_id) DO UPDATE SET
                source_count=news_story_cluster.source_count + excluded.source_count,
                providers_seen_json=excluded.providers_seen_json,
                first_seen_at=min(news_story_cluster.first_seen_at, excluded.first_seen_at),
                last_seen_at=max(news_story_cluster.last_seen_at, excluded.last_seen_at),
                updated_at=excluded.updated_at
            """,
            (
                row["dedupe_group_id"],
                row["canonical_event_hash"],
                row["normalized_title"],
                row["primary_entity"],
                row["primary_ticker"],
                row["publication_date"],
                row["source_count"],
                row["providers_seen_json"],
                row["first_seen_at"],
                row["last_seen_at"],
                capture_ts,
            ),
        )
    for row in bundle.entity_maps:
        con.execute(
            """
            INSERT OR REPLACE INTO news_event_entity_map(
                map_id, raw_item_id, event_id, entity_name_raw, entity_type,
                ticker, mapping_method, mapping_confidence, is_primary_subject,
                needs_review, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["map_id"],
                row["raw_item_id"],
                row["event_id"],
                row["entity_name_raw"],
                row["entity_type"],
                row["ticker"],
                row["mapping_method"],
                row["mapping_confidence"],
                row["is_primary_subject"],
                row["needs_review"],
                capture_ts,
            ),
        )
    for row in bundle.l1_events:
        con.execute(
            """
            INSERT INTO news_event_l1_evidence(
                event_id, raw_item_id, dedupe_group_id, source_family, provider,
                publication_time, event_time, normalized_title, normalized_summary,
                event_type, event_subtype, affected_tickers_json,
                affected_entities_json, entity_roles_json, keywords_json,
                source_count, confidence, freshness_status, evidence_score,
                contradiction_flag, missing_fields_json, quality_flags_json,
                provider_lineage_json, promotion_status, blocker_code,
                blocker_reason, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                source_count=news_event_l1_evidence.source_count + excluded.source_count,
                provider_lineage_json=excluded.provider_lineage_json,
                promotion_status=excluded.promotion_status,
                blocker_code=excluded.blocker_code,
                blocker_reason=excluded.blocker_reason,
                updated_at=excluded.updated_at
            """,
            (
                row["event_id"],
                row["raw_item_id"],
                row["dedupe_group_id"],
                row["source_family"],
                row["provider"],
                row["publication_time"],
                row["event_time"],
                row["normalized_title"],
                row["normalized_summary"],
                row["event_type"],
                row["event_subtype"],
                row["affected_tickers_json"],
                row["affected_entities_json"],
                row["entity_roles_json"],
                row["keywords_json"],
                row["source_count"],
                row["confidence"],
                row["freshness_status"],
                row["evidence_score"],
                row["contradiction_flag"],
                row["missing_fields_json"],
                row["quality_flags_json"],
                row["provider_lineage_json"],
                row["promotion_status"],
                row["blocker_code"],
                row["blocker_reason"],
                capture_ts,
                capture_ts,
            ),
        )
    return len(bundle.raw_items), bundle.max_source_ts


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


def _sanitize_url_for_ledger(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, "***" if key.lower() in {"api_token", "apikey", "api_key", "token", "authorization"} else value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _news_http_get(url: str, *, accept: str = "*/*") -> tuple[bytes, dict[str, Any]]:
    time.sleep(NEWS_REQUEST_INTERVAL_SECONDS)
    safe_url = _sanitize_url_for_ledger(url)
    started_at = utc_now()
    request = Request(
        url,
        headers={
            "User-Agent": NEWS_USER_AGENT,
            "Accept": accept,
            "Accept-Encoding": "gzip, deflate",
        },
    )
    try:
        with urlopen(request, timeout=NEWS_REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
            body = response.read()
            if str(response.headers.get("Content-Encoding") or "").lower() == "gzip":
                body = gzip.decompress(body)
            return body, {
                "url": safe_url,
                "status": "SUCCESS",
                "status_code": int(getattr(response, "status", 200)),
                "started_at": started_at,
                "finished_at": utc_now(),
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "body_bytes": len(body),
            }
    except HTTPError as exc:
        body = exc.read()
        if str(exc.headers.get("Content-Encoding") or "").lower() == "gzip":
            try:
                body = gzip.decompress(body)
            except OSError:
                pass
        reason = "HTTP_ERROR"
        if exc.code == 429:
            reason = "RATE_LIMIT_OR_QUOTA_429"
        elif exc.code == 403:
            reason = "PROVIDER_FORBIDDEN_403"
        return b"", {
            "url": safe_url,
            "status": "SKIPPED",
            "status_code": int(exc.code),
            "reason": reason,
            "started_at": started_at,
            "finished_at": utc_now(),
            "response_body_sha256": hashlib.sha256(body).hexdigest(),
            "response_body_bytes": len(body),
        }
    except Exception as exc:
        return b"", {
            "url": safe_url,
            "status": "SKIPPED",
            "status_code": 0,
            "reason": f"REQUEST_FAILED:{type(exc).__name__}",
            "started_at": started_at,
            "finished_at": utc_now(),
        }


def _parse_news_ts(value: Any, *, fallback: str = "") -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return fallback
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        parsed = pd.to_datetime(text, utc=True, errors="coerce")
        if pd.isna(parsed):
            return fallback
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _xml_child_text(node: ElementTree.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in list(node):
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name in wanted:
            return str(child.text or "").strip()
    return ""


def _xml_entry_link(node: ElementTree.Element) -> str:
    for child in list(node):
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name != "link":
            continue
        href = child.attrib.get("href")
        if href:
            return str(href).strip()
        if child.text:
            return str(child.text).strip()
    return ""


def _parse_rss_or_atom_items(xml_bytes: bytes, spec: dict[str, str], capture_ts: str) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return []
    rows: list[dict[str, Any]] = []
    for node in root.iter():
        local_name = node.tag.rsplit("}", 1)[-1].lower()
        if local_name not in {"item", "entry"}:
            continue
        title = _xml_child_text(node, ("title",))
        link = _xml_child_text(node, ("link",)) or _xml_entry_link(node)
        summary = _xml_child_text(node, ("description", "summary", "content"))
        published = _xml_child_text(node, ("pubdate", "published", "updated"))
        publication_ts = _parse_news_ts(published, fallback=capture_ts)
        provider_item_id = _xml_child_text(node, ("guid", "id")) or _digest_text(f"{spec['provider']}|{title}|{link}")[:24]
        rows.append(
            {
                "provider": spec["provider"],
                "provider_item_id": provider_item_id,
                "source_url": link or spec["url"],
                "title": title,
                "body_or_summary": summary,
                "publication_ts": publication_ts,
                "collection_ts": capture_ts,
                "publisher": spec["publisher"],
                "language": "en",
                "tickers": spec.get("tickers", ""),
                "entities": spec.get("entities", ""),
                "event_type": spec["event_type"],
                "event_subtype": spec["endpoint"],
                "keywords": "official;rss",
            }
        )
        if len(rows) >= OFFICIAL_NEWS_ITEM_LIMIT_PER_ENDPOINT:
            break
    return rows


def _html_title(html_bytes: bytes) -> str:
    text = html_bytes.decode("utf-8", errors="ignore")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title


def _fetch_official_public_releases(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    capture_ts = utc_now()
    rows: list[dict[str, Any]] = []
    call_ledger: list[dict[str, Any]] = []
    wanted_symbols = {symbol.upper() for symbol in symbols}
    for spec in OFFICIAL_RSS_FEEDS:
        tickers = {value.strip().upper() for value in str(spec.get("tickers") or "").split(",") if value.strip()}
        if tickers and wanted_symbols and not tickers.intersection(wanted_symbols):
            continue
        body, ledger = _news_http_get(spec["url"], accept="application/rss+xml, application/atom+xml, text/xml, */*")
        ledger.update({"provider": spec["provider"], "endpoint": spec["endpoint"], "token_used": 0})
        call_ledger.append(ledger)
        if ledger["status"] == "SUCCESS":
            rows.extend(_parse_rss_or_atom_items(body, spec, capture_ts))
    for spec in OFFICIAL_IR_PAGES:
        tickers = {value.strip().upper() for value in str(spec.get("tickers") or "").split(",") if value.strip()}
        if tickers and wanted_symbols and not tickers.intersection(wanted_symbols):
            continue
        body, ledger = _news_http_get(spec["url"], accept="text/html, */*")
        ledger.update({"provider": spec["provider"], "endpoint": spec["endpoint"], "token_used": 0})
        call_ledger.append(ledger)
        if ledger["status"] != "SUCCESS":
            continue
        title = _html_title(body) or f"{spec['publisher']} page snapshot"
        rows.append(
            {
                "provider": spec["provider"],
                "provider_item_id": f"{spec['endpoint']}:{_digest_text(ledger.get('body_sha256', '') + capture_ts)[:16]}",
                "source_url": spec["url"],
                "title": title,
                "body_or_summary": json.dumps(
                    {
                        "snapshot_body_sha256": ledger.get("body_sha256"),
                        "snapshot_body_bytes": ledger.get("body_bytes"),
                        "source_time_basis": "capture_time_only_ir_page_snapshot",
                    },
                    sort_keys=True,
                ),
                "publication_ts": capture_ts,
                "collection_ts": capture_ts,
                "publisher": spec["publisher"],
                "language": "en",
                "tickers": spec.get("tickers", ""),
                "entities": spec.get("entities", ""),
                "event_type": spec["event_type"],
                "event_subtype": spec["endpoint"],
                "keywords": "official;ir;html;capture_time_only",
            }
        )
    for spec in BLS_LATEST_SERIES:
        url = f"https://api.bls.gov/publicAPI/v2/timeseries/data/{quote_plus(spec['series_id'])}?latest=true"
        body, ledger = _news_http_get(url, accept="application/json")
        ledger.update({"provider": "bls_public_api_v2", "endpoint": spec["series_id"], "token_used": 0})
        call_ledger.append(ledger)
        if ledger["status"] != "SUCCESS":
            continue
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        series = (payload.get("Results") or {}).get("series") or []
        data = series[0].get("data") if series else []
        if not data:
            continue
        latest = data[0]
        year = str(latest.get("year") or "")
        period = str(latest.get("period") or "").replace("M", "")
        source_ts = f"{year}-{period.zfill(2)}-01T21:00:00Z" if year and period.isdigit() else capture_ts
        rows.append(
            {
                "provider": "bls_public_api_v2",
                "provider_item_id": f"{spec['series_id']}:{year}:{latest.get('period')}",
                "source_url": _sanitize_url_for_ledger(url),
                "title": f"BLS latest {spec['name']}: {latest.get('value')}",
                "body_or_summary": json.dumps(
                    {"series_id": spec["series_id"], "period": latest.get("periodName"), "value": latest.get("value")},
                    sort_keys=True,
                ),
                "publication_ts": source_ts,
                "collection_ts": capture_ts,
                "publisher": "U.S. Bureau of Labor Statistics",
                "language": "en",
                "tickers": "",
                "entities": spec["entity"],
                "event_type": "official_macro_data_latest",
                "event_subtype": "bls_public_api_latest",
                "keywords": "official;bls;macro",
            }
        )
    for spec in TREASURY_FISCALDATA_ENDPOINTS:
        body, ledger = _news_http_get(spec["url"], accept="application/json")
        ledger.update({"provider": spec["provider"], "endpoint": spec["endpoint"], "token_used": 0})
        call_ledger.append(ledger)
        if ledger["status"] != "SUCCESS":
            continue
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        for index, item in enumerate((payload.get("data") or [])[:3]):
            record_date = str(item.get("record_date") or "")[:10]
            source_ts = f"{record_date}T21:00:00Z" if record_date else capture_ts
            rows.append(
                {
                    "provider": spec["provider"],
                    "provider_item_id": f"{spec['endpoint']}:{record_date}:{index}",
                    "source_url": _sanitize_url_for_ledger(spec["url"]),
                    "title": f"Treasury Fiscal Data {spec['endpoint']} {record_date}",
                    "body_or_summary": json.dumps(item, sort_keys=True),
                    "publication_ts": source_ts,
                    "collection_ts": capture_ts,
                    "publisher": "U.S. Treasury Fiscal Data",
                    "language": "en",
                    "tickers": "",
                    "entities": spec["entity"],
                    "event_type": "official_treasury_data_latest",
                    "event_subtype": spec["endpoint"],
                    "keywords": "official;treasury;macro",
                }
            )
    if not rows:
        reason = "PROVIDER_RETURNED_EMPTY"
        for ledger in call_ledger:
            if ledger.get("reason"):
                reason = str(ledger["reason"])
                break
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = call_ledger
        return frame, reason
    frame = pd.DataFrame(rows)
    frame.attrs["provider_call_ledger"] = call_ledger
    return frame, ""


def _gdelt_query_symbol(symbols: tuple[str, ...]) -> str:
    for symbol in symbols:
        text = str(symbol or "").strip().upper()
        if text:
            return text
    return "AAPL"


def _gdelt_cooldown_state() -> dict[str, Any]:
    if not GDELT_BLOCK_STATE.exists():
        return {"active": False, "retry_after_ts": ""}
    try:
        payload = json.loads(GDELT_BLOCK_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"active": False, "retry_after_ts": ""}
    retry_after = str(payload.get("retry_after_ts") or "")
    parsed = pd.to_datetime(retry_after, utc=True, errors="coerce")
    if pd.isna(parsed):
        return {"active": False, "retry_after_ts": ""}
    return {
        "active": datetime.now(UTC) < parsed.to_pydatetime(),
        "retry_after_ts": retry_after,
        "reason": payload.get("reason", ""),
    }


def _record_gdelt_block(ledger: dict[str, Any]) -> None:
    now = datetime.now(UTC)
    payload = {
        "status": "GDELT_TEMPORARILY_BLOCKED",
        "reason": str(ledger.get("reason") or "RATE_LIMIT_OR_QUOTA_429"),
        "detected_at": now.isoformat().replace("+00:00", "Z"),
        "retry_after_ts": (now + timedelta(seconds=GDELT_COOLDOWN_SECONDS)).isoformat().replace("+00:00", "Z"),
        "cooldown_seconds": GDELT_COOLDOWN_SECONDS,
        "required_action": "Stop GDELT requests during cooldown; retry with one symbol, maxrecords=1, timespan=15m, and >=5 seconds between requests.",
        "provider_call": ledger,
    }
    GDELT_BLOCK_STATE.parent.mkdir(parents=True, exist_ok=True)
    GDELT_BLOCK_STATE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _clear_gdelt_block() -> None:
    if GDELT_BLOCK_STATE.exists():
        try:
            payload = json.loads(GDELT_BLOCK_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        payload.update({"status": "GDELT_ACCESS_RECOVERED", "recovered_at": utc_now()})
        GDELT_BLOCK_STATE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fetch_gdelt_news_events(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    cooldown = _gdelt_cooldown_state()
    if cooldown["active"]:
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [
            {
                "provider": "gdelt_doc_api",
                "endpoint": "doc_artlist",
                "status": "SKIPPED",
                "reason": "GDELT_COOLDOWN_ACTIVE",
                "retry_after_ts": cooldown["retry_after_ts"],
                "token_used": 0,
            }
        ]
        return frame, "GDELT_COOLDOWN_ACTIVE"
    capture_ts = utc_now()
    query_terms = _gdelt_query_symbol(symbols)
    params = {
        "query": query_terms,
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(GDELT_MAX_RECORDS),
        "timespan": GDELT_TIMESPAN,
        "sort": "datedesc",
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    time.sleep(GDELT_REQUEST_INTERVAL_SECONDS)
    body, ledger = _news_http_get(url, accept="application/json")
    ledger.update({"provider": "gdelt_doc_api", "endpoint": "doc_artlist", "token_used": 0})
    if ledger["status"] != "SUCCESS":
        if ledger.get("status_code") == 429:
            _record_gdelt_block(ledger)
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, str(ledger.get("reason") or "GDELT_REQUEST_FAILED")
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        ledger["reason"] = "GDELT_JSON_PARSE_FAILED"
        ledger["response_preview_sha256"] = hashlib.sha256(body[:256]).hexdigest()
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, "GDELT_JSON_PARSE_FAILED"
    _clear_gdelt_block()
    rows: list[dict[str, Any]] = []
    for index, article in enumerate((payload.get("articles") or [])[:GDELT_MAX_RECORDS]):
        title = str(article.get("title") or "")
        url_value = str(article.get("url") or "")
        domain = str(article.get("domain") or "")
        seendate = _parse_news_ts(article.get("seendate") or article.get("datetime"), fallback=capture_ts)
        matched = [symbol.upper() for symbol in symbols if symbol.upper() in f"{title} {url_value}".upper()]
        rows.append(
            {
                "provider": "gdelt_doc_api",
                "provider_item_id": str(article.get("url_mobile") or url_value or f"gdelt-row-{index}"),
                "source_url": url_value,
                "title": title,
                "body_or_summary": str(article.get("snippet") or ""),
                "publication_ts": seendate,
                "collection_ts": capture_ts,
                "publisher": domain,
                "language": str(article.get("language") or "unknown"),
                "tickers": ",".join(matched),
                "entities": "",
                "event_type": "news_discovery",
                "event_subtype": "gdelt_doc_artlist",
                "keywords": "gdelt;discovery",
            }
        )
    if not rows:
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, "PROVIDER_RETURNED_EMPTY"
    frame = pd.DataFrame(rows)
    frame.attrs["provider_call_ledger"] = [ledger]
    return frame, ""


def _load_local_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _marketaux_token() -> str:
    _load_local_env_file(MARKETAUX_ENV_FILE)
    return str(os.environ.get("MARKETAUX_API_TOKEN") or "").strip()


def _marketaux_usage_state() -> dict[str, Any]:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    if not MARKETAUX_USAGE_LEDGER.exists():
        return {"date": today, "request_count": 0}
    try:
        payload = json.loads(MARKETAUX_USAGE_LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"date": today, "request_count": 0}
    if payload.get("date") != today:
        return {"date": today, "request_count": 0}
    return {"date": today, "request_count": int(payload.get("request_count") or 0)}


def _record_marketaux_usage(count: int) -> None:
    state = _marketaux_usage_state()
    state["request_count"] = int(state["request_count"]) + count
    state["daily_limit"] = MARKETAUX_DAILY_REQUEST_LIMIT
    state["updated_at"] = utc_now()
    MARKETAUX_USAGE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    MARKETAUX_USAGE_LEDGER.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fetch_marketaux_news_free(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if not allow_network:
        return pd.DataFrame(), "NETWORK_FETCH_DISABLED"
    token = _marketaux_token()
    if not token:
        return pd.DataFrame(), "MARKETAUX_API_TOKEN_MISSING_SKIP"
    state = _marketaux_usage_state()
    if int(state["request_count"]) >= MARKETAUX_DAILY_REQUEST_LIMIT:
        return pd.DataFrame(), "MARKETAUX_DAILY_LIMIT_GUARD_ACTIVE"
    capture_ts = utc_now()
    symbol_list = ",".join(sorted({symbol.upper() for symbol in symbols if symbol})[:5])
    params = {
        "api_token": token,
        "symbols": symbol_list,
        "filter_entities": "true",
        "must_have_entities": "true",
        "language": "en",
        "limit": str(MARKETAUX_ARTICLES_PER_REQUEST_LIMIT),
    }
    url = "https://api.marketaux.com/v1/news/all?" + urlencode(params)
    body, ledger = _news_http_get(url, accept="application/json")
    ledger.update(
        {
            "provider": "marketaux_free_api",
            "endpoint": "news_all",
            "token_used": 1,
            "token_persisted": 0,
            "daily_limit": MARKETAUX_DAILY_REQUEST_LIMIT,
            "articles_per_request_limit": MARKETAUX_ARTICLES_PER_REQUEST_LIMIT,
            "request_count_before": int(state["request_count"]),
        }
    )
    _record_marketaux_usage(1)
    if ledger["status"] != "SUCCESS":
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, str(ledger.get("reason") or "MARKETAUX_REQUEST_FAILED")
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, "MARKETAUX_JSON_PARSE_FAILED"
    rows: list[dict[str, Any]] = []
    for article in (payload.get("data") or [])[:MARKETAUX_ARTICLES_PER_REQUEST_LIMIT]:
        entities = article.get("entities") or []
        tickers = [str(entity.get("symbol") or "").upper() for entity in entities if entity.get("symbol")]
        entity_names = [str(entity.get("name") or "") for entity in entities if entity.get("name")]
        rows.append(
            {
                "provider": "marketaux_free_api",
                "provider_item_id": str(article.get("uuid") or article.get("url") or _digest_text(str(article))[:24]),
                "source_url": str(article.get("url") or ""),
                "title": str(article.get("title") or ""),
                "body_or_summary": str(article.get("description") or article.get("snippet") or ""),
                "publication_ts": _parse_news_ts(article.get("published_at"), fallback=capture_ts),
                "collection_ts": capture_ts,
                "publisher": str((article.get("source") or "") if isinstance(article.get("source"), str) else (article.get("source") or {}).get("name", "")),
                "language": str(article.get("language") or "en"),
                "tickers": ",".join(tickers),
                "entities": ",".join(entity_names),
                "event_type": "market_news_metadata",
                "event_subtype": "marketaux_free_news_all",
                "keywords": "marketaux;metadata;free_plan",
            }
        )
    if not rows:
        frame = pd.DataFrame()
        frame.attrs["provider_call_ledger"] = [ledger]
        return frame, "PROVIDER_RETURNED_EMPTY"
    frame = pd.DataFrame(rows)
    frame.attrs["provider_call_ledger"] = [ledger]
    return frame, ""


def _fetch_news_family(family: str, symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    if family == "official_public_releases":
        return _fetch_official_public_releases(symbols, allow_network=allow_network)
    if family == "gdelt_news_events":
        return _fetch_gdelt_news_events(symbols, allow_network=allow_network)
    if family == "marketaux_news_free":
        return _fetch_marketaux_news_free(symbols, allow_network=allow_network)
    return pd.DataFrame(), "UNKNOWN_NEWS_FAMILY"


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


def _load_sec_company_tickers_cache(path: Path | None = None) -> dict[str, Any] | None:
    path = path or SEC_COMPANY_TICKERS_CACHE
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _load_sec_submission_cache(
    cik: str,
    path: Path | None = None,
) -> tuple[dict[str, Any], str] | None:
    path = path or SEC_BULK_SUBMISSIONS_ZIP
    if not path.exists():
        return None
    normalized_cik = str(cik or "").replace("CIK", "").zfill(10)
    candidate_names = (
        f"CIK{normalized_cik}.json",
        f"submissions/CIK{normalized_cik}.json",
    )
    try:
        with zipfile.ZipFile(path) as archive:
            for name in candidate_names:
                try:
                    with archive.open(name) as handle:
                        payload = json.loads(handle.read().decode("utf-8"))
                except KeyError:
                    continue
                return (payload, f"{rel(path)}::{name}") if isinstance(payload, dict) else None
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return None


def _sec_contact_email(user_agent: str) -> str:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", user_agent)
    return email_match.group(0) if email_match else ""


def _sec_browser_compat_headers_enabled(user_agent: str) -> bool:
    if str(os.environ.get("SEC_DISABLE_BROWSER_COMPAT_HEADERS") or "").strip().lower() in {"1", "true", "yes"}:
        return False
    return bool(_sec_contact_email(user_agent))


def _sec_header_strategy(user_agent: str) -> str:
    return "browser_compat_from_contact" if _sec_browser_compat_headers_enabled(user_agent) else "declared_user_agent"


def _sec_effective_user_agent(user_agent: str) -> str:
    if not _sec_browser_compat_headers_enabled(user_agent):
        return user_agent
    override = str(os.environ.get("SEC_BROWSER_COMPAT_USER_AGENT") or "").strip()
    return override or SEC_BROWSER_COMPAT_USER_AGENT


def _sec_headers(user_agent: str) -> dict[str, str]:
    headers = {
        "User-Agent": _sec_effective_user_agent(user_agent),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
    }
    contact_email = _sec_contact_email(user_agent)
    if contact_email:
        headers["From"] = contact_email
    return headers


def _sec_request_fingerprint(user_agent: str) -> str:
    return _digest_text(json.dumps(_sec_headers(user_agent), ensure_ascii=True, sort_keys=True))


def _sec_endpoint_group(url: str) -> str:
    if "data.sec.gov/submissions/" in url:
        return "sec_submissions_json"
    if "cgi-bin/browse-edgar" in url:
        return "sec_rss_delta"
    if "company_tickers.json" in url:
        return "sec_company_tickers"
    return "sec_other"


def _sec_live_force_retry_enabled() -> bool:
    return str(os.environ.get("SEC_LIVE_FORCE_RETRY") or "").strip().lower() in {"1", "true", "yes"}


def _sec_block_state() -> dict[str, Any] | None:
    if not SEC_LIVE_BLOCK_STATE.exists():
        return None
    try:
        payload = json.loads(SEC_LIVE_BLOCK_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _sec_live_block_active(user_agent: str | None = None, url: str = "") -> bool:
    if _sec_live_force_retry_enabled():
        return False
    payload = _sec_block_state()
    if not payload:
        return False
    if str(payload.get("status") or "") == "SEC_LIVE_ACCESS_RECOVERED":
        return False
    previous_endpoint_group = str(payload.get("endpoint_group") or "")
    if url and previous_endpoint_group and previous_endpoint_group != _sec_endpoint_group(url):
        return False
    if not url and previous_endpoint_group == "sec_rss_delta":
        return False
    if user_agent:
        current_strategy = _sec_header_strategy(user_agent)
        previous_strategy = str(payload.get("request_header_strategy") or "")
        if current_strategy != previous_strategy and current_strategy == "browser_compat_from_contact":
            return False
        previous_fingerprint = str(payload.get("request_headers_sha256") or "")
        if previous_fingerprint and previous_fingerprint != _sec_request_fingerprint(user_agent):
            return False
    detected_at = _parse_ts(str(payload.get("detected_at") or ""))
    if detected_at is not None:
        cooldown_seconds = int(payload.get("cooldown_seconds") or SEC_LIVE_COOLDOWN_SECONDS)
        retry_after = detected_at + timedelta(seconds=cooldown_seconds)
    else:
        retry_after = _parse_ts(str(payload.get("retry_after_ts") or ""))
    if retry_after is None:
        return False
    return datetime.now(UTC) < retry_after


def _clear_sec_live_block(*, url: str, user_agent: str) -> None:
    previous = _sec_block_state() or {}
    payload = {
        "status": "SEC_LIVE_ACCESS_RECOVERED",
        "last_success_url": url,
        "endpoint_group": _sec_endpoint_group(url),
        "recovered_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "request_header_strategy": _sec_header_strategy(user_agent),
        "request_headers_sha256": _sec_request_fingerprint(user_agent),
        "previous_status": previous.get("status", ""),
        "previous_reason": previous.get("reason", ""),
        "secrets_excluded": True,
    }
    SEC_LIVE_BLOCK_STATE.parent.mkdir(parents=True, exist_ok=True)
    SEC_LIVE_BLOCK_STATE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _record_sec_live_block(
    *,
    url: str,
    reason: str,
    user_agent: str = "",
    status_code: int | None = None,
    response_body: str = "",
) -> None:
    now = datetime.now(UTC)
    previous = _sec_block_state() or {}
    previous_count = int(previous.get("consecutive_block_count") or (1 if previous else 0))
    consecutive_block_count = previous_count + 1
    cooldown_seconds = SEC_LIVE_COOLDOWN_ESCALATION_SECONDS[
        min(consecutive_block_count - 1, len(SEC_LIVE_COOLDOWN_ESCALATION_SECONDS) - 1)
    ]
    response_body_sha256 = hashlib.sha256(response_body.encode("utf-8")).hexdigest() if response_body else ""
    payload = {
        "status": "SEC_LIVE_TEMPORARILY_BLOCKED",
        "reason": reason,
        "status_code": status_code,
        "last_blocked_url": url,
        "endpoint_group": _sec_endpoint_group(url),
        "detected_at": now.isoformat().replace("+00:00", "Z"),
        "retry_after_ts": (now + timedelta(seconds=cooldown_seconds)).isoformat().replace("+00:00", "Z"),
        "cooldown_seconds": cooldown_seconds,
        "consecutive_block_count": consecutive_block_count,
        "cooldown_policy_seconds": list(SEC_LIVE_COOLDOWN_ESCALATION_SECONDS),
        "required_action": "Stop SEC live requests during cooldown; retry once with declared User-Agent and <=1 request/second after cooldown.",
    }
    if user_agent:
        payload["request_header_strategy"] = _sec_header_strategy(user_agent)
        payload["request_headers_sha256"] = _sec_request_fingerprint(user_agent)
    if response_body:
        payload["response_body_sha256"] = response_body_sha256
        payload["response_body_length"] = len(response_body)
        previous_hash = str(previous.get("response_body_sha256") or "")
        if previous_hash:
            payload["previous_response_body_sha256"] = previous_hash
            payload["same_response_body_as_previous"] = previous_hash == response_body_sha256
    SEC_LIVE_BLOCK_STATE.parent.mkdir(parents=True, exist_ok=True)
    SEC_LIVE_BLOCK_STATE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _classify_sec_live_exception(exc: BaseException, *, url: str, user_agent: str = "") -> None:
    status_code = getattr(getattr(exc, "response", None), "status_code", None)
    body = str(getattr(getattr(exc, "response", None), "text", "") or "")
    message = str(exc)
    combined = f"{body}\n{message}"
    if status_code == 403 and SEC_UNDECLARED_TOOL_TEXT in combined:
        _record_sec_live_block(
            url=url,
            reason="SEC_UNDECLARED_AUTOMATED_TOOL_403",
            user_agent=user_agent,
            status_code=status_code,
            response_body=combined,
        )
    elif status_code == 403 and SEC_RATE_THRESHOLD_TEXT in combined:
        _record_sec_live_block(
            url=url,
            reason="SEC_REQUEST_RATE_THRESHOLD_403",
            user_agent=user_agent,
            status_code=status_code,
            response_body=combined,
        )
    elif status_code == 403:
        _record_sec_live_block(
            url=url,
            reason="SEC_FORBIDDEN_UNKNOWN_403",
            user_agent=user_agent,
            status_code=status_code,
            response_body=combined,
        )
    elif status_code == 429:
        _record_sec_live_block(
            url=url,
            reason="SEC_TOO_MANY_REQUESTS_429",
            user_agent=user_agent,
            status_code=status_code,
            response_body=combined,
        )


def _fetch_sec_json_edgartools(url: str, user_agent: str) -> dict[str, Any]:
    os.environ["EDGAR_IDENTITY"] = user_agent
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = str(SEC_EDGARTOOLS_RATE_LIMIT_PER_SEC)
    try:
        from edgar import configure_http, set_identity
        from edgar.httprequests import download_json
    except ImportError:
        raise RuntimeError("EDGARTOOLS_NOT_INSTALLED")
    set_identity(user_agent)
    configure_http(http2=False)
    payload = download_json(url)
    return payload if isinstance(payload, dict) else {}


def _fetch_sec_text_browser_compat(url: str, user_agent: str) -> str:
    try:
        from curl_cffi import requests as curl_cffi_requests
    except ImportError as exc:
        raise RuntimeError("CURL_CFFI_NOT_INSTALLED") from exc
    response = curl_cffi_requests.get(
        url,
        headers={**_sec_headers(user_agent), "Accept": "application/atom+xml, application/xml, text/xml, */*"},
        impersonate="chrome120",
        timeout=30,
    )
    if response.status_code >= 400:
        raise HTTPError(url, response.status_code, response.reason, response.headers, None)
    return str(response.text or "")


def _fetch_sec_json_live(url: str, user_agent: str) -> dict[str, Any]:
    time.sleep(SEC_REQUEST_INTERVAL_SECONDS)
    request = Request(url, headers=_sec_headers(user_agent))
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            body_bytes = response.read()
            if str(getattr(response, "headers", {}).get("Content-Encoding") or "").lower() == "gzip":
                body_bytes = gzip.decompress(body_bytes)
            payload = json.loads(body_bytes.decode("utf-8"))
    except HTTPError as exc:
        body_bytes = exc.read()
        if str(exc.headers.get("Content-Encoding") or "").lower() == "gzip":
            try:
                body_bytes = gzip.decompress(body_bytes)
            except OSError:
                pass
        body = body_bytes.decode("utf-8", errors="replace")
        if exc.code == 403 and SEC_UNDECLARED_TOOL_TEXT in body:
            _record_sec_live_block(
                url=url,
                reason="SEC_UNDECLARED_AUTOMATED_TOOL_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 403 and SEC_RATE_THRESHOLD_TEXT in body:
            _record_sec_live_block(
                url=url,
                reason="SEC_REQUEST_RATE_THRESHOLD_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 403:
            _record_sec_live_block(
                url=url,
                reason="SEC_FORBIDDEN_UNKNOWN_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 429:
            _record_sec_live_block(
                url=url,
                reason="SEC_TOO_MANY_REQUESTS_429",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        raise
    except Exception:
        try:
            return _fetch_sec_json_edgartools(url, user_agent)
        except Exception as exc:
            _classify_sec_live_exception(exc, url=url, user_agent=user_agent)
            raise
    if isinstance(payload, dict):
        _clear_sec_live_block(url=url, user_agent=user_agent)
        return payload
    try:
        return _fetch_sec_json_edgartools(url, user_agent)
    except Exception as exc:
        _classify_sec_live_exception(exc, url=url, user_agent=user_agent)
        raise


def _fetch_sec_text_live(url: str, user_agent: str) -> str:
    time.sleep(SEC_REQUEST_INTERVAL_SECONDS)
    request = Request(url, headers={**_sec_headers(user_agent), "Accept": "application/atom+xml, application/xml, text/xml"})
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            body_bytes = response.read()
            if str(getattr(response, "headers", {}).get("Content-Encoding") or "").lower() == "gzip":
                body_bytes = gzip.decompress(body_bytes)
    except HTTPError as exc:
        body_bytes = exc.read()
        if str(exc.headers.get("Content-Encoding") or "").lower() == "gzip":
            try:
                body_bytes = gzip.decompress(body_bytes)
            except OSError:
                pass
        body = body_bytes.decode("utf-8", errors="replace")
        if exc.code == 403 and _sec_endpoint_group(url) == "sec_rss_delta":
            try:
                body = _fetch_sec_text_browser_compat(url, user_agent)
            except Exception:
                pass
            else:
                _clear_sec_live_block(url=url, user_agent=user_agent)
                return body
        if exc.code == 403 and SEC_UNDECLARED_TOOL_TEXT in body:
            _record_sec_live_block(
                url=url,
                reason="SEC_UNDECLARED_AUTOMATED_TOOL_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 403 and SEC_RATE_THRESHOLD_TEXT in body:
            _record_sec_live_block(
                url=url,
                reason="SEC_REQUEST_RATE_THRESHOLD_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 403:
            _record_sec_live_block(
                url=url,
                reason="SEC_FORBIDDEN_UNKNOWN_403",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        elif exc.code == 429:
            _record_sec_live_block(
                url=url,
                reason="SEC_TOO_MANY_REQUESTS_429",
                user_agent=user_agent,
                status_code=exc.code,
                response_body=body,
            )
        raise
    _clear_sec_live_block(url=url, user_agent=user_agent)
    return body_bytes.decode("utf-8", errors="replace")


def _sec_submission_rows(
    *,
    symbol: str,
    cik: str,
    payload: dict[str, Any],
    provider: str,
    source_url: str,
    max_rows: int = 20,
    seen_accessions: set[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_accessions = seen_accessions if seen_accessions is not None else set()
    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])[:max_rows]
    accessions = recent.get("accessionNumber", [])[:max_rows]
    filing_dates = recent.get("filingDate", [])[:max_rows]
    acceptances = recent.get("acceptanceDateTime", [])[:max_rows]
    reports = recent.get("reportDate", [])[:max_rows]
    for idx, form in enumerate(forms):
        accession = str(accessions[idx] if idx < len(accessions) else "")
        if not accession or accession in seen_accessions:
            continue
        filed_at = filing_dates[idx] if idx < len(filing_dates) else ""
        accepted_raw = acceptances[idx] if idx < len(acceptances) else ""
        accepted_at = (
            pd.to_datetime(accepted_raw, utc=True, errors="coerce").strftime("%Y-%m-%dT%H:%M:%SZ")
            if accepted_raw
            else ""
        )
        rows.append(
            {
                "provider": provider,
                "cik": cik,
                "ticker": symbol.upper(),
                "accession_no": accession,
                "form_type": str(form),
                "filed_at": filed_at,
                "accepted_at": accepted_at,
                "period_of_report": reports[idx] if idx < len(reports) else "",
                "event_type": "filing_index",
                "source_url": source_url,
            }
        )
        seen_accessions.add(accession)
    return rows


def _sec_company_entries(symbols: tuple[str, ...], mapping: dict[str, Any]) -> dict[str, tuple[dict[str, Any], str]]:
    by_ticker = {str(v.get("ticker") or "").upper(): v for v in mapping.values() if isinstance(v, dict)}
    entries: dict[str, tuple[dict[str, Any], str]] = {}
    for symbol in symbols:
        entry = by_ticker.get(symbol.upper())
        if not entry:
            continue
        cik = str(entry.get("cik_str") or "").zfill(10)
        entries[symbol.upper()] = (entry, cik)
    return entries


def _fetch_sec_bulk_baseline(
    symbols: tuple[str, ...],
    mapping: dict[str, Any],
    seen_accessions: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, (_entry, cik) in _sec_company_entries(symbols, mapping).items():
        cached = _load_sec_submission_cache(cik)
        if cached is None:
            continue
        payload, source_url = cached
        rows.extend(
            _sec_submission_rows(
                symbol=symbol,
                cik=cik,
                payload=payload,
                provider="sec_bulk_baseline",
                source_url=source_url,
                seen_accessions=seen_accessions,
            )
        )
    return rows


def _fetch_sec_cache_fallback(
    symbols: tuple[str, ...],
    mapping: dict[str, Any],
    seen_accessions: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, (_entry, cik) in _sec_company_entries(symbols, mapping).items():
        cached = _load_sec_submission_cache(cik)
        if cached is None:
            continue
        payload, source_url = cached
        rows.extend(
            _sec_submission_rows(
                symbol=symbol,
                cik=cik,
                payload=payload,
                provider="sec_submissions_cache",
                source_url=source_url,
                seen_accessions=seen_accessions,
            )
        )
    return rows


def _fetch_sec_live_delta(
    symbols: tuple[str, ...],
    mapping: dict[str, Any],
    user_agent: str,
    seen_accessions: set[str],
) -> list[dict[str, Any]]:
    if not user_agent or _sec_live_block_active(user_agent):
        return []
    rows: list[dict[str, Any]] = []
    for symbol, (_entry, cik) in _sec_company_entries(symbols, mapping).items():
        live_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            if _sec_live_block_active(user_agent, live_url):
                break
            payload = _fetch_sec_json_live(live_url, user_agent)
        except Exception:
            continue
        rows.extend(
            _sec_submission_rows(
                symbol=symbol,
                cik=cik,
                payload=payload,
                provider="sec_live_delta",
                source_url=live_url,
                seen_accessions=seen_accessions,
            )
        )
    return rows


def _rss_child_text(entry: ElementTree.Element, local_name: str) -> str:
    for child in list(entry):
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return str(child.text or "").strip()
    return ""


def _rss_entry_link(entry: ElementTree.Element) -> str:
    for child in list(entry):
        if child.tag.rsplit("}", 1)[-1] == "link":
            href = child.attrib.get("href")
            if href:
                return href
            if child.text:
                return child.text.strip()
    return ""


def _parse_sec_rss_entries(xml_text: str, *, symbol: str, cik: str, source_url: str) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []
    rows: list[dict[str, Any]] = []
    for entry in root.iter():
        if entry.tag.rsplit("}", 1)[-1] not in {"entry", "item"}:
            continue
        title = _rss_child_text(entry, "title")
        updated = _rss_child_text(entry, "updated") or _rss_child_text(entry, "pubDate")
        filed_at = str(pd.to_datetime(updated, utc=True, errors="coerce").date()) if updated else ""
        accepted_at = (
            pd.to_datetime(updated, utc=True, errors="coerce").strftime("%Y-%m-%dT%H:%M:%SZ")
            if updated
            else ""
        )
        link = _rss_entry_link(entry) or source_url
        accession_match = re.search(r"([0-9]{10}-[0-9]{2}-[0-9]{6})", f"{title} {link}")
        accession = accession_match.group(1) if accession_match else _digest_text(f"{symbol}|{title}|{link}")[:16]
        form_match = re.search(r"\b(10-K|10-Q|8-K|6-K|20-F|40-F|S-1|S-3|424B[0-9]?|DEF 14A|4|3|5)\b", title)
        rows.append(
            {
                "provider": "sec_rss_delta",
                "cik": cik,
                "ticker": symbol.upper(),
                "accession_no": accession,
                "form_type": form_match.group(1) if form_match else "UNKNOWN",
                "filed_at": filed_at,
                "accepted_at": accepted_at,
                "period_of_report": "",
                "event_type": "latest_filing_rss_delta",
                "source_url": link,
            }
        )
    return rows


def _fetch_sec_rss_delta(
    symbols: tuple[str, ...],
    mapping: dict[str, Any],
    user_agent: str,
    seen_accessions: set[str],
) -> list[dict[str, Any]]:
    if not user_agent or _sec_live_block_active(user_agent):
        return []
    rows: list[dict[str, Any]] = []
    for symbol, (_entry, cik) in _sec_company_entries(symbols, mapping).items():
        if _sec_live_block_active(user_agent):
            break
        rss_url = (
            "https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count={SEC_RSS_ENTRY_LIMIT}&output=atom"
        )
        if _sec_live_block_active(user_agent, rss_url):
            continue
        try:
            xml_text = _fetch_sec_text_live(rss_url, user_agent)
        except Exception:
            continue
        for row in _parse_sec_rss_entries(xml_text, symbol=symbol, cik=cik, source_url=rss_url):
            accession = str(row.get("accession_no") or "")
            if not accession or accession in seen_accessions:
                continue
            rows.append(row)
            seen_accessions.add(accession)
    return rows


def _load_sec_ticker_mapping_for_hybrid(user_agent: str, *, allow_network: bool) -> dict[str, Any] | None:
    mapping = _load_sec_company_tickers_cache()
    if mapping is not None:
        return mapping
    mapping_url = "https://www.sec.gov/files/company_tickers.json"
    if not allow_network or not user_agent or _sec_live_block_active(user_agent, mapping_url):
        return None
    try:
        return _fetch_sec_json_live(mapping_url, user_agent)
    except Exception:
        return None


def _fetch_sec_events_hybrid(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if allow_network and user_agent and _sec_live_block_active(user_agent):
        return pd.DataFrame(), "SEC_LIVE_ACCESS_COOLDOWN_ACTIVE"
    mapping = _load_sec_ticker_mapping_for_hybrid(user_agent, allow_network=allow_network)
    if mapping is None:
        if not allow_network:
            return pd.DataFrame(), "SEC_BULK_BASELINE_MAPPING_CACHE_MISSING_NETWORK_DISABLED"
        if not user_agent:
            return pd.DataFrame(), "SEC_USER_AGENT_MISSING"
        return pd.DataFrame(), "SEC_TICKER_MAPPING_UNAVAILABLE"
    seen_accessions: set[str] = set()
    rows: list[dict[str, Any]] = []
    rows.extend(_fetch_sec_bulk_baseline(symbols, mapping, seen_accessions))
    if allow_network and user_agent:
        rows.extend(_fetch_sec_live_delta(symbols, mapping, user_agent, seen_accessions))
        rows.extend(_fetch_sec_rss_delta(symbols, mapping, user_agent, seen_accessions))
    if not rows:
        rows.extend(_fetch_sec_cache_fallback(symbols, mapping, seen_accessions))
    if not rows:
        return pd.DataFrame(), "PROVIDER_RETURNED_EMPTY"
    return pd.DataFrame(rows), ""


def _fetch_sec_events(symbols: tuple[str, ...], *, allow_network: bool) -> tuple[pd.DataFrame, str]:
    return _fetch_sec_events_hybrid(symbols, allow_network=allow_network)


def _highest_priority_sec_provider(providers: list[str]) -> str:
    if not providers:
        return "sec_events_provider_unknown"
    return sorted(providers, key=lambda provider: (SEC_PROVIDER_PRIORITY.get(provider, 99), provider))[0]


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
    providers_seen: list[str] = []
    provider_call_ledger: list[dict[str, Any]] = []
    if not frame.empty and family in NEWS_SOURCE_FAMILIES and "provider" in frame.columns:
        providers_seen = sorted({str(value) for value in frame["provider"].dropna().tolist() if str(value)})
        provider = providers_seen[0] if providers_seen else FAMILY_DEFAULT_PROVIDER[family]
    elif not frame.empty and family in NEWS_SOURCE_FAMILIES:
        provider = FAMILY_DEFAULT_PROVIDER[family]
    if frame.empty:
        provider = (
            "yfinance"
            if family in {"market_bars_5m", "market_ticks_intraday", "daily_ohlcv"}
            else "fred_csv"
            if family == "macro_rates"
            else FAMILY_DEFAULT_PROVIDER[family]
            if family in NEWS_SOURCE_FAMILIES
            else "sec_submissions_api"
        )
        if family == "market_bars_5m":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="5m", period="5d", allow_network=allow_network)
        elif family == "market_ticks_intraday":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="5m", period="1d", allow_network=allow_network)
        elif family == "daily_ohlcv":
            frame, skipped_reason = _fetch_yfinance(symbols, interval="1d", period="10d", allow_network=allow_network)
        elif family == "macro_rates":
            frame, skipped_reason = _fetch_macro(macro_series, allow_network=allow_network)
        elif family in NEWS_SOURCE_FAMILIES:
            frame, skipped_reason = _fetch_news_family(family, symbols, allow_network=allow_network)
            provider_call_ledger = list(frame.attrs.get("provider_call_ledger") or [])
            if not frame.empty and "provider" in frame.columns:
                providers_seen = sorted({str(value) for value in frame["provider"].dropna().tolist() if str(value)})
                provider = providers_seen[0] if providers_seen else FAMILY_DEFAULT_PROVIDER[family]
        elif family == "sec_events":
            frame, skipped_reason = _fetch_sec_events(symbols, allow_network=allow_network)
            if not frame.empty and "provider" in frame.columns:
                providers_seen = sorted({str(value) for value in frame["provider"].dropna().tolist() if str(value)})
                provider = _highest_priority_sec_provider(providers_seen)
    if family == "official_public_releases" and len(providers_seen) > 1:
        provider = "official_public_releases_multi_provider"
    if frame.empty:
        reason = skipped_reason or "NO_PROVIDER_ROWS"
        _write_scheduler_ledger(
            con,
            family=family,
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={
                "source_family": family,
                "missing_source_is_negative": 0,
                "allow_network": int(allow_network),
                "provider_call_ledger": provider_call_ledger,
            },
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
        "providers_seen": providers_seen or [provider],
        "provider_call_ledger": provider_call_ledger,
        "provider_selection_rule": (
            "sec_live_delta > sec_rss_delta > sec_bulk_baseline > sec_submissions_cache"
            if family == "sec_events"
            else "official first, discovery providers remain non-authority"
            if family in NEWS_SOURCE_FAMILIES
            else "single_provider"
        ),
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
    elif family in NEWS_SOURCE_FAMILIES:
        provisional_source = pd.Series([capture_ts])
        for column in ("publication_ts", "published_at", "published", "seendate", "datetime"):
            if column in frame.columns:
                provisional_source = frame[column]
                break
        max_publication = pd.to_datetime(provisional_source, utc=True, errors="coerce").max()
        source_ts = capture_ts if pd.isna(max_publication) else max_publication.strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt_id = _provider_receipt_id(
            family=family,
            provider=provider,
            source_key=f"{provider}:{family}:{bucket}",
            source_ts=source_ts,
            stable_input_hash=stable_input_hash,
        )
        row_count, source_ts = _upsert_news_events(
            con,
            family=family,
            provider=provider,
            frame=frame,
            raw_path=raw_path,
            raw_sha=raw_sha,
            capture_ts=capture_ts,
            raw_receipt_id=receipt_id,
        )
        target_table = "news_event_l0"
        source_time_basis = "news_publication_ts_or_capture_ts_when_missing"
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
            "missing_source_is_negative": 0,
            "allow_network": int(allow_network),
            "provider_call_ledger": provider_call_ledger,
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
        _ensure_news_event_tables(con)
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
