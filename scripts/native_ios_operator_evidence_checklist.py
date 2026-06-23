"""Build Task3853 read-only native iOS operator evidence checklist artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3853_native_ios_operator_evidence_checklist"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID

CHECKLIST_PATH = ARTIFACT_DIR / "native_ios_operator_evidence_checklist.csv"
TRACE_PATH = ARTIFACT_DIR / "native_ios_evidence_trace.csv"
STATE_PATH = ARTIFACT_DIR / "native_ios_operator_evidence_checklist_state.json"
REPORT_PATH = REPORT_DIR / "native_ios_operator_evidence_checklist_report.md"
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


def build_checklist() -> list[dict[str, str]]:
    return [
        {
            "check_id": "ios_evidence_001",
            "area": "development_build",
            "required_evidence": "development build command and environment outcome",
            "current_status": "UNKNOWN/BLOCKER",
            "permission_granted": "false",
            "notes": "Diagnostic evidence only; deployment readiness remains forbidden.",
        },
        {
            "check_id": "ios_evidence_002",
            "area": "device_runtime",
            "required_evidence": "physical iOS device launch proof or simulator substitute explicitly marked",
            "current_status": "UNKNOWN/BLOCKER",
            "permission_granted": "false",
            "notes": "No Expo Go assumption; native development client evidence is required.",
        },
        {
            "check_id": "ios_evidence_003",
            "area": "visual_evidence",
            "required_evidence": "fresh screenshots for HOME/BRAIN/PORTFOLIO/ORDERS/SYSTEM read-only surfaces",
            "current_status": "UNKNOWN/BLOCKER",
            "permission_granted": "false",
            "notes": "Screenshots do not validate trading strategy or broker permission.",
        },
        {
            "check_id": "ios_evidence_004",
            "area": "governance_affordance",
            "required_evidence": "visible blocked state for broker mutation, paper/live, and real capital",
            "current_status": "UNKNOWN/BLOCKER",
            "permission_granted": "false",
            "notes": "Every trading action must remain disabled or absent.",
        },
        {
            "check_id": "ios_evidence_005",
            "area": "operator_handoff",
            "required_evidence": "read-only operator runbook and non-production caveats",
            "current_status": "UNKNOWN/BLOCKER",
            "permission_granted": "false",
            "notes": "Operator evidence is not deployment approval.",
        },
    ]


def build_trace() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_name in [
        "native_ios_evidence_plan.csv",
        "native_ios_build_evidence_plan.csv",
        "native_ios_screenshot_evidence_plan.csv",
    ]:
        source_path = PREV_ARTIFACT_DIR / source_name
        source_rows = read_csv(source_path)
        rows.append(
            {
                "source_artifact": str(source_path),
                "source_rows": str(len(source_rows)),
                "trace_status": "READ_ONLY_REFERENCED" if source_rows else "UNKNOWN/BLOCKER",
                "notes": "Referenced as planning evidence only; no build, install, or device run was executed.",
            }
        )
    return rows


def build_manifest() -> list[dict[str, str]]:
    return [
        {"artifact_path": str(CHECKLIST_PATH), "artifact_type": "csv", "authority": "diagnostic", "status": "generated", "notes": "read-only iOS operator evidence checklist"},
        {"artifact_path": str(TRACE_PATH), "artifact_type": "csv", "authority": "diagnostic", "status": "generated", "notes": "read-only trace to prior iOS evidence plans"},
        {"artifact_path": str(STATE_PATH), "artifact_type": "json", "authority": "diagnostic", "status": "generated", "notes": "hard-state guardrail summary"},
        {"artifact_path": str(REPORT_PATH), "artifact_type": "markdown", "authority": "diagnostic", "status": "generated", "notes": "task closeout report"},
    ]


def write_report(state: dict[str, Any], checklist: list[dict[str, str]], trace: list[dict[str, str]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3853 Native iOS Operator Evidence Checklist",
        "",
        "## Summary",
        "- [actual] This task generated a read-only iOS operator evidence checklist.",
        "- [actual] It does not run iOS builds, install apps, mutate brokers, access DBs, or grant deployment permission.",
        "- [actual] Missing or stale evidence remains UNKNOWN/BLOCKER.",
        "",
        "## Hard State",
        f"- Strategy: {state['strategy']}",
        f"- Deployment: {state['deployment']}",
        f"- Real capital: {state['real_capital']}",
        "",
        "## Counts",
        f"- Checklist rows: {len(checklist)}",
        f"- Trace rows: {len(trace)}",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    checklist = build_checklist()
    trace = build_trace()
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_NATIVE_IOS_OPERATOR_EVIDENCE_COMPLETE_WITH_BLOCKERS",
        "checklist_row_count": len(checklist),
        "trace_row_count": len(trace),
        "permission_granted_rows": sum(1 for row in checklist if row["permission_granted"] != "false"),
        "ios_build_run": False,
        "device_install_run": False,
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(CHECKLIST_PATH, checklist, ["check_id", "area", "required_evidence", "current_status", "permission_granted", "notes"])
    write_csv(TRACE_PATH, trace, ["source_artifact", "source_rows", "trace_status", "notes"])
    write_json(STATE_PATH, state)
    write_report(state, checklist, trace)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
