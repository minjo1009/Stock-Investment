from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1288_1297_multisource_policy_replay"
REPORT = ROOT / "docs/reports/task_1288_1297_multisource_policy_replay"

REQUIRED_FILES = [
    "task1288_policy_catalog.csv",
    "task1289_policy_specs.csv",
    "task1290_replay_trades.csv",
    "task1291_replay_equity.csv",
    "task1292_replay_metrics.csv",
    "task1293_multisource_attribution.csv",
    "task1294_acceptance_gate.csv",
    "task1297_closeout.csv",
    "task1297_closeout.json",
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
    if not (REPORT / "task_1288_1297_multisource_policy_replay.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1288_1297_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    catalog = rows("task1288_policy_catalog.csv")
    specs = rows("task1289_policy_specs.csv")
    trades = rows("task1290_replay_trades.csv")
    equity = rows("task1291_replay_equity.csv")
    metrics = rows("task1292_replay_metrics.csv")
    attribution = rows("task1293_multisource_attribution.csv")
    gate = rows("task1294_acceptance_gate.csv")
    closeout = rows("task1297_closeout.csv")
    closeout_json = json.loads((ART / "task1297_closeout.json").read_text(encoding="utf-8"))

    if len({row["policy_variant_id"] for row in metrics}) != 4:
        errors.append("must replay four policy variants")
    if len(catalog) != 24:
        errors.append("policy catalog must contain six interpretations x four policies")
    if len(specs) != 1240 or len(trades) != 1240:
        errors.append("specs and trades must cover 310 selections x four policies")
    if len(equity) != 248:
        errors.append("equity must contain 62 monthly rows x four policies")
    if len(metrics) != 4 or len(gate) != 4:
        errors.append("metrics and acceptance gate must contain four rows")
    if not attribution:
        errors.append("attribution must not be empty")
    if any(row["assignment_uses_future_outcome"] != "0" for row in specs):
        errors.append("policy specs must not use future outcome assignment")
    if any(row["selection_promoted"] != "0" for row in catalog + specs + attribution + gate):
        errors.append("selection promotion must stay off")
    if not any(row["enhanced_composite_interpretation"] == "validated_growth_multisource_confirmed" for row in specs):
        errors.append("validated growth interpretation must appear in specs")
    for table_name, table in [("metrics", metrics), ("closeout", closeout)]:
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
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1288_1297_MULTISOURCE_POLICY_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1288_1297_MULTISOURCE_POLICY_REPLAY_OK] artifacts validated")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
