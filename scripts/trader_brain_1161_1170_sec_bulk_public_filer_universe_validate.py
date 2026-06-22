from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1161_1170_sec_bulk_public_filer_universe"
REPORT = ROOT / "docs/reports/task_1161_1170_sec_bulk_public_filer_universe"
RAW_ZIP = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip"

REQUIRED_FILES = [
    "task1161_sec_bulk_download_ledger.csv",
    "task1162_sec_bulk_zip_inventory.csv",
    "task1163_public_filer_entity_panel.csv",
    "task1164_public_filer_membership_events.csv",
    "task1165_decision_calendar.csv",
    "task1166_public_filer_asof_universe_panel.csv",
    "task1167_public_filer_universe_coverage.csv",
    "task1168_vendor_exchange_listing_gap.csv",
    "task1169_public_filer_proxy_readiness.csv",
    "task1170_sec_bulk_public_filer_closeout.csv",
    "task1170_sec_bulk_public_filer_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
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
    if not (REPORT / "task_1161_1170_sec_bulk_public_filer_universe.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1161_1170_decision.csv").exists():
        errors.append("missing decision csv")
    if not RAW_ZIP.exists():
        errors.append("missing raw SEC bulk submissions zip")
    if errors:
        return errors

    download = rows("task1161_sec_bulk_download_ledger.csv")
    inventory = rows("task1162_sec_bulk_zip_inventory.csv")
    entities = rows("task1163_public_filer_entity_panel.csv")
    events = rows("task1164_public_filer_membership_events.csv")
    calendar = rows("task1165_decision_calendar.csv")
    asof = rows("task1166_public_filer_asof_universe_panel.csv")
    coverage = rows("task1167_public_filer_universe_coverage.csv")
    vendor_gap = rows("task1168_vendor_exchange_listing_gap.csv")
    readiness = rows("task1169_public_filer_proxy_readiness.csv")
    closeout = rows("task1170_sec_bulk_public_filer_closeout.csv")
    closeout_json = json.loads((ART / "task1170_sec_bulk_public_filer_closeout.json").read_text(encoding="utf-8"))

    if len(download) != 1:
        errors.append("download ledger must have one row")
    else:
        row = download[0]
        if row["download_status"] not in {"downloaded", "already_complete"}:
            errors.append("SEC bulk download did not complete")
        if int(row["bytes_downloaded"]) < 1_000_000_000:
            errors.append("SEC bulk zip size unexpectedly small")
        if file_sha256(RAW_ZIP) != row["source_hash"]:
            errors.append("SEC bulk zip hash mismatch")

    if len(inventory) != 1:
        errors.append("zip inventory must have one row")
    else:
        row = inventory[0]
        if int(row["json_members"]) < 5000:
            errors.append("zip JSON member count unexpectedly low")
        if int(row["files_processed"]) < 5000:
            errors.append("processed file count unexpectedly low")
        if int(row["files_failed"]) != 0:
            errors.append("SEC bulk JSON processing failures detected")

    if len(entities) < 5000:
        errors.append("public-filer entity panel unexpectedly small")
    if len(events) < len(entities):
        errors.append("membership events should cover at least all entities")
    if any(row["exchange_listed_pit_pass"] != "0" for row in entities[:500]):
        errors.append("public filer entities must not claim exchange listing PIT")
    if any(row["public_filer_asof_pass"] != "1" for row in events[:500]):
        errors.append("membership events must pass public-filer asof proxy")

    if len(calendar) != 63:
        errors.append("calendar must cover 63 month-end decisions")
    if len(asof) < 100_000:
        errors.append("public-filer asof panel unexpectedly small")
    if any(row["replay_use_allowed"] != "0" for row in asof[:500]):
        errors.append("asof proxy rows must not allow replay before policy preregistration")

    if len(coverage) != 63:
        errors.append("coverage must cover all 63 decisions")
    if min(int(row["unique_symbol_count"]) for row in coverage) <= 0:
        errors.append("coverage must have positive symbol counts")

    if len(vendor_gap) < 2:
        errors.append("vendor gap panel must record listing and ticker-history gaps")
    if any(row["blocks_true_exchange_listed_replay"] != "1" for row in vendor_gap):
        errors.append("vendor gaps must block true exchange-listed replay")

    if len(readiness) != 1:
        errors.append("readiness must have one row")
    else:
        row = readiness[0]
        if row["public_filer_proxy_universe_ready"] != "1":
            errors.append("public-filer proxy universe should be ready")
        if row["true_exchange_listed_universe_ready"] != "0":
            errors.append("true exchange listed universe must remain not ready")
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("readiness must not execute replay or promote selection")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["public_filer_proxy_universe_ready"] != "1":
            errors.append("closeout must mark proxy universe ready")
        if row["true_exchange_listed_universe_ready"] != "0":
            errors.append("closeout must keep true listed universe blocked")
        if row["replay_executed"] != "0":
            errors.append("closeout must record no replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")

    if closeout_json.get("public_filer_proxy_universe_ready") != "1":
        errors.append("json closeout must mark proxy ready")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1161_1170_SEC_BULK_PUBLIC_FILER_UNIVERSE_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1161_1170_SEC_BULK_PUBLIC_FILER_UNIVERSE_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
