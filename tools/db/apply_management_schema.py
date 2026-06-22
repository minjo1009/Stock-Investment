from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from .common import ACTIVE_DB, connect_readonly, sqlite_meta, utc_now


MIGRATION_ID = "task3641_db_loop_contract_schema_v1"
MIGRATION_CHECKSUM = "task3641_scheduler_registry_freshness_policy_reference_hashes_lineage_v1"

CADENCE_SPECS = [
    {
        "job_name": "market_ticks_intraday_refresh",
        "source_family": "market_ticks_intraday",
        "cadence_seconds": 300,
        "max_lag_seconds": 600,
        "market_window": "US_REGULAR",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "provider_intraday",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "tick timestamp",
        "notes": "hard blocker for intraday tick freshness claims",
    },
    {
        "job_name": "market_bars_5m_refresh",
        "source_family": "market_bars_5m",
        "cadence_seconds": 600,
        "max_lag_seconds": 1200,
        "market_window": "US_REGULAR",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "provider_5m_bars",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "bar end timestamp",
        "notes": "hard blocker for 5m read model freshness claims",
    },
    {
        "job_name": "indicator_snapshots_refresh",
        "source_family": "indicator_snapshots",
        "cadence_seconds": 600,
        "max_lag_seconds": 1200,
        "market_window": "US_REGULAR",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "local indicator snapshot builder",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "indicator bar_end_ts",
        "notes": "hard blocker for runtime read model indicator freshness claims",
    },
    {
        "job_name": "runtime_strategy_decisions_refresh",
        "source_family": "runtime_strategy_decisions",
        "cadence_seconds": 600,
        "max_lag_seconds": 1200,
        "market_window": "MANUAL_DIAGNOSTIC",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Backend Operations / Execution Safety",
        "provider_owner": "L6 runtime decision store",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "runtime decision created_at",
        "notes": "hard blocker for latest L6 decision authority claims",
    },
    {
        "job_name": "daily_ohlcv_refresh",
        "source_family": "daily_ohlcv",
        "cadence_seconds": 86400,
        "max_lag_seconds": 129600,
        "market_window": "MANUAL_DIAGNOSTIC",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "provider_daily",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "daily bar date",
        "notes": "after-close plus next-morning verification policy",
    },
    {
        "job_name": "sec_events_refresh",
        "source_family": "sec_events",
        "cadence_seconds": 3600,
        "max_lag_seconds": 86400,
        "market_window": "ALWAYS",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "SEC/derived events",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "filing acceptance timestamp",
        "notes": "receipt and lineage required before event-source claims",
    },
    {
        "job_name": "macro_rates_refresh",
        "source_family": "macro_rates",
        "cadence_seconds": 3600,
        "max_lag_seconds": 86400,
        "market_window": "US_REGULAR",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Data Operations / Runtime DB Governance",
        "provider_owner": "FRED/rates/macro",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "release timestamp",
        "notes": "freshness required for macro regime claims",
    },
    {
        "job_name": "broker_truth_reconciliation_refresh",
        "source_family": "broker_truth_reconciliation",
        "cadence_seconds": 86400,
        "max_lag_seconds": 86400,
        "market_window": "MANUAL_DIAGNOSTIC",
        "requires_receipt": 1,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Backend Operations / Execution Safety",
        "provider_owner": "KIS paper truth fixture/source",
        "run_boundary": "DIAGNOSTIC_ONLY_NO_BROKER_MUTATION",
        "freshness_basis": "broker truth snapshot timestamp",
        "notes": "broker mutation forbidden; stale/absent blocks broker truth claims",
    },
    {
        "job_name": "diagnostic_runtime_heartbeats_refresh",
        "source_family": "diagnostic_runtime_heartbeats",
        "cadence_seconds": 300,
        "max_lag_seconds": 1800,
        "market_window": "ALWAYS",
        "requires_receipt": 0,
        "requires_lineage": 0,
        "downstream_blocker": 1,
        "owner": "Backend Operations / Execution Safety",
        "provider_owner": "local runtime",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "heartbeat persisted timestamp",
        "notes": "5-minute safety heartbeat and 10-minute brain heartbeat family",
    },
    {
        "job_name": "l6_authority_evidence_refresh",
        "source_family": "authority_evidence_ledger",
        "cadence_seconds": 600,
        "max_lag_seconds": 600,
        "market_window": "MANUAL_DIAGNOSTIC",
        "requires_receipt": 0,
        "requires_lineage": 1,
        "downstream_blocker": 1,
        "owner": "Backend Operations / Execution Safety",
        "provider_owner": "L6 runtime authority",
        "run_boundary": "DIAGNOSTIC_ONLY",
        "freshness_basis": "runtime authority evidence timestamp",
        "notes": "missing authority evidence is a hard blocker",
    },
    {
        "job_name": "frontend_read_models_refresh",
        "source_family": "frontend_read_models",
        "cadence_seconds": 60,
        "max_lag_seconds": 300,
        "market_window": "ALWAYS",
        "requires_receipt": 0,
        "requires_lineage": 1,
        "downstream_blocker": 0,
        "owner": "Frontend iOS / Read-only Trading Cockpit",
        "provider_owner": "local read model builder",
        "run_boundary": "READ_ONLY",
        "freshness_basis": "upstream source freshness",
        "notes": "must not present stale upstream as current",
    },
    {
        "job_name": "catalog_report_artifacts_refresh",
        "source_family": "catalog_report_artifacts",
        "cadence_seconds": 1800,
        "max_lag_seconds": 3600,
        "market_window": "ALWAYS",
        "requires_receipt": 0,
        "requires_lineage": 1,
        "downstream_blocker": 0,
        "owner": "Data Operations / Reporting",
        "provider_owner": "report/catalog generator",
        "run_boundary": "READ_ONLY",
        "freshness_basis": "originating scheduler run",
        "notes": "artifact lineage required before freshness claims",
    },
]


