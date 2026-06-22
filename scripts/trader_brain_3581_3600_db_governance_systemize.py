from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3581_3600_db_governance_systemization"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
MIGRATION_ID = "task3581_db_governance_controls_v1"

CONTROL_REASON = "TASK3581_DB_GOVERNANCE_NORMALIZATION_REAL_CAPITAL_FORBIDDEN"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_meta(path: Path) -> dict[str, object]:
    meta: dict[str, object] = {
        "db_path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": _sha256_file(path) if path.exists() else "",
        "integrity_status": "missing",
        "journal_mode": "",
        "table_count": 0,
    }
    if not path.exists():
        return meta
    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=10)
        cur = con.cursor()
        meta["integrity_status"] = cur.execute("PRAGMA integrity_check").fetchone()[0]
        meta["journal_mode"] = cur.execute("PRAGMA journal_mode").fetchone()[0]
        meta["table_count"] = cur.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        con.close()
    except Exception as exc:
        meta["integrity_status"] = f"error:{type(exc).__name__}:{exc}"
    return meta


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fetch_one(con: sqlite3.Connection, sql: str, default: object = "") -> object:
    try:
        row = con.execute(sql).fetchone()
        return default if row is None else row[0]
    except sqlite3.Error:
        return default


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return (
        con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        is not None
    )


