from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common import ACTIVE_DB, ROOT, rel, sha256_file, utc_now, write_json


RAW_HEARTBEAT_DIR = ROOT / "data" / "raw" / "diagnostic_runtime_heartbeats"
RAW_MARKET_BARS_DIR = ROOT / "data" / "raw" / "market_bars_5m_cached"
RAW_CACHED_TABLE_DIR = ROOT / "data" / "raw" / "db_cached_table_snapshots"
ADAPTERS = {
    "broker_truth_reconciliation_refresh": "diagnostic_broker_truth_reconciliation",
    "catalog_report_artifacts_refresh": "derived_catalog_report_artifacts_lineage",
    "daily_ohlcv_refresh": "cached_daily_ohlcv",
    "diagnostic_runtime_heartbeats_refresh": "internal_heartbeat",
    "frontend_read_models_refresh": "derived_frontend_read_models_lineage",
    "indicator_snapshots_refresh": "derived_indicator_snapshots_from_market_bars",
    "l6_authority_evidence_refresh": "runtime_authority_evidence_generation",
    "macro_rates_refresh": "cached_macro_rates",
    "market_bars_5m_refresh": "cached_market_bars_5m",
    "market_ticks_intraday_refresh": "cached_market_ticks_intraday",
    "official_public_releases_refresh": "cached_news_event_l0",
    "gdelt_news_events_refresh": "cached_news_event_l0",
    "marketaux_news_free_refresh": "cached_news_event_l0",
    "runtime_strategy_decisions_refresh": "derived_runtime_strategy_decisions_from_indicators",
    "sec_events_refresh": "cached_sec_events",
}
ADAPTER_SOURCE_FAMILIES = {
    "authority_evidence_ledger": "runtime_authority_evidence_generation",
    "broker_truth_reconciliation": "diagnostic_broker_truth_reconciliation",
    "catalog_report_artifacts": "derived_catalog_report_artifacts_lineage",
    "daily_ohlcv": "cached_daily_ohlcv",
    "diagnostic_runtime_heartbeats": "internal_heartbeat",
    "frontend_read_models": "derived_frontend_read_models_lineage",
    "indicator_snapshots": "derived_indicator_snapshots_from_market_bars",
    "macro_rates": "cached_macro_rates",
    "market_bars_5m": "cached_market_bars_5m",
    "market_ticks_intraday": "cached_market_ticks_intraday",
    "official_public_releases": "cached_news_event_l0",
    "gdelt_news_events": "cached_news_event_l0",
    "marketaux_news_free": "cached_news_event_l0",
    "runtime_strategy_decisions": "derived_runtime_strategy_decisions_from_indicators",
    "sec_events": "cached_sec_events",
}
PERMISSION_COLUMNS = (
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
)


@dataclass(frozen=True)
class JobResult:
    job_name: str
    source_family: str
    status: str
    skipped_reason: str
    receipt_id: str = ""
    ref_id: str = ""
    edge_id: str = ""


