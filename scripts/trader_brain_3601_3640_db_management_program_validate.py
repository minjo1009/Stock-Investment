from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = "task_3601_3640_db_management_program"
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


def _json(path: Path) -> dict[str, object] | list[object]:
    if not path.exists():
        raise AssertionError(f"missing required json: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> None:
    _run([sys.executable, "-m", "tools.db.healthcheck", "--diagnostic-only", "--strict"])
    _run([sys.executable, "-m", "tools.db.restore_drill"])

    plan = _rows(ARTIFACT_DIR / "db_management_program_plan.csv")
    if len(plan) != 40:
        raise AssertionError(f"program plan row count mismatch: {len(plan)}")
    plan_ids = {row["task_id"] for row in plan}
    for required in {"Task3601", "Task3610", "Task3621", "Task3640"}:
        if required not in plan_ids:
            raise AssertionError(f"missing program plan task {required}")

    topology = _rows(ARTIFACT_DIR / "db_topology_contract.csv")
    cadence = _rows(ARTIFACT_DIR / "db_loop_cadence_contract.csv")
    tooling = _rows(ARTIFACT_DIR / "db_tooling_decision_matrix.csv")
    scan = _rows(ARTIFACT_DIR / "db_authority_scan.csv")
    if len(topology) < 7:
        raise AssertionError("topology contract incomplete")
    if len(cadence) != 10:
        raise AssertionError("cadence contract must have 10 families")
    if len(tooling) != 8:
        raise AssertionError("tooling matrix must have 8 rows")
    if not any(row["db_path"] == "trading.db" and row["status"] == "ACTIVE" for row in scan):
        raise AssertionError("scan missing active trading.db row")
    if any(row["status"] == "QUARANTINE_REQUIRED" for row in scan):
        raise AssertionError("scan still has quarantine-required DB rows")

    metrics = _json(ARTIFACT_DIR / "db_health_metrics.json")
    if not isinstance(metrics, dict):
        raise AssertionError("metrics payload must be a dict")
    if metrics.get("healthcheck_status") not in {None, "PASS"}:
        raise AssertionError("healthcheck artifact reports failure")
    if metrics.get("governance_health") not in {"PASS_WITH_SOURCE_BLOCKERS", "PASS"}:
        raise AssertionError("governance health not pass-with-blockers")
    if metrics.get("control_guard_status") != "PASS_FAIL_CLOSED":
        raise AssertionError("control state guard must be fail-closed")
    if int(metrics.get("paper_order_intents_count", -1)) != 0:
        raise AssertionError("paper_order_intents must remain zero")

    restore = _json(ARTIFACT_DIR / "restore_drill_result.json")
    if not isinstance(restore, dict) or restore.get("restore_drill_status") != "PASS":
        raise AssertionError("restore drill did not pass")

    _require(
        ARTIFACT_DIR / "gpt_chrome_review.md",
        ("EXECUTED_REVIEW_ONLY", "not source-of-truth", "Real Capital `FORBIDDEN`"),
    )
    _require(
        REPORT_DIR / f"{TASK}.md",
        (
            "DB_MANAGEMENT_PROGRAM_IMPLEMENTED_WITH_SOURCE_BLOCKERS",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "No replay/backtest was run",
        ),
    )
    _require(
        ROOT / "docs" / "db" / "DB_TOPOLOGY.md",
        ("Active authority", "readonly_mcp", "NOT_ACCEPTED"),
    )
    _require(
        ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md",
        ("Acquire a lease", "RECEIPT_MISSING", "scheduler_run_ledger"),
    )
    _require(
        ROOT / "tasks" / "task_registry.csv",
        ("Task3601,DB Management Program Selection", "Task3640,DB Management Program Closeout"),
    )
    _require(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        ("Task3601-Task3640", "DB_MANAGEMENT_PROGRAM_IMPLEMENTED_WITH_SOURCE_BLOCKERS"),
    )
    print("TASK3601_3640_DB_MANAGEMENT_PROGRAM_OK")


if __name__ == "__main__":
    main()

