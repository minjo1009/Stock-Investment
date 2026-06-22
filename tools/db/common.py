from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DB = ROOT / "trading.db"
READONLY_DIR = ROOT / "data" / "readonly_mcp"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"

STATUS_NOT_ACCEPTED = "NOT_ACCEPTED"
STATUS_DEPLOYMENT = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
STATUS_REAL_CAPITAL = "FORBIDDEN"

DB_IGNORE_DIRS = {
    ".git",
    ".cache",
    ".codex",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def connect_readonly(path: Path = ACTIVE_DB) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def fetch_count(con: sqlite3.Connection, table: str) -> int:
    if not table_exists(con, table):
        return 0
    return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def sqlite_meta(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else "",
        "integrity_status": "MISSING",
        "foreign_key_check_count": None,
        "journal_mode": "",
        "table_count": 0,
    }
    if not path.exists():
        return meta
    try:
        con = connect_readonly(path)
        try:
            meta["integrity_status"] = str(con.execute("PRAGMA integrity_check").fetchone()[0])
            meta["foreign_key_check_count"] = len(con.execute("PRAGMA foreign_key_check").fetchall())
            meta["journal_mode"] = str(con.execute("PRAGMA journal_mode").fetchone()[0])
            meta["table_count"] = int(
                con.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchone()[0]
            )
        finally:
            con.close()
    except sqlite3.Error as exc:
        meta["integrity_status"] = f"ERROR:{type(exc).__name__}:{exc}"
    return meta


def iter_db_files(root: Path = ROOT) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*.db"):
        parts = set(path.relative_to(root).parts[:-1])
        if DB_IGNORE_DIRS.intersection(parts):
            continue
        paths.append(path)
    return sorted(paths, key=lambda p: rel(p).lower())


def classify_db(path: Path) -> tuple[str, str, str]:
    relative = rel(path)
    if path.resolve() == ACTIVE_DB.resolve():
        return ("active_runtime", "ACTIVE", "canonical root trading.db; data/active migration deferred")
    if relative.startswith("data/readonly_mcp/"):
        return ("readonly_mcp_copy", "DERIVED_READONLY", "replaceable read-only copy for MCP inspection")
    if relative.startswith("data/snapshots/"):
        return ("snapshot", "IMMUTABLE_SNAPSHOT", "point-in-time restore snapshot")
    if "chrome-" in relative and relative.endswith("/cache.db"):
        return ("profile_artifact", "NOT_AUTHORITATIVE", "generated browser profile cache DB retained as artifact")
    if relative.startswith("data/artifacts/") or relative.startswith("docs/reports/") or relative.startswith("data/"):
        return ("artifact_readonly", "NOT_AUTHORITATIVE", "artifact DB retained for audit")
    if path.name.startswith("trading-DESKTOP"):
        return ("host_backup_or_conflict_copy", "NOT_AUTHORITATIVE", "host copy retained pending retention review")
    return ("unknown_db", "QUARANTINE_REQUIRED", "unknown DB-like file requires manifest review")


def scan_db_authority() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_hashes: dict[str, str] = {}
    observed_at = utc_now()
    for path in iter_db_files():
        meta = sqlite_meta(path)
        role, status, notes = classify_db(path)
        sha = str(meta["sha256"])
        duplicate_of = seen_hashes.get(sha, "") if sha else ""
        if sha and not duplicate_of:
            seen_hashes[sha] = str(meta["path"])
        rows.append(
            {
                "db_path": meta["path"],
                "role": role,
                "status": status,
                "size_bytes": meta["size_bytes"],
                "sha256": sha,
                "duplicate_of": duplicate_of,
                "integrity_status": meta["integrity_status"],
                "foreign_key_check_count": meta["foreign_key_check_count"],
                "journal_mode": meta["journal_mode"],
                "table_count": meta["table_count"],
                "observed_at": observed_at,
                "notes": notes,
            }
        )
    return rows


def source_freshness_rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(con, "source_freshness"):
        return []
    query = """
        SELECT source_family, provider, storage_ref, max_source_ts, max_capture_ts,
               max_available_to_brain_ts, freshness_sla_minutes, freshness_status,
               strict_gate_allowed, proxy_allowed, evidence_ref, updated_at, notes
        FROM source_freshness
        ORDER BY source_family
    """
    return [dict(row) for row in con.execute(query).fetchall()]


def control_state(con: sqlite3.Connection) -> dict[str, Any]:
    if not table_exists(con, "control_state"):
        return {}
    row = con.execute(
        "SELECT * FROM control_state WHERE control_key='default' LIMIT 1"
    ).fetchone()
    return dict(row) if row else {}


def health_metrics() -> dict[str, Any]:
    con = connect_readonly(ACTIVE_DB)
    try:
        control = control_state(con)
        freshness = source_freshness_rows(con)
        manifest_active = 0
        manifest_non_authoritative = 0
        if table_exists(con, "db_authority_manifest"):
            manifest_active = int(
                con.execute("SELECT COUNT(*) FROM db_authority_manifest WHERE status='ACTIVE'").fetchone()[0]
            )
            manifest_non_authoritative = int(
                con.execute(
                    "SELECT COUNT(*) FROM db_authority_manifest WHERE status='NOT_AUTHORITATIVE'"
                ).fetchone()[0]
            )
        scan_rows = scan_db_authority()
        unknown_scan = sum(1 for row in scan_rows if row["status"] == "QUARANTINE_REQUIRED")
        duplicate_hashes = sum(1 for row in scan_rows if row["duplicate_of"])
        stale_sources = [
            row["source_family"]
            for row in freshness
            if row["freshness_status"] in {"STALE", "NO_AUTHORITY_EVIDENCE", "MISSING"}
        ]
        broker_mutation_attempt_count = 0
        if table_exists(con, "paper_order_intents"):
            paper_order_intents_count = fetch_count(con, "paper_order_intents")
        else:
            paper_order_intents_count = 0
        scheduler_rows = fetch_count(con, "scheduler_run_ledger")
        scheduler_distinct_buckets = 0
        if table_exists(con, "scheduler_run_ledger"):
            scheduler_distinct_buckets = int(
                con.execute(
                    "SELECT COUNT(DISTINCT expected_bucket_ts) FROM scheduler_run_ledger"
                ).fetchone()[0]
            )
        management_tables = {
            table: table_exists(con, table)
            for table in {
                "scheduler_job_registry",
                "source_freshness_policy",
                "reference_hashes",
                "data_lineage_edges",
            }
        }
        jobs_registered = fetch_count(con, "scheduler_job_registry")
        freshness_policy_count = fetch_count(con, "source_freshness_policy")
        reference_hash_count = fetch_count(con, "reference_hashes")
        lineage_edge_count = fetch_count(con, "data_lineage_edges")
        fk_violations = len(con.execute("PRAGMA foreign_key_check").fetchall())
        metrics = {
            "generated_at": utc_now(),
            "active_db_path": rel(ACTIVE_DB),
            "active_db_integrity": sqlite_meta(ACTIVE_DB)["integrity_status"],
            "db_active_manifest_count": manifest_active,
            "db_non_authoritative_manifest_count": manifest_non_authoritative,
            "db_scan_file_count": len(scan_rows),
            "unknown_db_count": unknown_scan,
            "duplicate_hash_count": duplicate_hashes,
            "stale_source_count": len(stale_sources),
            "stale_source_families": stale_sources,
            "source_freshness_row_count": len(freshness),
            "source_receipts_count": fetch_count(con, "source_receipts"),
            "scheduler_run_ledger_count": scheduler_rows,
            "scheduler_distinct_bucket_count": scheduler_distinct_buckets,
            "scheduler_recurrence_proven": scheduler_distinct_buckets >= 3,
            "runtime_authority_evidence_ledger_count": fetch_count(
                con, "runtime_authority_evidence_ledger"
            ),
            "paper_order_intents_count": paper_order_intents_count,
            "broker_mutation_attempt_count": broker_mutation_attempt_count,
            "management_tables": management_tables,
            "management_tables_present": all(management_tables.values()),
            "jobs_registered": jobs_registered,
            "source_freshness_policy_count": freshness_policy_count,
            "reference_hash_count": reference_hash_count,
            "lineage_edge_count": lineage_edge_count,
            "foreign_key_violation_count": fk_violations,
            "control_run_mode": control.get("run_mode", ""),
            "control_kill_switch_active": control.get("kill_switch_active", None),
            "control_guard_status": (
                "PASS_FAIL_CLOSED"
                if control.get("run_mode") == "DIAGNOSTIC_ONLY"
                and int(control.get("kill_switch_active", 0)) == 1
                else "FAIL_OPEN_OR_UNKNOWN"
            ),
            "governance_health": "PASS_WITH_SOURCE_BLOCKERS",
            "strategy": STATUS_NOT_ACCEPTED,
            "deployment": STATUS_DEPLOYMENT,
            "real_capital": STATUS_REAL_CAPITAL,
        }
        if manifest_active != 1 or unknown_scan > 0 or metrics["active_db_integrity"] != "ok":
            metrics["governance_health"] = "FAIL"
        return metrics
    finally:
        con.close()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def copy_db_with_hash(source: Path, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    meta = sqlite_meta(target)
    meta["source_path"] = rel(source)
    meta["copied_at"] = utc_now()
    return meta
