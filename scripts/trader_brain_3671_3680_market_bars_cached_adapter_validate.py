from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3671_3680_market_bars_cached_adapter"
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
    bucket = str(run_result["bucket_ts"])
    con = sqlite3.connect(f"file:{(ROOT / 'trading.db').as_posix()}?mode=ro", uri=True, timeout=10)
    try:
        con.row_factory = sqlite3.Row
        freshness = con.execute(
            """
            SELECT freshness_status, strict_gate_allowed, proxy_allowed, evidence_ref, max_source_ts
            FROM source_freshness
            WHERE source_family='market_bars_5m'
            """
        ).fetchone()
        if not freshness:
            raise AssertionError("market_bars_5m freshness row missing")
        if freshness["freshness_status"] != "STALE":
            raise AssertionError(f"market_bars_5m must remain STALE, got {freshness['freshness_status']}")
        if int(freshness["strict_gate_allowed"]) != 0 or int(freshness["proxy_allowed"]) != 0:
            raise AssertionError("market_bars_5m gates must remain closed")
        if freshness["max_source_ts"] != "2026-06-03T16:14:59Z":
            raise AssertionError(f"unexpected market_bars_5m max_source_ts: {freshness['max_source_ts']}")

        receipt_count = con.execute(
            "SELECT COUNT(*) FROM source_receipts WHERE source_family='market_bars_5m'"
        ).fetchone()[0]
        ref_count = con.execute(
            "SELECT COUNT(*) FROM reference_hashes WHERE source_family='market_bars_5m'"
        ).fetchone()[0]
        edge_count = con.execute(
            "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family='market_bars_5m'"
        ).fetchone()[0]
        if receipt_count < 1 or ref_count < 1 or edge_count < 1:
            raise AssertionError("market_bars_5m receipt/hash/lineage evidence missing")

        success = con.execute(
            """
            SELECT validation_refs_json
            FROM scheduler_run_ledger
            WHERE expected_bucket_ts=? AND status='SUCCESS' AND cadence='market_bars_5m_refresh'
            """,
            (bucket,),
        ).fetchone()
        if not success:
            raise AssertionError("market_bars_5m scheduler success row missing")
        validation = json.loads(success["validation_refs_json"])
        if validation.get("cached_source_only") != 1 or validation.get("live_fetch") != 0:
            raise AssertionError("market_bars_5m ledger must prove cached-only/no-live-fetch")
        if validation.get("freshness_recovered") != 0:
            raise AssertionError("stale market_bars_5m must not report freshness recovered")
        if validation.get("strict_gate_allowed") != 0 or validation.get("proxy_allowed") != 0:
            raise AssertionError("market_bars_5m ledger gates must be closed")

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

    run_result = _json(ARTIFACT_DIR / "registered_loop_run_result.json")
    if run_result.get("status") != "APPLIED_DIAGNOSTIC_ONLY":
        raise AssertionError("runner apply result missing")
    if run_result.get("success_count") != 2 or run_result.get("skipped_count") != 8:
        raise AssertionError("runner success/skipped counts mismatch")
    _db_checks(run_result)

    snapshot = _json(ARTIFACT_DIR / "market_bars_cached_snapshot.json")
    if snapshot.get("live_fetch") is not False:
        raise AssertionError("market snapshot must be live_fetch=false")
    if snapshot.get("freshness_status") != "STALE":
        raise AssertionError("market snapshot must record stale status")
    if snapshot.get("strict_gate_allowed") is not False or snapshot.get("proxy_allowed") is not False:
        raise AssertionError("market snapshot gates must be closed")
    if int(snapshot.get("snapshot_stats", {}).get("row_count", 0)) != 30410:
        raise AssertionError("unexpected active market_bars_5m row count")

    loop = _json(ARTIFACT_DIR / "loop_contract_report.json")
    if "market_bars_5m" not in loop.get("freshness_blockers", []):
        raise AssertionError("market_bars_5m must remain a freshness blocker")
    if "market_bars_5m" in loop.get("receipt_gaps", []):
        raise AssertionError("market_bars_5m receipt gap should be closed")
    if "market_bars_5m" in loop.get("lineage_gaps", []):
        raise AssertionError("market_bars_5m lineage gap should be closed")

    metrics = _json(ARTIFACT_DIR / "db_health_metrics.json")
    if metrics.get("healthcheck_status") != "PASS":
        raise AssertionError("db healthcheck must pass")
    if int(metrics.get("paper_order_intents_count", -1)) != 0:
        raise AssertionError("paper order intents must remain zero")

    for path in (
        ARTIFACT_DIR / "source_receipts_market_bars_5m.csv",
        ARTIFACT_DIR / "reference_hashes_market_bars_5m.csv",
        ARTIFACT_DIR / "data_lineage_edges_market_bars_5m.csv",
        ARTIFACT_DIR / "source_freshness_market_bars_5m.csv",
        ARTIFACT_DIR / "scheduler_run_ledger_market_bars_5m.csv",
    ):
        if not _rows(path):
            raise AssertionError(f"empty artifact: {path.relative_to(ROOT)}")

    _require(
        ARTIFACT_DIR / "gpt_chrome_review.md",
        ("EXECUTED_REVIEW_ONLY", "cached snapshot evidence", "not source-of-truth"),
    )
    _require(
        REPORT_DIR / f"{TASK}.md",
        (
            "MARKET_BARS_5M_CACHED_ADAPTER_INSTALLED_STALE_BLOCKER_RETAINED",
            "No live fetch was run",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md",
        ("Cached Market Bars Adapter", "NO_CACHED_MARKET_BARS_5M_SOURCE"),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        ("Task3671,Market Bars Cached Adapter Selection", "Task3680,Market Bars Cached Adapter Closeout"),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3671-Task3680", "MARKET_BARS_5M_CACHED_ADAPTER_INSTALLED_STALE_BLOCKER_RETAINED"),
    )
    print("TASK3671_3680_MARKET_BARS_CACHED_ADAPTER_OK")


if __name__ == "__main__":
    main()
