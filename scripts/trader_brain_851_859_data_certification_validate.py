from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_850_859_data_certification"

REQUIRED_ARTIFACTS = [
    "file_inventory.csv",
    "schema_fingerprint_inventory.csv",
    "symbol_file_map.csv",
    "canonical_data_manifest.csv",
    "coverage_gap_report.csv",
    "redownload_queue.csv",
    "certification_decision.csv",
    "microstructure_readiness_audit.csv",
    "market_calendar_audit.csv",
    "corporate_action_audit.csv",
    "validator_summary.json",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    if not ARTIFACT_DIR.exists():
        return [f"missing artifact dir: {ARTIFACT_DIR}"]
    for name in REQUIRED_ARTIFACTS:
        path = ARTIFACT_DIR / name
        if not path.exists():
            errors.append(f"missing artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty artifact: {name}")
    if errors:
        return errors

    manifest = read_csv(ARTIFACT_DIR / "canonical_data_manifest.csv")
    dataset_ids = {row.get("dataset_id") for row in manifest}
    for required in ["us_daily", "us_daily_breadth_top500", "us_intraday", "microstructure_full_quotes", "microstructure_full_trades"]:
        if required not in dataset_ids:
            errors.append(f"manifest missing dataset_id={required}")

    decisions = read_csv(ARTIFACT_DIR / "certification_decision.csv")
    if not any(row.get("decision_area") == "market_data_gate_handoff" and row.get("status") == "MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY" for row in decisions):
        errors.append("gate handoff must remain MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY")
    forbidden_statuses = {"certified", "certified_for_controlled_replay"}
    if any(row.get("certification_status") in forbidden_statuses for row in manifest):
        errors.append("no dataset may be fully certified for controlled replay in Task851-859")

    file_inventory = read_csv(ARTIFACT_DIR / "file_inventory.csv")
    if len(file_inventory) < 700:
        errors.append("file inventory should cover existing daily, breadth, and intraday csv files")
    schemas = read_csv(ARTIFACT_DIR / "schema_fingerprint_inventory.csv")
    intraday_schemas = [row for row in schemas if row.get("dataset_id") == "us_intraday"]
    if len(intraday_schemas) < 2:
        errors.append("intraday mixed schema must be detected")
    gaps = read_csv(ARTIFACT_DIR / "coverage_gap_report.csv")
    for required_gap in ["gap_daily_adjustment_proof", "gap_pit_universe", "gap_calendar_2021_2025", "gap_intraday_schema_normalization", "gap_corporate_actions"]:
        if not any(row.get("gap_id") == required_gap for row in gaps):
            errors.append(f"missing gap row {required_gap}")

    micro = read_csv(ARTIFACT_DIR / "microstructure_readiness_audit.csv")
    if not micro:
        errors.append("missing microstructure readiness rows")
    if any(row.get("certification_status") != "certified_reference_only" for row in micro):
        errors.append("microstructure must remain reference-only")

    summary = json.loads((ARTIFACT_DIR / "validator_summary.json").read_text(encoding="utf-8"))
    if summary.get("no_backtest_executed") is not True:
        errors.append("summary must assert no backtest was executed")
    for field, expected in [
        ("strategy_acceptance", "NOT_ACCEPTED"),
        ("deployment_readiness", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY"),
        ("real_capital", "FORBIDDEN"),
    ]:
        if summary.get(field) != expected:
            errors.append(f"summary {field} must be {expected}")

    reports = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (ROOT / "docs/reports").glob("task_85*/*")
        if path.is_file() and path.suffix in {".md", ".csv"}
    )
    for phrase in ["MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY", "NOT_ACCEPTED", "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in reports and phrase not in json.dumps(summary):
            errors.append(f"missing phrase {phrase}")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_851_859_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_851_859_OK] data certification artifacts are complete and replay remains no-go")


if __name__ == "__main__":
    main()
