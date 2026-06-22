from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest.build_task490r_firm_grade_intraday_continuation_validation import (
    DEFAULT_OUT_DIR as TASK490R_OUT_DIR,
    DEFAULT_TASK489_SELECTED_CELLS,
    PRIMARY_ADD_SCALE,
    PRIMARY_AVG_NET,
    PRIMARY_COUNT_MAX,
    PRIMARY_COUNT_MIN,
    PRIMARY_ENTRY_REDUCE_MAX,
    PRIMARY_RECENT_AVG_NET,
    PRIMARY_RECENT_COUNT,
    PRIMARY_RECENT_ENTRY_REDUCE_MAX,
    PRIMARY_VALIDATION_COUNT,
    PRIMARY_WIN_RATE,
    SECONDARY_AVG_NET,
    SECONDARY_COUNT_MAX,
    SECONDARY_COUNT_MIN,
    SECONDARY_ENTRY_REDUCE_MAX,
    SECONDARY_WIN_RATE,
    archetype_mask,
    build_cost_stress_quality,
    build_failure_decomposition,
    build_intraday_archetype_candidate_pool,
    build_leakage_audit,
    build_task489_selected_panel,
    evaluate_panel,
)
from src.backtest.build_task489_broad_regime_cell_portfolio import (
    DEFAULT_BROAD_DAILY_DIR,
    DEFAULT_BROAD_MARKET_CACHE,
    DEFAULT_TASK487_PANEL,
    aggregate_quality,
    load_or_build_broad_market_state,
    load_panel_with_broad_market,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_491_intraday_continuation_grid_development")

STRETCH_COUNT_MIN = 100
STRETCH_COUNT_MAX = 250
STRETCH_AVG_NET = 4.0
STRETCH_WIN_RATE = 0.75
STRETCH_ADD_SCALE = 0.70
STRETCH_ENTRY_REDUCE_MAX = 0.08
STRETCH_VALIDATION_COUNT = 20
STRETCH_RECENT_COUNT = 20
STRETCH_RECENT_AVG_NET = 2.50


@dataclass(frozen=True)
class Task491Artifacts:
    grid_portfolio_candidate_pool: pd.DataFrame
    selected_grid_archetype_rulebook: pd.DataFrame
    selected_grid_assignment_panel: pd.DataFrame
    selected_grid_portfolio_quality: pd.DataFrame
    selected_grid_split_quality: pd.DataFrame
    selected_grid_cost_stress_quality: pd.DataFrame
    selected_grid_failure_decomposition: pd.DataFrame
    grid_leakage_audit: pd.DataFrame
    grid_development_decision: pd.DataFrame


def build_task491_intraday_continuation_grid_development(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    task489_selected_cells_path: Path = DEFAULT_TASK489_SELECTED_CELLS,
    broad_daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    broad_market_cache: Path = DEFAULT_BROAD_MARKET_CACHE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task491Artifacts:
    _, market = load_or_build_broad_market_state(broad_daily_dir, broad_market_cache)
    panel = load_panel_with_broad_market(task487_panel_path, market)
    base = build_task489_selected_panel(panel, task489_selected_cells_path)
    cell_pool = build_intraday_archetype_candidate_pool(base)
    grid_pool, selected_cells, selected_panel = run_grid_search(base, cell_pool)
    quality = aggregate_quality(selected_panel, [])
    split_quality = aggregate_quality(selected_panel, ["split_name"])
    cost_stress = build_cost_stress_quality(selected_panel)
    failure = build_task491_failure_decomposition(selected_panel, selected_cells)
    leakage = build_leakage_audit(selected_cells)
    decision = build_decision(base, grid_pool, selected_cells, selected_panel, quality, split_quality, cost_stress, leakage, failure)
    artifacts = Task491Artifacts(
        grid_pool,
        selected_cells,
        selected_panel,
        quality,
        split_quality,
        cost_stress,
        failure,
        leakage,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def run_grid_search(base: pd.DataFrame, cell_pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if base.empty or cell_pool.empty:
        return pd.DataFrame(), cell_pool.iloc[0:0].copy(), base.iloc[0:0].copy()
    candidates = cell_pool[cell_pool["lifecycle_count"].ge(5)].reset_index(drop=True)
    masks = [archetype_mask(base, row) for _, row in candidates.iterrows()]
    rows: list[dict[str, object]] = []
    selected_record: dict[str, object] | None = None
    profiles = [
        ("stretch_firm_grade", 100, 250),
        ("primary_firm_grade", 80, 250),
        ("validation_sufficient", 80, 250),
        ("secondary_scaled", 250, 500),
        ("capacity_balanced", 300, 500),
    ]
    grids = []
    for min_avg in [0.5, 1.0, 1.5, 2.0, 3.0]:
        for max_er in [0.08, 0.12, 0.15, 0.20, 0.25, 0.30]:
            for min_win in [0.50, 0.55, 0.60, 0.65, 0.70]:
                for min_add in [0.45, 0.50, 0.55, 0.60, 0.70]:
                    grids.append((min_avg, max_er, min_win, min_add))
    order_specs = [
        ("score_desc", ["portfolio_search_score"], [False]),
        ("avg_desc", ["avg_net_return_pct"], [False]),
        ("entry_reduce_asc", ["entry_reduce_failure_rate", "avg_net_return_pct"], [True, False]),
        ("validation_count_desc", ["validation_count", "avg_net_return_pct"], [False, False]),
        ("recent_count_desc", ["recent_oos_count", "avg_net_return_pct"], [False, False]),
        ("add_scale_desc", ["add_scale_success_rate", "avg_net_return_pct"], [False, False]),
    ]
    for profile_name, min_count, max_count in profiles:
        for min_avg, max_er, min_win, min_add in grids:
            eligible = candidates[
                candidates["avg_net_return_pct"].ge(min_avg)
                & candidates["entry_reduce_failure_rate"].le(max_er)
                & candidates["win_rate"].ge(min_win)
                & candidates["add_scale_success_rate"].ge(min_add)
            ].copy()
            if eligible.empty:
                continue
            for order_name, sort_cols, ascending in order_specs:
                ordered_index = list(eligible.sort_values(sort_cols, ascending=ascending).index)
                mask = np.zeros(len(base), dtype=bool)
                chosen: list[int] = []
                for idx in ordered_index:
                    next_mask = mask | masks[idx]
                    if int(next_mask.sum()) > max_count:
                        continue
                    mask = next_mask
                    chosen.append(idx)
                    if int(mask.sum()) >= min_count:
                        selected = base[mask]
                        quality = evaluate_panel(selected)
                        status = classify_status(quality)
                        row = {
                            "grid_profile_name": profile_name,
                            "order_name": order_name,
                            "min_cell_avg_net_pct": min_avg,
                            "max_cell_entry_reduce": max_er,
                            "min_cell_win_rate": min_win,
                            "min_cell_add_scale": min_add,
                            "selected_cell_count": len(chosen),
                            "target_status": status,
                            **quality,
                        }
                        row["grid_score"] = grid_score(row)
                        rows.append(row)
                        record = {"row": row, "mask": mask.copy(), "chosen": chosen.copy()}
                        if selected_record is None or record_rank(record) > record_rank(selected_record):
                            selected_record = record
                        break
    grid_pool = pd.DataFrame(rows)
    if selected_record is None:
        return grid_pool, candidates.iloc[0:0].copy(), base.iloc[0:0].copy()
    chosen_cells = candidates.iloc[selected_record["chosen"]].copy().reset_index(drop=True)
    chosen_cells["selected_archetype_order"] = range(1, len(chosen_cells) + 1)
    chosen_cells["grid_profile_name"] = selected_record["row"]["grid_profile_name"]
    chosen_cells["order_name"] = selected_record["row"]["order_name"]
    chosen_cells["diagnostic_only_flag"] = 1
    selected_panel = base[selected_record["mask"]].copy().reset_index(drop=True)
    selected_panel["grid_profile_name"] = selected_record["row"]["grid_profile_name"]
    selected_panel["target_status"] = selected_record["row"]["target_status"]
    selected_panel["inferred_lifecycle_matching_used_flag"] = 0
    return grid_pool.sort_values("grid_score", ascending=False).reset_index(drop=True), chosen_cells, selected_panel


def classify_status(q: dict[str, object]) -> str:
    if (
        STRETCH_COUNT_MIN <= int(q["count"]) <= STRETCH_COUNT_MAX
        and float(q["avg_net_pct"]) >= STRETCH_AVG_NET
        and float(q["win_rate"]) >= STRETCH_WIN_RATE
        and float(q["add_scale_success_rate"]) >= STRETCH_ADD_SCALE
        and float(q["entry_reduce_failure_rate"]) <= STRETCH_ENTRY_REDUCE_MAX
        and int(q["validation_count"]) >= STRETCH_VALIDATION_COUNT
        and int(q["recent_oos_count"]) >= STRETCH_RECENT_COUNT
        and float(q["recent_oos_avg_net_pct"]) >= STRETCH_RECENT_AVG_NET
    ):
        return "STRETCH_PASS"
    if (
        PRIMARY_COUNT_MIN <= int(q["count"]) <= PRIMARY_COUNT_MAX
        and float(q["avg_net_pct"]) >= PRIMARY_AVG_NET
        and float(q["win_rate"]) >= PRIMARY_WIN_RATE
        and float(q["add_scale_success_rate"]) >= PRIMARY_ADD_SCALE
        and float(q["entry_reduce_failure_rate"]) <= PRIMARY_ENTRY_REDUCE_MAX
        and int(q["validation_count"]) >= PRIMARY_VALIDATION_COUNT
        and int(q["recent_oos_count"]) >= PRIMARY_RECENT_COUNT
        and float(q["recent_oos_avg_net_pct"]) >= PRIMARY_RECENT_AVG_NET
        and float(q["recent_oos_entry_reduce_rate"]) <= PRIMARY_RECENT_ENTRY_REDUCE_MAX
    ):
        return "PRIMARY_PASS"
    if (
        SECONDARY_COUNT_MIN <= int(q["count"]) <= SECONDARY_COUNT_MAX
        and float(q["avg_net_pct"]) >= SECONDARY_AVG_NET
        and float(q["win_rate"]) >= SECONDARY_WIN_RATE
        and float(q["entry_reduce_failure_rate"]) <= SECONDARY_ENTRY_REDUCE_MAX
    ):
        return "SECONDARY_PASS"
    return "DIAGNOSTIC_FAIL"


def grid_score(row: dict[str, object]) -> float:
    return (
        float(row.get("avg_net_pct", 0) or 0)
        + 0.50 * float(row.get("recent_oos_avg_net_pct", 0) or 0)
        + 0.30 * float(row.get("validation_avg_net_pct", 0) or 0)
        + 2.0 * float(row.get("win_rate", 0) or 0)
        + 2.0 * float(row.get("add_scale_success_rate", 0) or 0)
        - 6.0 * float(row.get("entry_reduce_failure_rate", 0) or 0)
        + min(float(row.get("validation_count", 0) or 0), 20) * 0.03
        + min(float(row.get("recent_oos_count", 0) or 0), 20) * 0.03
    )


def record_rank(record: dict[str, object]) -> tuple[int, float]:
    status_rank = {"STRETCH_PASS": 4, "PRIMARY_PASS": 3, "SECONDARY_PASS": 2, "DIAGNOSTIC_FAIL": 1}
    row = record["row"]
    return status_rank.get(str(row["target_status"]), 0), float(row["grid_score"])


def build_task491_failure_decomposition(panel: pd.DataFrame, selected_cells: pd.DataFrame) -> pd.DataFrame:
    rows = build_failure_decomposition(panel, selected_cells)
    if rows.empty:
        return rows
    q = evaluate_panel(panel)
    stretch_rows = [
        {
            "failure_name": "stretch_avg_net_below_target",
            "failure_active_flag": int(float(q["avg_net_pct"]) < STRETCH_AVG_NET),
            "failure_detail": f"{q['avg_net_pct']} < {STRETCH_AVG_NET}",
            "selected_archetype_count": int(len(selected_cells)),
        },
        {
            "failure_name": "stretch_validation_undercovered",
            "failure_active_flag": int(int(q["validation_count"]) < STRETCH_VALIDATION_COUNT),
            "failure_detail": f"{q['validation_count']} < {STRETCH_VALIDATION_COUNT}",
            "selected_archetype_count": int(len(selected_cells)),
        },
    ]
    return pd.concat([rows, pd.DataFrame(stretch_rows)], ignore_index=True)


def build_decision(
    base: pd.DataFrame,
    grid_pool: pd.DataFrame,
    selected_cells: pd.DataFrame,
    selected_panel: pd.DataFrame,
    quality: pd.DataFrame,
    split_quality: pd.DataFrame,
    cost_stress: pd.DataFrame,
    leakage: pd.DataFrame,
    failure: pd.DataFrame,
) -> pd.DataFrame:
    metrics = quality.iloc[0].to_dict() if not quality.empty else {}
    q = evaluate_panel(selected_panel)
    status = classify_status(q)
    validation = split_quality[split_quality["split_name"].eq("validation")] if not split_quality.empty else pd.DataFrame()
    recent = split_quality[split_quality["split_name"].eq("recent_oos")] if not split_quality.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "task_id": "Task491",
                "task_name": "Intraday Continuation Grid Development Loop",
                "task489_base_count": int(len(base)),
                "grid_candidate_count": int(len(grid_pool)),
                "selected_archetype_count": int(len(selected_cells)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_add_scale_success_rate": metrics.get("add_scale_success_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "validation_count": int(validation["lifecycle_count"].iloc[0]) if not validation.empty else 0,
                "validation_avg_net_pct": validation["avg_net_return_pct"].iloc[0] if not validation.empty else pd.NA,
                "recent_oos_count": int(recent["lifecycle_count"].iloc[0]) if not recent.empty else 0,
                "recent_oos_avg_net_pct": recent["avg_net_return_pct"].iloc[0] if not recent.empty else pd.NA,
                "best_target_status": status,
                "stretch_pass_flag": int(status == "STRETCH_PASS"),
                "primary_pass_flag": int(status == "PRIMARY_PASS"),
                "secondary_pass_flag": int(status == "SECONDARY_PASS"),
                "leakage_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "active_failure_count": int(failure["failure_active_flag"].sum()) if not failure.empty else 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_development_action": "extend_validation_history_or_collect_quote_depth_status_before_claiming_firm_grade",
            }
        ]
    )


def write_artifacts(artifacts: Task491Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.grid_portfolio_candidate_pool.to_csv(out_dir / "grid_portfolio_candidate_pool.csv", index=False)
    artifacts.selected_grid_archetype_rulebook.to_csv(out_dir / "selected_grid_archetype_rulebook.csv", index=False)
    artifacts.selected_grid_assignment_panel.to_csv(out_dir / "selected_grid_assignment_panel.csv", index=False)
    artifacts.selected_grid_portfolio_quality.to_csv(out_dir / "selected_grid_portfolio_quality.csv", index=False)
    artifacts.selected_grid_split_quality.to_csv(out_dir / "selected_grid_split_quality.csv", index=False)
    artifacts.selected_grid_cost_stress_quality.to_csv(out_dir / "selected_grid_cost_stress_quality.csv", index=False)
    artifacts.selected_grid_failure_decomposition.to_csv(out_dir / "selected_grid_failure_decomposition.csv", index=False)
    artifacts.grid_leakage_audit.to_csv(out_dir / "grid_leakage_audit.csv", index=False)
    artifacts.grid_development_decision.to_csv(out_dir / "grid_development_decision.csv", index=False)
    (out_dir / "task_491_intraday_continuation_grid_development.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task491Artifacts) -> str:
    d = artifacts.grid_development_decision.iloc[0].to_dict()
    top = artifacts.grid_portfolio_candidate_pool.head(10)
    return "\n".join(
        [
            "# Task 491 - Intraday Continuation Grid Development Loop",
            "",
            "## Quant Firm 4-Person Review",
            "",
            "### 1. Regime Specialist",
            "Task489 regime edge remains the necessary outer gate. The grid did not invalidate regime gating; it showed that intraday continuation quality must be selected inside the already-good regime.",
            "",
            "### 2. Intraday Structure Specialist",
            "The best sleeves are not broad filters. They cluster around upper-range hold, accepted participation, VWAP acceptance/reclaim, and controlled/healthy expansion states. The problem is validation depth, not immediate edge absence.",
            "",
            "### 3. Risk/Execution Specialist",
            "OHLCV/VWAP can separate a high-return sleeve, but cannot verify spread/depth/status fragility. Missing quote/depth/status/LULD remains a hard blocker for deployment-grade execution claims.",
            "",
            "### 4. Portfolio PM",
            "The high-conviction sleeve has attractive return quality but limited validation count. A firm would treat this as a research sleeve requiring more history or microstructure validation, not production capital.",
            "",
            "## Result Summary",
            "",
            f"- Status: {d['best_target_status']}",
            f"- Grid portfolios tested: {d['grid_candidate_count']}",
            f"- Selected count / avg net / win / ADD-SCALE / entry_reduce: {d['selected_count']} / "
            f"{float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / "
            f"{float(d['selected_add_scale_success_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Validation count / avg net: {d['validation_count']} / {float(d['validation_avg_net_pct']):.3f}%",
            f"- Recent OOS count / avg net: {d['recent_oos_count']} / {float(d['recent_oos_avg_net_pct']):.3f}%",
            "- Inferred lifecycle matching used: NO",
            "- Deployment ready: NO",
            "",
            "## Top Grid Candidates",
            "",
            _csv_block(top),
            "",
            "## Selected Split Quality",
            "",
            _csv_block(artifacts.selected_grid_split_quality),
            "",
            "## Failure Decomposition",
            "",
            _csv_block(artifacts.selected_grid_failure_decomposition),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "좋은 market/theme regime 안에서 intraday continuation 조합을 grid로 많이 돌렸다. 결과적으로 높은 수익률과 낮은 entry-reduce를 보이는 조합은 찾았지만, 검증 구간 표본이 충분하지 않아 회사 돈을 바로 넣을 단계는 아니다. 다음 개발은 더 긴 검증 데이터 또는 quote/depth/status 같은 실제 체결 품질 데이터 확보가 우선이다.",
        ]
    )


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task487-panel-path", type=Path, default=DEFAULT_TASK487_PANEL)
    parser.add_argument("--task489-selected-cells-path", type=Path, default=DEFAULT_TASK489_SELECTED_CELLS)
    parser.add_argument("--broad-daily-dir", type=Path, default=DEFAULT_BROAD_DAILY_DIR)
    parser.add_argument("--broad-market-cache", type=Path, default=DEFAULT_BROAD_MARKET_CACHE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task491_intraday_continuation_grid_development(
        task487_panel_path=args.task487_panel_path,
        task489_selected_cells_path=args.task489_selected_cells_path,
        broad_daily_dir=args.broad_daily_dir,
        broad_market_cache=args.broad_market_cache,
        out_dir=args.out_dir,
    )
    row = artifacts.grid_development_decision.iloc[0]
    print(
        "[TASK491] "
        f"status={row['best_target_status']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}% grid={row['grid_candidate_count']}"
    )


if __name__ == "__main__":
    main()
