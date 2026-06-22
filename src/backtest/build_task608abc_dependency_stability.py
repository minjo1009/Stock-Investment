from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task505_two_year_pnl_grid import build_cell_pool, simulate_portfolio
from src.backtest.build_task508_511_task505_validation import assign_cells_like, load_panel


TASK_ID = "Task608ABC"
REPORT_DIR = Path("docs/reports/task_608abc_dependency_stability")
TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK509_PANEL = Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")
TASK608_METRICS = Path("docs/reports/task_608_strategy_backtest_firm_grade_review/strategy_backtest_metric_snapshot.csv")


def build_task608abc_dependency_stability(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    task509_panel_path: Path = TASK509_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    wf_panel = load_oos_panel(task509_panel_path)
    source_panel = load_panel(task503_panel_path)
    metric_snapshot = _read_one(TASK608_METRICS)
    baseline = baseline_oos_metrics(wf_panel, metric_snapshot)
    theme = build_theme_dependency_audit(wf_panel, baseline)
    symbol = build_symbol_dependency_audit(wf_panel, baseline)
    neighborhood = build_parameter_neighborhood_oos(source_panel)
    decisions = build_decisions(theme, symbol, neighborhood, baseline)

    out_dir.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(out_dir / "baseline_oos_metrics.csv", index=False)
    theme.to_csv(out_dir / "theme_dependency_audit.csv", index=False)
    symbol.to_csv(out_dir / "symbol_dependency_audit.csv", index=False)
    neighborhood.to_csv(out_dir / "parameter_neighborhood_stability.csv", index=False)
    decisions.to_csv(out_dir / "task_608abc_decision.csv", index=False)
    (out_dir / "task_608abc_dependency_stability.md").write_text(
        render_report(baseline.iloc[0].to_dict(), theme, symbol, neighborhood, decisions),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "baseline_oos_metrics": baseline,
        "theme_dependency_audit": theme,
        "symbol_dependency_audit": symbol,
        "parameter_neighborhood_stability": neighborhood,
        "task_608abc_decision": decisions,
    }


def load_oos_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["simulated_exit_ts"] = pd.to_datetime(frame["simulated_exit_ts"], utc=True, errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame = frame.dropna(subset=["entry_ts", "simulated_exit_ts", "net_return_from_entry", "lifecycle_id"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    return frame.sort_values("entry_ts").reset_index(drop=True)


def baseline_oos_metrics(panel: pd.DataFrame, metric_snapshot: dict[str, Any]) -> pd.DataFrame:
    quality = aggregate(panel)
    capital = simulate_portfolio(panel, max_positions=10).quality
    quality["two_year_capital_pnl_pct"] = capital["two_year_capital_pnl_pct"]
    quality["max_drawdown_pct"] = capital["max_drawdown_pct"]
    metrics = _metrics_row(panel, quality, "baseline", "baseline", "", panel)
    metrics.update(
        {
            "task_id": TASK_ID,
            "baseline_avg_net_pct_from_task608": _float(metric_snapshot.get("walk_forward_avg_net_pct")),
            "baseline_entry_reduce_from_task608": _float(metric_snapshot.get("walk_forward_entry_reduce_rate")),
            "strategy_acceptance_status": "NOT_ACCEPTED",
            "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        }
    )
    return pd.DataFrame([metrics])


def build_theme_dependency_audit(panel: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    baseline_avg = float(baseline.iloc[0]["avg_net_return_pct"])
    rows = []
    for theme in sorted(panel["theme_id"].dropna().astype(str).unique().tolist()):
        filtered = panel[~panel["theme_id"].astype(str).eq(theme)].copy()
        quality = aggregate(filtered) if not filtered.empty else _empty_quality()
        capital = simulate_portfolio(filtered, max_positions=10).quality
        quality["two_year_capital_pnl_pct"] = capital["two_year_capital_pnl_pct"]
        quality["max_drawdown_pct"] = capital["max_drawdown_pct"]
        row = _metrics_row(filtered, quality, "leave_one_theme_out", theme, "theme_id", filtered)
        row.update(_stability_flags(row, baseline_avg, pass_degradation=0.40, min_count=25))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["pass_flag", "degradation_ratio", "removed_value"]).reset_index(drop=True)


def build_symbol_dependency_audit(panel: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    baseline_avg = float(baseline.iloc[0]["avg_net_return_pct"])
    counts = panel["symbol"].dropna().astype(str).value_counts()
    rows = []
    for top_n in [1, 3, 5]:
        removed = counts.head(top_n).index.tolist()
        filtered = panel[~panel["symbol"].astype(str).isin(removed)].copy()
        quality = aggregate(filtered) if not filtered.empty else _empty_quality()
        capital = simulate_portfolio(filtered, max_positions=10).quality
        quality["two_year_capital_pnl_pct"] = capital["two_year_capital_pnl_pct"]
        quality["max_drawdown_pct"] = capital["max_drawdown_pct"]
        row = _metrics_row(filtered, quality, f"leave_top{top_n}_symbols_out", "|".join(removed), "symbol", filtered)
        row.update(_stability_flags(row, baseline_avg, pass_degradation=0.50, min_count=25))
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def build_parameter_neighborhood_oos(source_panel: pd.DataFrame) -> pd.DataFrame:
    recent = source_panel[source_panel["entry_ts"].ge(source_panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    quarters = sorted(recent["quarter"].dropna().astype(str).unique().tolist())
    configs = _neighbor_configs()
    rows = []
    for config in configs:
        fold_rows = []
        panels = []
        for idx in range(2, len(quarters)):
            train = recent[recent["quarter"].isin(quarters[:idx])].copy()
            test = recent[recent["quarter"].eq(quarters[idx])].copy()
            if len(train) < 100 or len(test) < 5:
                continue
            pool = build_cell_pool(train)
            cells = pool[
                pool["cell_dims"].eq(config["cell_dims"])
                & pool["avg_net_return_pct"].ge(float(config["min_avg_net_pct"]))
                & pool["win_rate"].ge(float(config["min_win_rate"]))
                & pool["entry_reduce_failure_rate"].le(float(config["max_entry_reduce_rate"]))
            ].copy()
            assigned = assign_cells_like(test, cells)
            result = simulate_portfolio(assigned, max_positions=int(config["max_positions"]))
            fold_metric = aggregate(result.accepted_panel)
            fold_metric.update(
                {
                    **config,
                    "test_quarter": quarters[idx],
                    "selected_cell_count": int(len(cells)),
                    "fold_lifecycle_count": int(len(result.accepted_panel)),
                    "fold_capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                }
            )
            fold_rows.append(fold_metric)
            if not result.accepted_panel.empty:
                panels.append(result.accepted_panel)
        panel = pd.concat(panels, ignore_index=True) if panels else pd.DataFrame()
        fold_frame = pd.DataFrame(fold_rows)
        positive_fold_rate = (
            float((fold_frame["avg_net_return_pct"].astype(float) > 0).mean()) if not fold_frame.empty else 0.0
        )
        weak_fold_count = (
            int(
                (
                    fold_frame["avg_net_return_pct"].astype(float).le(0)
                    | fold_frame["entry_reduce_failure_rate"].astype(float).ge(0.50)
                ).sum()
            )
            if not fold_frame.empty
            else 0
        )
        summary = aggregate(panel) if not panel.empty else _empty_quality()
        rows.append(
            {
                **config,
                "neighbor_name": _config_name(config),
                "fold_count": int(len(fold_frame)),
                "lifecycle_count": int(summary["lifecycle_count"]),
                "avg_net_return_pct": float(summary["avg_net_return_pct"]),
                "win_rate": float(summary["win_rate"]),
                "entry_reduce_failure_rate": float(summary["entry_reduce_failure_rate"]),
                "positive_fold_rate": positive_fold_rate,
                "weak_fold_count": weak_fold_count,
                "pass_flag": int(positive_fold_rate >= 0.70 and float(summary["avg_net_return_pct"]) > 0),
            }
        )
    frame = pd.DataFrame(rows)
    positive_rate = float(frame["pass_flag"].mean()) if not frame.empty else 0.0
    frame["neighborhood_positive_rate"] = positive_rate
    frame["neighborhood_pass_flag"] = int(positive_rate >= 0.70)
    return frame.sort_values(["pass_flag", "avg_net_return_pct"], ascending=[False, False]).reset_index(drop=True)


def build_decisions(theme: pd.DataFrame, symbol: pd.DataFrame, neighborhood: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    theme_pass = int(not theme.empty and theme["pass_flag"].astype(int).eq(1).all())
    symbol_pass = int(not symbol.empty and symbol["pass_flag"].astype(int).eq(1).all())
    neighborhood_pass = int(not neighborhood.empty and int(neighborhood["neighborhood_pass_flag"].iloc[0]) == 1)
    return pd.DataFrame(
        [
            {
                "task_id": "Task608A",
                "decision": "PASS_THEME_DEPENDENCY_ROBUST" if theme_pass else "FAIL_THEME_DEPENDENCY_RISK",
                "pass_flag": theme_pass,
                "worst_degradation_ratio": float(theme["degradation_ratio"].max()) if not theme.empty else 1.0,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": "If fail, do not refine until theme dependency is explained.",
            },
            {
                "task_id": "Task608B",
                "decision": "PASS_SYMBOL_DEPENDENCY_ROBUST" if symbol_pass else "FAIL_SYMBOL_DEPENDENCY_RISK",
                "pass_flag": symbol_pass,
                "worst_degradation_ratio": float(symbol["degradation_ratio"].max()) if not symbol.empty else 1.0,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": "If fail, prove the edge is not carried by the top symbols before paper-shadow promotion.",
            },
            {
                "task_id": "Task608C",
                "decision": "PASS_PARAMETER_NEIGHBORHOOD_STABLE" if neighborhood_pass else "FAIL_PARAMETER_NEIGHBORHOOD_SPIKE_RISK",
                "pass_flag": neighborhood_pass,
                "neighborhood_positive_rate": float(neighborhood["neighborhood_positive_rate"].iloc[0]) if not neighborhood.empty else 0.0,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": "If fail, prefer ensemble or reject the single best cell as a parameter spike.",
            },
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_DEPENDENCY_STABILITY_DIAGNOSTIC"
                    if theme_pass and symbol_pass and neighborhood_pass
                    else "FAIL_DEPENDENCY_STABILITY_NOT_FIRM_GRADE"
                ),
                "pass_flag": int(theme_pass and symbol_pass and neighborhood_pass),
                "baseline_avg_net_pct": float(baseline.iloc[0]["avg_net_return_pct"]),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": (
                    "Proceed to Task608D/E/F: regime failure map, entry-reduce attribution, and ensemble validation."
                    if theme_pass and symbol_pass and neighborhood_pass
                    else "Do not refine until failed dependency or parameter stability rows are explained."
                ),
            },
        ]
    )


def render_report(
    baseline: dict[str, Any],
    theme: pd.DataFrame,
    symbol: pd.DataFrame,
    neighborhood: pd.DataFrame,
    decisions: pd.DataFrame,
) -> str:
    summary_decision = decisions[decisions["task_id"].eq(TASK_ID)].iloc[0].to_dict()
    theme_decision = decisions[decisions["task_id"].eq("Task608A")].iloc[0].to_dict()
    symbol_decision = decisions[decisions["task_id"].eq("Task608B")].iloc[0].to_dict()
    neighbor_decision = decisions[decisions["task_id"].eq("Task608C")].iloc[0].to_dict()
    return "\n".join(
        [
            "# Task608A/B/C Dependency And Stability Audit",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {summary_decision['decision']}",
            f"- Task608A theme decision: {theme_decision['decision']}",
            f"- Task608B symbol decision: {symbol_decision['decision']}",
            f"- Task608C parameter decision: {neighbor_decision['decision']}",
            f"- Baseline OOS avg net: {float(baseline['avg_net_return_pct']):.2f}%",
            f"- Baseline OOS count: {int(baseline['lifecycle_count'])}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- What changed: theme, symbol, and parameter-neighborhood robustness were tested before any refinement.",
            f"- Next action: {summary_decision['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task509 walk-forward OOS assignment panel and Task503 lifecycle panel; no new alpha source was introduced.",
            "- Exact join keys: existing lifecycle_id rows only; no inferred lifecycle matching.",
            "- Leakage audit: removal tests and neighborhood tests use rule parameters and pre-existing assignment fields, not outcome labels for assignment.",
            "- Split/OOS metrics: A/B use walk-forward OOS assignment rows; C replays neighboring rule thresholds through fold-by-fold train/test evaluation.",
            "- Failure decomposition: see `theme_dependency_audit.csv`, `symbol_dependency_audit.csv`, and `parameter_neighborhood_stability.csv`.",
            "- Cost/slippage stress: unchanged from Task508; this task is dependency and overfit stability only.",
            "- Remaining blockers: any failed A/B/C decision blocks refinement as firm-grade improvement.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: we tried to break the strategy by removing themes, removing top symbols, and changing nearby parameters.",
            "- Why it matters: if the strategy survives this, it is less likely to be one lucky theme, one lucky stock, or one lucky parameter.",
            "- Whether this changes capital/deployment readiness: no. This is still research only.",
            "- Plain-language next step: continue with failure-regime mapping, entry-reduce attribution, and ensemble validation.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def _neighbor_configs() -> list[dict[str, Any]]:
    configs = []
    for min_avg in [8.0, 12.0]:
        for min_win in [0.50, 0.55, 0.60]:
            for max_er in [0.35, 0.45]:
                configs.append(
                    {
                        "cell_dims": "theme_id|timing_state",
                        "min_avg_net_pct": min_avg,
                        "min_win_rate": min_win,
                        "max_entry_reduce_rate": max_er,
                        "max_positions": 10,
                    }
                )
    return configs


def _config_name(config: dict[str, Any]) -> str:
    return (
        f"{config['cell_dims']}_avg{config['min_avg_net_pct']:g}_"
        f"win{int(float(config['min_win_rate']) * 100)}_"
        f"er{int(float(config['max_entry_reduce_rate']) * 100)}_"
        f"pos{config['max_positions']}"
    )


def _metrics_row(
    accepted_panel: pd.DataFrame,
    quality: dict[str, Any],
    scenario: str,
    removed_value: str,
    removed_dimension: str,
    candidate_panel: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "removed_dimension": removed_dimension,
        "removed_value": removed_value,
        "candidate_count_after_removal": int(len(candidate_panel)),
        "lifecycle_count": int(quality.get("lifecycle_count", len(accepted_panel)) or 0),
        "avg_net_return_pct": float(quality.get("avg_net_return_pct", 0.0) or 0.0),
        "win_rate": float(quality.get("win_rate", 0.0) or 0.0),
        "entry_reduce_failure_rate": float(quality.get("entry_reduce_failure_rate", 0.0) or 0.0),
        "capital_pnl_pct": float(quality.get("two_year_capital_pnl_pct", 0.0) or 0.0),
        "max_drawdown_pct": float(quality.get("max_drawdown_pct", 0.0) or 0.0),
    }


def _stability_flags(row: dict[str, Any], baseline_avg: float, *, pass_degradation: float, min_count: int) -> dict[str, Any]:
    avg = float(row.get("avg_net_return_pct", 0.0) or 0.0)
    degradation = max(0.0, (baseline_avg - avg) / abs(baseline_avg)) if abs(baseline_avg) > 1e-9 else 1.0
    pass_flag = int(avg > 0.0 and degradation <= pass_degradation and int(row.get("lifecycle_count", 0)) >= min_count)
    return {
        "baseline_avg_net_pct": baseline_avg,
        "degradation_ratio": degradation,
        "pass_flag": pass_flag,
    }


def _empty_quality() -> dict[str, Any]:
    return {
        "lifecycle_count": 0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
    }


def _read_one(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _float(value: object) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task503-panel", type=Path, default=TASK503_PANEL)
    parser.add_argument("--task509-panel", type=Path, default=TASK509_PANEL)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608abc_dependency_stability(
        task503_panel_path=args.task503_panel,
        task509_panel_path=args.task509_panel,
        out_dir=args.out_dir,
    )
    decisions = artifacts["task_608abc_decision"]
    summary = decisions[decisions["task_id"].eq(TASK_ID)].iloc[0]
    print(f"[TASK608ABC] decision={summary['decision']} pass={int(summary['pass_flag'])}")


if __name__ == "__main__":
    main()
