from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TASK_ID = "TASK-4150"
DEFAULT_ARTIFACT_DIR = Path("data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap")
REPORT_DIR = Path("docs/reports/task_4150_l3_diagnostic_strategy_view_bootstrap")
ALLOWED_GRAPH_STATES = {
    "SUPPORT_DOMINANT_REVIEW",
    "RISK_DOMINANT_REVIEW",
    "MIXED_REVIEW",
    "CONTEXT_ONLY",
    "BLOCKED_CRITICAL",
    "INSUFFICIENT_EVIDENCE",
}
AUTHORITY_FIELDS = (
    "trading_eligible",
    "signal_export_allowed",
    "order_intent_allowed",
    "broker_mutation_allowed",
    "paper_promotion_allowed",
    "live_order_allowed",
)
REQUIRED_ARTIFACTS = (
    "l3_input_manifest.json",
    "l3_meanings.jsonl",
    "l3_evidence_edges.jsonl",
    "l3_relation_graph.json",
    "l3_blocker_gap_ledger.csv",
    "l3_validator_report.json",
    "l3_review_summary.csv",
    "l3_rejected_or_review_queue.csv",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default=str(DEFAULT_ARTIFACT_DIR))
    args = parser.parse_args()
    status = validate(Path(args.artifact_dir))
    return 0 if status == "PASS" else 1


def validate(artifact_dir: Path) -> str:
    passes: list[str] = []
    failures: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = artifact_dir / name
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing artifact: {path}")
    if failures:
        return write_results(artifact_dir, passes, failures)

    manifest = json.loads((artifact_dir / "l3_input_manifest.json").read_text(encoding="utf-8"))
    meanings = read_jsonl(artifact_dir / "l3_meanings.jsonl")
    edges = read_jsonl(artifact_dir / "l3_evidence_edges.jsonl")
    graph = json.loads((artifact_dir / "l3_relation_graph.json").read_text(encoding="utf-8"))
    gaps = read_csv(artifact_dir / "l3_blocker_gap_ledger.csv")
    rejected = read_csv(artifact_dir / "l3_rejected_or_review_queue.csv")

    if not meanings:
        failures.append("no L3 meanings produced")
    else:
        passes.append(f"meaning_rows: {len(meanings)}")
    if len(meanings) != len(edges):
        failures.append(f"meanings/edges mismatch: {len(meanings)} vs {len(edges)}")
    else:
        passes.append(f"edge_rows: {len(edges)}")

    row_recon = manifest.get("row_reconciliation", {})
    if not row_recon.get("balanced"):
        failures.append("row reconciliation is not balanced")
    else:
        passes.append("row reconciliation balanced")

    if not any(row.get("gap_type") == "INCOMPLETE_BACKFILL" for row in gaps):
        failures.append("coverage gap ledger does not include incomplete backfill")
    else:
        passes.append("coverage gaps include incomplete backfill")

    if any("UNKNOWN_MAPPING" in row.get("reason_codes", "") and row.get("negative_evidence_allowed") != "0" for row in gaps):
        failures.append("UNKNOWN mapping gap allowed negative evidence")
    else:
        passes.append("UNKNOWN/missing gaps are not negative evidence")

    active_l2_ids = {row.get("l2_row_id") for row in meanings}
    rejected_l2_ids = {row.get("l2_row_id") for row in rejected if "UNKNOWN_MAPPING" in row.get("rejection_reasons", "")}
    contaminated = active_l2_ids & rejected_l2_ids
    if contaminated:
        failures.append(f"UNKNOWN mapping row active in L3: {sorted(contaminated)[:5]}")
    else:
        passes.append("UNKNOWN mapping rows not active")

    for row in meanings:
        if not row.get("l2_row_id") or not row.get("l1_packet_id"):
            failures.append(f"L3 meaning missing L2/L1 lineage: {row.get('l3_meaning_id')}")
        if row.get("calibration_status") != "NOT_CALIBRATED" or row.get("calibrated_probability") not in {None, "", "null"}:
            failures.append(f"calibration opened on row: {row.get('l3_meaning_id')}")
        check_authority_closed(row, failures, f"meaning {row.get('l3_meaning_id')}")
    passes.append("active L3 rows keep lineage and calibration closed")

    for row in edges:
        if row.get("direction_review") in {"BUY", "SELL"}:
            failures.append(f"forbidden trade direction in edge: {row.get('evidence_edge_id')}")
        check_authority_closed(row, failures, f"edge {row.get('evidence_edge_id')}")
    passes.append("edges keep authority closed")

    for row in graph.get("graphs", []):
        if row.get("graph_state") not in ALLOWED_GRAPH_STATES:
            failures.append(f"invalid graph state: {row.get('graph_state')}")
        check_authority_closed(row, failures, f"graph {row.get('graph_key')}")
    passes.append("graph states and authority valid")

    raw_inputs = [
        item["path"]
        for item in manifest.get("inputs", [])
        if "data/raw/" in item.get("path", "").replace("\\", "/")
    ]
    if raw_inputs:
        failures.append(f"L3 input manifest directly references L0 raw inputs: {raw_inputs}")
    else:
        passes.append("L3 input manifest does not directly consume L0 raw")

    status = write_results(artifact_dir, passes, failures)
    report = {"task_id": TASK_ID, "status": status, "passes": passes, "failures": failures}
    (artifact_dir / "l3_validator_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return status


def check_authority_closed(row: dict[str, Any], failures: list[str], label: str) -> None:
    for field in AUTHORITY_FIELDS:
        value = row.get(field)
        if value not in {None, "", 0, "0", False, "False", "false"}:
            failures.append(f"{label} authority opened: {field}={value}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_results(artifact_dir: Path, passes: list[str], failures: list[str]) -> str:
    status = "PASS" if not failures else "FAIL"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"# {TASK_ID} Validation Results", "", f"status: {status}", "", "## Passes"]
    lines.extend(f"- {item}" for item in passes)
    lines.extend(["", "## Failures"])
    if failures:
        lines.extend(f"- {item}" for item in failures)
    else:
        lines.append("- none")
    (REPORT_DIR / "validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"[{TASK_ID}] {status} passes={len(passes)} failures={len(failures)}")
    for item in failures:
        print(f"FAIL: {item}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
