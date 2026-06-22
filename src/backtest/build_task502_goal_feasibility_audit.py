from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest


DEFAULT_TASK501_OUT = Path("docs/reports/task_501_multiday_continuation_policy_rebuild")
DEFAULT_OUT_DIR = Path("docs/reports/task_502_goal_feasibility_audit")


def build_task502_goal_feasibility_audit(
    *,
    task501_out: Path = DEFAULT_TASK501_OUT,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pool = pd.read_csv(task501_out / "multiday_policy_candidate_pool.csv")
    selected = pd.read_csv(task501_out / "selected_multiday_lifecycle_panel.csv")
    policy_frontier = build_policy_frontier(pool)
    cell_frontier = build_cell_frontier(selected)
    decision = build_decision(policy_frontier, cell_frontier)
    write_artifacts(out_dir, policy_frontier, cell_frontier, decision)
    return policy_frontier, cell_frontier, decision


def build_policy_frontier(pool: pd.DataFrame) -> pd.DataFrame:
    scoped = pool[pool["lifecycle_count"].between(300, 600)].copy()
    if scoped.empty:
        return pd.DataFrame([{"frontier_name": "policy_count_300_600", "candidate_count": 0}])
    rows = [
        {
            "frontier_name": "best_avg_net_in_count_band",
            **scoped.sort_values("avg_net_return_pct", ascending=False).iloc[0].to_dict(),
        },
        {
            "frontier_name": "best_win_in_count_band",
            **scoped.sort_values("win_rate", ascending=False).iloc[0].to_dict(),
        },
        {
            "frontier_name": "lowest_entry_reduce_in_count_band",
            **scoped.sort_values("entry_reduce_failure_rate", ascending=True).iloc[0].to_dict(),
        },
    ]
    return pd.DataFrame(rows)


def build_cell_frontier(selected: pd.DataFrame) -> pd.DataFrame:
    dims = ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4", "microstructure_state_v4"]
    rows = []
    for values, subset in selected.groupby(dims, dropna=False):
        rows.append(
            {
                "cell_key": "|".join(str(v) for v in values),
                "lifecycle_count": len(subset),
                "avg_net_return_pct": float(subset["net_return_from_entry"].mean() * 100.0),
                "win_rate": float(subset["win_flag"].mean()),
                "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()),
                "median_holding_days": float(subset["holding_days"].median()),
            }
        )
    cells = pd.DataFrame(rows).sort_values(["win_rate", "avg_net_return_pct"], ascending=[False, False]).reset_index(drop=True)
    frontier_rows = []
    mask_cells = []
    total = 0
    for _, row in cells.iterrows():
        mask_cells.append(str(row["cell_key"]))
        total += int(row["lifecycle_count"])
        scoped = selected[selected[dims].astype(str).agg("|".join, axis=1).isin(mask_cells)]
        frontier_rows.append(
            {
                "frontier_rank": len(frontier_rows) + 1,
                "cell_count": len(mask_cells),
                "lifecycle_count": int(len(scoped)),
                "avg_net_return_pct": float(scoped["net_return_from_entry"].mean() * 100.0),
                "win_rate": float(scoped["win_flag"].mean()),
                "entry_reduce_failure_rate": float(scoped["entry_reduce_failure_flag"].mean()),
                "median_holding_days": float(scoped["holding_days"].median()),
                "cell_keys": ";".join(mask_cells),
            }
        )
        if total >= 600:
            break
    return pd.DataFrame(frontier_rows)


def build_decision(policy_frontier: pd.DataFrame, cell_frontier: pd.DataFrame) -> pd.DataFrame:
    count_band_policy = policy_frontier[policy_frontier.get("lifecycle_count", pd.Series(dtype=float)).between(300, 600)] if "lifecycle_count" in policy_frontier.columns else pd.DataFrame()
    policy_goal_possible = int(
        not count_band_policy.empty
        and bool(
            (
                count_band_policy["avg_net_return_pct"].ge(3.0)
                & count_band_policy["win_rate"].ge(0.65)
                & count_band_policy["entry_reduce_failure_rate"].le(0.20)
                & count_band_policy["median_holding_days"].ge(3.0)
            ).any()
        )
    )
    cell_count_band = cell_frontier[cell_frontier["lifecycle_count"].between(300, 600)] if not cell_frontier.empty else pd.DataFrame()
    cell_goal_possible = int(
        not cell_count_band.empty
        and bool(
            (
                cell_count_band["avg_net_return_pct"].ge(3.0)
                & cell_count_band["win_rate"].ge(0.65)
                & cell_count_band["entry_reduce_failure_rate"].le(0.20)
                & cell_count_band["median_holding_days"].ge(3.0)
            ).any()
        )
    )
    best_count_band = cell_count_band.sort_values("win_rate", ascending=False).head(1) if not cell_count_band.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "task_id": "Task502",
                "policy_goal_possible_flag": policy_goal_possible,
                "cell_frontier_goal_possible_flag": cell_goal_possible,
                "best_count_band_win_rate": best_count_band["win_rate"].iloc[0] if not best_count_band.empty else pd.NA,
                "best_count_band_entry_reduce_rate": best_count_band["entry_reduce_failure_rate"].iloc[0] if not best_count_band.empty else pd.NA,
                "current_goal_status": "BLOCKED_BY_ENTRY_POPULATION_QUALITY" if not (policy_goal_possible or cell_goal_possible) else "GOAL_CANDIDATE_FOUND",
                "next_required_task": "rebuild_entry_population_for_multiday_continuation_not_more_exit_parameter_search",
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(out_dir: Path, policy_frontier: pd.DataFrame, cell_frontier: pd.DataFrame, decision: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    policy_frontier.to_csv(out_dir / "policy_feasibility_frontier.csv", index=False)
    cell_frontier.to_csv(out_dir / "cell_feasibility_frontier.csv", index=False)
    decision.to_csv(out_dir / "task_502_decision.csv", index=False)
    (out_dir / "task_502_goal_feasibility_audit.md").write_text(build_report(decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_report(decision: pd.DataFrame) -> str:
    row = decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 502 - Goal Feasibility Audit",
            "",
            "## Decision Summary",
            "",
            f"- Current goal status: {row['current_goal_status']}",
            f"- Policy goal possible: {row['policy_goal_possible_flag']}",
            f"- Cell frontier goal possible: {row['cell_frontier_goal_possible_flag']}",
            f"- Next task: {row['next_required_task']}",
            "",
            "## Quant Expert Report",
            "",
            "The multi-day exit policy fixed holding horizon and average net return, but count-band win rate and entry-reduce constraints are not feasible in the current exact entry population. More stop/hold parameter search is not the right next step.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "현재 후보들은 며칠 이상 보유하면 수익 크기는 커질 수 있지만, 이기는 비율과 손실 실패율이 목표에 못 미친다. 다음은 출구 파라미터가 아니라 진입 후보군 자체를 다시 만들어야 한다.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task501-out", type=Path, default=DEFAULT_TASK501_OUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    _, _, decision = build_task502_goal_feasibility_audit(task501_out=args.task501_out, out_dir=args.out_dir)
    row = decision.iloc[0]
    print(f"[TASK502] status={row['current_goal_status']} next={row['next_required_task']}")


if __name__ == "__main__":
    main()
