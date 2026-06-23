"""Build Task3851 read-only kill-switch clearance checklist artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3851_kill_switch_clearance_checklist"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID

CHECKLIST_PATH = ARTIFACT_DIR / "kill_switch_clearance_checklist.csv"
TRACE_PATH = ARTIFACT_DIR / "kill_switch_blocker_trace.csv"
STATE_PATH = ARTIFACT_DIR / "kill_switch_clearance_checklist_state.json"
REPORT_PATH = REPORT_DIR / "kill_switch_clearance_checklist_report.md"
MANIFEST_PATH = REPORT_DIR / "artifact_manifest.csv"

HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_checklist() -> list[dict[str, Any]]:
    items = [
        ("source_freshness_clear", "All source freshness blockers resolved with evidence.", "BLOCKED"),
        ("authority_evidence_clear", "Receipt/hash/lineage/freshness authority proof chain reviewed.", "BLOCKED"),
        ("broker_truth_clear", "Broker truth reconciliation evidence reviewed without mutation.", "BLOCKED"),
        ("execution_permission_clear", "Execution permission explicitly reviewed and still closed unless future governance changes.", "BLOCKED"),
        ("paper_permission_clear", "Paper permission explicitly reviewed and still closed unless future governance changes.", "BLOCKED"),
        ("emergency_cancel_clear", "Emergency cancel policy reviewed separately without live order implication.", "BLOCKED"),
        ("operator_signoff_clear", "Human/operator signoff captured in future authoritative docs.", "BLOCKED"),
    ]
    return [
        {
            "check_id": f"kill-check-{index:02d}",
            "check_name": name,
            "required_evidence": evidence,
            "current_status": status,
            "clearance_allowed_now": "false",
            "control_state_mutation_allowed": "false",
        }
        for index, (name, evidence, status) in enumerate(items, 1)
    ]


def build_trace(kill_rows: list[dict[str, str]], paper_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in kill_rows:
        output.append(
            {
                "source": "kill_switch_audit",
                "key": row.get("control_key", "default"),
                "area": "kill_switch_active",
                "current_value": row.get("kill_switch_active", "UNKNOWN"),
                "status": row.get("clearance_status", "BLOCKED"),
                "clearance_allowed_now": "false",
                "notes": row.get("notes", ""),
            }
        )
        output.append(
            {
                "source": "kill_switch_audit",
                "key": row.get("control_key", "default"),
                "area": "run_mode",
                "current_value": row.get("run_mode", "UNKNOWN"),
                "status": row.get("clearance_status", "BLOCKED"),
                "clearance_allowed_now": "false",
                "notes": row.get("kill_switch_reason", ""),
            }
        )
    for row in paper_rows:
        output.append(
            {
                "source": "paper_gate_blocker_matrix",
                "key": row.get("gate_id", ""),
                "area": row.get("gate", ""),
                "current_value": row.get("current_value", ""),
                "status": row.get("status", "BLOCKED"),
                "clearance_allowed_now": "false",
                "notes": row.get("notes", ""),
            }
        )
    return output


def build_manifest() -> list[dict[str, str]]:
    paths = [CHECKLIST_PATH, TRACE_PATH, STATE_PATH, REPORT_PATH, MANIFEST_PATH]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by Task3851 read-only kill-switch clearance checklist.",
        }
        for path in paths
    ]


def write_report(state: dict[str, Any], checklist_rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3851 Kill-switch Clearance Checklist",
        "",
        "## Summary",
        "",
        "This task records the evidence required before any future kill-switch clearance discussion.",
        "It does not clear, toggle, or mutate kill-switch or control state.",
        "",
        "## Hard State",
        "",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "- Kill-switch clearance: BLOCKED",
        "",
        "## Checklist",
        "",
        "| Check | Status | Clearance Allowed Now |",
        "| --- | --- | --- |",
    ]
    for row in checklist_rows:
        lines.append(f"| {row['check_name']} | {row['current_status']} | {row['clearance_allowed_now']} |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Checklist: `{CHECKLIST_PATH.as_posix()}`",
            f"- Blocker trace: `{TRACE_PATH.as_posix()}`",
            "",
            "## Safety",
            "",
            "- No control state mutation was performed.",
            "- Kill switch remains uncleared.",
            "- No paper/live permission, broker mutation, deployment readiness, strategy acceptance, or real-capital permission is granted.",
            "",
            "## State",
            "",
            f"- Checklist rows: {state['checklist_row_count']}",
            f"- Clearance allowed rows: {state['clearance_allowed_rows']}",
            f"- Control mutation rows: {state['control_mutation_rows']}",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    kill_rows = read_csv(PREV_ARTIFACT_DIR / "kill_switch_audit.csv")
    paper_rows = read_csv(PREV_ARTIFACT_DIR / "paper_gate_blocker_matrix.csv")
    if not kill_rows:
        raise SystemExit("Task3845 kill switch audit is missing or empty.")
    checklist_rows = build_checklist()
    trace_rows = build_trace(kill_rows, paper_rows)
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_KILL_SWITCH_CHECKLIST_COMPLETE_WITH_BLOCKERS",
        "checklist_row_count": len(checklist_rows),
        "trace_row_count": len(trace_rows),
        "clearance_allowed_rows": sum(1 for row in checklist_rows if row["clearance_allowed_now"] != "false"),
        "control_mutation_rows": sum(1 for row in checklist_rows if row["control_state_mutation_allowed"] != "false"),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(
        CHECKLIST_PATH,
        checklist_rows,
        ["check_id", "check_name", "required_evidence", "current_status", "clearance_allowed_now", "control_state_mutation_allowed"],
    )
    write_csv(
        TRACE_PATH,
        trace_rows,
        ["source", "key", "area", "current_value", "status", "clearance_allowed_now", "notes"],
    )
    write_json(STATE_PATH, state)
    write_report(state, checklist_rows)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
