from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise AssertionError(f"missing required file: {path}")
    return full.read_text(encoding="utf-8")


def _require(path: str, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def _csv_rows(path: str) -> list[dict[str, str]]:
    full = ROOT / path
    if not full.exists():
        raise AssertionError(f"missing required csv: {path}")
    with full.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _assert_no_generated_cache() -> None:
    if (ROOT / ".pytest_cache").exists():
        raise AssertionError("generated pytest cache remains: .pytest_cache")


def main() -> None:
    _assert_no_generated_cache()
    cleanup_rows = _csv_rows("data/artifacts/task_3561_3570_ops_cleanup_skillization/cleanup_audit.csv")
    skill_rows = _csv_rows("data/artifacts/task_3561_3570_ops_cleanup_skillization/skillization_backlog.csv")
    if len(cleanup_rows) != 8:
        raise AssertionError(f"cleanup audit row count mismatch: {len(cleanup_rows)}")
    if len(skill_rows) != 5:
        raise AssertionError(f"skillization backlog row count mismatch: {len(skill_rows)}")
    required_skills = {
        "trader-brain-runtime-ops-scheduler",
        "trader-brain-ops-cleanup-retention",
    }
    actual_skills = {row["candidate_skill"] for row in skill_rows}
    missing_skills = sorted(required_skills.difference(actual_skills))
    if missing_skills:
        raise AssertionError(f"missing P0 skill candidates: {missing_skills}")
    _require(
        "docs/reports/task_3561_3570_ops_cleanup_skillization/task_3561_3570_ops_cleanup_skillization.md",
        (
            "OPS_CLEANUP_SKILLIZATION_AUDIT_COMPLETE",
            "cache directories removed: 39+",
            "skillization backlog rows: 5",
            "Decision Summary",
            "Quant Expert Report",
            "No-Background Decision-Maker Report",
            "Artifact Manifest",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        "docs/reports/task_3561_3570_ops_cleanup_skillization/task_3570_decision.csv",
        (
            "Task3570",
            "OPS_CLEANUP_SKILLIZATION_AUDIT_COMPLETE",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ),
    )
    _require(
        "data/artifacts/task_3561_3570_ops_cleanup_skillization/artifact_manifest.md",
        (
            "Removed generated cache directories: 39+",
            "Did not delete logs, DBs, Graphify outputs, external references, source data, reports, or raw artifacts.",
        ),
    )
    _require(
        "tasks/task_registry.csv",
        (
            "Task3561,Ops Cleanup Skillization Selection",
            "Task3570,Ops Cleanup Skillization Closeout",
            "task_3561_3570_ops_cleanup_skillization",
        ),
    )
    _require(
        "docs/operating_system/project_operating_state.md",
        (
            "Task3561-Task3570",
            "generated cache directories",
            "skillization backlog",
        ),
    )
    _require(
        "docs/obsidian/Vault Home.md",
        (
            "Task3561-3570",
            "Ops Cleanup Skillization",
            "P0 skill candidates",
        ),
    )
    print("TASK3561_3570_OK")


if __name__ == "__main__":
    main()
