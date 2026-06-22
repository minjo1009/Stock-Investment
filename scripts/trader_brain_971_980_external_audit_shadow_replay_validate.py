from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_971_980_external_audit_shadow_replay"
RANKING_PATH = ROOT / "data/artifacts/task_961_970_external_audit_redesign/task969_shadow_trader_ranking.csv"
SPEC_PATH = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv"
BASELINE_SUMMARY_PATH = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay/task946_slot_capped_summary.csv"

POLICY_ID = "slot10_external_audit_shadow_rank_v1"
REQUIRED_FILES = [
    "task971_expert_review_and_policy_freeze.csv",
    "task972_pre_registered_policy.csv",
    "task973_policy_selection_ledger.csv",
    "task974_replay_entry_decision_ledger.csv",
    "task975_replay_trades.csv",
    "task976_replay_equity.csv",
    "task977_skipped_orders.csv",
    "task978_replay_summary.csv",
    "task978_replay_summary.json",
    "task979_by_split.csv",
    "task979_baseline_shadow_attribution.csv",
    "task980_source_manifest.csv",
    "task980_governance_closeout.csv",
    "task971_980_summary.csv",
    "task971_980_summary.json",
    "artifact_manifest.csv",
]
FORBIDDEN_OUTCOME_INPUTS = {
    "future_return",
    "realized_return",
    "pnl",
    "post_entry_price_change",
    "outcome_rank",
}
ALLOWED_HARD_BLOCK_REASONS = {
    "future_evidence",
    "missing_required_lineage",
    "source_backed_invalidation",
}
ACTION_PRIORITY = {"enter": 0, "monitor": 1, "wait": 2}


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
    specs = [row for row in rows(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    spec_ids = {row["trade_spec_id"] for row in specs}
    policy_rows = rows(ART / "task972_pre_registered_policy.csv")
    selection = rows(ART / "task973_policy_selection_ledger.csv")
    entry_decisions = rows(ART / "task974_replay_entry_decision_ledger.csv")
    trades = rows(ART / "task975_replay_trades.csv")
    equity = rows(ART / "task976_replay_equity.csv")
    replay_summary_rows = rows(ART / "task978_replay_summary.csv")
    comparison_rows = rows(ART / "task979_baseline_shadow_attribution.csv")
    closeout_rows = rows(ART / "task980_governance_closeout.csv")
    source_manifest = rows(ART / "task980_source_manifest.csv")
    summary = json.loads((ART / "task971_980_summary.json").read_text(encoding="utf-8"))
    baseline = next(row for row in rows(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")

    if len(policy_rows) != 1:
        errors.append("pre-registered policy must have one row")
    else:
        policy = policy_rows[0]
        if policy["policy_id"] != POLICY_ID:
            errors.append("unexpected policy id")
        if policy["pre_registered_before_replay"] != "1":
            errors.append("policy must be pre-registered before replay")
        if not FORBIDDEN_OUTCOME_INPUTS <= set(policy["forbidden_inputs"].split()):
            errors.append("policy forbidden inputs incomplete")

    ranking_ids = {row["trade_spec_id"] for row in ranking}
    selection_ids = {row["trade_spec_id"] for row in selection}
    if selection_ids != ranking_ids:
        errors.append("selection ledger must cover every shadow ranking row")
    if not selection_ids <= spec_ids:
        errors.append("selection ids must exist in ready trade specs")

    selected_by_date: dict[str, list[dict[str, str]]] = {}
    for row in selection:
        if row["policy_id"] != POLICY_ID:
            errors.append("selection row has unexpected policy id")
            break
        if not FORBIDDEN_OUTCOME_INPUTS <= set(row["does_not_use"].split()):
            errors.append("selection row does_not_use incomplete")
            break
        if row["selection_state"] == "hard_blocked":
            reason = row["blocked_reason"]
            if reason not in ALLOWED_HARD_BLOCK_REASONS and reason != "hard_block_from_pre_registered_shadow_input":
                errors.append("selection hard block reason not allowed")
                break
        if row["selection_state"] == "selected":
            selected_by_date.setdefault(row["entry_date"], []).append(row)
    for day, group in selected_by_date.items():
        if len(group) > 10:
            errors.append(f"preselected rows exceed slot10 on {day}")
            break
        ranked = sorted(group, key=lambda row: (-int(row["shadow_rank_score"]), ACTION_PRIORITY.get(row["trader_action"], 99), row["theme"], row["symbol"], row["trade_spec_id"]))
        if [row["trade_spec_id"] for row in group] != [row["trade_spec_id"] for row in ranked]:
            errors.append(f"selected rows are not in frozen order on {day}")
            break

    entered_ids = {row["trade_spec_id"] for row in entry_decisions if row["entry_decision_state"] == "entered"}
    deferred_ids = {row["trade_spec_id"] for row in entry_decisions if row["entry_decision_state"] == "deferred_by_live_slot_cap"}
    if entered_ids & deferred_ids:
        errors.append("entry decision cannot both enter and defer same trade_spec_id")
    traded_ids = {row["trade_spec_id"] for row in trades}
    if traded_ids != entered_ids:
        errors.append("traded ids must match entered decision ids")

    for row in trades:
        if row["side"] != "long":
            errors.append("replay must remain long-only")
            break
        for key in ["adapter_input_id", "candidate_bundle_id", "trader_decision_id", "source_graph_id"]:
            if not row[key]:
                errors.append(f"trade row missing lineage {key}")
                break
        if errors and errors[-1].startswith("trade row missing"):
            break
        if float(row["entry_cash_spent"]) <= 0 or float(row["shares"]) <= 0:
            errors.append("trade cash and shares must be positive")
            break

    for row in equity:
        if int(row["open_positions"]) > 10:
            errors.append("open positions exceed slot10")
            break
        cash = float(row["cash"])
        market_value = float(row["open_market_value"])
        total = float(row["equity"])
        if cash < -0.0001:
            errors.append("cash went negative")
            break
        if abs((cash + market_value) - total) > 0.02:
            errors.append("equity must equal cash plus market value")
            break

    if len(replay_summary_rows) != 1:
        errors.append("replay summary must have one row")
    else:
        replay = replay_summary_rows[0]
        if replay["policy_id"] != POLICY_ID:
            errors.append("summary policy id mismatch")
        if int(replay["policy_preselected_entries"]) != sum(1 for row in selection if row["selection_state"] == "selected"):
            errors.append("summary preselected count mismatch")
        if int(replay["selected_entries"]) != len(entered_ids):
            errors.append("summary selected entries mismatch")
        if int(replay["closed_trades"]) != len(trades):
            errors.append("summary closed trades mismatch")
        if replay["strategy_acceptance"] != "NOT_ACCEPTED" or replay["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or replay["real_capital"] != "FORBIDDEN":
            errors.append("replay summary changed standing statuses")

    if len(comparison_rows) != 1:
        errors.append("comparison must have one row")
    else:
        comp = comparison_rows[0]
        if comp["baseline_final_equity"] != baseline["strategy_final_equity"]:
            errors.append("baseline final equity mismatch")
        if comp["strategy_acceptance"] != "NOT_ACCEPTED" or comp["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or comp["real_capital"] != "FORBIDDEN":
            errors.append("comparison changed standing statuses")

    if len(closeout_rows) != 1:
        errors.append("closeout must have one row")
    else:
        closeout = closeout_rows[0]
        if closeout["strategy_acceptance"] != "NOT_ACCEPTED" or closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or closeout["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed standing statuses")

    if summary.get("policy_id") != POLICY_ID:
        errors.append("json summary policy id mismatch")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json summary changed strategy acceptance")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("json summary changed deployment readiness")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("json summary changed real capital")

    for source in source_manifest:
        if not (ROOT / source["path"]).exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_971_980_EXTERNAL_AUDIT_SHADOW_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_971_980_EXTERNAL_AUDIT_SHADOW_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
