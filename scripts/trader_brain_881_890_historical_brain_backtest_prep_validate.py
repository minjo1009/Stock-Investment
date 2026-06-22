from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep"


REQUIRED = [
    "historical_decision_calendar.csv",
    "universe_membership_panel.csv",
    "historical_source_time_panel_status.csv",
    "brain_layer_state_reconstruction_preview.csv",
    "rolling_graph_snapshot_preview.csv",
    "candidate_bundle_generation_preview.csv",
    "trader_decision_policy_preview.csv",
    "historical_trade_spec_adapter_preview.csv",
    "replay_harness_data_gate_status.csv",
    "negative_fixture_leakage_cases.csv",
    "negative_fixture_validation_result.csv",
    "historical_brain_backtest_prep_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_BUNDLE_COLUMNS = {"rank", "future_return", "position_size", "price_target", "realized_return"}


def parse_ts(value: str, errors: list[str], label: str) -> pd.Timestamp | None:
    if value == "EXPLICIT_MISSING_SOURCE_PANEL":
        return None
    try:
        return pd.Timestamp(value)
    except Exception:  # noqa: BLE001
        errors.append(f"invalid timestamp {label}={value}")
        return None


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
    calendar = rows(ART / "historical_decision_calendar.csv")
    if len(calendar) != 63:
        errors.append("decision calendar must contain 63 monthly decisions from 2021-01 through 2026-03")
    if calendar[0]["session_date"] < "2021-01-01":
        errors.append("decision calendar starts before contract start")
    if calendar[-1]["session_date"] > "2026-03-31":
        errors.append("decision calendar ends after contract end")
    membership = rows(ART / "universe_membership_panel.csv")
    if len(membership) != 63 * 70:
        errors.append("membership panel must be 63 decisions x 70 symbols")
    source_status = rows(ART / "historical_source_time_panel_status.csv")
    if not any(row["availability_status"] == "missing_historical_source_panel" for row in source_status):
        errors.append("source-time status must expose missing historical source panel blocker")
    for i, row in enumerate(source_status):
        decision_ts = parse_ts(row["decision_asof_ts"], errors, f"source[{i}].decision_asof_ts")
        published_ts = parse_ts(row["published_ts"], errors, f"source[{i}].published_ts")
        received_ts = parse_ts(row["received_ts"], errors, f"source[{i}].received_ts")
        available_ts = parse_ts(row["available_to_brain_ts"], errors, f"source[{i}].available_to_brain_ts")
        if row["availability_status"] == "missing_historical_source_panel":
            if row["source_gap_flag"] != "1":
                errors.append("missing source rows must carry source_gap_flag=1")
            if any(row[field] != "EXPLICIT_MISSING_SOURCE_PANEL" for field in ["published_ts", "received_ts", "available_to_brain_ts"]):
                errors.append("missing source rows must use explicit missing marker")
        else:
            if not decision_ts or not published_ts or not received_ts or not available_ts:
                errors.append("available source rows must have parseable source-time timestamps")
            elif not (published_ts <= received_ts <= available_ts <= decision_ts):
                errors.append("source-time ordering must be published <= received <= available <= decision_asof")
    brain = rows(ART / "brain_layer_state_reconstruction_preview.csv")
    if not brain or any(row["brain_replay_state"] != "blocked_before_candidate_generation" for row in brain):
        errors.append("brain states must be blocked before candidate generation until source-time panel exists")
    brain_ids = {row["brain_state_id"] for row in brain}
    graph = rows(ART / "rolling_graph_snapshot_preview.csv")
    for i, row in enumerate(graph):
        if row["brain_state_id"] not in brain_ids:
            errors.append("graph snapshot must reference existing brain_state_id")
        decision_ts = parse_ts(row["decision_asof_ts"], errors, f"graph[{i}].decision_asof_ts")
        node_ts = parse_ts(row["node_asof_max_ts"], errors, f"graph[{i}].node_asof_max_ts")
        edge_ts = parse_ts(row["edge_asof_max_ts"], errors, f"graph[{i}].edge_asof_max_ts")
        if decision_ts and node_ts and node_ts > decision_ts:
            errors.append("graph node_asof_max_ts cannot exceed decision_asof_ts")
        if decision_ts and edge_ts and edge_ts > decision_ts:
            errors.append("graph edge_asof_max_ts cannot exceed decision_asof_ts")
    graph_ids = {row["graph_snapshot_id"] for row in graph}
    bundles = rows(ART / "candidate_bundle_generation_preview.csv")
    if FORBIDDEN_BUNDLE_COLUMNS.intersection(bundles[0].keys()):
        errors.append("candidate bundle preview contains forbidden future-outcome columns")
    for i, row in enumerate(bundles):
        if row["graph_snapshot_id"] not in graph_ids:
            errors.append("candidate bundle must reference existing graph_snapshot_id")
        decision_ts = parse_ts(row["decision_asof_ts"], errors, f"bundle[{i}].decision_asof_ts")
        bundle_ts = parse_ts(row["bundle_asof_ts"], errors, f"bundle[{i}].bundle_asof_ts")
        if decision_ts and bundle_ts and bundle_ts > decision_ts:
            errors.append("bundle_asof_ts cannot exceed decision_asof_ts")
    decisions = rows(ART / "trader_decision_policy_preview.csv")
    if not decisions or any(row["decision_state"] != "skip" for row in decisions):
        errors.append("decision preview must skip when source gaps block candidate bundles")
    bundle_ids = {row["candidate_bundle_id"] for row in bundles}
    for i, row in enumerate(decisions):
        if row["candidate_bundle_id"] not in bundle_ids:
            errors.append("trader decision must reference existing candidate_bundle_id")
        decision_ts = parse_ts(row["decision_asof_ts"], errors, f"decision[{i}].decision_asof_ts")
        policy_ts = parse_ts(row["decision_policy_asof_ts"], errors, f"decision[{i}].decision_policy_asof_ts")
        if decision_ts and policy_ts and policy_ts > decision_ts:
            errors.append("decision_policy_asof_ts cannot exceed decision_asof_ts")
        if row["decision_state"] == "reduce" and row.get("position_state", "") == "zero":
            errors.append("reduce requires existing nonzero position state")
    specs = rows(ART / "historical_trade_spec_adapter_preview.csv")
    if not specs or any(row["trade_spec_state"] != "blocked" for row in specs):
        errors.append("trade spec preview must remain blocked")
    policy_ids = {row["decision_policy_output_id"] for row in decisions}
    for i, row in enumerate(specs):
        if row["decision_policy_output_id"] not in policy_ids:
            errors.append("trade spec preview must reference existing decision_policy_output_id")
        decision_ts = parse_ts(row["decision_asof_ts"], errors, f"spec[{i}].decision_asof_ts")
        spec_ts = parse_ts(row["trade_spec_asof_ts"], errors, f"spec[{i}].trade_spec_asof_ts")
        if decision_ts and spec_ts and spec_ts > decision_ts:
            errors.append("trade_spec_asof_ts cannot exceed decision_asof_ts")
        if row["trade_spec_state"] != "blocked" and (not row["symbol"] or not row["side"] or not row["allocated_capital"]):
            errors.append("active trade spec requires symbol side and allocated_capital")
    gate = rows(ART / "replay_harness_data_gate_status.csv")
    if not any(row["gate"] == "historical_source_time_panel" and row["status"] == "fail" for row in gate):
        errors.append("source-time panel gate must fail")
    if not any(row["gate"] == "first_real_historical_brain_replay" and row["status"] == "no_go" for row in gate):
        errors.append("first real historical brain replay must remain no_go")
    summary = json.loads((ART / "historical_brain_backtest_prep_summary.json").read_text(encoding="utf-8"))
    if summary.get("replay_gate") != "no_go":
        errors.append("summary replay gate must remain no_go")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary strategy acceptance must remain NOT_ACCEPTED")
    negative_cases = rows(ART / "negative_fixture_leakage_cases.csv")
    negative_results = rows(ART / "negative_fixture_validation_result.csv")
    if len(negative_cases) < 5:
        errors.append("negative fixture set must include at least 5 leakage/no-inference cases")
    if {row["fixture_id"] for row in negative_cases} != {row["fixture_id"] for row in negative_results}:
        errors.append("negative fixture results must cover all cases")
    if any(row["actual_status"] != "rejected" for row in negative_results):
        errors.append("all negative fixtures must be rejected")
    if int(summary.get("negative_fixture_count", 0)) != len(negative_cases):
        errors.append("summary negative fixture count must match fixture rows")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_881_890_PREP_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_881_890_PREP_OK] historical brain backtest prep artifacts validated")


if __name__ == "__main__":
    main()
