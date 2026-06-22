from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_895_l1_source_attachment"

REQUIRED_FILES = [
    "task_895_current_state_to_be_diagnosis.csv",
    "l1_source_attachment_ledger.csv",
    "l1_source_evidence_seed_with_attachments.csv",
    "local_lineage_attachment_gaps.csv",
    "raw_source_attachment_acquisition_queue.csv",
    "task_895_l1_source_attachment_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_FIELDS = {"side", "entry", "exit", "position_size", "rank", "score", "future_return", "realized_return", "pnl", "raw_trade_id"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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

    diagnosis = rows(ART / "task_895_current_state_to_be_diagnosis.csv")
    ledger = rows(ART / "l1_source_attachment_ledger.csv")
    enriched = rows(ART / "l1_source_evidence_seed_with_attachments.csv")
    gaps = rows(ART / "local_lineage_attachment_gaps.csv")
    queue = rows(ART / "raw_source_attachment_acquisition_queue.csv")
    summary = json.loads((ART / "task_895_l1_source_attachment_summary.json").read_text(encoding="utf-8"))

    if len(diagnosis) < 3:
        errors.append("diagnosis must cover local attachment, raw external source, and L2 readiness")
    if len(ledger) != 139:
        errors.append("attachment ledger must contain 139 L1 seed rows")
    if len(enriched) != len(ledger):
        errors.append("enriched L1 seed rows must match attachment ledger rows")
    if len(queue) != 70:
        errors.append("raw source acquisition queue must have 70 symbol rows")
    if gaps:
        errors.append("local lineage attachment gaps must be empty after Task895")
    if ledger and FORBIDDEN_FIELDS & set(ledger[0].keys()):
        errors.append("attachment ledger contains forbidden trading/raw price fields")
    if enriched and FORBIDDEN_FIELDS & set(enriched[0].keys()):
        errors.append("enriched L1 panel contains forbidden trading/raw price fields")

    for row in ledger:
        if row["local_attachment_state"] != "local_lineage_bundle_attached":
            errors.append("all ledger rows must have complete local lineage bundles")
            break
        if row["raw_external_document_state"] != "missing":
            errors.append("raw external document state must remain missing")
            break
        if row["attachment_authority"] != "LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE":
            errors.append("unexpected attachment authority")
            break
        for field in ["event_row_hash", "snapshot_row_hash", "lifecycle_row_hash", "setup_row_hash", "raw_trade_id_hash"]:
            if not row[field]:
                errors.append(f"ledger row missing {field}")
                break
        if errors:
            break

    for row in enriched:
        if row["l2_readiness"] != "blocked_until_raw_source_or_owner_approved_internal_scope":
            errors.append("L2 readiness must remain blocked with explicit reason")
            break
        if row["primitive_fact_state"] != "not_generated" or row["economic_meaning_state"] != "not_generated" or row["relation_state"] != "not_generated":
            errors.append("Task895 must not generate L2/L3 semantics")
            break

    if summary.get("attachment_ledger_rows") != len(ledger):
        errors.append("summary ledger row count mismatch")
    if summary.get("complete_local_lineage_attachments") != len(ledger):
        errors.append("summary complete local lineage count mismatch")
    if summary.get("raw_external_documents_attached") != 0:
        errors.append("Task895 must not claim raw external document attachment")
    if summary.get("raw_external_documents_missing") != len(ledger):
        errors.append("summary raw external missing count mismatch")
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
            print(f"[TRADER_BRAIN_895_L1_SOURCE_ATTACHMENT_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_895_L1_SOURCE_ATTACHMENT_OK] L1 source attachment artifacts validated")


if __name__ == "__main__":
    main()
