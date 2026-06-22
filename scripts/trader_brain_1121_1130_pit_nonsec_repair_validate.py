from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
import hashlib


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1121_1130_pit_nonsec_repair"

REQUIRED_FILES = [
    "task1121_pit_membership_schema_contract.csv",
    "task1122_pit_source_catalog.csv",
    "task1123_pit_membership_validation_panel.csv",
    "task1124_trade_spec_pit_join_audit.csv",
    "task1125_nonsec_event_schema_contract.csv",
    "task1126_nonsec_normalized_event_candidates.csv",
    "task1127_nonsec_event_validation_panel.csv",
    "task1128_fresh_entry_candidate_ledger.csv",
    "task1128_continuous_exposure_episode_ledger.csv",
    "task1129_integrated_pre_replay_gate.csv",
    "task1130_pit_nonsec_repair_closeout.csv",
    "task1130_pit_nonsec_repair_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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
    if errors:
        return errors

    pit_schema = rows("task1121_pit_membership_schema_contract.csv")
    pit_sources = rows("task1122_pit_source_catalog.csv")
    pit_membership = rows("task1123_pit_membership_validation_panel.csv")
    pit_join = rows("task1124_trade_spec_pit_join_audit.csv")
    nonsec_schema = rows("task1125_nonsec_event_schema_contract.csv")
    nonsec_events = rows("task1126_nonsec_normalized_event_candidates.csv")
    nonsec_validation = rows("task1127_nonsec_event_validation_panel.csv")
    fresh = rows("task1128_fresh_entry_candidate_ledger.csv")
    exposure = rows("task1128_continuous_exposure_episode_ledger.csv")
    gate = rows("task1129_integrated_pre_replay_gate.csv")
    closeout = rows("task1130_pit_nonsec_repair_closeout.csv")
    manifest = rows("artifact_manifest.csv")
    closeout_json = json.loads((ART / "task1130_pit_nonsec_repair_closeout.json").read_text(encoding="utf-8"))

    required_pit_fields = {
        "effective_start_ts",
        "effective_end_ts",
        "published_ts",
        "received_ts",
        "available_to_brain_ts",
        "raw_source_path",
        "source_hash",
        "pit_membership_pass",
    }
    if not required_pit_fields.issubset({row["field_name"] for row in pit_schema}):
        errors.append("PIT schema missing required fields")

    if len(pit_sources) != 70:
        errors.append("PIT source catalog must retain 70 reference rows")
    if {row["pit_membership_source_pass"] for row in pit_sources} != {"0"}:
        errors.append("reference-only PIT sources must not pass")

    if len(pit_membership) != 4410:
        errors.append("PIT membership validation must audit 4410 decision-symbol rows")
    if {row["pit_membership_pass"] for row in pit_membership} != {"0"}:
        errors.append("PIT membership must remain blocked without source dates")
    if {row["selection_use_allowed"] for row in pit_membership} != {"0"}:
        errors.append("PIT membership must not allow selection")

    if len(pit_join) != 3689:
        errors.append("PIT join audit must cover 3689 SEC feature rows")
    if {row["pit_membership_pass"] for row in pit_join} != {"0"}:
        errors.append("PIT join must block all SEC feature rows in current state")
    if {row["replay_use_allowed"] for row in pit_join} != {"0"}:
        errors.append("PIT join must not allow replay")

    required_nonsec_fields = {
        "event_id",
        "source_family",
        "published_ts",
        "received_ts",
        "available_to_brain_ts",
        "source_hash",
        "time_precision",
        "source_time_method",
        "tag_source_method",
        "dynamic_use_allowed",
    }
    if not required_nonsec_fields.issubset({row["field_name"] for row in nonsec_schema}):
        errors.append("non-SEC schema missing required fields")
    if len(nonsec_events) < 1000:
        errors.append("non-SEC normalized candidate panel unexpectedly small")
    if not any(row["source_family"] == "macro_fred" for row in nonsec_events):
        errors.append("macro_fred candidates missing")
    if not any(row["source_family"] == "task_636_content_source_text" for row in nonsec_events):
        errors.append("Task636 content candidates missing")
    if any(row.get("source_name") == "sec_company_submissions" for row in nonsec_events):
        errors.append("SEC company submissions must not be mixed into non-SEC candidates")

    checked_hashes = 0
    for row in nonsec_events[:250]:
        raw_path = ROOT / row["raw_source_path"] if row.get("raw_source_path") else None
        if raw_path and raw_path.exists() and row.get("source_hash"):
            checked_hashes += 1
            if file_sha256(raw_path) != row["source_hash"]:
                errors.append(f"source hash mismatch for {row['event_id']}")
                break
    if checked_hashes == 0:
        errors.append("non-SEC validation must be able to verify at least one raw source hash")

    if len(nonsec_validation) != len(nonsec_events):
        errors.append("non-SEC validation row count must match normalized candidates")
    if {row["dynamic_use_allowed"] for row in nonsec_validation} != {"0"}:
        errors.append("non-SEC events must not be dynamic-use allowed yet")
    if not any("missing_received_ts" in row["block_reason"] for row in nonsec_validation):
        errors.append("non-SEC validation should detect missing received timestamp")
    for row in nonsec_validation:
        available = parse_dt(row["available_to_brain_ts"])
        published = parse_dt(row["published_ts"])
        received = parse_dt(row["received_ts"])
        if available and published and available < published:
            errors.append("non-SEC available timestamp before published timestamp")
            break
        if available and received and available < received:
            errors.append("non-SEC available timestamp before received timestamp")
            break

    if len(fresh) != 135:
        errors.append("fresh entry boundary must cover 135 selected rows")
    if sum(1 for row in fresh if row["fresh_entry_candidate_flag"] == "1") != 6:
        errors.append("fresh entry boundary should isolate 6 first-entry candidates")
    if {row["replay_use_allowed"] for row in fresh} != {"0"}:
        errors.append("fresh entry boundary must not allow replay")

    if len(exposure) != 6:
        errors.append("exposure boundary must contain six continuous exposure episodes")
    if {row["entry_counting_allowed"] for row in exposure} != {"0"}:
        errors.append("continuous exposure episodes must not be counted as fresh entries")

    if len(gate) != 1 or len(closeout) != 1:
        errors.append("gate and closeout must each have one row")
    else:
        row = closeout[0]
        if row["verdict"] not in {"blocked_continue_source_repair", "go_for_policy_preregistration_only"}:
            errors.append("closeout verdict is not allowed")
        if row["verdict"] != "blocked_continue_source_repair":
            errors.append("current state should remain blocked because PIT and non-SEC dynamic rows are zero")
        if row["replay_executed"] != "0":
            errors.append("closeout must not execute replay")
        if row["selection_promoted"] != "0":
            errors.append("closeout must not promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")
    if len(manifest) < len(REQUIRED_FILES) - 1:
        errors.append("artifact manifest must list generated artifacts")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1121_1130_PIT_NONSEC_REPAIR_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1121_1130_PIT_NONSEC_REPAIR_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
