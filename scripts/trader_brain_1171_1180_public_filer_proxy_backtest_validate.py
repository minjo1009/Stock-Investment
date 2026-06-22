from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
REPORT = ROOT / "docs/reports/task_1171_1180_public_filer_proxy_backtest"

REQUIRED_FILES = [
    "task1171_price_download_pool.csv",
    "task1172_yfinance_price_download_ledger.csv",
    "task1173_price_coverage_gate.csv",
    "task1174_public_filer_proxy_feature_panel.csv",
    "task1175_policy_selections.csv",
    "task1176_proxy_backtest_trades.csv",
    "task1176_proxy_backtest_equity.csv",
    "task1177_proxy_backtest_metrics.csv",
    "task1180_public_filer_proxy_backtest_closeout.csv",
    "task1180_public_filer_proxy_backtest_closeout.json",
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
    if not (REPORT / "task_1171_1180_public_filer_proxy_backtest.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1171_1180_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    pool = rows("task1171_price_download_pool.csv")
    download = rows("task1172_yfinance_price_download_ledger.csv")
    coverage = rows("task1173_price_coverage_gate.csv")
    features = rows("task1174_public_filer_proxy_feature_panel.csv")
    selections = rows("task1175_policy_selections.csv")
    trades = rows("task1176_proxy_backtest_trades.csv")
    equity = rows("task1176_proxy_backtest_equity.csv")
    metrics = rows("task1177_proxy_backtest_metrics.csv")
    closeout = rows("task1180_public_filer_proxy_backtest_closeout.csv")
    closeout_json = json.loads((ART / "task1180_public_filer_proxy_backtest_closeout.json").read_text(encoding="utf-8"))

    if len(pool) != 1501:
        errors.append("price pool must contain 1500 strategy symbols plus QQQ")
    if len(download) != len(pool):
        errors.append("download ledger must match price pool")
    if sum(1 for row in download if row["download_status"] == "downloaded") < 500:
        errors.append("downloaded price symbols unexpectedly low")

    if len(coverage) != 1:
        errors.append("coverage gate must have one row")
    elif coverage[0]["price_coverage_pass"] != "1":
        errors.append("price coverage gate must pass for diagnostic replay")

    if len(features) < 1000:
        errors.append("feature panel unexpectedly small")
    if any(row["future_price_used"] != "0" for row in features[:1000]):
        errors.append("feature panel must not use future prices")
    if any(row["future_filing_used"] != "0" for row in features[:1000]):
        errors.append("feature panel must not use future filings")

    variants = {row["policy_variant_id"] for row in metrics}
    expected = {
        "public_filer_proxy_slot3_v1",
        "public_filer_proxy_slot5_v1",
        "public_filer_proxy_slot10_v1",
    }
    if variants != expected:
        errors.append("metrics must cover slot 3 5 and 10 variants")
    if len(selections) <= 0:
        errors.append("selection rows must exist")
    if len(trades) <= 0:
        errors.append("trade rows must exist")
    if len(equity) <= 0:
        errors.append("equity rows must exist")
    if any(row["real_capital"] != "FORBIDDEN" for row in metrics):
        errors.append("metrics must keep real capital forbidden")
    if any(row["strategy_acceptance"] != "NOT_ACCEPTED" for row in metrics):
        errors.append("metrics must keep strategy not accepted")
    if not all(float(row["benchmark_final_equity"]) > 1000 for row in metrics):
        errors.append("benchmark should have positive final equity above initial capital in this window")

    best_metric = max(metrics, key=lambda row: float(row["final_equity"]))
    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["diagnostic_replay_executed"] != "1":
            errors.append("closeout must record diagnostic replay execution")
        if row["selection_promoted"] != "0":
            errors.append("closeout must not promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout real capital changed")
        if row["best_variant"] != best_metric["policy_variant_id"]:
            errors.append("closeout best variant must match metrics")

    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout strategy acceptance changed")
    if closeout_json.get("real_capital") != "FORBIDDEN":
        errors.append("json closeout real capital changed")
    if closeout_json.get("diagnostic_replay_executed") != "1":
        errors.append("json closeout must record diagnostic replay execution")
    if closeout_json.get("selection_promoted") != "0":
        errors.append("json closeout must not promote selection")
    if float(closeout_json.get("best_final_equity", 0)) <= 0:
        errors.append("json closeout must include best final equity")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1171_1180_PUBLIC_FILER_PROXY_BACKTEST_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1171_1180_PUBLIC_FILER_PROXY_BACKTEST_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
