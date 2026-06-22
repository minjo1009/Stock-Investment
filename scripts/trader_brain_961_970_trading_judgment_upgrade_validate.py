from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_961_970_trading_judgment_upgrade"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
BASELINE_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"

REQUIRED_FILES = [
    "task961_baseline_weakness_decomposition.csv",
    "task962_thesis_freshness_panel.csv",
    "task963_duplicate_thesis_clusters.csv",
    "task964_independent_evidence_quality.csv",
    "task965_catalyst_validity_expiry.csv",
    "task966_contradiction_severity_panel.csv",
    "task967_thesis_exposure_map.csv",
    "task968_entry_cohort_stability_audit.csv",
    "task969_fresh_duplicate_replay_decisions.csv",
    "task969_fresh_duplicate_replay_trades.csv",
    "task969_fresh_duplicate_replay_equity.csv",
    "task969_fresh_duplicate_replay_summary.csv",
    "task969_fresh_duplicate_replay_summary.json",
    "task970_source_manifest.csv",
    "task970_governance_closeout.csv",
    "task961_970_summary.csv",
    "task961_970_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_DOES_NOT_USE = {
    "future_return",
    "realized_return",
    "pnl",
    "post_entry_price_change",
    "outcome_rank",
}


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

    ready_specs = [
        row for row in rows(SPEC_DIR / "task929_controlled_trade_specs.csv")
        if row["trade_spec_state"] == "ready_for_controlled_replay_plan"
    ]
    spec_ids = {row["trade_spec_id"] for row in ready_specs}
    freshness = rows(ART / "task962_thesis_freshness_panel.csv")
    duplicate = rows(ART / "task963_duplicate_thesis_clusters.csv")
    evidence = rows(ART / "task964_independent_evidence_quality.csv")
    catalyst = rows(ART / "task965_catalyst_validity_expiry.csv")
    contradiction = rows(ART / "task966_contradiction_severity_panel.csv")
    decisions = rows(ART / "task969_fresh_duplicate_replay_decisions.csv")
    trades = rows(ART / "task969_fresh_duplicate_replay_trades.csv")
    equity = rows(ART / "task969_fresh_duplicate_replay_equity.csv")
    replay_summary_rows = rows(ART / "task969_fresh_duplicate_replay_summary.csv")
    source_manifest = rows(ART / "task970_source_manifest.csv")
    closeout = rows(ART / "task970_governance_closeout.csv")
    summary_rows = rows(ART / "task961_970_summary.csv")
    summary = json.loads((ART / "task961_970_summary.json").read_text(encoding="utf-8"))
    baseline = next(row for row in rows(BASELINE_DIR / "task946_slot_capped_summary.csv") if row["slot_cap"] == "10")

    for panel_name, panel in [
        ("freshness", freshness),
        ("duplicate", duplicate),
        ("evidence", evidence),
        ("catalyst", catalyst),
        ("contradiction", contradiction),
    ]:
        panel_ids = {row["trade_spec_id"] for row in panel}
        if panel_ids != spec_ids:
            errors.append(f"{panel_name} panel must cover every ready trade spec")

    for row in freshness:
        if row["leakage_state"] != "pass":
            errors.append("freshness panel contains future evidence")
            break
        if not FORBIDDEN_DOES_NOT_USE <= set(row["does_not_use"].split()):
            errors.append("freshness panel must explicitly exclude future outcome fields")
            break

    decision_ids = {row["trade_spec_id"] for row in decisions}
    if not decision_ids <= spec_ids:
        errors.append("decisions contain ids outside ready trade specs")
    traded_ids = {row["trade_spec_id"] for row in trades}
    selected_ids = {row["trade_spec_id"] for row in decisions if row["selection_state"] == "selected"}
    if not traded_ids <= selected_ids:
        errors.append("traded ids must be selected ids")

    live_clusters_by_day: dict[str, set[str]] = {}
    for row in decisions:
        if row["selection_state"] != "selected":
            continue
        if row["blocked_reason"]:
            errors.append("selected decisions must not carry blocked reasons")
            break
        if row["entry_date"] in live_clusters_by_day and row["thesis_cluster_key"] in live_clusters_by_day[row["entry_date"]]:
            errors.append("duplicate thesis cluster selected twice on same entry date")
            break
        live_clusters_by_day.setdefault(row["entry_date"], set()).add(row["thesis_cluster_key"])

    for row in trades:
        if row["side"] != "long":
            errors.append("replay must remain long-only")
            break
        for key in ["adapter_input_id", "candidate_bundle_id", "trader_decision_id", "source_graph_id"]:
            if not row[key]:
                errors.append(f"trade row missing lineage id {key}")
                break
        if errors and errors[-1].startswith("trade row missing"):
            break
        if float(row["entry_cash_spent"]) <= 0 or float(row["shares"]) <= 0:
            errors.append("trade row must have positive cash spent and shares")
            break

    for row in equity:
        if int(row["open_positions"]) > 10:
            errors.append("open positions exceed slot cap 10")
            break
        cash = float(row["cash"])
        market_value = float(row["open_market_value"])
        total = float(row["equity"])
        if cash < -0.0001:
            errors.append("cash went negative")
            break
        if abs((cash + market_value) - total) > 0.02:
            errors.append("equity must equal cash plus market value")
            break

    if len(replay_summary_rows) != 1:
        errors.append("replay summary must have one row")
    else:
        row = replay_summary_rows[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("replay summary changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("replay summary changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("replay summary changed real capital")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")
        if row["beats_baseline_slot10"] != "0":
            errors.append("Task961-970 should not record a baseline beat")

    if len(summary_rows) != 1:
        errors.append("summary csv must have one row")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary strategy acceptance changed")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary deployment readiness changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary real capital changed")
    if str(summary.get("baseline_slot10_final_equity")) != str(baseline["strategy_final_equity"]):
        errors.append("summary baseline final equity mismatch")
    if summary.get("beats_baseline_slot10") != "0":
        errors.append("summary must record that upgraded replay did not beat baseline slot10")

    for source in source_manifest:
        path = ROOT / source["path"]
        if not path.exists():
            errors.append(f"source manifest path missing: {source['path']}")
            break

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_961_970_TRADING_JUDGMENT_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_961_970_TRADING_JUDGMENT_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
