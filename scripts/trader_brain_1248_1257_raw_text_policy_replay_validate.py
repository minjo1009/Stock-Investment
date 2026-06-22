from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1248_1257_raw_text_policy_replay"
REPORT = ROOT / "docs/reports/task_1248_1257_raw_text_policy_replay"

REQUIRED_FILES = [
    "task1248_policy_catalog.csv",
    "task1249_policy_specs.csv",
    "task1250_replay_trades.csv",
    "task1251_replay_equity.csv",
    "task1252_replay_metrics.csv",
    "task1253_route_attribution.csv",
    "task1254_acceptance_gate.csv",
    "task1255_expert_closeout.csv",
    "task1257_closeout.csv",
    "task1257_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1248_1257_raw_text_policy_replay.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1248_1257_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    policy = rows("task1248_policy_catalog.csv")
    specs = rows("task1249_policy_specs.csv")
    trades = rows("task1250_replay_trades.csv")
    equity = rows("task1251_replay_equity.csv")
    metrics = rows("task1252_replay_metrics.csv")
    attribution = rows("task1253_route_attribution.csv")
    gate = rows("task1254_acceptance_gate.csv")
    expert = rows("task1255_expert_closeout.csv")
    closeout = rows("task1257_closeout.csv")
    closeout_json = json.loads((ART / "task1257_closeout.json").read_text(encoding="utf-8"))

    policies = {row["policy_variant_id"] for row in metrics}
    if len(policies) != 4:
        errors.append("exactly four policy variants must be replayed")
    if len(policy) != 20:
        errors.append("policy catalog must contain five routes for four policies")
    if len(specs) != 1240 or len(trades) != 1240:
        errors.append("specs and trades must cover 310 selections x 4 policies")
    if len(equity) != 248:
        errors.append("equity must contain 62 monthly rows x 4 policies")
    if len(metrics) != 4 or len(gate) != 4:
        errors.append("metrics and gate must contain four rows")
    if not attribution:
        errors.append("route attribution must not be empty")
    if len(expert) < 3:
        errors.append("expert closeout rows missing")

    if any(row["assignment_uses_future_outcome"] != "0" for row in specs):
        errors.append("policy specs must not use outcomes for assignment")
    if any(row["selection_promoted"] != "0" for row in specs + policy + attribution):
        errors.append("selection promotion must stay off")
    if not any(row["terminal_interpretation_route"] == "terminal_distress" and row["position_multiplier"] == "0.0" for row in specs):
        errors.append("strict policy must block terminal_distress rows")
    if not any(row["policy_variant_id"] == "raw_text_shadow_only_slot5_v1" and row["exit_reason"].startswith("raw_text_shadow_only_no_trade_action") for row in specs):
        errors.append("shadow-only policy must preserve Task1228 trade action")
    if not any(row["terminal_interpretation_route"] == "high_vol_upside_raw_not_contradicted" and row["position_multiplier"] == "1.0" for row in specs):
        errors.append("high-vol raw-not-contradicted rows must remain full size somewhere")

    for table_name, table in [("metrics", metrics), ("gate", gate), ("closeout", closeout)]:
        for row in table:
            if row["strategy_acceptance"] != "NOT_ACCEPTED":
                errors.append(f"{table_name} changed strategy acceptance")
            if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{table_name} changed deployment readiness")
            if row["real_capital"] != "FORBIDDEN":
                errors.append(f"{table_name} changed real capital")
    for row in [closeout[0], closeout_json]:
        if str(row.get("replay_executed")) != "1":
            errors.append("closeout must record replay executed")
        if str(row.get("selection_promoted")) != "0":
            errors.append("closeout must not promote selection")
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("json/csv closeout changed strategy acceptance")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1248_1257_RAW_TEXT_POLICY_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1248_1257_RAW_TEXT_POLICY_REPLAY_OK] artifacts validated")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