def _bucket_ts() -> str:
    now = datetime.now(UTC)
    minute = (now.minute // 5) * 5
    return now.replace(minute=minute, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return (
        con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        is not None
    )


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


def _jobs(con: sqlite3.Connection, only_job: str | None = None) -> list[sqlite3.Row]:
    sql = """
        SELECT * FROM scheduler_job_registry
        WHERE enabled=1 AND diagnostic_only=1
        ORDER BY job_name
    """
    rows = con.execute(sql).fetchall()
    if only_job:
        rows = [row for row in rows if row["job_name"] == only_job]
    return rows


def _validate_permissions(row: sqlite3.Row) -> None:
    for column in PERMISSION_COLUMNS:
        if int(row[column]) != 0:
            raise RuntimeError(f"PERMISSION_COLUMN_NOT_ZERO:{row['job_name']}:{column}")


def _ledger_id(job_name: str, bucket: str, status: str) -> str:
    return f"db-loop:{job_name}:{bucket}:{status}:{_digest_text(job_name + bucket + status)[:12]}"


def _write_scheduler_ledger(
    con: sqlite3.Connection,
    *,
    job_name: str,
    bucket: str,
    status: str,
    skipped_reason: str,
    validation: dict[str, Any],
) -> None:
    now = utc_now()
    con.execute(
        """
        INSERT OR REPLACE INTO scheduler_run_ledger(
            run_ledger_id, cadence, expected_bucket_ts, actual_start_at, actual_finish_at,
            owner_id, lease_token, status, lag_seconds, skipped_reason,
            validation_refs_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, 'tools.db.run_registered_loop_once', ?, ?, 0, ?, ?, ?)
        """,
        (
            _ledger_id(job_name, bucket, status),
            job_name,
            bucket,
            now,
            now,
            f"diagnostic-loop:{bucket}",
            status,
            skipped_reason,
            json.dumps(validation, sort_keys=True),
            now,
        ),
    )


def _write_heartbeat_raw(job: sqlite3.Row, bucket: str, raw_dir: Path) -> tuple[Path, dict[str, Any]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    payload = {
        "source_family": job["source_family"],
        "job_name": job["job_name"],
        "bucket_ts": bucket,
        "captured_at": now,
        "diagnostic_only": True,
        "execution_permitted": False,
        "broker_mutation_permitted": False,
        "paper_promotion_permitted": False,
        "real_capital_permitted": False,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    path = raw_dir / f"heartbeat_{bucket.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, payload


def _policy_max_lag_seconds(con: sqlite3.Connection, source_family: str) -> int:
    row = con.execute(
        "SELECT max_lag_seconds FROM source_freshness_policy WHERE source_family=?",
        (source_family,),
    ).fetchone()
    return int(row[0]) if row else 1200


def _market_bars_columns(con: sqlite3.Connection) -> list[str]:
    columns = [row["name"] for row in con.execute("PRAGMA table_info(market_bars_5m)").fetchall()]
    preferred = [
        "bar_id",
        "symbol",
        "bar_start_ts",
        "bar_end_ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "tick_count",
        "trade_count",
        "vwap",
        "source",
        "last_updated_at",
    ]
    selected = [column for column in preferred if column in columns]
    missing = {"symbol", "bar_start_ts", "bar_end_ts"}.difference(selected)
    if missing:
        raise RuntimeError(f"MARKET_BARS_5M_SCHEMA_BLOCKED:{','.join(sorted(missing))}")
    return selected


def _encode_hash_value(value: Any) -> str:
    if value is None:
        return "<NULL>"
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


def _hash_market_bars_table(con: sqlite3.Connection, columns: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update(("columns|" + "|".join(columns) + "\n").encode("utf-8"))
    query = (
        "SELECT "
        + ", ".join(f'"{column}"' for column in columns)
        + " FROM market_bars_5m ORDER BY symbol, bar_start_ts, bar_end_ts"
    )
    for row in con.execute(query):
        digest.update(("|".join(_encode_hash_value(value) for value in row) + "\n").encode("utf-8"))
    return digest.hexdigest()


def _table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in con.execute(f'PRAGMA table_info("{table}")').fetchall()]


def _hash_table_rows(
    con: sqlite3.Connection,
    table: str,
    columns: list[str],
    order_columns: list[str],
    *,
    where_sql: str = "",
    where_params: tuple[Any, ...] = (),
) -> str:
    digest = hashlib.sha256()
    digest.update((f"table|{table}|columns|" + "|".join(columns) + f"|where|{where_sql}\n").encode("utf-8"))
    order = ", ".join(f'"{column}"' for column in order_columns if column in columns)
    if not order:
        order = ", ".join(f'"{column}"' for column in columns)
    query = "SELECT " + ", ".join(f'"{column}"' for column in columns) + f' FROM "{table}"'
    if where_sql:
        query += f" WHERE {where_sql}"
    query += f" ORDER BY {order}"
    for row in con.execute(query, where_params):
        digest.update(("|".join(_encode_hash_value(value) for value in row) + "\n").encode("utf-8"))
    return digest.hexdigest()


def _cached_table_stats(
    con: sqlite3.Connection,
    *,
    table: str,
    source_ts_column: str,
    capture_ts_column: str | None,
    distinct_column: str | None = None,
    where_sql: str = "",
    where_params: tuple[Any, ...] = (),
) -> dict[str, Any]:
    expressions = [
        "COUNT(*) AS row_count",
        f'MIN("{source_ts_column}") AS min_source_ts',
        f'MAX("{source_ts_column}") AS max_source_ts',
    ]
    if capture_ts_column:
        expressions.extend(
            [
                f'MIN("{capture_ts_column}") AS min_capture_ts',
                f'MAX("{capture_ts_column}") AS max_capture_ts',
            ]
        )
    if distinct_column:
        expressions.append(f'COUNT(DISTINCT "{distinct_column}") AS distinct_count')
    query = f'SELECT {", ".join(expressions)} FROM "{table}"'
    if where_sql:
        query += f" WHERE {where_sql}"
    row = con.execute(query, where_params).fetchone()
    return dict(row)


def _write_cached_table_raw(
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    *,
    adapter_name: str,
    table: str,
    stats: dict[str, Any],
    table_hash: str,
    freshness_status: str,
) -> tuple[Path, dict[str, Any]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    payload = {
        "source_family": job["source_family"],
        "job_name": job["job_name"],
        "adapter_name": adapter_name,
        "bucket_ts": bucket,
        "captured_at": now,
        "cached_table": table,
        "live_fetch": False,
        "diagnostic_only": True,
        "table_hash": table_hash,
        "freshness_status": freshness_status,
        "strict_gate_allowed": False,
        "proxy_allowed": False,
        "missing_source_is_negative": False,
        "snapshot_stats": stats,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    safe_family = str(job["source_family"]).replace("/", "_")
    path = raw_dir / safe_family / f"{safe_family}_{bucket.replace(':', '').replace('-', '')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, payload


def _write_derived_artifact_raw(
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    *,
    adapter_name: str,
    files: list[dict[str, Any]],
    freshness_status: str,
) -> tuple[Path, dict[str, Any]]:
    family_dir = raw_dir / str(job["source_family"])
    family_dir.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    payload = {
        "source_family": job["source_family"],
        "job_name": job["job_name"],
        "adapter_name": adapter_name,
        "bucket_ts": bucket,
        "captured_at": now,
        "derived_artifact_files": files,
        "file_count": len(files),
        "freshness_status": freshness_status,
        "strict_gate_allowed": False,
        "proxy_allowed": False,
        "read_only": True,
        "source_truth_claim": False,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    path = family_dir / f"{job['source_family']}_{bucket.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, payload


def _artifact_files_for_family(source_family: str) -> list[Path]:
    if source_family == "frontend_read_models":
        candidates = [
            ROOT / "frontend" / "trader-terminal" / "public" / "catalog" / "paper_ops_runtime_catalog.json",
            ROOT / "apps" / "trader-brain-web" / "public" / "catalog" / "paper_ops_runtime_catalog.json",
            ROOT / "apps" / "ios-trader-brain" / "public" / "catalog" / "paper_ops_runtime_catalog.json",
            ROOT / "apps" / "ios-trader-brain" / "public" / "catalog" / "paper_trade_detail_view.json",
        ]
    else:
        candidates = [
            ROOT / "frontend" / "trader-terminal" / "public" / "catalog" / "trader_terminal_catalog.json",
            ROOT / "frontend" / "trader-terminal" / "public" / "catalog" / "paper_ops_runtime_catalog.json",
            ROOT / "apps" / "trader-brain-web" / "public" / "catalog" / "paper_ops_runtime_catalog.json",
        ]
    return [path for path in candidates if path.exists() and path.is_file()]


def _file_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: rel(item)):
        stat = path.stat()
        rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat().replace("+00:00", "Z"),
            }
        )
    return rows


def _run_derived_artifact_lineage(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    *,
    adapter_name: str,
) -> JobResult:
    files = _file_rows(_artifact_files_for_family(str(job["source_family"])))
    if not files:
        reason = f"NO_DERIVED_{str(job['source_family']).upper()}_FILES"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={
                "source_family": job["source_family"],
                "read_only": 1,
                "source_truth_claim": 0,
                "freshness_recovered": 0,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    max_modified = max(str(row["modified_utc"]) for row in files)
    max_source = _parse_ts(max_modified)
    max_lag_seconds = _policy_max_lag_seconds(con, job["source_family"])
    freshness_status = "STALE"
    if max_source is not None and (datetime.now(UTC) - max_source).total_seconds() <= max_lag_seconds:
        freshness_status = "CURRENT_OR_RECENT"
    raw_path, payload = _write_derived_artifact_raw(
        job,
        bucket,
        raw_dir,
        adapter_name=adapter_name,
        files=files,
        freshness_status=freshness_status,
    )
    raw_sha = sha256_file(raw_path)
    now = payload["captured_at"]
    aggregate_hash = _digest_text("|".join(f"{row['path']}:{row['sha256']}" for row in files))
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{aggregate_hash[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
    con.execute(
        """
        INSERT INTO source_receipts(
            receipt_id, provider, source_family, source_key, source_ts, capture_ts,
            available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
            strict_gate_allowed, proxy_allowed, created_at
        )
        VALUES (?, 'local_readonly_artifact_builder', ?, ?, ?, ?, ?, ?, ?,
                'derived_artifact_file_mtime', 0, 0, ?)
        ON CONFLICT(receipt_id) DO UPDATE SET
            provider=excluded.provider,
            source_family=excluded.source_family,
            source_key=excluded.source_key,
            source_ts=excluded.source_ts,
            capture_ts=excluded.capture_ts,
            available_to_brain_ts=excluded.available_to_brain_ts,
            raw_path=excluded.raw_path,
            raw_sha256=excluded.raw_sha256,
            source_time_basis=excluded.source_time_basis,
            strict_gate_allowed=excluded.strict_gate_allowed,
            proxy_allowed=excluded.proxy_allowed,
            created_at=excluded.created_at
        """,
        (
            receipt_id,
            job["source_family"],
            "derived_artifact_files",
            max_modified,
            now,
            now,
            rel(raw_path),
            raw_sha,
            now,
        ),
    )
    ref_path_or_key = ";".join(row["path"] for row in files)
    existing_ref = con.execute(
        """
        SELECT ref_id FROM reference_hashes
        WHERE ref_type='derived_artifact_hash_set' AND path_or_key=? AND sha256=?
        """,
        (ref_path_or_key, aggregate_hash),
    ).fetchone()
    if existing_ref is not None:
        ref_id = str(existing_ref["ref_id"])
    else:
        con.execute(
            """
            INSERT INTO reference_hashes(
                ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
            )
            VALUES (?, 'derived_artifact_hash_set', ?, ?, ?, ?, ?,
                    'read-only derived artifact hash set; not source truth')
            ON CONFLICT(ref_id) DO UPDATE SET
                ref_type=excluded.ref_type,
                path_or_key=excluded.path_or_key,
                sha256=excluded.sha256,
                size_bytes=excluded.size_bytes,
                source_family=excluded.source_family,
                created_at=excluded.created_at,
                notes=excluded.notes
            """,
            (
                ref_id,
                ref_path_or_key,
                aggregate_hash,
                sum(int(row["size_bytes"]) for row in files),
                job["source_family"],
                now,
            ),
        )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?,
                'read-only derived artifact lineage; must not present stale upstream as current')
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            "derived_artifacts",
            job["source_family"],
            adapter_name,
            aggregate_hash,
            _digest_text(f"{job['source_family']}|{freshness_status}|{aggregate_hash}"),
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, 'local_readonly_artifact_builder', 'derived_artifacts',
                ?, ?, ?, ?, ?, 0, 0, ?, ?,
                'derived read-only artifact lineage only; not source truth')
        """,
        (
            job["source_family"],
            max_modified,
            now,
            now,
            max(1, max_lag_seconds // 60),
            freshness_status,
            receipt_id,
            now,
        ),
    )
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={
            "receipt_id": receipt_id,
            "ref_id": ref_id,
            "edge_id": edge_id,
            "file_count": len(files),
            "freshness_status": freshness_status,
            "read_only": 1,
            "source_truth_claim": 0,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
        },
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def _run_cached_table_snapshot(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    *,
    adapter_name: str,
    table: str,
    source_ts_column: str,
    capture_ts_column: str | None,
    order_columns: list[str],
    distinct_column: str | None,
    missing_reason: str,
    provider: str,
    source_time_basis: str,
    transform_name: str,
    notes: str,
    where_sql: str = "",
    where_params: tuple[Any, ...] = (),
) -> JobResult:
    if not _table_exists(con, table):
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=missing_reason,
            validation={
                "source_family": job["source_family"],
                "missing_source_is_negative": 0,
                "freshness_recovered": 0,
                "cached_source_only": 1,
                "live_fetch": 0,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", missing_reason)

    columns = _table_columns(con, table)
    if source_ts_column not in columns:
        raise RuntimeError(f"CACHED_TABLE_SCHEMA_BLOCKED:{table}:{source_ts_column}")
    if capture_ts_column and capture_ts_column not in columns:
        raise RuntimeError(f"CACHED_TABLE_SCHEMA_BLOCKED:{table}:{capture_ts_column}")
    stats = _cached_table_stats(
        con,
        table=table,
        source_ts_column=source_ts_column,
        capture_ts_column=capture_ts_column,
        distinct_column=distinct_column if distinct_column in columns else None,
        where_sql=where_sql,
        where_params=where_params,
    )
    if int(stats["row_count"] or 0) <= 0:
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=missing_reason,
            validation={
                "source_family": job["source_family"],
                "missing_source_is_negative": 0,
                "freshness_recovered": 0,
                "cached_source_only": 1,
                "live_fetch": 0,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", missing_reason)

    max_source = _parse_ts(stats.get("max_source_ts"))
    max_lag_seconds = _policy_max_lag_seconds(con, job["source_family"])
    freshness_status = "STALE"
    if max_source is not None and (datetime.now(UTC) - max_source).total_seconds() <= max_lag_seconds:
        freshness_status = "CURRENT_OR_RECENT"

    table_hash = _hash_table_rows(
        con,
        table,
        columns,
        order_columns,
        where_sql=where_sql,
        where_params=where_params,
    )
    raw_path, payload = _write_cached_table_raw(
        job,
        bucket,
        raw_dir,
        adapter_name=adapter_name,
        table=table,
        stats=stats,
        table_hash=table_hash,
        freshness_status=freshness_status,
    )
    raw_sha = sha256_file(raw_path)
    now = payload["captured_at"]
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{table_hash[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
    output_hash = _digest_text(
        f"{job['source_family']}|source_freshness|{stats.get('max_source_ts')}|{table_hash}|{freshness_status}"
    )
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
            job["source_family"],
            f"trading.db:{table}",
            stats.get("max_source_ts"),
            now,
            now,
            rel(raw_path),
            raw_sha,
            source_time_basis,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'cached_table_snapshot', ?, ?, ?, ?, ?, ?)
        """,
        (
            ref_id,
            f"trading.db::{table}",
            table_hash,
            int(stats["row_count"] or 0),
            job["source_family"],
            now,
            notes,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, 'source_freshness', ?, ?, 'v1', ?, ?, ?, ?)
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            job["source_family"],
            transform_name,
            table_hash,
            output_hash,
            now,
            notes,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
        """,
        (
            job["source_family"],
            provider,
            f"trading.db:{table}",
            stats.get("max_source_ts"),
            stats.get("max_capture_ts") or now,
            now,
            max(1, max_lag_seconds // 60),
            freshness_status,
            receipt_id,
            now,
            notes,
        ),
    )
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={
            "receipt_id": receipt_id,
            "ref_id": ref_id,
            "edge_id": edge_id,
            "row_count": int(stats["row_count"] or 0),
            "max_source_ts": stats.get("max_source_ts"),
            "freshness_status": freshness_status,
            "freshness_recovered": 1 if freshness_status == "CURRENT_OR_RECENT" else 0,
            "cached_source_only": 1,
            "live_fetch": 0,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
        },
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def _market_bars_stats(con: sqlite3.Connection) -> dict[str, Any]:
    row = con.execute(
        """
        SELECT COUNT(*) AS row_count,
               COUNT(DISTINCT symbol) AS symbol_count,
               MIN(bar_start_ts) AS min_bar_start_ts,
               MAX(bar_start_ts) AS max_bar_start_ts,
               MIN(bar_end_ts) AS min_bar_end_ts,
               MAX(bar_end_ts) AS max_bar_end_ts,
               MIN(last_updated_at) AS min_last_updated_at,
               MAX(last_updated_at) AS max_last_updated_at
        FROM market_bars_5m
        """
    ).fetchone()
    return dict(row)


def _write_market_bars_raw(
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    stats: dict[str, Any],
    table_hash: str,
    freshness_status: str,
) -> tuple[Path, dict[str, Any]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    payload = {
        "source_family": job["source_family"],
        "job_name": job["job_name"],
        "adapter_name": "cached_market_bars_5m",
        "bucket_ts": bucket,
        "captured_at": now,
        "cached_table": "market_bars_5m",
        "live_fetch": False,
        "diagnostic_only": True,
        "table_hash": table_hash,
        "freshness_status": freshness_status,
        "strict_gate_allowed": False,
        "proxy_allowed": False,
        "missing_source_is_negative": False,
        "snapshot_stats": stats,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    path = raw_dir / f"market_bars_5m_cached_{bucket.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, payload


def _run_heartbeat(con: sqlite3.Connection, job: sqlite3.Row, bucket: str, raw_dir: Path) -> JobResult:
    raw_path, payload = _write_heartbeat_raw(job, bucket, raw_dir)
    raw_sha = sha256_file(raw_path)
    now = payload["captured_at"]
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{raw_sha[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
    output_hash = _digest_text(f"{job['source_family']}|source_freshness|{bucket}|{raw_sha}")
    con.execute(
        """
        INSERT OR REPLACE INTO source_receipts(
            receipt_id, provider, source_family, source_key, source_ts, capture_ts,
            available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
            strict_gate_allowed, proxy_allowed, created_at
        )
        VALUES (?, 'local_diagnostic_runtime', ?, ?, ?, ?, ?, ?, ?,
                'capture_time_diagnostic_internal', 0, 0, ?)
        """,
        (receipt_id, job["source_family"], job["job_name"], now, now, now, rel(raw_path), raw_sha, now),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'raw_diagnostic_heartbeat', ?, ?, ?, ?, ?, 'internal heartbeat raw payload')
        """,
        (ref_id, rel(raw_path), raw_sha, raw_path.stat().st_size, job["source_family"], now),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, 'source_freshness', ?, 'diagnostic_heartbeat_freshness_update',
                'v1', ?, ?, ?, 'internal heartbeat updates only its own freshness family')
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            job["source_family"],
            raw_sha,
            output_hash,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, 'local_diagnostic_runtime', ?, ?, ?, ?, 30, 'CURRENT_OR_RECENT',
                0, 0, ?, ?, 'updated by diagnostic-only registered loop heartbeat')
        """,
        (job["source_family"], f"trading.db:{job['source_family']}", now, now, now, receipt_id, now),
    )
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={"receipt_id": receipt_id, "ref_id": ref_id, "edge_id": edge_id},
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def _latest_runtime_decision_row(con: sqlite3.Connection) -> sqlite3.Row | None:
    if not _table_exists(con, "runtime_strategy_decisions"):
        return None
    return con.execute(
        """
        SELECT *
        FROM runtime_strategy_decisions
        ORDER BY created_at DESC, decision_id DESC
        LIMIT 1
        """
    ).fetchone()


def _authority_payload(con: sqlite3.Connection, runtime_row: sqlite3.Row, created_at: str) -> dict[str, Any]:
    freshness_rows = []
    if _table_exists(con, "source_freshness"):
        freshness_rows = [
            dict(row)
            for row in con.execute(
                """
                SELECT source_family, freshness_status, evidence_ref, max_source_ts,
                       strict_gate_allowed, proxy_allowed
                FROM source_freshness
                ORDER BY source_family
                """
            ).fetchall()
        ]
    blockers = [
        str(row["source_family"])
        for row in freshness_rows
        if str(row.get("freshness_status") or "") in {"STALE", "MISSING", "NO_AUTHORITY_EVIDENCE"}
    ]
    receipt_ids = tuple(
        sorted({str(row.get("evidence_ref") or "") for row in freshness_rows if str(row.get("evidence_ref") or "")})
    )
    runtime_id = str(runtime_row["decision_id"])
    runtime_hash = _digest_text(json.dumps(dict(runtime_row), sort_keys=True, default=str))
    return {
        "authority_id": f"single-l6-authority:{runtime_id}",
        "runtime_decision_id": runtime_id,
        "gate": "BLOCKED",
        "paper_order_intent_allowed": False,
        "live_order_allowed": False,
        "reason_codes": [
            "AUTHORITY_EVIDENCE_CHECKED",
            "DIAGNOSTIC_ONLY_CONTROL_STATE",
            "SOURCE_FRESHNESS_BLOCKERS_PRESENT" if blockers else "NO_SOURCE_FRESHNESS_BLOCKER_IN_LEDGER",
            "PAPER_PERMISSION_NOT_GRANTED_BY_DB_LOOP",
        ],
        "valid_from": created_at,
        "valid_until": created_at,
        "source_freshness_blockers": blockers,
        "source_receipt_ids": receipt_ids,
        "lineage": {
            "runtime_decision_hash": runtime_hash,
            "source_freshness_hash": _digest_text(json.dumps(freshness_rows, sort_keys=True, default=str)),
        },
        "latest_runtime_decision": {
            "decision_id": runtime_id,
            "created_at": runtime_row["created_at"],
            "decision_status": runtime_row["decision_status"],
            "symbol": runtime_row["symbol"],
            "reason_code": runtime_row["reason_code"],
            "source_snapshot_id": runtime_row["source_snapshot_id"],
        },
        "permissions": {
            "execution_permitted": 0,
            "broker_mutation_permitted": 0,
            "paper_promotion_permitted": 0,
            "real_capital_permitted": 0,
        },
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }


def _run_authority_evidence_generation(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
) -> JobResult:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_authority_evidence_ledger (
            authority_hash TEXT PRIMARY KEY,
            authority_id TEXT NOT NULL,
            runtime_decision_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    row = _latest_runtime_decision_row(con)
    if row is None:
        reason = "NO_RUNTIME_STRATEGY_DECISIONS_SOURCE"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={
                "source_family": job["source_family"],
                "freshness_recovered": 0,
                "paper_order_intent_allowed": 0,
                "live_order_allowed": 0,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    now = utc_now()
    payload = _authority_payload(con, row, now)
    authority_hash = _digest_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))
    payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    existing = con.execute(
        "SELECT payload_json FROM runtime_authority_evidence_ledger WHERE authority_hash=?",
        (authority_hash,),
    ).fetchone()
    if existing is not None and str(existing["payload_json"]) != payload_json:
        raise ValueError("authority evidence hash collision or mutation attempt")
    if existing is None:
        con.execute(
            """
            INSERT INTO runtime_authority_evidence_ledger(
                authority_hash, authority_id, runtime_decision_id, payload_json, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                authority_hash,
                payload["authority_id"],
                payload["runtime_decision_id"],
                payload_json,
                now,
            ),
        )
    raw_path, raw_payload = _write_cached_table_raw(
        job,
        bucket,
        raw_dir,
        adapter_name="runtime_authority_evidence_generation",
        table="runtime_authority_evidence_ledger",
        stats={
            "row_count": 1,
            "max_source_ts": now,
            "max_capture_ts": now,
            "distinct_count": 1,
            "authority_hash": authority_hash,
            "paper_order_intent_allowed": 0,
            "live_order_allowed": 0,
        },
        table_hash=authority_hash,
        freshness_status="CURRENT_OR_RECENT",
    )
    raw_sha = sha256_file(raw_path)
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{authority_hash[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
    con.execute(
        """
        INSERT OR REPLACE INTO source_receipts(
            receipt_id, provider, source_family, source_key, source_ts, capture_ts,
            available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
            strict_gate_allowed, proxy_allowed, created_at
        )
        VALUES (?, 'local_runtime_authority_validator', ?, ?, ?, ?, ?, ?, ?,
                'authority_evidence_created_at', 0, 0, ?)
        """,
        (
            receipt_id,
            job["source_family"],
            str(payload["runtime_decision_id"]),
            now,
            now,
            now,
            rel(raw_path),
            raw_sha,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'runtime_authority_evidence_payload', ?, ?, ?, ?, ?,
                'blocked authority evidence payload; no paper/live permission opened')
        """,
        (ref_id, rel(raw_path), authority_hash, raw_path.stat().st_size, job["source_family"], now),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, 'runtime_authority_evidence_ledger', ?,
                'runtime_authority_evidence_generation', 'v1', ?, ?, ?,
                'latest L6 runtime decision reviewed into blocked authority evidence')
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            authority_hash,
            authority_hash,
            _digest_text(f"authority|{authority_hash}|{raw_sha}"),
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, 'local_runtime_authority_validator', 'trading.db:runtime_authority_evidence_ledger',
                ?, ?, ?, 10, 'CURRENT_OR_RECENT', 0, 0, ?, ?,
                'authority evidence generated in blocked diagnostic mode; no paper/live gates opened')
        """,
        (job["source_family"], now, now, now, receipt_id, now),
    )
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={
            "receipt_id": receipt_id,
            "ref_id": ref_id,
            "edge_id": edge_id,
            "authority_hash": authority_hash,
            "paper_order_intent_allowed": 0,
            "live_order_allowed": 0,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
        },
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def _freshness_for_ts(con: sqlite3.Connection, source_family: str, source_ts: str | None) -> tuple[str, float | None]:
    parsed = _parse_ts(source_ts)
    if parsed is None:
        return "MISSING", None
    lag_seconds = (datetime.now(UTC) - parsed).total_seconds()
    if lag_seconds <= _policy_max_lag_seconds(con, source_family):
        return "CURRENT_OR_RECENT", lag_seconds
    return "STALE", lag_seconds


def _write_derived_family_evidence(
    con: sqlite3.Connection,
    *,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
    adapter_name: str,
    source_key: str,
    source_ts: str,
    source_time_basis: str,
    target_table: str,
    target_key: str,
    row_count: int,
    distinct_count: int,
    input_hash: str,
    output_hash: str,
    freshness_status: str,
    notes: str,
    validation_extra: dict[str, Any] | None = None,
) -> JobResult:
    raw_path, payload = _write_cached_table_raw(
        job,
        bucket,
        raw_dir,
        adapter_name=adapter_name,
        table=target_table,
        stats={
            "row_count": row_count,
            "distinct_count": distinct_count,
            "max_source_ts": source_ts,
            "max_capture_ts": utc_now(),
            "input_hash": input_hash,
            "output_hash": output_hash,
        },
        table_hash=output_hash,
        freshness_status=freshness_status,
    )
    raw_sha = sha256_file(raw_path)
    now = payload["captured_at"]
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{output_hash[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
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
            adapter_name,
            job["source_family"],
            source_key,
            source_ts,
            now,
            now,
            rel(raw_path),
            raw_sha,
            source_time_basis,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'derived_table_snapshot', ?, ?, ?, ?, ?, ?)
        """,
        (ref_id, rel(raw_path), output_hash, raw_path.stat().st_size, job["source_family"], now, notes),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?, ?)
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            target_table,
            target_key,
            adapter_name,
            input_hash,
            output_hash,
            now,
            notes,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
        """,
        (
            job["source_family"],
            adapter_name,
            f"trading.db:{target_table}",
            source_ts,
            now,
            now,
            max(1, _policy_max_lag_seconds(con, job["source_family"]) // 60),
            freshness_status,
            receipt_id,
            now,
            notes,
        ),
    )
    validation = {
        "receipt_id": receipt_id,
        "ref_id": ref_id,
        "edge_id": edge_id,
        "row_count": row_count,
        "distinct_count": distinct_count,
        "max_source_ts": source_ts,
        "freshness_status": freshness_status,
        "freshness_recovered": 1 if freshness_status == "CURRENT_OR_RECENT" else 0,
        "strict_gate_allowed": 0,
        "proxy_allowed": 0,
        "broker_mutation": 0,
        "paper_order_intent_allowed": 0,
        "live_order_allowed": 0,
    }
    if validation_extra:
        validation.update(validation_extra)
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation=validation,
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def _run_indicator_snapshot_refresh(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
) -> JobResult:
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
    if not _table_exists(con, "market_bars_5m"):
        reason = "NO_MARKET_BARS_5M_SOURCE_FOR_INDICATORS"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"missing_source_is_negative": 0, "freshness_recovered": 0},
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    rows = con.execute(
        """
        SELECT symbol, bar_end_ts, close, high
        FROM market_bars_5m
        WHERE close IS NOT NULL AND high IS NOT NULL
        ORDER BY symbol, bar_end_ts
        """
    ).fetchall()
    if not rows:
        reason = "NO_MARKET_BARS_5M_SOURCE_FOR_INDICATORS"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"missing_source_is_negative": 0, "freshness_recovered": 0},
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)

    by_symbol: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_symbol.setdefault(str(row["symbol"]).upper(), []).append(row)
    now = utc_now()
    inserts = []
    input_digest = hashlib.sha256()
    latest_source_ts = ""
    for symbol in sorted(by_symbol):
        series = by_symbol[symbol]
        latest = series[-1]
        closes = [float(item["close"]) for item in series if item["close"] is not None]
        highs = [float(item["high"]) for item in series if item["high"] is not None]
        bar_end = str(latest["bar_end_ts"])
        latest_source_ts = max(latest_source_ts, bar_end)
        for item in series[-240:]:
            input_digest.update(f"{symbol}|{item['bar_end_ts']}|{item['close']}|{item['high']}\n".encode("utf-8"))
        freshness_status, lag_seconds = _freshness_for_ts(con, "market_bars_5m", bar_end)
        data_fresh = 1 if freshness_status == "CURRENT_OR_RECENT" else 0
        window20 = closes[-20:] or [float(latest["close"])]
        window50 = closes[-50:] or window20
        window200 = closes[-200:] or window50
        high20 = max(highs[-20:] or [float(latest["high"])])
        snapshot_id = f"diag-indicator:{symbol}:{bar_end}"
        inserts.append(
            (
                snapshot_id,
                now,
                symbol,
                bar_end,
                float(latest["close"]),
                sum(window20) / len(window20),
                sum(window50) / len(window50),
                sum(window200) / len(window200),
                high20,
                0,
                0,
                0,
                data_fresh,
                1 if len(closes) < 20 else 0,
                "OBSERVE",
                "NONE",
                "DIAGNOSTIC_INDICATOR_REFRESH_NO_TRADE",
                0.0,
                len(inserts) + 1,
                0,
                bar_end,
                float(latest["close"]),
                "MARKET_BARS_5M_DIAGNOSTIC",
                lag_seconds,
                "" if data_fresh else "UPSTREAM_MARKET_BARS_STALE",
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO indicator_snapshots(
            snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
            breakout_high_20, breakout_condition, ma_condition, entry_allowed,
            data_fresh, insufficient_history, action, side, reason, score,
            candidate_rank, selected_for_portfolio, source_price_ts, source_price,
            source_type, freshness_age_sec, stale_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        inserts,
    )
    input_hash = input_digest.hexdigest()
    output_hash = _digest_text(json.dumps([(row[0], row[2], row[3], row[12]) for row in inserts], sort_keys=True))
    freshness_status, _lag = _freshness_for_ts(con, job["source_family"], latest_source_ts)
    return _write_derived_family_evidence(
        con,
        job=job,
        bucket=bucket,
        raw_dir=raw_dir,
        adapter_name="derived_indicator_snapshots_from_market_bars",
        source_key="trading.db:market_bars_5m",
        source_ts=latest_source_ts,
        source_time_basis="market_bars_5m_bar_end_ts",
        target_table="indicator_snapshots",
        target_key="diagnostic_indicator_snapshots",
        row_count=len(inserts),
        distinct_count=len(by_symbol),
        input_hash=input_hash,
        output_hash=output_hash,
        freshness_status=freshness_status,
        notes="diagnostic indicator rows derived from market_bars_5m; entry_allowed and selected_for_portfolio forced to 0",
    )


def _run_runtime_decision_refresh(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
) -> JobResult:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_strategy_decisions (
            decision_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            decision_status TEXT NOT NULL,
            symbol TEXT,
            side TEXT,
            quantity INTEGER NOT NULL,
            limit_price REAL,
            reason_code TEXT NOT NULL,
            reason_detail TEXT,
            entry_allowed INTEGER NOT NULL,
            data_fresh INTEGER NOT NULL,
            selected_for_portfolio INTEGER NOT NULL,
            score REAL,
            source_snapshot_id TEXT,
            source_price_ts TEXT,
            source_type TEXT,
            used_label_flag INTEGER NOT NULL DEFAULT 0,
            dummy_fallback_used_flag INTEGER NOT NULL DEFAULT 0,
            kis_paper_env_flag INTEGER NOT NULL DEFAULT 0,
            kill_switch_off_flag INTEGER NOT NULL DEFAULT 0,
            created_by_task TEXT NOT NULL,
            regime_state TEXT,
            intraday_state TEXT,
            runtime_state_capture_status TEXT,
            state_source_snapshot_id TEXT
        )
        """
    )
    if not _table_exists(con, "indicator_snapshots"):
        reason = "NO_INDICATOR_SNAPSHOTS_SOURCE_FOR_RUNTIME_DECISIONS"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"missing_source_is_negative": 0, "freshness_recovered": 0},
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    latest = con.execute("SELECT MAX(created_at) AS created_at FROM indicator_snapshots").fetchone()
    latest_created = str(latest["created_at"] or "") if latest else ""
    if not latest_created:
        reason = "NO_INDICATOR_SNAPSHOTS_SOURCE_FOR_RUNTIME_DECISIONS"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"missing_source_is_negative": 0, "freshness_recovered": 0},
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    indicator_rows = con.execute(
        """
        SELECT snapshot_id, created_at, symbol, side, close, entry_allowed, data_fresh,
               selected_for_portfolio, score, source_price_ts, source_type
        FROM indicator_snapshots
        WHERE created_at=?
        ORDER BY symbol, snapshot_id
        """,
        (latest_created,),
    ).fetchall()
    if not indicator_rows:
        reason = "NO_INDICATOR_SNAPSHOTS_SOURCE_FOR_RUNTIME_DECISIONS"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={"missing_source_is_negative": 0, "freshness_recovered": 0},
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)
    now = utc_now()
    inserts = []
    input_digest = hashlib.sha256()
    for row in indicator_rows:
        snapshot_id = str(row["snapshot_id"])
        decision_id = f"diag-runtime:{snapshot_id}"
        input_digest.update(
            f"{snapshot_id}|{row['symbol']}|{row['data_fresh']}|{row['entry_allowed']}|{row['score']}\n".encode("utf-8")
        )
        data_fresh = int(row["data_fresh"] or 0)
        reason_code = "DIAGNOSTIC_RUNTIME_BLOCKED_NO_PAPER_PERMISSION"
        if not data_fresh:
            reason_code = "DIAGNOSTIC_RUNTIME_BLOCKED_STALE_INDICATOR"
        inserts.append(
            (
                decision_id,
                now,
                "BLOCKED",
                str(row["symbol"]).upper(),
                "NONE",
                0,
                row["close"],
                reason_code,
                "DB loop diagnostic runtime decision; no order intent and no paper/live permission",
                0,
                data_fresh,
                0,
                float(row["score"] or 0.0),
                snapshot_id,
                row["source_price_ts"],
                row["source_type"],
                0,
                0,
                0,
                1,
                "Task3761_3800",
                "DIAGNOSTIC_ONLY",
                "DIAGNOSTIC_ONLY",
                "BLOCKED_NO_ORDER_PERMISSION",
                snapshot_id,
            )
        )
    con.executemany(
        """
        INSERT OR REPLACE INTO runtime_strategy_decisions(
            decision_id, created_at, decision_status, symbol, side, quantity,
            limit_price, reason_code, reason_detail, entry_allowed, data_fresh,
            selected_for_portfolio, score, source_snapshot_id, source_price_ts,
            source_type, used_label_flag, dummy_fallback_used_flag,
            kis_paper_env_flag, kill_switch_off_flag, created_by_task,
            regime_state, intraday_state, runtime_state_capture_status,
            state_source_snapshot_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        inserts,
    )
    input_hash = input_digest.hexdigest()
    output_hash = _digest_text(json.dumps([(row[0], row[3], row[4], row[5], row[7]) for row in inserts], sort_keys=True))
    freshness_status, _lag = _freshness_for_ts(con, job["source_family"], now)
    return _write_derived_family_evidence(
        con,
        job=job,
        bucket=bucket,
        raw_dir=raw_dir,
        adapter_name="derived_runtime_strategy_decisions_from_indicators",
        source_key="trading.db:indicator_snapshots",
        source_ts=now,
        source_time_basis="runtime_decision_created_at",
        target_table="runtime_strategy_decisions",
        target_key="diagnostic_runtime_decisions",
        row_count=len(inserts),
        distinct_count=len({row[3] for row in inserts}),
        input_hash=input_hash,
        output_hash=output_hash,
        freshness_status=freshness_status,
        notes="diagnostic runtime decisions from indicator snapshots; quantity=0 side=NONE status=BLOCKED",
    )


def _run_broker_truth_reconciliation_blocker(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
) -> JobResult:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliation_runs(
            reconciliation_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            max_severity TEXT NOT NULL,
            block_new_orders INTEGER NOT NULL,
            summary_text TEXT NOT NULL,
            raw_snapshot_json TEXT
        )
        """
    )
    now = utc_now()
    fixture_env = os.environ.get("TRADER_BRAIN_BROKER_TRUTH_FIXTURE_JSON", "").strip()
    fixture_path = Path(fixture_env) if fixture_env else None
    if fixture_path and fixture_path.exists():
        fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
        broker_orders = fixture_payload.get("broker_orders", [])
        if not isinstance(broker_orders, list):
            raise RuntimeError("BROKER_TRUTH_FIXTURE_SCHEMA_BLOCKED:broker_orders")
        source_ts = str(fixture_payload.get("snapshot_ts") or fixture_payload.get("source_ts") or now)
        clean = str(fixture_payload.get("reconciliation_status") or "CLEAN").upper() == "CLEAN"
        severity = str(fixture_payload.get("max_severity") or ("INFO" if clean else "CRITICAL")).upper()
        block_new_orders = 0 if clean and severity == "INFO" else 1
        payload = {
            "broker_orders": broker_orders,
            "broker_mutation": False,
            "broker_api_called": False,
            "source": "operator_broker_truth_fixture",
            "fixture_path": rel(fixture_path),
            "source_ts": source_ts,
            "block_new_orders": bool(block_new_orders),
            "status": "FIXTURE_RECONCILED" if clean else "FIXTURE_MISMATCH",
        }
        reconciliation_id = f"fixture-broker-truth:{bucket}"
        con.execute(
            """
            INSERT OR REPLACE INTO reconciliation_runs(
                reconciliation_id, run_id, started_at, finished_at, status,
                max_severity, block_new_orders, summary_text, raw_snapshot_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reconciliation_id,
                f"fixture-broker-truth-run:{bucket}",
                now,
                now,
                "CLEAN" if clean else "MISMATCH",
                severity,
                block_new_orders,
                "operator broker truth fixture reconciled without broker API call",
                json.dumps(payload, sort_keys=True),
            ),
        )
        input_hash = _digest_text(json.dumps(payload, sort_keys=True))
        output_hash = _digest_text(f"{reconciliation_id}|{source_ts}|{clean}|{severity}|{block_new_orders}")
        freshness_status, _lag = _freshness_for_ts(con, job["source_family"], source_ts)
        return _write_derived_family_evidence(
            con,
            job=job,
            bucket=bucket,
            raw_dir=raw_dir,
            adapter_name="operator_broker_truth_fixture_reconciliation",
            source_key=f"broker_truth_fixture:{input_hash[:16]}",
            source_ts=source_ts,
            source_time_basis="operator_fixture_snapshot_ts",
            target_table="reconciliation_runs",
            target_key=reconciliation_id,
            row_count=1,
            distinct_count=len(broker_orders),
            input_hash=input_hash,
            output_hash=output_hash,
            freshness_status=freshness_status,
            notes="operator broker-truth fixture source connected; no broker API call and no gate opening",
            validation_extra={
                "broker_api_called": 0,
                "broker_mutation": 0,
                "fixture_source": 1,
                "broker_order_count": len(broker_orders),
                "block_new_orders": block_new_orders,
                "status": "CLEAN" if clean else "MISMATCH",
            },
        )
    payload = {
        "broker_orders": [],
        "broker_mutation": False,
        "broker_api_called": False,
        "source": "diagnostic_no_broker_truth_source",
        "block_new_orders": True,
        "status": "BLOCKED_NO_BROKER_TRUTH_SOURCE",
    }
    reconciliation_id = f"diag-broker-truth:{bucket}"
    con.execute(
        """
        INSERT OR REPLACE INTO reconciliation_runs(
            reconciliation_id, run_id, started_at, finished_at, status,
            max_severity, block_new_orders, summary_text, raw_snapshot_json
        )
        VALUES (?, ?, ?, ?, 'BLOCKED', 'CRITICAL', 1, ?, ?)
        """,
        (
            reconciliation_id,
            f"diag-broker-truth-run:{bucket}",
            now,
            now,
            "broker truth source not configured; diagnostic blocker recorded without broker API call",
            json.dumps(payload, sort_keys=True),
        ),
    )
    input_hash = _digest_text(json.dumps(payload, sort_keys=True))
    output_hash = _digest_text(f"{reconciliation_id}|{now}|BLOCKED|CRITICAL|1")
    freshness_status, _lag = _freshness_for_ts(con, job["source_family"], now)
    return _write_derived_family_evidence(
        con,
        job=job,
        bucket=bucket,
        raw_dir=raw_dir,
        adapter_name="diagnostic_broker_truth_reconciliation",
        source_key="broker_truth_source:not_configured",
        source_ts=now,
        source_time_basis="diagnostic_reconciliation_finished_at",
        target_table="reconciliation_runs",
        target_key=reconciliation_id,
        row_count=1,
        distinct_count=1,
        input_hash=input_hash,
        output_hash=output_hash,
        freshness_status=freshness_status,
        notes="current broker-truth blocker row; no broker API call and no broker truth completion claim",
        validation_extra={"broker_api_called": 0, "block_new_orders": 1, "status": "BLOCKED"},
    )


def _run_cached_market_bars(
    con: sqlite3.Connection,
    job: sqlite3.Row,
    bucket: str,
    raw_dir: Path,
) -> JobResult:
    if not _table_exists(con, "market_bars_5m"):
        reason = "NO_CACHED_MARKET_BARS_5M_SOURCE"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={
                "source_family": job["source_family"],
                "missing_source_is_negative": 0,
                "freshness_recovered": 0,
                "cached_source_only": 1,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)

    columns = _market_bars_columns(con)
    stats = _market_bars_stats(con)
    if int(stats["row_count"] or 0) <= 0:
        reason = "NO_CACHED_MARKET_BARS_5M_SOURCE"
        _write_scheduler_ledger(
            con,
            job_name=job["job_name"],
            bucket=bucket,
            status="SKIPPED",
            skipped_reason=reason,
            validation={
                "source_family": job["source_family"],
                "missing_source_is_negative": 0,
                "freshness_recovered": 0,
                "cached_source_only": 1,
            },
        )
        return JobResult(job["job_name"], job["source_family"], "SKIPPED", reason)

    max_source = _parse_ts(stats.get("max_bar_end_ts"))
    max_lag_seconds = _policy_max_lag_seconds(con, job["source_family"])
    freshness_status = "STALE"
    if max_source is not None:
        lag_seconds = (datetime.now(UTC) - max_source).total_seconds()
        if lag_seconds <= max_lag_seconds:
            freshness_status = "CURRENT_OR_RECENT"

    table_hash = _hash_market_bars_table(con, columns)
    raw_path, payload = _write_market_bars_raw(job, bucket, raw_dir, stats, table_hash, freshness_status)
    raw_sha = sha256_file(raw_path)
    now = payload["captured_at"]
    receipt_id = f"receipt:{job['source_family']}:{bucket}"
    ref_id = f"ref:{job['source_family']}:{table_hash[:16]}"
    edge_id = f"edge:{job['source_family']}:{bucket}"
    output_hash = _digest_text(
        f"{job['source_family']}|source_freshness|{stats.get('max_bar_end_ts')}|{table_hash}|{freshness_status}"
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_receipts(
            receipt_id, provider, source_family, source_key, source_ts, capture_ts,
            available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
            strict_gate_allowed, proxy_allowed, created_at
        )
        VALUES (?, 'trading_db_cached_market_bars_5m', ?, ?, ?, ?, ?, ?, ?,
                'cached_table_bar_end_ts', 0, 0, ?)
        """,
        (
            receipt_id,
            job["source_family"],
            "trading.db:market_bars_5m",
            stats.get("max_bar_end_ts"),
            now,
            now,
            rel(raw_path),
            raw_sha,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO reference_hashes(
            ref_id, ref_type, path_or_key, sha256, size_bytes, source_family, created_at, notes
        )
        VALUES (?, 'cached_table_snapshot', 'trading.db::market_bars_5m', ?, ?, ?, ?,
                'deterministic cached market_bars_5m table hash; not live source freshness')
        """,
        (ref_id, table_hash, int(stats["row_count"] or 0), job["source_family"], now),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO data_lineage_edges(
            edge_id, source_family, source_receipt_id, input_ref_id, target_table,
            target_key, transform_name, transform_version, input_hash, output_hash,
            created_at, notes
        )
        VALUES (?, ?, ?, ?, 'source_freshness', ?, 'cached_market_bars_5m_freshness_update',
                'v1', ?, ?, ?, 'cached DB table evidence only; stale cached evidence does not open gates')
        """,
        (
            edge_id,
            job["source_family"],
            receipt_id,
            ref_id,
            job["source_family"],
            table_hash,
            output_hash,
            now,
        ),
    )
    con.execute(
        """
        INSERT OR REPLACE INTO source_freshness(
            source_family, provider, storage_ref, max_source_ts, max_capture_ts,
            max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
            strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        )
        VALUES (?, 'trading_db_cached_market_bars_5m', 'trading.db:market_bars_5m',
                ?, ?, ?, ?, ?, 0, 0, ?, ?,
                'cached market_bars_5m table snapshot; live fetch disabled; stale remains blocker')
        """,
        (
            job["source_family"],
            stats.get("max_bar_end_ts"),
            stats.get("max_last_updated_at") or now,
            now,
            max(1, max_lag_seconds // 60),
            freshness_status,
            receipt_id,
            now,
        ),
    )
    _write_scheduler_ledger(
        con,
        job_name=job["job_name"],
        bucket=bucket,
        status="SUCCESS",
        skipped_reason="",
        validation={
            "receipt_id": receipt_id,
            "ref_id": ref_id,
            "edge_id": edge_id,
            "row_count": int(stats["row_count"] or 0),
            "symbol_count": int(stats["symbol_count"] or 0),
            "max_bar_end_ts": stats.get("max_bar_end_ts"),
            "freshness_status": freshness_status,
            "freshness_recovered": 1 if freshness_status == "CURRENT_OR_RECENT" else 0,
            "cached_source_only": 1,
            "live_fetch": 0,
            "strict_gate_allowed": 0,
            "proxy_allowed": 0,
        },
    )
    return JobResult(job["job_name"], job["source_family"], "SUCCESS", "", receipt_id, ref_id, edge_id)


def run_once(
    *,
    db_path: Path = ACTIVE_DB,
    apply: bool = False,
    only_job: str | None = None,
    bucket: str | None = None,
    raw_dir: Path = RAW_HEARTBEAT_DIR,
    market_bars_raw_dir: Path = RAW_MARKET_BARS_DIR,
) -> dict[str, Any]:
    bucket_ts = bucket or _bucket_ts()
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        _guard(con)
        jobs = _jobs(con, only_job)
        results: list[JobResult] = []
        if not apply:
            return {
                "status": "DRY_RUN_OK_NO_MUTATION",
                "bucket_ts": bucket_ts,
                "jobs_seen": len(jobs),
                "jobs_with_adapters": sorted(ADAPTERS),
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        for job in jobs:
            _validate_permissions(job)
            with con:
                adapter = ADAPTERS.get(job["job_name"]) or ADAPTER_SOURCE_FAMILIES.get(job["source_family"])
                if adapter == "internal_heartbeat":
                    results.append(_run_heartbeat(con, job, bucket_ts, raw_dir))
                elif adapter == "runtime_authority_evidence_generation":
                    results.append(_run_authority_evidence_generation(con, job, bucket_ts, RAW_CACHED_TABLE_DIR))
                elif adapter == "derived_frontend_read_models_lineage":
                    results.append(
                        _run_derived_artifact_lineage(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                        )
                    )
                elif adapter == "derived_catalog_report_artifacts_lineage":
                    results.append(
                        _run_derived_artifact_lineage(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                        )
                    )
                elif adapter == "cached_market_bars_5m":
                    results.append(_run_cached_market_bars(con, job, bucket_ts, market_bars_raw_dir))
                elif adapter == "cached_market_ticks_intraday":
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="market_ticks",
                            source_ts_column="timestamp",
                            capture_ts_column="created_at",
                            order_columns=["symbol", "timestamp", "tick_id"],
                            distinct_column="symbol",
                            missing_reason="NO_CACHED_MARKET_TICKS_INTRADAY_SOURCE",
                            provider="trading_db_cached_market_ticks",
                            source_time_basis="cached_tick_timestamp",
                            transform_name="cached_market_ticks_intraday_freshness_update",
                            notes="cached market_ticks evidence only; live fetch disabled; stale remains blocker",
                        )
                    )
                elif adapter == "diagnostic_broker_truth_reconciliation":
                    results.append(_run_broker_truth_reconciliation_blocker(con, job, bucket_ts, RAW_CACHED_TABLE_DIR))
                elif adapter == "cached_authority_evidence_ledger":
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="runtime_authority_evidence_ledger",
                            source_ts_column="created_at",
                            capture_ts_column="created_at",
                            order_columns=["created_at", "authority_hash"],
                            distinct_column="runtime_decision_id",
                            missing_reason="NO_CACHED_AUTHORITY_EVIDENCE_LEDGER_SOURCE",
                            provider="trading_db_cached_authority_evidence_ledger",
                            source_time_basis="cached_authority_evidence_created_at",
                            transform_name="cached_authority_evidence_freshness_update",
                            notes="cached authority evidence ledger only; empty ledger remains hard blocker",
                        )
                    )
                elif adapter == "derived_runtime_strategy_decisions_from_indicators":
                    results.append(_run_runtime_decision_refresh(con, job, bucket_ts, RAW_CACHED_TABLE_DIR))
                elif adapter == "cached_daily_ohlcv":
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="daily_ohlcv",
                            source_ts_column="source_ts",
                            capture_ts_column="capture_ts",
                            order_columns=["symbol", "session_date", "provider"],
                            distinct_column="symbol",
                            missing_reason="NO_CACHED_DAILY_OHLCV_SOURCE",
                            provider="trading_db_cached_daily_ohlcv",
                            source_time_basis="cached_daily_source_ts",
                            transform_name="cached_daily_ohlcv_freshness_update",
                            notes="cached daily_ohlcv provider acquisition evidence; gates remain closed until certification",
                        )
                    )
                elif adapter == "cached_macro_rates":
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="macro_rates",
                            source_ts_column="source_ts",
                            capture_ts_column="capture_ts",
                            order_columns=["series_id", "observation_date", "provider"],
                            distinct_column="series_id",
                            missing_reason="NO_CACHED_MACRO_RATES_SOURCE",
                            provider="trading_db_cached_macro_rates",
                            source_time_basis="cached_macro_source_ts_no_vintage_certification",
                            transform_name="cached_macro_rates_freshness_update",
                            notes="cached macro_rates provider acquisition evidence; no-vintage rows remain diagnostic",
                        )
                    )
                elif adapter == "cached_sec_events":
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="sec_events",
                            source_ts_column="source_ts",
                            capture_ts_column="capture_ts",
                            order_columns=["ticker", "accepted_at", "accession_no"],
                            distinct_column="ticker",
                            missing_reason="NO_CACHED_SEC_EVENTS_SOURCE",
                            provider="trading_db_cached_sec_events",
                            source_time_basis="cached_sec_accepted_or_filed_ts",
                            transform_name="cached_sec_events_freshness_update",
                            notes="cached sec_events provider acquisition evidence; missing SEC source remains blocker",
                        )
                    )
                elif adapter == "cached_news_event_l0":
                    missing_reason = f"NO_CACHED_{str(job['source_family']).upper()}_SOURCE"
                    results.append(
                        _run_cached_table_snapshot(
                            con,
                            job,
                            bucket_ts,
                            RAW_CACHED_TABLE_DIR,
                            adapter_name=adapter,
                            table="news_event_l0",
                            source_ts_column="publication_ts",
                            capture_ts_column="collection_ts",
                            order_columns=["source_family", "publication_ts", "provider", "provider_item_id", "raw_item_id"],
                            distinct_column="raw_item_id",
                            missing_reason=missing_reason,
                            provider=f"trading_db_cached_{job['source_family']}",
                            source_time_basis="cached_news_publication_ts",
                            transform_name=f"cached_{job['source_family']}_freshness_update",
                            notes="cached news L0 evidence only; L1 promotion and strict gates remain closed until certification",
                            where_sql='"source_family"=?',
                            where_params=(str(job["source_family"]),),
                        )
                    )
                elif adapter == "derived_indicator_snapshots_from_market_bars":
                    results.append(_run_indicator_snapshot_refresh(con, job, bucket_ts, RAW_CACHED_TABLE_DIR))
                else:
                    reason = "NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY"
                    _write_scheduler_ledger(
                        con,
                        job_name=job["job_name"],
                        bucket=bucket_ts,
                        status="SKIPPED",
                        skipped_reason=reason,
                        validation={
                            "source_family": job["source_family"],
                            "missing_source_is_negative": 0,
                            "freshness_recovered": 0,
                        },
                    )
                    results.append(JobResult(job["job_name"], job["source_family"], "SKIPPED", reason))
        return {
            "status": "APPLIED_DIAGNOSTIC_ONLY",
            "bucket_ts": bucket_ts,
            "jobs_seen": len(jobs),
            "success_count": sum(1 for row in results if row.status == "SUCCESS"),
            "skipped_count": sum(1 for row in results if row.status == "SKIPPED"),
            "results": [row.__dict__ for row in results],
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run registered DB loop jobs once in diagnostic-only mode.")
    parser.add_argument("--db-path", type=Path, default=ACTIVE_DB)
    parser.add_argument("--apply", action="store_true", help="Write scheduler/receipt/hash/lineage evidence.")
    parser.add_argument("--job", help="Optional single job_name filter.")
    parser.add_argument("--bucket-ts", help="Optional bucket timestamp for tests/controlled runs.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_HEARTBEAT_DIR)
    parser.add_argument("--market-bars-raw-dir", type=Path, default=RAW_MARKET_BARS_DIR)
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()
    result = run_once(
        db_path=args.db_path,
        apply=args.apply,
        only_job=args.job,
        bucket=args.bucket_ts,
        raw_dir=args.raw_dir,
        market_bars_raw_dir=args.market_bars_raw_dir,
    )
    if args.json:
        write_json(args.json, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
