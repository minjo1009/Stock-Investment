"""Build Task3848 read-only SEC provider evidence reconciliation artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3848_sec_provider_evidence_reconciliation"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID

RECON_PATH = ARTIFACT_DIR / "sec_provider_reconciliation.csv"
BLOCKER_PATH = ARTIFACT_DIR / "sec_provider_blocker_matrix.csv"
STATE_PATH = ARTIFACT_DIR / "sec_provider_evidence_reconciliation_state.json"
REPORT_PATH = REPORT_DIR / "sec_provider_evidence_reconciliation_report.md"
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


def build_reconciliation(provider_rows: list[dict[str, str]], freshness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    sec_freshness = next((row for row in freshness_rows if row.get("source_family") == "sec_events"), {})
    output = []
    for row in provider_rows:
        event_count = int(row.get("event_count") or 0)
        evidence_present = event_count > 0
        output.append(
            {
                "provider": row.get("provider", ""),
                "event_count": event_count,
                "receipt_count": int(row.get("receipt_count") or 0),
                "latest_capture_ts": row.get("latest_capture_ts", ""),
                "provider_status": row.get("provider_status", "UNKNOWN_BLOCKER"),
                "evidence_present": str(evidence_present).lower(),
                "freshness_status": sec_freshness.get("freshness_status", "UNKNOWN"),
                "strict_gate_claimed": row.get("strict_gate_claimed", "0"),
                "strict_gate_allowed": sec_freshness.get("strict_gate_allowed", "0"),
                "proxy_allowed": sec_freshness.get("proxy_allowed", "0"),
                "authority_claim_allowed": "false",
                "network_call_performed": "false",
                "notes": "Provider evidence is diagnostic only; no live SEC request performed by Task3848.",
            }
        )
    return output


def build_blockers(recon_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in recon_rows:
        provider = row["provider"]
        checks = [
            ("NO_EVENTS", row["event_count"] == 0, "Provider has no event rows in Task3845 evidence."),
            ("STRICT_GATE_CLOSED", row["strict_gate_allowed"] != "1", "SEC strict gate remains closed."),
            ("PROXY_GATE_CLOSED", row["proxy_allowed"] != "1", "SEC proxy gate remains closed."),
            ("NO_AUTHORITY_CLAIM", row["authority_claim_allowed"] == "false", "Provider evidence is not authority certification."),
            ("NO_NETWORK_CALL", row["network_call_performed"] == "false", "This reconciliation did not call SEC live endpoints."),
        ]
        for blocker_type, active, reason in checks:
            output.append(
                {
                    "provider": provider,
                    "blocker_type": blocker_type,
                    "blocker_active": str(active).lower(),
                    "severity": "P0_BLOCKER" if blocker_type in {"STRICT_GATE_CLOSED", "NO_AUTHORITY_CLAIM"} else "P1_BLOCKER",
                    "reason": reason,
                    "allowed_next_action": "Write evidence requirements or validate cached artifacts only.",
                    "forbidden_action": "No SEC live retry, source acquisition, gate opening, paper/live permission, broker call, or authority claim.",
                }
            )
    return output


def build_manifest() -> list[dict[str, str]]:
    paths = [RECON_PATH, BLOCKER_PATH, STATE_PATH, REPORT_PATH, MANIFEST_PATH]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by Task3848 read-only SEC provider reconciliation.",
        }
        for path in paths
    ]


def write_report(state: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3848 SEC Provider Evidence Reconciliation",
        "",
        "## Summary",
        "",
        "This task reconciles Task3845 SEC provider evidence without SEC network calls.",
        "Bulk/cache evidence remains diagnostic only; live/RSS absence remains `UNKNOWN/BLOCKER`.",
        "",
        "## Hard State",
        "",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "- SEC strict/proxy gates remain closed.",
        "",
        "## Provider Rows",
        "",
        "| Provider | Events | Evidence Present | Strict Gate Claimed | Authority Claim Allowed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in recon_rows:
        lines.append(
            f"| {row['provider']} | {row['event_count']} | {row['evidence_present']} | {row['strict_gate_claimed']} | {row['authority_claim_allowed']} |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Reconciliation: `{RECON_PATH.as_posix()}`",
            f"- Blocker matrix: `{BLOCKER_PATH.as_posix()}`",
            "",
            "## Safety",
            "",
            "- No SEC live retry was performed.",
            "- No source acquisition, scheduler run, DB mutation, broker mutation, paper/live permission, deployment readiness, strategy acceptance, or real-capital permission is granted.",
            "- Provider evidence is not source authority certification.",
            "",
            "## State",
            "",
            f"- Provider rows: {state['provider_row_count']}",
            f"- Authority claim rows: {state['authority_claim_rows']}",
            f"- Network call rows: {state['network_call_rows']}",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    provider_rows = read_csv(PREV_ARTIFACT_DIR / "sec_hybrid_provider_chain.csv")
    freshness_rows = read_csv(PREV_ARTIFACT_DIR / "freshness_certification_matrix.csv")
    if not provider_rows:
        raise SystemExit("Task3845 SEC provider chain is missing or empty.")
    recon_rows = build_reconciliation(provider_rows, freshness_rows)
    blocker_rows = build_blockers(recon_rows)
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_SEC_PROVIDER_RECONCILIATION_COMPLETE_WITH_BLOCKERS",
        "provider_row_count": len(recon_rows),
        "blocker_row_count": len(blocker_rows),
        "authority_claim_rows": sum(1 for row in recon_rows if row["authority_claim_allowed"] != "false"),
        "network_call_rows": sum(1 for row in recon_rows if row["network_call_performed"] != "false"),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(
        RECON_PATH,
        recon_rows,
        [
            "provider",
            "event_count",
            "receipt_count",
            "latest_capture_ts",
            "provider_status",
            "evidence_present",
            "freshness_status",
            "strict_gate_claimed",
            "strict_gate_allowed",
            "proxy_allowed",
            "authority_claim_allowed",
            "network_call_performed",
            "notes",
        ],
    )
    write_csv(
        BLOCKER_PATH,
        blocker_rows,
        [
            "provider",
            "blocker_type",
            "blocker_active",
            "severity",
            "reason",
            "allowed_next_action",
            "forbidden_action",
        ],
    )
    write_json(STATE_PATH, state)
    write_report(state, recon_rows)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
