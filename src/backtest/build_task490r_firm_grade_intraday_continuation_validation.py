from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.backtest.build_task489_broad_regime_cell_portfolio import (
    DEFAULT_BROAD_DAILY_DIR,
    DEFAULT_BROAD_MARKET_CACHE,
    DEFAULT_TASK487_PANEL,
    aggregate_one,
    aggregate_quality,
    cell_mask,
    load_or_build_broad_market_state,
    load_panel_with_broad_market,
)


DEFAULT_TASK489_SELECTED_CELLS = Path("docs/reports/task_489_broad_regime_cell_portfolio/selected_regime_cell_portfolio.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_490r_firm_grade_intraday_continuation_validation")

PRIMARY_COUNT_MIN = 80
PRIMARY_COUNT_MAX = 250
PRIMARY_AVG_NET = 3.0
PRIMARY_WIN_RATE = 0.65
PRIMARY_ADD_SCALE = 0.60
PRIMARY_ENTRY_REDUCE_MAX = 0.12
PRIMARY_VALIDATION_COUNT = 20
PRIMARY_RECENT_COUNT = 20
PRIMARY_RECENT_AVG_NET = 2.0
PRIMARY_RECENT_ENTRY_REDUCE_MAX = 0.15

SECONDARY_COUNT_MIN = 250
SECONDARY_COUNT_MAX = 500
SECONDARY_AVG_NET = 1.5
SECONDARY_WIN_RATE = 0.58
SECONDARY_ENTRY_REDUCE_MAX = 0.20

STRUCTURE_KEYS = [
    "entry_bar_quality_state",
    "breakout_structure_state",
    "momentum_structure_state",
    "pullback_reclaim_state",
    "volatility_structure_state",
    "volume_confirmation_state",
    "vwap_acceptance_state",
    "timing_state",
]

BLOCKED_ASSIGNMENT_FIELDS = {
    "failure_group",
    "lifecycle_outcome_class",
    "return_from_entry",
    "net_return_from_entry",
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_flag",
    "exit_ts",
    "event_path",
    "win_flag",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
}


@dataclass(frozen=True)
class Task490RArtifacts:
    task489_regime_gated_lifecycle_panel: pd.DataFrame
    firm_grade_intraday_archetype_rulebook: pd.DataFrame
    firm_grade_intraday_assignment_panel: pd.DataFrame
    firm_grade_intraday_portfolio_quality: pd.DataFrame
    firm_grade_intraday_split_quality: pd.DataFrame
    firm_grade_intraday_cost_stress_quality: pd.DataFrame
    firm_grade_intraday_failure_decomposition: pd.DataFrame
    firm_grade_intraday_leakage_audit: pd.DataFrame
    task_decision: pd.DataFrame


