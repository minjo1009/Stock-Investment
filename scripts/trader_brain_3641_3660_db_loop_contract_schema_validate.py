from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3641_3660_db_loop_contract_schema"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise AssertionError(f"missing json: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"json must be object: {path.relative_to(ROOT)}")
    return payload


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


def _db_checks() -> None:
    con = sqlite3.connect(f"file:{(ROOT / 'trading.db').as_posix()}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        required_tables = {
            "scheduler_job_registry",
            "source_freshness_policy",
            "reference_hashes",
            "data_lineage_edges",
        }
        actual = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        missing = required_tables.difference(actual)
        if missing:
            raise AssertionError(f"missing management tables: {sorted(missing)}")
        jobs = con.execute("SELECT COUNT(*) FROM scheduler_job_registry").fetchone()[0]
        policies = con.execute("SELECT COUNT(*) FROM source_freshness_policy").fetchone()[0]
        if jobs != 10 or policies != 10:
            raise AssertionError(f"job/policy row mismatch: {jobs}/{policies}")
        unsafe = con.execute(
            """
            SELECT COUNT(*) FROM scheduler_job_registry
            WHERE diagnostic_only != 1
               OR execution_permitted != 0
               OR broker_mutation_permitted != 0
               OR real_capital_permitted != 0
               OR paper_promotion_permitted != 0
            """
        ).fetchone()[0]
        if unsafe:
            raise AssertionError("unsafe scheduler registry permission row exists")
        semantics = con.execute(
            """
            SELECT COUNT(*) FROM source_freshness_policy
            WHERE missing_semantics != 'UNKNOWN_BLOCKER'
               OR stale_semantics != 'UNKNOWN_BLOCKER'
            """
        ).fetchone()[0]
        if semantics:
            raise AssertionError("stale/missing semantics must remain UNKNOWN_BLOCKER")
        migration = con.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_id='task3641_db_loop_contract_schema_v1'"
        ).fetchone()[0]
        if migration != 1:
            raise AssertionError("schema migration row missing")
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise AssertionError(f"foreign key violations: {len(fk)}")
    finally:
        con.close()


def main() -> None:
    _run([sys.executable, "-m", "tools.db.apply_management_schema"])
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
    _run([sys.executable, "-m", "tools.db.restore_drill"])
    _db_checks()

    jobs = _rows(ARTIFACT_DIR / "scheduler_job_registry.csv")
    policies = _rows(ARTIFACT_DIR / "source_freshness_policy.csv")
    if len(jobs) != 10 or len(policies) != 10:
        raise AssertionError("artifact job/policy row count mismatch")
    loop = _json(ARTIFACT_DIR / "loop_contract_report.json")
    if loop.get("jobs_registered") != 10:
        raise AssertionError("loop report jobs_registered mismatch")
    if loop.get("acceptance_granted") is not False:
        raise AssertionError("loop report must not grant acceptance")
    if loop.get("broker_mutation_permitted") is not False:
        raise AssertionError("loop report must not permit broker mutation")
    if loop.get("scheduler_recurrence_proven") is not False:
        raise AssertionError("scheduler recurrence should remain unproven")

    _require(
        ARTIFACT_DIR / "gpt_chrome_review.md",
        ("EXECUTED_REVIEW_ONLY", "CHECK constraints", "not source-of-truth"),
    )
    _require(
        REPORT_DIR / f"{TASK}.md",
        (
            "DB_LOOP_CONTRACT_SCHEMA_INSTALLED_WITH_BLOCKERS",
            "No replay/backtest was run",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md",
        ("DB Loop Contract Schema", "execution_permitted", "UNKNOWN_BLOCKER"),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        ("Task3641,DB Loop Contract Schema Selection", "Task3660,DB Loop Contract Schema Closeout"),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3641-Task3660", "DB_LOOP_CONTRACT_SCHEMA_INSTALLED_WITH_BLOCKERS"),
    )
    print("TASK3641_3660_DB_LOOP_CONTRACT_SCHEMA_OK")


if __name__ == "__main__":
    main()

