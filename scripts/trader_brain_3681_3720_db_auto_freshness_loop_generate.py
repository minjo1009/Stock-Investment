from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.db.common import ACTIVE_DB, connect_readonly, sha256_file, write_csv, write_json
from tools.db.loop_contract_report import build_report


TASK = "task_3681_3720_db_auto_freshness_loop"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK


def _query(sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    con = connect_readonly(ACTIVE_DB)
    try:
        return [dict(row) for row in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def _run_result() -> dict[str, object]:
    path = ARTIFACT_DIR / "registered_loop_run_result_after_contract_expansion.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    path = ARTIFACT_DIR / "registered_loop_run_result.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_csv_fixed(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_task_loop_plan() -> None:
    rows = [
        {"loop": 1, "status": "DONE", "scope": "inventory active DB tables and source freshness blockers", "result": "found cached tables for market ticks, bars, broker reconciliation, indicators, runtime decisions"},
        {"loop": 2, "status": "DONE", "scope": "extend runner adapters", "result": "added cached table snapshot helper and adapters"},
        {"loop": 3, "status": "DONE", "scope": "broker truth cached adapter", "result": "reconciliation_runs evidence writes receipt/hash/lineage/freshness without broker API"},
        {"loop": 4, "status": "DONE", "scope": "market ticks cached adapter", "result": "market_ticks evidence writes receipt/hash/lineage/freshness without live fetch"},
        {"loop": 5, "status": "DONE", "scope": "runtime and indicator contract gap", "result": "registered runtime_strategy_decisions and indicator_snapshots jobs and adapters"},
        {"loop": 6, "status": "DONE", "scope": "authority evidence empty ledger handling", "result": "authority evidence remains neutral SKIPPED when table has 0 rows"},
        {"loop": 7, "status": "DONE", "scope": "active DB apply", "result": "12 jobs seen, 6 success, 6 skipped, diagnostic-only"},
        {"loop": 8, "status": "DONE", "scope": "health and recurrence", "result": "DB healthcheck PASS and scheduler recurrence proven by 5 distinct buckets"},
        {"loop": 9, "status": "DONE", "scope": "governance artifacts", "result": "task report, artifacts, registry, wiki, Obsidian prepared"},
        {"loop": 10, "status": "DONE_WITH_BLOCKERS", "scope": "completion audit", "result": "DB loop management improved; live source acquisition loops still required for freshness recovery"},
    ]
    _write_csv_fixed(ARTIFACT_DIR / "db_auto_freshness_10_loop_plan.csv", rows, ["loop", "status", "scope", "result"])


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    run_result = _run_result()
    bucket = str(run_result.get("bucket_ts", ""))
    write_json(ARTIFACT_DIR / "loop_contract_report_after_contract_expansion.json", build_report())
    write_csv(ARTIFACT_DIR / "scheduler_job_registry.csv", _query("SELECT * FROM scheduler_job_registry ORDER BY job_name"))
    write_csv(ARTIFACT_DIR / "source_freshness_policy.csv", _query("SELECT * FROM source_freshness_policy ORDER BY source_family"))
    write_csv(ARTIFACT_DIR / "source_freshness_snapshot.csv", _query("SELECT * FROM source_freshness ORDER BY source_family"))
    write_csv(
        ARTIFACT_DIR / "scheduler_run_ledger_latest_bucket.csv",
        _query("SELECT * FROM scheduler_run_ledger WHERE expected_bucket_ts=? ORDER BY cadence", (bucket,)),
    )
    families = (
        "broker_truth_reconciliation",
        "indicator_snapshots",
        "market_bars_5m",
        "market_ticks_intraday",
        "runtime_strategy_decisions",
        "diagnostic_runtime_heartbeats",
    )
    placeholders = ",".join("?" for _ in families)
    write_csv(
        ARTIFACT_DIR / "source_receipts_loop_families.csv",
        _query(f"SELECT * FROM source_receipts WHERE source_family IN ({placeholders}) ORDER BY source_family, created_at DESC", families),
    )
    write_csv(
        ARTIFACT_DIR / "reference_hashes_loop_families.csv",
        _query(f"SELECT * FROM reference_hashes WHERE source_family IN ({placeholders}) ORDER BY source_family, created_at DESC", families),
    )
    write_csv(
        ARTIFACT_DIR / "data_lineage_edges_loop_families.csv",
        _query(f"SELECT * FROM data_lineage_edges WHERE source_family IN ({placeholders}) ORDER BY source_family, created_at DESC", families),
    )
    _write_task_loop_plan()
    write_csv(
        ARTIFACT_DIR / "artifact_manifest.csv",
        [
            {
                "artifact": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "notes": "Task3681-3720 DB auto freshness loop artifact",
            }
            for path in sorted(ARTIFACT_DIR.glob("*"))
            if path.is_file() and path.name != "artifact_manifest.csv"
        ],
    )
    print("TASK3681_3720_DB_AUTO_FRESHNESS_LOOP_GENERATED")


if __name__ == "__main__":
    main()
