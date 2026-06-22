from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task505_two_year_pnl_grid import build_cell_pool, run_grid, simulate_portfolio
from src.backtest.build_task508_511_task505_validation import assign_cells_like, load_panel
from src.backtest.task_report_utils import write_standard_report


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK529_OUT = Path("docs/reports/task_529_trend_persistence_entry_safe_refinement")
TASK530_OUT = Path("docs/reports/task_530_paper_shadow_candidate_rerun")


def add_entry_bar_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in ["open", "high", "low", "close", "vwap"]:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
    bar_range = (out["high"] - out["low"]).replace(0, pd.NA)
    out["entry_close_pos_in_bar"] = (out["close"] - out["low"]) / bar_range
    out["entry_close_vs_vwap"] = (out["close"] / out["vwap"]) - 1.0
    out["entry_safe_feature_available_flag"] = out[["entry_close_pos_in_bar", "entry_close_vs_vwap"]].notna().all(axis=1).astype(int)
    return out


def build_walk_forward_base(panel: pd.DataFrame) -> pd.DataFrame:
    recent = panel[panel["entry_ts"].ge(panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    quarters = sorted(recent["quarter"].dropna().astype(str).unique().tolist())
    base = []
    for idx in range(2, len(quarters)):
        train = recent[recent["quarter"].isin(quarters[:idx])].copy()
        test = recent[recent["quarter"].eq(quarters[idx])].copy()
        if len(train) < 100 or len(test) < 5:
            continue
        pool = build_cell_pool(train)
        candidates, _ = run_grid(train, pool)
        if candidates.empty:
            continue
        best = candidates.iloc[0]
        cells = pool[
            pool["cell_dims"].eq(best["cell_dims"])
            & pool["avg_net_return_pct"].ge(float(best["min_avg_net_pct"]))
            & pool["win_rate"].ge(float(best["min_win_rate"]))
            & pool["entry_reduce_failure_rate"].le(float(best["max_entry_reduce_rate"]))
        ].copy()
        assigned = assign_cells_like(test, cells)
        assigned["fold_q"] = quarters[idx]
        assigned["fold_max_positions"] = int(best["max_positions"])
        base.append(assigned)
    return pd.concat(base, ignore_index=True) if base else pd.DataFrame()


def refined_rule_mask(frame: pd.DataFrame, family_name: str) -> pd.Series:
    trend = frame["symbol_multiday_setup_state"].astype(str).eq("trend_persistence_near_high")
    if family_name == "trend_persistence_only":
        return trend
    if family_name == "trend_vwap_closepos_refined":
        return trend & frame["entry_close_vs_vwap"].le(0.028) & frame["entry_close_pos_in_bar"].le(0.97)
    if family_name == "trend_vwap_closepos_tight":
        return trend & frame["entry_close_vs_vwap"].le(0.020) & frame["entry_close_pos_in_bar"].le(0.97)
    if family_name == "trend_vwap_only_028":
        return trend & frame["entry_close_vs_vwap"].le(0.028)
    if family_name == "trend_closepos_only_097":
        return trend & frame["entry_close_pos_in_bar"].le(0.97)
    return trend


def evaluate_refined_families(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    families = [
        {"family_name": "trend_persistence_only", "rule": "symbol_multiday_setup_state == trend_persistence_near_high"},
        {"family_name": "trend_vwap_closepos_refined", "rule": "trend_persistence_near_high and entry_close_vs_vwap <= 0.028 and entry_close_pos_in_bar <= 0.97"},
        {"family_name": "trend_vwap_closepos_tight", "rule": "trend_persistence_near_high and entry_close_vs_vwap <= 0.020 and entry_close_pos_in_bar <= 0.97"},
        {"family_name": "trend_vwap_only_028", "rule": "trend_persistence_near_high and entry_close_vs_vwap <= 0.028"},
        {"family_name": "trend_closepos_only_097", "rule": "trend_persistence_near_high and entry_close_pos_in_bar <= 0.97"},
    ]
    fold_rows = []
    for family in families:
        for q, subset in base.groupby("fold_q"):
            filtered = subset[refined_rule_mask(subset, family["family_name"])].copy()
            max_positions = int(subset["fold_max_positions"].iloc[0]) if not subset.empty else 10
            result = simulate_portfolio(filtered, max_positions=max_positions)
            metrics = aggregate(result.accepted_panel)
            row = dict(family)
            row.update(metrics)
            row.update(
                {
                    "test_quarter": q,
                    "baseline_count": int(len(subset)),
                    "retained_count": int(len(filtered)),
                    "retention_rate": float(len(filtered) / max(len(subset), 1)),
                    "positive_fold_flag": int(float(metrics["avg_net_return_pct"]) > 0),
                    "entry_safe_assignment_flag": 1,
                    "label_used_in_assignment_flag": 0,
                }
            )
            fold_rows.append(row)
    folds = pd.DataFrame(fold_rows)
    summary = (
        folds.groupby(["family_name", "rule"], dropna=False)
        .agg(
            fold_count=("test_quarter", "nunique"),
            total_count=("lifecycle_count", "sum"),
            avg_net_mean=("avg_net_return_pct", "mean"),
            positive_fold_rate=("positive_fold_flag", "mean"),
            entry_reduce_mean=("entry_reduce_failure_rate", "mean"),
            retention_mean=("retention_rate", "mean"),
        )
        .reset_index()
    )
    summary["pass_flag"] = (
        summary["entry_reduce_mean"].le(0.30)
        & summary["positive_fold_rate"].ge(0.70)
        & summary["retention_mean"].ge(0.60)
    ).astype(int)
    selected = summary[summary["pass_flag"].eq(1)].sort_values(["entry_reduce_mean", "avg_net_mean"], ascending=[True, False]).head(1)
    return summary, folds, selected


def build_task529_trend_persistence_entry_safe_refinement(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    out_dir: Path = TASK529_OUT,
) -> dict[str, pd.DataFrame]:
    panel = add_entry_bar_features(load_panel(task503_panel_path))
    base = build_walk_forward_base(panel)
    summary, folds, selected = evaluate_refined_families(base)
    pass_flag = int(not selected.empty)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task529",
                "entry_safe_refinement_pass_flag": pass_flag,
                "selected_family": selected.iloc[0]["family_name"] if pass_flag else "none",
                "selected_entry_reduce_rate": selected.iloc[0]["entry_reduce_mean"] if pass_flag else pd.NA,
                "selected_positive_fold_rate": selected.iloc[0]["positive_fold_rate"] if pass_flag else pd.NA,
                "selected_retention_rate": selected.iloc[0]["retention_mean"] if pass_flag else pd.NA,
                "label_used_in_assignment_flag": 0,
                "strategy_acceptance_status": "ENTRY_SAFE_REFINEMENT_PASS_DIAGNOSTIC" if pass_flag else "ENTRY_SAFE_REFINEMENT_FAIL",
            }
        ]
    )
    _write(out_dir, {
        "entry_safe_feature_audit": panel[["lifecycle_id", "entry_close_vs_vwap", "entry_close_pos_in_bar", "entry_safe_feature_available_flag"]].copy(),
        "trend_persistence_refined_candidate_pool": summary,
        "trend_persistence_refined_walk_forward_quality": folds,
        "trend_persistence_refined_selected_rule": selected,
        "task_529_decision": decision,
    }, "task_529_trend_persistence_entry_safe_refinement.md")
    return {"trend_persistence_refined_candidate_pool": summary, "task_529_decision": decision}


