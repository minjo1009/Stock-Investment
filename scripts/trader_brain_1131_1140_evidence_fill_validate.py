from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1131_1140_evidence_fill"

REQUIRED_FILES = [
    "task1131_pit_source_candidate_inventory.csv",
    "task1132_pit_source_timestamp_hash_ledger.csv",
    "task1133_pit_membership_event_candidates.csv",
    "task1134_pit_membership_pass_recheck.csv",
    "task1135_nonsec_raw_timestamp_recovery.csv",
    "task1136_macro_vintage_recheck.csv",
    "task1137_nonsec_asof_event_panel.csv",
    "task1138_dynamic_event_l1_l4_shadow_bridge.csv",
    "task1139_policy_preregistration_readiness.csv",
    "task1140_evidence_fill_closeout.csv",
    "task1140_evidence_fill_closeout.json",
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
    if errors:
        return errors

    pit_candidates = rows("task1131_pit_source_candidate_inventory.csv")
    pit_ts = rows("task1132_pit_source_timestamp_hash_ledger.csv")
    pit_events = rows("task1133_pit_membership_event_candidates.csv")
    pit_recheck = rows("task1134_pit_membership_pass_recheck.csv")
    nonsec_recovered = rows("task1135_nonsec_raw_timestamp_recovery.csv")
    macro = rows("task1136_macro_vintage_recheck.csv")
    asof = rows("task1137_nonsec_asof_event_panel.csv")
    bridge = rows("task1138_dynamic_event_l1_l4_shadow_bridge.csv")
    readiness = rows("task1139_policy_preregistration_readiness.csv")
    closeout = rows("task1140_evidence_fill_closeout.csv")
    manifest = rows("artifact_manifest.csv")
    closeout_json = json.loads((ART / "task1140_evidence_fill_closeout.json").read_text(encoding="utf-8"))

    if len(pit_candidates) < 5:
        errors.append("PIT candidate inventory must include local candidate classes")
    if {row["pit_source_candidate"] for row in pit_candidates} != {"0"}:
        errors.append("current PIT source candidates must remain blocked")
    if len(pit_ts) != len(pit_candidates):
        errors.append("PIT timestamp ledger must match candidate inventory")

    if len(pit_events) != 4410:
        errors.append("PIT membership event candidates must cover 4410 decision-symbol rows")
    if {row["pit_membership_pass"] for row in pit_events} != {"0"}:
        errors.append("PIT membership candidates must not pass without row-level evidence")

    if len(pit_recheck) != 3689:
        errors.append("PIT recheck must cover 3689 SEC feature rows")
    if {row["pit_membership_pass"] for row in pit_recheck} != {"0"}:
        errors.append("PIT feature recheck must remain blocked")
    if {row["replay_use_allowed"] for row in pit_recheck} != {"0"}:
        errors.append("PIT recheck must not allow replay")

    if len(nonsec_recovered) < 100:
        errors.append("non-SEC raw timestamp recovery unexpectedly small")
    if any(row["source_name"] == "sec_company_submissions" for row in nonsec_recovered):
        errors.append("SEC company submissions must not be in non-SEC recovery")
    checked_hashes = 0
    for row in nonsec_recovered[:250]:
        raw_path = ROOT / row["raw_source_path"] if row["raw_source_path"] else None
        if raw_path and raw_path.exists() and row["source_hash"]:
            checked_hashes += 1
            if file_sha256(raw_path) != row["source_hash"]:
                errors.append(f"hash mismatch for {row['recovered_event_id']}")
                break
    if checked_hashes == 0:
        errors.append("must verify at least one non-SEC raw hash")

    if len(macro) != 11654:
        errors.append("macro vintage recheck must cover 11654 FRED rows")
    if {row["macro_vintage_pass"] for row in macro} != {"0"}:
        errors.append("macro rows must remain blocked without vintage as-of certification")

    if len(asof) != len(nonsec_recovered) + len(macro):
        errors.append("as-of panel row count must equal recovered non-SEC plus macro rows")
    if sum(1 for row in asof if row["source_time_complete_flag"] == "1") <= 0:
        errors.append("as-of panel should have source-time complete rows from local captures")
    if {row["replay_use_allowed"] for row in asof} != {"0"}:
        errors.append("as-of events must not allow replay")
    if any(row["historical_dynamic_use_allowed"] == "1" for row in asof):
        errors.append("current local-capture events must not be historical dynamic-use allowed")

    if len(bridge) != len(asof):
        errors.append("L1-L4 shadow bridge must cover all as-of events")
    if {row["selection_use_allowed"] for row in bridge} != {"0"}:
        errors.append("shadow bridge must not allow selection")

    if len(readiness) != 1:
        errors.append("policy readiness must have one row")
    else:
        if readiness[0]["policy_preregistration_allowed"] != "0":
            errors.append("policy preregistration must remain blocked")
        if readiness[0]["replay_executed"] != "0" or readiness[0]["selection_promoted"] != "0":
            errors.append("readiness must not execute replay or promote selection")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["verdict"] != "blocked_continue_source_repair":
            errors.append("closeout must remain blocked")
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("closeout must not execute replay or promote selection")
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
        print("[TRADER_BRAIN_1131_1140_EVIDENCE_FILL_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1131_1140_EVIDENCE_FILL_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
