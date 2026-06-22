from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"
REPORT = ROOT / "docs/reports/task_1141_1150_external_source_acquisition"

REQUIRED_FILES = [
    "task1141_external_source_catalog.csv",
    "task1142_sec_ticker_cik_map.csv",
    "task1143_sec_submission_download_panel.csv",
    "task1144_current_exchange_directory_panel.csv",
    "task1145_federal_register_policy_archive_panel.csv",
    "task1146_macro_vintage_download_panel.csv",
    "task1147_pit_universe_resolution_matrix.csv",
    "task1148_historical_receipt_resolution_matrix.csv",
    "task1149_replay_readiness_after_external_acquisition.csv",
    "task1150_external_source_acquisition_closeout.csv",
    "task1150_external_source_acquisition_closeout.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1141_1150_external_source_acquisition.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1141_1150_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    catalog = rows(ART / "task1141_external_source_catalog.csv")
    sec_map = rows(ART / "task1142_sec_ticker_cik_map.csv")
    submissions = rows(ART / "task1143_sec_submission_download_panel.csv")
    exchange = rows(ART / "task1144_current_exchange_directory_panel.csv")
    fr = rows(ART / "task1145_federal_register_policy_archive_panel.csv")
    macro = rows(ART / "task1146_macro_vintage_download_panel.csv")
    pit = rows(ART / "task1147_pit_universe_resolution_matrix.csv")
    receipt = rows(ART / "task1148_historical_receipt_resolution_matrix.csv")
    readiness = rows(ART / "task1149_replay_readiness_after_external_acquisition.csv")
    closeout = rows(ART / "task1150_external_source_acquisition_closeout.csv")
    closeout_json = json.loads((ART / "task1150_external_source_acquisition_closeout.json").read_text(encoding="utf-8"))

    downloaded_catalog = [row for row in catalog if row["download_status"] == "downloaded"]
    if len(downloaded_catalog) < 3:
        errors.append("must download at least three official catalog files")
    for row in downloaded_catalog:
        raw_path = ROOT / row["raw_source_path"]
        if not raw_path.exists():
            errors.append(f"missing downloaded raw file {row['raw_source_path']}")
        elif file_sha256(raw_path) != row["source_hash"]:
            errors.append(f"hash mismatch for {row['source_id']}")

    if len(sec_map) != 70:
        errors.append("SEC ticker map must cover 70 universe rows")
    if sum(1 for row in sec_map if row["sec_mapping_pass"] == "1") < 60:
        errors.append("SEC ticker map unexpectedly low")
    if any(row["pit_theme_membership_pass"] != "0" for row in sec_map):
        errors.append("SEC map must not prove custom theme membership")

    if len(submissions) != 70:
        errors.append("SEC submissions panel must cover 70 universe rows")
    sec_accepted = sum(int(row["accepted_datetime_rows_2021_2026q1"]) for row in submissions)
    if sec_accepted <= 100:
        errors.append("SEC acceptedDateTime rows unexpectedly low")

    if len(exchange) != 70:
        errors.append("exchange directory panel must cover 70 universe rows")
    if any(row["pit_membership_pass"] != "0" for row in exchange):
        errors.append("current exchange directory must not grant PIT membership")

    if len(fr) != 10:
        errors.append("Federal Register panel must cover 10 theme queries")
    if sum(int(row["result_count"]) for row in fr) <= 0:
        errors.append("Federal Register downloads produced no official documents")
    if any(row["dynamic_replay_use_allowed"] != "0" for row in fr):
        errors.append("Federal Register rows must not allow replay yet")

    if len(macro) != 36:
        errors.append("macro vintage download panel must cover 6 series x 6 vintages")

    if len(pit) != 70:
        errors.append("PIT resolution must cover 70 universe rows")
    if any(row["pit_membership_pass"] != "0" for row in pit):
        errors.append("PIT membership must remain blocked")
    if any(row["replay_use_allowed"] != "0" for row in pit):
        errors.append("PIT rows must not allow replay")

    if len(receipt) != 4:
        errors.append("receipt resolution matrix must cover four source families")
    if any(row["dynamic_replay_use_allowed"] != "0" for row in receipt):
        errors.append("receipt matrix must not allow replay")

    if len(readiness) != 1:
        errors.append("readiness must have one row")
    else:
        row = readiness[0]
        if row["policy_preregistration_allowed"] != "0":
            errors.append("policy preregistration must remain blocked")
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("readiness must not execute replay or promote selection")
        if row["pit_membership_pass_rows"] != "0":
            errors.append("PIT pass must remain zero")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")
        if row["replay_executed"] != "0":
            errors.append("closeout must not execute replay")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")
    if closeout_json.get("pit_membership_pass_rows") != 0:
        errors.append("json closeout PIT pass must remain zero")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1141_1150_EXTERNAL_SOURCE_ACQUISITION_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1141_1150_EXTERNAL_SOURCE_ACQUISITION_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
