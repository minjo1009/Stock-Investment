from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"


REQUIRED = [
    "theme_universe_10x7_contract.csv",
    "full_data_acquisition_audit.csv",
    "intraday_acquisition_audit.csv",
    "daily_canonical_manifest.csv",
    "intraday_15m_canonical_manifest.csv",
    "calendar_certification_manifest.csv",
    "corporate_action_adjustment_manifest.csv",
    "market_data_gate_promotion_result.csv",
    "controlled_trade_specs.csv",
    "controlled_replay_trades.csv",
    "controlled_replay_by_theme.csv",
    "controlled_replay_summary.csv",
    "full_cycle_summary.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors
    contract = rows(ART / "theme_universe_10x7_contract.csv")
    if len(contract) != 10:
        errors.append("theme universe contract must have exactly 10 themes")
    if any(row["symbol_count"] != "7" for row in contract):
        errors.append("each theme must have exactly 7 symbols")
    daily = rows(ART / "daily_canonical_manifest.csv")
    intraday = rows(ART / "intraday_15m_canonical_manifest.csv")
    if len(daily) != 71:
        errors.append("daily canonical manifest must cover 70 universe symbols plus QQQ benchmark")
    if len(intraday) != 71:
        errors.append("intraday canonical manifest must cover 70 universe symbols plus QQQ benchmark")
    if any(row["canonical_status"] != "ok" for row in daily):
        errors.append("all universe and benchmark daily symbols must be canonical ok")
    if any(row["canonical_status"] != "ok" for row in intraday):
        errors.append("all universe and benchmark intraday symbols must be canonical ok")
    promotion = rows(ART / "market_data_gate_promotion_result.csv")[0]
    if promotion["market_data_gate_status"] != "READY_FOR_THEME_UNIVERSE_CONTROLLED_REPLAY_PLAN":
        errors.append("market data gate must be ready for theme universe controlled replay")
    specs = rows(ART / "controlled_trade_specs.csv")
    trades = rows(ART / "controlled_replay_trades.csv")
    if len(specs) != 70:
        errors.append("theme universe replay must produce 70 trade specs")
    if len(trades) != 70:
        errors.append("theme universe replay must produce 70 diagnostic trades")
    by_theme = rows(ART / "controlled_replay_by_theme.csv")
    if len(by_theme) != 10:
        errors.append("replay by-theme summary must have 10 rows")
    summary = rows(ART / "controlled_replay_summary.csv")[0]
    if summary["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic only")
    if summary["real_capital"] != "FORBIDDEN":
        errors.append("real capital must remain forbidden")
    cycle = json.loads((ART / "full_cycle_summary.json").read_text(encoding="utf-8"))
    if cycle.get("theme_count") != 10:
        errors.append("cycle summary must show 10 themes")
    if cycle.get("symbol_count") != 70:
        errors.append("cycle summary must show 70 symbols")
    if cycle.get("trade_count") != 70:
        errors.append("cycle summary must show 70 trades")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_880_THEME_10X7_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_880_THEME_10X7_OK] 10 themes x 7 symbols data and diagnostic replay artifacts validated")


if __name__ == "__main__":
    main()
