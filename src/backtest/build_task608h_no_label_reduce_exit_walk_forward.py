from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task505_two_year_pnl_grid import simulate_portfolio
from src.backtest.build_task608g_live_detectable_entry_failure_path_diagnostics import (
    REPORT_DIR as TASK608G_DIR,
    TASK509_PANEL,
    build_state_signal_interaction_summary,
    build_task608g_live_detectable_entry_failure_path_diagnostics,
    signal_columns,
)


TASK_ID = "Task608H"
REPORT_DIR = Path("docs/reports/task_608h_no_label_reduce_exit_walk_forward")
TASK608G_PATH_PANEL = TASK608G_DIR / "entry_failure_path_panel.csv"

TOP_N_VALUES = [1, 3, 5]
ACTIONS = ["full_exit", "reduce_50"]
EXTRA_COST_RATES = [0.0, 0.005, 0.010]


def build_task608h_no_label_reduce_exit_walk_forward(
    *,
    task509_panel_path: Path = TASK509_PANEL,
    task608g_path_panel: Path = TASK608G_PATH_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    base_panel = load_base_panel(task509_panel_path)
    path_panel = load_or_build_path_panel(task608g_path_panel)
    merged = merge_base_and_path(base_panel, path_panel)
    baseline_fold = build_baseline_fold_quality(merged)
    rule_selection, simulation_panel = run_walk_forward_reduce_simulation(merged)
    quality = build_reduce_quality(merged, baseline_fold, simulation_panel)
    decisions = build_decisions(quality)

    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_fold.to_csv(out_dir / "baseline_walk_forward_quality.csv", index=False)
    rule_selection.to_csv(out_dir / "walk_forward_reduce_rule_selection.csv", index=False)
    simulation_panel.to_csv(out_dir / "walk_forward_reduce_simulation_panel.csv", index=False)
    quality.to_csv(out_dir / "walk_forward_reduce_quality.csv", index=False)
    decisions.to_csv(out_dir / "task_608h_decision.csv", index=False)
    (out_dir / "task_608h_no_label_reduce_exit_walk_forward.md").write_text(
        render_report(baseline_fold, quality, decisions),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "baseline_walk_forward_quality": baseline_fold,
        "walk_forward_reduce_rule_selection": rule_selection,
        "walk_forward_reduce_simulation_panel": simulation_panel,
        "walk_forward_reduce_quality": quality,
        "task_608h_decision": decisions,
    }


def load_base_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["simulated_exit_ts"] = pd.to_datetime(frame["simulated_exit_ts"], utc=True, errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["entry_reduce_failure_flag"] = pd.to_numeric(
        frame["entry_reduce_failure_flag"], errors="coerce"
    ).fillna(0).astype(int)
    frame["win_flag"] = pd.to_numeric(frame["win_flag"], errors="coerce").fillna(0).astype(int)
    frame = frame.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    frame["task608h_original_net_return_from_entry"] = frame["net_return_from_entry"]
    return frame.sort_values("entry_ts").reset_index(drop=True)


def load_or_build_path_panel(path: Path) -> pd.DataFrame:
    if not Path(path).exists():
        build_task608g_live_detectable_entry_failure_path_diagnostics()
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    for column in signal_columns():
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
    for column in ["symbol_ret_60m", "symbol_ret_120m"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def merge_base_and_path(base_panel: pd.DataFrame, path_panel: pd.DataFrame) -> pd.DataFrame:
    path_cols = [
        "lifecycle_id",
        "symbol_ret_60m",
        "symbol_ret_120m",
        *signal_columns(),
    ]
    state_cols = [
        "timing_state",
        "symbol_multiday_setup_state",
        "theme_regime_state_v4",
        "theme_id",
        "symbol",
    ]
    path_cols.extend([column for column in state_cols if column in path_panel.columns])
    path = path_panel[[column for column in path_cols if column in path_panel.columns]].drop_duplicates("lifecycle_id")
    merged = base_panel.merge(path, on="lifecycle_id", how="left", suffixes=("", "_path"))
    for column in signal_columns():
        if column not in merged.columns:
            merged[column] = 0
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0).astype(int)
    return merged


def build_baseline_fold_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for quarter, group in panel.groupby("quarter", sort=True):
        row = aggregate(group)
        capital = simulate_portfolio(group, max_positions=10).quality
        row.update(
            {
                "quarter": quarter,
                "scenario": "baseline",
                "action": "none",
                "top_n": 0,
                "extra_cost_rate": 0.0,
                "capital_pnl_pct": float(capital["two_year_capital_pnl_pct"]),
                "max_drawdown_pct": float(capital["max_drawdown_pct"]),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def run_walk_forward_reduce_simulation(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    quarters = sorted(panel["quarter"].astype(str).unique().tolist())
    selection_rows = []
    simulation_rows = []
    for idx in range(1, len(quarters)):
        train_quarters = quarters[:idx]
        test_quarter = quarters[idx]
        train = panel[panel["quarter"].astype(str).isin(train_quarters)].copy()
        test = panel[panel["quarter"].astype(str).eq(test_quarter)].copy()
        candidates = build_state_signal_interaction_summary(train).copy()
        candidates = candidates[candidates["diagnostic_pass_flag"].astype(int).eq(1)].reset_index(drop=True)
        for top_n in TOP_N_VALUES:
            selected = candidates.head(top_n).copy()
            selected_names = selected["candidate_name"].astype(str).tolist() if not selected.empty else []
            selection_rows.append(
                {
                    "test_quarter": test_quarter,
                    "train_quarters": "|".join(train_quarters),
                    "top_n": top_n,
                    "selected_candidate_count": len(selected_names),
                    "selected_candidates": " || ".join(selected_names),
                    "label_used_in_test_assignment_flag": 0,
                }
            )
            for action in ACTIONS:
                for cost in EXTRA_COST_RATES:
                    simulated = apply_reduce_candidates(
                        test,
                        selected_names,
                        action=action,
                        extra_cost_rate=cost,
                        top_n=top_n,
                        test_quarter=test_quarter,
                    )
                    simulation_rows.extend(simulated.to_dict(orient="records"))
    return pd.DataFrame(selection_rows), pd.DataFrame(simulation_rows)


def apply_reduce_candidates(
    test: pd.DataFrame,
    candidates: list[str],
    *,
    action: str,
    extra_cost_rate: float,
    top_n: int,
    test_quarter: str,
) -> pd.DataFrame:
    rows = []
    for item in test.to_dict(orient="records"):
        row = dict(item)
        triggered_name = first_triggered_candidate(row, candidates)
        triggered = bool(triggered_name)
        horizon = candidate_horizon(triggered_name) if triggered_name else 0
        original_return = float(row["net_return_from_entry"])
        path_return = path_return_for_horizon(row, horizon)
        simulated_return = original_return
        simulated_exit_ts = pd.Timestamp(row["simulated_exit_ts"])
        if triggered and path_return is not None:
            if action == "full_exit":
                simulated_return = path_return - extra_cost_rate
                simulated_exit_ts = pd.Timestamp(row["entry_ts"]) + pd.Timedelta(minutes=horizon)
            elif action == "reduce_50":
                simulated_return = 0.5 * (path_return - extra_cost_rate) + 0.5 * original_return
        row.update(
            {
                "scenario": f"top{top_n}_{action}_cost{int(extra_cost_rate * 10000)}bp",
                "test_quarter": test_quarter,
                "action": action,
                "top_n": top_n,
                "extra_cost_rate": extra_cost_rate,
                "triggered_reduce_flag": int(triggered and path_return is not None),
                "triggered_candidate": triggered_name or "",
                "trigger_horizon_minutes": horizon,
                "task608h_original_net_return_from_entry": original_return,
                "task608h_simulated_net_return_from_entry": simulated_return,
                "net_return_from_entry": simulated_return,
                "win_flag": int(simulated_return > 0),
                "add_scale_success_flag": int(simulated_return >= 0.03),
                "entry_reduce_failure_flag": int(simulated_return <= -0.03),
                "false_positive_flag": int(simulated_return <= 0),
                "simulated_exit_ts": simulated_exit_ts,
                "label_used_in_test_assignment_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_reduce_quality(
    baseline_panel: pd.DataFrame,
    baseline_fold: pd.DataFrame,
    simulation_panel: pd.DataFrame,
) -> pd.DataFrame:
    comparable_ids = set(simulation_panel["lifecycle_id"].astype(str).unique().tolist())
    comparable_baseline = baseline_panel[baseline_panel["lifecycle_id"].astype(str).isin(comparable_ids)].copy()
    baseline_all = aggregate(comparable_baseline)
    baseline_capital = simulate_portfolio(comparable_baseline, max_positions=10).quality
    baseline_avg = float(baseline_all["avg_net_return_pct"])
    baseline_er = float(baseline_all["entry_reduce_failure_rate"])
    rows = []
    for scenario, group in simulation_panel.groupby("scenario", sort=True):
        quality = aggregate(group)
        capital = simulate_portfolio(group, max_positions=10).quality
        fold_frame = pd.DataFrame(
            [
                {"test_quarter": quarter, **aggregate(part)}
                for quarter, part in group.groupby("test_quarter", sort=True)
            ]
        )
        positive_fold_rate = float((pd.to_numeric(fold_frame["avg_net_return_pct"], errors="coerce") > 0).mean()) if not fold_frame.empty else 0.0
        triggered = group[group["triggered_reduce_flag"].astype(int).eq(1)]
        quality.update(
            {
                "scenario": scenario,
                "action": str(group["action"].iloc[0]),
                "top_n": int(group["top_n"].iloc[0]),
                "extra_cost_rate": float(group["extra_cost_rate"].iloc[0]),
                "fold_count": int(group["test_quarter"].nunique()),
                "positive_fold_rate": positive_fold_rate,
                "triggered_count": int(group["triggered_reduce_flag"].sum()),
                "trigger_rate": float(group["triggered_reduce_flag"].mean()) if len(group) else 0.0,
                "triggered_original_failure_rate": float(triggered["task608h_original_net_return_from_entry"].le(-0.03).mean()) if len(triggered) else 0.0,
                "clean_false_alarm_count": int(
                    (
                        group["triggered_reduce_flag"].astype(int).eq(1)
                        & pd.to_numeric(group["task608h_original_net_return_from_entry"], errors="coerce").gt(-0.03)
                    ).sum()
                ),
                "baseline_avg_net_return_pct": baseline_avg,
                "baseline_entry_reduce_failure_rate": baseline_er,
                "baseline_capital_pnl_pct": float(baseline_capital["two_year_capital_pnl_pct"]),
                "delta_avg_net_return_pct": float(quality["avg_net_return_pct"]) - baseline_avg,
                "delta_entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]) - baseline_er,
                "capital_pnl_pct": float(capital["two_year_capital_pnl_pct"]),
                "max_drawdown_pct": float(capital["max_drawdown_pct"]),
            }
        )
        rows.append(quality)
    return pd.DataFrame(rows).sort_values(
        ["extra_cost_rate", "delta_avg_net_return_pct", "positive_fold_rate"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def build_decisions(quality: pd.DataFrame) -> pd.DataFrame:
    if quality.empty:
        return pd.DataFrame(
            [
                {
                    "task_id": TASK_ID,
                    "decision": "FAIL_NO_REDUCE_SIMULATION_ROWS",
                    "pass_flag": 0,
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "next_action": "Fix simulation coverage before any refinement claim.",
                }
            ]
        )
    stress = quality[quality["extra_cost_rate"].astype(float).eq(0.005)].copy()
    passing = stress[
        stress["delta_avg_net_return_pct"].astype(float).gt(0)
        & stress["delta_entry_reduce_failure_rate"].astype(float).lt(0)
        & stress["positive_fold_rate"].astype(float).ge(0.60)
        & stress["triggered_count"].astype(int).gt(0)
    ].copy()
    best = (passing if not passing.empty else stress).sort_values(
        ["delta_avg_net_return_pct", "positive_fold_rate"], ascending=[False, False]
    ).iloc[0]
    pass_flag = int(not passing.empty)
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_NO_LABEL_REDUCE_SIM_CANDIDATE_FOUND_NEEDS_RULE_LOCK"
                    if pass_flag
                    else "FAIL_NO_LABEL_REDUCE_SIM_DID_NOT_IMPROVE_WITH_COST"
                ),
                "pass_flag": pass_flag,
                "best_scenario_50bp": best["scenario"],
                "best_delta_avg_net_return_pct_50bp": float(best["delta_avg_net_return_pct"]),
                "best_delta_entry_reduce_failure_rate_50bp": float(best["delta_entry_reduce_failure_rate"]),
                "best_positive_fold_rate_50bp": float(best["positive_fold_rate"]),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_action": (
                    "Lock the candidate family and rerun OOS with full cost/slippage and parameter-neighborhood stress."
                    if pass_flag
                    else "Do not refine this reducer yet; investigate why fold-forward candidates mostly hit clean trades and add stronger live features."
                ),
            }
        ]
    )


def render_report(baseline_fold: pd.DataFrame, quality: pd.DataFrame, decisions: pd.DataFrame) -> str:
    decision = decisions.iloc[0].to_dict()
    baseline_avg = float(baseline_fold["avg_net_return_pct"].mean()) if not baseline_fold.empty else 0.0
    baseline_er = float(baseline_fold["entry_reduce_failure_rate"].mean()) if not baseline_fold.empty else 0.0
    best_rows = quality.sort_values(["extra_cost_rate", "delta_avg_net_return_pct"], ascending=[True, False]).head(8)
    best_lines = [
        (
            f"- {row['scenario']}: delta avg {float(row['delta_avg_net_return_pct']):.2f} pct points, "
            f"entry-reduce delta {float(row['delta_entry_reduce_failure_rate']):.2%}, "
            f"positive folds {float(row['positive_fold_rate']):.2%}, triggers {int(row['triggered_count'])}"
        )
        for _, row in best_rows.iterrows()
    ]
    return "\n".join(
        [
            "# Task608H No-Label Reduce/Exit Walk-Forward",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {decision['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            f"- Best 50bp scenario: {decision.get('best_scenario_50bp', '')}",
            f"- Best 50bp delta avg net: {float(decision.get('best_delta_avg_net_return_pct_50bp', 0.0)):.2f} pct points.",
            f"- Best 50bp entry-reduce delta: {float(decision.get('best_delta_entry_reduce_failure_rate_50bp', 0.0)):.2%}.",
            "- What changed: state/path candidates are now applied fold-forward without using test labels.",
            f"- Next action: {decision['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task509 OOS rows plus Task608G live path features.",
            "- Exact join keys: existing `lifecycle_id` only; no symbol/date/price/time lifecycle fallback.",
            "- Leakage audit: candidates are selected from prior quarters and applied to the next quarter. Test-quarter labels are not used for assignment.",
            "- Split/OOS metrics: fold-forward by quarter from Task509 rows.",
            "- Failure decomposition: see `walk_forward_reduce_rule_selection.csv`, `walk_forward_reduce_simulation_panel.csv`, and `walk_forward_reduce_quality.csv`.",
            "- Cost/slippage stress where PnL changed: scenarios include 0bp, 50bp, and 100bp extra reduce/exit costs.",
            "- Remaining blockers: pass here is still not strategy acceptance; it only promotes a candidate family to rule-lock testing.",
            "",
            f"Baseline fold mean avg net: {baseline_avg:.2f}%",
            f"Baseline fold mean entry-reduce: {baseline_er:.2%}",
            "",
            "Top scenarios:",
            *best_lines,
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: we tested whether early warning signs can improve the next quarter without looking at that quarter's labels.",
            "- Why it matters: this is the first real check that entry-reduce can become a live rule instead of a hindsight label.",
            "- Whether this changes capital/deployment readiness: no. It stays research only.",
            "- Plain-language next step: only if this passes under cost, lock the rule family and stress it harder.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def first_triggered_candidate(row: dict[str, Any], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate_triggered(row, candidate):
            return candidate
    return ""


def candidate_triggered(row: dict[str, Any], candidate: str) -> bool:
    for part in str(candidate).split("&"):
        if "=" in part:
            column, value = part.split("=", 1)
            if str(row.get(column, "")) != value:
                return False
        else:
            if int(row.get(part, 0) or 0) != 1:
                return False
    return True


def candidate_horizon(candidate: str) -> int:
    if "60m" in str(candidate):
        return 60
    if "120m" in str(candidate):
        return 120
    return 120


def path_return_for_horizon(row: dict[str, Any], horizon: int) -> float | None:
    value = row.get(f"symbol_ret_{horizon}m")
    if value is None or pd.isna(value):
        return None
    return float(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task509-panel", type=Path, default=TASK509_PANEL)
    parser.add_argument("--task608g-path-panel", type=Path, default=TASK608G_PATH_PANEL)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608h_no_label_reduce_exit_walk_forward(
        task509_panel_path=args.task509_panel,
        task608g_path_panel=args.task608g_path_panel,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608h_decision"].iloc[0]
    print(f"[TASK608H] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
