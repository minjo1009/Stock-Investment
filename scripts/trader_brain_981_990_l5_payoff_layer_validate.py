from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_981_990_l5_payoff_layer"
RANKING_PATH = ROOT / "data/artifacts/task_961_970_external_audit_redesign/task969_shadow_trader_ranking.csv"

REQUIRED_FILES = [
    "task981_l5_source_context_manifest.csv",
    "task982_l5_layer_contract.csv",
    "task983_l5a_reflectedness_panel.csv",
    "task984_l5b_payoff_shape_panel.csv",
    "task985_l5c_motion_timing_panel.csv",
    "task986_l5d_best_expression_panel.csv",
    "task987_l5e_portfolio_risk_budget_panel.csv",
    "task988_l5v_validation_guard_panel.csv",
    "task989_baseline_shadow_gap_evaluation_only.csv",
    "task990_l5_payoff_layer_closeout.csv",
    "task981_990_summary.csv",
    "task981_990_summary.json",
    "artifact_manifest.csv",
]
FEATURE_PANELS = [
    "task983_l5a_reflectedness_panel.csv",
    "task984_l5b_payoff_shape_panel.csv",
    "task985_l5c_motion_timing_panel.csv",
    "task986_l5d_best_expression_panel.csv",
    "task987_l5e_portfolio_risk_budget_panel.csv",
    "task988_l5v_validation_guard_panel.csv",
]
FORBIDDEN_COLUMNS = {
    "pnl",
    "return_pct",
    "future_return",
    "realized_return",
    "post_entry_price_change",
    "outcome_rank",
    "exit_price",
}
FORBIDDEN_INPUTS = {
    "future_return",
    "realized_return",
    "pnl",
    "post_entry_price_change",
    "outcome_rank",
    "exit_price",
}
REQUIRED_LAYERS = {"L5-A", "L5-B", "L5-C", "L5-D", "L5-E", "L5-V"}


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

    ranking = rows(RANKING_PATH)
    ranking_ids = {row["trade_spec_id"] for row in ranking}
    source_context = rows(ART / "task981_l5_source_context_manifest.csv")
    contract = rows(ART / "task982_l5_layer_contract.csv")
    guard = rows(ART / "task988_l5v_validation_guard_panel.csv")
    gap_eval = rows(ART / "task989_baseline_shadow_gap_evaluation_only.csv")
    closeout = rows(ART / "task990_l5_payoff_layer_closeout.csv")
    summary = json.loads((ART / "task981_990_summary.json").read_text(encoding="utf-8"))

    source_layers = {row["layer_id"] for row in source_context}
    if not REQUIRED_LAYERS <= source_layers:
        errors.append("source context must cover every L5 layer")
    for row in source_context:
        if row["use_mode"] != "research_context_only_not_source_of_trade_truth":
            errors.append("source context use mode must be research-only")
            break

    contract_layers = {row["layer_id"] for row in contract}
    if not REQUIRED_LAYERS <= contract_layers:
        errors.append("contract must cover every L5 layer")
    for row in contract:
        if "no_replay" not in row["perfect_done_condition"] and row["layer_id"].startswith("L5"):
            errors.append("contract must encode no-replay completion condition")
            break

    for panel_name in FEATURE_PANELS:
        panel_rows = rows(ART / panel_name)
        ids = {row["trade_spec_id"] for row in panel_rows}
        if ids != ranking_ids:
            errors.append(f"{panel_name} must cover Task969 ranking ids 1:1")
        fieldnames = set(panel_rows[0].keys()) if panel_rows else set()
        if FORBIDDEN_COLUMNS & fieldnames:
            errors.append(f"{panel_name} contains forbidden outcome columns")
        for row in panel_rows:
            if "forbidden_inputs" in row and not FORBIDDEN_INPUTS <= set(row["forbidden_inputs"].split()):
                errors.append(f"{panel_name} forbidden_inputs incomplete")
                break
            if "use_mode" in row and not row["use_mode"].startswith("diagnostic_feature_only"):
                errors.append(f"{panel_name} use_mode must be diagnostic_feature_only")
                break

    for row in guard:
        if row["feature_time_state"] == "pass" and not (row["max_price_timestamp_used"] < row["entry_date"]):
            errors.append("guard has pass row using entry-date or future price")
            break
        if row["selection_use_allowed"] != "0":
            errors.append("L5 feature rows must not be direct selection inputs")
            break
        if row["replay_executed"] != "0":
            errors.append("L5 builder must not execute replay")
            break

    for row in gap_eval:
        if row["evaluation_use_mode"] != "post_replay_failure_decomposition_only_never_selection_input":
            errors.append("gap evaluation PnL must be evaluation-only")
            break

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0":
            errors.append("closeout must record no replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")

    if summary.get("replay_executed") != "0":
        errors.append("summary must record no replay")
    if int(summary.get("input_ranking_rows", -1)) != len(ranking):
        errors.append("summary input row count mismatch")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary changed strategy acceptance")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary changed deployment readiness")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary changed real capital")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_981_990_L5_PAYOFF_LAYER_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_981_990_L5_PAYOFF_LAYER_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
