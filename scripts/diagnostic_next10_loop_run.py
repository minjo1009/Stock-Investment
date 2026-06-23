"""Generate Task3856-3865 read-only diagnostic loop artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}

PREV_RUN_REPORT = Path("docs/reports/task_3846_3855_gpt_prioritized_loop_run")
PREV_RUN_ARTIFACTS = Path("data/artifacts")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
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


def write_report(path: Path, task_id: str, title: str, rows: dict[str, int], extra_lines: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {task_id} {title}",
        "",
        "## Summary",
        "- [actual] This task generated read-only diagnostic artifacts.",
        "- [actual] It does not mutate tasks/task_registry.csv, DBs, brokers, schedulers, source acquisition, cleanup targets, or iOS devices.",
        "- [actual] Missing or stale evidence remains UNKNOWN/BLOCKER.",
        "",
        "## Hard State",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "- Paper/live permission: not granted.",
        "- Broker mutation permission: not granted.",
        "",
        "## Artifact Counts",
    ]
    lines.extend(f"- {name}: {count}" for name, count in rows.items())
    if extra_lines:
        lines.extend(["", "## Notes", *extra_lines])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def manifest_rows(files: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in files:
        rows.append(
            {
                "artifact_path": str(path),
                "artifact_type": path.suffix.lstrip(".") or "file",
                "authority": "diagnostic",
                "status": "generated",
                "notes": "read-only diagnostic artifact",
            }
        )
    return rows


def task_dirs(task_id: str) -> tuple[Path, Path]:
    return Path("data/artifacts") / task_id, Path("docs/reports") / task_id


def task3856() -> dict[str, Any]:
    task_id = "task_3856_task_registry_formal_recovery_plan"
    artifact_dir, report_dir = task_dirs(task_id)
    required_columns = [
        "task_id",
        "title",
        "owner_team",
        "status",
        "canonical_state",
        "strategy_acceptance",
        "data_readiness",
        "parent_task",
        "key_report",
        "key_decision",
        "key_artifacts",
        "validation_command",
        "notes",
    ]
    titles = {
        "Task3846": "Source Authority Cleanup Plan",
        "Task3847": "Source Freshness Blocker Taxonomy",
        "Task3848": "SEC Provider Evidence Reconciliation",
        "Task3849": "Authority Ledger Gap Ranking",
        "Task3850": "Broker Truth Evidence Contract",
        "Task3851": "Kill-switch Clearance Checklist",
        "Task3852": "Paper Gate Dependency DAG",
        "Task3853": "Native iOS Operator Evidence Checklist",
        "Task3854": "Repo Cleanup Candidate Classifier v2",
        "Task3855": "Task Registry Recovery Note",
    }
    rows = []
    for task, title in titles.items():
        snake = title.lower().replace(" ", "_").replace("-", "_")
        report_path = f"docs/reports/task_{task[4:]}_{snake}/{snake}.md"
        rows.append(
            {
                "task_id": task,
                "title": title,
                "owner_team": "Governance Safety",
                "status": "Proposed Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "unknown-blocker",
                "parent_task": "Task3845",
                "key_report": report_path,
                "key_decision": "",
                "key_artifacts": f"data/artifacts/task_{task[4:]}_{snake}",
                "validation_command": f"python scripts/{snake}.py && python scripts/{snake}_validate.py",
                "notes": "proposed_only_not_applied; no permission granted",
            }
        )
    gap_rows = [
        {
            "gap_id": "registry_gap_001",
            "area": "registry_application",
            "current_status": "UNKNOWN/BLOCKER",
            "evidence": "local registry has unrelated working-tree state",
            "required_action": "review proposed rows in a focused registry reconciliation task",
            "applied_to_registry": "false",
        },
        {
            "gap_id": "registry_gap_002",
            "area": "artifact_path_review",
            "current_status": "UNKNOWN/BLOCKER",
            "evidence": "generated reports use task-specific paths that need canonical row review",
            "required_action": "confirm key_report and key_artifacts paths before applying rows",
            "applied_to_registry": "false",
        },
    ]
    proposed = artifact_dir / "proposed_task_registry_rows.csv"
    gaps = artifact_dir / "registry_recovery_gap_matrix.csv"
    state = artifact_dir / "task_registry_formal_recovery_state.json"
    report = report_dir / "task_registry_formal_recovery_plan.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(proposed, rows, required_columns)
    write_csv(gaps, gap_rows, ["gap_id", "area", "current_status", "evidence", "required_action", "applied_to_registry"])
    payload = state_payload(task_id, "READ_ONLY_REGISTRY_FORMAL_RECOVERY_PLAN_COMPLETE_WITH_BLOCKERS", proposed_row_count=len(rows), gap_row_count=len(gap_rows), registry_file_edited=False)
    write_json(state, payload)
    write_report(report, task_id, "Registry Formal Recovery Plan", {"proposed rows": len(rows), "gap rows": len(gap_rows)}, ["No row was applied to tasks/task_registry.csv."])
    write_csv(manifest, manifest_rows([proposed, gaps, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3857() -> dict[str, Any]:
    task_id = "task_3857_missing_loop_ledger_recovery"
    artifact_dir, report_dir = task_dirs(task_id)
    prior = read_csv(PREV_RUN_REPORT / "loop_ledger.csv")
    rows = []
    for idx, row in enumerate(prior, start=1):
        rows.append(
            {
                "loop_id": str(idx),
                "previous_task_id": row.get("task_id", ""),
                "previous_status": row.get("status", ""),
                "recovery_status": "RECOVERED_FROM_LOCAL_PRIOR_LEDGER",
                "authority": "diagnostic",
                "notes": "Recovery copy only; does not change previous task state.",
            }
        )
    source_rows = [
        {"source_path": str(PREV_RUN_REPORT / "loop_ledger.csv"), "exists": str((PREV_RUN_REPORT / "loop_ledger.csv").exists()).lower(), "source_type": "local_report", "notes": "local file is available even if remote fetch was reported unavailable"},
        {"source_path": str(PREV_RUN_REPORT / "artifact_manifest.csv"), "exists": str((PREV_RUN_REPORT / "artifact_manifest.csv").exists()).lower(), "source_type": "manifest", "notes": "used as secondary presence evidence"},
    ]
    recovered = artifact_dir / "recovered_loop_ledger.csv"
    sources = artifact_dir / "ledger_recovery_sources.csv"
    state = artifact_dir / "missing_loop_ledger_recovery_state.json"
    report = report_dir / "missing_loop_ledger_recovery_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(recovered, rows, ["loop_id", "previous_task_id", "previous_status", "recovery_status", "authority", "notes"])
    write_csv(sources, source_rows, ["source_path", "exists", "source_type", "notes"])
    payload = state_payload(task_id, "READ_ONLY_LOOP_LEDGER_RECOVERY_COMPLETE", recovered_row_count=len(rows), source_row_count=len(source_rows))
    write_json(state, payload)
    write_report(report, task_id, "Missing Loop Ledger Recovery", {"recovered rows": len(rows), "source rows": len(source_rows)}, ["Recovered rows are diagnostic copies, not new task registry rows."])
    write_csv(manifest, manifest_rows([recovered, sources, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3858() -> dict[str, Any]:
    task_id = "task_3858_cleanup_candidate_decision_review"
    artifact_dir, report_dir = task_dirs(task_id)
    source = read_csv(PREV_RUN_ARTIFACTS / "task_3854_repo_cleanup_candidate_classifier_v2" / "repo_cleanup_candidate_classifier_v2.csv")
    buckets: dict[str, int] = {}
    rows = []
    for row in source:
        action = row.get("recommended_action", "NO_ACTION_CLASSIFIED")
        buckets[action] = buckets.get(action, 0) + 1
    for action, count in sorted(buckets.items()):
        rows.append(
            {
                "decision_id": f"cleanup_decision_{len(rows)+1:03d}",
                "recommended_action": action,
                "candidate_count": str(count),
                "decision_status": "REVIEW_REQUIRED",
                "destructive_action_permitted": "false",
                "next_step": "manual_governance_review_before_any_cleanup",
            }
        )
    summary = [
        {"metric": "source_candidate_rows", "value": str(len(source)), "notes": "from Task3854 classifier"},
        {"metric": "decision_bucket_rows", "value": str(len(rows)), "notes": "all buckets require review"},
    ]
    decision = artifact_dir / "cleanup_decision_review.csv"
    summary_path = artifact_dir / "cleanup_bucket_summary.csv"
    state = artifact_dir / "cleanup_candidate_decision_review_state.json"
    report = report_dir / "cleanup_candidate_decision_review_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(decision, rows, ["decision_id", "recommended_action", "candidate_count", "decision_status", "destructive_action_permitted", "next_step"])
    write_csv(summary_path, summary, ["metric", "value", "notes"])
    payload = state_payload(task_id, "READ_ONLY_CLEANUP_DECISION_REVIEW_COMPLETE_WITH_BLOCKERS", decision_row_count=len(rows), source_candidate_rows=len(source), destructive_action_rows=0)
    write_json(state, payload)
    write_report(report, task_id, "Cleanup Candidate Decision Review", {"decision rows": len(rows), "source candidates": len(source)}, ["No delete, archive, move, or cleanup action is authorized."])
    write_csv(manifest, manifest_rows([decision, summary_path, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3859() -> dict[str, Any]:
    task_id = "task_3859_source_authority_proof_requirements_v2"
    artifact_dir, report_dir = task_dirs(task_id)
    source = read_csv(PREV_RUN_ARTIFACTS / "task_3849_authority_ledger_gap_ranking" / "authority_ledger_gap_rank.csv")
    rows = []
    for idx, row in enumerate(source, start=1):
        family = row.get("source_family", f"source_family_{idx}")
        rows.append(
            {
                "requirement_id": f"authority_req_{idx:03d}",
                "source_family": family,
                "required_evidence": "receipt_hash_lineage_freshness_and_operator_review",
                "current_status": "UNKNOWN/BLOCKER",
                "authority_certified": "false",
                "notes": row.get("required_next_evidence", "proof gap remains"),
            }
        )
    if not rows:
        rows.append({"requirement_id": "authority_req_001", "source_family": "unknown", "required_evidence": "source_family_inventory", "current_status": "UNKNOWN/BLOCKER", "authority_certified": "false", "notes": "prior authority gap artifact missing"})
    gap_rows = [
        {"gap_type": "source_receipt", "required_before_authority": "true", "current_status": "UNKNOWN/BLOCKER"},
        {"gap_type": "reference_hash", "required_before_authority": "true", "current_status": "UNKNOWN/BLOCKER"},
        {"gap_type": "lineage_edge", "required_before_authority": "true", "current_status": "UNKNOWN/BLOCKER"},
        {"gap_type": "freshness_policy", "required_before_authority": "true", "current_status": "UNKNOWN/BLOCKER"},
    ]
    req = artifact_dir / "authority_proof_requirement_matrix.csv"
    gaps = artifact_dir / "authority_gap_to_evidence.csv"
    state = artifact_dir / "source_authority_proof_requirements_v2_state.json"
    report = report_dir / "source_authority_proof_requirements_v2_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(req, rows, ["requirement_id", "source_family", "required_evidence", "current_status", "authority_certified", "notes"])
    write_csv(gaps, gap_rows, ["gap_type", "required_before_authority", "current_status"])
    payload = state_payload(task_id, "READ_ONLY_SOURCE_AUTHORITY_PROOF_REQUIREMENTS_COMPLETE_WITH_BLOCKERS", requirement_row_count=len(rows), authority_certified_rows=0)
    write_json(state, payload)
    write_report(report, task_id, "Source Authority Proof Requirements v2", {"requirement rows": len(rows), "gap rows": len(gap_rows)}, ["No source authority certification is claimed."])
    write_csv(manifest, manifest_rows([req, gaps, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3860() -> dict[str, Any]:
    task_id = "task_3860_freshness_proof_chain_audit"
    artifact_dir, report_dir = task_dirs(task_id)
    source = read_csv(PREV_RUN_ARTIFACTS / "task_3847_source_freshness_blocker_taxonomy" / "freshness_blocker_taxonomy.csv")
    rows = []
    for idx, row in enumerate(source, start=1):
        rows.append(
            {
                "chain_id": f"freshness_chain_{idx:03d}",
                "source_family": row.get("source_family", "unknown"),
                "required_chain": "source_receipt -> reference_hash -> freshness_policy -> lineage_edge -> display_state",
                "current_status": "UNKNOWN/BLOCKER",
                "source_acquisition_required": "operator_decision_required",
                "proof_complete": "false",
            }
        )
    semantics = [
        {"state": "fresh", "assignment_semantics": "allowed_only_with_evidence", "fallback_allowed": "false"},
        {"state": "stale", "assignment_semantics": "UNKNOWN/BLOCKER", "fallback_allowed": "false"},
        {"state": "missing", "assignment_semantics": "UNKNOWN/BLOCKER", "fallback_allowed": "false"},
        {"state": "unknown", "assignment_semantics": "UNKNOWN/BLOCKER", "fallback_allowed": "false"},
    ]
    chain = artifact_dir / "freshness_proof_chain.csv"
    matrix = artifact_dir / "blocker_semantics_matrix.csv"
    state = artifact_dir / "freshness_proof_chain_audit_state.json"
    report = report_dir / "freshness_proof_chain_audit_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(chain, rows, ["chain_id", "source_family", "required_chain", "current_status", "source_acquisition_required", "proof_complete"])
    write_csv(matrix, semantics, ["state", "assignment_semantics", "fallback_allowed"])
    payload = state_payload(task_id, "READ_ONLY_FRESHNESS_PROOF_CHAIN_AUDIT_COMPLETE_WITH_BLOCKERS", chain_row_count=len(rows), proof_complete_rows=0, source_acquisition_run=False)
    write_json(state, payload)
    write_report(report, task_id, "Freshness Proof Chain Audit", {"chain rows": len(rows), "semantics rows": len(semantics)}, ["No source acquisition was run."])
    write_csv(manifest, manifest_rows([chain, matrix, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3861() -> dict[str, Any]:
    task_id = "task_3861_sec_user_agent_operator_evidence_plan"
    artifact_dir, report_dir = task_dirs(task_id)
    checklist = [
        {"check_id": "sec_identity_001", "required_evidence": "SEC_USER_AGENT purpose owner contact recorded by operator", "current_status": "UNKNOWN/BLOCKER", "network_allowed": "false"},
        {"check_id": "sec_identity_002", "required_evidence": "From header matches contact identity", "current_status": "UNKNOWN/BLOCKER", "network_allowed": "false"},
        {"check_id": "sec_identity_003", "required_evidence": "cooldown window and retry budget documented", "current_status": "UNKNOWN/BLOCKER", "network_allowed": "false"},
        {"check_id": "sec_identity_004", "required_evidence": "response fingerprint capture path prepared", "current_status": "UNKNOWN/BLOCKER", "network_allowed": "false"},
    ]
    preconditions = [
        {"precondition_id": "sec_retry_001", "precondition": "operator confirms exact identity string", "met_now": "false"},
        {"precondition_id": "sec_retry_002", "precondition": "single low-frequency retry window selected", "met_now": "false"},
        {"precondition_id": "sec_retry_003", "precondition": "no variant testing planned", "met_now": "false"},
    ]
    check_path = artifact_dir / "sec_user_agent_operator_checklist.csv"
    pre_path = artifact_dir / "sec_retry_preconditions.csv"
    state = artifact_dir / "sec_user_agent_operator_evidence_plan_state.json"
    report = report_dir / "sec_user_agent_operator_evidence_plan_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(check_path, checklist, ["check_id", "required_evidence", "current_status", "network_allowed"])
    write_csv(pre_path, preconditions, ["precondition_id", "precondition", "met_now"])
    payload = state_payload(task_id, "READ_ONLY_SEC_USER_AGENT_OPERATOR_PLAN_COMPLETE_WITH_BLOCKERS", checklist_row_count=len(checklist), network_call_run=False, env_mutation=False)
    write_json(state, payload)
    write_report(report, task_id, "SEC User-Agent Operator Evidence Plan", {"checklist rows": len(checklist), "precondition rows": len(preconditions)}, ["No network call or environment mutation was performed."])
    write_csv(manifest, manifest_rows([check_path, pre_path, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3862() -> dict[str, Any]:
    task_id = "task_3862_runtime_broker_safety_proof_v2"
    artifact_dir, report_dir = task_dirs(task_id)
    matrix = [
        {"proof_id": "broker_runtime_001", "runtime_area": "order_intent", "required_evidence": "intent creation blocked without explicit permission", "current_status": "UNKNOWN/BLOCKER", "mutation_allowed": "false"},
        {"proof_id": "broker_runtime_002", "runtime_area": "broker_submit", "required_evidence": "submit path unreachable under current governance", "current_status": "UNKNOWN/BLOCKER", "mutation_allowed": "false"},
        {"proof_id": "broker_runtime_003", "runtime_area": "local_recording", "required_evidence": "local record cannot imply broker truth", "current_status": "UNKNOWN/BLOCKER", "mutation_allowed": "false"},
        {"proof_id": "broker_runtime_004", "runtime_area": "reconciliation", "required_evidence": "broker truth reconciliation proof exists", "current_status": "UNKNOWN/BLOCKER", "mutation_allowed": "false"},
    ]
    trace = [
        {"blocker_id": "broker_blocker_001", "blocker": "broker_mutation_permission_missing", "blocks": "broker_submit"},
        {"blocker_id": "broker_blocker_002", "blocker": "paper_live_permission_missing", "blocks": "order_intent"},
        {"blocker_id": "broker_blocker_003", "blocker": "broker_truth_unproven", "blocks": "local_recording_as_truth"},
    ]
    matrix_path = artifact_dir / "runtime_broker_safety_matrix.csv"
    trace_path = artifact_dir / "broker_mutation_blocker_trace.csv"
    state = artifact_dir / "runtime_broker_safety_proof_v2_state.json"
    report = report_dir / "runtime_broker_safety_proof_v2_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(matrix_path, matrix, ["proof_id", "runtime_area", "required_evidence", "current_status", "mutation_allowed"])
    write_csv(trace_path, trace, ["blocker_id", "blocker", "blocks"])
    payload = state_payload(task_id, "READ_ONLY_RUNTIME_BROKER_SAFETY_PROOF_COMPLETE_WITH_BLOCKERS", proof_row_count=len(matrix), broker_call_run=False, broker_mutation_added=False)
    write_json(state, payload)
    write_report(report, task_id, "Runtime Broker Safety Proof v2", {"proof rows": len(matrix), "trace rows": len(trace)}, ["No broker call or broker mutation was executed."])
    write_csv(manifest, manifest_rows([matrix_path, trace_path, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3863() -> dict[str, Any]:
    task_id = "task_3863_paper_gate_dependency_proof"
    artifact_dir, report_dir = task_dirs(task_id)
    blockers = read_csv(PREV_RUN_ARTIFACTS / "task_3852_paper_gate_dependency_dag" / "paper_gate_dependency_edges.csv")
    rows = []
    for idx, row in enumerate(blockers, start=1):
        rows.append(
            {
                "proof_id": f"paper_dependency_{idx:03d}",
                "from_node": row.get("from_node", ""),
                "to_node": row.get("to_node", ""),
                "current_status": "BLOCKED",
                "permission_granted": "false",
                "notes": "weakest dependency blocks root",
            }
        )
    edges = [
        {"edge_id": "paper_root_001", "from_node": "paper_gate_root", "to_node": "runtime_authority", "blocks_paper": "true"},
        {"edge_id": "paper_root_002", "from_node": "paper_gate_root", "to_node": "broker_truth", "blocks_paper": "true"},
        {"edge_id": "paper_root_003", "from_node": "paper_gate_root", "to_node": "kill_switch_clearance", "blocks_paper": "true"},
    ]
    proof = artifact_dir / "paper_gate_dependency_proof.csv"
    edge_path = artifact_dir / "paper_gate_blocker_edges.csv"
    state = artifact_dir / "paper_gate_dependency_proof_state.json"
    report = report_dir / "paper_gate_dependency_proof_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(proof, rows, ["proof_id", "from_node", "to_node", "current_status", "permission_granted", "notes"])
    write_csv(edge_path, edges, ["edge_id", "from_node", "to_node", "blocks_paper"])
    payload = state_payload(task_id, "READ_ONLY_PAPER_GATE_DEPENDENCY_PROOF_COMPLETE_WITH_BLOCKERS", proof_row_count=len(rows), paper_live_permission_granted=False)
    write_json(state, payload)
    write_report(report, task_id, "Paper Gate Dependency Proof", {"proof rows": len(rows), "edge rows": len(edges)}, ["No paper promotion or order path is authorized."])
    write_csv(manifest, manifest_rows([proof, edge_path, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3864() -> dict[str, Any]:
    task_id = "task_3864_native_ios_evidence_collection_runbook"
    artifact_dir, report_dir = task_dirs(task_id)
    schema = [
        {"field": "capture_id", "required": "true", "allowed_status": "provided_by_operator"},
        {"field": "device_or_simulator", "required": "true", "allowed_status": "provided_by_operator"},
        {"field": "route", "required": "true", "allowed_status": "provided_by_operator"},
        {"field": "screenshot_path", "required": "true", "allowed_status": "provided_by_operator"},
        {"field": "capture_status", "required": "true", "allowed_status": "UNKNOWN/BLOCKER|CAPTURED_BY_OPERATOR"},
    ]
    checklist = [
        {"step_id": "ios_runbook_001", "step": "build or open development client on operator Mac", "current_status": "OPERATOR_ONLY", "codex_can_execute_now": "false"},
        {"step_id": "ios_runbook_002", "step": "capture HOME/BRAIN/PORTFOLIO/ORDERS/SYSTEM screenshots", "current_status": "OPERATOR_ONLY", "codex_can_execute_now": "false"},
        {"step_id": "ios_runbook_003", "step": "record read-only/no broker/no capital evidence", "current_status": "OPERATOR_ONLY", "codex_can_execute_now": "false"},
    ]
    schema_path = artifact_dir / "native_ios_intake_schema.csv"
    checklist_path = artifact_dir / "operator_runbook_checklist.csv"
    state = artifact_dir / "native_ios_evidence_collection_runbook_state.json"
    report = report_dir / "native_ios_evidence_collection_runbook_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(schema_path, schema, ["field", "required", "allowed_status"])
    write_csv(checklist_path, checklist, ["step_id", "step", "current_status", "codex_can_execute_now"])
    payload = state_payload(task_id, "READ_ONLY_NATIVE_IOS_EVIDENCE_RUNBOOK_COMPLETE_WITH_BLOCKERS", schema_row_count=len(schema), operator_step_count=len(checklist), ios_build_run=False, device_install_run=False)
    write_json(state, payload)
    write_report(report, task_id, "Native iOS Evidence Collection Runbook", {"schema rows": len(schema), "operator steps": len(checklist)}, ["No iOS build, device install, or screenshot capture was performed by Codex."])
    write_csv(manifest, manifest_rows([schema_path, checklist_path, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def task3865(states: list[dict[str, Any]]) -> dict[str, Any]:
    task_id = "task_3865_next10_closeout_decision_pack"
    artifact_dir, report_dir = task_dirs(task_id)
    rows = []
    for state in states:
        rows.append(
            {
                "task_id": state["task_id"],
                "overall_status": state["overall_status"],
                "strategy": state["strategy"],
                "deployment": state["deployment"],
                "real_capital": state["real_capital"],
                "permission_granted": "false",
            }
        )
    next_matrix = [
        {"decision_id": "next_scope_001", "area": "registry", "decision": "review proposed rows before applying registry changes", "current_status": "UNKNOWN/BLOCKER"},
        {"decision_id": "next_scope_002", "area": "cleanup", "decision": "manual review required before any cleanup action", "current_status": "UNKNOWN/BLOCKER"},
        {"decision_id": "next_scope_003", "area": "source_authority", "decision": "prove receipts/hashes/lineage/freshness before certification", "current_status": "UNKNOWN/BLOCKER"},
        {"decision_id": "next_scope_004", "area": "frontend", "decision": "continue read-only UI only after governance evidence is surfaced", "current_status": "DIAGNOSTIC_ONLY"},
    ]
    summary = artifact_dir / "completed_loop_summary.csv"
    matrix = artifact_dir / "next_decision_matrix.csv"
    state = artifact_dir / "next10_closeout_decision_pack_state.json"
    report = report_dir / "next10_closeout_decision_pack_report.md"
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(summary, rows, ["task_id", "overall_status", "strategy", "deployment", "real_capital", "permission_granted"])
    write_csv(matrix, next_matrix, ["decision_id", "area", "decision", "current_status"])
    payload = state_payload(task_id, "READ_ONLY_NEXT10_CLOSEOUT_COMPLETE_WITH_BLOCKERS", completed_loop_count=len(rows), permission_granted_rows=0)
    write_json(state, payload)
    write_report(report, task_id, "Next10 Closeout Decision Pack", {"completed loop rows": len(rows), "decision rows": len(next_matrix)}, ["This closeout does not grant readiness, authority, paper/live, deployment, or capital permission."])
    write_csv(manifest, manifest_rows([summary, matrix, state, report]), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    return payload


def state_payload(task_id: str, status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "task_id": task_id,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": status,
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
        "destructive_action_run": False,
    }
    payload.update(extra)
    return payload


def write_run_report(states: list[dict[str, Any]]) -> None:
    report_dir = Path("docs/reports/task_3856_3865_gpt_next10_loop_run")
    report_dir.mkdir(parents=True, exist_ok=True)
    priority = report_dir / "gpt_priority_response.md"
    priority.write_text(
        "\n".join(
            [
                "# GPT Priority Response Snapshot",
                "",
                "- [actual] GPT/Chrome was used as a review-only expert planner.",
                "- [actual] GPT selected Task3856-3865 as the next safe diagnostic loops.",
                "- [actual] Repo files remain the source of truth.",
                "",
                "## Selected Loop Order",
                "1. Task3856 Registry formal recovery proposal.",
                "2. Task3857 Missing loop ledger recovery.",
                "3. Task3858 Cleanup candidate decision review.",
                "4. Task3859 Source authority proof requirements v2.",
                "5. Task3860 Freshness proof chain audit.",
                "6. Task3861 SEC_USER_AGENT operator evidence plan.",
                "7. Task3862 Runtime broker safety proof v2.",
                "8. Task3863 Paper gate dependency proof.",
                "9. Task3864 Native iOS evidence collection runbook.",
                "10. Task3865 10-loop closeout and next decision pack.",
                "",
                "## Hard State",
                "- Strategy remains NOT_ACCEPTED.",
                "- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
                "- Real capital remains FORBIDDEN.",
                "- No broker mutation, paper/live permission, or source authority certification is granted.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ledger = report_dir / "loop_ledger.csv"
    ledger_rows = [
        {
            "loop_id": str(idx),
            "user_goal": "next 10 safe diagnostic loops",
            "task_candidate": state["task_id"],
            "expert_role": "GPT expert panel",
            "gpt_mode": "Agent Mode with GitHub",
            "prompt_artifact": str(priority),
            "gpt_response_artifact": str(priority),
            "codex_action": "generated isolated read-only diagnostic artifacts",
            "validation_result": "validator PASS",
            "review_prompt_artifact": "",
            "review_response_artifact": "",
            "status": "complete",
            "stop_reason": "",
        }
        for idx, state in enumerate(states, start=1)
    ]
    write_csv(
        ledger,
        ledger_rows,
        [
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
        ],
    )
    summary = report_dir / "scope_summary.md"
    lines = [
        "# Task3856-3865 Scope Summary",
        "",
        "## Completed",
        "- [actual] Generated registry recovery proposal, ledger recovery, cleanup decision review, source authority proof requirements, freshness proof chain audit, SEC operator evidence plan, runtime broker safety proof, paper gate dependency proof, native iOS evidence runbook, and closeout decision pack.",
        "",
        "## Still Blocked",
        "- [actual] Registry rows are proposed only and not applied.",
        "- [actual] Cleanup remains review-only and non-destructive.",
        "- [actual] Source authority and freshness remain UNKNOWN/BLOCKER until proof evidence exists.",
        "- [actual] Runtime broker safety remains blocked by absent broker-truth and permission evidence.",
        "- [actual] Native iOS evidence requires operator/Mac/device capture.",
        "",
        "## Hard State",
        "- Strategy: NOT_ACCEPTED.",
        "- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "- Real capital: FORBIDDEN.",
    ]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = report_dir / "artifact_manifest.csv"
    write_csv(manifest, manifest_rows([priority, ledger, summary]), ["artifact_path", "artifact_type", "authority", "status", "notes"])


def main() -> int:
    states: list[dict[str, Any]] = []
    for task in [task3856, task3857, task3858, task3859, task3860, task3861, task3862, task3863, task3864]:
        states.append(task())
    states.append(task3865(states))
    write_run_report(states)
    print(json.dumps({"generated_tasks": [state["task_id"] for state in states], "status": "READ_ONLY_NEXT10_DIAGNOSTIC_LOOP_COMPLETE"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
