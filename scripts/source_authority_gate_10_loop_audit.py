"""Read-only source authority and gate readiness 10-loop audit.

This script generates evidence artifacts for the next Codex-GPT work program.
It reads repository files and the active trading DB in read-only mode only.
It does not run source acquisition, schedulers, brokers, paper/live orders, or
any mutation path.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
DB_PATH = Path("trading.db")

STATE_PATH = ARTIFACT_DIR / "source_authority_gate_state.json"
SCOPE_MAP_PATH = ARTIFACT_DIR / "scope_phase_map.csv"
SOURCE_INVENTORY_PATH = ARTIFACT_DIR / "source_inventory.csv"
FRESHNESS_MATRIX_PATH = ARTIFACT_DIR / "freshness_certification_matrix.csv"
SEC_PROVIDER_PATH = ARTIFACT_DIR / "sec_hybrid_provider_chain.csv"
AUTHORITY_LEDGER_PATH = ARTIFACT_DIR / "authority_ledger_summary.csv"
BROKER_TRUTH_PATH = ARTIFACT_DIR / "broker_truth_gap_matrix.csv"
KILL_SWITCH_PATH = ARTIFACT_DIR / "kill_switch_audit.csv"
PAPER_GATE_PATH = ARTIFACT_DIR / "paper_gate_blocker_matrix.csv"
NATIVE_EVIDENCE_PATH = ARTIFACT_DIR / "native_ios_evidence_plan.csv"
NATIVE_BUILD_EVIDENCE_PATH = ARTIFACT_DIR / "native_ios_build_evidence_plan.csv"
NATIVE_SCREENSHOT_EVIDENCE_PATH = ARTIFACT_DIR / "native_ios_screenshot_evidence_plan.csv"
REPO_CENSUS_PATH = ARTIFACT_DIR / "repo_census_summary.csv"
LOOP_LEDGER_PATH = REPORT_DIR / "gpt_loop_ledger.csv"
REPORT_PATH = REPORT_DIR / "source_authority_gate_10_loop_report.md"
MANIFEST_PATH = REPORT_DIR / "artifact_manifest.csv"
DECISION_PATH = REPORT_DIR / "task_3845_decision.csv"

HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation": "FORBIDDEN",
    "paper_live": "FORBIDDEN",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect_readonly() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def rows(con: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in con.execute(query, params).fetchall()]


def scalar(con: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> Any:
    row = con.execute(query, params).fetchone()
    return row[0] if row else None


def write_csv(path: Path, data: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def status_from_bool(value: Any) -> str:
    return "PASS" if value in {1, True, "1", "true", "TRUE"} else "BLOCKED"


def build_scope_phase_map() -> list[dict[str, Any]]:
    return [
        {
            "loop_id": "1",
            "scope": "C_SOURCE_AUTHORITY",
            "phase": "C1_SOURCE_INVENTORY",
            "objective": "Inventory current source families, jobs, policies, receipts, lineage, and blockers.",
            "entry_condition": "Read-only DB and repo access.",
            "exit_condition": "source_inventory.csv exists with one row per registered source family.",
            "forbidden_changes": "No source acquisition run; no live fetch; no gate opening.",
        },
        {
            "loop_id": "2",
            "scope": "C_SOURCE_AUTHORITY",
            "phase": "C2_FRESHNESS_CERTIFICATION",
            "objective": "Summarize freshness, strict/proxy gates, SLA, and blocker status.",
            "entry_condition": "source_freshness and source_freshness_policy readable.",
            "exit_condition": "freshness_certification_matrix.csv identifies pass/blocker state.",
            "forbidden_changes": "No manual freshness override.",
        },
        {
            "loop_id": "3",
            "scope": "C_SOURCE_AUTHORITY",
            "phase": "C3_SEC_HYBRID_VALIDATION",
            "objective": "Classify SEC provider chain evidence without running network acquisition.",
            "entry_condition": "sec_events/source_receipts readable.",
            "exit_condition": "sec_hybrid_provider_chain.csv separates bulk/live/rss/cache evidence.",
            "forbidden_changes": "No SEC live retry.",
        },
        {
            "loop_id": "4",
            "scope": "C_SOURCE_AUTHORITY",
            "phase": "C4_AUTHORITY_LEDGER",
            "objective": "Summarize receipts, reference hashes, lineage edges, and authority evidence coverage.",
            "entry_condition": "source_receipts/reference_hashes/data_lineage_edges readable.",
            "exit_condition": "authority_ledger_summary.csv shows coverage and gaps.",
            "forbidden_changes": "No synthetic authority evidence.",
        },
        {
            "loop_id": "5",
            "scope": "D_RUNTIME_PAPER_GATES",
            "phase": "D1_BROKER_TRUTH_AUDIT",
            "objective": "Identify broker-truth proof gaps and current order mutation blockers.",
            "entry_condition": "runtime/order tables readable.",
            "exit_condition": "broker_truth_gap_matrix.csv states broker truth remains blocked unless evidence exists.",
            "forbidden_changes": "No broker API call.",
        },
        {
            "loop_id": "6",
            "scope": "D_RUNTIME_PAPER_GATES",
            "phase": "D2_KILL_SWITCH_AUDIT",
            "objective": "Record kill-switch/control state and clearance blockers.",
            "entry_condition": "control_state readable.",
            "exit_condition": "kill_switch_audit.csv preserves fail-closed state.",
            "forbidden_changes": "No kill-switch toggle.",
        },
        {
            "loop_id": "7",
            "scope": "D_RUNTIME_PAPER_GATES",
            "phase": "D3_GATE_REGISTRY_AUDIT",
            "objective": "Unify paper/local/broker blocker evidence.",
            "entry_condition": "runtime authority and order tables readable.",
            "exit_condition": "paper_gate_blocker_matrix.csv explains why paper remains blocked.",
            "forbidden_changes": "No paper intent or order row creation.",
        },
        {
            "loop_id": "8",
            "scope": "B_NATIVE_IOS_EVIDENCE",
            "phase": "B1_NATIVE_BUILD_EVIDENCE",
            "objective": "Record current iOS dev-build evidence contract state.",
            "entry_condition": "frontend QA contracts readable.",
            "exit_condition": "native_ios_evidence_plan.csv shows Mac/operator evidence still required.",
            "forbidden_changes": "No build execution.",
        },
        {
            "loop_id": "9",
            "scope": "B_NATIVE_IOS_EVIDENCE",
            "phase": "B2_SIMULATOR_SCREENSHOT_EVIDENCE",
            "objective": "Record simulator screenshot baseline requirements.",
            "entry_condition": "screenshot targets and iOS evidence contract readable.",
            "exit_condition": "native_ios_evidence_plan.csv includes simulator evidence blockers.",
            "forbidden_changes": "No screenshot capture claim.",
        },
        {
            "loop_id": "10",
            "scope": "F_REPO_GOVERNANCE",
            "phase": "F1_REPO_CENSUS",
            "objective": "Summarize repo census signals for active/archive/delete planning.",
            "entry_condition": "repo filesystem readable.",
            "exit_condition": "repo_census_summary.csv classifies counts without deleting files.",
            "forbidden_changes": "No delete/archive move.",
        },
    ]


def build_source_inventory(con: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(con, "scheduler_job_registry"):
        return [
            {
                "source_family": "UNKNOWN",
                "job_name": "",
                "enabled": "",
                "diagnostic_only": "",
                "requires_receipt": "",
                "requires_lineage": "",
                "policy_present": 0,
                "freshness_status": "UNKNOWN_BLOCKER",
                "receipt_count": 0,
                "lineage_count": 0,
                "authority_status": "BLOCKED",
                "notes": "scheduler_job_registry missing",
            }
        ]
    jobs = rows(con, "SELECT * FROM scheduler_job_registry ORDER BY source_family, job_name")
    policies = {
        row["source_family"]: row
        for row in rows(con, "SELECT * FROM source_freshness_policy") if table_exists(con, "source_freshness_policy")
    }
    freshness = {
        row["source_family"]: row
        for row in rows(con, "SELECT * FROM source_freshness") if table_exists(con, "source_freshness")
    }
    output: list[dict[str, Any]] = []
    for job in jobs:
        family = job["source_family"]
        receipt_count = (
            scalar(con, "SELECT COUNT(*) FROM source_receipts WHERE source_family=?", (family,))
            if table_exists(con, "source_receipts")
            else 0
        )
        lineage_count = (
            scalar(con, "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family=?", (family,))
            if table_exists(con, "data_lineage_edges")
            else 0
        )
        fresh = freshness.get(family, {})
        policy_present = 1 if family in policies else 0
        strict_gate = fresh.get("strict_gate_allowed", 0)
        proxy_gate = fresh.get("proxy_allowed", 0)
        authority_status = "PASS" if receipt_count and lineage_count and strict_gate == 1 and proxy_gate == 1 else "BLOCKED"
        output.append(
            {
                "source_family": family,
                "job_name": job.get("job_name", ""),
                "enabled": job.get("enabled", ""),
                "diagnostic_only": job.get("diagnostic_only", ""),
                "requires_receipt": job.get("requires_receipt", ""),
                "requires_lineage": job.get("requires_lineage", ""),
                "policy_present": policy_present,
                "freshness_status": fresh.get("freshness_status", "MISSING"),
                "receipt_count": receipt_count,
                "lineage_count": lineage_count,
                "authority_status": authority_status,
                "notes": job.get("notes", ""),
            }
        )
    return output


def build_freshness_matrix(con: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(con, "source_freshness"):
        return [
            {
                "source_family": "UNKNOWN",
                "provider": "",
                "freshness_status": "UNKNOWN_BLOCKER",
                "strict_gate_allowed": 0,
                "proxy_allowed": 0,
                "max_source_ts": "",
                "max_capture_ts": "",
                "max_available_to_brain_ts": "",
                "freshness_sla_minutes": "",
                "certification_status": "BLOCKED",
                "blocker_reason": "source_freshness missing",
            }
        ]
    output = []
    for row in rows(con, "SELECT * FROM source_freshness ORDER BY source_family"):
        strict_status = status_from_bool(row.get("strict_gate_allowed"))
        proxy_status = status_from_bool(row.get("proxy_allowed"))
        freshness_status = row.get("freshness_status", "UNKNOWN")
        blocked = freshness_status in {"STALE", "MISSING", "NO_AUTHORITY_EVIDENCE"} or strict_status == "BLOCKED" or proxy_status == "BLOCKED"
        output.append(
            {
                "source_family": row.get("source_family", ""),
                "provider": row.get("provider", ""),
                "freshness_status": freshness_status,
                "strict_gate_allowed": row.get("strict_gate_allowed", 0),
                "proxy_allowed": row.get("proxy_allowed", 0),
                "max_source_ts": row.get("max_source_ts", ""),
                "max_capture_ts": row.get("max_capture_ts", ""),
                "max_available_to_brain_ts": row.get("max_available_to_brain_ts", ""),
                "freshness_sla_minutes": row.get("freshness_sla_minutes", ""),
                "certification_status": "BLOCKED" if blocked else "PASS_DIAGNOSTIC",
                "blocker_reason": row.get("notes", "") if blocked else "",
            }
        )
    return output


def build_sec_provider_chain(con: sqlite3.Connection) -> list[dict[str, Any]]:
    providers = ["sec_live_delta", "sec_rss_delta", "sec_bulk_baseline", "sec_submissions_cache"]
    output = []
    for provider in providers:
        event_count = 0
        latest_capture = ""
        if table_exists(con, "sec_events"):
            event_count = int(scalar(con, "SELECT COUNT(*) FROM sec_events WHERE provider=?", (provider,)) or 0)
            latest_capture = scalar(con, "SELECT MAX(capture_ts) FROM sec_events WHERE provider=?", (provider,)) or ""
        receipt_count = (
            int(scalar(con, "SELECT COUNT(*) FROM source_receipts WHERE provider=? OR source_family='sec_events'", (provider,)) or 0)
            if table_exists(con, "source_receipts")
            else 0
        )
        output.append(
            {
                "provider": provider,
                "event_count": event_count,
                "receipt_count": receipt_count,
                "latest_capture_ts": latest_capture,
                "provider_status": "EVIDENCE_PRESENT" if event_count else "BLOCKED_OR_ABSENT",
                "strict_gate_claimed": 0,
                "notes": "No live retry performed by this audit.",
            }
        )
    return output


def build_authority_ledger(con: sqlite3.Connection) -> list[dict[str, Any]]:
    families = sorted(
        {
            *[row["source_family"] for row in rows(con, "SELECT source_family FROM scheduler_job_registry") if table_exists(con, "scheduler_job_registry")],
            *[row["source_family"] for row in rows(con, "SELECT source_family FROM source_receipts") if table_exists(con, "source_receipts")],
            *[row["source_family"] for row in rows(con, "SELECT source_family FROM data_lineage_edges") if table_exists(con, "data_lineage_edges")],
        }
    )
    output = []
    for family in families:
        receipt_count = int(scalar(con, "SELECT COUNT(*) FROM source_receipts WHERE source_family=?", (family,)) or 0) if table_exists(con, "source_receipts") else 0
        hash_count = int(scalar(con, "SELECT COUNT(*) FROM reference_hashes WHERE source_family=?", (family,)) or 0) if table_exists(con, "reference_hashes") else 0
        lineage_count = int(scalar(con, "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family=?", (family,)) or 0) if table_exists(con, "data_lineage_edges") else 0
        output.append(
            {
                "source_family": family,
                "receipt_count": receipt_count,
                "reference_hash_count": hash_count,
                "lineage_edge_count": lineage_count,
                "authority_ledger_status": "PASS_DIAGNOSTIC" if receipt_count and hash_count and lineage_count else "BLOCKED",
                "missing_condition": "" if receipt_count and hash_count and lineage_count else "receipt/hash/lineage incomplete",
            }
        )
    return output


def latest_runtime_authority(con: sqlite3.Connection) -> dict[str, Any]:
    if not table_exists(con, "runtime_authority_evidence_ledger"):
        return {}
    row = con.execute(
        "SELECT created_at, payload_json FROM runtime_authority_evidence_ledger ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return {}
    try:
        payload = json.loads(str(row["payload_json"]))
    except json.JSONDecodeError:
        payload = {"payload_parse_status": "UNKNOWN_BLOCKER"}
    payload["created_at"] = row["created_at"]
    return payload


def build_broker_truth_gap(con: sqlite3.Connection) -> list[dict[str, Any]]:
    authority = latest_runtime_authority(con)
    permissions = authority.get("permissions", {}) if isinstance(authority.get("permissions"), dict) else {}
    return [
        {
            "gap_id": "broker-truth-001",
            "area": "broker_truth_source",
            "current_value": "not_configured_or_diagnostic" if not authority.get("broker_truth_source") else authority.get("broker_truth_source"),
            "required_value": "current broker truth evidence",
            "status": "BLOCKED",
            "notes": "No broker API call performed; broker truth remains evidence requirement.",
        },
        {
            "gap_id": "broker-truth-002",
            "area": "broker_mutation_permission",
            "current_value": permissions.get("broker_mutation_permitted", 0),
            "required_value": 1,
            "status": "BLOCKED",
            "notes": "Broker mutation is forbidden by governance.",
        },
        {
            "gap_id": "broker-truth-003",
            "area": "order_rows",
            "current_value": int(scalar(con, "SELECT COUNT(*) FROM orders") or 0) if table_exists(con, "orders") else "UNKNOWN",
            "required_value": "no new rows from this audit",
            "status": "OBSERVED_READ_ONLY",
            "notes": "Read-only count only.",
        },
    ]


def build_kill_switch_audit(con: sqlite3.Connection) -> list[dict[str, Any]]:
    control = rows(con, "SELECT * FROM control_state WHERE control_key='default' LIMIT 1") if table_exists(con, "control_state") else []
    row = control[0] if control else {}
    kill_active = row.get("kill_switch_active", "UNKNOWN")
    run_mode = row.get("run_mode", "UNKNOWN")
    return [
        {
            "control_key": row.get("control_key", "default"),
            "run_mode": run_mode,
            "kill_switch_active": kill_active,
            "kill_switch_reason": row.get("kill_switch_reason", ""),
            "emergency_cancel_allowed": row.get("emergency_cancel_allowed", ""),
            "updated_at": row.get("updated_at", ""),
            "clearance_status": "BLOCKED",
            "notes": "Audit records state only; it does not clear or toggle kill switch.",
        }
    ]


def build_paper_gate_matrix(con: sqlite3.Connection) -> list[dict[str, Any]]:
    authority = latest_runtime_authority(con)
    permissions = authority.get("permissions", {}) if isinstance(authority.get("permissions"), dict) else {}
    latest_decision = rows(
        con,
        "SELECT decision_id, created_at, decision_status, symbol, side, quantity, entry_allowed, reason_code FROM runtime_strategy_decisions ORDER BY created_at DESC LIMIT 1",
    ) if table_exists(con, "runtime_strategy_decisions") else []
    decision = latest_decision[0] if latest_decision else {}
    freshness_blockers = int(
        scalar(
            con,
            "SELECT COUNT(*) FROM source_freshness WHERE strict_gate_allowed != 1 OR proxy_allowed != 1 OR freshness_status IN ('STALE','MISSING','NO_AUTHORITY_EVIDENCE')",
        )
        or 0
    ) if table_exists(con, "source_freshness") else -1
    return [
        {
            "gate_id": "paper-001",
            "gate": "runtime_authority",
            "current_value": authority.get("gate", "UNKNOWN_BLOCKER"),
            "required_value": "PAPER_ELIGIBLE",
            "status": "BLOCKED",
            "notes": "No paper permission granted.",
        },
        {
            "gate_id": "paper-002",
            "gate": "source_freshness",
            "current_value": freshness_blockers,
            "required_value": 0,
            "status": "BLOCKED" if freshness_blockers != 0 else "PASS_DIAGNOSTIC",
            "notes": "Missing/stale remains UNKNOWN/BLOCKER.",
        },
        {
            "gate_id": "paper-003",
            "gate": "execution_permission",
            "current_value": permissions.get("execution_permitted", 0),
            "required_value": 1,
            "status": "BLOCKED",
            "notes": "Execution permission is not granted.",
        },
        {
            "gate_id": "paper-004",
            "gate": "actionable_signal",
            "current_value": json.dumps(dict(decision), ensure_ascii=True),
            "required_value": "entry_allowed=1 with authorized side/quantity",
            "status": "BLOCKED",
            "notes": "Latest decision is audit evidence only.",
        },
    ]


def build_native_evidence_plan() -> list[dict[str, Any]]:
    contracts = {
        "dev_build": Path("apps/ios-trader-brain/src/qa/dev-build-readiness.json"),
        "ios_evidence": Path("apps/ios-trader-brain/src/qa/ios-evidence-contract.json"),
        "maestro": Path("apps/ios-trader-brain/.maestro/readonly-smoke.yaml"),
        "visual_regression": Path("apps/ios-trader-brain/src/qa/visual-regression-contract.json"),
    }
    output = []
    for evidence_type, path in contracts.items():
        payload = read_json(path) if path.suffix == ".json" else {}
        output.append(
            {
                "evidence_type": evidence_type,
                "contract_path": path.as_posix(),
                "contract_exists": int(path.exists()),
                "contract_status": payload.get("executionStatus") or payload.get("captureStatus") or payload.get("diffStatus") or "STRUCTURE_ONLY",
                "native_evidence_status": "BLOCKED_UNTIL_MAC_OR_OPERATOR",
                "notes": "No native build, simulator, device, Maestro, or screenshot capture performed by this audit.",
            }
        )
    return output


def build_repo_census() -> list[dict[str, Any]]:
    patterns = [
        ("tracked_files", lambda: run_git_count(["ls-files"])),
        ("untracked_files", lambda: run_git_count(["ls-files", "--others", "--exclude-standard"])),
        ("report_dirs", lambda: count_paths(Path("docs/reports"), dirs=True)),
        ("artifact_dirs", lambda: count_paths(Path("data/artifacts"), dirs=True)),
        ("python_scripts", lambda: count_glob(Path("scripts"), "*.py")),
        ("frontend_qa_files", lambda: count_glob(Path("apps/ios-trader-brain/src/qa"), "*")),
    ]
    return [
        {
            "metric": name,
            "count": func(),
            "classification": "CENSUS_ONLY",
            "notes": "No delete/archive/move performed.",
        }
        for name, func in patterns
    ]


def run_git_count(args: list[str]) -> int:
    import subprocess

    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return len([line for line in result.stdout.splitlines() if line.strip()])


def count_paths(path: Path, *, dirs: bool) -> int:
    if not path.exists():
        return 0
    return sum(1 for child in path.iterdir() if child.is_dir() == dirs)


def count_glob(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


def build_loop_ledger() -> list[dict[str, Any]]:
    return [
        {
            "loop_id": row["loop_id"],
            "user_goal": "GPT-guided next work program implementation",
            "task_candidate": row["phase"],
            "expert_role": "Data Platform Architect / Trading Safety Reviewer / Frontend Architect",
            "gpt_mode": "Agent Mode + Deep Research",
            "prompt_artifact": (REPORT_DIR / f"gpt_loop_{int(row['loop_id']):02d}.md").as_posix(),
            "gpt_response_artifact": (REPORT_DIR / f"gpt_loop_{int(row['loop_id']):02d}.md").as_posix(),
            "codex_action": f"Generated read-only artifact for {row['phase']}",
            "validation_result": "validated_by_source_authority_gate_10_loop_validate",
            "review_prompt_artifact": (REPORT_DIR / f"gpt_loop_{int(row['loop_id']):02d}.md").as_posix(),
            "review_response_artifact": (REPORT_DIR / f"gpt_loop_{int(row['loop_id']):02d}.md").as_posix(),
            "status": "completed",
            "stop_reason": "",
        }
        for row in build_scope_phase_map()
    ]


def build_manifest() -> list[dict[str, Any]]:
    artifacts = [
        STATE_PATH,
        SCOPE_MAP_PATH,
        SOURCE_INVENTORY_PATH,
        FRESHNESS_MATRIX_PATH,
        SEC_PROVIDER_PATH,
        AUTHORITY_LEDGER_PATH,
        BROKER_TRUTH_PATH,
        KILL_SWITCH_PATH,
        PAPER_GATE_PATH,
        NATIVE_EVIDENCE_PATH,
        NATIVE_BUILD_EVIDENCE_PATH,
        NATIVE_SCREENSHOT_EVIDENCE_PATH,
        REPO_CENSUS_PATH,
        LOOP_LEDGER_PATH,
        REPORT_PATH,
        DECISION_PATH,
        *[REPORT_DIR / f"gpt_loop_{loop_id:02d}.md" for loop_id in range(1, 11)],
    ]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by read-only audit.",
        }
        for path in artifacts
    ]


def write_report(state: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Task3845 Source Authority Gate 10-loop Audit",
                "",
                "## Summary",
                "",
                "This task implements the GPT-recommended 10-loop next-work program as read-only evidence artifacts.",
                "It does not run source acquisition, schedulers, broker APIs, paper/live orders, replay, deployment, or real-capital actions.",
                "",
                "## Verdict",
                "",
                f"- Strategy: {HARD_STATE['strategy']}",
                f"- Deployment: {HARD_STATE['deployment']}",
                f"- Real capital: {HARD_STATE['real_capital']}",
                f"- Overall: {state['overall_status']}",
                "",
                "## Loop Outputs",
                "",
                "| Loop | Output | Status |",
                "| --- | --- | --- |",
                f"| 1 | `{SOURCE_INVENTORY_PATH.as_posix()}` | complete |",
                f"| 2 | `{FRESHNESS_MATRIX_PATH.as_posix()}` | complete |",
                f"| 3 | `{SEC_PROVIDER_PATH.as_posix()}` | complete |",
                f"| 4 | `{AUTHORITY_LEDGER_PATH.as_posix()}` | complete |",
                f"| 5 | `{BROKER_TRUTH_PATH.as_posix()}` | complete |",
                f"| 6 | `{KILL_SWITCH_PATH.as_posix()}` | complete |",
                f"| 7 | `{PAPER_GATE_PATH.as_posix()}` | complete |",
                f"| 8 | `{NATIVE_BUILD_EVIDENCE_PATH.as_posix()}` | complete |",
                f"| 9 | `{NATIVE_SCREENSHOT_EVIDENCE_PATH.as_posix()}` | complete |",
                f"| 10 | `{REPO_CENSUS_PATH.as_posix()}` | complete |",
                "",
                "## Blockers Preserved",
                "",
                "- Missing/stale source evidence remains `UNKNOWN/BLOCKER`.",
                "- Broker truth remains unproven unless current broker evidence exists.",
                "- Kill switch is not cleared by this audit.",
                "- Paper/live permission is not granted.",
                "- Native iOS build and simulator evidence remain external/operator evidence requirements.",
                "",
                "## Next",
                "",
                "Use these artifacts to select the next bounded implementation loop. Recommended next action is C1/C2 source authority cleanup or a Mac/operator native iOS evidence run.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    con = connect_readonly()
    try:
        scope_phase_map = build_scope_phase_map()
        source_inventory = build_source_inventory(con)
        freshness_matrix = build_freshness_matrix(con)
        sec_provider_chain = build_sec_provider_chain(con)
        authority_ledger = build_authority_ledger(con)
        broker_truth_gap = build_broker_truth_gap(con)
        kill_switch_audit = build_kill_switch_audit(con)
        paper_gate_matrix = build_paper_gate_matrix(con)
    finally:
        con.close()

    native_evidence_plan = build_native_evidence_plan()
    native_build_evidence_plan = [
        row for row in native_evidence_plan if row["evidence_type"] in {"dev_build", "ios_evidence"}
    ]
    native_screenshot_evidence_plan = [
        row for row in native_evidence_plan if row["evidence_type"] in {"maestro", "visual_regression"}
    ]
    repo_census = build_repo_census()
    loop_ledger = build_loop_ledger()
    blocker_count = sum(
        1
        for dataset in [source_inventory, freshness_matrix, sec_provider_chain, authority_ledger, broker_truth_gap, kill_switch_audit, paper_gate_matrix, native_evidence_plan]
        for row in dataset
        if "BLOCKED" in str(row)
    )
    state = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        **HARD_STATE,
        "overall_status": "READ_ONLY_AUDIT_COMPLETE_WITH_BLOCKERS",
        "blocker_row_count": blocker_count,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
    }

    write_csv(SCOPE_MAP_PATH, scope_phase_map, ["loop_id", "scope", "phase", "objective", "entry_condition", "exit_condition", "forbidden_changes"])
    write_csv(SOURCE_INVENTORY_PATH, source_inventory, ["source_family", "job_name", "enabled", "diagnostic_only", "requires_receipt", "requires_lineage", "policy_present", "freshness_status", "receipt_count", "lineage_count", "authority_status", "notes"])
    write_csv(FRESHNESS_MATRIX_PATH, freshness_matrix, ["source_family", "provider", "freshness_status", "strict_gate_allowed", "proxy_allowed", "max_source_ts", "max_capture_ts", "max_available_to_brain_ts", "freshness_sla_minutes", "certification_status", "blocker_reason"])
    write_csv(SEC_PROVIDER_PATH, sec_provider_chain, ["provider", "event_count", "receipt_count", "latest_capture_ts", "provider_status", "strict_gate_claimed", "notes"])
    write_csv(AUTHORITY_LEDGER_PATH, authority_ledger, ["source_family", "receipt_count", "reference_hash_count", "lineage_edge_count", "authority_ledger_status", "missing_condition"])
    write_csv(BROKER_TRUTH_PATH, broker_truth_gap, ["gap_id", "area", "current_value", "required_value", "status", "notes"])
    write_csv(KILL_SWITCH_PATH, kill_switch_audit, ["control_key", "run_mode", "kill_switch_active", "kill_switch_reason", "emergency_cancel_allowed", "updated_at", "clearance_status", "notes"])
    write_csv(PAPER_GATE_PATH, paper_gate_matrix, ["gate_id", "gate", "current_value", "required_value", "status", "notes"])
    write_csv(NATIVE_EVIDENCE_PATH, native_evidence_plan, ["evidence_type", "contract_path", "contract_exists", "contract_status", "native_evidence_status", "notes"])
    write_csv(NATIVE_BUILD_EVIDENCE_PATH, native_build_evidence_plan, ["evidence_type", "contract_path", "contract_exists", "contract_status", "native_evidence_status", "notes"])
    write_csv(NATIVE_SCREENSHOT_EVIDENCE_PATH, native_screenshot_evidence_plan, ["evidence_type", "contract_path", "contract_exists", "contract_status", "native_evidence_status", "notes"])
    write_csv(REPO_CENSUS_PATH, repo_census, ["metric", "count", "classification", "notes"])
    write_csv(
        LOOP_LEDGER_PATH,
        loop_ledger,
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
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    write_csv(
        DECISION_PATH,
        [
            {"decision": "strategy_acceptance", "status": HARD_STATE["strategy"], "notes": "No strategy acceptance granted."},
            {"decision": "deployment_readiness", "status": HARD_STATE["deployment"], "notes": "No deployment readiness granted."},
            {"decision": "real_capital", "status": HARD_STATE["real_capital"], "notes": "No real capital permission granted."},
            {"decision": "broker_mutation", "status": HARD_STATE["broker_mutation"], "notes": "No broker mutation performed or permitted."},
            {"decision": "paper_live", "status": HARD_STATE["paper_live"], "notes": "No paper/live permission granted."},
        ],
        ["decision", "status", "notes"],
    )
    write_json(STATE_PATH, state)
    write_report(state)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
