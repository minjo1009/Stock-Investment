from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK546_OUT = Path("docs/reports/task_546_microstructure_live_capture_layer")
TASK531_DECISIONS = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_decision_snapshot_log.csv")
TASK531_LINEAGE = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_lifecycle_lineage.csv")
TASK525_CONTRACT = Path("docs/reports/task_525_broker_order_fill_archive_contract/broker_order_fill_archive_contract.csv")
TASK526_DEPTH = Path("docs/reports/task_526_depth_scope_decision/task_526_decision.csv")


def build_task546_microstructure_live_capture_layer(
    *,
    task531_decisions_path: Path = TASK531_DECISIONS,
    task531_lineage_path: Path = TASK531_LINEAGE,
    task525_contract_path: Path = TASK525_CONTRACT,
    task526_depth_path: Path = TASK526_DEPTH,
    out_dir: Path = TASK546_OUT,
) -> dict[str, pd.DataFrame]:
    source_contract = build_microstructure_live_source_contract()
    source_audit = build_source_availability_audit(source_contract)
    blockers = build_missing_source_blocker_audit(source_audit)
    schema = build_microstructure_capture_schema()
    snapshot_contract = build_decision_snapshot_contract()
    event_clock = build_event_clock_consistency_contract()
    order_lineage = build_order_lineage(task531_decisions_path, task531_lineage_path)
    order_contract = build_order_fill_microstructure_archive_contract(task525_contract_path)
    lineage_audit = build_decision_to_lifecycle_lineage_audit(order_lineage)
    feature_contract = build_microstructure_feature_contract(source_audit)
    hypothesis = build_microstructure_failure_separation_hypothesis()
    task_decisions = build_team_decisions(source_audit, blockers, lineage_audit, task526_depth_path)
    gate = build_readiness_gate(source_audit, lineage_audit, task_decisions)
    next_actions = build_next_action_queue(gate, blockers)
    artifacts = {
        "microstructure_live_source_contract": source_contract,
        "microstructure_source_availability_audit": source_audit,
        "missing_microstructure_source_blocker_audit": blockers,
        "task_546a_decision": task_decisions["a"],
        "microstructure_capture_schema": schema,
        "decision_snapshot_contract": snapshot_contract,
        "event_clock_consistency_contract": event_clock,
        "task_546b_decision": task_decisions["b"],
        "paper_shadow_microstructure_order_lineage": order_lineage,
        "order_fill_microstructure_archive_contract": order_contract,
        "decision_to_lifecycle_lineage_audit": lineage_audit,
        "task_546c_decision": task_decisions["c"],
        "microstructure_feature_contract": feature_contract,
        "microstructure_failure_separation_hypothesis": hypothesis,
        "task_546d_decision": task_decisions["d"],
        "microstructure_capture_readiness_gate": gate,
        "task_546_next_action_queue": next_actions,
        "task_546e_decision": task_decisions["e"],
    }
    write_task546(out_dir, artifacts)
    return artifacts


def build_microstructure_live_source_contract() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_name": "nbbo_quote_stream",
                "required_for": "spread_size_staleness_features",
                "required_fields": "symbol,event_ts,recv_ts_utc,bid,ask,bid_size,ask_size",
                "minimum_scope": "paper_shadow",
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "trade_bar_updated_bar_stream",
                "required_for": "bar_vwap_trade_count_and_intraday_range",
                "required_fields": "symbol,event_ts,recv_ts_utc,open,high,low,close,volume,vwap,trade_count",
                "minimum_scope": "paper_shadow",
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "status_luld_stream",
                "required_for": "halt_pause_luld_cleanliness",
                "required_fields": "symbol,event_ts,recv_ts_utc,status,luld_state",
                "minimum_scope": "paper_shadow",
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "order_update_stream",
                "required_for": "decision_order_fill_lifecycle_lineage",
                "required_fields": "decision_id,client_order_id,order_id,order_status,submitted_ts,filled_ts,filled_qty,filled_avg_price",
                "minimum_scope": "paper_shadow",
                "approximation_allowed_flag": 0,
            },
            {
                "source_name": "full_depth_book_stream",
                "required_for": "deployment_grade_depth_pressure",
                "required_fields": "symbol,event_ts,recv_ts_utc,book_levels",
                "minimum_scope": "deployment",
                "approximation_allowed_flag": 0,
            },
        ]
    )