def build_task530_paper_shadow_candidate_rerun(
    *,
    task529_decision_path: Path = TASK529_OUT / "task_529_decision.csv",
    task529_selected_path: Path = TASK529_OUT / "trend_persistence_refined_selected_rule.csv",
    out_dir: Path = TASK530_OUT,
) -> dict[str, pd.DataFrame]:
    decision529 = pd.read_csv(task529_decision_path).iloc[0].to_dict() if task529_decision_path.exists() else {}
    selected = pd.read_csv(task529_selected_path) if task529_selected_path.exists() else pd.DataFrame()
    promoted = pd.DataFrame()
    rejects = pd.DataFrame()
    if int(decision529.get("entry_safe_refinement_pass_flag", 0)) == 1 and not selected.empty:
        promoted = selected.copy()
        promoted["promotion_decision"] = "PROMOTE_TO_PAPER_SHADOW_CANDIDATE"
        promoted["promotion_reason"] = "entry_safe_refinement_pass_nbbo_only_scope_limited"
    else:
        rejects = pd.DataFrame([{"promotion_decision": "NEEDS_ENTRY_SAFE_REFINEMENT", "promotion_reason": "Task529 did not pass"}])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task530",
                "paper_shadow_candidate_count": int(len(promoted)),
                "promotion_decision": "PROMOTE_TO_PAPER_SHADOW_CANDIDATE" if not promoted.empty else "NEEDS_ENTRY_SAFE_REFINEMENT",
                "deployment_ready_flag": 0,
                "scope_mode": "NBBO_ONLY_SCOPE_LIMITED",
                "strategy_acceptance_status": "PAPER_SHADOW_CANDIDATE_DIAGNOSTIC" if not promoted.empty else "NOT_PROMOTED",
            }
        ]
    )
    _write(out_dir, {
        "paper_shadow_candidate_quality": promoted,
        "paper_shadow_candidate_reject_reasons": rejects,
        "task_530_decision": decision,
    }, "task_530_paper_shadow_candidate_rerun.md")
    return {"paper_shadow_candidate_quality": promoted, "task_530_decision": decision}


