from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task529_530_trend_persistence_refinement import (
    TASK503_PANEL,
    TASK529_OUT,
    add_entry_bar_features,
    build_walk_forward_base,
    refined_rule_mask,
)
from src.backtest.build_task505_two_year_pnl_grid import simulate_portfolio
from src.backtest.build_task508_511_task505_validation import load_panel
from src.backtest.task_report_utils import write_standard_report
from src.execution.paper_shadow_order_fill_archive import (
    build_shadow_order_fill_records,
    validate_order_fill_contract,
)


TASK531_OUT = Path("docs/reports/task_531_paper_shadow_order_fill_archive")
BLOCKED_ONLINE_LABEL_FIELDS = {
    "failure_group",
    "lifecycle_outcome_class",
    "return_from_entry",
    "net_return_from_entry",
    "win_flag",
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_flag",
    "exit_ts",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "label_source",
}


def build_task531_paper_shadow_order_fill_archive(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    task529_selected_path: Path = TASK529_OUT / "trend_persistence_refined_selected_rule.csv",
    out_dir: Path = TASK531_OUT,
) -> dict[str, pd.DataFrame]:
    selected = pd.read_csv(task529_selected_path) if task529_selected_path.exists() else pd.DataFrame()
    selected_family = str(selected.iloc[0]["family_name"]) if not selected.empty else "none"
    cached_pre_capacity = _load_cached_pre_capacity_panel(out_dir, selected_family)
    if cached_pre_capacity.empty:
        panel = add_entry_bar_features(load_panel(task503_panel_path))
        walk_forward_base = build_walk_forward_base(panel)
        candidate_panel = _portfolio_accepted_shadow_panel(walk_forward_base, selected_family) if selected_family != "none" and not walk_forward_base.empty else pd.DataFrame()
        pre_capacity_count = int(len(walk_forward_base[refined_rule_mask(walk_forward_base, selected_family)])) if selected_family != "none" and not walk_forward_base.empty else 0
    else:
        candidate_panel = _portfolio_accepted_from_cached_panel(cached_pre_capacity)
        pre_capacity_count = int(len(cached_pre_capacity))

    assignment_panel = _build_shadow_assignment_panel(candidate_panel, selected_family)
    shadow_records = build_shadow_order_fill_records(
        assignment_panel,
        policy_version=f"task531_{selected_family}",
    )
    contract_audit = validate_order_fill_contract(shadow_records["paper_shadow_order_archive"])
    receive_ts_audit = _build_receive_ts_audit(shadow_records["paper_shadow_decision_snapshot_log"])
    readiness = _build_readiness_decision(selected_family, assignment_panel, shadow_records, receive_ts_audit, pre_capacity_count)
    source_separation = _build_source_separation_audit(shadow_records["paper_shadow_decision_snapshot_log"])

    artifacts = {
        "paper_shadow_assignment_panel": assignment_panel,
        **shadow_records,
        "paper_shadow_order_fill_contract_audit": contract_audit,
        "paper_shadow_receive_ts_audit": receive_ts_audit,
        "historical_vs_live_shadow_source_audit": source_separation,
        "task_531_decision": readiness,
    }
    _write(out_dir, artifacts)
    return artifacts


def _build_shadow_assignment_panel(candidate_panel: pd.DataFrame, selected_family: str) -> pd.DataFrame:
    if candidate_panel.empty:
        return pd.DataFrame(
            columns=[
                "lifecycle_id",
                "symbol",
                "theme_id",
                "entry_ts",
                "entry_price",
                "selected_family",
                "decision_action",
                "inferred_lifecycle_matching_used_flag",
                "label_used_in_assignment_flag",
            ]
        )
    allowed_cols = [col for col in candidate_panel.columns if col not in BLOCKED_ONLINE_LABEL_FIELDS]
    out = candidate_panel[allowed_cols].copy()
    out["selected_family"] = selected_family
    out["decision_action"] = "SHADOW_ENTRY"
    out["order_submission_enabled_flag"] = 0
    out["paper_shadow_recording_enabled_flag"] = 1
    out["inferred_lifecycle_matching_used_flag"] = 0
    out["label_used_in_assignment_flag"] = 0
    return out.reset_index(drop=True)


