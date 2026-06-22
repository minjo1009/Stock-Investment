from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3651_3670_db_registered_loop_runner"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(_read(path))
    if not isinstance(payload, dict):
        raise AssertionError(f"json must be object: {path.relative_to(ROOT)}")
    return payload


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require(path: Path, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing {missing}")


def _run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def _db_checks(run_result: dict[str, object]) -> None:
    bucket = run_result["bucket_ts"]
    con = sqlite3.connect(f"file:{(ROOT / 'trading.db').as_posix()}?mode=ro", uri=True, timeout=10)
    try:
        receipt_count = con.execute(
            "SELECT COUNT(*) FROM source_receipts WHERE source_family='diagnostic_runtime_heartbeats'"
        ).fetchone()[0]
        ref_count = con.execute(
            "SELECT COUNT(*) FROM reference_hashes WHERE source_family='diagnostic_runtime_heartbeats'"
        ).fetchone()[0]
        edge_count = con.execute(
            "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family='diagnostic_runtime_heartbeats'"
        ).fetchone()[0]
        if receipt_count < 1 or ref_count < 1 or edge_count < 1:
            raise AssertionError("heartbeat receipt/hash/lineage evidence missing")
        success = con.execute(
            """
            SELECT COUNT(*) FROM scheduler_run_ledger
            WHERE expected_bucket_ts=? AND status='SUCCESS'
              AND cadence='diagnostic_runtime_heartbeats_refresh'
            """,
            (bucket,),
        ).fetchone()[0]
        skipped = con.execute(
            """
            SELECT COUNT(*) FROM scheduler_run_ledger
            WHERE expected_bucket_ts=? AND status='SKIPPED'
              AND skipped_reason='NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY'
            """,
            (bucket,),
        ).fetchone()[0]
        if success != 1 or skipped != 9:
            raise AssertionError(f"runner ledger status mismatch: success={success} skipped={skipped}")
        fresh = con.execute(
            """
            SELECT freshness_status, strict_gate_allowed, proxy_allowed
            FROM source_freshness
            WHERE source_family='diagnostic_runtime_heartbeats'
            """
        ).fetchone()
        if not fresh or fresh[0] != "CURRENT_OR_RECENT" or int(fresh[1]) != 0 or int(fresh[2]) != 0:
            raise AssertionError("heartbeat freshness row invalid")
        unsafe = con.execute(
            """
            SELECT COUNT(*) FROM scheduler_job_registry
            WHERE execution_permitted != 0
               OR broker_mutation_permitted != 0
               OR paper_promotion_permitted != 0
               OR real_capital_permitted != 0
            """
        ).fetchone()[0]
        if unsafe:
            raise AssertionError("unsafe permission column found")
    finally:
        con.close()


def main() -> None:
    _run([sys.executable, "-m", "unittest", "tests.test_db_registered_loop_runner"])
    _run([sys.executable, "-m", "tools.db.run_registered_loop_once"])
    _run(
        [
            sys.executable,
            "-m",
            "tools.db.healthcheck",
            "--diagnostic-only",
            "--strict",
            "--require-management-schema",
        ]
    )
    run_result = _json(ARTIFACT_DIR / "registered_loop_run_result.json")
    if run_result.get("status") != "APPLIED_DIAGNOSTIC_ONLY":
        raise AssertionError("runner apply result missing")
    if run_result.get("success_count") != 1 or run_result.get("skipped_count") != 9:
        raise AssertionError("runner success/skipped counts mismatch")
    _db_checks(run_result)

    loop = _json(ARTIFACT_DIR / "loop_contract_report.json")
    if loop.get("scheduler_recurrence_proven") is not False:
        raise AssertionError("recurrence should remain unproven after one bucket")
    if loop.get("acceptance_granted") is not False:
        raise AssertionError("acceptance must not be granted")
    metrics = _json(ARTIFACT_DIR / "db_health_metrics.json")
    if int(metrics.get("reference_hash_count", 0)) < 1:
        raise AssertionError("reference hash count did not increase")
    if int(metrics.get("lineage_edge_count", 0)) < 1:
        raise AssertionError("lineage edge count did not increase")
    if int(metrics.get("paper_order_intents_count", -1)) != 0:
        raise AssertionError("paper order intents must remain zero")

    if len(_rows(ARTIFACT_DIR / "scheduler_run_ledger_task_rows.csv")) != 10:
        raise AssertionError("expected 10 scheduler run rows for runner bucket")
    if len(_rows(ARTIFACT_DIR / "source_receipts_heartbeat.csv")) < 1:
        raise AssertionError("heartbeat source receipt artifact empty")
    if len(_rows(ARTIFACT_DIR / "reference_hashes_heartbeat.csv")) < 1:
        raise AssertionError("heartbeat reference hash artifact empty")
    if len(_rows(ARTIFACT_DIR / "data_lineage_edges_heartbeat.csv")) < 1:
        raise AssertionError("heartbeat lineage edge artifact empty")

    _require(
        ARTIFACT_DIR / "gpt_chrome_review.md",
        ("EXECUTED_REVIEW_ONLY", "diagnostic_runtime_heartbeats", "not source-of-truth"),
    )
    _require(
        REPORT_DIR / f"{TASK}.md",
        (
            "DB_REGISTERED_LOOP_RUNNER_INSTALLED_WITH_HEARTBEAT_EVIDENCE",
            "No replay/backtest was run",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md",
        ("Registered Loop Runner", "NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY"),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        ("Task3651,DB Registered Loop Runner Selection", "Task3670,DB Registered Loop Runner Closeout"),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3651-Task3670", "DB_REGISTERED_LOOP_RUNNER_INSTALLED_WITH_HEARTBEAT_EVIDENCE"),
    )
    print("TASK3651_3670_DB_REGISTERED_LOOP_RUNNER_OK")


if __name__ == "__main__":
    main()

