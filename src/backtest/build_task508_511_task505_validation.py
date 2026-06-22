from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, quality
from src.backtest.build_task505_two_year_pnl_grid import build_cell_pool, run_grid, select_best_candidate, simulate_portfolio


DEFAULT_TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
DEFAULT_TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
DEFAULT_DATA_RAW = Path("data/raw")
TASK508_OUT = Path("docs/reports/task_508_cost_stress_validation")
TASK509_OUT = Path("docs/reports/task_509_walk_forward_oos_validation")
TASK510_OUT = Path("docs/reports/task_510_entry_reduce_failure_decomposition")
TASK511_OUT = Path("docs/reports/task_511_live_source_feature_revalidation")


@dataclass(frozen=True)
class Task508Artifacts:
    cost_stress_quality: pd.DataFrame
    cost_stress_equity_summary: pd.DataFrame
    task_508_decision: pd.DataFrame


def load_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["simulated_exit_ts"] = pd.to_datetime(frame["simulated_exit_ts"], utc=True, errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame = frame.dropna(subset=["entry_ts", "simulated_exit_ts", "net_return_from_entry", "lifecycle_id"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    frame["inferred_lifecycle_matching_used_flag"] = 0
    return frame.sort_values("entry_ts").reset_index(drop=True)


def build_task508_cost_stress_validation(*, task505_panel_path: Path = DEFAULT_TASK505_PANEL, out_dir: Path = TASK508_OUT) -> Task508Artifacts:
    panel = load_panel(task505_panel_path)
    stresses = [
        ("reported_no_extra_cost", 0.0),
        ("roundtrip_25bp", 0.0025),
        ("roundtrip_50bp", 0.0050),
        ("roundtrip_100bp", 0.0100),
        ("roundtrip_200bp", 0.0200),
    ]
    rows = []
    equity_rows = []
    for name, cost in stresses:
        adjusted = panel.copy()
        adjusted["cost_stress_name"] = name
        adjusted["roundtrip_cost_rate"] = cost
        adjusted["net_return_from_entry"] = adjusted["net_return_from_entry"] - cost
        adjusted["win_flag"] = (adjusted["net_return_from_entry"] > 0).astype(int)
        adjusted["add_scale_success_flag"] = (adjusted["net_return_from_entry"] >= 0.03).astype(int)
        adjusted["entry_reduce_failure_flag"] = (adjusted["net_return_from_entry"] <= -0.03).astype(int)
        adjusted["false_positive_flag"] = (adjusted["net_return_from_entry"] <= 0).astype(int)
        result = simulate_portfolio(adjusted, max_positions=10)
        row = aggregate(result.accepted_panel)
        row.update(
            {
                "cost_stress_name": name,
                "roundtrip_cost_rate": cost,
                "two_year_capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                "max_drawdown_pct": result.quality["max_drawdown_pct"],
                "skipped_due_capacity_count": result.quality["skipped_due_capacity_count"],
            }
        )
        rows.append(row)
        curve = result.equity_curve.copy()
        if not curve.empty:
            curve["cost_stress_name"] = name
            equity_rows.append(curve)
    quality_df = pd.DataFrame(rows)
    equity_summary = pd.concat(equity_rows, ignore_index=True) if equity_rows else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task508",
                "reported_pnl_pct": float(quality_df[quality_df["cost_stress_name"].eq("reported_no_extra_cost")]["two_year_capital_pnl_pct"].iloc[0]) if not quality_df.empty else pd.NA,
                "roundtrip_100bp_pnl_pct": float(quality_df[quality_df["cost_stress_name"].eq("roundtrip_100bp")]["two_year_capital_pnl_pct"].iloc[0]) if not quality_df.empty else pd.NA,
                "roundtrip_100bp_positive_flag": int(float(quality_df[quality_df["cost_stress_name"].eq("roundtrip_100bp")]["two_year_capital_pnl_pct"].iloc[0]) > 0) if not quality_df.empty else 0,
                "explicit_cost_model_added_flag": 1,
                "inferred_lifecycle_matching_used_flag": 0,
                "strategy_acceptance_status": "COST_STRESS_DIAGNOSTIC_ONLY",
            }
        ]
    )
    write_task508(out_dir, quality_df, equity_summary, decision)
    return Task508Artifacts(quality_df, equity_summary, decision)


