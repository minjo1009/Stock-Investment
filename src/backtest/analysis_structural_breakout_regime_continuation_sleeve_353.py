from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import _apply_cost_scaled, _f
from src.backtest.analysis_structural_breakout_continuation_regime_persistence_351 import (
    _artifact_vs_structure,
    _candidate_rows,
    _filter_candidate,
    _positive_tail_persistence,
    _prepare_continuation_master,
)
from src.backtest.analysis_structural_breakout_continuation_regime_reframing_352 import _relative_ranking
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import ROLLING_WINDOWS
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _annual_trade_frequency
from src.backtest.analysis_structural_breakout_alpha_family_viability_350 import _metrics, _scaled_frame


DEFAULT_OUT_DIR = Path("docs/reports/task_353_regime_continuation_sleeve")
STRUCTURE_ORDER = (
    "single_best_binary",
    "top_regime_basket_binary",
    "score_ranked_top3",
    "regime_conditioned_overlay_balanced",
)
SIZING_TEMPLATES: dict[str, dict[str, float]] = {
    "balanced": {"core": 1.50, "active": 1.00, "light": 0.50, "skip": 0.0},
    "aggressive": {"core": 2.00, "active": 1.25, "light": 0.50, "skip": 0.0},
    "persistence_adjusted": {"core": 1.50, "active": 0.90, "light": 0.25, "skip": 0.0},
}


def _anchored_oos_mask(df: pd.DataFrame) -> pd.Series:
    current_split = df["current_split"].astype(str) if "current_split" in df.columns else pd.Series("", index=df.index)
    if current_split.eq("test").any():
        return current_split.eq("test")
    fallback_start = min(pd.Timestamp(window.oos_start, tz="UTC") for window in ROLLING_WINDOWS)
    entry_ts = pd.to_datetime(df["entry_ts"], errors="coerce", utc=True)
    return entry_ts >= fallback_start


