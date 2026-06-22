from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_991_1000_l5_policy_replay"
RANKING_PATH = ROOT / "data/artifacts/task_961_970_external_audit_redesign/task969_shadow_trader_ranking.csv"

REQUIRED_FILES = [
    "task991_l5_expert_policy_freeze.csv",
    "task992_pre_registered_l5_policy.csv",
    "task993_l5_policy_selection_ledger.csv",
    "task994_l5_replay_entry_decision_ledger.csv",
    "task995_l5_replay_trades.csv",
    "task996_l5_replay_equity.csv",
    "task997_l5_skipped_orders.csv",
    "task998_l5_replay_summary.csv",
    "task998_l5_replay_summary.json",
    "task999_l5_replay_by_split.csv",
    "task999_l5_vs_task941_attribution.csv",
    "task999_l5_bucket_attribution_evaluation_only.csv",
    "task999_l5_tail_trades_evaluation_only.csv",
    "task1000_l5_policy_source_manifest.csv",
    "task1000_l5_policy_governance_closeout.csv",
    "task991_1000_summary.csv",
    "task991_1000_summary.json",
    "artifact_manifest.csv",
]
FORBIDDEN_SELECTION_COLUMNS = {
    "pnl",
    "return_pct",
    "future_return",
    "realized_return",
    "post_entry_price_change",
    "outcome_rank",
    "exit_price",
    "exit_adj_close",
}
FORBIDDEN_INPUTS = {
    "future_return",
    "realized_return",
    "pnl",
    "post_entry_price_change",
    "outcome_rank",
    "exit_price",
}


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
    policy = rows(ART / "task992_pre_registered_l5_policy.csv")
    selection = rows(ART / "task993_l5_policy_selection_ledger.csv")
    entry = rows(ART / "task994_l5_replay_entry_decision_ledger.csv")
    trades = rows(ART / "task995_l5_replay_trades.csv")
    equity = rows(ART / "task996_l5_replay_equity.csv")
    attribution = rows(ART / "task999_l5_vs_task941_attribution.csv")
    buckets = rows(ART / "task999_l5_bucket_attribution_evaluation_only.csv")
    tails = rows(ART / "task999_l5_tail_trades_evaluation_only.csv")
    closeout = rows(ART / "task1000_l5_policy_governance_closeout.csv")
    summary = json.loads((ART / "task991_1000_summary.json").read_text(encoding="utf-8"))

    if len(policy) != 1 or policy[0]["pre_registered_before_replay"] != "1":
        errors.append("policy must be pre-registered before replay")
    elif not FORBIDDEN_INPUTS <= set(policy[0]["forbidden_inputs"].split()):
        errors.append("policy forbidden inputs incomplete")

    selection_ids = {row["trade_spec_id"] for row in selection}
    if selection_ids != ranking_ids:
        errors.append("selection ledger must cover Task969 ranking ids 1:1")
    if selection:
        if FORBIDDEN_SELECTION_COLUMNS & set(selection[0].keys()):
            errors.append("selection ledger contains forbidden outcome columns")
    for row in selection:
        if not FORBIDDEN_INPUTS <= set(row["forbidden_inputs"].split()):
            errors.append("selection forbidden inputs incomplete")
            break
        if row["selection_state"] == "selected" and row["trader_action"] == "hard_block":
            errors.append("hard block row selected")
            break
        if row["selection_state"] == "selected" and row["feature_time_state"] != "pass":
            errors.append("non-pass L5V row selected")
            break

    selected_by_entry: dict[str, int] = {}
    for row in selection:
        if row["selection_state"] == "selected":
            selected_by_entry[row["entry_date"]] = selected_by_entry.get(row["entry_date"], 0) + 1
    if any(count > 10 for count in selected_by_entry.values()):
        errors.append("preselected entries exceed slot cap 10 for an entry date")

    entered_ids = {row["trade_spec_id"] for row in entry if row["entry_decision_state"] == "entered"}
    trade_ids = {row["trade_spec_id"] for row in trades}
    if trade_ids != entered_ids:
        errors.append("closed trade ids must match entered decision ids")
    if not equity:
        errors.append("equity curve missing")

    if len(attribution) != 1:
        errors.append("attribution must have one row")
    else:
        row = attribution[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("attribution changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("attribution changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("attribution changed real capital")

    for row in buckets + tails:
        if row["evaluation_use_mode"] != "post_replay_failure_decomposition_only_never_selection_input":
            errors.append("failure decomposition must be evaluation-only")
            break

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")

    if int(summary.get("input_ranking_rows", -1)) != len(ranking):
        errors.append("summary input row count mismatch")
    if int(summary.get("closed_trades", -1)) != len(trades):
        errors.append("summary closed trade count mismatch")
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
        print("[TRADER_BRAIN_991_1000_L5_POLICY_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_991_1000_L5_POLICY_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