def _portfolio_accepted_shadow_panel(walk_forward_base: pd.DataFrame, selected_family: str) -> pd.DataFrame:
    accepted = []
    for _, fold in walk_forward_base.groupby("fold_q", dropna=False):
        filtered = fold[refined_rule_mask(fold, selected_family)].copy()
        if filtered.empty:
            continue
        max_positions = int(fold["fold_max_positions"].iloc[0]) if "fold_max_positions" in fold.columns else 10
        result = simulate_portfolio(filtered, max_positions=max_positions)
        if not result.accepted_panel.empty:
            accepted.append(result.accepted_panel)
    return pd.concat(accepted, ignore_index=True) if accepted else pd.DataFrame()


def _load_cached_pre_capacity_panel(out_dir: Path, selected_family: str) -> pd.DataFrame:
    path = out_dir / "paper_shadow_assignment_panel.csv"
    if not path.exists() or selected_family == "none":
        return pd.DataFrame()
    frame = pd.read_csv(path)
    required = {"fold_q", "fold_max_positions", "lifecycle_id", "selected_family"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    subset = frame[frame["selected_family"].astype(str).eq(selected_family)].copy()
    if subset.empty:
        return pd.DataFrame()
    for col in ["entry_ts", "simulated_exit_ts"]:
        if col in subset.columns:
            subset[col] = pd.to_datetime(subset[col], utc=True, errors="coerce")
    return subset


def _portfolio_accepted_from_cached_panel(pre_capacity: pd.DataFrame) -> pd.DataFrame:
    if not {"simulated_exit_ts", "net_return_from_entry"}.issubset(pre_capacity.columns):
        return _capacity_projection_from_task529_counts(pre_capacity)
    accepted = []
    for _, fold in pre_capacity.groupby("fold_q", dropna=False):
        max_positions = int(fold["fold_max_positions"].iloc[0]) if "fold_max_positions" in fold.columns else 10
        result = simulate_portfolio(fold.copy(), max_positions=max_positions)
        if not result.accepted_panel.empty:
            accepted.append(result.accepted_panel)
    return pd.concat(accepted, ignore_index=True) if accepted else pd.DataFrame()


def _capacity_projection_from_task529_counts(pre_capacity: pd.DataFrame) -> pd.DataFrame:
    quality_path = TASK529_OUT / "trend_persistence_refined_walk_forward_quality.csv"
    if not quality_path.exists():
        return pre_capacity.iloc[0:0].copy()
    quality = pd.read_csv(quality_path)
    if quality.empty:
        return pre_capacity.iloc[0:0].copy()
    selected_family = str(pre_capacity["selected_family"].iloc[0])
    quality = quality[quality["family_name"].astype(str).eq(selected_family)].copy()
    accepted = []
    for _, fold in pre_capacity.groupby("fold_q", dropna=False):
        q = str(fold["fold_q"].iloc[0])
        q_quality = quality[quality["test_quarter"].astype(str).eq(q)]
        if q_quality.empty:
            continue
        accepted_count = int(q_quality.iloc[0]["lifecycle_count"])
        ordered = fold.sort_values("entry_ts").head(accepted_count).copy()
        ordered["capacity_projection_source"] = "task529_fold_lifecycle_count_no_label_fields"
        accepted.append(ordered)
    return pd.concat(accepted, ignore_index=True) if accepted else pd.DataFrame()


def _build_receive_ts_audit(decision_log: pd.DataFrame) -> pd.DataFrame:
    if decision_log.empty:
        return pd.DataFrame(
            [
                {
                    "decision_snapshot_count": 0,
                    "receive_ts_available_count": 0,
                    "receive_ts_missing_count": 0,
                    "live_clock_record_count": 0,
                    "historical_seed_record_count": 0,
                    "historical_rows_treated_live_ready_flag": 0,
                }
            ]
        )
    return pd.DataFrame(
        [
            {
                "decision_snapshot_count": int(len(decision_log)),
                "receive_ts_available_count": int(decision_log["receive_ts_available_flag"].sum()),
                "receive_ts_missing_count": int((decision_log["receive_ts_available_flag"] == 0).sum()),
                "live_clock_record_count": int(decision_log["live_clock_record_flag"].sum()),
                "historical_seed_record_count": int(decision_log["historical_seed_record_flag"].sum()),
                "historical_rows_treated_live_ready_flag": 0,
            }
        ]
    )


def _build_source_separation_audit(decision_log: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_layer": "historical_shadow_seed",
                "row_count": int(decision_log["historical_seed_record_flag"].sum()) if not decision_log.empty else 0,
                "live_equivalent_flag": 0,
                "description": "Historical exact-lifecycle candidates converted into shadow archive format without pretending receive_ts exists.",
            },
            {
                "source_layer": "live_clock_shadow_archive",
                "row_count": int(decision_log["live_clock_record_flag"].sum()) if not decision_log.empty else 0,
                "live_equivalent_flag": 1,
                "description": "Rows with actual receive_ts from live stream archive.",
            },
        ]
    )