def write_task508(out_dir: Path, quality_df: pd.DataFrame, equity_summary: pd.DataFrame, decision: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    quality_df.to_csv(out_dir / "cost_stress_quality.csv", index=False)
    equity_summary.to_csv(out_dir / "cost_stress_equity_curve.csv", index=False)
    decision.to_csv(out_dir / "task_508_decision.csv", index=False)
    (out_dir / "task_508_cost_stress_validation.md").write_text(report_task508(quality_df, decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def report_task508(quality_df: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 508 - Cost Stress Validation",
            "",
            "## Quant Expert Report",
            "",
            "Task508 applies explicit round-trip cost stress to the selected Task505 strategy. This is still a stress model, not broker-truth fill data.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Reported PnL before extra cost: {float(d['reported_pnl_pct']):.2f}%",
            f"- PnL after 100bp round-trip stress: {float(d['roundtrip_100bp_pnl_pct']):.2f}%",
            f"- Still positive after 100bp stress: {d['roundtrip_100bp_positive_flag']}",
        ]
    )


def build_task509_walk_forward_oos_validation(*, task503_panel_path: Path = DEFAULT_TASK503_PANEL, out_dir: Path = TASK509_OUT) -> dict[str, pd.DataFrame]:
    source = load_panel(task503_panel_path)
    source = source[source["entry_ts"].ge(source["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    quarters = sorted(source["quarter"].dropna().astype(str).unique().tolist())
    rows = []
    panels = []
    for idx in range(2, len(quarters)):
        train_q = quarters[:idx]
        test_q = quarters[idx]
        train = source[source["quarter"].isin(train_q)].copy()
        test = source[source["quarter"].eq(test_q)].copy()
        if len(train) < 100 or len(test) < 5:
            continue
        pool = build_cell_pool(train)
        candidates, _ = run_grid(train, pool)
        if candidates.empty:
            continue
        selected = select_best_candidate(candidates)
        rule_cells = pool[
            pool["cell_dims"].eq(selected["cell_dims"])
            & pool["avg_net_return_pct"].ge(float(selected["min_avg_net_pct"]))
            & pool["win_rate"].ge(float(selected["min_win_rate"]))
            & pool["entry_reduce_failure_rate"].le(float(selected["max_entry_reduce_rate"]))
        ].copy()
        assigned = assign_cells_like(test, rule_cells)
        result = simulate_portfolio(assigned, max_positions=int(selected["max_positions"]))
        metrics = aggregate(result.accepted_panel)
        metrics.update(
            {
                "test_quarter": test_q,
                "train_start_quarter": train_q[0],
                "train_end_quarter": train_q[-1],
                "selected_candidate_strategy_name": selected["candidate_strategy_name"],
                "test_two_year_capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                "test_max_drawdown_pct": result.quality["max_drawdown_pct"],
                "selected_cell_count": int(len(rule_cells)),
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
            }
        )
        rows.append(metrics)
        if not result.accepted_panel.empty:
            out = result.accepted_panel.copy()
            out["walk_forward_test_quarter"] = test_q
            panels.append(out)
    wf = pd.DataFrame(rows)
    panel = pd.concat(panels, ignore_index=True) if panels else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task509",
                "walk_forward_fold_count": int(len(wf)),
                "walk_forward_total_count": int(wf["lifecycle_count"].sum()) if not wf.empty else 0,
                "walk_forward_avg_net_pct": float((panel["net_return_from_entry"].mean() * 100.0)) if not panel.empty else pd.NA,
                "walk_forward_win_rate": float(panel["win_flag"].mean()) if not panel.empty else pd.NA,
                "walk_forward_entry_reduce_rate": float(panel["entry_reduce_failure_flag"].mean()) if not panel.empty else pd.NA,
                "hindsight_grid_selection_removed_flag": 1,
                "strategy_acceptance_status": "WALK_FORWARD_DIAGNOSTIC_ONLY",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    wf.to_csv(out_dir / "walk_forward_oos_quality.csv", index=False)
    panel.to_csv(out_dir / "walk_forward_oos_assignment_panel.csv", index=False)
    decision.to_csv(out_dir / "task_509_decision.csv", index=False)
    (out_dir / "task_509_walk_forward_oos_validation.md").write_text(report_task509(decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"walk_forward_oos_quality": wf, "walk_forward_oos_assignment_panel": panel, "task_509_decision": decision}


def assign_cells_like(panel: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    if panel.empty or cells.empty:
        return panel.iloc[0:0].copy()
    masks = []
    for _, cell in cells.iterrows():
        dims = str(cell["cell_dims"]).split("|")
        values = str(cell["cell_values"]).split("|")
        mask = pd.Series(True, index=panel.index)
        for dim, value in zip(dims, values):
            mask &= panel[dim].astype(str).eq(value)
        masks.append(mask)
    combined = masks[0].copy()
    for mask in masks[1:]:
        combined |= mask
    return panel[combined].copy().reset_index(drop=True)


def report_task509(decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 509 - Walk-Forward OOS Validation",
            "",
            "## Quant Expert Report",
            "",
            "Task509 freezes grid selection on prior quarters and evaluates the selected rule on the next quarter. This directly audits Task505 hindsight selection bias.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Walk-forward folds: {d['walk_forward_fold_count']}",
            f"- Test trades: {d['walk_forward_total_count']}",
            f"- Test avg net / win / entry_reduce: {float(d['walk_forward_avg_net_pct']):.3f}% / {float(d['walk_forward_win_rate']):.1%} / {float(d['walk_forward_entry_reduce_rate']):.1%}",
        ]
    )


def build_task510_entry_reduce_failure_decomposition(*, task505_panel_path: Path = DEFAULT_TASK505_PANEL, out_dir: Path = TASK510_OUT) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    failure = panel[panel["entry_reduce_failure_flag"].eq(1)].copy()
    axes = ["theme_id", "theme_regime_state_v4", "timing_state", "symbol_multiday_setup_state", "exit_reason"]
    decomposition = quality(failure, axes) if not failure.empty else pd.DataFrame()
    state_rows = []
    compare_axes = ["theme_id", "timing_state", "symbol_multiday_setup_state", "theme_regime_state_v4"]
    for axis in compare_axes:
        if axis not in panel.columns:
            continue
        temp = quality(panel, [axis])
        temp["decomposition_axis"] = axis
        temp = temp.rename(columns={axis: "state_value"})
        state_rows.append(temp)
    by_state = pd.concat(state_rows, ignore_index=True) if state_rows else pd.DataFrame()
    severe = failure[failure["net_return_from_entry"].le(-0.10)].copy()
    severe_summary = quality(severe, ["theme_id", "timing_state"]) if not severe.empty else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task510",
                "entry_reduce_count": int(len(failure)),
                "entry_reduce_rate": float(panel["entry_reduce_failure_flag"].mean()) if not panel.empty else 0.0,
                "severe_loss_count": int(len(severe)),
                "largest_failure_axis": "theme_id|theme_regime_state_v4|timing_state|symbol_multiday_setup_state|exit_reason",
                "label_used_for_evaluation_only_flag": 1,
                "strategy_acceptance_status": "FAILURE_DECOMPOSITION_ONLY",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    decomposition.to_csv(out_dir / "entry_reduce_failure_decomposition.csv", index=False)
    by_state.to_csv(out_dir / "entry_reduce_failure_by_state.csv", index=False)
    severe_summary.to_csv(out_dir / "entry_reduce_severe_loss_summary.csv", index=False)
    decision.to_csv(out_dir / "task_510_decision.csv", index=False)
    (out_dir / "task_510_entry_reduce_failure_decomposition.md").write_text(report_task510(decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"entry_reduce_failure_decomposition": decomposition, "entry_reduce_failure_by_state": by_state, "task_510_decision": decision}


def report_task510(decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 510 - Entry Reduce Failure Decomposition",
            "",
            "## Quant Expert Report",
            "",
            "Task510 isolates Task505 entry-reduce failures and quantifies where they concentrate. Labels are used only after assignment to explain failure, not to create entries.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Entry-reduce count: {d['entry_reduce_count']}",
            f"- Entry-reduce rate: {float(d['entry_reduce_rate']):.1%}",
            f"- Severe loss count <= -10%: {d['severe_loss_count']}",
        ]
    )


def build_task511_live_source_feature_revalidation(*, data_raw: Path = DEFAULT_DATA_RAW, out_dir: Path = TASK511_OUT) -> dict[str, pd.DataFrame]:
    quote_window = data_raw / "alpaca_quote_entry_windows" / "task492_raw_quote_entry_windows.csv"
    rows = [
        {
            "source_name": "historical_intraday_ohlcv_vwap",
            "required_for": "technical_intraday_continuation_features",
            "available_flag": int((data_raw / "us_intraday").exists()),
            "usable_now_flag": int((data_raw / "us_intraday").exists()),
            "missing_reason": "",
        },
        {
            "source_name": "entry_quote_window_nbbo",
            "required_for": "spread_nbbo_size_cost_filter",
            "available_flag": int(quote_window.exists()),
            "usable_now_flag": int(quote_window.exists()),
            "missing_reason": "" if quote_window.exists() else "quote_window_missing",
        },
        {
            "source_name": "raw_receive_timestamp_archive",
            "required_for": "true_forward_live_replay",
            "available_flag": 0,
            "usable_now_flag": 0,
            "missing_reason": "historical_task505_panel_has_no_raw_receive_timestamp",
        },
        {
            "source_name": "status_luld_historical_stream",
            "required_for": "halt_luld_clean_filter",
            "available_flag": 0,
            "usable_now_flag": 0,
            "missing_reason": "historical_status_luld_not_available_for_task505_rows",
        },
        {
            "source_name": "full_depth_book",
            "required_for": "depth_imbalance_and_capacity_filter",
            "available_flag": 0,
            "usable_now_flag": 0,
            "missing_reason": "full_depth_provider_required_not_approximated",
        },
    ]
    audit = pd.DataFrame(rows)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task511",
                "usable_source_count": int(audit["usable_now_flag"].sum()),
                "required_source_count": int(len(audit)),
                "live_source_revalidation_ready_flag": int(audit["usable_now_flag"].sum() == len(audit)),
                "missing_sources_approximated_flag": 0,
                "strategy_acceptance_status": "LIVE_SOURCE_REVALIDATION_BLOCKED_BY_MISSING_SOURCES",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out_dir / "live_source_feature_readiness_audit.csv", index=False)
    decision.to_csv(out_dir / "task_511_decision.csv", index=False)
    (out_dir / "task_511_live_source_feature_revalidation.md").write_text(report_task511(decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"live_source_feature_readiness_audit": audit, "task_511_decision": decision}


def report_task511(decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 511 - Live Source Feature Revalidation",
            "",
            "## Quant Expert Report",
            "",
            "Task511 checks whether Task505 can be revalidated with live-source-grade features. It cannot yet: raw receive timestamps, historical status/LULD, and full depth book are not available for the Task505 history.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            f"- Usable sources: {d['usable_source_count']} / {d['required_source_count']}",
            f"- Live-source revalidation ready: {d['live_source_revalidation_ready_flag']}",
            "- Missing data was not approximated.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task505-panel", type=Path, default=DEFAULT_TASK505_PANEL)
    parser.add_argument("--task503-panel", type=Path, default=DEFAULT_TASK503_PANEL)
    parser.add_argument("--data-raw", type=Path, default=DEFAULT_DATA_RAW)
    args = parser.parse_args()
    build_task508_cost_stress_validation(task505_panel_path=args.task505_panel)
    build_task509_walk_forward_oos_validation(task503_panel_path=args.task503_panel)
    build_task510_entry_reduce_failure_decomposition(task505_panel_path=args.task505_panel)
    build_task511_live_source_feature_revalidation(data_raw=args.data_raw)


if __name__ == "__main__":
    main()
