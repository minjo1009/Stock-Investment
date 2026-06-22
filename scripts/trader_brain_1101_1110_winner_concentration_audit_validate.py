from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1101_1110_winner_concentration_audit"

REQUIRED_FILES = [
    "task1101_winner_concentration_summary.csv",
    "task1102_symbol_pnl_contribution.csv",
    "task1103_selected_score_stability.csv",
    "task1104_full_feature_score_stability.csv",
    "task1105_universe_pit_audit.csv",
    "task1110_winner_concentration_closeout.csv",
    "task1110_winner_concentration_closeout.json",
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

    summary = rows(ART / "task1101_winner_concentration_summary.csv")
    symbols = rows(ART / "task1102_symbol_pnl_contribution.csv")
    stability = rows(ART / "task1103_selected_score_stability.csv")
    universe = rows(ART / "task1105_universe_pit_audit.csv")
    closeout = rows(ART / "task1110_winner_concentration_closeout.csv")
    closeout_json = json.loads((ART / "task1110_winner_concentration_closeout.json").read_text(encoding="utf-8"))

    if len(summary) != 1:
        errors.append("summary must have one row")
    else:
        row = summary[0]
        if row["verdict"] != "winner_basket_concentration_confirmed":
            errors.append("winner concentration verdict must be confirmed")
        if int(row["selected_symbols"]) > 10:
            errors.append("selected symbol count unexpectedly broad")
        if float(row["top3_pnl_share_pct"]) < 80.0:
            errors.append("top3 PnL share must confirm concentration")
        if row["pit_universe_gap"] != "1":
            errors.append("PIT universe gap must be recorded")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("summary changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("summary changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("summary changed real capital")

    if len(symbols) != 6:
        errors.append("audited winner variant should have 6 selected symbols")
    top3 = ";".join(row["symbol"] for row in symbols[:3])
    if top3 != "ASTS;VRT;ARM":
        errors.append(f"unexpected top3 symbols {top3}")
    if {row["static_score_flag"] for row in stability} != {"1"}:
        errors.append("all selected symbols should have static selected scores")
    if len(universe) != 1 or universe[0]["has_point_in_time_columns"] != "0":
        errors.append("universe PIT audit must record missing PIT columns")
    if len(closeout) != 1:
        errors.append("closeout must have one row")
    if closeout_json.get("verdict") != "winner_basket_concentration_confirmed":
        errors.append("json closeout verdict mismatch")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1101_1110_WINNER_CONCENTRATION_AUDIT_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1101_1110_WINNER_CONCENTRATION_AUDIT_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
