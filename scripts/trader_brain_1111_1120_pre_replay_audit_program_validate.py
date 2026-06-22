from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1111_1120_pre_replay_audit_program"

REQUIRED_FILES = [
    "task1111_pit_universe_source_catalog.csv",
    "task1112_pit_membership_panel.csv",
    "task1113_trade_spec_pit_join_audit.csv",
    "task1114_pit_block_ledger.csv",
    "task1115_reentry_freshness_ledger.csv",
    "task1116_continuous_thesis_exposure_ledger.csv",
    "task1117_structural_hold_policy_preregistration.csv",
    "task1118_non_sec_source_time_panel.csv",
    "task1119_dynamic_event_shadow_ranking.csv",
    "task1120_external_audit_closeout.csv",
    "task1120_external_audit_closeout.json",
    "artifact_manifest.csv",
]


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

    task1111 = rows(ART / "task1111_pit_universe_source_catalog.csv")
    task1112 = rows(ART / "task1112_pit_membership_panel.csv")
    task1113 = rows(ART / "task1113_trade_spec_pit_join_audit.csv")
    task1114 = rows(ART / "task1114_pit_block_ledger.csv")
    task1115 = rows(ART / "task1115_reentry_freshness_ledger.csv")
    task1116 = rows(ART / "task1116_continuous_thesis_exposure_ledger.csv")
    task1117 = rows(ART / "task1117_structural_hold_policy_preregistration.csv")
    task1118 = rows(ART / "task1118_non_sec_source_time_panel.csv")
    task1119 = rows(ART / "task1119_dynamic_event_shadow_ranking.csv")
    closeout = rows(ART / "task1120_external_audit_closeout.csv")
    closeout_json = json.loads((ART / "task1120_external_audit_closeout.json").read_text(encoding="utf-8"))

    if len(task1111) != 70:
        errors.append("Task1111 must catalog 70 universe rows")
    if {row["has_pit_membership_timestamp"] for row in task1111} != {"0"}:
        errors.append("Task1111 must not infer PIT membership timestamps")
    if {row["selection_use_allowed"] for row in task1111} != {"0"}:
        errors.append("Task1111 must block selection use")

    if len(task1112) != 70:
        errors.append("Task1112 must produce 70 membership rows")
    if {row["pit_membership_pass"] for row in task1112} != {"0"}:
        errors.append("Task1112 must block all unverified static memberships")
    if {row["evidence_state"] for row in task1112} != {"missing_pit_membership_source"}:
        errors.append("Task1112 must preserve missing PIT evidence state")

    if len(task1113) != 3689:
        errors.append("Task1113 must audit all 3689 SEC as-of feature rows")
    if {row["pit_universe_pass"] for row in task1113} != {"0"}:
        errors.append("Task1113 must block all rows by PIT universe")
    if {row["pit_replay_allowed"] for row in task1113} != {"0"}:
        errors.append("Task1113 must not allow replay")

    if len(task1114) != len(task1113):
        errors.append("Task1114 PIT block ledger must match blocked join rows")
    if {row["would_block_replay"] for row in task1114} != {"1"}:
        errors.append("Task1114 must block replay")

    if len(task1115) != 135:
        errors.append("Task1115 must audit 135 selected rows for sec_slot3_theme_cap1_v1")
    stale = [row for row in task1115 if row["stale_reentry_flag"] == "1"]
    if len(stale) < 100:
        errors.append("Task1115 must detect broad stale same-score reentry")
    if {row["reentry_selection_use_allowed"] for row in task1115} != {"0"}:
        errors.append("Task1115 must not promote reentry selections")

    if len(task1116) != 6:
        errors.append("Task1116 must collapse selected rows into 6 symbol/thesis exposure chains")
    if not all(int(row["stale_reentry_count"]) > 0 for row in task1116):
        errors.append("Task1116 must identify stale exposure chains")

    if len(task1117) != 3:
        errors.append("Task1117 must preregister three policy/control rows")
    if {row["preregistered_before_replay_flag"] for row in task1117} != {"1"}:
        errors.append("Task1117 policies must be preregistered")
    if {row["pit_universe_required_flag"] for row in task1117} != {"1"}:
        errors.append("Task1117 must require PIT universe")
    if {row["non_sec_source_required_flag"] for row in task1117} != {"1"}:
        errors.append("Task1117 must require non-SEC sources")

    if len(task1118) < 5:
        errors.append("Task1118 must inventory at least five non-SEC source families")
    if {row["dynamic_use_allowed"] for row in task1118} != {"0"}:
        errors.append("Task1118 must not allow dynamic use before normalized source-time rows")
    if not any(row["has_published_ts"] == "1" for row in task1118):
        errors.append("Task1118 should surface at least one timestamped candidate for later repair")

    if len(task1119) != len(task1115):
        errors.append("Task1119 shadow rows must match selected reentry audit rows")
    if {row["shadow_ranking_use_allowed"] for row in task1119} != {"0"}:
        errors.append("Task1119 must keep shadow ranking out of selection/replay")

    if len(closeout) != 1:
        errors.append("Task1120 closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0":
            errors.append("Task1120 must not execute replay")
        if row["selection_promoted"] != "0":
            errors.append("Task1120 must not promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("Task1120 changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("Task1120 changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("Task1120 changed real capital")
        if int(row["trade_specs_blocked_by_pit"]) != 3689:
            errors.append("Task1120 must record all 3689 rows blocked by PIT")
    if closeout_json.get("replay_executed") != "0":
        errors.append("Task1120 json closeout must record no replay")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1111_1120_PRE_REPLAY_AUDIT_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1111_1120_PRE_REPLAY_AUDIT_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
