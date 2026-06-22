from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1151_1160_official_universe_redefinition"
REPORT = ROOT / "docs/reports/task_1151_1160_official_universe_redefinition"

REQUIRED_FILES = [
    "task1151_universe_basis_decision.csv",
    "task1152_official_source_feasibility.csv",
    "task1153_current_sec_exchange_universe.csv",
    "task1154_historical_asof_universe_contract.csv",
    "task1155_decision_calendar.csv",
    "task1156_official_universe_seed_panel.csv",
    "task1157_theme_label_policy.csv",
    "task1158_selection_policy_contract.csv",
    "task1159_official_universe_replay_gate.csv",
    "task1160_official_universe_redefinition_closeout.csv",
    "task1160_official_universe_redefinition_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1151_1160_official_universe_redefinition.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1151_1160_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    basis = rows("task1151_universe_basis_decision.csv")
    feasibility = rows("task1152_official_source_feasibility.csv")
    universe = rows("task1153_current_sec_exchange_universe.csv")
    contract = rows("task1154_historical_asof_universe_contract.csv")
    calendar = rows("task1155_decision_calendar.csv")
    seed = rows("task1156_official_universe_seed_panel.csv")
    theme_policy = rows("task1157_theme_label_policy.csv")
    selection = rows("task1158_selection_policy_contract.csv")
    gate = rows("task1159_official_universe_replay_gate.csv")
    closeout = rows("task1160_official_universe_redefinition_closeout.csv")
    closeout_json = json.loads((ART / "task1160_official_universe_redefinition_closeout.json").read_text(encoding="utf-8"))

    if len(basis) != 1:
        errors.append("basis decision must have one row")
    elif basis[0]["custom_10x7_for_selection_allowed"] != "0":
        errors.append("custom 10x7 must be disallowed as selection basis")

    if len(feasibility) < 4:
        errors.append("source feasibility must cover official source options")
    if not any(row["source_id"] == "sec_bulk_submissions_zip" for row in feasibility):
        errors.append("SEC bulk submissions source must be represented")

    if len(universe) < 9000:
        errors.append("official SEC exchange universe unexpectedly small")
    if any(row["historical_listing_pit_pass"] != "0" for row in universe):
        errors.append("current SEC exchange rows must not pass historical PIT listing")
    if not all(row["source_hash"] for row in universe[:100]):
        errors.append("universe rows must retain source hash")

    required_fields = {row["field"] for row in contract}
    for field in ["symbol", "exchange", "effective_start_ts", "available_to_brain_ts", "pit_membership_pass"]:
        if field not in required_fields:
            errors.append(f"missing contract field {field}")

    if len(calendar) != 63:
        errors.append("decision calendar must cover 63 month-end decisions")
    if len(seed) != len(calendar) * 1000:
        errors.append("seed panel must cover 1000 sample symbols across all decision dates")
    if any(row["eligible_for_brain_selection"] != "0" for row in seed):
        errors.append("seed panel must not allow selection before historical membership is built")

    if len(theme_policy) != 1:
        errors.append("theme policy must have one row")
    elif "preselecting_candidate_symbols" not in theme_policy[0]["forbidden_use"]:
        errors.append("theme policy must forbid candidate preselection")

    if len(selection) != 3:
        errors.append("selection contract must have three ordered steps")
    if any(row["replay_allowed_if_fail"] != "0" for row in selection):
        errors.append("selection contract must block replay on failed prerequisites")

    if len(gate) != 1:
        errors.append("replay gate must have one row")
    else:
        row = gate[0]
        if row["official_universe_replay_ready"] != "0":
            errors.append("official universe replay must remain blocked")
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("gate must not execute replay or promote selection")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["custom_10x7_selection_basis_allowed"] != "0":
            errors.append("closeout must block custom 10x7 selection basis")
        if row["replay_executed"] != "0":
            errors.append("closeout must not execute replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")

    if closeout_json.get("custom_10x7_selection_basis_allowed") != "0":
        errors.append("json closeout must block custom 10x7 selection basis")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1151_1160_OFFICIAL_UNIVERSE_REDEFINITION_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1151_1160_OFFICIAL_UNIVERSE_REDEFINITION_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
