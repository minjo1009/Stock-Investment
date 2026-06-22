from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_951_960_conviction_risk_filter_replay"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"

REQUIRED_FILES = [
    "task951_failure_and_target_gap.csv",
    "task952_conviction_price_context_panel.csv",
    "task953_cash_qqq_regime_decision_ledger.csv",
    "task956_conviction_risk_source_manifest.csv",
    "task957_conviction_risk_skipped_orders.csv",
    "task958_conviction_risk_equity_curves.csv",
    "task959_conviction_risk_replay_trades.csv",
    "task959_conviction_risk_replay_summary.csv",
    "task959_conviction_risk_replay_summary.json",
    "task960_conviction_risk_governance_closeout.csv",
    "task951_960_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_DOES_NOT_USE = {"future_return", "realized_return", "pnl", "price_change"}


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

    specs = [row for row in rows(SPEC_DIR / "task929_controlled_trade_specs.csv") if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    features = rows(ART / "task952_conviction_price_context_panel.csv")
    decisions = rows(ART / "task953_cash_qqq_regime_decision_ledger.csv")
    equity = rows(ART / "task958_conviction_risk_equity_curves.csv")
    trades = rows(ART / "task959_conviction_risk_replay_trades.csv")
    summary_rows = rows(ART / "task959_conviction_risk_replay_summary.csv")
    source_manifest = rows(ART / "task956_conviction_risk_source_manifest.csv")
    closeout = rows(ART / "task960_conviction_risk_governance_closeout.csv")
    summary = json.loads((ART / "task951_960_summary.json").read_text(encoding="utf-8"))

    spec_ids = {row["trade_spec_id"] for row in specs}
    if len(features) != len(specs):
        errors.append("feature panel must cover every ready trade spec")
    if {row["trade_spec_id"] for row in features} != spec_ids:
        errors.append("feature trade_spec ids must match ready specs")
    for row in features:
        if not FORBIDDEN_DOES_NOT_USE <= set(row["does_not_use"].split()):
            errors.append("features must explicitly exclude future outcome fields")
            break
        if row["price_context_rule"] != "uses_prior_session_only_no_future_price":
            errors.append("price context must use prior-session-only rule")
            break

    policy_ids = {row["policy_id"] for row in summary_rows}
    if len(policy_ids) < 3:
        errors.append("must test at least three diagnostic policies")
    for policy_id in policy_ids:
        policy_decisions = [row for row in decisions if row["policy_id"] == policy_id]
        decision_ids = {row["trade_spec_id"] for row in policy_decisions}
        if decision_ids != spec_ids:
            errors.append(f"policy {policy_id} decisions must cover every spec")
        selected = {row["trade_spec_id"] for row in policy_decisions if row["selection_state"] == "selected"}
        traded = {row["trade_spec_id"] for row in trades if row["policy_id"] == policy_id}
        if not traded <= selected:
            errors.append(f"policy {policy_id} traded ids must be selected ids")

    for row in equity:
        if int(row["open_positions"]) > 10:
            errors.append("open positions exceed hard base slot cap 10")
            break
        if int(row["open_positions"]) > int(row["active_slot_cap"]) and int(row["entries_selected"]) != 0:
            errors.append("active throttle exceeded while still adding entries")
            break
        cash = float(row["cash"])
        mv = float(row["open_market_value"])
        total = float(row["equity"])
        if cash < -0.0001:
            errors.append("cash went negative")
            break
        if abs((cash + mv) - total) > 0.02:
            errors.append("equity must equal cash plus market value")
            break

    for row in trades:
        if row["side"] != "long":
            errors.append("replay must remain long-only")
            break
        if not row["adapter_input_id"] or not row["candidate_bundle_id"] or not row["source_graph_id"]:
            errors.append("trade row missing lineage ids")
            break
        if float(row["entry_cash_spent"]) <= 0 or float(row["shares"]) <= 0:
            errors.append("trade row must have positive cash spent and shares")
            break

    for row in summary_rows:
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("summary row changed standing statuses")
        if row["meets_cagr_30"] not in {"0", "1"} or row["meets_mdd_minus30"] not in {"0", "1"} or row["beats_qqq"] not in {"0", "1"}:
            errors.append("target flags must be 0/1")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed standing statuses")
        if row["best_policy_beats_baseline_slot10"] != "0":
            errors.append("Task951-960 should explicitly show no policy beat the Task941-950 slot10 baseline")

    for source in source_manifest:
        path = ROOT / source["path"]
        if not path.exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    if summary.get("input_trade_specs") != len(specs):
        errors.append("summary input trade spec count mismatch")
    if summary.get("tested_policy_count") != len(policy_ids):
        errors.append("summary tested policy count mismatch")
    if summary.get("best_policy_beats_baseline_slot10") != "0":
        errors.append("summary must record that best policy did not beat baseline slot10")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary strategy acceptance changed")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary deployment readiness changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary real capital changed")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_951_960_CONVICTION_RISK_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_951_960_CONVICTION_RISK_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
