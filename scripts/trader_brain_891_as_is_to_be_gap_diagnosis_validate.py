from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_891_as_is_to_be_gap_diagnosis"

REQUIRED = [
    "repo_source_evidence_inventory.csv",
    "repo_source_evidence_inventory_summary.csv",
    "as_is_to_be_gap_matrix.csv",
    "to_be_requirement_backlog.csv",
    "task_891_gap_diagnosis_summary.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors
    inventory = rows(ART / "repo_source_evidence_inventory.csv")
    if not inventory:
        errors.append("source evidence inventory must not be empty")
    required_cols = {"relative_path", "classification", "source_time_bridge_state", "has_available_to_brain_ts", "has_source_hash"}
    if not required_cols.issubset(inventory[0].keys()):
        errors.append("source evidence inventory missing required columns")
    gap = rows(ART / "as_is_to_be_gap_matrix.csv")
    areas = {row["area"] for row in gap}
    for area in ["market_data", "historical_source_time_panel", "brain_state", "relationship_graph", "candidate_decision_trade_spec", "leakage_guard"]:
        if area not in areas:
            errors.append(f"gap matrix missing area {area}")
    source_gap = [row for row in gap if row["area"] == "historical_source_time_panel"]
    if not source_gap or source_gap[0]["status"] != "not_ready":
        errors.append("historical source-time panel must remain not_ready")
    backlog = rows(ART / "to_be_requirement_backlog.csv")
    if len(backlog) < 5:
        errors.append("to-be backlog must contain at least five requirements")
    summary = json.loads((ART / "task_891_gap_diagnosis_summary.json").read_text(encoding="utf-8"))
    if summary.get("first_real_historical_brain_replay") != "no_go":
        errors.append("first real historical brain replay must remain no_go")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_891_GAP_DIAGNOSIS_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_891_GAP_DIAGNOSIS_OK] AS-IS/TO-BE gap diagnosis artifacts validated")


if __name__ == "__main__":
    main()
