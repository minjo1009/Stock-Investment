from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3571_3580_db_data_ops_audit"
REPORT_DIR = ROOT / "docs" / "reports" / "task_3571_3580_db_data_ops_audit"


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing required csv: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require_text(path: Path, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing {missing}")


def main() -> None:
    inventory = _rows(ARTIFACT_DIR / "db_inventory.csv")
    cadence = _rows(ARTIFACT_DIR / "data_family_cadence.csv")
    findings = _rows(ARTIFACT_DIR / "db_management_findings.csv")
    if len(inventory) != 11:
        raise AssertionError(f"db inventory row count mismatch: {len(inventory)}")
    if len(cadence) != 14:
        raise AssertionError(f"data cadence row count mismatch: {len(cadence)}")
    if len(findings) != 11:
        raise AssertionError(f"db findings row count mismatch: {len(findings)}")
    if not any(row["db_path"] == "trading.db" and row["integrity"] == "ok" for row in inventory):
        raise AssertionError("trading.db integrity row missing")
    if not any(row["severity"] == "P0" and "control_state" in row["finding"] for row in findings):
        raise AssertionError("P0 control_state finding missing")
    if not any(row["severity"] == "P0" and "authority is ambiguous" in row["finding"] for row in findings):
        raise AssertionError("P0 DB authority finding missing")
    if not any(row["data_family"] == "market_ticks_intraday" and "stale" in row["current_status"] for row in cadence):
        raise AssertionError("market freshness finding missing")
    _require_text(
        REPORT_DIR / "task_3571_3580_db_data_ops_audit.md",
        (
            "DB_DATA_OPS_AUDIT_COMPLETE_WITH_P0_MANAGEMENT_GAPS",
            "control_state.run_mode",
            "LIVE_ENABLED",
            "market ticks/bars stop at `2026-06-03`",
            "source_freshness",
            "schema_migrations",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require_text(
        REPORT_DIR / "task_3580_decision.csv",
        (
            "Task3580",
            "DB_DATA_OPS_AUDIT_COMPLETE_WITH_P0_MANAGEMENT_GAPS",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ),
    )
    _require_text(
        ROOT / "tasks" / "task_registry.csv",
        (
            "Task3571,DB Data Ops Audit Selection",
            "Task3580,DB Data Ops Audit Closeout",
            "task_3571_3580_db_data_ops_audit",
        ),
    )
    _require_text(
        ROOT / "docs" / "operating_system" / "project_operating_state.md",
        (
            "Task3571-Task3580",
            "DB_DATA_OPS_AUDIT_COMPLETE_WITH_P0_MANAGEMENT_GAPS",
            "control_state",
        ),
    )
    print("TASK3571_3580_DB_DATA_OPS_AUDIT_OK")


if __name__ == "__main__":
    main()
