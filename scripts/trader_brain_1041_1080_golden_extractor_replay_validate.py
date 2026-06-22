from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1041_1080_golden_extractor_replay"

REQUIRED_FILES = [
    "task1041_gpt_expert_plan_synthesis.csv",
    "task1042_extractor_contract.csv",
    "task1043_extractor_golden_match.csv",
    "task1044_expanded_stress_input_set.csv",
    "task1045_golden_brain_adapter_feature_panel.csv",
    "task1046_golden_brain_selection_ledger.csv",
    "task1047_golden_brain_replay_trades.csv",
    "task1048_golden_brain_equity_curves.csv",
    "task1049_golden_brain_skipped_orders.csv",
    "task1050_golden_brain_backtest_summary.csv",
    "task1051_golden_brain_attribution.csv",
    "task1052_golden_risk_overlay_selection_ledger.csv",
    "task1053_golden_risk_overlay_replay_trades.csv",
    "task1054_golden_risk_overlay_equity_curves.csv",
    "task1055_golden_risk_overlay_summary.csv",
    "task1080_golden_extractor_replay_closeout.csv",
    "task1080_golden_extractor_replay_closeout.json",
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
        elif path.stat().st_size == 0 and name != "task1049_golden_brain_skipped_orders.csv":
            errors.append(f"empty {name}")
    if errors:
        return errors

    expert = rows(ART / "task1041_gpt_expert_plan_synthesis.csv")
    extracted = rows(ART / "task1042_extractor_contract.csv")
    match = rows(ART / "task1043_extractor_golden_match.csv")
    stress = rows(ART / "task1044_expanded_stress_input_set.csv")
    features = rows(ART / "task1045_golden_brain_adapter_feature_panel.csv")
    base_summary = rows(ART / "task1050_golden_brain_backtest_summary.csv")
    risk_summary = rows(ART / "task1055_golden_risk_overlay_summary.csv")
    closeout = rows(ART / "task1080_golden_extractor_replay_closeout.csv")
    closeout_json = json.loads((ART / "task1080_golden_extractor_replay_closeout.json").read_text(encoding="utf-8"))

    if len(expert) != 10:
        errors.append("expert synthesis must include 10 reviewer roles")
    if len(extracted) != 20:
        errors.append("extractor contract must include 20 golden cases")
    if len(match) != 20 or any(row["match_state"] != "pass" for row in match):
        errors.append("all 20 golden extractor matches must pass")
    if len(stress) != 200:
        errors.append("expanded stress input set must have 200 rows")
    if len(features) != 3689:
        errors.append("adapter feature panel must have 3689 rows")
    if {row["historical_source_time_gap"] for row in features} != {"1"}:
        errors.append("feature panel must explicitly carry historical source-time gap")

    if {row["slot_cap"] for row in base_summary} != {"3", "5", "10"}:
        errors.append("base replay must test slot caps 3,5,10")
    if not any(row["meets_cagr_30"] == "1" for row in base_summary):
        errors.append("base replay should record whether any variant meets CAGR 30")
    if len(risk_summary) != 8:
        errors.append("risk overlay must include 8 preconfigured variants")
    if not any(row["meets_cagr_30"] == "1" for row in risk_summary):
        errors.append("risk overlay must include at least one CAGR>=30 diagnostic variant")

    all_summary_rows = base_summary + risk_summary
    for row in all_summary_rows:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("summary changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("summary changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("summary changed real capital")
        if row["historical_source_time_gap"] != "1":
            errors.append("summary must report historical source-time gap")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "1":
            errors.append("closeout must record diagnostic replay execution")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")
        if row["historical_source_time_gap"] != "1":
            errors.append("closeout must record historical source-time gap")
        if row["risk_overlay_best_meets_cagr_30"] != "1":
            errors.append("risk overlay best must meet CAGR 30 diagnostic target")

    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")
    if closeout_json.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("json closeout changed deployment readiness")
    if closeout_json.get("real_capital") != "FORBIDDEN":
        errors.append("json closeout changed real capital")
    if closeout_json.get("historical_source_time_gap") != "1":
        errors.append("json closeout must record historical source-time gap")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1041_1080_GOLDEN_EXTRACTOR_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1041_1080_GOLDEN_EXTRACTOR_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
