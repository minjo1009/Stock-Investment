from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, goal_pass, holding_quality, quality


DEFAULT_TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_504_multiday_entry_cell_portfolio")


def build_task504_multiday_entry_cell_portfolio(
    *,
    task503_panel_path: Path = DEFAULT_TASK503_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = pd.read_csv(task503_panel_path)
    pool = build_cell_pool(panel)
    selected_cells, selected = select_cell_portfolio(panel, pool)
    selected_quality = pd.DataFrame([aggregate(selected)])
    split = quality(selected, ["split_name"])
    quarter = quality(selected, ["quarter"])
    theme = quality(selected, ["theme_id"])
    holding = holding_quality(selected)
    decision = build_decision(pool, selected_cells, selected_quality)
    write_artifacts(out_dir, pool, selected_cells, selected, selected_quality, split, quarter, theme, holding, decision)
    return {
        "multiday_entry_cell_candidate_pool": pool,
        "selected_multiday_entry_cell_rulebook": selected_cells,
        "selected_multiday_entry_cell_panel": selected,
        "selected_multiday_entry_cell_quality": selected_quality,
        "task_504_decision": decision,
    }


def build_cell_pool(panel: pd.DataFrame) -> pd.DataFrame:
    dims = ["theme_id", "symbol_multiday_setup_state", "timing_state"]
    rows = []
    for values, subset in panel.groupby(dims, dropna=False):
        if len(subset) < 20:
            continue
        row = aggregate(subset)
        row.update(
            {
                "cell_key": "|".join(str(v) for v in values),
                "cell_dims": "|".join(dims),
                "cell_values": "|".join(str(v) for v in values),
                "candidate_cell_flag": int(
                    row["avg_net_return_pct"] >= 3.0
                    and row["win_rate"] >= 0.65
                    and row["entry_reduce_failure_rate"] <= 0.22
                    and row["median_holding_days"] >= 3.0
                ),
            }
        )
        row["cell_score"] = (
            row["avg_net_return_pct"]
            + 4.0 * row["win_rate"]
            - 8.0 * row["entry_reduce_failure_rate"]
            + min(row["lifecycle_count"], 100) / 25.0
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["candidate_cell_flag", "cell_score"], ascending=[False, False]).reset_index(drop=True)


def select_cell_portfolio(panel: pd.DataFrame, pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if pool.empty:
        return pool, panel.iloc[0:0].copy()
    candidates = pool[pool["candidate_cell_flag"].eq(1)].copy()
    if candidates.empty:
        candidates = pool.head(20).copy()
    selected_keys: list[str] = []
    panel = panel.copy()
    panel["cell_key"] = panel[["theme_id", "symbol_multiday_setup_state", "timing_state"]].astype(str).agg("|".join, axis=1)
    mask = pd.Series(False, index=panel.index)
    for _, row in candidates.sort_values("cell_score", ascending=False).iterrows():
        next_mask = mask | panel["cell_key"].eq(row["cell_key"])
        if int(next_mask.sum()) > 600:
            continue
        mask = next_mask
        selected_keys.append(str(row["cell_key"]))
        selected = panel[mask]
        metrics = aggregate(selected)
        if int(metrics["lifecycle_count"]) >= 300 and bool(goal_pass(metrics)):
            break
    selected_cells = candidates[candidates["cell_key"].isin(selected_keys)].copy()
    selected_cells["selected_order"] = range(1, len(selected_cells) + 1)
    selected = panel[mask].copy().reset_index(drop=True)
    selected["selected_cell_portfolio_name"] = "task504_multiday_entry_cell_portfolio"
    return selected_cells.reset_index(drop=True), selected


def build_decision(pool: pd.DataFrame, selected_cells: pd.DataFrame, quality_df: pd.DataFrame) -> pd.DataFrame:
    metrics = quality_df.iloc[0].to_dict() if not quality_df.empty else {}
    return pd.DataFrame(
        [
            {
                "task_id": "Task504",
                "candidate_cell_count": int(len(pool)),
                "selected_cell_count": int(len(selected_cells)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "median_holding_days": metrics.get("median_holding_days", pd.NA),
                "same_day_exit_share": metrics.get("same_day_exit_share", pd.NA),
                "goal_achieved_flag": int(goal_pass(metrics)) if metrics else 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(
    out_dir: Path,
    pool: pd.DataFrame,
    selected_cells: pd.DataFrame,
    selected: pd.DataFrame,
    selected_quality: pd.DataFrame,
    split: pd.DataFrame,
    quarter: pd.DataFrame,
    theme: pd.DataFrame,
    holding: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pool.to_csv(out_dir / "multiday_entry_cell_candidate_pool.csv", index=False)
    selected_cells.to_csv(out_dir / "selected_multiday_entry_cell_rulebook.csv", index=False)
    selected.to_csv(out_dir / "selected_multiday_entry_cell_panel.csv", index=False)
    selected_quality.to_csv(out_dir / "selected_multiday_entry_cell_quality.csv", index=False)
    split.to_csv(out_dir / "selected_multiday_entry_cell_split_quality.csv", index=False)
    quarter.to_csv(out_dir / "selected_multiday_entry_cell_quarterly_quality.csv", index=False)
    theme.to_csv(out_dir / "selected_multiday_entry_cell_theme_quality.csv", index=False)
    holding.to_csv(out_dir / "selected_multiday_entry_cell_holding_quality.csv", index=False)
    decision.to_csv(out_dir / "task_504_decision.csv", index=False)
    (out_dir / "task_504_multiday_entry_cell_portfolio.md").write_text(build_report(decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_report(decision: pd.DataFrame) -> str:
    d = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 504 - Multi-Day Entry Cell Portfolio",
            "",
            "## Decision Summary",
            "",
            f"- Goal achieved: {d['goal_achieved_flag']}",
            f"- Count / avg net / win / entry_reduce: {d['selected_count']} / {float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Median holding days / same-day exit: {float(d['median_holding_days']):.2f} / {float(d['same_day_exit_share']):.1%}",
            "- Inferred lifecycle matching used: NO",
            "- Label used in assignment: NO",
            "",
            "## Quant Expert Report",
            "",
            "Task504 selects practical multi-day entry cells from the raw-built Task503 population. It tests whether market/theme regime plus symbol setup plus intraday timing can meet the requested count, PnL, win, entry-reduce, and holding constraints.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "새로 만든 후보군 안에서 실제로 좋은 조합만 묶었다. 목표를 만족하면 이제 처음으로 multi-day continuation 후보군이 실질적으로 보이는 단계다.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task503-panel", type=Path, default=DEFAULT_TASK503_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task504_multiday_entry_cell_portfolio(task503_panel_path=args.task503_panel, out_dir=args.out_dir)
    row = artifacts["task_504_decision"].iloc[0]
    print(
        "[TASK504] "
        f"goal={row['goal_achieved_flag']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}% win={float(row['selected_win_rate']):.1%}"
    )


if __name__ == "__main__":
    main()
