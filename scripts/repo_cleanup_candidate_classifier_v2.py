"""Build Task3854 read-only repo cleanup candidate classifier artifacts."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3854_repo_cleanup_candidate_classifier_v2"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

CLASSIFIER_PATH = ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2.csv"
SUMMARY_PATH = ARTIFACT_DIR / "repo_cleanup_candidate_summary.csv"
STATE_PATH = ARTIFACT_DIR / "repo_cleanup_candidate_classifier_v2_state.json"
REPORT_PATH = REPORT_DIR / "repo_cleanup_candidate_classifier_v2_report.md"
MANIFEST_PATH = REPORT_DIR / "artifact_manifest.csv"

HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def classify_path(path: str, tracked: bool, status: str) -> dict[str, str]:
    if path.startswith("data/artifacts/"):
        category = "generated_artifact"
        action = "MANIFEST_AND_IGNORE_REVIEW"
    elif path.startswith("docs/reports/"):
        category = "task_report"
        action = "KEEP_IF_TASK_CANONICAL"
    elif path.startswith("scripts/"):
        category = "automation_script"
        action = "KEEP_WITH_VALIDATOR_IF_ACTIVE"
    elif path == "tasks/task_registry.csv":
        category = "registry"
        action = "SEPARATE_RECOVERY_REVIEW"
    elif path.endswith(".db") or path.endswith(".sqlite"):
        category = "database_copy"
        action = "AUTHORITY_CLASSIFICATION_REQUIRED"
    else:
        category = "repo_file"
        action = "NO_ACTION_CLASSIFIED"
    return {
        "path": path,
        "tracked": str(tracked).lower(),
        "git_status": status,
        "category": category,
        "recommended_action": action,
        "destructive_action_permitted": "false",
        "notes": "Classification only; do not remove, move, or rewrite from this output.",
    }


def build_rows() -> list[dict[str, str]]:
    tracked_paths = set(run_git(["ls-files"]))
    status_lines = run_git(["status", "--short"])
    status_map: dict[str, str] = {}
    for line in status_lines:
        status = line[:2].strip() or "modified"
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status_map[path] = status
    candidate_paths = sorted({path for path in tracked_paths if path.startswith(("data/artifacts/", "docs/reports/"))} | set(status_map))
    return [classify_path(path, path in tracked_paths, status_map.get(path, "tracked")) for path in candidate_paths]


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    buckets: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["category"], row["recommended_action"])
        buckets[key] = buckets.get(key, 0) + 1
    return [
        {"category": category, "recommended_action": action, "row_count": str(count), "destructive_action_permitted": "false"}
        for (category, action), count in sorted(buckets.items())
    ]


def build_manifest() -> list[dict[str, str]]:
    return [
        {"artifact_path": str(CLASSIFIER_PATH), "artifact_type": "csv", "authority": "diagnostic", "status": "generated", "notes": "read-only cleanup candidate classification"},
        {"artifact_path": str(SUMMARY_PATH), "artifact_type": "csv", "authority": "diagnostic", "status": "generated", "notes": "classification summary"},
        {"artifact_path": str(STATE_PATH), "artifact_type": "json", "authority": "diagnostic", "status": "generated", "notes": "hard-state guardrail summary"},
        {"artifact_path": str(REPORT_PATH), "artifact_type": "markdown", "authority": "diagnostic", "status": "generated", "notes": "task closeout report"},
    ]


def write_report(state: dict[str, Any], summary: list[dict[str, str]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3854 Repo Cleanup Candidate Classifier v2",
        "",
        "## Summary",
        "- [actual] This task generated a read-only cleanup candidate classifier.",
        "- [actual] It permits no destructive action and does not resolve authority by inference.",
        "- [actual] DB copies and generated artifacts remain UNKNOWN/BLOCKER until separately reviewed.",
        "",
        "## Hard State",
        f"- Strategy: {state['strategy']}",
        f"- Deployment: {state['deployment']}",
        f"- Real capital: {state['real_capital']}",
        "",
        "## Category Summary",
    ]
    lines.extend(f"- {row['category']} / {row['recommended_action']}: {row['row_count']}" for row in summary)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = build_summary(rows)
    state = {
        "task_id": TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_REPO_CLEANUP_CLASSIFIER_COMPLETE_WITH_BLOCKERS",
        "classified_row_count": len(rows),
        "summary_row_count": len(summary),
        "destructive_action_rows": sum(1 for row in rows if row["destructive_action_permitted"] != "false"),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(CLASSIFIER_PATH, rows, ["path", "tracked", "git_status", "category", "recommended_action", "destructive_action_permitted", "notes"])
    write_csv(SUMMARY_PATH, summary, ["category", "recommended_action", "row_count", "destructive_action_permitted"])
    write_json(STATE_PATH, state)
    write_report(state, summary)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
