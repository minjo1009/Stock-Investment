"""Validate Task3845 read-only source authority gate artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_ARTIFACTS = [
    ARTIFACT_DIR / "source_authority_gate_state.json",
    ARTIFACT_DIR / "scope_phase_map.csv",
    ARTIFACT_DIR / "source_inventory.csv",
    ARTIFACT_DIR / "freshness_certification_matrix.csv",
    ARTIFACT_DIR / "sec_hybrid_provider_chain.csv",
    ARTIFACT_DIR / "authority_ledger_summary.csv",
    ARTIFACT_DIR / "broker_truth_gap_matrix.csv",
    ARTIFACT_DIR / "kill_switch_audit.csv",
    ARTIFACT_DIR / "paper_gate_blocker_matrix.csv",
    ARTIFACT_DIR / "native_ios_evidence_plan.csv",
    ARTIFACT_DIR / "native_ios_build_evidence_plan.csv",
    ARTIFACT_DIR / "native_ios_screenshot_evidence_plan.csv",
    ARTIFACT_DIR / "repo_census_summary.csv",
    REPORT_DIR / "gpt_loop_ledger.csv",
    REPORT_DIR / "source_authority_gate_10_loop_report.md",
    REPORT_DIR / "artifact_manifest.csv",
    REPORT_DIR / "task_3845_decision.csv",
    *[REPORT_DIR / f"gpt_loop_{loop_id:02d}.md" for loop_id in range(1, 11)],
]

REQUIRED_LOOP_COLUMNS = {
    "loop_id",
    "user_goal",
    "task_candidate",
    "expert_role",
    "gpt_mode",
    "prompt_artifact",
    "gpt_response_artifact",
    "codex_action",
    "validation_result",
    "review_prompt_artifact",
    "review_response_artifact",
    "status",
    "stop_reason",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED_ARTIFACTS:
        if not path.exists():
            failures.append(f"missing artifact: {path}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    state = json.loads((ARTIFACT_DIR / "source_authority_gate_state.json").read_text(encoding="utf-8"))
    if state.get("strategy") != "NOT_ACCEPTED":
        failures.append("strategy state changed")
    if state.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        failures.append("deployment state changed")
    if state.get("real_capital") != "FORBIDDEN":
        failures.append("real capital state changed")
    for field in ["broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted", "source_acquisition_run", "scheduler_run", "db_mutation"]:
        if state.get(field) is not False:
            failures.append(f"{field} must be false")
    if state.get("overall_status") != "READ_ONLY_AUDIT_COMPLETE_WITH_BLOCKERS":
        failures.append("unexpected overall status")

    loop_rows = read_csv(REPORT_DIR / "gpt_loop_ledger.csv")
    if len(loop_rows) != 10:
        failures.append("loop ledger must have exactly 10 rows")
    if loop_rows and not REQUIRED_LOOP_COLUMNS.issubset(loop_rows[0].keys()):
        failures.append("loop ledger missing required autonomous loop columns")
    if {row["status"] for row in loop_rows} != {"completed"}:
        failures.append("all loop rows must be completed")
    for row in loop_rows:
        for artifact_column in ["prompt_artifact", "gpt_response_artifact", "review_prompt_artifact", "review_response_artifact"]:
            artifact = Path(row.get(artifact_column, ""))
            if not artifact.exists():
                failures.append(f"loop {row.get('loop_id')} missing {artifact_column}: {artifact}")

    for loop_id in range(1, 11):
        loop_text = (REPORT_DIR / f"gpt_loop_{loop_id:02d}.md").read_text(encoding="utf-8")
        for phrase in ["Chrome GPT Prompt Sent", "Chrome GPT Output Summary", "GPT Review Result", "PASS"]:
            if phrase not in loop_text:
                failures.append(f"gpt_loop_{loop_id:02d}.md missing phrase: {phrase}")

    source_rows = read_csv(ARTIFACT_DIR / "source_inventory.csv")
    if not source_rows:
        failures.append("source inventory empty")
    if not any(row.get("authority_status") == "BLOCKED" for row in source_rows):
        failures.append("source inventory must preserve blocker rows")

    freshness_rows = read_csv(ARTIFACT_DIR / "freshness_certification_matrix.csv")
    if not any(row.get("certification_status") == "BLOCKED" for row in freshness_rows):
        failures.append("freshness matrix must preserve blocker rows")

    sec_rows = read_csv(ARTIFACT_DIR / "sec_hybrid_provider_chain.csv")
    providers = {row.get("provider") for row in sec_rows}
    for provider in {"sec_live_delta", "sec_rss_delta", "sec_bulk_baseline", "sec_submissions_cache"}:
        if provider not in providers:
            failures.append(f"missing SEC provider row: {provider}")
    if any(row.get("strict_gate_claimed") != "0" for row in sec_rows):
        failures.append("SEC strict gate must not be claimed")

    kill_rows = read_csv(ARTIFACT_DIR / "kill_switch_audit.csv")
    if not kill_rows or kill_rows[0].get("clearance_status") != "BLOCKED":
        failures.append("kill switch audit must remain blocked")

    paper_rows = read_csv(ARTIFACT_DIR / "paper_gate_blocker_matrix.csv")
    if not any(row.get("status") == "BLOCKED" for row in paper_rows):
        failures.append("paper gate blockers must remain blocked")

    native_rows = read_csv(ARTIFACT_DIR / "native_ios_evidence_plan.csv")
    if not all(row.get("native_evidence_status") == "BLOCKED_UNTIL_MAC_OR_OPERATOR" for row in native_rows):
        failures.append("native evidence must remain blocked until Mac/operator")
    build_rows = read_csv(ARTIFACT_DIR / "native_ios_build_evidence_plan.csv")
    screenshot_rows = read_csv(ARTIFACT_DIR / "native_ios_screenshot_evidence_plan.csv")
    if not build_rows or {row.get("evidence_type") for row in build_rows} - {"dev_build", "ios_evidence"}:
        failures.append("native build evidence plan must contain only build evidence rows")
    if not screenshot_rows or {row.get("evidence_type") for row in screenshot_rows} - {"maestro", "visual_regression"}:
        failures.append("native screenshot evidence plan must contain only screenshot/visual QA rows")

    report = (REPORT_DIR / "source_authority_gate_10_loop_report.md").read_text(encoding="utf-8")
    for phrase in [
        "read-only evidence artifacts",
        "does not run source acquisition",
        "Broker truth remains unproven",
        "Paper/live permission is not granted",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
    ]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/source_authority_gate_10_loop_audit.py").read_text(encoding="utf-8").lower()
    for forbidden in ["insert into", "update ", "delete from", "submit_order", "cancel_order", "replace_order", "broker.submit"]:
        if forbidden in script_text:
            failures.append(f"audit script contains forbidden mutation token: {forbidden}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Source authority gate 10-loop validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