def _guard(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys=ON")
    control = con.execute(
        "SELECT run_mode, kill_switch_active FROM control_state WHERE control_key='default'"
    ).fetchone()
    if not control or control[0] != "DIAGNOSTIC_ONLY" or int(control[1]) != 1:
        raise RuntimeError("CONTROL_STATE_BLOCKED")
    active_rows = con.execute(
        "SELECT db_path FROM db_authority_manifest WHERE status='ACTIVE'"
    ).fetchall()
    if len(active_rows) != 1 or active_rows[0][0] != "trading.db":
        raise RuntimeError("ACTIVE_DB_AUTHORITY_BLOCKED")
    if sqlite_meta(ACTIVE_DB)["integrity_status"] != "ok":
        raise RuntimeError("ACTIVE_DB_INTEGRITY_BLOCKED")


def _create_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS scheduler_job_registry (
            job_name TEXT PRIMARY KEY,
            source_family TEXT NOT NULL,
            cadence_seconds INTEGER NOT NULL CHECK(cadence_seconds > 0),
            max_lag_seconds INTEGER NOT NULL CHECK(max_lag_seconds >= cadence_seconds),
            market_window TEXT NOT NULL CHECK(market_window IN ('ALWAYS','US_REGULAR','US_PREMARKET','US_POSTMARKET','WEEKEND_ALLOWED','MANUAL_DIAGNOSTIC')),
            enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
            diagnostic_only INTEGER NOT NULL DEFAULT 1 CHECK(diagnostic_only = 1),
            execution_permitted INTEGER NOT NULL DEFAULT 0 CHECK(execution_permitted = 0),
            broker_mutation_permitted INTEGER NOT NULL DEFAULT 0 CHECK(broker_mutation_permitted = 0),
            real_capital_permitted INTEGER NOT NULL DEFAULT 0 CHECK(real_capital_permitted = 0),
            paper_promotion_permitted INTEGER NOT NULL DEFAULT 0 CHECK(paper_promotion_permitted = 0),
            requires_receipt INTEGER NOT NULL CHECK(requires_receipt IN (0,1)),
            requires_lineage INTEGER NOT NULL CHECK(requires_lineage IN (0,1)),
            downstream_blocker INTEGER NOT NULL CHECK(downstream_blocker IN (0,1)),
            owner TEXT NOT NULL,
            notes TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_freshness_policy (
            source_family TEXT PRIMARY KEY,
            target_cadence_seconds INTEGER NOT NULL CHECK(target_cadence_seconds > 0),
            max_lag_seconds INTEGER NOT NULL CHECK(max_lag_seconds >= target_cadence_seconds),
            hard_blocker INTEGER NOT NULL CHECK(hard_blocker IN (0,1)),
            provider_owner TEXT NOT NULL,
            run_boundary TEXT NOT NULL,
            freshness_basis TEXT NOT NULL,
            missing_semantics TEXT NOT NULL DEFAULT 'UNKNOWN_BLOCKER' CHECK(missing_semantics = 'UNKNOWN_BLOCKER'),
            stale_semantics TEXT NOT NULL DEFAULT 'UNKNOWN_BLOCKER' CHECK(stale_semantics = 'UNKNOWN_BLOCKER'),
            notes TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reference_hashes (
            ref_id TEXT PRIMARY KEY,
            ref_type TEXT NOT NULL,
            path_or_key TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
            source_family TEXT NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL,
            UNIQUE(ref_type, path_or_key, sha256)
        );

        CREATE TABLE IF NOT EXISTS data_lineage_edges (
            edge_id TEXT PRIMARY KEY,
            source_family TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            input_ref_id TEXT NOT NULL,
            target_table TEXT NOT NULL,
            target_key TEXT NOT NULL,
            transform_name TEXT NOT NULL,
            transform_version TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL,
            FOREIGN KEY(source_receipt_id) REFERENCES source_receipts(receipt_id),
            FOREIGN KEY(input_ref_id) REFERENCES reference_hashes(ref_id),
            UNIQUE(source_family, source_receipt_id, input_ref_id, target_table, target_key, transform_name, transform_version)
        );

        CREATE INDEX IF NOT EXISTS idx_scheduler_job_registry_family
            ON scheduler_job_registry(source_family);
        CREATE INDEX IF NOT EXISTS idx_source_freshness_policy_blocker
            ON source_freshness_policy(hard_blocker, source_family);
        CREATE INDEX IF NOT EXISTS idx_reference_hashes_family
            ON reference_hashes(source_family, ref_type);
        CREATE INDEX IF NOT EXISTS idx_data_lineage_edges_family_target
            ON data_lineage_edges(source_family, target_table, target_key);

        CREATE TABLE IF NOT EXISTS daily_ohlcv (
            provider TEXT NOT NULL,
            symbol TEXT NOT NULL,
            session_date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume REAL,
            dividends REAL,
            splits REAL,
            source_ts TEXT NOT NULL,
            capture_ts TEXT NOT NULL,
            available_to_brain_ts TEXT NOT NULL,
            source_time_basis TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(provider, symbol, session_date)
        );

        CREATE TABLE IF NOT EXISTS macro_rates (
            provider TEXT NOT NULL,
            series_id TEXT NOT NULL,
            observation_date TEXT NOT NULL,
            vintage_ts TEXT NOT NULL,
            value REAL,
            units TEXT,
            source_ts TEXT NOT NULL,
            capture_ts TEXT NOT NULL,
            available_to_brain_ts TEXT NOT NULL,
            source_time_basis TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(provider, series_id, observation_date, vintage_ts)
        );

        CREATE TABLE IF NOT EXISTS sec_events (
            provider TEXT NOT NULL,
            cik TEXT NOT NULL,
            ticker TEXT,
            accession_no TEXT NOT NULL,
            form_type TEXT NOT NULL,
            filed_at TEXT,
            accepted_at TEXT,
            period_of_report TEXT,
            event_type TEXT NOT NULL,
            source_url TEXT,
            source_ts TEXT NOT NULL,
            capture_ts TEXT NOT NULL,
            available_to_brain_ts TEXT NOT NULL,
            source_time_basis TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            parser_version TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(provider, accession_no, form_type, event_type)
        );

        CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_symbol_date
            ON daily_ohlcv(symbol, session_date);
        CREATE INDEX IF NOT EXISTS idx_macro_rates_series_date
            ON macro_rates(series_id, observation_date);
        CREATE INDEX IF NOT EXISTS idx_sec_events_ticker_accepted
            ON sec_events(ticker, accepted_at);

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


def _seed(con: sqlite3.Connection, now: str) -> None:
    for spec in CADENCE_SPECS:
        con.execute(
            """
            INSERT INTO scheduler_job_registry(
                job_name, source_family, cadence_seconds, max_lag_seconds, market_window,
                enabled, diagnostic_only, execution_permitted, broker_mutation_permitted,
                real_capital_permitted, paper_promotion_permitted, requires_receipt,
                requires_lineage, downstream_blocker, owner, notes, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 1, 1, 0, 0, 0, 0, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_name) DO UPDATE SET
                source_family=excluded.source_family,
                cadence_seconds=excluded.cadence_seconds,
                max_lag_seconds=excluded.max_lag_seconds,
                market_window=excluded.market_window,
                enabled=excluded.enabled,
                diagnostic_only=excluded.diagnostic_only,
                execution_permitted=excluded.execution_permitted,
                broker_mutation_permitted=excluded.broker_mutation_permitted,
                real_capital_permitted=excluded.real_capital_permitted,
                paper_promotion_permitted=excluded.paper_promotion_permitted,
                requires_receipt=excluded.requires_receipt,
                requires_lineage=excluded.requires_lineage,
                downstream_blocker=excluded.downstream_blocker,
                owner=excluded.owner,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (
                spec["job_name"],
                spec["source_family"],
                spec["cadence_seconds"],
                spec["max_lag_seconds"],
                spec["market_window"],
                spec["requires_receipt"],
                spec["requires_lineage"],
                spec["downstream_blocker"],
                spec["owner"],
                spec["notes"],
                now,
            ),
        )
        con.execute(
            """
            INSERT INTO source_freshness_policy(
                source_family, target_cadence_seconds, max_lag_seconds, hard_blocker,
                provider_owner, run_boundary, freshness_basis, missing_semantics,
                stale_semantics, notes, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'UNKNOWN_BLOCKER', 'UNKNOWN_BLOCKER', ?, ?)
            ON CONFLICT(source_family) DO UPDATE SET
                target_cadence_seconds=excluded.target_cadence_seconds,
                max_lag_seconds=excluded.max_lag_seconds,
                hard_blocker=excluded.hard_blocker,
                provider_owner=excluded.provider_owner,
                run_boundary=excluded.run_boundary,
                freshness_basis=excluded.freshness_basis,
                missing_semantics=excluded.missing_semantics,
                stale_semantics=excluded.stale_semantics,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (
                spec["source_family"],
                spec["cadence_seconds"],
                spec["max_lag_seconds"],
                spec["downstream_blocker"],
                spec["provider_owner"],
                spec["run_boundary"],
                spec["freshness_basis"],
                spec["notes"],
                now,
            ),
        )
    con.execute(
        """
        INSERT OR REPLACE INTO schema_migrations(
            migration_id, applied_at, checksum, owning_module, description
        )
        VALUES (?, ?, ?, 'tools.db.apply_management_schema',
                'DB loop contract tables with diagnostic-only permission checks')
        """,
        (MIGRATION_ID, now, MIGRATION_CHECKSUM),
    )


def apply_schema(db_path: Path = ACTIVE_DB) -> dict[str, object]:
    before = sqlite_meta(db_path)
    if before["integrity_status"] != "ok":
        raise RuntimeError(f"pre_integrity_failed:{before['integrity_status']}")
    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        _guard(con)
        now = utc_now()
        with con:
            _create_schema(con)
            _seed(con, now)
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise RuntimeError(f"foreign_key_check_failed:{len(fk)}")
    finally:
        con.close()
    after = sqlite_meta(db_path)
    if after["integrity_status"] != "ok":
        raise RuntimeError(f"post_integrity_failed:{after['integrity_status']}")
    return {
        "migration_id": MIGRATION_ID,
        "status": "APPLIED",
        "before_sha256": before["sha256"],
        "after_sha256": after["sha256"],
        "before_table_count": before["table_count"],
        "after_table_count": after["table_count"],
        "applied_at": utc_now(),
    }


def dry_run() -> dict[str, object]:
    con = connect_readonly(ACTIVE_DB)
    try:
        _guard(con)
    finally:
        con.close()
    return {
        "migration_id": MIGRATION_ID,
        "status": "DRY_RUN_OK_NO_MUTATION",
        "jobs_to_seed": len(CADENCE_SPECS),
        "tables_to_create": [
            "scheduler_job_registry",
            "source_freshness_policy",
            "reference_hashes",
            "data_lineage_edges",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply guarded DB loop contract management schema.")
    parser.add_argument("--apply", action="store_true", help="Actually mutate active DB. Omitted means dry-run.")
    args = parser.parse_args()
    result = apply_schema() if args.apply else dry_run()
    print(result)


if __name__ == "__main__":
    main()