def build_source_availability_audit(contract: pd.DataFrame) -> pd.DataFrame:
    availability = {
        "nbbo_quote_stream": ("collectable_not_archived", 0, 1, "No live receive-ts quote archive exists in current artifacts."),
        "trade_bar_updated_bar_stream": ("historical_ohlcv_available_live_archive_missing", 0, 1, "Historical OHLCV exists, but recv_ts live archive is not present."),
        "status_luld_stream": ("collectable_not_archived", 0, 1, "No status/LULD receive-ts archive exists in current artifacts."),
        "order_update_stream": ("historical_shadow_archive_only", 0, 1, "Task531 has shadow lineage but no broker-truth paper/live order updates."),
        "full_depth_book_stream": ("provider_missing", 0, 0, "Task526 keeps full depth blocked without provider."),
    }
    rows = []
    for rec in contract.to_dict(orient="records"):
        status, live_ready, paper_scope, note = availability[rec["source_name"]]
        rows.append(
            {
                **rec,
                "availability_status": status,
                "live_ready_flag": live_ready,
                "paper_shadow_scope_allowed_flag": paper_scope,
                "blocked_missing_source_flag": int(live_ready == 0 and rec["minimum_scope"] == "deployment"),
                "note": note,
            }
        )
    return pd.DataFrame(rows)


def build_missing_source_blocker_audit(source_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rec in source_audit.to_dict(orient="records"):
        blocked = int(rec["live_ready_flag"] == 0)
        rows.append(
            {
                "source_name": rec["source_name"],
                "blocked_flag": blocked,
                "blocked_scope": "deployment" if rec["minimum_scope"] == "deployment" else "live_ready_capture",
                "approximation_attempted_flag": 0,
                "required_next_action": "configure_provider_or_collector" if blocked else "none",
                "note": rec["note"],
            }
        )
    return pd.DataFrame(rows)


def build_microstructure_capture_schema() -> pd.DataFrame:
    rows = []
    for table_name, fields in {
        "raw_quote_event_log": ["symbol", "event_ts", "recv_ts_utc", "ingest_seq", "bid", "ask", "bid_size", "ask_size", "source_hash"],
        "raw_bar_event_log": ["symbol", "event_ts", "recv_ts_utc", "ingest_seq", "open", "high", "low", "close", "volume", "vwap", "trade_count", "source_hash"],
        "raw_status_luld_event_log": ["symbol", "event_ts", "recv_ts_utc", "ingest_seq", "status", "luld_state", "source_hash"],
        "decision_microstructure_snapshot_log": [
            "decision_id",
            "lifecycle_id",
            "symbol",
            "decision_ts_utc",
            "feature_cutoff_recv_ts_utc",
            "last_quote_recv_ts_utc",
            "bid",
            "ask",
            "bid_size",
            "ask_size",
            "spread_bps",
            "nbbo_size_dollar",
            "quote_staleness_ms",
            "status_clean_flag",
            "luld_active_flag",
            "microstructure_source_ready_flag",
            "missing_source_codes",
        ],
        "microstructure_feature_lineage_log": ["decision_id", "feature_name", "required_source_name", "source_event_ids_json", "source_hashes_json"],
    }.items():
        for field in fields:
            rows.append({"table_name": table_name, "field_name": field, "required_flag": 1, "append_only_flag": 1})
    return pd.DataFrame(rows)


def build_decision_snapshot_contract() -> pd.DataFrame:
    fields = [
        "decision_id",
        "lifecycle_id",
        "symbol",
        "decision_ts_utc",
        "feature_cutoff_recv_ts_utc",
        "last_quote_recv_ts_utc",
        "bid",
        "ask",
        "bid_size",
        "ask_size",
        "spread_bps",
        "nbbo_size_dollar",
        "quote_staleness_ms",
        "status_clean_flag",
        "luld_active_flag",
        "microstructure_source_ready_flag",
        "missing_source_codes",
    ]
    return pd.DataFrame([{"field_name": field, "required_flag": 1, "pre_order_required_flag": 1} for field in fields])


def build_event_clock_consistency_contract() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule_name": "source_recv_before_feature_cutoff", "rule_expression": "max(source.recv_ts_utc) <= feature_cutoff_recv_ts_utc", "required_flag": 1},
            {"rule_name": "feature_cutoff_before_decision", "rule_expression": "feature_cutoff_recv_ts_utc <= decision_ts_utc", "required_flag": 1},
            {"rule_name": "decision_snapshot_before_order_action", "rule_expression": "decision_ts_utc <= order_submit_or_simulated_action_ts_utc", "required_flag": 1},
            {"rule_name": "historical_without_recv_ts_not_live_ready", "rule_expression": "recv_ts_utc is not null for live_ready rows", "required_flag": 1},
        ]
    )


