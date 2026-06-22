from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_3431_3480_runtime_promotion_blocker_hardening"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3431_3480_runtime_promotion_blocker_hardening"
REPORT = REPORT_DIR / "task_3431_3480_runtime_promotion_blocker_hardening.md"
DECISION = REPORT_DIR / "task_3480_decision.csv"
HARDENING = ARTIFACT_DIR / "hardening_status.csv"
VALIDATION = ARTIFACT_DIR / "validation_results.csv"
MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"
REGISTRY = ROOT / "tasks" / "task_registry.csv"
OPERATING_STATE = ROOT / "docs" / "operating_system" / "project_operating_state.md"


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stdout + proc.stderr)
    return proc.stdout + proc.stderr


def main() -> None:
    report = _read(REPORT)
    manifest = _read(MANIFEST)
    registry = _read(REGISTRY)
    operating_state = _read(OPERATING_STATE)

    for term in [
        "P0_RUNTIME_HARDENING_IMPLEMENTED_PROMOTION_STILL_BLOCKED",
        "Task588 PowerShell parser: PASS",
        "`run_trade_once` dummy fallback path: blocked",
        "default Task585 legacy paper execution path: blocked",
        "Task588 5-minute safety heartbeat ledger: implemented",
        "Broker submit/local record atomicity | Still open",
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
    ]:
        if term not in report:
            raise AssertionError(f"missing report term: {term}")

    decision_rows = _rows(DECISION)
    if len(decision_rows) != 1:
        raise AssertionError(f"expected 1 decision row, got {len(decision_rows)}")
    if decision_rows[0].get("decision") != "P0_RUNTIME_HARDENING_IMPLEMENTED_PROMOTION_STILL_BLOCKED":
        raise AssertionError("unexpected decision")
    if decision_rows[0].get("real_capital") != "FORBIDDEN":
        raise AssertionError("real capital boundary missing")

    hardening_rows = _rows(HARDENING)
    if len(hardening_rows) != 10:
        raise AssertionError(f"expected 10 hardening rows, got {len(hardening_rows)}")
    required_items = {
        "Task588 PowerShell parser": "CLOSED",
        "run_trade_once dummy fallback": "CLOSED",
        "Task585 default legacy execution guard": "CLOSED",
        "full semantic scheduler": "OPEN",
    }
    for item, status in required_items.items():
        if not any(row["item"] == item and row["status"] == status for row in hardening_rows):
            raise AssertionError(f"missing hardening row: {item}={status}")

    validation_rows = _rows(VALIDATION)
    if len(validation_rows) != 4:
        raise AssertionError(f"expected 4 validation rows, got {len(validation_rows)}")

    if "hardening status: 10" not in manifest:
        raise AssertionError("manifest row count missing")
    if "Task3431" not in registry or "Task3480" not in registry:
        raise AssertionError("missing Task3431/Task3480 registry rows")
    if "Task3431-Task3480" not in operating_state:
        raise AssertionError("missing operating state entry")

    ps_command = (
        "$errors=$null; "
        "[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath 'scripts/run_task588_nasdaq_paper_loop.ps1'), [ref]$errors) | Out-Null; "
        "if ($errors) { $errors | ForEach-Object { $_.Message }; exit 1 }"
    )
    _run(["powershell", "-NoProfile", "-Command", ps_command])

    test_command = [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_task588_nasdaq_paper_supervisor_scripts",
        "tests.test_run_trade_once_runtime_signal",
        "tests.test_task585_kis_paper_order_execution",
        "tests.test_runtime_diagnostic_ledger",
        "tests.test_task588_kis_paper_market_hours_runtime_loop",
        "tests.test_brain_diagnostic_orchestration",
    ]
    env_prefix = str(ROOT / "src")
    import os

    old_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = env_prefix + (os.pathsep + old_pythonpath if old_pythonpath else "")
    try:
        _run(test_command)
    finally:
        if old_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = old_pythonpath

    print("[TASK3431_3480_OK] Runtime promotion blocker hardening validated")


if __name__ == "__main__":
    main()
