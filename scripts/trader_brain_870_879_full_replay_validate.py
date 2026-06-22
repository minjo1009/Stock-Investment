from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_870_879_full_controlled_replay"


REQUIRED = [
    "full_data_acquisition_audit.csv",
    "intraday_acquisition_audit.csv",
    "daily_canonical_manifest.csv",
    "intraday_15m_canonical_manifest.csv",
    "calendar_certification_manifest.csv",
    "corporate_action_adjustment_manifest.csv",
    "market_data_gate_promotion_result.csv",
    "controlled_trade_specs.csv",
    "controlled_replay_trades.csv",
    "controlled_replay_summary.csv",
    "full_cycle_summary.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors = []
    for name in REQUIRED:
        p = ART / name
        if not p.exists():
            errors.append(f"missing {name}")
        elif p.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors
    daily = rows(ART / "daily_canonical_manifest.csv")
    intraday = rows(ART / "intraday_15m_canonical_manifest.csv")
    if len(daily) < 16:
        errors.append("daily canonical manifest must cover full explicit harness universe")
    if len(intraday) < 16:
        errors.append("intraday canonical manifest must cover full explicit harness universe")
    if any(row["canonical_status"] != "ok" for row in daily):
        errors.append("all explicit daily symbols must be canonical ok")
    if any(row["canonical_status"] != "ok" for row in intraday):
        errors.append("all explicit intraday symbols must be canonical ok")
    promotion = rows(ART / "market_data_gate_promotion_result.csv")[0]
    if promotion["market_data_gate_status"] != "READY_FOR_CONTROLLED_REPLAY_PLAN":
        errors.append("market data gate must be promoted to READY_FOR_CONTROLLED_REPLAY_PLAN")
    specs = rows(ART / "controlled_trade_specs.csv")
    if not specs:
        errors.append("trade specs must exist")
    needed = {"symbol", "side", "tradable_after_ts", "entry_policy_id", "exit_policy_id", "position_policy_id", "allocated_capital"}
    if not needed.issubset(specs[0].keys()):
        errors.append("trade specs missing required fields")
    trades = rows(ART / "controlled_replay_trades.csv")
    summary = rows(ART / "controlled_replay_summary.csv")[0]
    if int(summary["trade_count"]) != len(trades):
        errors.append("summary trade_count must match trade rows")
    if summary["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    cycle = json.loads((ART / "full_cycle_summary.json").read_text(encoding="utf-8"))
    if cycle.get("symbol_count", 0) < 16:
        errors.append("cycle must cover full explicit universe")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_870_879_FULL_REPLAY_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_870_879_FULL_REPLAY_OK] full explicit-universe data and controlled replay artifacts validated")


if __name__ == "__main__":
    main()
