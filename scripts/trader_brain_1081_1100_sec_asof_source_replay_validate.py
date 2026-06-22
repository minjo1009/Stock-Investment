from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"

REQUIRED_FILES = [
    "task1081_sec_source_time_audit.csv",
    "task1082_sec_asof_adapter_feature_panel.csv",
    "task1083_sec_asof_selection_ledger.csv",
    "task1084_sec_asof_replay_trades.csv",
    "task1085_sec_asof_equity_curves.csv",
    "task1086_sec_asof_backtest_summary.csv",
    "task1087_sec_asof_attribution.csv",
    "task1100_sec_asof_source_replay_closeout.csv",
    "task1100_sec_asof_source_replay_closeout.json",
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

    audit = rows(ART / "task1081_sec_source_time_audit.csv")
    features = rows(ART / "task1082_sec_asof_adapter_feature_panel.csv")
    summary = rows(ART / "task1086_sec_asof_backtest_summary.csv")
    closeout = rows(ART / "task1100_sec_asof_source_replay_closeout.csv")
    closeout_json = json.loads((ART / "task1100_sec_asof_source_replay_closeout.json").read_text(encoding="utf-8"))

    if len(audit) != 3689:
        errors.append("source-time audit must have 3689 rows")
    if {row["source_time_pass"] for row in audit} != {"1"}:
        errors.append("all SEC source-time audit rows must pass")
    if {row["future_source_rows_used"] for row in audit} != {"0"}:
        errors.append("SEC source-time audit cannot use future source rows")
    if len(features) != 3689:
        errors.append("SEC adapter feature panel must have 3689 rows")
    if {row["source_time_pass"] for row in features} != {"1"}:
        errors.append("SEC adapter feature panel must carry source_time_pass=1")
    if len(summary) != 15:
        errors.append("SEC replay summary must have 15 variants")
    if not any(row["meets_cagr_30"] == "1" for row in summary):
        errors.append("SEC as-of replay should include at least one CAGR>=30 diagnostic variant")
    if any(row["meets_mdd_minus30"] == "1" for row in summary):
        pass

    for row in summary:
        if row["historical_source_time_gap"] != "0":
            errors.append("SEC summary must close historical_source_time_gap for SEC scope")
        if row["non_sec_source_gap"] != "1":
            errors.append("SEC summary must keep non-SEC source gap open")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("summary changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("summary changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("summary changed real capital")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["source_scope"] != "sec_companyfacts_only":
            errors.append("closeout must be SEC-only scope")
        if row["historical_source_time_gap"] != "0":
            errors.append("closeout must close historical_source_time_gap for SEC scope")
        if row["non_sec_source_gap"] != "1":
            errors.append("closeout must keep non-SEC source gap open")
        if row["source_time_pass_rows"] != "3689":
            errors.append("closeout must record 3689 source-time pass rows")
        if row["best_meets_cagr_30"] != "1":
            errors.append("best SEC variant must meet CAGR 30 diagnostic target")
        if row["balanced_meets_cagr_30"] != "1":
            errors.append("balanced SEC variant must meet CAGR 30 diagnostic target")
        if row["best_meets_mdd_minus30"] != "0":
            errors.append("SEC-only best should honestly record MDD target failure")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")

    if closeout_json.get("source_scope") != "sec_companyfacts_only":
        errors.append("json closeout scope mismatch")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")
    if closeout_json.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("json closeout changed deployment readiness")
    if closeout_json.get("real_capital") != "FORBIDDEN":
        errors.append("json closeout changed real capital")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1081_1100_SEC_ASOF_SOURCE_REPLAY_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1081_1100_SEC_ASOF_SOURCE_REPLAY_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
