from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "trading.db"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3721_3760_source_acquisition_runtime_loop"
REGISTERED_LOOP = ARTIFACT_DIR / "registered_loop_all_adapters_after_sec.json"
PROVIDER_RUN = ARTIFACT_DIR / "source_acquisition_provider_run.json"
SEC_RUN = ARTIFACT_DIR / "sec_events_cached_fixture_run.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_raw_complete(run: dict) -> None:
    for result in run.get("results", []):
        if result.get("status") != "SUCCESS":
            continue
        raw_path_text = str(result.get("raw_path") or "")
        if not raw_path_text:
            raise AssertionError("successful result missing raw_path")
        metadata_path = ROOT / raw_path_text
        metadata = _load_json(metadata_path)
        if int(metadata.get("truncated_raw_rows", -1)) != 0:
            raise AssertionError(f"raw metadata is truncated: {metadata_path}")
        full_raw_path = ROOT / str(metadata.get("full_raw_path") or "")
        if not full_raw_path.exists():
            raise AssertionError(f"full_raw_path missing: {full_raw_path}")
        if _sha256(full_raw_path) != metadata.get("full_raw_sha256"):
            raise AssertionError(f"full_raw_sha256 mismatch: {full_raw_path}")
        if int(metadata.get("full_raw_row_count", -1)) < int(result.get("row_count", -2)):
            raise AssertionError("full raw row count is smaller than normalized result row_count")


def _count(con: sqlite3.Connection, table: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _duplicate_count(con: sqlite3.Connection, table: str, columns: str) -> int:
    total = _count(con, table)
    distinct = int(con.execute(f"SELECT COUNT(*) FROM (SELECT {columns} FROM {table} GROUP BY {columns})").fetchone()[0])
    return total - distinct


def main() -> None:
    provider = _load_json(PROVIDER_RUN)
    sec = _load_json(SEC_RUN)
    registered = _load_json(REGISTERED_LOOP)
    if provider.get("status") != "APPLIED_DIAGNOSTIC_ONLY" or int(provider.get("success_count", 0)) < 4:
        raise AssertionError("provider acquisition run did not succeed for market/daily/macro families")
    if sec.get("status") != "APPLIED_DIAGNOSTIC_ONLY" or int(sec.get("success_count", 0)) != 1:
        raise AssertionError("cached SEC fixture acquisition did not succeed")
    _assert_raw_complete(provider)
    _assert_raw_complete(sec)
    if registered.get("status") != "APPLIED_DIAGNOSTIC_ONLY":
        raise AssertionError("registered loop did not apply")
    if int(registered.get("jobs_seen", 0)) != 12:
        raise AssertionError("registered loop must see 12 jobs")
    if int(registered.get("success_count", 0)) != 12 or int(registered.get("skipped_count", -1)) != 0:
        raise AssertionError("all registered jobs must have adapter evidence after cached SEC attachment")

    con = sqlite3.connect(DB)
    try:
        control = con.execute(
            "SELECT run_mode, kill_switch_active FROM control_state WHERE control_key='default'"
        ).fetchone()
        if control != ("DIAGNOSTIC_ONLY", 1):
            raise AssertionError(f"control_state must stay fail-closed, got {control}")

        bad_permissions = con.execute(
            """
            SELECT COUNT(*)
            FROM scheduler_job_registry
            WHERE execution_permitted != 0
               OR broker_mutation_permitted != 0
               OR real_capital_permitted != 0
               OR paper_promotion_permitted != 0
            """
        ).fetchone()[0]
        if int(bad_permissions) != 0:
            raise AssertionError("scheduler permission columns must remain 0")

        required_counts = {
            "market_bars_5m": 30_000,
            "market_ticks": 5_800,
            "daily_ohlcv": 1,
            "macro_rates": 1,
            "sec_events": 1,
            "runtime_authority_evidence_ledger": 1,
            "source_receipts": 1,
            "reference_hashes": 1,
            "data_lineage_edges": 1,
        }
        for table, minimum in required_counts.items():
            observed = _count(con, table)
            if observed < minimum:
                raise AssertionError(f"{table} row count too small: {observed} < {minimum}")

        duplicate_specs = {
            "daily_ohlcv": "provider, symbol, session_date",
            "macro_rates": "provider, series_id, observation_date, vintage_ts",
            "sec_events": "provider, accession_no, form_type, event_type",
        }
        for table, columns in duplicate_specs.items():
            duplicates = _duplicate_count(con, table, columns)
            if duplicates != 0:
                raise AssertionError(f"{table} duplicate key rows: {duplicates}")

        families = {
            row[0]: row
            for row in con.execute(
                """
                SELECT source_family, freshness_status, strict_gate_allowed, proxy_allowed, evidence_ref
                FROM source_freshness
                """
            ).fetchall()
        }
        required_families = {
            "authority_evidence_ledger",
            "broker_truth_reconciliation",
            "catalog_report_artifacts",
            "daily_ohlcv",
            "diagnostic_runtime_heartbeats",
            "frontend_read_models",
            "indicator_snapshots",
            "macro_rates",
            "market_bars_5m",
            "market_ticks_intraday",
            "runtime_strategy_decisions",
            "sec_events",
        }
        missing = sorted(required_families.difference(families))
        if missing:
            raise AssertionError(f"missing freshness families: {missing}")
        for family in required_families:
            row = families[family]
            if int(row[2]) != 0 or int(row[3]) != 0:
                raise AssertionError(f"{family} gates must remain closed")
            if not str(row[4] or ""):
                raise AssertionError(f"{family} evidence_ref missing")

        provider_rows = [
            row[0]
            for row in con.execute(
                """
                SELECT provider
                FROM source_receipts
                WHERE created_at >= '2026-06-21T02:00:00Z'
                """
            ).fetchall()
        ]
        forbidden_provider_tokens = ("ORDER", "SUBMIT", "BROKER_MUTATION", "LIVE_ORDER")
        for provider_name in provider_rows:
            if any(token in str(provider_name).upper() for token in forbidden_provider_tokens):
                raise AssertionError(f"forbidden order-like provider in source receipts: {provider_name}")

        states = con.execute(
            """
            SELECT payload_json
            FROM runtime_authority_evidence_ledger
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
        payload = json.loads(states[0])
        if payload.get("gate") != "BLOCKED":
            raise AssertionError("latest authority evidence must remain BLOCKED")
        if payload.get("paper_order_intent_allowed") is not False or payload.get("live_order_allowed") is not False:
            raise AssertionError("authority evidence must not open paper/live order permissions")
    finally:
        con.close()

    print(
        "[TASK3721_3760_OK] provider_acquisition=PASS registered_jobs=12 "
        "duplicates=0 gates_closed=1 authority_blocked=1"
    )


if __name__ == "__main__":
    main()