def build_order_lineage(decisions_path: Path, lineage_path: Path) -> pd.DataFrame:
    decisions = pd.read_csv(decisions_path) if decisions_path.exists() else pd.DataFrame()
    lineage = pd.read_csv(lineage_path) if lineage_path.exists() else pd.DataFrame()
    if decisions.empty or lineage.empty:
        return pd.DataFrame()
    cols = ["decision_id", "client_order_id", "order_id", "fill_id", "lifecycle_id", "lineage_complete_flag", "broker_truth_flag", "shadow_mode_flag"]
    merged = lineage[cols].merge(
        decisions[["decision_id", "symbol", "decision_action", "receive_ts_available_flag", "live_clock_record_flag", "historical_seed_record_flag"]],
        on="decision_id",
        how="left",
    )
    merged["microstructure_snapshot_ready_flag"] = 0
    merged["historical_seed_only_flag"] = merged["historical_seed_record_flag"].fillna(0).astype(int)
    return merged


def build_order_fill_microstructure_archive_contract(task525_contract_path: Path) -> pd.DataFrame:
    base = pd.read_csv(task525_contract_path) if task525_contract_path.exists() else pd.DataFrame()
    extra = pd.DataFrame(
        [
            {"field_name": "microstructure_snapshot_id", "required_flag": 1, "nullable_allowed_flag": 0},
            {"field_name": "simulated_action_ts_utc", "required_flag": 1, "nullable_allowed_flag": 1},
            {"field_name": "broker_truth_flag", "required_flag": 1, "nullable_allowed_flag": 0},
            {"field_name": "shadow_mode_flag", "required_flag": 1, "nullable_allowed_flag": 0},
        ]
    )
    return pd.concat([base, extra], ignore_index=True).drop_duplicates("field_name", keep="first")


def build_decision_to_lifecycle_lineage_audit(order_lineage: pd.DataFrame) -> pd.DataFrame:
    if order_lineage.empty:
        return pd.DataFrame([{"audit_name": "lineage_rows", "row_count": 0, "pass_flag": 0}])
    return pd.DataFrame(
        [
            {"audit_name": "lineage_rows", "row_count": int(len(order_lineage)), "pass_flag": int(len(order_lineage) > 0)},
            {"audit_name": "decision_to_client_order_to_order_to_fill_to_lifecycle", "row_count": int(order_lineage["lineage_complete_flag"].sum()), "pass_flag": int(order_lineage["lineage_complete_flag"].min())},
            {"audit_name": "broker_truth_rows", "row_count": int(order_lineage["broker_truth_flag"].sum()), "pass_flag": 0},
            {"audit_name": "historical_seed_only_rows", "row_count": int(order_lineage["historical_seed_only_flag"].sum()), "pass_flag": 1},
        ]
    )


