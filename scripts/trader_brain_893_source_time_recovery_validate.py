from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_893_source_time_recovery"

REQUIRED_FILES = [
    "recovered_source_time_panel.csv",
    "rejected_event_source_rows.csv",
    "source_time_recovery_summary.csv",
    "source_time_recovery_backlog.csv",
    "task_893_source_time_recovery_summary.json",
    "artifact_manifest.csv",
]

REQUIRED_RECOVERED_FIELDS = {
    "evidence_id",
    "source_family",
    "symbol",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "source_url_or_file",
    "source_hash",
    "source_gap_flag",
    "bridge_authority",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    recovered = rows(ART / "recovered_source_time_panel.csv")
    rejected = rows(ART / "rejected_event_source_rows.csv")
    backlog = rows(ART / "source_time_recovery_backlog.csv")
    summary = json.loads((ART / "task_893_source_time_recovery_summary.json").read_text(encoding="utf-8"))

    if not recovered:
        errors.append("recovered source-time panel must contain recovered rows")
    if not rejected:
        errors.append("rejected event rows must not be empty")
    if len(backlog) < 4:
        errors.append("source-time recovery backlog must list concrete remaining steps")
    if recovered and not REQUIRED_RECOVERED_FIELDS.issubset(recovered[0].keys()):
        errors.append("recovered panel missing required Task883 bridge fields")

    for row in recovered:
        if row["source_url_or_file"] != "docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv":
            errors.append("only Task372 historical source capture rows may be recovered")
            break
        if row["source_family"] != "internal_source_event_capture":
            errors.append("unexpected source_family")
            break
        if row["source_gap_flag"] != "raw_external_document_missing":
            errors.append("recovered rows must preserve raw external document gap")
            break
        if row["bridge_authority"] != "diagnostic_recovered_internal_event_only":
            errors.append("recovered rows must remain diagnostic internal-event evidence")
            break
        if not row["source_hash"]:
            errors.append("recovered row missing source_hash")
            break
        if parse_ts(row["available_to_brain_ts"]) < parse_ts(row["published_ts"]):
            errors.append("available_to_brain_ts precedes published_ts")
            break
        if parse_ts(row["available_to_brain_ts"]) < parse_ts(row["received_ts"]):
            errors.append("available_to_brain_ts precedes received_ts")
            break

    if summary.get("recovered_source_time_rows") != len(recovered):
        errors.append("summary recovered row count mismatch")
    if summary.get("rejected_event_rows") != len(rejected):
        errors.append("summary rejected row count mismatch")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic-only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain FORBIDDEN")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_893_SOURCE_TIME_RECOVERY_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_893_SOURCE_TIME_RECOVERY_OK] recovered source-time artifacts validated")


if __name__ == "__main__":
    main()