def _percentile_rank(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() <= 1:
        return pd.Series(np.where(values.notna(), 1.0, math.nan), index=series.index, dtype=float)
    return values.rank(method="average", pct=True)


def _selected_regimes(ranked_df: pd.DataFrame) -> pd.DataFrame:
    top_ids: list[str] = []
    top_ids.extend(ranked_df.head(5)["regime_id"].astype(str).tolist())
    top_ids.extend(ranked_df[ranked_df["candidate_type"] == "single_axis"].head(3)["regime_id"].astype(str).tolist())
    top_ids.extend(ranked_df[ranked_df["candidate_type"] == "interaction"].head(3)["regime_id"].astype(str).tolist())
    top_ids = list(dict.fromkeys(top_ids))
    selected = ranked_df[ranked_df["regime_id"].astype(str).isin(top_ids)].copy()
    selected["selection_bucket"] = np.where(
        selected["regime_id"].astype(str).isin(ranked_df.head(5)["regime_id"].astype(str)),
        "top5_overall",
        np.where(selected["candidate_type"].astype(str).eq("single_axis"), "top3_single_axis", "top3_interaction"),
    )
    selected["artifact_adjusted_weight"] = (
        pd.to_numeric(selected["continuation_quality_score"], errors="coerce").fillna(0.0)
        * pd.to_numeric(selected["structural_share"], errors="coerce").fillna(0.0)
    ).round(6)
    return selected.sort_values(
        ["continuation_quality_score", "artifact_adjusted_weight", "trade_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def _match_regime(master: pd.DataFrame, regime_row: pd.Series) -> pd.Index:
    axes = str(regime_row["axes"]).split("|")
    buckets = str(regime_row["buckets"]).split("|")
    return _filter_candidate(master, axes, buckets).index


def _build_participation_scorecard(master: pd.DataFrame, selected_df: pd.DataFrame) -> pd.DataFrame:
    scorecard = master[
        ["trade_id", "symbol", "entry_ts", "current_split", "sector_group", "realized_R"]
    ].copy()
    scorecard["regime_participation_score"] = 0.0
    scorecard["artifact_adjusted_score"] = 0.0
    scorecard["matched_regime_count"] = 0
    scorecard["matched_regime_ids"] = ""
    scorecard["matched_selection_buckets"] = ""
    scorecard["single_best_match"] = False

    top_regime_id = str(selected_df.iloc[0]["regime_id"]) if not selected_df.empty else ""
    for _, regime_row in selected_df.iterrows():
        idx = _match_regime(master, regime_row)
        raw_score = float(pd.to_numeric(pd.Series([regime_row["continuation_quality_score"]]), errors="coerce").iloc[0])
        adjusted_score = float(pd.to_numeric(pd.Series([regime_row["artifact_adjusted_weight"]]), errors="coerce").iloc[0])
        scorecard.loc[idx, "regime_participation_score"] += raw_score
        scorecard.loc[idx, "artifact_adjusted_score"] += adjusted_score
        scorecard.loc[idx, "matched_regime_count"] += 1
        current_ids = scorecard.loc[idx, "matched_regime_ids"].astype(str)
        current_buckets = scorecard.loc[idx, "matched_selection_buckets"].astype(str)
        regime_id = str(regime_row["regime_id"])
        selection_bucket = str(regime_row["selection_bucket"])
        scorecard.loc[idx, "matched_regime_ids"] = current_ids.map(
            lambda value: regime_id if value == "" else value if regime_id in value.split("|") else value + "|" + regime_id
        )
        scorecard.loc[idx, "matched_selection_buckets"] = current_buckets.map(
            lambda value: selection_bucket
            if value == ""
            else value
            if selection_bucket in value.split("|")
            else value + "|" + selection_bucket
        )
        if str(regime_row["regime_id"]) == top_regime_id:
            scorecard.loc[idx, "single_best_match"] = True

    scorecard["matched_regime_ids"] = scorecard["matched_regime_ids"].str.strip("|")
    scorecard["matched_selection_buckets"] = scorecard["matched_selection_buckets"].str.strip("|")
    positive_raw = scorecard["regime_participation_score"] > 0
    positive_adjusted = scorecard["artifact_adjusted_score"] > 0
    scorecard["regime_score_percentile"] = math.nan
    scorecard["artifact_score_percentile"] = math.nan
    if positive_raw.any():
        scorecard.loc[positive_raw, "regime_score_percentile"] = _percentile_rank(
            scorecard.loc[positive_raw, "regime_participation_score"]
        )
    if positive_adjusted.any():
        scorecard.loc[positive_adjusted, "artifact_score_percentile"] = _percentile_rank(
            scorecard.loc[positive_adjusted, "artifact_adjusted_score"]
        )
    scorecard["participation_tier"] = np.select(
        [
            (pd.to_numeric(scorecard["matched_regime_count"], errors="coerce") >= 2)
            | (pd.to_numeric(scorecard["regime_score_percentile"], errors="coerce") >= 0.8),
            pd.to_numeric(scorecard["regime_score_percentile"], errors="coerce") >= 0.5,
            pd.to_numeric(scorecard["matched_regime_count"], errors="coerce") >= 1,
        ],
        ["core", "active", "light"],
        default="skip",
    )
    scorecard["artifact_adjusted_tier"] = np.select(
        [
            pd.to_numeric(scorecard["artifact_score_percentile"], errors="coerce") >= 0.8,
            pd.to_numeric(scorecard["artifact_score_percentile"], errors="coerce") >= 0.5,
            pd.to_numeric(scorecard["artifact_adjusted_score"], errors="coerce") > 0,
        ],
        ["core", "active", "light"],
        default="skip",
    )
    return scorecard.sort_values(["entry_ts", "regime_participation_score"], ascending=[True, False]).reset_index(drop=True)


def _rolling_positive_share(df: pd.DataFrame, value_col: str = "scaled_R") -> float:
    positives = 0
    total = 0
    for window in ROLLING_WINDOWS:
        scoped = df[
            (df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        total += 1
        if float(pd.to_numeric(scoped[value_col], errors="coerce").mean()) > 0:
            positives += 1
    return float(positives / max(total, 1))


def _monetization_score(metrics: dict[str, Any], annual_trade_frequency: float, capital_utilization: float, rolling_oos: float) -> float:
    cost_adj = float(pd.to_numeric(pd.Series([metrics["cost_adjusted_expectancy"]]), errors="coerce").iloc[0])
    expectancy = float(pd.to_numeric(pd.Series([metrics["expectancy"]]), errors="coerce").iloc[0])
    cost_component = max(cost_adj, 0.0) / max(abs(cost_adj) + 0.25, 1e-9)
    expectancy_component = max(expectancy, 0.0) / max(abs(expectancy) + 0.25, 1e-9)
    capital_component = min(max(capital_utilization, 0.0) * 4.0, 1.0)
    activity_component = min(max(annual_trade_frequency, 0.0) / 100.0, 1.0)
    return _f(
        0.35 * cost_component
        + 0.25 * rolling_oos
        + 0.20 * expectancy_component
        + 0.10 * capital_component
        + 0.10 * activity_component
    )


def _evaluate_frame(
    name: str,
    frame: pd.DataFrame,
    eligible_trade_days: int,
    multipliers: pd.Series | None = None,
    structure_group: str = "basket",
) -> dict[str, Any]:
    scoped = frame.copy()
    if scoped.empty:
        return {
            "structure_name": name,
            "structure_group": structure_group,
            "trade_count": 0,
            "annual_trade_frequency": 0.0,
            "expectancy": math.nan,
            "sharpe_proxy": math.nan,
            "mdd_pct": math.nan,
            "return_contribution": math.nan,
            "cost_adjusted_expectancy": math.nan,
            "cost_2x_expectancy": math.nan,
            "turnover_proxy": 0.0,
            "capital_utilization": 0.0,
            "concentration": math.nan,
            "rolling_oos_robustness": 0.0,
            "anchored_oos_expectancy": math.nan,
            "anchored_oos_cost_adjusted_expectancy": math.nan,
            "monetization_score": 0.0,
        }
    if "exit_ts" not in scoped.columns:
        scoped["exit_ts"] = pd.to_datetime(scoped["entry_ts"], errors="coerce", utc=True)
    if "entry_ts" in scoped.columns:
        scoped["entry_ts"] = pd.to_datetime(scoped["entry_ts"], errors="coerce", utc=True)
    if "exit_ts" in scoped.columns:
        scoped["exit_ts"] = pd.to_datetime(scoped["exit_ts"], errors="coerce", utc=True)
    scaled = _scaled_frame(scoped, multipliers)
    metrics = _metrics(scaled)
    entry_days = pd.to_datetime(scaled["entry_ts"], errors="coerce", utc=True).dt.normalize()
    annual_trade_frequency = _annual_trade_frequency(scaled)
    capital_utilization = float(entry_days.dropna().nunique() / max(eligible_trade_days, 1))
    cost_2x = pd.to_numeric(_apply_cost_scaled(scaled, 0.0020, 0.0010), errors="coerce")
    anchored = scaled[_anchored_oos_mask(scaled)].copy()
    anchored_cost = pd.to_numeric(_apply_cost_scaled(anchored, 0.0010, 0.0005), errors="coerce") if not anchored.empty else pd.Series(dtype=float)
    anchored_expectancy = float(pd.to_numeric(anchored["scaled_R"], errors="coerce").mean()) if not anchored.empty else math.nan
    anchored_cost_expectancy = float(anchored_cost.mean()) if not anchored_cost.empty else math.nan
    rolling_oos = _rolling_positive_share(scaled, "scaled_R")
    return {
        "structure_name": name,
        "structure_group": structure_group,
        "trade_count": int(len(scaled)),
        "annual_trade_frequency": _f(annual_trade_frequency),
        "expectancy": metrics["expectancy"],
        "sharpe_proxy": metrics["sharpe_proxy"],
        "mdd_pct": metrics["mdd_pct"],
        "return_contribution": _f(float(pd.to_numeric(scaled["scaled_R"], errors="coerce").sum())),
        "cost_adjusted_expectancy": metrics["cost_adjusted_expectancy"],
        "cost_2x_expectancy": _f(float(cost_2x.mean())) if not cost_2x.empty else math.nan,
        "turnover_proxy": _f(float(len(scaled) / max(eligible_trade_days, 1))),
        "capital_utilization": _f(capital_utilization),
        "concentration": metrics["concentration"],
        "rolling_oos_robustness": _f(rolling_oos),
        "anchored_oos_expectancy": _f(anchored_expectancy) if not math.isnan(anchored_expectancy) else math.nan,
        "anchored_oos_cost_adjusted_expectancy": _f(anchored_cost_expectancy) if not math.isnan(anchored_cost_expectancy) else math.nan,
        "monetization_score": _monetization_score(metrics, annual_trade_frequency, capital_utilization, rolling_oos),
    }


def _apply_structure_frames(master: pd.DataFrame, scorecard: pd.DataFrame) -> dict[str, tuple[pd.DataFrame, pd.Series | None]]:
    merged = master.merge(
        scorecard[
            [
                "trade_id",
                "regime_participation_score",
                "artifact_adjusted_score",
                "matched_regime_count",
                "regime_score_percentile",
                "artifact_score_percentile",
                "participation_tier",
                "artifact_adjusted_tier",
                "single_best_match",
            ]
        ],
        on="trade_id",
        how="left",
    )
    merged["participation_tier"] = merged["participation_tier"].fillna("skip")
    merged["artifact_adjusted_tier"] = merged["artifact_adjusted_tier"].fillna("skip")

    basket_mask = pd.to_numeric(merged["matched_regime_count"], errors="coerce").fillna(0).ge(1)
    single_best = merged[merged["single_best_match"].astype(bool)].copy()
    basket = merged[basket_mask].copy()
    ranked = basket.sort_values(
        ["entry_ts", "regime_participation_score", "artifact_adjusted_score"],
        ascending=[True, False, False],
    ).copy()
    ranked["daily_rank"] = ranked.groupby(ranked["entry_ts"].dt.strftime("%Y-%m-%d")).cumcount() + 1
    top3 = ranked[ranked["daily_rank"] <= 3].copy()
    balanced_mult = ranked["participation_tier"].map(SIZING_TEMPLATES["balanced"]).fillna(0.0)
    return {
        "single_best_binary": (single_best, None),
        "top_regime_basket_binary": (basket, None),
        "score_ranked_top3": (top3, None),
        "regime_conditioned_overlay_balanced": (ranked, balanced_mult),
    }


def _basket_comparison(master: pd.DataFrame, scorecard: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.Series | None]]]:
    eligible_days = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    frames = _apply_structure_frames(master, scorecard)
    rows = [
        _evaluate_frame(name, frame, int(eligible_days), multipliers, "basket")
        for name, (frame, multipliers) in frames.items()
    ]
    out = pd.DataFrame(rows)
    out["structure_name"] = pd.Categorical(out["structure_name"], categories=list(STRUCTURE_ORDER), ordered=True)
    out = out.sort_values(["structure_name"]).reset_index(drop=True)
    return out, frames


def _template_multipliers(frame: pd.DataFrame, template_name: str) -> pd.Series:
    if template_name == "persistence_adjusted":
        tier_series = frame["artifact_adjusted_tier"]
    else:
        tier_series = frame["participation_tier"]
    return tier_series.map(SIZING_TEMPLATES[template_name]).fillna(0.0)


def _sizing_template_comparison(master: pd.DataFrame, scorecard: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.Series | None]]]:
    eligible_days = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    merged = master.merge(
        scorecard[
            [
                "trade_id",
                "matched_regime_count",
                "participation_tier",
                "artifact_adjusted_tier",
            ]
        ],
        on="trade_id",
        how="left",
    )
    base = merged[pd.to_numeric(merged["matched_regime_count"], errors="coerce").fillna(0).ge(1)].copy()
    frames: dict[str, tuple[pd.DataFrame, pd.Series | None]] = {}
    rows: list[dict[str, Any]] = []
    for template_name in SIZING_TEMPLATES:
        multipliers = _template_multipliers(base, template_name)
        structure_name = f"sizing_template_{template_name}"
        frames[structure_name] = (base.copy(), multipliers)
        rows.append(_evaluate_frame(structure_name, base, int(eligible_days), multipliers, "sizing"))
    return pd.DataFrame(rows).sort_values(["monetization_score", "cost_adjusted_expectancy"], ascending=[False, False]).reset_index(drop=True), frames


def _artifact_adjusted_sleeve(master: pd.DataFrame, scorecard: pd.DataFrame) -> pd.DataFrame:
    eligible_days = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    merged = master.merge(
        scorecard[
            [
                "trade_id",
                "matched_regime_count",
                "artifact_adjusted_score",
                "artifact_score_percentile",
            ]
        ],
        on="trade_id",
        how="left",
    )
    base = merged[pd.to_numeric(merged["matched_regime_count"], errors="coerce").fillna(0).ge(1)].copy()
    half_plus = base[pd.to_numeric(base["artifact_score_percentile"], errors="coerce") >= 0.5].copy()
    core = base[pd.to_numeric(base["artifact_score_percentile"], errors="coerce") >= 0.8].copy()
    rows = [
        _evaluate_frame("raw_top_basket", base, int(eligible_days), None, "artifact_adjusted"),
        _evaluate_frame("artifact_half_plus", half_plus, int(eligible_days), None, "artifact_adjusted"),
        _evaluate_frame("artifact_core", core, int(eligible_days), None, "artifact_adjusted"),
    ]
    return pd.DataFrame(rows).sort_values(["monetization_score", "cost_adjusted_expectancy"], ascending=[False, False]).reset_index(drop=True)


def _oos_validation(
    structure_name: str,
    frame: pd.DataFrame,
    eligible_days: int,
    multipliers: pd.Series | None = None,
) -> pd.DataFrame:
    rows = []
    full_eval = _evaluate_frame(structure_name, frame, eligible_days, multipliers, "oos_validation")
    full_eval["scope"] = "full_period"
    full_eval["window_id"] = ""
    rows.append(full_eval)

    anchored = frame[_anchored_oos_mask(frame)].copy()
    anchored_mult = multipliers.loc[anchored.index] if multipliers is not None and not anchored.empty else None
    anchored_eval = _evaluate_frame(structure_name, anchored, eligible_days, anchored_mult, "oos_validation")
    anchored_eval["scope"] = "anchored_oos"
    anchored_eval["window_id"] = ""
    rows.append(anchored_eval)

    for window in ROLLING_WINDOWS:
        scoped = frame[
            (frame["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (frame["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        scoped_mult = multipliers.loc[scoped.index] if multipliers is not None and not scoped.empty else None
        eval_row = _evaluate_frame(structure_name, scoped, eligible_days, scoped_mult, "oos_validation")
        eval_row["scope"] = "rolling_window"
        eval_row["window_id"] = window.window_id
        rows.append(eval_row)
    return pd.DataFrame(rows)


def _economic_utility(best_row: pd.Series, best_name: str) -> pd.DataFrame:
    annual_trade_frequency = float(pd.to_numeric(pd.Series([best_row["annual_trade_frequency"]]), errors="coerce").iloc[0])
    capital_utilization = float(pd.to_numeric(pd.Series([best_row["capital_utilization"]]), errors="coerce").iloc[0])
    concentration = float(pd.to_numeric(pd.Series([best_row["concentration"]]), errors="coerce").iloc[0])
    cost_adj = float(pd.to_numeric(pd.Series([best_row["cost_adjusted_expectancy"]]), errors="coerce").iloc[0])
    rolling = float(pd.to_numeric(pd.Series([best_row["rolling_oos_robustness"]]), errors="coerce").iloc[0])
    usable_bucket = (
        "moderate"
        if annual_trade_frequency >= 50 and capital_utilization >= 0.10
        else "small"
        if annual_trade_frequency >= 20
        else "tiny"
    )
    concentration_risk = "high" if concentration >= 0.50 else "medium" if concentration >= 0.35 else "low"
    execution_fragility = "high" if rolling < 0.50 else "medium" if rolling < 0.75 else "low"
    expected_live_slippage = "elevated" if cost_adj <= 0.20 else "manageable" if cost_adj <= 0.50 else "contained"
    likely_decay = "high" if float(pd.to_numeric(pd.Series([best_row["monetization_score"]]), errors="coerce").iloc[0]) < 0.55 else "medium" if concentration >= 0.35 else "moderate"
    shadow_ready = cost_adj > 0 and rolling >= 0.5
    return pd.DataFrame(
        [
            {
                "best_structure": best_name,
                "trade_count": best_row["trade_count"],
                "annual_trade_frequency": best_row["annual_trade_frequency"],
                "capital_utilization": best_row["capital_utilization"],
                "usable_capital_bucket": usable_bucket,
                "concentration_risk": concentration_risk,
                "execution_fragility": execution_fragility,
                "expected_live_slippage": expected_live_slippage,
                "shadow_monitor_suitability": shadow_ready,
                "likely_live_decay_risk": likely_decay,
            }
        ]
    )


def _final_decision(
    basket_df: pd.DataFrame,
    sizing_df: pd.DataFrame,
    artifact_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    utility_df: pd.DataFrame,
) -> pd.DataFrame:
    combined = pd.concat([basket_df, sizing_df], ignore_index=True)
    combined = combined.sort_values(
        ["monetization_score", "cost_adjusted_expectancy", "rolling_oos_robustness"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    best = combined.iloc[0] if not combined.empty else pd.Series(dtype=object)
    best_name = str(best.get("structure_name", ""))
    top_basket = basket_df[basket_df["structure_name"] == "top_regime_basket_binary"]
    overlay = basket_df[basket_df["structure_name"] == "regime_conditioned_overlay_balanced"]
    artifact_best = artifact_df.sort_values(["monetization_score", "cost_adjusted_expectancy"], ascending=[False, False]).iloc[0] if not artifact_df.empty else pd.Series(dtype=object)
    rolling_rows = oos_df[oos_df["scope"].astype(str) == "rolling_window"].copy()
    positive_rolling_share = float(
        (pd.to_numeric(rolling_rows["expectancy"], errors="coerce") > 0).mean()
    ) if not rolling_rows.empty else 0.0
    best_cost = float(pd.to_numeric(pd.Series([best.get("cost_adjusted_expectancy", math.nan)]), errors="coerce").iloc[0])
    best_rolling = float(pd.to_numeric(pd.Series([best.get("rolling_oos_robustness", 0.0)]), errors="coerce").iloc[0])
    best_capital = float(pd.to_numeric(pd.Series([best.get("capital_utilization", 0.0)]), errors="coerce").iloc[0])
    best_concentration = float(pd.to_numeric(pd.Series([best.get("concentration", math.nan)]), errors="coerce").iloc[0])
    artifact_half_cost = float(
        pd.to_numeric(
            artifact_df.loc[artifact_df["structure_name"].astype(str) == "artifact_half_plus", "cost_adjusted_expectancy"],
            errors="coerce",
        ).fillna(math.nan).iloc[0]
    ) if (artifact_df["structure_name"].astype(str) == "artifact_half_plus").any() else math.nan
    stackable = (
        not top_basket.empty
        and not overlay.empty
        and float(pd.to_numeric(top_basket["cost_adjusted_expectancy"], errors="coerce").iloc[0]) > 0
        and float(pd.to_numeric(overlay["cost_adjusted_expectancy"], errors="coerce").iloc[0]) > 0
        and positive_rolling_share >= 0.75
        and best_cost > 0.40
        and best_capital >= 0.15
        and best_concentration < 0.35
        and not math.isnan(artifact_half_cost)
        and artifact_half_cost > 0.35
    )

    if math.isnan(best_cost) or best_cost <= 0 or best_rolling < 0.50:
        decision = "NO_MONETIZABLE_CONTINUATION_SLEEVE"
        reason = "Top continuation regimes remain positive in theory, but sleeve structures do not hold up after costs or OOS validation."
    elif stackable and best_concentration < 0.40:
        decision = "REGIME_STACKABLE_ALPHA"
        reason = "Multiple regime sleeves remain positive after costs and rolling validation, with enough breadth to stack into repeatable offensive alpha."
    elif best_cost > 0.35 and best_rolling >= 0.75 and positive_rolling_share >= 0.75 and best_capital >= 0.08:
        decision = "OFFENSIVE_REGIME_SLEEVE"
        reason = "Regime basket monetization survives post-cost and rolling OOS checks strongly enough for small offensive tactical capital."
    else:
        decision = "TACTICAL_CONTINUATION_SLEEVE"
        reason = "Continuation alpha can be monetized as a tactical sleeve, but artifact dependence and persistence risk still cap scalability."

    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_structure": best_name,
                "best_monetization_score": best.get("monetization_score", math.nan),
                "best_cost_adjusted_expectancy": best_cost,
                "best_rolling_oos_robustness": best_rolling,
                "best_capital_utilization": best_capital,
                "best_concentration": best_concentration,
                "artifact_adjusted_best_structure": artifact_best.get("structure_name", ""),
                "artifact_adjusted_best_cost_adjusted_expectancy": artifact_best.get("cost_adjusted_expectancy", math.nan),
                "artifact_half_plus_cost_adjusted_expectancy": artifact_half_cost,
                "positive_rolling_window_share": _f(positive_rolling_share),
                "shadow_monitor_ready": bool(utility_df.iloc[0]["shadow_monitor_suitability"]) if not utility_df.empty else False,
            }
        ]
    )


def _report(
    out_dir: Path,
    final_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    basket_df: pd.DataFrame,
    sizing_df: pd.DataFrame,
    artifact_df: pd.DataFrame,
    utility_df: pd.DataFrame,
    oos_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    lines = [
        "# Task 353 - Regime-Dependent Continuation Sleeve Monetization",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_structure: {final_row['best_structure']}",
        f"- best_cost_adjusted_expectancy: {final_row['best_cost_adjusted_expectancy']}",
        f"- best_rolling_oos_robustness: {final_row['best_rolling_oos_robustness']}",
        "",
        "## Final Interpretation",
        "1. The next question is not whether continuation alpha exists, but whether top-ranked regimes can be monetized as an offensive sleeve.",
        f"2. Best monetization structure: `{final_row['best_structure']}`",
        f"3. Final decision: `{final_row['decision']}`",
        f"4. Shadow-monitor ready: `{bool(final_row['shadow_monitor_ready'])}`",
        "",
        "## Selected Regime Candidates",
        *(_markdown_table(selected_df.head(10))),
        "",
        "## Basket Comparison",
        *(_markdown_table(basket_df)),
        "",
        "## Sizing Template Comparison",
        *(_markdown_table(sizing_df)),
        "",
        "## Artifact-Adjusted Sleeve",
        *(_markdown_table(artifact_df)),
        "",
        "## Economic Utility",
        *(_markdown_table(utility_df)),
        "",
        "## OOS Validation",
        *(_markdown_table(oos_df)),
    ]
    (out_dir / "task_353_regime_continuation_sleeve.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 353: monetize regime-dependent continuation alpha as an offensive sleeve")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_continuation_master()
    candidates_df = _candidate_rows(master)
    artifact_map_df = _artifact_vs_structure(master, candidates_df)
    tail_df = _positive_tail_persistence(master, candidates_df)
    ranked_df = _relative_ranking(candidates_df, artifact_map_df, tail_df)
    selected_df = _selected_regimes(ranked_df)
    scorecard_df = _build_participation_scorecard(master, selected_df)
    basket_df, basket_frames = _basket_comparison(master, scorecard_df)
    sizing_df, sizing_frames = _sizing_template_comparison(master, scorecard_df)
    artifact_adjusted_df = _artifact_adjusted_sleeve(master, scorecard_df)

    combined = pd.concat([basket_df, sizing_df], ignore_index=True).sort_values(
        ["monetization_score", "cost_adjusted_expectancy", "rolling_oos_robustness"],
        ascending=[False, False, False],
    )
    best_name = str(combined.iloc[0]["structure_name"]) if not combined.empty else ""
    eligible_days = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique()
    frame_map = {**basket_frames, **sizing_frames}
    best_frame, best_mult = frame_map.get(best_name, (master.iloc[0:0].copy(), None))
    oos_df = _oos_validation(best_name, best_frame, int(eligible_days), best_mult)
    utility_df = _economic_utility(combined.iloc[0], best_name) if not combined.empty else pd.DataFrame()
    final_df = _final_decision(basket_df, sizing_df, artifact_adjusted_df, oos_df, utility_df)

    candidate_out = selected_df[
        [
            "selection_bucket",
            "regime_id",
            "candidate_type",
            "trade_count",
            "cost_adjusted_expectancy",
            "rolling_robustness",
            "structural_share",
            "artifact_dependence",
            "continuation_quality_score",
            "artifact_adjusted_weight",
        ]
    ].copy()
    candidate_out.to_csv(out_dir / "task_353_regime_sleeve_candidates.csv", index=False)
    basket_df.to_csv(out_dir / "task_353_regime_basket_comparison.csv", index=False)
    scorecard_df.to_csv(out_dir / "task_353_regime_participation_scorecard.csv", index=False)
    sizing_df.to_csv(out_dir / "task_353_sizing_template_comparison.csv", index=False)
    oos_df.to_csv(out_dir / "task_353_offensive_sleeve_oos_validation.csv", index=False)
    artifact_adjusted_df.to_csv(out_dir / "task_353_artifact_adjusted_sleeve.csv", index=False)
    utility_df.to_csv(out_dir / "task_353_economic_utility_assessment.csv", index=False)
    final_df.to_csv(out_dir / "task_353_final_decision.csv", index=False)
    _report(out_dir, final_df, candidate_out, basket_df, sizing_df, artifact_adjusted_df, utility_df, oos_df)


if __name__ == "__main__":
    main()
