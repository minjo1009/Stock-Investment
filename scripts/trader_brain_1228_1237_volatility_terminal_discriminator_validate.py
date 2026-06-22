from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
REPORT = ROOT / "docs/reports/task_1228_1237_volatility_terminal_discriminator"

REQUIRED_FILES = [
    "task1228_source_catalog.csv",
    "task1229_l0_instrument_gate.csv",
    "task1230_l1_prior_knowable_signals.csv",
    "task1231_l2_volatility_terminal_discriminator.csv",
    "task1232_l3_route_edges.csv",
    "task1233_policy_specs.csv",
    "task1234_replay_trades.csv",
    "task1234_replay_equity.csv",
    "task1234_replay_metrics.csv",
    "task1235_route_distribution.csv",
    "task1236_acceptance_gate.csv",
    "task1237_closeout.csv",
    "task1237_closeout.json",
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
    if not (REPORT / "task_1228_1237_volatility_terminal_discriminator.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1228_1237_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    sources = rows("task1228_source_catalog.csv")
    instrument = rows("task1229_l0_instrument_gate.csv")
    signals = rows("task1230_l1_prior_knowable_signals.csv")
    discriminator = rows("task1231_l2_volatility_terminal_discriminator.csv")
    edges = rows("task1232_l3_route_edges.csv")
    specs = rows("task1233_policy_specs.csv")
    trades = rows("task1234_replay_trades.csv")
    equity = rows("task1234_replay_equity.csv")
    metrics = rows("task1234_replay_metrics.csv")
    routes = rows("task1235_route_distribution.csv")
    gate = rows("task1236_acceptance_gate.csv")
    closeout = rows("task1237_closeout.csv")
    closeout_json = json.loads((ART / "task1237_closeout.json").read_text(encoding="utf-8"))

    expected = 310
    for name, table in [
        ("instrument", instrument),
        ("signals", signals),
        ("discriminator", discriminator),
        ("edges", edges),
        ("specs", specs),
        ("trades", trades),
    ]:
        if len(table) != expected:
            errors.append(f"{name} must contain {expected} slot5 rows")
    if len(sources) < 12:
        errors.append("source catalog must contain at least 12 rows")
    if sum(1 for row in sources if row["download_status"].startswith("downloaded")) < 9:
        errors.append("at least 9 source rows must be downloaded")
    if len(equity) != 62:
        errors.append("equity must contain 62 monthly rows")
    if len(metrics) != 1 or len(gate) != 1 or len(closeout) != 1:
        errors.append("metrics gate closeout must each contain one row")

    for name, table, field in [
        ("instrument", instrument, "assignment_uses_future_outcome"),
        ("signals", signals, "assignment_uses_future_outcome"),
        ("edges", edges, "assignment_uses_future_outcome"),
        ("specs", specs, "assignment_uses_future_outcome"),
    ]:
        if any(row[field] != "0" for row in table):
            errors.append(f"{name} must not use future outcome for assignment")
    if any(row["outcome_used_for_assignment"] != "0" for row in discriminator):
        errors.append("discriminator must not use outcome for assignment")
    if any(row["volatility_not_penalized_alone"] != "1" for row in discriminator):
        errors.append("volatility-alone penalty must be disabled")
    if any(row["requires_two_independent_distress_evidence"] != "1" for row in discriminator):
        errors.append("distress route must require conjunction")
    if any(row["selection_promoted"] != "0" for row in specs + routes):
        errors.append("policy specs and routes must not promote selection")

    route_names = {row["route"] for row in routes}
    if "high_vol_upside" not in route_names:
        errors.append("route distribution must preserve high_vol_upside")
    if "product_sleeve" not in route_names:
        errors.append("route distribution must preserve product_sleeve")
    if not any(row["volatility_terminal_route"] == "high_vol_upside" and row["position_multiplier"] == "1.0" for row in specs):
        errors.append("high_vol_upside rows must retain full-size eligibility")
    if not any(row["volatility_terminal_route"] == "product_sleeve" and row["position_multiplier"] == "0.25" for row in specs):
        errors.append("product_sleeve rows must be routed small")
    if any(row["exit_reason"] != "scheduled_preserve_upside" for row in specs if row["volatility_terminal_route"] == "high_vol_upside"):
        errors.append("high_vol_upside must not receive tight drawdown stop in this policy")

    metric = metrics[0] if metrics else {}
    if metric.get("policy_variant_id") != "vol_terminal_discriminator_slot5_v1":
        errors.append("metric policy variant mismatch")
    if metric.get("beats_base_slot5") != "1":
        errors.append("volatility-terminal discriminator should beat base slot5 in this diagnostic run")
    if metric.get("beats_benchmark") != "1":
        errors.append("volatility-terminal discriminator should beat QQQ in this diagnostic run")
    if gate and gate[0].get("target_cagr_30pct_pass") != "0":
        errors.append("30pct CAGR target must not be marked as passed")
    if gate and gate[0].get("target_mdd_minus30pct_pass") != "0":
        errors.append("-30pct MDD target must not be marked as passed")
    for table_name, table in [("metrics", metrics), ("gate", gate), ("closeout", closeout)]:
        for row in table:
            if row["strategy_acceptance"] != "NOT_ACCEPTED":
                errors.append(f"{table_name} changed strategy acceptance")
            if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
                errors.append(f"{table_name} changed deployment readiness")
            if row["real_capital"] != "FORBIDDEN":
                errors.append(f"{table_name} changed real capital")
    if closeout_json.get("replay_executed") != "1":
        errors.append("json closeout must record diagnostic replay executed")
    if closeout_json.get("selection_promoted") != "0":
        errors.append("json closeout must keep selection promotion off")
    if closeout_json.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("json closeout changed strategy acceptance")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1228_1237_VOL_TERM_DISCRIMINATOR_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1228_1237_VOL_TERM_DISCRIMINATOR_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
