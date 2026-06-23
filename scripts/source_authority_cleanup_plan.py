"""Build Task3846 read-only source authority cleanup planning artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3846_source_authority_cleanup_plan"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID
PREV_REPORT_DIR = Path("docs/reports") / PREV_TASK_ID
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

CLEANUP_MATRIX_PATH = ARTIFACT_DIR / "cleanup_candidate_matrix.csv"
GAP_RANK_PATH = ARTIFACT_DIR / "source_authority_gap_rank.csv"
NEXT_ACTIONS_PATH = ARTIFACT_DIR / "non_destructive_next_actions.csv"
STATE_PATH = ARTIFACT_DIR / "source_authority_cleanup_plan_state.json"
REPORT_PATH = REPORT_DIR / "source_authority_cleanup_plan_report.md"
MANIFEST_PATH = REPORT_DIR / "artifact_manifest.csv"
REGISTRY_NOTE_PATH = REPORT_DIR / "registry_recovery_note.md"

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


def is_blocked(value: str) -> bool:
    return "BLOCKED" in str(value).upper() or str(value).upper() in {"STALE", "MISSING", "UNKNOWN"}


def build_cleanup_candidates(
    source_rows: list[dict[str, str]],
    freshness_rows: list[dict[str, str]],
    authority_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    freshness_by_family = {row.get("source_family", ""): row for row in freshness_rows}
    authority_by_family = {row.get("source_family", ""): row for row in authority_rows}
    candidates: list[dict[str, Any]] = []
    candidate_number = 1
    for source in source_rows:
        family = source.get("source_family", "UNKNOWN")
        fresh = freshness_by_family.get(family, {})
        authority = authority_by_family.get(family, {})
        checks = [
            (
                "AUTHORITY_STATUS_BLOCKED",
                source.get("authority_status", ""),
                "Classify why authority remains blocked before any gate discussion.",
            ),
            (
                "FRESHNESS_STATUS_BLOCKED",
                fresh.get("freshness_status", source.get("freshness_status", "")),
                "Classify stale/missing/current evidence without converting it to permission.",
            ),
            (
                "STRICT_GATE_CLOSED",
                fresh.get("strict_gate_allowed", ""),
                "Keep strict gate closed until independent certification exists.",
            ),
            (
                "PROXY_GATE_CLOSED",
                fresh.get("proxy_allowed", ""),
                "Keep proxy gate closed until independent certification exists.",
            ),
            (
                "DIAGNOSTIC_LEDGER_ONLY",
                authority.get("authority_ledger_status", ""),
                "Treat diagnostic receipts, hashes, and lineage as evidence inputs only.",
            ),
        ]
        for issue_type, current_status, notes in checks:
            blocked = issue_type.endswith("CLOSED") and str(current_status) != "1"
            blocked = blocked or issue_type == "DIAGNOSTIC_LEDGER_ONLY"
            blocked = blocked or is_blocked(current_status)
            if not blocked:
                continue
            candidates.append(
                {
                    "candidate_id": f"cleanup-{candidate_number:03d}",
                    "source_family": family,
                    "issue_type": issue_type,
                    "evidence_file": evidence_file_for(issue_type),
                    "current_status": current_status,
                    "cleanup_action_type": "REPORT_ONLY_CLASSIFICATION",
                    "destructive_action_required": "false",
                    "implement_now_allowed": "true",
                    "blocker_reason": fresh.get("blocker_reason") or source.get("notes") or "authority cleanup classification required",
                    "notes": notes,
                }
            )
            candidate_number += 1
    return candidates


def evidence_file_for(issue_type: str) -> str:
    if issue_type in {"AUTHORITY_STATUS_BLOCKED"}:
        return (PREV_ARTIFACT_DIR / "source_inventory.csv").as_posix()
    if issue_type in {"FRESHNESS_STATUS_BLOCKED", "STRICT_GATE_CLOSED", "PROXY_GATE_CLOSED"}:
        return (PREV_ARTIFACT_DIR / "freshness_certification_matrix.csv").as_posix()
    return (PREV_ARTIFACT_DIR / "authority_ledger_summary.csv").as_posix()


def build_gap_rank(cleanup_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_order = {
        "AUTHORITY_STATUS_BLOCKED": 1,
        "STRICT_GATE_CLOSED": 2,
        "PROXY_GATE_CLOSED": 3,
        "FRESHNESS_STATUS_BLOCKED": 4,
        "DIAGNOSTIC_LEDGER_ONLY": 5,
    }
    sorted_rows = sorted(
        cleanup_rows,
        key=lambda row: (severity_order.get(str(row["issue_type"]), 99), str(row["source_family"])),
    )
    output = []
    for rank, row in enumerate(sorted_rows, 1):
        issue_type = str(row["issue_type"])
        severity = "P0_BLOCKER" if issue_type in {"AUTHORITY_STATUS_BLOCKED", "STRICT_GATE_CLOSED"} else "P1_BLOCKER"
        output.append(
            {
                "rank": rank,
                "source_family": row["source_family"],
                "gap_type": issue_type,
                "severity": severity,
                "evidence_basis": row["evidence_file"],
                "required_next_evidence": required_evidence_for(issue_type),
                "allowed_next_action": "Generate focused diagnostic evidence plan or validator only.",
                "forbidden_action": "No source acquisition, DB mutation, scheduler run, broker call, paper/live permission, or destructive cleanup.",
            }
        )
    return output


def required_evidence_for(issue_type: str) -> str:
    if issue_type == "AUTHORITY_STATUS_BLOCKED":
        return "Explicit authority acceptance criteria and proof chain for receipt/hash/lineage/freshness separation."
    if issue_type == "STRICT_GATE_CLOSED":
        return "Independent strict-gate certification evidence; no inference from diagnostic rows."
    if issue_type == "PROXY_GATE_CLOSED":
        return "Independent proxy-gate certification evidence; no inference from diagnostic rows."
    if issue_type == "FRESHNESS_STATUS_BLOCKED":
        return "Source-specific freshness remediation evidence that preserves stale/missing as blocker until proven."
    return "Clear distinction between diagnostic ledger evidence and authority certification."


def build_next_actions(gap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phases = [
        (
            "source_authority_taxonomy",
            "Create a source-family blocker taxonomy from Task3845 evidence.",
            "docs/reports/task_3847_source_freshness_blocker_taxonomy; data/artifacts/task_3847_source_freshness_blocker_taxonomy",
        ),
        (
            "freshness_blocker_matrix",
            "Split stale, strict-gate, proxy-gate, and authority blockers into separate validation rows.",
            "docs/reports/task_3847_source_freshness_blocker_taxonomy; data/artifacts/task_3847_source_freshness_blocker_taxonomy",
        ),
        (
            "sec_provider_reconciliation",
            "Compare SEC provider evidence without live SEC network calls.",
            "docs/reports/task_3848_sec_provider_evidence_reconciliation; data/artifacts/task_3848_sec_provider_evidence_reconciliation",
        ),
        (
            "authority_gap_ranking",
            "Rank receipt/hash/lineage/freshness gaps without synthetic certification.",
            "docs/reports/task_3849_authority_ledger_gap_ranking; data/artifacts/task_3849_authority_ledger_gap_ranking",
        ),
        (
            "broker_truth_contract",
            "Draft broker-truth evidence contract without broker connectivity.",
            "docs/reports/task_3850_broker_truth_evidence_contract; data/artifacts/task_3850_broker_truth_evidence_contract",
        ),
    ]
    output = []
    for idx, (phase, action, files) in enumerate(phases, 1):
        output.append(
            {
                "action_id": f"action-{idx:02d}",
                "phase": phase,
                "action": action,
                "allowed_files": files,
                "validation": "Task-specific validator plus git diff --check.",
                "expected_output": "Report, artifact manifest, CSV evidence, and no permission change.",
                "non_authority_notice": "Diagnostic planning only; not source authority certification.",
            }
        )
    if gap_rows:
        output.append(
            {
                "action_id": f"action-{len(output) + 1:02d}",
                "phase": "largest_gap_followup",
                "action": f"Start with {gap_rows[0]['source_family']} / {gap_rows[0]['gap_type']} if user asks for the next implementation loop.",
                "allowed_files": "New report/artifact/script only.",
                "validation": "Preserve UNKNOWN/BLOCKER and no mutation tokens.",
                "expected_output": "Focused proof requirements and validator.",
                "non_authority_notice": "UNKNOWN/BLOCKER follow-up only; cannot open source, paper, broker, deployment, or capital gates.",
            }
        )
    return output


def build_manifest() -> list[dict[str, str]]:
    paths = [
        CLEANUP_MATRIX_PATH,
        GAP_RANK_PATH,
        NEXT_ACTIONS_PATH,
        STATE_PATH,
        REPORT_PATH,
        MANIFEST_PATH,
        REGISTRY_NOTE_PATH,
    ]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by Task3846 read-only cleanup planning.",
        }
        for path in paths
    ]


def write_report(state: dict[str, Any], cleanup_rows: list[dict[str, Any]], gap_rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    top_rows = gap_rows[:10]
    lines = [
        "# Task3846 Source Authority Cleanup Plan",
        "",
        "## Summary",
        "",
        "This task converts Task3845 read-only evidence into a non-destructive source authority cleanup plan.",
        "It does not run source acquisition, schedulers, broker APIs, paper/live orders, replay, deployment, DB mutation, or cleanup actions.",
        "",
        "## Hard State",
        "",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "- Broker mutation: FORBIDDEN",
        "- Paper/live permission: FORBIDDEN",
        "",
        "## Outputs",
        "",
        f"- Cleanup candidate matrix: `{CLEANUP_MATRIX_PATH.as_posix()}`",
        f"- Source authority gap rank: `{GAP_RANK_PATH.as_posix()}`",
        f"- Non-destructive next actions: `{NEXT_ACTIONS_PATH.as_posix()}`",
        f"- Registry note: `{REGISTRY_NOTE_PATH.as_posix()}`",
        "",
        "## Top Gaps",
        "",
        "| Rank | Source Family | Gap Type | Severity |",
        "| --- | --- | --- | --- |",
    ]
    for row in top_rows:
        lines.append(f"| {row['rank']} | {row['source_family']} | {row['gap_type']} | {row['severity']} |")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Missing/stale data remains `UNKNOWN/BLOCKER`.",
            "- Diagnostic ledger rows are not source authority certification.",
            "- No destructive cleanup candidate is executable from this task.",
            "- No source gates, broker gates, paper/live gates, deployment gates, strategy acceptance, or real-capital gates are opened.",
            "",
            "## State",
            "",
            f"- Cleanup candidates: {state['cleanup_candidate_count']}",
            f"- Ranked gaps: {state['ranked_gap_count']}",
            f"- Destructive action rows: {state['destructive_action_rows']}",
            "",
            "## Next",
            "",
            "Use this plan to pick the next focused non-destructive cleanup loop. Recommended next step is a freshness blocker taxonomy or authority gap ranking validator.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_registry_note() -> None:
    REGISTRY_NOTE_PATH.write_text(
        "\n".join(
            [
                "# Task3846 Registry Recovery Note",
                "",
                "Task3846 is intentionally generated as isolated report/artifact/script work.",
                "The local task registry has unrelated dirty changes in this worktree, so this task does not require blind registry mutation.",
                "If a later closeout pass reconciles registry rows, use the report and artifact manifest paths from this directory.",
                "",
                "- Strategy remains NOT_ACCEPTED.",
                "- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
                "- Real capital remains FORBIDDEN.",
                "- No broker mutation, paper/live permission, source acquisition, scheduler run, DB mutation, or cleanup execution occurred.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    source_rows = read_csv(PREV_ARTIFACT_DIR / "source_inventory.csv")
    freshness_rows = read_csv(PREV_ARTIFACT_DIR / "freshness_certification_matrix.csv")
    authority_rows = read_csv(PREV_ARTIFACT_DIR / "authority_ledger_summary.csv")
    if not source_rows:
        raise SystemExit("Task3845 source inventory is missing or empty.")

    cleanup_rows = build_cleanup_candidates(source_rows, freshness_rows, authority_rows)
    gap_rows = build_gap_rank(cleanup_rows)
    next_actions = build_next_actions(gap_rows)
    destructive_rows = [row for row in cleanup_rows if row["destructive_action_required"] != "false"]
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_CLEANUP_PLAN_COMPLETE_WITH_BLOCKERS",
        "cleanup_candidate_count": len(cleanup_rows),
        "ranked_gap_count": len(gap_rows),
        "destructive_action_rows": len(destructive_rows),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }

    write_csv(
        CLEANUP_MATRIX_PATH,
        cleanup_rows,
        [
            "candidate_id",
            "source_family",
            "issue_type",
            "evidence_file",
            "current_status",
            "cleanup_action_type",
            "destructive_action_required",
            "implement_now_allowed",
            "blocker_reason",
            "notes",
        ],
    )
    write_csv(
        GAP_RANK_PATH,
        gap_rows,
        [
            "rank",
            "source_family",
            "gap_type",
            "severity",
            "evidence_basis",
            "required_next_evidence",
            "allowed_next_action",
            "forbidden_action",
        ],
    )
    write_csv(
        NEXT_ACTIONS_PATH,
        next_actions,
        [
            "action_id",
            "phase",
            "action",
            "allowed_files",
            "validation",
            "expected_output",
            "non_authority_notice",
        ],
    )
    write_json(STATE_PATH, state)
    write_report(state, cleanup_rows, gap_rows)
    write_registry_note()
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
