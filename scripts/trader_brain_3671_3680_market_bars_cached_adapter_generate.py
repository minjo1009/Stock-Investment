from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.db.common import ACTIVE_DB, connect_readonly, health_metrics, rel, sha256_file, write_csv, write_json
from tools.db.loop_contract_report import build_report


TASK = "task_3671_3680_market_bars_cached_adapter"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK


def _query(sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    con = connect_readonly(ACTIVE_DB)
    try:
        return [dict(row) for row in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def _latest_raw_market_metadata() -> dict[str, object]:
    rows = _query(
        """
        SELECT raw_path, raw_sha256, source_ts, capture_ts
        FROM source_receipts
        WHERE source_family='market_bars_5m'
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    if not rows:
        return {}
    row = rows[0]
    path = ROOT / str(row["raw_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    if sha256_file(path) != row["raw_sha256"]:
        raise RuntimeError("MARKET_BARS_RAW_HASH_MISMATCH")
    payload["raw_path"] = rel(path)
    payload["raw_sha256"] = row["raw_sha256"]
    payload["receipt_source_ts"] = row["source_ts"]
    payload["receipt_capture_ts"] = row["capture_ts"]
    return payload


def _market_table_stats() -> dict[str, object]:
    con = sqlite3.connect(f"file:{ACTIVE_DB.as_posix()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
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
    finally:
        con.close()


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    run_result_path = ARTIFACT_DIR / "registered_loop_run_result.json"
    if not run_result_path.exists():
        raise RuntimeError(f"missing {rel(run_result_path)}")
    run_result = json.loads(run_result_path.read_text(encoding="utf-8"))
    bucket = str(run_result["bucket_ts"])

    write_json(ARTIFACT_DIR / "loop_contract_report.json", build_report())
    health_path = ARTIFACT_DIR / "db_health_metrics.json"
    if not health_path.exists():
        write_json(health_path, health_metrics())
    write_json(ARTIFACT_DIR / "market_bars_cached_snapshot.json", _latest_raw_market_metadata())
    write_json(ARTIFACT_DIR / "market_bars_table_stats.json", _market_table_stats())
    write_csv(
        ARTIFACT_DIR / "source_receipts_market_bars_5m.csv",
        _query("SELECT * FROM source_receipts WHERE source_family='market_bars_5m' ORDER BY created_at DESC"),
    )
    write_csv(
        ARTIFACT_DIR / "reference_hashes_market_bars_5m.csv",
        _query("SELECT * FROM reference_hashes WHERE source_family='market_bars_5m' ORDER BY created_at DESC"),
    )
    write_csv(
        ARTIFACT_DIR / "data_lineage_edges_market_bars_5m.csv",
        _query("SELECT * FROM data_lineage_edges WHERE source_family='market_bars_5m' ORDER BY created_at DESC"),
    )
    write_csv(
        ARTIFACT_DIR / "source_freshness_market_bars_5m.csv",
        _query("SELECT * FROM source_freshness WHERE source_family='market_bars_5m'"),
    )
    write_csv(
        ARTIFACT_DIR / "scheduler_run_ledger_market_bars_5m.csv",
        _query(
            """
            SELECT * FROM scheduler_run_ledger
            WHERE cadence='market_bars_5m_refresh' AND expected_bucket_ts=?
            ORDER BY created_at DESC
            """,
            (bucket,),
        ),
    )
    write_csv(
        ARTIFACT_DIR / "artifact_manifest.csv",
        [
            {
                "artifact": rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "notes": "Task3671-3680 cached market_bars_5m adapter closeout artifact",
            }
            for path in sorted(ARTIFACT_DIR.glob("*"))
            if path.is_file() and path.name != "artifact_manifest.csv"
        ],
    )
    print("TASK3671_3680_MARKET_BARS_CACHED_ADAPTER_GENERATED")


if __name__ == "__main__":
    main()
