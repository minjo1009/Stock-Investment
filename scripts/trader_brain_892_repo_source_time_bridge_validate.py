from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_892_repo_source_time_bridge"

REQUIRED = [
    "accepted_source_time_panel.csv",
    "rejected_source_artifact_ledger.csv",
    "source_bridge_gap_summary.csv",
    "task_892_source_bridge_summary.json",
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
    accepted = rows(ART / "accepted_source_time_panel.csv")
    rejected = rows(ART / "rejected_source_artifact_ledger.csv")
    if accepted:
        required = {"evidence_id", "source_family", "published_ts", "received_ts", "available_to_brain_ts", "source_hash", "source_gap_flag"}
        if not required.issubset(accepted[0].keys()):
            errors.append("accepted source-time panel missing Task883 fields")
    if not rejected:
        errors.append("rejected artifact ledger must not be empty")
    summary = json.loads((ART / "task_892_source_bridge_summary.json").read_text(encoding="utf-8"))
    if summary.get("accepted_source_time_rows") != 0:
        errors.append("accepted source-time rows must remain 0 until row-level mapping exists")
    if summary.get("first_real_historical_brain_replay") != "no_go":
        errors.append("first real historical brain replay must remain no_go")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_892_SOURCE_BRIDGE_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_892_SOURCE_BRIDGE_OK] repo source-time bridge artifacts validated")


if __name__ == "__main__":
    main()