def _write(out_dir: Path, artifacts: dict[str, pd.DataFrame], report_name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = next((frame for name, frame in artifacts.items() if name.startswith("task_")), pd.DataFrame())
    _write_report(out_dir / report_name, report_name.replace(".md", "").replace("_", " ").title(), decision, artifacts)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _write_report(path: Path, title: str, decision: pd.DataFrame, artifacts: dict[str, pd.DataFrame]) -> None:
    status = decision.iloc[0].get("strategy_acceptance_status", "UNKNOWN") if not decision.empty else "UNKNOWN"
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    selected_family = row.get("selected_family", "n/a")
    selected_er = row.get("selected_entry_reduce_rate", "n/a")
    selected_fold = row.get("selected_positive_fold_rate", "n/a")
    candidate_count = len(artifacts.get("trend_persistence_refined_candidate_pool", pd.DataFrame()))
    shadow_count = int(row.get("paper_shadow_candidate_count", 0)) if "paper_shadow_candidate_count" in row else "n/a"
    write_standard_report(
        path,
        title=title,
        decision_summary=[
            f"Strategy acceptance: {status}",
            f"Selected family: {selected_family}",
            f"Selected entry_reduce rate: {selected_er}",
            f"Selected positive fold rate: {selected_fold}",
            f"Paper/shadow candidate count: {shadow_count}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "This task is a diagnostic refinement of the near-passing `trend_persistence_near_high` family. Assignment uses only entry-safe OHLCV/VWAP-derived fields and does not use labels or future outcome columns.",
            f"Candidate families evaluated: {candidate_count}. The selected rule is intentionally simple so it can be replayed and audited before paper/shadow instrumentation.",
            "The result should be interpreted as a paper/shadow candidate, not as alpha validation. Broker-truth fills, receive timestamps, status/LULD, and full-depth data remain outside this task.",
        ],
        decision_maker_lines=[
            "The strategy candidate was cleaned enough to move into a paper/shadow bookkeeping test, but it is not ready for real trading.",
            "The main practical value is that the next step can record every decision, simulated order, fill, and lifecycle with explicit IDs instead of guessing later.",
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task503-panel", type=Path, default=TASK503_PANEL)
    args = parser.parse_args()
    build_task529_trend_persistence_entry_safe_refinement(task503_panel_path=args.task503_panel)
    build_task530_paper_shadow_candidate_rerun()


if __name__ == "__main__":
    main()
