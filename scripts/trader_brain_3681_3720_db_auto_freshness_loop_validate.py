from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3681_3720_db_auto_freshness_loop"
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
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def _require(path: Path, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing {missing}")


def _db_checks() -> None:
    con = sqlite3.connect(f"file:{(ROOT / 'trading.db').as_posix()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        jobs = con.execute("SELECT COUNT(*) FROM scheduler_job_registry").fetchone()[0]
        policies = con.execute("SELECT COUNT(*) FROM source_freshness_policy").fetchone()[0]
        if jobs != 12 or policies != 12:
            raise AssertionError(f"expected 12 jobs/policies, got {jobs}/{policies}")
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
            raise AssertionError("unsafe scheduler permissions found")
        required = [
            "broker_truth_reconciliation",
            "indicator_snapshots",
            "market_bars_5m",
            "market_ticks_intraday",
            "runtime_strategy_decisions",
        ]
        for family in required:
            receipt_count = con.execute(
                "SELECT COUNT(*) FROM source_receipts WHERE source_family=?",
                (family,),
            ).fetchone()[0]
            edge_count = con.execute(
                "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family=?",
                (family,),
            ).fetchone()[0]
            if receipt_count < 1 or edge_count < 1:
                raise AssertionError(f"missing receipt/lineage evidence for {family}")
            fresh = con.execute(
                """
                SELECT freshness_status, strict_gate_allowed, proxy_allowed
                FROM source_freshness
                WHERE source_family=?
                """,
                (family,),
            ).fetchone()
            if not fresh or fresh["freshness_status"] != "STALE":
                raise AssertionError(f"{family} should remain STALE")
            if int(fresh["strict_gate_allowed"]) != 0 or int(fresh["proxy_allowed"]) != 0:
                raise AssertionError(f"{family} gates must remain closed")
        authority_skips = con.execute(
            """
            SELECT COUNT(*) FROM scheduler_run_ledger
            WHERE cadence='l6_authority_evidence_refresh'
              AND skipped_reason='NO_CACHED_AUTHORITY_EVIDENCE_LEDGER_SOURCE'
            """
        ).fetchone()[0]
        if authority_skips < 1:
            raise AssertionError("authority evidence empty-ledger skip missing")
        if con.execute("SELECT COUNT(*) FROM paper_order_intents").fetchone()[0] != 0:
            raise AssertionError("paper_order_intents must remain zero")
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
    _db_checks()
    run_result = _json(ARTIFACT_DIR / "registered_loop_run_result_after_contract_expansion.json")
    if run_result.get("jobs_seen") != 12 or run_result.get("success_count") != 6 or run_result.get("skipped_count") != 6:
        raise AssertionError("expanded runner result mismatch")
    health = _json(ARTIFACT_DIR / "db_health_metrics_after_contract_expansion.json")
    if health.get("healthcheck_status") != "PASS":
        raise AssertionError("healthcheck artifact must pass")
    loop = _json(ARTIFACT_DIR / "loop_contract_report_after_contract_expansion.json")
    if loop.get("jobs_registered") != 12:
        raise AssertionError("loop contract report must show 12 jobs")
    for family in ("broker_truth_reconciliation", "indicator_snapshots", "market_bars_5m", "market_ticks_intraday", "runtime_strategy_decisions"):
        if family in loop.get("receipt_gaps", []) or family in loop.get("lineage_gaps", []):
            raise AssertionError(f"{family} should not remain a receipt/lineage gap")
    if len(_rows(ARTIFACT_DIR / "db_auto_freshness_10_loop_plan.csv")) != 10:
        raise AssertionError("10-loop plan artifact must have 10 rows")
    _require(
        REPORT_DIR / f"{TASK}.md",
        (
            "DB_AUTO_FRESHNESS_LOOP_EXPANDED_WITH_CACHED_EVIDENCE",
            "No live fetch was run",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        ("Task3681,DB Auto Freshness Loop Selection", "Task3720,DB Auto Freshness Loop Closeout"),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3681-Task3720", "DB_AUTO_FRESHNESS_LOOP_EXPANDED_WITH_CACHED_EVIDENCE"),
    )
    print("TASK3681_3720_DB_AUTO_FRESHNESS_LOOP_OK")


if __name__ == "__main__":
    main()
