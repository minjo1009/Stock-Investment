from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
REPORT = ROOT / "docs/reports/task_1931_1940_interaction_forecast_layer/task_1931_1940_interaction_forecast_layer.md"
DECISION = ROOT / "docs/reports/task_1931_1940_interaction_forecast_layer/task_1931_1940_decision.csv"
AUTHORITY = "DIAGNOSTIC_INTERACTION_FORECAST_LAYER_ONLY"

REQUIRED_COUNTS = {
    "task1931_interaction_primitive_schema.csv": 10,
    "task1932_event_window_absorption_panel.csv": 377,
    "task1933_sector_breadth_source_field.csv": 310,
    "task1934_sec_financing_specificity_parser.csv": 377,
    "task1935_l4_interaction_payoff_thesis_cards.csv": 377,
    "task1936_source_independence_contract.csv": 377,
    "task1937_negative_fixture_pack.csv": 8,
    "task1938_interaction_top3_replay_trades.csv": 160,
    "task1938_interaction_top3_replay_equity.csv": 61,
    "task1938_interaction_top3_replay_metrics.csv": 1,
    "task1938_split_oos_metrics.csv": 2,
    "task1938_cost_stress_metrics.csv": 4,
    "task1939_top5_expansion_gate.csv": 217,
    "task1940_acceptance_gate.csv": 1,
    "task1940_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_COUNTS:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "task1940_failure_attribution.csv").exists(), "missing failure attribution")
    fail_if(not (OUT_DIR / "task1940_closeout.json").exists(), "missing closeout json")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} rows got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment")


def validate_schema_and_fixtures() -> None:
    schema = read_csv(OUT_DIR / "task1931_interaction_primitive_schema.csv")
    primitives = {row["primitive_name"] for row in schema}
    for primitive in [
        "price_accepts_surprise",
        "financing_risk_overrides_growth",
        "breadth_confirms_leadership",
        "quality_defends_volatility",
        "expectation_gap_expands_payoff",
    ]:
        fail_if(primitive not in primitives, f"missing primitive {primitive}")
    fail_if(any("pnl" not in row["forbidden_input_fields"] for row in schema), "schema missing pnl forbidden field")
    fixtures = {row["fixture_name"]: row for row in read_csv(OUT_DIR / "task1937_negative_fixture_pack.csv")}
    for fixture in ["generic_positive_words_only", "future_sec_timestamp", "outcome_field_present"]:
        fail_if(fixture not in fixtures, f"missing negative fixture {fixture}")


def validate_interaction_content() -> None:
    events = read_csv(OUT_DIR / "task1932_event_window_absorption_panel.csv")
    fail_if(not any(row["event_window_absorption_state"] == "sustained_market_acceptance" for row in events), "no sustained acceptance rows")
    breadth = read_csv(OUT_DIR / "task1933_sector_breadth_source_field.csv")
    fail_if(not any(row["sector_breadth_state"] == "theme_breadth_confirmed" for row in breadth), "no confirmed breadth rows")
    sec = read_csv(OUT_DIR / "task1934_sec_financing_specificity_parser.csv")
    sec_states = {row["dilution_specificity_state"] for row in sec}
    fail_if("live_active_dilution" not in sec_states, "live active dilution not detected")
    fail_if("historical_or_closed_financing" not in sec_states, "historical financing not separated")
    l4 = read_csv(OUT_DIR / "task1935_l4_interaction_payoff_thesis_cards.csv")
    fail_if(not any("quality_defends_volatility" in row["positive_interaction_primitives"] for row in l4), "quality defense primitive did not fire")
    fail_if(not any("financing_risk_overrides_growth" in row["negative_interaction_primitives"] for row in l4), "financing override primitive did not fire")
    multipliers = {row["l5_budget_multiplier"] for row in l4}
    for expected in ["1.08", "0.7"]:
        fail_if(expected not in multipliers, f"missing multiplier bucket {expected}")


def validate_replay_metrics() -> None:
    trades = read_csv(OUT_DIR / "task1938_interaction_top3_replay_trades.csv")
    metrics = read_csv(OUT_DIR / "task1938_interaction_top3_replay_metrics.csv")
    metric = metrics[0]
    fail_if(metric["policy_variant_id"] != "interaction_forecast_top3_v1", "unexpected policy")
    fail_if(to_float(metric["final_equity"]) <= to_float(metric["baseline_final_equity"]), "did not improve baseline final equity")
    fail_if(metric["joint_target_met"] != "1", "joint diagnostic target not met")
    fail_if(metric["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(metric["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(metric["real_capital"] != "FORBIDDEN", "real capital status changed")
    fail_if(any(to_float(row["final_budget_multiplier"]) <= 0 for row in trades), "nonpositive replay trade multiplier")
    top5 = read_csv(OUT_DIR / "task1939_top5_expansion_gate.csv")
    fail_if(not any(row["top5_expansion_gate"] == "blocked_until_stronger_source_field_confirmation" for row in top5), "top5 gate did not block weak rows")
    fail_if(not any(row["top5_expansion_gate"] == "eligible_for_future_top5_expansion" for row in top5), "top5 gate has no eligible rows")


def validate_report_and_closeout() -> None:
    closeout = read_csv(OUT_DIR / "task1940_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "closeout real capital status changed")
    payload = json.loads((OUT_DIR / "task1940_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "interaction_forecast_layer_complete_diagnostic_only", "json closeout mismatch")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Interaction Forecast Layer",
        "source-field-only",
        "Top5 gate is an eligibility audit only",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_schema_and_fixtures()
        validate_interaction_content()
        validate_replay_metrics()
        validate_report_and_closeout()
    except AssertionError as exc:
        print(f"[TASK1931_1940_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1931_1940_VALIDATE_OK] interaction forecast layer artifacts are valid")


if __name__ == "__main__":
    main()