def _build_readiness_decision(
    selected_family: str,
    assignment_panel: pd.DataFrame,
    shadow_records: dict[str, pd.DataFrame],
    receive_ts_audit: pd.DataFrame,
    pre_capacity_count: int,
) -> pd.DataFrame:
    order_count = len(shadow_records["paper_shadow_order_archive"])
    fill_count = len(shadow_records["paper_shadow_fill_archive"])
    lineage_count = len(shadow_records["paper_shadow_lifecycle_lineage"])
    live_count = int(receive_ts_audit.iloc[0]["live_clock_record_count"]) if not receive_ts_audit.empty else 0
    lineage_complete = int(order_count == fill_count == lineage_count == len(assignment_panel) and order_count > 0)
    return pd.DataFrame(
        [
            {
                "task_id": "Task531",
                "selected_family": selected_family,
                "pre_capacity_shadow_candidate_count": int(pre_capacity_count),
                "shadow_assignment_count": int(len(assignment_panel)),
                "shadow_order_count": int(order_count),
                "shadow_fill_count": int(fill_count),
                "lineage_complete_flag": lineage_complete,
                "decision_to_client_order_to_order_to_fill_to_lifecycle_flag": lineage_complete,
                "live_clock_record_count": live_count,
                "historical_seed_record_count": int(len(assignment_panel) - live_count),
                "order_submission_enabled_flag": 0,
                "broker_truth_fill_available_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "PAPER_SHADOW_ARCHIVE_READY_HISTORICAL_SEED_ONLY"
                if lineage_complete
                else "PAPER_SHADOW_ARCHIVE_NOT_READY",
            }
        ]
    )


def _write(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_531_decision"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_531_paper_shadow_order_fill_archive.md",
        title="Task 531 Paper Shadow Order Fill Archive",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Shadow assignment count: {decision['shadow_assignment_count']}",
            f"Lineage complete: {'YES' if decision['lineage_complete_flag'] else 'NO'}",
            f"Live-clock records: {decision['live_clock_record_count']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task531 converts the Task530 paper/shadow candidate into an explicit lineage archive: decision_id -> client_order_id -> order_id -> fill -> lifecycle_id.",
            "No broker order is submitted. The generated fills are shadow records with `broker_truth_flag=0`, so this is suitable for paper/shadow instrumentation and lineage testing, not execution-grade validation.",
            "Historical seed rows are kept separate from live-equivalent rows. Rows without `receive_ts_utc` are not treated as live-ready.",
        ],
        decision_maker_lines=[
            "We now have the missing bookkeeping layer that shows exactly how a future paper/shadow decision will connect to a simulated order, fill, and lifecycle.",
            "This does not mean the strategy is ready for live trading. It means the next live/paper run can be audited without guessing which order belonged to which lifecycle.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task503-panel", type=Path, default=TASK503_PANEL)
    parser.add_argument("--task529-selected", type=Path, default=TASK529_OUT / "trend_persistence_refined_selected_rule.csv")
    args = parser.parse_args()
    build_task531_paper_shadow_order_fill_archive(
        task503_panel_path=args.task503_panel,
        task529_selected_path=args.task529_selected,
    )


if __name__ == "__main__":
    main()
