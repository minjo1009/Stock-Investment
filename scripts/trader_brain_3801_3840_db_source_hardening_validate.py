from __future__ import annotations

import csv
import json
import os
import sqlite3
import tempfile
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.db.apply_management_schema import _create_schema, _seed
from tools.db.common import ACTIVE_DB, ROOT, rel
from tools.db.run_registered_loop_once import run_once as run_registered_loop_once


TASK_ID = "task_3801_3840_db_source_hardening"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
CONFIG = ROOT / "configs" / "db_source_acquisition_scheduler.json"
RUNNER = ROOT / "scripts" / "run_db_source_acquisition_scheduler.ps1"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _count(con: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    return int(con.execute(sql, params).fetchone()[0])


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone() is not None


def _make_temp_loop_db() -> Path:
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "fresh_gate.db"
    # Keep the temp directory alive by registering the path under ARTIFACT_DIR through a copy-like location.
    stable_dir = ARTIFACT_DIR / "temp_fresh_gate"
    stable_dir.mkdir(parents=True, exist_ok=True)
    path = stable_dir / "fresh_gate.db"
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE control_state(
                control_key TEXT PRIMARY KEY,
                run_mode TEXT NOT NULL,
                kill_switch_active INTEGER NOT NULL
            );
            INSERT INTO control_state VALUES('default', 'DIAGNOSTIC_ONLY', 1);

            CREATE TABLE db_authority_manifest(
                authority_id TEXT PRIMARY KEY,
                db_path TEXT NOT NULL,
                status TEXT NOT NULL
            );
            INSERT INTO db_authority_manifest VALUES('active', 'trading.db', 'ACTIVE');

            CREATE TABLE schema_migrations(
                migration_id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL,
                owning_module TEXT NOT NULL,
                description TEXT NOT NULL
            );
            CREATE TABLE source_receipts(
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
            CREATE TABLE source_freshness(
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
            CREATE TABLE scheduler_run_ledger(
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
            """
        )
        _create_schema(con)
        _seed(con, "2026-06-21T00:00:00Z")
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        con.executescript(
            f"""
            CREATE TABLE market_bars_5m(
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
            INSERT INTO market_bars_5m VALUES
            ('AAPL:{now}','AAPL','{now}','{now}',10,11,9,10.5,1000,12,'fresh-fixture','{now}');
            """
        )
        con.commit()
    finally:
        con.close()
    return path


def _fresh_market_gate_probe() -> dict[str, object]:
    db_path = _make_temp_loop_db()
    result = run_registered_loop_once(
        db_path=db_path,
        apply=True,
        only_job="market_bars_5m_refresh",
        bucket="2026-06-21T00:00:00Z",
        raw_dir=ARTIFACT_DIR / "fresh_gate_raw",
        market_bars_raw_dir=ARTIFACT_DIR / "fresh_gate_market_raw",
    )
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT freshness_status, strict_gate_allowed, proxy_allowed
            FROM source_freshness
            WHERE source_family='market_bars_5m'
            """
        ).fetchone()
    finally:
        con.close()
    if row != ("CURRENT_OR_RECENT", 0, 0):
        raise AssertionError(f"fresh market gate probe failed: {row}")
    return {
        "probe_db": rel(db_path),
        "status": result["status"],
        "market_bars_freshness": row[0],
        "strict_gate_allowed": row[1],
        "proxy_allowed": row[2],
    }


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    runner_text = RUNNER.read_text(encoding="utf-8")
    if "sec_user_agent_env_file" not in config:
        raise AssertionError("scheduler config must include sec_user_agent_env_file")
    if config.get("sec_user_agent_env_name") != "SEC_USER_AGENT":
        raise AssertionError("scheduler config must name SEC_USER_AGENT")
    for token in ("sec_user_agent_env_file", "SetEnvironmentVariable", "example.com", "TODO"):
        if token not in runner_text:
            raise AssertionError(f"scheduler runner missing SEC user-agent loader token: {token}")

    sec_user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    sec_audit = {
        "env_name": "SEC_USER_AGENT",
        "configured": int(bool(sec_user_agent)),
        "status": "CONFIGURED" if sec_user_agent else "BLOCKED_OPERATOR_VALUE_REQUIRED",
    }

    con = sqlite3.connect(ACTIVE_DB)
    con.row_factory = sqlite3.Row
    try:
        for table in ("source_scheduler_leases", "source_acquisition_input_fingerprints"):
            if not _table_exists(con, table):
                raise AssertionError(f"missing hardening table: {table}")
        duplicate_ledger = _count(
            con,
            "SELECT COUNT(*) FROM scheduler_run_ledger WHERE skipped_reason='DUPLICATE_INPUT_HASH'",
        )
        fingerprints = _count(con, "SELECT COUNT(*) FROM source_acquisition_input_fingerprints")
        released_leases = _count(con, "SELECT COUNT(*) FROM source_scheduler_leases WHERE status='RELEASED'")
        if duplicate_ledger <= 0:
            raise AssertionError("DUPLICATE_INPUT_HASH ledger evidence missing")
        if fingerprints <= 0 or released_leases <= 0:
            raise AssertionError("source scheduler lease/fingerprint evidence missing")

        broker = con.execute(
            """
            SELECT provider, freshness_status, strict_gate_allowed, proxy_allowed, evidence_ref
            FROM source_freshness
            WHERE source_family='broker_truth_reconciliation'
            """
        ).fetchone()
        if broker is None:
            raise AssertionError("broker truth freshness row missing")
        if int(broker["strict_gate_allowed"]) != 0 or int(broker["proxy_allowed"]) != 0:
            raise AssertionError("broker truth gates must remain closed")
        broker_payload_row = con.execute(
            """
            SELECT raw_snapshot_json
            FROM reconciliation_runs
            WHERE reconciliation_id LIKE 'fixture-broker-truth:%'
            ORDER BY finished_at DESC
            LIMIT 1
            """
        ).fetchone()
        if broker_payload_row is None:
            raise AssertionError("operator broker truth fixture reconciliation row missing")
        broker_payload = json.loads(broker_payload_row["raw_snapshot_json"])
        if broker_payload.get("broker_api_called") is not False or broker_payload.get("broker_mutation") is not False:
            raise AssertionError("broker truth fixture must not call or mutate broker state")

        gate_open_candidates = _count(
            con,
            """
            SELECT COUNT(*)
            FROM source_freshness
            WHERE freshness_status='CURRENT_OR_RECENT'
              AND (strict_gate_allowed=1 OR proxy_allowed=1)
            """,
        )
        if gate_open_candidates:
            raise AssertionError("active DB must not have opened source gates")
    finally:
        con.close()

    fresh_probe = _fresh_market_gate_probe()
    rows = [
        {"check": "sec_user_agent", **sec_audit},
        {"check": "duplicate_input_hash_ledger", "count": duplicate_ledger, "status": "PASS"},
        {"check": "input_fingerprints", "count": fingerprints, "status": "PASS"},
        {"check": "released_leases", "count": released_leases, "status": "PASS"},
        {"check": "broker_truth_fixture", "provider": broker["provider"], "status": "PASS"},
        {"check": "active_gate_open_candidates", "count": gate_open_candidates, "status": "PASS"},
        {"check": "fresh_market_gate_probe", **fresh_probe},
    ]
    _write_csv(ARTIFACT_DIR / "task_3801_3840_validation_audit.csv", rows)
    (ARTIFACT_DIR / "task_3801_3840_validation_audit.json").write_text(
        json.dumps(
            {
                "task_id": TASK_ID,
                "sec_user_agent": sec_audit,
                "duplicate_input_hash_ledger": duplicate_ledger,
                "input_fingerprints": fingerprints,
                "released_leases": released_leases,
                "broker_truth_provider": broker["provider"],
                "active_gate_open_candidates": gate_open_candidates,
                "fresh_market_gate_probe": fresh_probe,
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "[TASK3801_3840_OK] source_hardening=PASS duplicate_input_hash=PASS "
        "broker_truth_fixture=PASS fresh_market_gate_probe=PASS gates_closed=1"
    )


if __name__ == "__main__":
    main()