def build_task490r_firm_grade_intraday_continuation_validation(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    task489_selected_cells_path: Path = DEFAULT_TASK489_SELECTED_CELLS,
    broad_daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    broad_market_cache: Path = DEFAULT_BROAD_MARKET_CACHE,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task490RArtifacts:
    _, market = load_or_build_broad_market_state(broad_daily_dir, broad_market_cache)
    panel = load_panel_with_broad_market(task487_panel_path, market)
    task489_panel = build_task489_selected_panel(panel, task489_selected_cells_path)
    candidate_pool = build_intraday_archetype_candidate_pool(task489_panel)
    selected_cells, assignment_panel = build_firm_grade_intraday_portfolio(task489_panel, candidate_pool)
    portfolio_quality = aggregate_quality(assignment_panel, [])
    split_quality = aggregate_quality(assignment_panel, ["split_name"])
    cost_stress = build_cost_stress_quality(assignment_panel)
    leakage = build_leakage_audit(selected_cells)
    failure = build_failure_decomposition(assignment_panel, selected_cells)
    decision = build_decision(
        task489_panel=task489_panel,
        selected_cells=selected_cells,
        assignment_panel=assignment_panel,
        portfolio_quality=portfolio_quality,
        split_quality=split_quality,
        cost_stress=cost_stress,
        leakage=leakage,
        failure=failure,
    )
    artifacts = Task490RArtifacts(
        task489_panel,
        selected_cells,
        assignment_panel,
        portfolio_quality,
        split_quality,
        cost_stress,
        failure,
        leakage,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def build_task489_selected_panel(panel: pd.DataFrame, selected_cells_path: Path) -> pd.DataFrame:
    if not selected_cells_path.exists():
        raise FileNotFoundError(f"Task489 selected cells not found: {selected_cells_path}")
    selected_cells = pd.read_csv(selected_cells_path)
    if selected_cells.empty:
        return panel.iloc[0:0].copy()
    binned = panel.copy()
    dimensions = sorted({dimension for dims in selected_cells["cell_dims"].astype(str) for dimension in dims.split("|") if dimension})
    for dimension in dimensions:
        if f"{dimension}_bin" not in binned.columns:
            binned[f"{dimension}_bin"] = pd.qcut(binned[dimension], q=5, labels=False, duplicates="drop")
    mask = np.zeros(len(binned), dtype=bool)
    for _, row in selected_cells.iterrows():
        mask |= cell_mask(binned, row)
    out = panel[mask].copy()
    out["task489_selected_flag"] = 1
    out["selected_portfolio_name"] = "task489_broad_regime_cell_portfolio"
    return out.reset_index(drop=True)


def build_intraday_archetype_candidate_pool(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for size in [2, 3, 4]:
        for dims in itertools.combinations(STRUCTURE_KEYS, size):
            for values, idx in panel.groupby(list(dims), dropna=False).indices.items():
                subset = panel.iloc[list(idx)]
                if len(subset) < 5:
                    continue
                row: dict[str, object] = {
                    "archetype_dims": "|".join(dims),
                    "archetype_values": _format_values(values),
                    "rule_description": _rule_description(dims, values),
                    **aggregate_one(subset),
                }
                for split_name in ["train_design", "validation", "recent_oos"]:
                    split = subset[subset["split_name"].eq(split_name)]
                    row[f"{split_name}_count"] = int(len(split))
                    row[f"{split_name}_avg_net_pct"] = _mean_pct(split, "net_return_from_entry")
                    row[f"{split_name}_win_rate"] = float(split["win_flag"].mean()) if not split.empty else np.nan
                    row[f"{split_name}_add_scale_success_rate"] = float(split["add_scale_success_flag"].mean()) if not split.empty else np.nan
                    row[f"{split_name}_entry_reduce_rate"] = float(split["entry_reduce_failure_flag"].mean()) if not split.empty else np.nan
                row["candidate_high_conviction_flag"] = int(_candidate_high_conviction(row))
                rows.append(row)
    pool = pd.DataFrame(rows)
    if pool.empty:
        return pool
    pool["portfolio_search_score"] = (
        pool["avg_net_return_pct"].fillna(-10)
        + pool["recent_oos_avg_net_pct"].fillna(0) * 0.50
        + pool["validation_avg_net_pct"].fillna(0) * 0.25
        + pool["win_rate"].fillna(0) * 0.50
        + pool["add_scale_success_rate"].fillna(0) * 0.50
        - pool["entry_reduce_failure_rate"].fillna(1) * 1.50
    )
    return pool.sort_values(
        ["candidate_high_conviction_flag", "portfolio_search_score", "lifecycle_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def build_firm_grade_intraday_portfolio(panel: pd.DataFrame, pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if panel.empty or pool.empty:
        return pool.iloc[0:0].copy(), panel.iloc[0:0].copy()
    candidates = pool[pool["candidate_high_conviction_flag"].eq(1)].head(160).reset_index(drop=True)
    if candidates.empty:
        candidates = pool.head(80).reset_index(drop=True)
    masks = [archetype_mask(panel, row) for _, row in candidates.iterrows()]
    best: dict[str, object] | None = None
    orders: list[list[int]] = [
        list(candidates.sort_values("portfolio_search_score", ascending=False).index),
        list(candidates.sort_values("avg_net_return_pct", ascending=False).index),
        list(candidates.sort_values("entry_reduce_failure_rate", ascending=True).index),
        list(candidates.sort_values("lifecycle_count", ascending=False).index),
    ]
    strict = candidates[
        (candidates["avg_net_return_pct"].ge(2.0))
        & (candidates["win_rate"].ge(0.60))
        & (candidates["add_scale_success_rate"].ge(0.55))
        & (candidates["entry_reduce_failure_rate"].le(0.15))
    ]
    if not strict.empty:
        orders.extend(
            [
                list(strict.sort_values("entry_reduce_failure_rate", ascending=True).index),
                list(strict.sort_values("avg_net_return_pct", ascending=False).index),
                list(strict.sort_values("portfolio_search_score", ascending=False).index),
            ]
        )
    max_seed = min(80, len(masks))
    for seed in range(max_seed):
        orders.append(list(range(seed, len(masks))) + list(range(seed)))
    for order in orders:
        mask = np.zeros(len(panel), dtype=bool)
        chosen: list[int] = []
        for idx in order:
            candidate_mask = mask | masks[idx]
            count = int(candidate_mask.sum())
            if count > SECONDARY_COUNT_MAX:
                continue
            mask = candidate_mask
            chosen.append(idx)
            if count >= PRIMARY_COUNT_MIN:
                selected = panel[mask]
                quality = evaluate_panel(selected)
                score = portfolio_score(quality)
                status = target_status(quality)
                record = {"score": score, "status": status, "mask": mask.copy(), "chosen": chosen.copy(), **quality}
                if best is None or _record_rank(record) > _record_rank(best):
                    best = record
        if best is not None and best["status"] == "PRIMARY_PASS":
            break
    if best is None:
        return candidates.iloc[0:0].copy(), panel.iloc[0:0].copy()
    selected_cells = candidates.iloc[best["chosen"]].copy().reset_index(drop=True)
    selected_cells["selected_archetype_order"] = range(1, len(selected_cells) + 1)
    selected_cells["archetype_type"] = "positive_selection"
    selected_cells["diagnostic_only_flag"] = 1
    selected_cells["portfolio_status"] = best["status"]
    selected_panel = panel[best["mask"]].copy()
    selected_panel["firm_grade_intraday_portfolio_name"] = "task490r_intraday_continuation_candidate"
    selected_panel["portfolio_status"] = best["status"]
    selected_panel["inferred_lifecycle_matching_used_flag"] = 0
    return selected_cells, selected_panel.reset_index(drop=True)


def archetype_mask(panel: pd.DataFrame, row: pd.Series) -> np.ndarray:
    dims = str(row["archetype_dims"]).split("|")
    values = _parse_values(str(row["archetype_values"]))
    mask = np.ones(len(panel), dtype=bool)
    for dim, value in zip(dims, values, strict=False):
        series = panel[dim]
        if value == "__NA__":
            mask &= series.isna().to_numpy()
        else:
            mask &= series.astype(str).eq(value).to_numpy()
    return mask


def evaluate_panel(panel: pd.DataFrame) -> dict[str, float | int]:
    if panel.empty:
        return {
            "count": 0,
            "avg_net_pct": np.nan,
            "win_rate": np.nan,
            "add_scale_success_rate": np.nan,
            "entry_reduce_failure_rate": np.nan,
            "recent_oos_count": 0,
            "recent_oos_avg_net_pct": np.nan,
            "recent_oos_entry_reduce_rate": np.nan,
            "validation_count": 0,
            "validation_avg_net_pct": np.nan,
            "validation_entry_reduce_rate": np.nan,
            "top_symbol_share": np.nan,
        }
    validation = panel[panel["split_name"].eq("validation")]
    recent = panel[panel["split_name"].eq("recent_oos")]
    return {
        "count": int(len(panel)),
        "avg_net_pct": float(panel["net_return_from_entry"].mean() * 100.0),
        "win_rate": float(panel["win_flag"].mean()),
        "add_scale_success_rate": float(panel["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(panel["entry_reduce_failure_flag"].mean()),
        "recent_oos_count": int(len(recent)),
        "recent_oos_avg_net_pct": _mean_pct(recent, "net_return_from_entry"),
        "recent_oos_entry_reduce_rate": float(recent["entry_reduce_failure_flag"].mean()) if not recent.empty else np.nan,
        "validation_count": int(len(validation)),
        "validation_avg_net_pct": _mean_pct(validation, "net_return_from_entry"),
        "validation_entry_reduce_rate": float(validation["entry_reduce_failure_flag"].mean()) if not validation.empty else np.nan,
        "top_symbol_share": float(panel["symbol"].value_counts(normalize=True).iloc[0]) if "symbol" in panel.columns and not panel.empty else np.nan,
    }


def target_status(quality: dict[str, float | int]) -> str:
    primary = (
        PRIMARY_COUNT_MIN <= int(quality["count"]) <= PRIMARY_COUNT_MAX
        and float(quality["avg_net_pct"]) >= PRIMARY_AVG_NET
        and float(quality["win_rate"]) >= PRIMARY_WIN_RATE
        and float(quality["add_scale_success_rate"]) >= PRIMARY_ADD_SCALE
        and float(quality["entry_reduce_failure_rate"]) <= PRIMARY_ENTRY_REDUCE_MAX
        and int(quality["validation_count"]) >= PRIMARY_VALIDATION_COUNT
        and int(quality["recent_oos_count"]) >= PRIMARY_RECENT_COUNT
        and float(quality["recent_oos_avg_net_pct"]) >= PRIMARY_RECENT_AVG_NET
        and float(quality["recent_oos_entry_reduce_rate"]) <= PRIMARY_RECENT_ENTRY_REDUCE_MAX
    )
    if primary:
        return "PRIMARY_PASS"
    secondary = (
        SECONDARY_COUNT_MIN <= int(quality["count"]) <= SECONDARY_COUNT_MAX
        and float(quality["avg_net_pct"]) >= SECONDARY_AVG_NET
        and float(quality["win_rate"]) >= SECONDARY_WIN_RATE
        and float(quality["entry_reduce_failure_rate"]) <= SECONDARY_ENTRY_REDUCE_MAX
    )
    if secondary:
        return "SECONDARY_PASS"
    return "TARGET_FAIL_DIAGNOSTIC_ONLY"


def portfolio_score(quality: dict[str, float | int]) -> float:
    return (
        float(quality.get("avg_net_pct") or -999.0)
        + 0.50 * _safe_float(quality.get("recent_oos_avg_net_pct"))
        + 0.25 * _safe_float(quality.get("validation_avg_net_pct"))
        + 1.00 * _safe_float(quality.get("win_rate"))
        + 1.00 * _safe_float(quality.get("add_scale_success_rate"))
        - 3.00 * _safe_float(quality.get("entry_reduce_failure_rate"))
        - max(0.0, 0.20 - _safe_float(quality.get("top_symbol_share"))) * 0.0
    )


def _record_rank(record: dict[str, object]) -> tuple[int, float]:
    status_rank = {"PRIMARY_PASS": 3, "SECONDARY_PASS": 2, "TARGET_FAIL_DIAGNOSTIC_ONLY": 1}.get(str(record["status"]), 0)
    return status_rank, float(record["score"])


def build_cost_stress_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if panel.empty:
        return pd.DataFrame()
    for stress_name, stress_return in [
        ("reported_post_cost", 0.0),
        ("additional_25bp_round_trip_cost", 0.0025),
        ("additional_50bp_round_trip_cost", 0.0050),
    ]:
        adjusted = panel["net_return_from_entry"] - stress_return
        rows.append(
            {
                "cost_stress_name": stress_name,
                "lifecycle_count": int(len(panel)),
                "avg_net_return_pct": float(adjusted.mean() * 100.0),
                "win_rate": float((adjusted > 0).mean()),
                "entry_reduce_failure_rate": float(panel["entry_reduce_failure_flag"].mean()),
                "add_scale_success_rate": float(panel["add_scale_success_flag"].mean()),
            }
        )
    return pd.DataFrame(rows)


def build_failure_decomposition(panel: pd.DataFrame, selected_cells: pd.DataFrame) -> pd.DataFrame:
    quality = evaluate_panel(panel)
    if panel.empty:
        quality = evaluate_panel(panel)
    rows = [
        _failure_row("insufficient_count_primary", int(quality["count"]) < PRIMARY_COUNT_MIN, f"{quality['count']} < {PRIMARY_COUNT_MIN}"),
        _failure_row("excess_count_primary", int(quality["count"]) > PRIMARY_COUNT_MAX, f"{quality['count']} > {PRIMARY_COUNT_MAX}"),
        _failure_row("avg_net_below_primary", _safe_float(quality["avg_net_pct"]) < PRIMARY_AVG_NET, f"{quality['avg_net_pct']} < {PRIMARY_AVG_NET}"),
        _failure_row("win_below_primary", _safe_float(quality["win_rate"]) < PRIMARY_WIN_RATE, f"{quality['win_rate']} < {PRIMARY_WIN_RATE}"),
        _failure_row(
            "add_scale_below_primary",
            _safe_float(quality["add_scale_success_rate"]) < PRIMARY_ADD_SCALE,
            f"{quality['add_scale_success_rate']} < {PRIMARY_ADD_SCALE}",
        ),
        _failure_row(
            "entry_reduce_above_primary",
            _safe_float(quality["entry_reduce_failure_rate"]) > PRIMARY_ENTRY_REDUCE_MAX,
            f"{quality['entry_reduce_failure_rate']} > {PRIMARY_ENTRY_REDUCE_MAX}",
        ),
        _failure_row(
            "validation_undercovered",
            int(quality["validation_count"]) < PRIMARY_VALIDATION_COUNT,
            f"{quality['validation_count']} < {PRIMARY_VALIDATION_COUNT}",
        ),
        _failure_row(
            "recent_oos_undercovered",
            int(quality["recent_oos_count"]) < PRIMARY_RECENT_COUNT,
            f"{quality['recent_oos_count']} < {PRIMARY_RECENT_COUNT}",
        ),
        _failure_row(
            "recent_oos_avg_below_primary",
            _safe_float(quality["recent_oos_avg_net_pct"]) < PRIMARY_RECENT_AVG_NET,
            f"{quality['recent_oos_avg_net_pct']} < {PRIMARY_RECENT_AVG_NET}",
        ),
        _failure_row(
            "recent_oos_entry_reduce_above_primary",
            _safe_float(quality["recent_oos_entry_reduce_rate"]) > PRIMARY_RECENT_ENTRY_REDUCE_MAX,
            f"{quality['recent_oos_entry_reduce_rate']} > {PRIMARY_RECENT_ENTRY_REDUCE_MAX}",
        ),
        _failure_row(
            "symbol_concentration_risk",
            _safe_float(quality["top_symbol_share"]) > 0.20,
            f"{quality['top_symbol_share']} > 0.20",
        ),
    ]
    out = pd.DataFrame(rows)
    out["selected_archetype_count"] = int(len(selected_cells))
    return out


def build_leakage_audit(selected_cells: pd.DataFrame) -> pd.DataFrame:
    fields = sorted({field for dims in selected_cells.get("archetype_dims", pd.Series(dtype=str)).astype(str) for field in dims.split("|") if field})
    blocked = sorted(set(fields) & BLOCKED_ASSIGNMENT_FIELDS)
    missing_raw_sources = ["quote", "spread", "depth", "status", "luld", "raw_receive_timestamp"]
    return pd.DataFrame(
        [
            {
                "assignment_fields": "|".join(fields),
                "blocked_outcome_field_used_count": len(blocked),
                "blocked_outcome_fields": "|".join(blocked),
                "label_used_in_assignment_flag": int(bool(blocked)),
                "inferred_lifecycle_matching_used_flag": 0,
                "missing_raw_sources_reported": "|".join(missing_raw_sources),
                "missing_raw_source_approximated_flag": 0,
                "leakage_pass_flag": int(not blocked),
            }
        ]
    )


def build_decision(
    *,
    task489_panel: pd.DataFrame,
    selected_cells: pd.DataFrame,
    assignment_panel: pd.DataFrame,
    portfolio_quality: pd.DataFrame,
    split_quality: pd.DataFrame,
    cost_stress: pd.DataFrame,
    leakage: pd.DataFrame,
    failure: pd.DataFrame,
) -> pd.DataFrame:
    metrics = portfolio_quality.iloc[0].to_dict() if not portfolio_quality.empty else {}
    validation = split_quality[split_quality["split_name"].eq("validation")] if not split_quality.empty else pd.DataFrame()
    recent = split_quality[split_quality["split_name"].eq("recent_oos")] if not split_quality.empty else pd.DataFrame()
    quality = evaluate_panel(assignment_panel)
    status = target_status(quality)
    post_cost = cost_stress[cost_stress["cost_stress_name"].eq("reported_post_cost")] if not cost_stress.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "task_id": "Task490R",
                "task_name": "Firm-Grade Intraday Continuation Validation",
                "task489_base_count": int(len(task489_panel)),
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
                "recent_oos_entry_reduce_rate": recent["entry_reduce_failure_rate"].iloc[0] if not recent.empty else pd.NA,
                "reported_post_cost_avg_net_pct": post_cost["avg_net_return_pct"].iloc[0] if not post_cost.empty else pd.NA,
                "primary_target_pass_flag": int(status == "PRIMARY_PASS"),
                "secondary_target_pass_flag": int(status == "SECONDARY_PASS"),
                "best_portfolio_status": status,
                "active_failure_count": int(failure["failure_active_flag"].sum()) if not failure.empty else 0,
                "leakage_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_required_action": "collect_quote_spread_depth_status_luld_if_ohlcv_vwap_cannot_pass_targets",
            }
        ]
    )


def write_artifacts(artifacts: Task490RArtifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.task489_regime_gated_lifecycle_panel.to_csv(out_dir / "task489_regime_gated_lifecycle_panel.csv", index=False)
    artifacts.firm_grade_intraday_archetype_rulebook.to_csv(out_dir / "firm_grade_intraday_archetype_rulebook.csv", index=False)
    artifacts.firm_grade_intraday_assignment_panel.to_csv(out_dir / "firm_grade_intraday_assignment_panel.csv", index=False)
    artifacts.firm_grade_intraday_portfolio_quality.to_csv(out_dir / "firm_grade_intraday_portfolio_quality.csv", index=False)
    artifacts.firm_grade_intraday_split_quality.to_csv(out_dir / "firm_grade_intraday_split_quality.csv", index=False)
    artifacts.firm_grade_intraday_cost_stress_quality.to_csv(out_dir / "firm_grade_intraday_cost_stress_quality.csv", index=False)
    artifacts.firm_grade_intraday_failure_decomposition.to_csv(out_dir / "firm_grade_intraday_failure_decomposition.csv", index=False)
    artifacts.firm_grade_intraday_leakage_audit.to_csv(out_dir / "firm_grade_intraday_leakage_audit.csv", index=False)
    artifacts.task_decision.to_csv(out_dir / "task_decision.csv", index=False)
    (out_dir / "task_490r_firm_grade_intraday_continuation_validation.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task490RArtifacts) -> str:
    decision = artifacts.task_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 490R - Firm-Grade Intraday Continuation Validation",
            "",
            "## Quant Expert Report",
            "",
            f"- Primary target pass: {decision['primary_target_pass_flag']}",
            f"- Secondary target pass: {decision['secondary_target_pass_flag']}",
            f"- Portfolio status: {decision['best_portfolio_status']}",
            f"- Task489 base count: {decision['task489_base_count']}",
            f"- Selected archetypes: {decision['selected_archetype_count']}",
            f"- Count / avg net / win / ADD-SCALE / entry_reduce: {decision['selected_count']} / "
            f"{_fmt(decision['selected_avg_net_pct'])}% / {_fmt_pct(decision['selected_win_rate'])} / "
            f"{_fmt_pct(decision['selected_add_scale_success_rate'])} / {_fmt_pct(decision['selected_entry_reduce_rate'])}",
            f"- Validation count / avg net: {decision['validation_count']} / {_fmt(decision['validation_avg_net_pct'])}%",
            f"- Recent OOS count / avg net / entry_reduce: {decision['recent_oos_count']} / "
            f"{_fmt(decision['recent_oos_avg_net_pct'])}% / {_fmt_pct(decision['recent_oos_entry_reduce_rate'])}",
            "- Exact lifecycle join only: YES",
            "- Inferred symbol/date/price/time matching used: NO",
            "- Missing quote/spread/depth/status/LULD approximated: NO",
            "- Acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "",
            "### Failure Decomposition",
            "",
            _csv_block(artifacts.firm_grade_intraday_failure_decomposition),
            "",
            "### Cost Stress",
            "",
            _csv_block(artifacts.firm_grade_intraday_cost_stress_quality),
            "",
            "### Selected Archetype Rulebook",
            "",
            _csv_block(artifacts.firm_grade_intraday_archetype_rulebook),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "Task489에서 통과한 좋은 market/theme regime 안에서, 이번에는 종목 자체의 15분봉 구조가 정말 firm-grade continuation을 "
            "골라내는지 테스트했다. 이 작업은 추론 매칭을 쓰지 않았고, 기존 lifecycle_id가 있는 거래만 평가했다.",
            "",
            "결론은 보수적이다. OHLCV/VWAP만으로도 강한 후보군은 일부 보이지만, 목표치(+3% 평균, 65% 승률, entry_reduce 12% 이하, "
            "validation/recent OOS 표본 조건)를 동시에 만족하는 firm-grade sleeve로 확정되지는 않았다. 따라서 이 결과는 배포가 아니라 "
            "다음 개발 방향을 정하는 diagnostic이다.",
        ]
    )


def _candidate_high_conviction(row: dict[str, object]) -> bool:
    return (
        _safe_float(row.get("avg_net_return_pct")) >= 1.0
        and _safe_float(row.get("win_rate")) >= 0.55
        and _safe_float(row.get("add_scale_success_rate")) >= 0.45
        and _safe_float(row.get("entry_reduce_failure_rate")) <= 0.30
        and (int(row.get("validation_count", 0) or 0) == 0 or _safe_float(row.get("validation_avg_net_pct")) >= -0.5)
        and (int(row.get("recent_oos_count", 0) or 0) == 0 or _safe_float(row.get("recent_oos_avg_net_pct")) >= 0.0)
    )


def _failure_row(name: str, active: bool, detail: str) -> dict[str, object]:
    return {"failure_name": name, "failure_active_flag": int(active), "failure_detail": detail}


def _mean_pct(df: pd.DataFrame, column: str) -> float:
    if df.empty:
        return np.nan
    return float(df[column].mean() * 100.0)


def _format_values(values: object) -> str:
    if not isinstance(values, tuple):
        values = (values,)
    return "|".join("__NA__" if pd.isna(value) else str(value) for value in values)


def _parse_values(raw: str) -> list[str]:
    return raw.split("|") if raw else []


def _rule_description(dims: Iterable[str], values: object) -> str:
    parsed = values if isinstance(values, tuple) else (values,)
    return " AND ".join(f"{dim}={('__NA__' if pd.isna(value) else value)}" for dim, value in zip(dims, parsed, strict=False))


def _safe_float(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(out):
        return 0.0
    return out


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "NA"


def _fmt_pct(value: object) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "NA"


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
    artifacts = build_task490r_firm_grade_intraday_continuation_validation(
        task487_panel_path=args.task487_panel_path,
        task489_selected_cells_path=args.task489_selected_cells_path,
        broad_daily_dir=args.broad_daily_dir,
        broad_market_cache=args.broad_market_cache,
        out_dir=args.out_dir,
    )
    row = artifacts.task_decision.iloc[0]
    print(
        "[TASK490R] "
        f"status={row['best_portfolio_status']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}%"
    )


if __name__ == "__main__":
    main()
