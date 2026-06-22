from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"

REQUIRED_FILES = [
    "task941_selection_feature_panel.csv",
    "task942_slot_capped_selection_ledger.csv",
    "task943_slot_capped_replay_trades.csv",
    "task944_slot_capped_equity_curves.csv",
    "task945_slot_capped_skipped_orders.csv",
    "task946_slot_capped_summary.csv",
    "task946_slot_capped_summary.json",
    "task947_slot_capped_by_split.csv",
    "task948_slot_capped_source_manifest.csv",
    "task950_slot_capped_governance_closeout.csv",
    "task941_950_summary.json",
    "artifact_manifest.csv",
]

SLOT_CAPS = {3, 5, 10}
FORBIDDEN_SELECTION_TERMS = {"future_return", "realized_return", "pnl", "price_change"}


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
    features = rows(ART / "task941_selection_feature_panel.csv")
    selections = rows(ART / "task942_slot_capped_selection_ledger.csv")
    trades = rows(ART / "task943_slot_capped_replay_trades.csv")
    equity = rows(ART / "task944_slot_capped_equity_curves.csv")
    skipped = rows(ART / "task945_slot_capped_skipped_orders.csv")
    summary_rows = rows(ART / "task946_slot_capped_summary.csv")
    split_rows = rows(ART / "task947_slot_capped_by_split.csv")
    manifest = rows(ART / "task948_slot_capped_source_manifest.csv")
    closeout = rows(ART / "task950_slot_capped_governance_closeout.csv")
    summary = json.loads((ART / "task941_950_summary.json").read_text(encoding="utf-8"))

    if len(features) != len(specs):
        errors.append("selection feature panel must cover each ready trade spec")
    if {int(row["slot_cap"]) for row in summary_rows} != SLOT_CAPS:
        errors.append("summary must contain slot caps 3, 5, and 10")
    if {int(row["slot_cap"]) for row in selections} != SLOT_CAPS:
        errors.append("selection ledger must contain slot caps 3, 5, and 10")
    if any(term not in row["does_not_use"] for row in features for term in FORBIDDEN_SELECTION_TERMS):
        errors.append("selection features must explicitly exclude future outcome terms")

    spec_ids = {row["trade_spec_id"] for row in specs}
    feature_ids = {row["trade_spec_id"] for row in features}
    if feature_ids != spec_ids:
        errors.append("selection feature ids must match trade spec ids")
    selected_by_cap: dict[int, set[str]] = {}
    for cap in SLOT_CAPS:
        selected = {row["trade_spec_id"] for row in selections if int(row["slot_cap"]) == cap and row["selection_state"] == "selected"}
        rejected = {row["trade_spec_id"] for row in selections if int(row["slot_cap"]) == cap and row["selection_state"] == "rejected_by_slot_cap"}
        if selected | rejected != spec_ids:
            errors.append(f"slot cap {cap} selection plus rejection must cover all specs")
        if selected & rejected:
            errors.append(f"slot cap {cap} has spec both selected and rejected")
        selected_by_cap[cap] = selected

    for row in equity:
        cap = int(row["slot_cap"])
        if int(row["open_positions"]) > cap:
            errors.append("open positions exceed slot cap")
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
        cap = int(row["slot_cap"])
        if row["trade_spec_id"] not in selected_by_cap.get(cap, set()):
            errors.append("trade row must come from selected spec for the same slot cap")
            break
        if row["side"] != "long":
            errors.append("slot-capped replay must remain long-only")
            break
        if not row["adapter_input_id"] or not row["candidate_bundle_id"] or not row["source_graph_id"]:
            errors.append("trade row missing lineage ids")
            break
        if float(row["entry_cash_spent"]) <= 0 or float(row["shares"]) <= 0:
            errors.append("trade row must have positive cash and shares")
            break

    for row in summary_rows:
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("summary row changed standing statuses")
        if row["beats_qqq"] not in {"0", "1"} or row["meets_cagr_30"] not in {"0", "1"} or row["meets_mdd_minus30"] not in {"0", "1"}:
            errors.append("target flags must be 0 or 1")
    if len(split_rows) != 9:
        errors.append("split summary must contain three splits for each of three slot caps")
    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed standing statuses")

    for source in manifest:
        path = ROOT / source["path"]
        if not path.exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    if summary.get("input_trade_specs") != len(specs):
        errors.append("summary input trade specs mismatch")
    if summary.get("selection_feature_rows") != len(features):
        errors.append("summary selection feature rows mismatch")
    if summary.get("summary_rows") != 3:
        errors.append("summary row count mismatch")
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
        print("[TRADER_BRAIN_941_950_SLOT_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_941_950_SLOT_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
