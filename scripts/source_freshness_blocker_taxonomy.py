"""Build Task3847 read-only source freshness blocker taxonomy artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3847_source_freshness_blocker_taxonomy"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID

TAXONOMY_PATH = ARTIFACT_DIR / "freshness_blocker_taxonomy.csv"
GATE_MATRIX_PATH = ARTIFACT_DIR / "strict_proxy_gate_matrix.csv"
SUMMARY_PATH = ARTIFACT_DIR / "source_family_blocker_summary.csv"
STATE_PATH = ARTIFACT_DIR / "source_freshness_blocker_taxonomy_state.json"
REPORT_PATH = REPORT_DIR / "source_freshness_blocker_taxonomy_report.md"
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


def blocker_class(row: dict[str, str]) -> str:
    status = row.get("freshness_status", "UNKNOWN")
    strict = row.get("strict_gate_allowed", "0")
    proxy = row.get("proxy_allowed", "0")
    if status in {"STALE", "MISSING", "NO_AUTHORITY_EVIDENCE"}:
        return f"{status}_SOURCE_BLOCKER"
    if strict != "1" and proxy != "1":
        return "STRICT_AND_PROXY_GATE_CLOSED"
    if strict != "1":
        return "STRICT_GATE_CLOSED"
    if proxy != "1":
        return "PROXY_GATE_CLOSED"
    return "DIAGNOSTIC_ONLY_REVIEW_REQUIRED"


def blocker_severity(row: dict[str, str]) -> str:
    status = row.get("freshness_status", "UNKNOWN")
    if status in {"STALE", "MISSING", "NO_AUTHORITY_EVIDENCE"}:
        return "P0_BLOCKER"
    if row.get("strict_gate_allowed", "0") != "1":
        return "P0_BLOCKER"
    return "P1_BLOCKER"


def build_taxonomy(freshness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in freshness_rows:
        output.append(
            {
                "source_family": row.get("source_family", ""),
                "provider": row.get("provider", ""),
                "freshness_status": row.get("freshness_status", "UNKNOWN"),
                "strict_gate_allowed": row.get("strict_gate_allowed", "0"),
                "proxy_allowed": row.get("proxy_allowed", "0"),
                "blocker_class": blocker_class(row),
                "severity": blocker_severity(row),
                "sla_minutes": row.get("freshness_sla_minutes", ""),
                "max_source_ts": row.get("max_source_ts", ""),
                "blocker_reason": row.get("blocker_reason", ""),
                "allowed_next_action": "Produce evidence requirements or validators only; do not run acquisition or open gates.",
                "forbidden_action": "No source acquisition, scheduler run, DB mutation, broker call, paper/live permission, or authority claim.",
            }
        )
    return output


def build_gate_matrix(freshness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in freshness_rows:
        family = row.get("source_family", "")
        for gate in ["strict_gate_allowed", "proxy_allowed"]:
            output.append(
                {
                    "source_family": family,
                    "gate_name": gate,
                    "gate_value": row.get(gate, "0"),
                    "gate_status": "CLOSED_BLOCKER" if row.get(gate, "0") != "1" else "OPEN_DIAGNOSTIC_ONLY",
                    "freshness_status": row.get("freshness_status", "UNKNOWN"),
                    "certification_status": row.get("certification_status", "UNKNOWN_BLOCKER"),
                    "permission_inference_allowed": "false",
                    "notes": "Gate values are copied from Task3845 evidence and do not grant permission.",
                }
            )
    return output


def build_summary(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = sorted({str(row["source_family"]) for row in taxonomy_rows})
    output = []
    for family in families:
        rows = [row for row in taxonomy_rows if row["source_family"] == family]
        p0_count = sum(1 for row in rows if row["severity"] == "P0_BLOCKER")
        output.append(
            {
                "source_family": family,
                "blocker_count": len(rows),
                "p0_blocker_count": p0_count,
                "top_blocker_class": rows[0]["blocker_class"] if rows else "UNKNOWN_BLOCKER",
                "next_evidence_needed": "Source-specific proof that freshness, strict gate, proxy gate, and authority evidence are separately satisfied.",
                "current_decision": "BLOCKED_DIAGNOSTIC_ONLY",
            }
        )
    return output


def build_manifest() -> list[dict[str, str]]:
    paths = [TAXONOMY_PATH, GATE_MATRIX_PATH, SUMMARY_PATH, STATE_PATH, REPORT_PATH, MANIFEST_PATH]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by Task3847 read-only freshness blocker taxonomy.",
        }
        for path in paths
    ]


def write_report(state: dict[str, Any], summary_rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3847 Source Freshness Blocker Taxonomy",
        "",
        "## Summary",
        "",
        "This task separates stale, strict-gate, proxy-gate, and certification blockers from Task3845 freshness evidence.",
        "It does not run source acquisition, schedulers, broker APIs, paper/live orders, replay, deployment, DB mutation, or gate changes.",
        "",
        "## Hard State",
        "",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "- Missing/stale data remains `UNKNOWN/BLOCKER`.",
        "",
        "## Outputs",
        "",
        f"- Freshness blocker taxonomy: `{TAXONOMY_PATH.as_posix()}`",
        f"- Strict/proxy gate matrix: `{GATE_MATRIX_PATH.as_posix()}`",
        f"- Source family summary: `{SUMMARY_PATH.as_posix()}`",
        "",
        "## Source Family Summary",
        "",
        "| Source Family | Blockers | P0 Blockers | Decision |",
        "| --- | --- | --- | --- |",
    ]
    for row in summary_rows:
        lines.append(f"| {row['source_family']} | {row['blocker_count']} | {row['p0_blocker_count']} | {row['current_decision']} |")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- No freshness blocker is interpreted as negative evidence.",
            "- No strict/proxy gate is opened by this taxonomy.",
            "- No source authority certification, paper/live permission, deployment readiness, strategy acceptance, broker mutation, or real-capital permission is granted.",
            "",
            "## State",
            "",
            f"- Taxonomy rows: {state['taxonomy_row_count']}",
            f"- Gate rows: {state['gate_row_count']}",
            f"- Open permission inference rows: {state['permission_inference_rows']}",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    freshness_rows = read_csv(PREV_ARTIFACT_DIR / "freshness_certification_matrix.csv")
    if not freshness_rows:
        raise SystemExit("Task3845 freshness matrix is missing or empty.")
    taxonomy_rows = build_taxonomy(freshness_rows)
    gate_rows = build_gate_matrix(freshness_rows)
    summary_rows = build_summary(taxonomy_rows)
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_FRESHNESS_TAXONOMY_COMPLETE_WITH_BLOCKERS",
        "taxonomy_row_count": len(taxonomy_rows),
        "gate_row_count": len(gate_rows),
        "summary_row_count": len(summary_rows),
        "permission_inference_rows": sum(1 for row in gate_rows if row["permission_inference_allowed"] != "false"),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(
        TAXONOMY_PATH,
        taxonomy_rows,
        [
            "source_family",
            "provider",
            "freshness_status",
            "strict_gate_allowed",
            "proxy_allowed",
            "blocker_class",
            "severity",
            "sla_minutes",
            "max_source_ts",
            "blocker_reason",
            "allowed_next_action",
            "forbidden_action",
        ],
    )
    write_csv(
        GATE_MATRIX_PATH,
        gate_rows,
        [
            "source_family",
            "gate_name",
            "gate_value",
            "gate_status",
            "freshness_status",
            "certification_status",
            "permission_inference_allowed",
            "notes",
        ],
    )
    write_csv(
        SUMMARY_PATH,
        summary_rows,
        [
            "source_family",
            "blocker_count",
            "p0_blocker_count",
            "top_blocker_class",
            "next_evidence_needed",
            "current_decision",
        ],
    )
    write_json(STATE_PATH, state)
    write_report(state, summary_rows)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
