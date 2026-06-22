from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_931_940_controlled_brain_replay"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"

REQUIRED_FILES = [
    "task931_controlled_replay_trades.csv",
    "task932_controlled_replay_equity_curve.csv",
    "task933_controlled_replay_by_split.csv",
    "task934_controlled_replay_by_theme.csv",
    "task935_controlled_replay_skipped_orders.csv",
    "task936_controlled_replay_summary.csv",
    "task936_controlled_replay_summary.json",
    "task937_replay_source_manifest.csv",
    "task940_governance_closeout.csv",
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

    specs = rows(SPEC_DIR / "task929_controlled_trade_specs.csv")
    trades = rows(ART / "task931_controlled_replay_trades.csv")
    equity = rows(ART / "task932_controlled_replay_equity_curve.csv")
    by_split = rows(ART / "task933_controlled_replay_by_split.csv")
    by_theme = rows(ART / "task934_controlled_replay_by_theme.csv")
    skipped = rows(ART / "task935_controlled_replay_skipped_orders.csv")
    manifest = rows(ART / "task937_replay_source_manifest.csv")
    closeout = rows(ART / "task940_governance_closeout.csv")
    summary = json.loads((ART / "task936_controlled_replay_summary.json").read_text(encoding="utf-8"))

    ready_specs = [row for row in specs if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    spec_ids = {row["trade_spec_id"] for row in ready_specs}
    traded_ids = {row["trade_spec_id"] for row in trades}
    skipped_ids = {row["trade_spec_id"] for row in skipped}
    if traded_ids & skipped_ids:
        errors.append("trade spec cannot be both traded and skipped")
    if traded_ids | skipped_ids != spec_ids:
        errors.append("traded plus skipped ids must cover all ready trade specs")

    if not trades:
        errors.append("controlled replay must close at least one trade")
    for row in trades:
        if row["trade_spec_id"] not in spec_ids:
            errors.append("trade row references unknown trade spec")
            break
        if not row["adapter_input_id"] or not row["candidate_bundle_id"] or not row["source_graph_id"]:
            errors.append("trade row missing lineage ids")
            break
        if row["side"] != "long":
            errors.append("replay must remain long-only")
            break
        if float(row["entry_cash_spent"]) <= 0 or float(row["shares"]) <= 0:
            errors.append("trade row must have positive cash spent and shares")
            break
        if row["exit_date"] < row["entry_date"]:
            errors.append("trade exits before entry")
            break
        if row["authority"] != "DIAGNOSTIC_CONTROLLED_BRAIN_REPLAY_ONLY":
            errors.append("trade authority mismatch")
            break

    if not equity:
        errors.append("equity curve empty")
    for row in equity:
        cash = float(row["cash"])
        mv = float(row["open_market_value"])
        total = float(row["equity"])
        if cash < -0.0001:
            errors.append("cash went negative")
            break
        if abs((cash + mv) - total) > 0.02:
            errors.append("equity row does not equal cash plus market value")
            break

    if {row["split_id"] for row in by_split} != {"development_2021_2024", "oos_1_2025", "oos_2_2026_q1"}:
        errors.append("split summary must include development, OOS-1, and OOS-2")
    if len(by_theme) != 10:
        errors.append("theme summary must include 10 themes")

    if len(closeout) != 1:
        errors.append("governance closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED" or row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" or row["real_capital"] != "FORBIDDEN":
            errors.append("governance closeout changed standing statuses")

    for source in manifest:
        path = ROOT / source["path"]
        if not path.exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    expected = {
        "trade_specs_input": len(ready_specs),
        "closed_trades": len(trades),
        "skipped_orders": len(skipped),
        "open_positions_end": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"summary mismatch for {key}: {summary.get(key)} != {value}")

    if summary.get("initial_capital") != 1000.0:
        errors.append("initial capital must be 1000")
    if summary.get("benchmark_symbol") != "QQQ":
        errors.append("benchmark must be QQQ")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary strategy acceptance changed")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary deployment readiness changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary real capital changed")
    if summary.get("strategy_final_equity", 0) <= 0 or summary.get("qqq_final_equity", 0) <= 0:
        errors.append("final equity values must be positive")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_931_940_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_931_940_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
