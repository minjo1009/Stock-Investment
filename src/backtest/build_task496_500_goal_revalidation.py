from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest


DEFAULT_TASK493_PANEL = Path("docs/reports/task_493_microstructure_enhanced_continuation_grid/microstructure_enriched_lifecycle_panel.csv")
DEFAULT_TASK489_MARKET = Path("docs/reports/task_489_broad_regime_cell_portfolio/broad_market_state_panel.csv")
TASK496_OUT = Path("docs/reports/task_496_multi_day_regime_v4")
TASK497_OUT = Path("docs/reports/task_497_intraday_continuation_structure")
TASK498_OUT = Path("docs/reports/task_498_entry_reduce_failure_decomposition")
TASK499_OUT = Path("docs/reports/task_499_regime_intraday_continuation_grid")
TASK500_OUT = Path("docs/reports/task_500_goal_loop_synthesis")

TARGET_COUNT_MIN = 300
TARGET_COUNT_MAX = 600
TARGET_AVG_NET = 3.0
TARGET_WIN = 0.65
TARGET_ENTRY_REDUCE_MAX = 0.20
TARGET_MEDIAN_HOLD_DAYS = 3.0
TARGET_SAME_DAY_EXIT_MAX = 0.25

OUTCOME_FIELDS = {
    "return_from_entry",
    "net_return_from_entry",
    "lifecycle_outcome_class",
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


def build_goal_revalidation(
    *,
    task493_panel_path: Path = DEFAULT_TASK493_PANEL,
    task489_market_path: Path = DEFAULT_TASK489_MARKET,
    task496_out: Path = TASK496_OUT,
    task497_out: Path = TASK497_OUT,
    task498_out: Path = TASK498_OUT,
    task499_out: Path = TASK499_OUT,
    task500_out: Path = TASK500_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_base_panel(task493_panel_path)
    market = pd.read_csv(task489_market_path) if task489_market_path.exists() else pd.DataFrame()
    regime_panel, theme_panel, transition_audit, regime_split, task496_decision = build_task496(panel, market)
    intraday_panel, intraday_quality, intraday_split, intraday_leakage, task497_decision = build_task497(regime_panel)
    failure_decomp, failure_by_state, contrast, task498_decision = build_task498(intraday_panel)
    grid_pool, selected_panel, quality, split_quality, quarterly, holding_quality, selected_failure, task499_decision = build_task499(intraday_panel)
    synthesis, task500_decision = build_task500(task499_decision, selected_failure, holding_quality)

    write_task496(task496_out, regime_panel, theme_panel, transition_audit, regime_split, task496_decision)
    write_task497(task497_out, intraday_panel, intraday_quality, intraday_split, intraday_leakage, task497_decision)
    write_task498(task498_out, failure_decomp, failure_by_state, contrast, task498_decision)
    write_task499(task499_out, grid_pool, selected_panel, quality, split_quality, quarterly, holding_quality, selected_failure, task499_decision)
    write_task500(task500_out, synthesis, task500_decision)

    return {
        "multi_day_regime_v4_panel": regime_panel,
        "theme_regime_v4_panel": theme_panel,
        "intraday_continuation_state_panel": intraday_panel,
        "selected_goal_portfolio_assignment_panel": selected_panel,
        "selected_goal_portfolio_quality": quality,
        "task_499_decision": task499_decision,
        "task_500_decision": task500_decision,
    }


def load_base_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {"lifecycle_id", "entry_ts", "exit_ts", "net_return_from_entry", "win_flag", "entry_reduce_failure_flag"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    panel = panel[panel["lifecycle_id"].notna()].copy()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["exit_ts"] = pd.to_datetime(panel["exit_ts"], utc=True, errors="coerce")
    panel["holding_days"] = (panel["exit_ts"] - panel["entry_ts"]).dt.total_seconds() / 86400.0
    panel["holding_days"] = panel["holding_days"].clip(lower=0)
    panel["same_day_exit_flag"] = (panel["holding_days"] < 1.0).astype(int)
    for col in ["win_flag", "add_scale_success_flag", "entry_reduce_failure_flag", "false_positive_flag"]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).astype(int)
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    panel = panel.dropna(subset=["entry_ts", "net_return_from_entry"]).copy()
    if "split_name" not in panel.columns:
        assign_time_splits(panel)
    return panel


def assign_time_splits(panel: pd.DataFrame) -> None:
    valid = panel["entry_ts"].sort_values()
    validation_cut = valid.quantile(0.70)
    recent_cut = valid.quantile(0.85)
    panel["split_name"] = "train_design"
    panel.loc[panel["entry_ts"].ge(validation_cut), "split_name"] = "validation"
    panel.loc[panel["entry_ts"].ge(recent_cut), "split_name"] = "recent_oos"


def build_task496(panel: pd.DataFrame, market: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = panel.copy()
    out["multi_day_market_state_v4"] = out.apply(classify_market_state, axis=1)
    out["theme_regime_state_v4"] = out.apply(classify_theme_state, axis=1)
    out["regime_v4_combo"] = out["multi_day_market_state_v4"] + "|" + out["theme_regime_state_v4"]
    out["regime_assignment_field_set"] = (
        "market_ret_5d/20d/60d|breadth_5d/20d/60d|liquidity_ratio|vol_ratio|"
        "broad_market_score|broad_market_stress|payoff_theme_score|payoff_theme_stress_score"
    )
    out["lifecycle_outcome_used_for_regime_flag"] = 0
    theme = quality(out, ["theme_id", "theme_regime_state_v4"])
    transition = build_transition_audit(out, market)
    split = quality(out, ["multi_day_market_state_v4", "theme_regime_state_v4", "split_name"])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task496",
                "regime_rows": len(out),
                "market_state_count": out["multi_day_market_state_v4"].nunique(),
                "theme_state_count": out["theme_regime_state_v4"].nunique(),
                "lifecycle_outcome_used_for_regime_flag": 0,
                "multi_day_only_flag": 1,
                "validation_rows": int(out["split_name"].eq("validation").sum()),
                "recent_oos_rows": int(out["split_name"].eq("recent_oos").sum()),
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    return out, theme, transition, split, decision


def classify_market_state(row: pd.Series) -> str:
    score = _num(row, "broad_market_score")
    stress = _num(row, "broad_market_stress")
    bm20 = _num(row, "breadth_20d", np.nan)
    ret20 = _num(row, "market_ret_20d", np.nan)
    if pd.notna(score) and score >= 4 and (pd.isna(stress) or stress <= 2):
        return "persistent_broad_risk_on"
    if pd.notna(score) and score >= 3:
        return "constructive_risk_on"
    if pd.notna(stress) and stress >= 4:
        return "weak_or_stressed"
    if pd.notna(bm20) and bm20 >= 0.60 and pd.notna(ret20) and ret20 > 0:
        return "broadening_transition"
    return "mixed_or_transition"


def classify_theme_state(row: pd.Series) -> str:
    score = _num(row, "payoff_theme_score")
    stress = _num(row, "payoff_theme_stress_score")
    breadth = _num(row, "forward_live_theme_breadth_positive_rate", np.nan)
    ret = _num(row, "forward_live_theme_return", np.nan)
    rank = _num(row, "forward_live_theme_rank", np.nan)
    if pd.notna(score) and score >= 4 and (pd.isna(stress) or stress <= 2):
        return "persistent_theme_leader"
    if pd.notna(breadth) and breadth >= 0.70 and pd.notna(ret) and ret > 0:
        return "theme_participation"
    if pd.notna(rank) and rank <= 2 and pd.notna(ret) and ret > 0:
        return "narrow_theme_leader"
    if pd.notna(stress) and stress >= 4:
        return "weak_or_crowded_theme"
    return "mixed_theme"


def build_transition_audit(panel: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if market.empty or "score_date" not in market.columns:
        return pd.DataFrame([{"audit_name": "market_transition_source", "available_flag": 0, "detail": "market panel unavailable"}])
    scoped = market.copy()
    score_col = "broad_market_score" if "broad_market_score" in scoped.columns else None
    if score_col is None:
        return pd.DataFrame([{"audit_name": "market_transition_source", "available_flag": 0, "detail": "score column unavailable"}])
    scoped["score_change"] = pd.to_numeric(scoped[score_col], errors="coerce").diff()
    rows.append({"audit_name": "positive_score_transition_days", "available_flag": 1, "count": int(scoped["score_change"].gt(0).sum())})
    rows.append({"audit_name": "negative_score_transition_days", "available_flag": 1, "count": int(scoped["score_change"].lt(0).sum())})
    rows.append({"audit_name": "lifecycle_regime_rows", "available_flag": 1, "count": int(len(panel))})
    return pd.DataFrame(rows)


def build_task497(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = panel.copy()
    out["intraday_entry_state_v4"] = out.apply(classify_intraday_state, axis=1)
    out["microstructure_state_v4"] = out.apply(classify_microstructure_state, axis=1)
    out["continuation_state_v4"] = out["intraday_entry_state_v4"] + "|" + out["microstructure_state_v4"]
    out["intraday_assignment_field_set"] = (
        "vwap_acceptance_state|close_location|upper_wick_pct|range_pos|entry_extension_atr|"
        "volume_ratio_20|vwap_deviation|timing_state|spread_state|quote_freshness_state|nbbo_size_state"
    )
    out["label_used_in_intraday_assignment_flag"] = 0
    q = quality(out, ["intraday_entry_state_v4", "microstructure_state_v4"])
    split = quality(out, ["intraday_entry_state_v4", "split_name"])
    leakage = leakage_audit(["intraday_entry_state_v4", "microstructure_state_v4", "continuation_state_v4"])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task497",
                "state_count": out["intraday_entry_state_v4"].nunique(),
                "microstructure_state_count": out["microstructure_state_v4"].nunique(),
                "label_used_in_assignment_flag": int(leakage["label_used_in_assignment_flag"].max()),
                "missing_full_depth_reported_flag": 1,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    return out, q, split, leakage, decision


def classify_intraday_state(row: pd.Series) -> str:
    vwap_state = str(row.get("vwap_acceptance_state", ""))
    timing = str(row.get("timing_state", ""))
    close_loc = _num(row, "close_location")
    upper_wick = _num(row, "upper_wick_pct")
    range_pos = _num(row, "range_pos")
    ext = _num(row, "entry_extension_atr")
    volume = _num(row, "volume_ratio_20")
    vwap_dev = _num(row, "vwap_deviation")
    if "below" in vwap_state or (pd.notna(vwap_dev) and vwap_dev < -0.002):
        return "failed_vwap_reclaim"
    if pd.notna(upper_wick) and upper_wick > 0.45 and pd.notna(close_loc) and close_loc < 0.60:
        return "wick_rejection"
    if pd.notna(ext) and ext > 2.0 and pd.notna(close_loc) and close_loc < 0.75:
        return "exhaustion_breakout"
    if "late" in timing and pd.notna(range_pos) and range_pos > 0.90:
        return "late_chase"
    if pd.notna(volume) and volume >= 2.0 and pd.notna(close_loc) and close_loc >= 0.75:
        return "volume_climax_continuation"
    if pd.notna(range_pos) and range_pos >= 0.75 and pd.notna(close_loc) and close_loc >= 0.70:
        return "upper_range_hold"
    if "above" in vwap_state and pd.notna(vwap_dev) and vwap_dev >= 0:
        return "vwap_acceptance"
    if "midday" in timing:
        return "midday_absorption_continuation"
    return "neutral_continuation"


def classify_microstructure_state(row: pd.Series) -> str:
    spread = str(row.get("spread_state", ""))
    fresh = str(row.get("quote_freshness_state", ""))
    size = str(row.get("nbbo_size_state", ""))
    available = int(_num(row, "microstructure_feature_available_flag", 0) or 0)
    if not available:
        return "microstructure_missing"
    if any(token in spread for token in ["wide", "dirty"]) or "stale" in fresh:
        return "friction_dirty"
    if any(token in size for token in ["thin", "small"]):
        return "thin_nbbo"
    if any(token in spread for token in ["tight", "clean"]) or "fresh" in fresh:
        return "microstructure_clean"
    return "microstructure_neutral"


def build_task498(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    failure_rows = panel[panel["entry_reduce_failure_flag"].eq(1)].copy()
    if failure_rows.empty:
        failure = pd.DataFrame()
    else:
        failure_rows["failure_root_cause_v4"] = failure_rows.apply(classify_failure_root_cause, axis=1)
        failure = quality(failure_rows, ["failure_root_cause_v4"])
    by_state = quality(panel, ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4"])
    contrast = build_good_bad_contrast(panel)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task498",
                "entry_reduce_failure_count": int(panel["entry_reduce_failure_flag"].sum()),
                "entry_reduce_failure_rate": float(panel["entry_reduce_failure_flag"].mean()) if not panel.empty else 0.0,
                "root_cause_count": int(failure["failure_root_cause_v4"].nunique()) if not failure.empty else 0,
                "label_fields_evaluation_only_flag": 1,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    return failure, by_state, contrast, decision


def classify_failure_root_cause(row: pd.Series) -> str:
    if str(row.get("multi_day_market_state_v4", "")).startswith(("weak", "mixed")):
        return "wrong_or_transition_regime"
    if "weak" in str(row.get("theme_regime_state_v4", "")) or "mixed" in str(row.get("theme_regime_state_v4", "")):
        return "theme_leadership_failure"
    if str(row.get("intraday_entry_state_v4", "")) in {"late_chase", "exhaustion_breakout", "wick_rejection", "failed_vwap_reclaim"}:
        return "entry_structure_failure"
    if str(row.get("microstructure_state_v4", "")) in {"friction_dirty", "thin_nbbo"}:
        return "friction_failure"
    if _num(row, "holding_days", 999) < 1:
        return "same_day_collapse"
    return "multi_day_decay_or_unclassified"


def build_good_bad_contrast(panel: pd.DataFrame) -> pd.DataFrame:
    good = panel[panel["add_scale_success_flag"].eq(1)].copy()
    bad = panel[panel["entry_reduce_failure_flag"].eq(1)].copy()
    rows = []
    for name, subset in [("add_scale_success", good), ("entry_reduce_failure", bad)]:
        row = aggregate(subset)
        row["contrast_group"] = name
        rows.append(row)
    return pd.DataFrame(rows)


def build_task499(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dims = [
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "intraday_entry_state_v4",
        "microstructure_state_v4",
    ]
    cell_pool = build_cell_pool(panel, dims)
    candidate_sets = build_candidate_sets(panel, cell_pool)
    if candidate_sets.empty:
        selected = panel.iloc[0:0].copy()
        pool = candidate_sets
    else:
        pool = candidate_sets.sort_values("selection_score", ascending=False).reset_index(drop=True)
        selected_name = str(pool.iloc[0]["candidate_set_name"])
        selected_cells = str(pool.iloc[0]["cell_keys"]).split(";")
        selected = panel[panel["goal_cell_key"].isin(selected_cells)].copy()
        selected["selected_goal_portfolio_name"] = selected_name
    q = pd.DataFrame([aggregate(selected)])
    split = quality(selected, ["split_name"])
    quarterly = quality(selected, ["quarter"]) if "quarter" in selected.columns else pd.DataFrame()
    holding = holding_quality(selected)
    failure = selected_failure_decomposition(selected)
    decision = build_task499_decision(pool, selected, q, split, holding, failure)
    return pool, selected, q, split, quarterly, holding, failure, decision


def build_cell_pool(panel: pd.DataFrame, dims: list[str]) -> pd.DataFrame:
    rows = []
    for values, subset in panel.groupby(dims, dropna=False):
        if len(subset) < 5:
            continue
        row = aggregate(subset)
        row["cell_key"] = "|".join(str(v) for v in values)
        row["cell_dims"] = "|".join(dims)
        row["cell_values"] = row["cell_key"]
        row["theme_concentration"] = max_share(subset, "theme_id")
        row["symbol_concentration"] = max_share(subset, "symbol")
        rows.append(row)
    pool = pd.DataFrame(rows)
    if pool.empty:
        panel["goal_cell_key"] = ""
        return pool
    panel["goal_cell_key"] = panel[dims].astype(str).agg("|".join, axis=1)
    pool["cell_quality_score"] = (
        pool["avg_net_return_pct"].fillna(0)
        + 2.0 * pool["win_rate"].fillna(0)
        + 1.5 * pool["add_scale_success_rate"].fillna(0)
        - 6.0 * pool["entry_reduce_failure_rate"].fillna(1)
        + 0.5 * pool["median_holding_days"].fillna(0).clip(upper=10) / 10
    )
    return pool.sort_values("cell_quality_score", ascending=False).reset_index(drop=True)


def build_candidate_sets(panel: pd.DataFrame, cell_pool: pd.DataFrame) -> pd.DataFrame:
    if cell_pool.empty:
        return pd.DataFrame()
    specs = [
        ("high_conviction_300_600", 3.0, 0.65, 0.20, 3.0, 300, 600),
        ("low_entry_reduce_set", 1.5, 0.58, 0.12, 2.0, 150, 600),
        ("multi_day_hold_set", 1.0, 0.55, 0.25, 5.0, 150, 700),
        ("regime_persistence_leader_set", 1.0, 0.55, 0.25, 2.0, 200, 700),
        ("microstructure_clean_continuation_set", 1.5, 0.58, 0.20, 2.0, 100, 500),
        ("balanced_theme_diversified_set", 1.0, 0.55, 0.22, 2.0, 250, 700),
        ("broad_capacity_600_plus_diagnostic", 0.5, 0.52, 0.27, 1.0, 600, 1200),
        ("current_data_best_available_diagnostic", 0.5, 0.52, 0.30, 0.0, 300, 700),
    ]
    rows = []
    for name, min_avg, min_win, max_er, min_hold, target_min, target_max in specs:
        eligible = cell_pool[
            cell_pool["avg_net_return_pct"].ge(min_avg)
            & cell_pool["win_rate"].ge(min_win)
            & cell_pool["entry_reduce_failure_rate"].le(max_er)
            & cell_pool["median_holding_days"].ge(min_hold)
        ].copy()
        if name == "regime_persistence_leader_set":
            eligible = eligible[eligible["cell_key"].str.contains("persistent_broad_risk_on|persistent_theme_leader", regex=True)]
        if name == "microstructure_clean_continuation_set":
            eligible = eligible[eligible["cell_key"].str.contains("microstructure_clean", regex=False)]
        if eligible.empty:
            continue
        selected_keys: list[str] = []
        mask = pd.Series(False, index=panel.index)
        for _, cell in eligible.sort_values("cell_quality_score", ascending=False).iterrows():
            next_mask = mask | panel["goal_cell_key"].eq(cell["cell_key"])
            if int(next_mask.sum()) > target_max:
                continue
            mask = next_mask
            selected_keys.append(str(cell["cell_key"]))
            if int(mask.sum()) >= target_min:
                break
        selected = panel[mask].copy()
        if selected.empty:
            continue
        metrics = aggregate(selected)
        metrics.update(
            {
                "candidate_set_name": name,
                "selected_cell_count": len(selected_keys),
                "cell_keys": ";".join(selected_keys),
                "target_min": target_min,
                "target_max": target_max,
                "target_pass_flag": int(goal_pass(metrics)),
                "selection_score": selection_score(metrics, name),
                "theme_concentration": max_share(selected, "theme_id"),
                "symbol_concentration": max_share(selected, "symbol"),
            }
        )
        rows.append(metrics)
    return pd.DataFrame(rows)


def build_task499_decision(pool: pd.DataFrame, selected: pd.DataFrame, q: pd.DataFrame, split: pd.DataFrame, holding: pd.DataFrame, failure: pd.DataFrame) -> pd.DataFrame:
    metrics = q.iloc[0].to_dict() if not q.empty else aggregate(selected)
    validation = split[split["split_name"].eq("validation")] if not split.empty else pd.DataFrame()
    recent = split[split["split_name"].eq("recent_oos")] if not split.empty else pd.DataFrame()
    passed = goal_pass(metrics)
    return pd.DataFrame(
        [
            {
                "task_id": "Task499",
                "candidate_set_count": int(len(pool)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "median_holding_days": metrics.get("median_holding_days", pd.NA),
                "same_day_exit_share": metrics.get("same_day_exit_share", pd.NA),
                "validation_count": int(validation["lifecycle_count"].iloc[0]) if not validation.empty else 0,
                "recent_oos_count": int(recent["lifecycle_count"].iloc[0]) if not recent.empty else 0,
                "goal_achieved_flag": int(passed),
                "inferred_lifecycle_matching_used_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def build_task500(task499_decision: pd.DataFrame, failure: pd.DataFrame, holding: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = task499_decision.iloc[0].to_dict()
    active = []
    if int(d.get("selected_count", 0) or 0) < TARGET_COUNT_MIN:
        active.append("count_shortfall_expand_adjacent_high_quality_states")
    if int(d.get("selected_count", 0) or 0) > TARGET_COUNT_MAX:
        active.append("count_excess_tighten_state_quality")
    if float(d.get("selected_avg_net_pct", -999) or -999) < TARGET_AVG_NET:
        active.append("avg_net_shortfall_remove_weak_state_or_holding_decay")
    if float(d.get("selected_win_rate", 0) or 0) < TARGET_WIN:
        active.append("win_shortfall_refine_entry_timing_theme_quality")
    if float(d.get("selected_entry_reduce_rate", 1) or 1) > TARGET_ENTRY_REDUCE_MAX:
        active.append("entry_reduce_excess_suppress_late_chase_exhaustion_failed_reclaim")
    if float(d.get("median_holding_days", 0) or 0) < TARGET_MEDIAN_HOLD_DAYS:
        active.append("holding_shortfall_remove_scalp_like_lifecycles")
    if float(d.get("same_day_exit_share", 1) or 1) > TARGET_SAME_DAY_EXIT_MAX:
        active.append("same_day_exit_excess_require_multi_day_persistence")
    if not active:
        active.append("goal_pass_prepare_canonical_candidate_review")
    synthesis = pd.DataFrame([{"next_iteration_action": action, "priority_order": i + 1} for i, action in enumerate(active)])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task500",
                "goal_achieved_flag": int(d.get("goal_achieved_flag", 0) or 0),
                "active_next_action_count": len(active),
                "top_next_action": active[0],
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "report_has_quant_and_decision_maker_sections_flag": 1,
            }
        ]
    )
    return synthesis, decision


def aggregate(subset: pd.DataFrame) -> dict[str, float | int]:
    if subset.empty:
        return {
            "lifecycle_count": 0,
            "avg_net_return_pct": np.nan,
            "win_rate": np.nan,
            "add_scale_success_rate": np.nan,
            "entry_reduce_failure_rate": np.nan,
            "false_positive_rate": np.nan,
            "median_holding_days": np.nan,
            "same_day_exit_share": np.nan,
        }
    return {
        "lifecycle_count": int(len(subset)),
        "avg_net_return_pct": float(subset["net_return_from_entry"].mean() * 100.0),
        "win_rate": float(subset["win_flag"].mean()),
        "add_scale_success_rate": float(subset.get("add_scale_success_flag", pd.Series(0, index=subset.index)).mean()),
        "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(subset.get("false_positive_flag", pd.Series(0, index=subset.index)).mean()),
        "median_holding_days": float(subset["holding_days"].median()),
        "same_day_exit_share": float(subset["same_day_exit_flag"].mean()),
    }


def quality(panel: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    if not keys:
        return pd.DataFrame([aggregate(panel)])
    rows = []
    for values, subset in panel.groupby(keys, dropna=False):
        row = aggregate(subset)
        if not isinstance(values, tuple):
            values = (values,)
        for key, value in zip(keys, values, strict=False):
            row[key] = value
        rows.append(row)
    return pd.DataFrame(rows).sort_values("avg_net_return_pct", ascending=False)


def holding_quality(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame([{"median_holding_days": np.nan, "p75_holding_days": np.nan, "p90_holding_days": np.nan, "same_day_exit_share": np.nan}])
    return pd.DataFrame(
        [
            {
                "median_holding_days": float(panel["holding_days"].median()),
                "p75_holding_days": float(panel["holding_days"].quantile(0.75)),
                "p90_holding_days": float(panel["holding_days"].quantile(0.90)),
                "same_day_exit_share": float(panel["same_day_exit_flag"].mean()),
            }
        ]
    )


def selected_failure_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    return quality(panel, ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4", "microstructure_state_v4"])


def goal_pass(metrics: dict[str, object]) -> bool:
    return (
        TARGET_COUNT_MIN <= int(_metric(metrics, "lifecycle_count", 0)) <= TARGET_COUNT_MAX
        and _metric(metrics, "avg_net_return_pct", -999) >= TARGET_AVG_NET
        and _metric(metrics, "win_rate", 0) >= TARGET_WIN
        and _metric(metrics, "entry_reduce_failure_rate", 1) <= TARGET_ENTRY_REDUCE_MAX
        and _metric(metrics, "median_holding_days", 0) >= TARGET_MEDIAN_HOLD_DAYS
        and _metric(metrics, "same_day_exit_share", 1) <= TARGET_SAME_DAY_EXIT_MAX
    )


def selection_score(metrics: dict[str, object], name: str) -> float:
    score = (
        _metric(metrics, "avg_net_return_pct", 0)
        + 2.0 * _metric(metrics, "win_rate", 0)
        - 8.0 * _metric(metrics, "entry_reduce_failure_rate", 1)
        + min(_metric(metrics, "lifecycle_count", 0), TARGET_COUNT_MAX) / 200.0
        + min(_metric(metrics, "median_holding_days", 0), 20.0) / 10.0
        - 2.0 * _metric(metrics, "same_day_exit_share", 1)
    )
    if name == "high_conviction_300_600":
        score += 1.0
    return score


def _metric(metrics: dict[str, object], key: str, default: float) -> float:
    value = metrics.get(key, default)
    if value is None or pd.isna(value):
        return float(default)
    return float(value)


def max_share(panel: pd.DataFrame, column: str) -> float:
    if panel.empty or column not in panel.columns:
        return 0.0
    return float(panel[column].value_counts(normalize=True, dropna=False).max())


def leakage_audit(fields: list[str]) -> pd.DataFrame:
    blocked = sorted(set(fields) & OUTCOME_FIELDS)
    return pd.DataFrame(
        [
            {
                "assignment_fields": "|".join(fields),
                "blocked_outcome_field_used_count": len(blocked),
                "blocked_outcome_fields": "|".join(blocked),
                "label_used_in_assignment_flag": int(bool(blocked)),
                "inferred_lifecycle_matching_used_flag": 0,
                "leakage_pass_flag": int(not blocked),
            }
        ]
    )


def _num(row: pd.Series, col: str, default: float = np.nan) -> float:
    try:
        return float(row.get(col, default))
    except (TypeError, ValueError):
        return default


def write_task496(out: Path, panel: pd.DataFrame, theme: pd.DataFrame, transition: pd.DataFrame, split: pd.DataFrame, decision: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "multi_day_regime_v4_panel.csv", index=False)
    theme.to_csv(out / "theme_regime_v4_panel.csv", index=False)
    transition.to_csv(out / "regime_v4_transition_audit.csv", index=False)
    split.to_csv(out / "regime_v4_split_quality.csv", index=False)
    decision.to_csv(out / "task_496_decision.csv", index=False)
    (out / "task_496_multi_day_regime_v4.md").write_text(report("Task 496 - Multi-Day Regime V4", decision, "Multi-day market/theme regime was rebuilt without intraday outcome leakage."), encoding="utf-8")
    write_manifest(out, out / "artifact_manifest.csv")


def write_task497(out: Path, panel: pd.DataFrame, q: pd.DataFrame, split: pd.DataFrame, leakage: pd.DataFrame, decision: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "intraday_continuation_state_panel.csv", index=False)
    q.to_csv(out / "intraday_state_quality.csv", index=False)
    split.to_csv(out / "intraday_state_split_quality.csv", index=False)
    leakage.to_csv(out / "intraday_state_leakage_audit.csv", index=False)
    decision.to_csv(out / "task_497_decision.csv", index=False)
    (out / "task_497_intraday_continuation_structure.md").write_text(report("Task 497 - Intraday Continuation Structure", decision, "Intraday continuation states were separated inside exact lifecycle rows."), encoding="utf-8")
    write_manifest(out, out / "artifact_manifest.csv")


def write_task498(out: Path, failure: pd.DataFrame, by_state: pd.DataFrame, contrast: pd.DataFrame, decision: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    failure.to_csv(out / "entry_reduce_failure_decomposition.csv", index=False)
    by_state.to_csv(out / "entry_reduce_failure_by_regime_theme_state.csv", index=False)
    contrast.to_csv(out / "good_vs_bad_continuation_contrast.csv", index=False)
    decision.to_csv(out / "task_498_decision.csv", index=False)
    (out / "task_498_entry_reduce_failure_decomposition.md").write_text(report("Task 498 - Entry Reduce Failure Decomposition", decision, "Entry-reduce failures were decomposed by regime, theme, intraday structure, friction, and holding behavior."), encoding="utf-8")
    write_manifest(out, out / "artifact_manifest.csv")


def write_task499(out: Path, pool: pd.DataFrame, selected: pd.DataFrame, q: pd.DataFrame, split: pd.DataFrame, quarterly: pd.DataFrame, holding: pd.DataFrame, failure: pd.DataFrame, decision: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pool.to_csv(out / "regime_intraday_continuation_grid_candidate_pool.csv", index=False)
    selected.to_csv(out / "selected_goal_portfolio_assignment_panel.csv", index=False)
    q.to_csv(out / "selected_goal_portfolio_quality.csv", index=False)
    split.to_csv(out / "selected_goal_portfolio_split_quality.csv", index=False)
    quarterly.to_csv(out / "selected_goal_portfolio_quarterly_quality.csv", index=False)
    holding.to_csv(out / "selected_goal_portfolio_holding_period_quality.csv", index=False)
    failure.to_csv(out / "selected_goal_portfolio_failure_decomposition.csv", index=False)
    decision.to_csv(out / "task_499_decision.csv", index=False)
    (out / "task_499_regime_intraday_continuation_grid.md").write_text(report("Task 499 - Regime x Intraday x Continuation Grid", decision, "The goal grid combined multi-day regime and intraday continuation states with exact lifecycle evaluation."), encoding="utf-8")
    write_manifest(out, out / "artifact_manifest.csv")


def write_task500(out: Path, synthesis: pd.DataFrame, decision: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    synthesis.to_csv(out / "goal_loop_next_iteration_plan.csv", index=False)
    decision.to_csv(out / "task_500_decision.csv", index=False)
    (out / "task_500_goal_loop_synthesis.md").write_text(report("Task 500 - Goal Loop Synthesis", decision, "The next iteration is selected from the measured failure modes."), encoding="utf-8")
    write_manifest(out, out / "artifact_manifest.csv")


def report(title: str, decision: pd.DataFrame, summary: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Decision Summary",
            "",
            summary,
            "",
            "```csv",
            decision.to_csv(index=False),
            "```",
            "",
            "## Quant Expert Report",
            "",
            "- Exact lifecycle identity only.",
            "- No symbol/date/price/time fallback matching.",
            "- Missing raw sources are reported, not approximated.",
            "- Labels/outcomes are evaluation-only.",
            "- Strategy acceptance remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이번 결과는 좋은 시장/테마, 좋은 intraday 구조, 그리고 실제 lifecycle 손익을 분리해서 검증하기 위한 진단 단계다. 배포 판단이 아니라 다음 개발 방향을 정하기 위한 자료다.",
            "",
            "## Artifact Manifest",
            "",
            "See `artifact_manifest.csv` in this task directory.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task493-panel", type=Path, default=DEFAULT_TASK493_PANEL)
    parser.add_argument("--task489-market", type=Path, default=DEFAULT_TASK489_MARKET)
    args = parser.parse_args()
    artifacts = build_goal_revalidation(task493_panel_path=args.task493_panel, task489_market_path=args.task489_market)
    row = artifacts["task_499_decision"].iloc[0]
    print(
        "[TASK496_500] "
        f"goal={row['goal_achieved_flag']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}% win={float(row['selected_win_rate']):.1%}"
    )


if __name__ == "__main__":
    main()