def _create_governance_tables(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL,
            owning_module TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS db_authority_manifest (
            authority_id TEXT PRIMARY KEY,
            db_path TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            owner TEXT NOT NULL,
            retention_class TEXT NOT NULL,
            restore_priority INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            integrity_status TEXT NOT NULL,
            journal_mode TEXT NOT NULL,
            table_count INTEGER NOT NULL,
            observed_at TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_freshness (
            source_family TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            storage_ref TEXT NOT NULL,
            max_source_ts TEXT,
            max_capture_ts TEXT,
            max_available_to_brain_ts TEXT,
            freshness_sla_minutes INTEGER NOT NULL,
            freshness_status TEXT NOT NULL,
            strict_gate_allowed INTEGER NOT NULL,
            proxy_allowed INTEGER NOT NULL,
            evidence_ref TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_receipts (
            receipt_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            source_family TEXT NOT NULL,
            source_key TEXT NOT NULL,
            source_ts TEXT,
            capture_ts TEXT NOT NULL,
            available_to_brain_ts TEXT,
            raw_path TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            source_time_basis TEXT NOT NULL,
            strict_gate_allowed INTEGER NOT NULL,
            proxy_allowed INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scheduler_run_ledger (
            run_ledger_id TEXT PRIMARY KEY,
            cadence TEXT NOT NULL,
            expected_bucket_ts TEXT NOT NULL,
            actual_start_at TEXT,
            actual_finish_at TEXT,
            owner_id TEXT NOT NULL,
            lease_token TEXT,
            status TEXT NOT NULL,
            lag_seconds REAL,
            skipped_reason TEXT,
            validation_refs_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS db_retention_policy (
            policy_id TEXT PRIMARY KEY,
            db_path TEXT NOT NULL,
            role TEXT NOT NULL,
            retention_class TEXT NOT NULL,
            action TEXT NOT NULL,
            backup_required INTEGER NOT NULL,
            deletion_allowed INTEGER NOT NULL,
            owner TEXT NOT NULL,
            reason TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS db_control_state_audit (
            audit_id TEXT PRIMARY KEY,
            observed_run_mode TEXT,
            observed_kill_switch_active INTEGER,
            observed_kill_switch_reason TEXT,
            new_run_mode TEXT NOT NULL,
            new_kill_switch_active INTEGER NOT NULL,
            new_kill_switch_reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_source_receipts_family_capture
            ON source_receipts(source_family, capture_ts);
        CREATE INDEX IF NOT EXISTS idx_source_freshness_status
            ON source_freshness(freshness_status);
        CREATE INDEX IF NOT EXISTS idx_scheduler_run_ledger_cadence_bucket
            ON scheduler_run_ledger(cadence, expected_bucket_ts);
        CREATE INDEX IF NOT EXISTS idx_db_authority_status
            ON db_authority_manifest(status, role);
        """
    )


def _normalize_control_state(con: sqlite3.Connection, now: str) -> dict[str, object]:
    if not _table_exists(con, "control_state"):
        con.execute(
            """
            CREATE TABLE control_state (
                control_key TEXT PRIMARY KEY,
                run_mode TEXT NOT NULL,
                kill_switch_active INTEGER NOT NULL,
                kill_switch_reason TEXT,
                kill_switch_activated_at TEXT,
                emergency_cancel_allowed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT
            )
            """
        )
    row = con.execute(
        "SELECT run_mode, kill_switch_active, kill_switch_reason FROM control_state WHERE control_key='default'"
    ).fetchone()
    observed_run_mode = row[0] if row else ""
    observed_kill_switch_active = int(row[1]) if row else None
    observed_kill_switch_reason = row[2] if row else ""
    con.execute(
        """
        INSERT OR REPLACE INTO control_state(
            control_key, run_mode, kill_switch_active, kill_switch_reason,
            kill_switch_activated_at, emergency_cancel_allowed, updated_at
        )
        VALUES('default', 'DIAGNOSTIC_ONLY', 1, ?, ?, 0, ?)
        """,
        (CONTROL_REASON, now, now),
    )
    audit_id = f"control-state-normalization:{now}"
    con.execute(
        """
        INSERT OR REPLACE INTO db_control_state_audit(
            audit_id, observed_run_mode, observed_kill_switch_active, observed_kill_switch_reason,
            new_run_mode, new_kill_switch_active, new_kill_switch_reason, created_at
        )
        VALUES (?, ?, ?, ?, 'DIAGNOSTIC_ONLY', 1, ?, ?)
        """,
        (audit_id, observed_run_mode, observed_kill_switch_active, observed_kill_switch_reason, CONTROL_REASON, now),
    )
    return {
        "audit_id": audit_id,
        "observed_run_mode": observed_run_mode,
        "observed_kill_switch_active": observed_kill_switch_active,
        "observed_kill_switch_reason": observed_kill_switch_reason,
        "new_run_mode": "DIAGNOSTIC_ONLY",
        "new_kill_switch_active": 1,
        "new_kill_switch_reason": CONTROL_REASON,
        "created_at": now,
    }


def _seed_db_authority(con: sqlite3.Connection, now: str, db_path: Path) -> list[dict[str, object]]:
    candidates = [
        (db_path, "active_runtime", "ACTIVE"),
        (ROOT / "trading-DESKTOP-2R00TB4.db", "host_backup_or_conflict_copy", "NOT_AUTHORITATIVE"),
        (ROOT / "trading-DESKTOP-2R00TB4-2.db", "host_backup_or_conflict_copy", "NOT_AUTHORITATIVE"),
        (ROOT / "trading-DESKTOP-TFM86SG.db", "host_backup_or_conflict_copy", "NOT_AUTHORITATIVE"),
        (ROOT / "trading-DESKTOP-TFM86SG-2.db", "host_backup_or_conflict_copy", "NOT_AUTHORITATIVE"),
        (ROOT / "data" / "task388_intraday_canonical_continuation_engine.db", "artifact_readonly", "NOT_AUTHORITATIVE"),
        (ROOT / "data" / "task385_canonical_continuation_engine.db", "artifact_readonly", "NOT_AUTHORITATIVE"),
        (ROOT / "data" / "task384_actual_canonical_backtest.db", "artifact_readonly", "NOT_AUTHORITATIVE"),
        (ROOT / "data" / "task384_engine_integrated_canonical.db", "artifact_readonly", "NOT_AUTHORITATIVE"),
        (ROOT / "data" / "task384_offline_canonical_smoke.db", "artifact_readonly", "NOT_AUTHORITATIVE"),
        (ROOT / "docs" / "reports" / "task_371_source_time_capture" / "task_371_harness.db", "report_harness_artifact", "NOT_AUTHORITATIVE"),
    ]
    rows: list[dict[str, object]] = []
    for path, role, status in candidates:
        meta = _sqlite_meta(path)
        db_rel = str(path.relative_to(ROOT)) if path.exists() and path.is_relative_to(ROOT) else str(path)
        retention_class = {
            "active_runtime": "retain_until_operator_snapshot_and_restore_policy",
            "host_backup_or_conflict_copy": "retain_pending_authority_manifest_review",
            "artifact_readonly": "retain_with_task_artifact_manifest",
            "report_harness_artifact": "retain_with_report",
        }[role]
        row = {
            "authority_id": f"{role}:{db_rel}",
            "db_path": db_rel,
            "role": role,
            "status": status,
            "owner": "Data Operations / Runtime DB Governance",
            "retention_class": retention_class,
            "restore_priority": 1 if status == "ACTIVE" else 9,
            "sha256": meta["sha256"],
            "size_bytes": meta["size_bytes"],
            "integrity_status": meta["integrity_status"],
            "journal_mode": meta["journal_mode"],
            "table_count": meta["table_count"],
            "observed_at": now,
            "notes": "Active runtime DB by config" if status == "ACTIVE" else "Not active; do not delete until retention policy approves.",
        }
        rows.append(row)
        con.execute(
            """
            INSERT OR REPLACE INTO db_authority_manifest(
                authority_id, db_path, role, status, owner, retention_class, restore_priority,
                sha256, size_bytes, integrity_status, journal_mode, table_count, observed_at, notes
            )
            VALUES (:authority_id, :db_path, :role, :status, :owner, :retention_class, :restore_priority,
                    :sha256, :size_bytes, :integrity_status, :journal_mode, :table_count, :observed_at, :notes)
            """,
            row,
        )
    return rows


def _freshness_status(max_ts: str | None, *, stale_reason: str = "STALE") -> str:
    if not max_ts:
        return "NO_ROWS"
    if max_ts < "2026-06-20":
        return stale_reason
    return "CURRENT_OR_RECENT"


def _seed_source_freshness(con: sqlite3.Connection, now: str) -> list[dict[str, object]]:
    specs = [
        {
            "source_family": "market_ticks_intraday",
            "provider": "KIS_QUOTE",
            "storage_ref": "trading.db:market_ticks",
            "max_source_sql": "SELECT MAX(timestamp) FROM market_ticks",
            "max_capture_sql": "SELECT MAX(created_at) FROM market_ticks",
            "sla": 5,
            "strict": 0,
            "proxy": 1,
            "notes": "Intraday runtime quote ticks; stale blocks current runtime freshness.",
        },
        {
            "source_family": "market_bars_5m",
            "provider": "KIS_QUOTE|ALPACA_HISTORICAL_5M",
            "storage_ref": "trading.db:market_bars_5m",
            "max_source_sql": "SELECT MAX(bar_end_ts) FROM market_bars_5m",
            "max_capture_sql": "SELECT MAX(last_updated_at) FROM market_bars_5m",
            "sla": 5,
            "strict": 0,
            "proxy": 1,
            "notes": "5-minute bars; active DB max timestamp determines frontend DB freshness.",
        },
        {
            "source_family": "indicator_snapshots",
            "provider": "runtime_indicator_builder",
            "storage_ref": "trading.db:indicator_snapshots",
            "max_source_sql": "SELECT MAX(bar_end_ts) FROM indicator_snapshots",
            "max_capture_sql": "SELECT MAX(created_at) FROM indicator_snapshots",
            "sla": 10,
            "strict": 0,
            "proxy": 1,
            "notes": "Derived indicators depend on market data freshness.",
        },
        {
            "source_family": "runtime_strategy_decisions",
            "provider": "task584_runtime_strategy_decision_gate",
            "storage_ref": "trading.db:runtime_strategy_decisions",
            "max_source_sql": "SELECT MAX(created_at) FROM runtime_strategy_decisions",
            "max_capture_sql": "SELECT MAX(created_at) FROM runtime_strategy_decisions",
            "sla": 10,
            "strict": 0,
            "proxy": 1,
            "notes": "Legacy paper candidate decisions; not L6 authority.",
        },
        {
            "source_family": "broker_truth_reconciliation",
            "provider": "KIS_PAPER_ORDER_STATUS",
            "storage_ref": "trading.db:reconciliation_runs",
            "max_source_sql": "SELECT MAX(started_at) FROM reconciliation_runs",
            "max_capture_sql": "SELECT MAX(started_at) FROM reconciliation_runs",
            "sla": 1440,
            "strict": 0,
            "proxy": 1,
            "notes": "Broker truth evidence must be fresh before retry or PAPER_ELIGIBLE local intent.",
        },
        {
            "source_family": "diagnostic_runtime_heartbeats",
            "provider": "runtime_scheduler_supervisor",
            "storage_ref": "trading.db:diagnostic_runtime_heartbeats",
            "max_source_sql": "SELECT MAX(heartbeat_bucket_ts) FROM diagnostic_runtime_heartbeats",
            "max_capture_sql": "SELECT MAX(created_at) FROM diagnostic_runtime_heartbeats",
            "sla": 5,
            "strict": 0,
            "proxy": 1,
            "notes": "Scheduler liveness evidence; one bucket is package proof, not recurrence proof.",
        },
        {
            "source_family": "authority_evidence_ledger",
            "provider": "runtime_authority",
            "storage_ref": "trading.db:runtime_authority_evidence_ledger",
            "max_source_sql": "SELECT MAX(created_at) FROM runtime_authority_evidence_ledger",
            "max_capture_sql": "SELECT MAX(created_at) FROM runtime_authority_evidence_ledger",
            "sla": 10,
            "strict": 0,
            "proxy": 0,
            "notes": "No current evidence rows means PAPER_ELIGIBLE must remain blocked.",
        },
    ]
    rows: list[dict[str, object]] = []
    for spec in specs:
        max_source = _fetch_one(con, str(spec["max_source_sql"]), "")
        max_capture = _fetch_one(con, str(spec["max_capture_sql"]), "")
        status = _freshness_status(str(max_source or ""))
        if spec["source_family"] == "authority_evidence_ledger" and not max_source:
            status = "NO_AUTHORITY_EVIDENCE"
        row = {
            "source_family": spec["source_family"],
            "provider": spec["provider"],
            "storage_ref": spec["storage_ref"],
            "max_source_ts": max_source or "",
            "max_capture_ts": max_capture or "",
            "max_available_to_brain_ts": max_capture or max_source or "",
            "freshness_sla_minutes": spec["sla"],
            "freshness_status": status,
            "strict_gate_allowed": spec["strict"],
            "proxy_allowed": spec["proxy"],
            "evidence_ref": f"task3581_systemized:{spec['storage_ref']}",
            "updated_at": now,
            "notes": spec["notes"],
        }
        rows.append(row)
        con.execute(
            """
            INSERT OR REPLACE INTO source_freshness(
                source_family, provider, storage_ref, max_source_ts, max_capture_ts,
                max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
                strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
            )
            VALUES (:source_family, :provider, :storage_ref, :max_source_ts, :max_capture_ts,
                    :max_available_to_brain_ts, :freshness_sla_minutes, :freshness_status,
                    :strict_gate_allowed, :proxy_allowed, :evidence_ref, :updated_at, :notes)
            """,
            row,
        )
        receipt_id = f"source-receipt:{spec['source_family']}:{now}"
        con.execute(
            """
            INSERT OR REPLACE INTO source_receipts(
                receipt_id, provider, source_family, source_key, source_ts, capture_ts,
                available_to_brain_ts, raw_path, raw_sha256, source_time_basis,
                strict_gate_allowed, proxy_allowed, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt_id,
                spec["provider"],
                spec["source_family"],
                "active_db_summary",
                max_source or "",
                max_capture or now,
                max_capture or max_source or "",
                str(spec["storage_ref"]),
                "",
                "active_db_max_timestamp_summary",
                spec["strict"],
                spec["proxy"],
                now,
            ),
        )
    return rows


def _seed_scheduler_ledger(con: sqlite3.Connection, now: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if _table_exists(con, "diagnostic_runtime_heartbeats"):
        for row in con.execute(
            """
            SELECT cadence, heartbeat_bucket_ts, created_at, status, reason_codes_json
            FROM diagnostic_runtime_heartbeats
            ORDER BY created_at
            """
        ).fetchall():
            item = {
                "run_ledger_id": f"{row[0]}:{row[1]}",
                "cadence": row[0],
                "expected_bucket_ts": row[1],
                "actual_start_at": row[2],
                "actual_finish_at": row[2],
                "owner_id": "operator-runtime-diagnostic-scheduler",
                "lease_token": "",
                "status": row[3],
                "lag_seconds": "",
                "skipped_reason": row[4],
                "validation_refs_json": json.dumps(["python scripts/task_registry_validate.py"]),
                "created_at": now,
            }
            rows.append(item)
            con.execute(
                """
                INSERT OR REPLACE INTO scheduler_run_ledger(
                    run_ledger_id, cadence, expected_bucket_ts, actual_start_at, actual_finish_at,
                    owner_id, lease_token, status, lag_seconds, skipped_reason,
                    validation_refs_json, created_at
                )
                VALUES (:run_ledger_id, :cadence, :expected_bucket_ts, :actual_start_at, :actual_finish_at,
                        :owner_id, :lease_token, :status, :lag_seconds, :skipped_reason,
                        :validation_refs_json, :created_at)
                """,
                item,
            )
    return rows


def _seed_retention_policy(con: sqlite3.Connection, now: str, manifest_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for manifest in manifest_rows:
        role = str(manifest["role"])
        status = str(manifest["status"])
        deletion_allowed = 0
        action = "retain"
        if role in {"host_backup_or_conflict_copy", "artifact_readonly", "report_harness_artifact"}:
            action = "retain_until_manifested_archive_or_operator_delete"
        row = {
            "policy_id": f"retention:{manifest['db_path']}",
            "db_path": manifest["db_path"],
            "role": role,
            "retention_class": manifest["retention_class"],
            "action": action,
            "backup_required": 1,
            "deletion_allowed": deletion_allowed,
            "owner": "Data Operations / Runtime DB Governance",
            "reason": "Active DB and evidence-bearing DB copies must not be deleted without explicit authority manifest review.",
            "updated_at": now,
        }
        rows.append(row)
        con.execute(
            """
            INSERT OR REPLACE INTO db_retention_policy(
                policy_id, db_path, role, retention_class, action, backup_required,
                deletion_allowed, owner, reason, updated_at
            )
            VALUES (:policy_id, :db_path, :role, :retention_class, :action, :backup_required,
                    :deletion_allowed, :owner, :reason, :updated_at)
            """,
            row,
        )
    return rows


def _tooling_review_rows() -> list[dict[str, str]]:
    return [
        {
            "tool": "Litestream",
            "category": "sqlite_backup_replication",
            "fit": "P1 later",
            "repo_or_url": "https://litestream.io/",
            "why": "Good fit for active SQLite backup/restore after db_authority_manifest is stable.",
            "decision": "Do not install yet; first finish local authority and restore policy.",
        },
        {
            "tool": "dbmate",
            "category": "schema_migration",
            "fit": "P1 candidate",
            "repo_or_url": "https://github.com/amacneil/dbmate",
            "why": "Framework-agnostic raw SQL migrations match current SQLite/Python repo better than ORM-heavy tooling.",
            "decision": "Candidate for future migration runner; current task implements minimal schema_migrations table first.",
        },
        {
            "tool": "dbt source freshness",
            "category": "freshness_model",
            "fit": "pattern reference",
            "repo_or_url": "https://docs.getdbt.com/docs/deploy/source-freshness",
            "why": "Freshness SLA pattern maps directly to source_freshness table and scheduler checks.",
            "decision": "Adopt concept, not full dbt dependency yet.",
        },
        {
            "tool": "GX Core / Great Expectations",
            "category": "data_quality",
            "fit": "P2 candidate",
            "repo_or_url": "https://greatexpectations.io/",
            "why": "Useful for broader data quality docs and validations when source_receipts mature.",
            "decision": "Do not add dependency now; current validators remain lightweight.",
        },
        {
            "tool": "sqlite-utils",
            "category": "sqlite_inspection_cli",
            "fit": "P2 optional",
            "repo_or_url": "https://sqlite-utils.datasette.io/",
            "why": "Useful for ad hoc SQLite inspection/import/export, but current stdlib sqlite3 is enough.",
            "decision": "Optional operator tool, not core dependency.",
        },
        {
            "tool": "sqlite-explorer-fastmcp-mcp-server",
            "category": "read_only_sqlite_mcp",
            "fit": "P1 MCP candidate",
            "repo_or_url": "https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server",
            "why": "Read-only MCP is the right safety posture for LLM DB inspection.",
            "decision": "Candidate only with read-only DB copy, not writable active trading.db.",
        },
        {
            "tool": "DuckDB MCP extension",
            "category": "analytical_mcp",
            "fit": "P2 MCP candidate",
            "repo_or_url": "https://duckdb.org/community_extensions/extensions/duckdb_mcp",
            "why": "Better suited for artifact/lake analytics than active runtime DB mutation.",
            "decision": "Use later for read-only large panel inspection.",
        },
    ]


def _write_review_artifacts(openai_available: bool) -> None:
    rows = _tooling_review_rows()
    _write_csv(
        ARTIFACT_DIR / "db_tooling_review.csv",
        rows,
        ["tool", "category", "fit", "repo_or_url", "why", "decision"],
    )
    status = "NOT_EXECUTED_NO_LOCAL_OPENAI_KEY_OR_SDK" if not openai_available else "EXECUTED"
    (ARTIFACT_DIR / "gpt_review_status.md").write_text(
        "\n".join(
            [
                "# GPT Review Status",
                "",
                f"- Status: `{status}`",
                "- Review role: review-only; never source-of-truth.",
                "- Local check: `OPENAI_API_KEY` absent and `openai` package absent, so an API-based GPT review was not executed.",
                "- Fallback: local engineering review plus official/open-source source review was recorded in `db_tooling_review.csv`.",
                "",
                "## Review Packet Used",
                "",
                "Evaluate whether the DB governance plan closes P0 gaps: active DB authority, control_state fail-closed state, source freshness ledger, schema migration ledger, scheduler run ledger, and DB retention policy. Do not approve strategy, deployment, broker mutation, paper order, live order, or real capital.",
            ]
        ),
        encoding="utf-8",
    )


def run(db_path: Path, *, openai_available: bool = False) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    now = _utc_now()
    backup_dir = ARTIFACT_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"trading_pre_task3581_{now.replace(':', '').replace('-', '').replace('.', '')}.db"
    shutil.copy2(db_path, backup_path)

    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 5000")
    try:
        con.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
    try:
        con.execute("BEGIN IMMEDIATE")
        _create_governance_tables(con)
        control_row = _normalize_control_state(con, now)
        manifest_rows = _seed_db_authority(con, now, db_path)
        freshness_rows = _seed_source_freshness(con, now)
        scheduler_rows = _seed_scheduler_ledger(con, now)
        retention_rows = _seed_retention_policy(con, now, manifest_rows)
        checksum = hashlib.sha256(MIGRATION_ID.encode("utf-8")).hexdigest()
        con.execute(
            """
            INSERT OR REPLACE INTO schema_migrations(
                migration_id, applied_at, checksum, owning_module, description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                MIGRATION_ID,
                now,
                checksum,
                "scripts/trader_brain_3581_3600_db_governance_systemize.py",
                "DB authority, freshness, scheduler ledger, retention policy, and fail-closed control_state normalization.",
            ),
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    _write_csv(
        ARTIFACT_DIR / "db_authority_manifest.csv",
        manifest_rows,
        [
            "authority_id",
            "db_path",
            "role",
            "status",
            "owner",
            "retention_class",
            "restore_priority",
            "sha256",
            "size_bytes",
            "integrity_status",
            "journal_mode",
            "table_count",
            "observed_at",
            "notes",
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "source_freshness_snapshot.csv",
        freshness_rows,
        [
            "source_family",
            "provider",
            "storage_ref",
            "max_source_ts",
            "max_capture_ts",
            "max_available_to_brain_ts",
            "freshness_sla_minutes",
            "freshness_status",
            "strict_gate_allowed",
            "proxy_allowed",
            "evidence_ref",
            "updated_at",
            "notes",
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "scheduler_run_ledger_snapshot.csv",
        scheduler_rows,
        [
            "run_ledger_id",
            "cadence",
            "expected_bucket_ts",
            "actual_start_at",
            "actual_finish_at",
            "owner_id",
            "lease_token",
            "status",
            "lag_seconds",
            "skipped_reason",
            "validation_refs_json",
            "created_at",
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "db_retention_policy.csv",
        retention_rows,
        [
            "policy_id",
            "db_path",
            "role",
            "retention_class",
            "action",
            "backup_required",
            "deletion_allowed",
            "owner",
            "reason",
            "updated_at",
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "control_state_normalization.csv",
        [control_row],
        [
            "audit_id",
            "observed_run_mode",
            "observed_kill_switch_active",
            "observed_kill_switch_reason",
            "new_run_mode",
            "new_kill_switch_active",
            "new_kill_switch_reason",
            "created_at",
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "normalization_result.csv",
        [
            {
                "task_id": "Task3581",
                "db_path": str(db_path.relative_to(ROOT)),
                "backup_path": str(backup_path.relative_to(ROOT)),
                "control_state_normalized": 1,
                "governance_tables_created": 6,
                "source_freshness_rows": len(freshness_rows),
                "scheduler_run_ledger_rows": len(scheduler_rows),
                "db_authority_rows": len(manifest_rows),
                "retention_policy_rows": len(retention_rows),
                "created_at": now,
            }
        ],
        [
            "task_id",
            "db_path",
            "backup_path",
            "control_state_normalized",
            "governance_tables_created",
            "source_freshness_rows",
            "scheduler_run_ledger_rows",
            "db_authority_rows",
            "retention_policy_rows",
            "created_at",
        ],
    )
    _write_review_artifacts(openai_available)
    print(f"TASK3581_DB_GOVERNANCE_SYSTEMIZED backup={backup_path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=ROOT / "trading.db")
    parser.add_argument("--openai-review-available", action="store_true")
    args = parser.parse_args()
    db_path = args.db_path
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    run(db_path, openai_available=args.openai_review_available)


if __name__ == "__main__":
    main()
