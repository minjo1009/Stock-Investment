from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_895_l1_source_attachment"
L1_SEED = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed/l1_source_evidence_seed_state.csv"
SYMBOL_COVERAGE = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed/source_time_symbol_coverage_matrix.csv"
TASK372_DIR = ROOT / "docs/reports/task_372_historical_source_backfill"
TASK372_EVENTS = TASK372_DIR / "task_372_historical_source_event_dataset.csv"
TASK372_SNAPSHOTS = TASK372_DIR / "task_372_historical_snapshot_dataset.csv"
TASK372_LIFECYCLES = TASK372_DIR / "task_372_historical_lifecycle_identity.csv"
TASK372_SETUPS = TASK372_DIR / "task_372_historical_setup_identity.csv"

FORBIDDEN_FIELDS = {"side", "entry", "exit", "position_size", "rank", "score", "future_return", "realized_return", "pnl", "raw_trade_id"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def stable_hash(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_details(details_json: str) -> dict[str, object]:
    if not details_json:
        return {}
    try:
        parsed = json.loads(details_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def event_id_from_evidence(evidence_id: str) -> str:
    prefix = "Task893|"
    return evidence_id[len(prefix) :] if evidence_id.startswith(prefix) else evidence_id


def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    l1_rows = rows(L1_SEED)
    coverage_rows = rows(SYMBOL_COVERAGE)
    event_rows = rows(TASK372_EVENTS)
    snapshot_rows = rows(TASK372_SNAPSHOTS)
    lifecycle_rows = rows(TASK372_LIFECYCLES)
    setup_rows = rows(TASK372_SETUPS)

    events_by_id = {row["source_event_id"]: row for row in event_rows}
    snapshots_by_event = {row["event_id"]: row for row in snapshot_rows}
    lifecycles_by_id = {row["lifecycle_id"]: row for row in lifecycle_rows}
    setups_by_id = {row["setup_id"]: row for row in setup_rows}

    attachment_rows: list[dict[str, object]] = []
    enriched_rows: list[dict[str, object]] = []
    missing_rows: list[dict[str, object]] = []

    for l1 in l1_rows:
        source_event_id = event_id_from_evidence(l1["evidence_id"])
        event = events_by_id.get(source_event_id)
        snapshot = snapshots_by_event.get(source_event_id)
        details = parse_details(event.get("details_json", "") if event else "")
        lifecycle = lifecycles_by_id.get(event.get("lifecycle_id", "") if event else "")
        setup = setups_by_id.get(event.get("setup_id", "") if event else "")
        bundle_payload = {
            "evidence_id": l1["evidence_id"],
            "source_event_id": source_event_id,
            "event": event or {},
            "snapshot": snapshot or {},
            "lifecycle": lifecycle or {},
            "setup": setup or {},
        }
        attachment_bundle_id = f"ATTACH895-{stable_hash(bundle_payload)[:16]}"
        lineage_quality = str(details.get("lineage_quality", ""))
        intraday_match_status = str(details.get("intraday_match_status", ""))
        transition_reason = str(details.get("transition_reason", ""))
        raw_signal_id = str(details.get("raw_signal_id", ""))
        raw_trade_id_hash = stable_hash({"raw_trade_id": details.get("raw_trade_id", "")}) if details.get("raw_trade_id") else ""
        local_attachment_complete = bool(event and snapshot and lifecycle and setup)
        attachment_state = "local_lineage_bundle_attached" if local_attachment_complete else "local_lineage_bundle_incomplete"
        if not local_attachment_complete:
            missing_rows.append(
                {
                    "evidence_id": l1["evidence_id"],
                    "source_event_id": source_event_id,
                    "missing_event": int(not event),
                    "missing_snapshot": int(not snapshot),
                    "missing_lifecycle": int(not lifecycle),
                    "missing_setup": int(not setup),
                    "next_action": "repair_task372_local_lineage_before_l2",
                }
            )
        attachment_rows.append(
            {
                "attachment_bundle_id": attachment_bundle_id,
                "evidence_id": l1["evidence_id"],
                "source_event_id": source_event_id,
                "symbol": l1["symbol"],
                "theme": l1["theme"],
                "event_row_hash": stable_hash(event or {}),
                "snapshot_row_hash": stable_hash(snapshot or {}),
                "lifecycle_row_hash": stable_hash(lifecycle or {}),
                "setup_row_hash": stable_hash(setup or {}),
                "raw_signal_id": raw_signal_id,
                "raw_trade_id_hash": raw_trade_id_hash,
                "lineage_quality": lineage_quality,
                "intraday_match_status": intraday_match_status,
                "transition_reason": transition_reason,
                "local_attachment_state": attachment_state,
                "raw_external_document_state": "missing",
                "attachment_authority": "LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE",
                "does_not_mean": "raw external document exists, L2 meaning, L3 relation, candidate, trade, score, or rank",
            }
        )
        enriched_rows.append(
            {
                **l1,
                "attachment_bundle_id": attachment_bundle_id,
                "local_attachment_state": attachment_state,
                "raw_external_document_state": "missing",
                "attachment_authority": "LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE",
                "l2_readiness": "blocked_until_raw_source_or_owner_approved_internal_scope",
            }
        )

    acquisition_rows: list[dict[str, object]] = []
    for row in coverage_rows:
        if row["coverage_state"] == "l1_seed_available":
            step = "attach_raw_external_document_to_existing_l1_seed"
            priority = 1
        else:
            step = "collect_source_time_seed_then_attach_raw_external_document"
            priority = 2
        acquisition_rows.append(
            {
                "priority": priority,
                "theme": row["theme"],
                "symbol": row["symbol"],
                "coverage_state": row["coverage_state"],
                "recovered_event_rows": row["recovered_event_rows"],
                "required_source_families": row["required_source_families"],
                "implementation_step": step,
                "minimum_required_fields": "evidence_id;source_family;published_ts;received_ts;available_to_brain_ts;raw_source_uri;raw_source_hash",
                "guardrail": "no price/outcome inference; no synthetic rows; missing evidence is not a negative",
            }
        )
    acquisition_rows = sorted(acquisition_rows, key=lambda row: (int(row["priority"]), str(row["theme"]), str(row["symbol"])))

    diagnosis_rows = [
        {
            "area": "l1_local_lineage_attachment",
            "as_is": "139 L1 seed rows existed without an explicit local attachment bundle",
            "to_be": "each L1 seed links to Task372 event, snapshot, lifecycle, and setup lineage hashes",
            "gap": f"{len(missing_rows)} L1 seeds have incomplete local lineage attachment",
            "implemented_remediation": "l1_source_attachment_ledger.csv and l1_source_evidence_seed_with_attachments.csv",
            "status_after_task895": "implemented" if not missing_rows else "partial",
        },
        {
            "area": "raw_external_document_attachment",
            "as_is": "raw external documents are still absent from recovered internal seed rows",
            "to_be": "each evidence row has raw_source_uri and raw_source_hash",
            "gap": "raw external documents remain missing",
            "implemented_remediation": "raw source acquisition queue separated from local lineage attachment",
            "status_after_task895": "structured_gap_not_fabricated",
        },
        {
            "area": "l2_readiness",
            "as_is": "Task894 emitted L1-only seed states",
            "to_be": "L2 builder may consume only rows with approved source scope",
            "gap": "L2 remains blocked until raw source attachment or explicit owner-approved internal evidence scope",
            "implemented_remediation": "l2_readiness flag added per L1 seed",
            "status_after_task895": "blocked_with_explicit_reason",
        },
    ]

    write_csv(
        out_dir / "task_895_current_state_to_be_diagnosis.csv",
        diagnosis_rows,
        ["area", "as_is", "to_be", "gap", "implemented_remediation", "status_after_task895"],
    )
    write_csv(
        out_dir / "l1_source_attachment_ledger.csv",
        attachment_rows,
        [
            "attachment_bundle_id",
            "evidence_id",
            "source_event_id",
            "symbol",
            "theme",
            "event_row_hash",
            "snapshot_row_hash",
            "lifecycle_row_hash",
            "setup_row_hash",
            "raw_signal_id",
            "raw_trade_id_hash",
            "lineage_quality",
            "intraday_match_status",
            "transition_reason",
            "local_attachment_state",
            "raw_external_document_state",
            "attachment_authority",
            "does_not_mean",
        ],
    )
    write_csv(
        out_dir / "l1_source_evidence_seed_with_attachments.csv",
        enriched_rows,
        list(enriched_rows[0].keys()) if enriched_rows else [],
    )
    write_csv(
        out_dir / "local_lineage_attachment_gaps.csv",
        missing_rows,
        ["evidence_id", "source_event_id", "missing_event", "missing_snapshot", "missing_lifecycle", "missing_setup", "next_action"],
    )
    write_csv(
        out_dir / "raw_source_attachment_acquisition_queue.csv",
        acquisition_rows,
        ["priority", "theme", "symbol", "coverage_state", "recovered_event_rows", "required_source_families", "implementation_step", "minimum_required_fields", "guardrail"],
    )

    forbidden_present = sorted(FORBIDDEN_FIELDS & set(attachment_rows[0].keys())) if attachment_rows else []
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task895",
        "l1_seed_rows": len(l1_rows),
        "attachment_ledger_rows": len(attachment_rows),
        "complete_local_lineage_attachments": sum(1 for row in attachment_rows if row["local_attachment_state"] == "local_lineage_bundle_attached"),
        "incomplete_local_lineage_attachments": len(missing_rows),
        "raw_external_documents_attached": 0,
        "raw_external_documents_missing": len(attachment_rows),
        "raw_source_acquisition_queue_rows": len(acquisition_rows),
        "forbidden_fields_present": forbidden_present,
        "l2_readiness": "blocked_until_raw_source_or_owner_approved_internal_scope",
        "first_real_historical_brain_replay": "no_go_until_l2_l3_candidate_trade_spec_gates_pass",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_895_l1_source_attachment_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_895_L1_SOURCE_ATTACHMENT_OK] "
        f"l1_rows={summary['l1_seed_rows']} local_attached={summary['complete_local_lineage_attachments']} "
        f"raw_external_attached={summary['raw_external_documents_attached']} queue={summary['raw_source_acquisition_queue_rows']}"
    )


if __name__ == "__main__":
    main()
