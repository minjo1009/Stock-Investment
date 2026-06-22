from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3581_3600_db_governance_systemization"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing required csv: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require(path: Path, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing {missing}")


def _db_checks() -> None:
    con = sqlite3.connect(f"file:{(ROOT / 'trading.db').as_posix()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        control = con.execute(
            "SELECT run_mode, kill_switch_active, kill_switch_reason FROM control_state WHERE control_key='default'"
        ).fetchone()
        if control is None:
            raise AssertionError("control_state default row missing")
        if control["run_mode"] != "DIAGNOSTIC_ONLY":
            raise AssertionError(f"control_state run_mode not normalized: {control['run_mode']}")
        if int(control["kill_switch_active"]) != 1:
            raise AssertionError("kill_switch_active must be 1")
        if "REAL_CAPITAL_FORBIDDEN" not in str(control["kill_switch_reason"]):
            raise AssertionError("kill switch reason missing real-capital boundary")
        required_tables = {
            "schema_migrations",
            "db_authority_manifest",
            "source_freshness",
            "source_receipts",
            "scheduler_run_ledger",
            "db_retention_policy",
            "db_control_state_audit",
        }
        actual = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        missing = required_tables.difference(actual)
        if missing:
            raise AssertionError(f"missing governance tables: {sorted(missing)}")
        migration = con.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_id='task3581_db_governance_controls_v1'"
        ).fetchone()[0]
        if int(migration) != 1:
            raise AssertionError("schema migration row missing")
        active = con.execute(
            "SELECT COUNT(*) FROM db_authority_manifest WHERE db_path='trading.db' AND status='ACTIVE'"
        ).fetchone()[0]
        if int(active) != 1:
            raise AssertionError("active DB authority row missing")
        non_authority = con.execute(
            "SELECT COUNT(*) FROM db_authority_manifest WHERE status='NOT_AUTHORITATIVE'"
        ).fetchone()[0]
        if int(non_authority) < 4:
            raise AssertionError("root/artifact DB non-authoritative rows missing")
        stale = con.execute(
            "SELECT COUNT(*) FROM source_freshness WHERE freshness_status IN ('STALE','NO_AUTHORITY_EVIDENCE')"
        ).fetchone()[0]
        if int(stale) < 4:
            raise AssertionError("source freshness blockers missing")
        retention = con.execute("SELECT COUNT(*) FROM db_retention_policy WHERE deletion_allowed=0").fetchone()[0]
        if int(retention) < 11:
            raise AssertionError("retention policy rows must block deletion")
    finally:
        con.close()


def main() -> None:
    _db_checks()
    expected_counts = {
        "db_authority_manifest.csv": 11,
        "source_freshness_snapshot.csv": 7,
        "scheduler_run_ledger_snapshot.csv": 2,
        "db_retention_policy.csv": 11,
        "control_state_normalization.csv": 1,
        "db_tooling_review.csv": 7,
        "normalization_result.csv": 1,
    }
    for filename, expected in expected_counts.items():
        rows = _rows(ARTIFACT_DIR / filename)
        if len(rows) != expected:
            raise AssertionError(f"{filename} row count mismatch: {len(rows)} != {expected}")
    tooling = {row["tool"] for row in _rows(ARTIFACT_DIR / "db_tooling_review.csv")}
    for required in {"Litestream", "dbmate", "dbt source freshness", "GX Core / Great Expectations", "sqlite-utils", "sqlite-explorer-fastmcp-mcp-server", "DuckDB MCP extension"}:
        if required not in tooling:
            raise AssertionError(f"missing tooling review row: {required}")
    _require(
        ARTIFACT_DIR / "gpt_review_status.md",
        ("NOT_EXECUTED_NO_LOCAL_OPENAI_KEY_OR_SDK", "review-only", "OPENAI_API_KEY"),
    )
    _require(
        REPORT_DIR / "task_3581_3600_db_governance_systemization.md",
        (
            "DB_GOVERNANCE_SYSTEMIZED_FAIL_CLOSED",
            "DIAGNOSTIC_ONLY",
            "kill_switch_active=1",
            "source_freshness",
            "db_authority_manifest",
            "NOT_EXECUTED_NO_LOCAL_OPENAI_KEY_OR_SDK",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        REPORT_DIR / "task_3600_decision.csv",
        (
            "Task3600",
            "DB_GOVERNANCE_SYSTEMIZED_FAIL_CLOSED",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        (
            "Task3581,DB Governance Systemization Selection",
            "Task3600,DB Governance Systemization Closeout",
            "task_3581_3600_db_governance_systemization",
        ),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3581-Task3600", "DB_GOVERNANCE_SYSTEMIZED_FAIL_CLOSED", "control_state"),
    )
    print("TASK3581_3600_DB_GOVERNANCE_SYSTEMIZED_OK")


if __name__ == "__main__":
    main()
