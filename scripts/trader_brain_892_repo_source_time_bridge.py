from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK891_ART = ROOT / "data/artifacts/task_891_as_is_to_be_gap_diagnosis"
OUT_DIR = ROOT / "data/artifacts/task_892_repo_source_time_bridge"

ACCEPTED_FIELDS = [
    "evidence_id",
    "source_family",
    "symbol",
    "theme",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "source_url_or_file",
    "source_hash",
    "source_gap_flag",
    "bridge_authority",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def rejection_reason(row: dict[str, str]) -> str:
    if row["classification"] == "source_time_status_gap_report":
        return "prep_status_report_not_raw_evidence"
    if row["has_available_to_brain_ts"] != "1":
        return "missing_available_to_brain_ts"
    if row["has_received_ts"] != "1":
        return "missing_received_ts"
    if row["has_published_ts"] != "1":
        return "missing_published_ts"
    if row["has_source_hash"] != "1":
        return "missing_source_hash"
    if row["has_forbidden_outcome_hint"] == "1":
        return "contains_outcome_or_evaluation_columns"
    return "not_task883_compliant_without_manual_mapping"


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory = rows(TASK891_ART / "repo_source_evidence_inventory.csv")
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for row in inventory:
        if row["source_time_bridge_state"] == "bridge_ready" and row["classification"] != "source_time_status_gap_report":
            accepted.append(
                {
                    "evidence_id": "",
                    "source_family": "",
                    "symbol": "",
                    "theme": "",
                    "published_ts": "",
                    "received_ts": "",
                    "available_to_brain_ts": "",
                    "source_url_or_file": row["relative_path"],
                    "source_hash": row["sha256"],
                    "source_gap_flag": "",
                    "bridge_authority": "requires_row_level_mapping_before_use",
                }
            )
        else:
            rejected.append(
                {
                    "relative_path": row["relative_path"],
                    "classification": row["classification"],
                    "rejection_reason": rejection_reason(row),
                    "can_be_revisited": "1" if row["classification"] in {"derived_event_context_candidate", "lineage_support_candidate", "source_inventory_candidate"} else "0",
                    "does_not_mean": "negative evidence or source absence",
                }
            )
    summary_rows = [
        {"metric": "inventory_files", "value": len(inventory)},
        {"metric": "accepted_source_time_rows", "value": len(accepted)},
        {"metric": "rejected_source_artifacts", "value": len(rejected)},
        {"metric": "bridge_state", "value": "blocked_no_task883_compliant_raw_evidence"},
        {"metric": "first_real_historical_brain_replay", "value": "no_go"},
    ]
    write_csv(out_dir / "accepted_source_time_panel.csv", accepted, ACCEPTED_FIELDS)
    write_csv(out_dir / "rejected_source_artifact_ledger.csv", rejected, ["relative_path", "classification", "rejection_reason", "can_be_revisited", "does_not_mean"])
    write_csv(out_dir / "source_bridge_gap_summary.csv", summary_rows, ["metric", "value"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task892",
        "inventory_files": len(inventory),
        "accepted_source_time_rows": len(accepted),
        "rejected_source_artifacts": len(rejected),
        "bridge_state": "blocked_no_task883_compliant_raw_evidence",
        "first_real_historical_brain_replay": "no_go",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_892_source_bridge_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_892_SOURCE_BRIDGE_OK] "
        f"accepted={summary['accepted_source_time_rows']} rejected={summary['rejected_source_artifacts']} "
        f"bridge={summary['bridge_state']} replay={summary['first_real_historical_brain_replay']}"
    )


if __name__ == "__main__":
    main()