def build_microstructure_feature_contract(source_audit: pd.DataFrame) -> pd.DataFrame:
    source_status = dict(zip(source_audit["source_name"], source_audit["live_ready_flag"]))
    features = [
        ("spread_bps", "nbbo_quote_stream"),
        ("spread_to_intraday_range", "nbbo_quote_stream,trade_bar_updated_bar_stream"),
        ("quote_staleness_ms", "nbbo_quote_stream"),
        ("nbbo_size_dollar", "nbbo_quote_stream"),
        ("nbbo_imbalance", "nbbo_quote_stream"),
        ("micro_liquidity_clean_flag", "nbbo_quote_stream"),
        ("micro_liquidity_stress_flag", "nbbo_quote_stream"),
        ("status_clean_flag", "status_luld_stream"),
        ("luld_active_flag", "status_luld_stream"),
        ("quote_available_flag", "nbbo_quote_stream"),
    ]
    rows = []
    for feature, required in features:
        required_sources = required.split(",")
        available = all(int(source_status.get(source, 0)) == 1 for source in required_sources)
        rows.append(
            {
                "feature_name": feature,
                "required_raw_sources": required,
                "entry_safe_flag": 1,
                "current_live_ready_flag": int(available),
                "missing_source_flag": int(not available),
                "outcome_or_fill_after_field_used_flag": 0,
                "approximation_allowed_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_microstructure_failure_separation_hypothesis() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"failure_mode": "fake_breakout_acceptance", "expected_discriminator": "wide_spread_or_low_nbbo_size_or_stale_quote", "required_features": "spread_bps,nbbo_size_dollar,quote_staleness_ms"},
            {"failure_mode": "entry_reduce_failure", "expected_discriminator": "liquidity_stress_or_status_luld_dirty", "required_features": "micro_liquidity_stress_flag,status_clean_flag,luld_active_flag"},
            {"failure_mode": "opening_drive_failure", "expected_discriminator": "opening_spread_to_range_too_high", "required_features": "spread_to_intraday_range,quote_staleness_ms"},
        ]
    )


def build_team_decisions(source_audit: pd.DataFrame, blockers: pd.DataFrame, lineage_audit: pd.DataFrame, task526_depth_path: Path) -> dict[str, pd.DataFrame]:
    nbbo_allowed = int(source_audit.loc[source_audit["source_name"].eq("nbbo_quote_stream"), "paper_shadow_scope_allowed_flag"].max())
    full_depth_blocked = int(blockers.loc[blockers["source_name"].eq("full_depth_book_stream"), "blocked_flag"].max())
    lineage_complete = int(lineage_audit.loc[lineage_audit["audit_name"].eq("decision_to_client_order_to_order_to_fill_to_lifecycle"), "pass_flag"].max()) if not lineage_audit.empty else 0
    return {
        "a": pd.DataFrame([{"task_id": "Task546A", "missing_source_approximation_flag": 0, "full_depth_blocked_flag": full_depth_blocked, "nbbo_only_paper_shadow_scope_allowed_flag": nbbo_allowed, "strategy_acceptance_status": "SOURCE_CONTRACT_READY_FULL_DEPTH_BLOCKED"}]),
        "b": pd.DataFrame([{"task_id": "Task546B", "schema_defined_flag": 1, "receive_ts_required_flag": 1, "historical_without_recv_ts_live_ready_flag": 0, "inferred_lifecycle_matching_used_flag": 0, "strategy_acceptance_status": "CAPTURE_SCHEMA_READY"}]),
        "c": pd.DataFrame([{"task_id": "Task546C", "lineage_complete_flag": lineage_complete, "broker_truth_available_flag": 0, "historical_seed_only_flag": 1, "deployment_ready_flag": 0, "strategy_acceptance_status": "LINEAGE_READY_HISTORICAL_SEED_ONLY"}]),
        "d": pd.DataFrame([{"task_id": "Task546D", "feature_contract_defined_flag": 1, "current_live_ready_feature_count": int(0), "outcome_or_fill_after_field_used_flag": 0, "strategy_acceptance_status": "FEATURE_CONTRACT_READY_SOURCE_BLOCKED"}]),
        "e": pd.DataFrame([{"task_id": "Task546E", "readiness_gate_defined_flag": 1, "deployment_ready_flag": 0, "strategy_acceptance_status": "PAPER_SHADOW_CAPTURE_READY_NBBO_ONLY_PENDING_COLLECTOR"}]),
    }


