"""Build Task3849 read-only authority ledger gap ranking artifacts."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "task_3849_authority_ledger_gap_ranking"
PREV_TASK_ID = "task_3845_source_authority_gate_10_loop"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID
PREV_ARTIFACT_DIR = Path("data/artifacts") / PREV_TASK_ID

GAP_RANK_PATH = ARTIFACT_DIR / "authority_ledger_gap_rank.csv"
LAYER_MATRIX_PATH = ARTIFACT_DIR / "evidence_layer_separation_matrix.csv"
STATE_PATH = ARTIFACT_DIR / "authority_ledger_gap_ranking_state.json"
REPORT_PATH = REPORT_DIR / "authority_ledger_gap_ranking_report.md"
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


def build_layer_matrix(authority_rows: list[dict[str, str]], freshness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    freshness_by_family = {row.get("source_family", ""): row for row in freshness_rows}
    output = []
    for row in authority_rows:
        family = row.get("source_family", "")
        fresh = freshness_by_family.get(family, {})
        layers = [
            ("source_receipt", int(row.get("receipt_count") or 0), "acquisition evidence only"),
            ("reference_hash", int(row.get("reference_hash_count") or 0), "content fingerprint only"),
            ("lineage_edge", int(row.get("lineage_edge_count") or 0), "derivation chain evidence only"),
            ("freshness_gate", 1 if fresh.get("freshness_status") == "CURRENT_OR_RECENT" else 0, "temporal evidence only"),
            ("strict_gate", 1 if fresh.get("strict_gate_allowed") == "1" else 0, "permission gate remains closed unless independently certified"),
            ("proxy_gate", 1 if fresh.get("proxy_allowed") == "1" else 0, "proxy gate remains closed unless independently certified"),
        ]
        for layer_name, evidence_count, meaning in layers:
            output.append(
                {
                    "source_family": family,
                    "evidence_layer": layer_name,
                    "evidence_count": evidence_count,
                    "layer_present": str(evidence_count > 0).lower(),
                    "layer_meaning": meaning,
                    "authority_certification_allowed": "false",
                    "blocker_status": "BLOCKED_DIAGNOSTIC_ONLY",
                }
            )
    return output


def build_gap_rank(layer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in layer_rows:
        grouped.setdefault(str(row["source_family"]), []).append(row)
    output = []
    for family, rows in grouped.items():
        closed_layers = [row["evidence_layer"] for row in rows if row["authority_certification_allowed"] != "true"]
        missing_layers = [row["evidence_layer"] for row in rows if row["layer_present"] != "true"]
        strict_closed = any(row["evidence_layer"] == "strict_gate" and row["evidence_count"] == 0 for row in rows)
        severity = "P0_BLOCKER" if strict_closed or missing_layers else "P1_BLOCKER"
        output.append(
            {
                "source_family": family,
                "severity": severity,
                "missing_layers": ";".join(missing_layers) if missing_layers else "",
                "closed_layers": ";".join(closed_layers),
                "authority_status": "BLOCKED_DIAGNOSTIC_ONLY",
                "required_next_evidence": "Independent proof that each evidence layer is complete and that strict/proxy gates may remain closed or be reviewed separately.",
                "forbidden_action": "No synthetic authority, gate opening, source acquisition, DB mutation, broker call, or paper/live permission.",
            }
        )
    output.sort(key=lambda row: (0 if row["severity"] == "P0_BLOCKER" else 1, row["source_family"]))
    for index, row in enumerate(output, 1):
        row["rank"] = index
    return output


def build_manifest() -> list[dict[str, str]]:
    paths = [GAP_RANK_PATH, LAYER_MATRIX_PATH, STATE_PATH, REPORT_PATH, MANIFEST_PATH]
    return [
        {
            "artifact_path": path.as_posix(),
            "artifact_type": "report" if path.suffix == ".md" else path.suffix.lstrip("."),
            "authority": "DIAGNOSTIC_ONLY_NOT_AUTHORITY",
            "status": "active",
            "notes": "Generated by Task3849 read-only authority ledger gap ranking.",
        }
        for path in paths
    ]


def write_report(state: dict[str, Any], gap_rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task3849 Authority Ledger Gap Ranking",
        "",
        "## Summary",
        "",
        "This task ranks authority-ledger gaps while keeping receipt, hash, lineage, freshness, strict gate, and proxy gate as separate evidence layers.",
        "It does not synthesize authority evidence and does not open source, broker, paper/live, deployment, strategy, or real-capital gates.",
        "",
        "## Hard State",
        "",
        f"- Strategy: {HARD_STATE['strategy']}",
        f"- Deployment: {HARD_STATE['deployment']}",
        f"- Real capital: {HARD_STATE['real_capital']}",
        "",
        "## Top Ranked Gaps",
        "",
        "| Rank | Source Family | Severity | Authority Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in gap_rows[:12]:
        lines.append(f"| {row['rank']} | {row['source_family']} | {row['severity']} | {row['authority_status']} |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Authority gap rank: `{GAP_RANK_PATH.as_posix()}`",
            f"- Evidence layer separation matrix: `{LAYER_MATRIX_PATH.as_posix()}`",
            "",
            "## Safety",
            "",
            "- Diagnostic receipt/hash/lineage rows are not authority certification.",
            "- Missing or closed layers remain `UNKNOWN/BLOCKER` or `BLOCKED_DIAGNOSTIC_ONLY`.",
            "- No source acquisition, scheduler run, DB mutation, broker mutation, paper/live permission, deployment readiness, strategy acceptance, or real-capital permission is granted.",
            "",
            "## State",
            "",
            f"- Ranked source families: {state['ranked_family_count']}",
            f"- Evidence layer rows: {state['layer_row_count']}",
            f"- Authority certification rows: {state['authority_certification_rows']}",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    authority_rows = read_csv(PREV_ARTIFACT_DIR / "authority_ledger_summary.csv")
    freshness_rows = read_csv(PREV_ARTIFACT_DIR / "freshness_certification_matrix.csv")
    if not authority_rows:
        raise SystemExit("Task3845 authority ledger summary is missing or empty.")
    layer_rows = build_layer_matrix(authority_rows, freshness_rows)
    gap_rows = build_gap_rank(layer_rows)
    state = {
        "task_id": TASK_ID,
        "previous_task_id": PREV_TASK_ID,
        "generated_at_utc": utc_now(),
        **HARD_STATE,
        "overall_status": "READ_ONLY_AUTHORITY_GAP_RANKING_COMPLETE_WITH_BLOCKERS",
        "ranked_family_count": len(gap_rows),
        "layer_row_count": len(layer_rows),
        "authority_certification_rows": sum(1 for row in layer_rows if row["authority_certification_allowed"] != "false"),
        "source_acquisition_run": False,
        "scheduler_run": False,
        "db_mutation": False,
        "broker_mutation_added": False,
        "paper_live_permission_granted": False,
        "real_capital_permission_granted": False,
    }
    write_csv(
        GAP_RANK_PATH,
        gap_rows,
        [
            "rank",
            "source_family",
            "severity",
            "missing_layers",
            "closed_layers",
            "authority_status",
            "required_next_evidence",
            "forbidden_action",
        ],
    )
    write_csv(
        LAYER_MATRIX_PATH,
        layer_rows,
        [
            "source_family",
            "evidence_layer",
            "evidence_count",
            "layer_present",
            "layer_meaning",
            "authority_certification_allowed",
            "blocker_status",
        ],
    )
    write_json(STATE_PATH, state)
    write_report(state, gap_rows)
    write_csv(MANIFEST_PATH, build_manifest(), ["artifact_path", "artifact_type", "authority", "status", "notes"])
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