def build_readiness_gate(source_audit: pd.DataFrame, lineage_audit: pd.DataFrame, task_decisions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    quote_scope = int(source_audit.loc[source_audit["source_name"].eq("nbbo_quote_stream"), "paper_shadow_scope_allowed_flag"].max())
    full_depth_live = int(source_audit.loc[source_audit["source_name"].eq("full_depth_book_stream"), "live_ready_flag"].max())
    lineage_pass = int(lineage_audit.loc[lineage_audit["audit_name"].eq("decision_to_client_order_to_order_to_fill_to_lifecycle"), "pass_flag"].max()) if not lineage_audit.empty else 0
    if quote_scope and lineage_pass and not full_depth_live:
        gate = "FULL_DEPTH_BLOCKED_BUT_NBBO_SCOPE_ALLOWED"
    elif not quote_scope:
        gate = "DATA_BLOCKED_QUOTE"
    else:
        gate = "NOT_READY_SOURCE_CONTRACT_INCOMPLETE"
    return pd.DataFrame(
        [
            {
                "readiness_gate": gate,
                "paper_shadow_capture_ready_flag": int(gate == "FULL_DEPTH_BLOCKED_BUT_NBBO_SCOPE_ALLOWED"),
                "deployment_ready_flag": 0,
                "inferred_matching_used_flag": 0,
                "missing_raw_source_approximated_flag": 0,
                "diagnostic_or_paper_state": "PAPER_SHADOW_READY_NBBO_ONLY" if gate == "FULL_DEPTH_BLOCKED_BUT_NBBO_SCOPE_ALLOWED" else "DATA_BLOCKED",
            }
        ]
    )


def build_next_action_queue(gate: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    readiness = gate.iloc[0]["readiness_gate"] if not gate.empty else "NOT_READY_SOURCE_CONTRACT_INCOMPLETE"
    actions = [
        {"priority": 1, "next_task": "Task547_Paper_Shadow_Microstructure_Capture_Run", "action": "Implement collector for NBBO quote/bar/status snapshots with recv_ts and pre-order decision snapshots.", "blocked_flag": int(readiness != "FULL_DEPTH_BLOCKED_BUT_NBBO_SCOPE_ALLOWED")},
        {"priority": 2, "next_task": "Task548_Microstructure_Failure_Separation_ReTest", "action": "After live/paper capture accumulates rows, rerun Task545 failure separation with real spread/size/staleness/status features.", "blocked_flag": 1},
        {"priority": 3, "next_task": "Full_Depth_Provider_Selection", "action": "Select and integrate full-depth provider before any deployment-grade claim.", "blocked_flag": 1},
    ]
    return pd.DataFrame(actions)


def write_task546(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    gate = artifacts["microstructure_capture_readiness_gate"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_546_microstructure_live_capture_plan.md",
        title="Task 546 Microstructure Live Capture Layer",
        decision_summary=[
            f"Readiness gate: {gate['readiness_gate']}",
            f"Paper/shadow capture ready: {gate['paper_shadow_capture_ready_flag']}",
            f"Deployment-ready: {gate['deployment_ready_flag']}",
            "Missing raw source approximated: NO",
            "Inferred lifecycle matching used: NO",
        ],
        quant_expert_lines=[
            "Task546 converts the Task545 blocker into a source and capture contract: NBBO quote, status/LULD, receive timestamp, and order/fill lineage must be captured at decision time.",
            "Current state is NBBO-only paper/shadow scope allowed, but deployment-grade full depth remains blocked without a provider.",
            "Historical OHLCV rows are explicitly not live-ready because they lack receive timestamps and quote/status context.",
        ],
        decision_maker_lines=[
            "The next bottleneck is data capture, not another OHLCV filter.",
            "We can proceed to paper/shadow capture with NBBO-level data, but we cannot claim production readiness.",
            "Full depth remains a separate blocker for deployment-grade validation.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task546_microstructure_live_capture_layer()


if __name__ == "__main__":
    main()
