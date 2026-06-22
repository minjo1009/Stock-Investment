from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_alpha_family_viability_350 import (
    _add_universe_environment_labels,
    _prepare_unified_master,
)
from src.backtest.analysis_structural_breakout_shadow_integration_360 import (
    _build_task360_context,
    _shadow_log_from_baseline,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH
from src.backtest.build_source_time_capture_372 import SourceTimeCapture372Artifacts, build_source_time_capture_372


DEFAULT_OUT_DIR = Path("docs/reports/task_374_forward_pure_breakout")
FEATURE_SET_VERSION = "task374-forward-v1"


@dataclass(frozen=True)
class ForwardPureBreakout374Artifacts:
    forward_only_feature_matrix: pd.DataFrame
    prediction_leakage_audit: pd.DataFrame
    prediction_input_completeness: pd.DataFrame
    forward_breakout_rulebook: pd.DataFrame
    forward_pure_breakout_candidates: pd.DataFrame
    prediction_vs_policy_overlap: pd.DataFrame
    forward_breakout_evaluation_panel: pd.DataFrame
    forward_breakout_bucket_audit: pd.DataFrame
    breakout_purity_summary: pd.DataFrame
    task_375_interface_ready: pd.DataFrame


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return float(numeric)


def _clamp01(value: float | None) -> float | None:
    if value is None:
        return None
    return min(max(float(value), 0.0), 1.0)


def _signed_unit(value: Any, cap: float) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    capped = min(max(float(numeric), -abs(cap)), abs(cap))
    return (capped + abs(cap)) / (2.0 * abs(cap))


def _weighted_average(pairs: list[tuple[float | None, float]]) -> float:
    valid = [(float(score), float(weight)) for score, weight in pairs if score is not None and not pd.isna(score)]
    if not valid:
        return 0.0
    weight_sum = sum(weight for _, weight in valid)
    if weight_sum <= 0:
        return 0.0
    return float(sum(score * weight for score, weight in valid) / weight_sum)


def _feature_registry(master: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "feature_name": "breakout_timestamp",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "timing_anchor",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Entry-time anchor timestamp.",
            "prediction_layer_role": "timing_anchor",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "entry_ts",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "timing_anchor",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Prediction cutoff timestamp.",
            "prediction_layer_role": "prediction_cutoff",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "session_timing_bucket",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "timing_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Known at breakout time.",
            "prediction_layer_role": "timing_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "relative_volume_percentile",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "breakout_structure",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Available at breakout/entry.",
            "prediction_layer_role": "breakout_structure",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "price_vs_session_vwap_at_breakout",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "breakout_structure",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Known at breakout bar close.",
            "prediction_layer_role": "breakout_structure",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "vwap_deviation_at_breakout",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "breakout_structure",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Known at breakout bar close.",
            "prediction_layer_role": "breakout_structure",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "vwap_slope_prebreak",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "breakout_structure",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Prebreak structure metric.",
            "prediction_layer_role": "breakout_structure",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "breakout_bar_close_location",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "breakout_structure",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Available on breakout bar.",
            "prediction_layer_role": "breakout_structure",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "market_breadth_state",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "market_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Same-session market context.",
            "prediction_layer_role": "market_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "gap_environment_state",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "market_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Known pre/at-entry.",
            "prediction_layer_role": "market_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "sector_leadership_state",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "market_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Same-session leadership context.",
            "prediction_layer_role": "market_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "same_day_candidate_count",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "crowding_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Computed from same-day candidate pool.",
            "prediction_layer_role": "crowding_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "same_day_sector_candidate_count",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "crowding_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Computed from same-day sector crowding.",
            "prediction_layer_role": "crowding_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "dispersion_20d",
            "source_path": "src/backtest/analysis_structural_breakout_behavior_state_monetization_334.py",
            "source_stage": "market_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Backward-looking market structure.",
            "prediction_layer_role": "market_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "mean_pairwise_corr",
            "source_path": "src/backtest/analysis_structural_breakout_behavior_state_monetization_334.py",
            "source_stage": "market_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Backward-looking correlation regime.",
            "prediction_layer_role": "market_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "semis_concentration_ratio",
            "source_path": "src/backtest/analysis_structural_breakout_behavior_state_monetization_334.py",
            "source_stage": "crowding_context",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": True,
            "reason": "Known from same-day concentration context.",
            "prediction_layer_role": "crowding_context",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "ker",
            "source_path": "src/backtest/entry_gates.py",
            "source_stage": "entry_gate",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": "ker" in master.columns and pd.to_numeric(master.get("ker"), errors="coerce").notna().any(),
            "reason": "Forward-safe only if materially present on the canonical prediction frame.",
            "prediction_layer_role": "entry_gate",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "volume_percentile",
            "source_path": "src/backtest/entry_gates.py",
            "source_stage": "entry_gate",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": "volume_percentile" in master.columns and pd.to_numeric(master.get("volume_percentile"), errors="coerce").notna().any(),
            "reason": "Forward-safe only if materially present on the canonical prediction frame.",
            "prediction_layer_role": "entry_gate",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "daily_bias",
            "source_path": "src/backtest/entry_gates.py",
            "source_stage": "entry_gate",
            "available_by_entry_ts": True,
            "uses_future_bars": False,
            "allowed_for_task_374": "daily_bias" in master.columns and master["daily_bias"].astype(str).str.len().gt(0).any(),
            "reason": "Forward-safe and usable once materialized from canonical pre-entry fields.",
            "prediction_layer_role": "entry_gate",
            "evaluation_layer_role": "",
        },
        {
            "feature_name": "breakout_hold_duration_bars",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_quality",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Requires future bars after breakout.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "post_event_diagnostic",
        },
        {
            "feature_name": "breakout_response",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_quality",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Ambiguous response label that depends on post-break behavior.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "post_event_diagnostic",
        },
        {
            "feature_name": "vwap_response",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_quality",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Ambiguous VWAP hold label can encode post-break persistence.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "post_event_diagnostic",
        },
        {
            "feature_name": "volume_persistence_3bars",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
            "source_stage": "future_quality",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Three-bar persistence requires future bars.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "post_event_diagnostic",
        },
        {
            "feature_name": "return_next_3bars",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Pure future return.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "outcome_label",
        },
        {
            "feature_name": "adverse_excursion_next_3bars",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Future adverse excursion after entry.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "outcome_label",
        },
        {
            "feature_name": "intraday_pullback_depth_3bars",
            "source_path": "src/backtest/analysis_structural_breakout_tactical_sleeve_348.py",
            "source_stage": "future_outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Future pullback depth after breakout.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "outcome_label",
        },
        {
            "feature_name": "persistence_duration_minutes",
            "source_path": "src/backtest/build_source_time_capture_372.py",
            "source_stage": "lifecycle_outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Duration is known only after the trade evolves.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "lifecycle_outcome",
        },
        {
            "feature_name": "PERSISTENCE_CONFIRMED",
            "source_path": "src/backtest/continuation_intraday_events.py",
            "source_stage": "lifecycle_outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Explicit future persistence tag.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "lifecycle_outcome",
        },
        {
            "feature_name": "realized_R",
            "source_path": "src/backtest/build_source_time_capture_372.py",
            "source_stage": "outcome",
            "available_by_entry_ts": False,
            "uses_future_bars": True,
            "allowed_for_task_374": False,
            "reason": "Realized outcome cannot be used in prediction.",
            "prediction_layer_role": "",
            "evaluation_layer_role": "realized_outcome",
        },
    ]
    frame = pd.DataFrame(rows)
    present_flags: list[bool] = []
    for feature_name in frame["feature_name"].astype(str):
        if feature_name not in master.columns:
            present_flags.append(False)
            continue
        series = master[feature_name]
        if series.dtype == object:
            present_flags.append(series.astype(str).str.len().gt(0).any())
        else:
            present_flags.append(pd.to_numeric(series, errors="coerce").notna().any())
    frame["feature_present_on_dataset"] = present_flags
    return frame.sort_values(["allowed_for_task_374", "feature_name"], ascending=[False, True], kind="stable").reset_index(drop=True)


def _derive_daily_bias_from_distance_fields(master: pd.DataFrame) -> pd.Series:
    dist20 = pd.to_numeric(master.get("dist_to_sma20_pct", pd.Series(index=master.index, dtype=float)), errors="coerce")
    dist50 = pd.to_numeric(master.get("dist_to_sma50_pct", pd.Series(index=master.index, dtype=float)), errors="coerce")
    close_over_sma20 = 1.0 + dist20
    close_over_sma50 = 1.0 + dist50
    sma20_over_sma50 = close_over_sma50 / close_over_sma20

    daily_bias = pd.Series(index=master.index, dtype=object)
    valid = close_over_sma20.gt(0) & close_over_sma50.gt(0)
    strong = valid & close_over_sma50.gt(1.0) & sma20_over_sma50.gt(1.0)
    bullish = valid & close_over_sma50.gt(1.0) & ~strong
    bearish = valid & ~close_over_sma50.gt(1.0)

    daily_bias.loc[strong] = "STRONG_BULLISH"
    daily_bias.loc[bullish] = "BULLISH"
    daily_bias.loc[bearish] = "BEARISH"
    return daily_bias


def _materialize_forward_safe_inputs(master: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    if "daily_bias" not in out.columns or out["daily_bias"].isna().all():
        out["daily_bias"] = _derive_daily_bias_from_distance_fields(out)
    if "ker" not in out.columns:
        out["ker"] = np.nan
    if "volume_percentile" not in out.columns:
        out["volume_percentile"] = np.nan
    return out


def _prediction_input_completeness(master: pd.DataFrame, feature_matrix: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    forward_safe = feature_matrix[
        feature_matrix["available_by_entry_ts"].astype(bool) & ~feature_matrix["uses_future_bars"].astype(bool)
    ].copy()
    unavailable = {
        "ker": "Entry-gate formula exists in src/backtest/entry_gates.py but canonical prediction master lacks the rolling close window needed to compute it.",
        "volume_percentile": "Entry-gate formula exists in src/backtest/entry_gates.py but canonical prediction master lacks the rolling volume window needed to compute it.",
        "daily_bias": "Materialized from dist_to_sma20_pct and dist_to_sma50_pct when direct daily SMA columns are absent.",
    }
    derivation = {
        "ker": "unavailable_on_canonical_master",
        "volume_percentile": "unavailable_on_canonical_master",
        "daily_bias": "derived_from_dist_to_sma20_pct_and_dist_to_sma50_pct",
    }
    for row in forward_safe.itertuples(index=False):
        feature_name = str(row.feature_name)
        present = feature_name in master.columns and master[feature_name].notna().any()
        if present:
            status = "materialized"
        elif feature_name in {"ker", "volume_percentile"}:
            status = "forward_safe_but_unavailable"
        else:
            status = "missing"
        rows.append(
            {
                "feature_name": feature_name,
                "source_path": row.source_path,
                "allowed_for_task_374": bool(row.allowed_for_task_374),
                "feature_present_on_dataset": bool(row.feature_present_on_dataset),
                "materialization_status": status,
                "derivation_path": derivation.get(feature_name, "direct_from_canonical_master"),
                "reason": unavailable.get(feature_name, str(row.reason)),
            }
        )
    return pd.DataFrame(rows).sort_values(["materialization_status", "feature_name"], kind="stable").reset_index(drop=True)


def _prepare_prediction_master(master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    master = master_df.copy() if master_df is not None else _add_universe_environment_labels(_prepare_unified_master())
    master["trade_id"] = master["trade_id"].astype(str)
    master["entry_ts"] = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True)
    master["breakout_timestamp"] = pd.to_datetime(master.get("breakout_timestamp"), errors="coerce", utc=True)
    if "day_key" not in master.columns:
        master["day_key"] = master["entry_ts"].dt.strftime("%Y-%m-%d")
    master = _materialize_forward_safe_inputs(master)
    master = master.sort_values(["entry_ts", "trade_id"], kind="stable").drop_duplicates(subset=["trade_id"], keep="first")
    return master.reset_index(drop=True)


def _train_thresholds(master: pd.DataFrame) -> dict[str, float]:
    train = master[master["current_split"].astype(str) == "train"].copy()
    reference = train if not train.empty else master
    thresholds: dict[str, float] = {}
    for column in (
        "same_day_candidate_count",
        "same_day_sector_candidate_count",
        "dispersion_20d",
        "mean_pairwise_corr",
        "semis_concentration_ratio",
    ):
        series = pd.to_numeric(reference.get(column, pd.Series(dtype=float)), errors="coerce")
        thresholds[f"{column}_mid"] = float(series.quantile(0.50)) if series.notna().any() else 0.0
        thresholds[f"{column}_high"] = float(series.quantile(0.75)) if series.notna().any() else 0.0
    return thresholds


def _market_breadth_score(value: Any) -> float | None:
    mapping = {"broad": 1.0, "narrow": 0.2}
    text = _safe_text(value, "unknown")
    return mapping.get(text, 0.5)


def _gap_score(value: Any) -> float | None:
    mapping = {"calm": 0.85, "unstable": 0.2}
    return mapping.get(_safe_text(value, "unknown"), 0.5)


def _leadership_score(value: Any) -> float | None:
    mapping = {"broad_led": 1.0, "broad_risk_on": 0.95, "tech_led": 0.55}
    return mapping.get(_safe_text(value, "unknown"), 0.5)


def _timing_context_score(value: Any) -> float | None:
    mapping = {"mid_session": 0.85, "first_30m": 0.45, "last_hour": 0.30, "preopen": 0.65}
    return mapping.get(_safe_text(value, "unknown"), 0.35)


def _timing_risk_score(value: Any) -> float | None:
    mapping = {"mid_session": 0.20, "first_30m": 0.85, "last_hour": 0.55, "preopen": 0.40}
    return mapping.get(_safe_text(value, "unknown"), 0.80)


def _daily_bias_score(value: Any) -> float | None:
    mapping = {"STRONG_BULLISH": 1.0, "BULLISH": 0.8, "BEARISH": 0.2}
    text = _safe_text(value)
    if not text:
        return None
    return mapping.get(text, 0.5)


def _pressure_from_quantiles(value: Any, mid: float, high: float) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    value_f = float(numeric)
    if high <= mid:
        return 0.2 if value_f <= mid else 1.0
    if value_f <= mid:
        return 0.2
    if value_f <= high:
        return 0.6
    return 1.0


def _build_candidates(master: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    frame = master.copy()

    context_scores: list[float] = []
    risk_scores: list[float] = []
    buckets: list[str] = []

    for _, row in frame.iterrows():
        context = _weighted_average(
            [
                (_clamp01(_safe_float(row.get("relative_volume_percentile"), np.nan)), 0.15),
                (_signed_unit(row.get("price_vs_session_vwap_at_breakout"), 0.05), 0.10),
                (_signed_unit(row.get("vwap_deviation_at_breakout"), 0.05), 0.05),
                (_signed_unit(row.get("vwap_slope_prebreak"), 0.01), 0.05),
                (_clamp01(pd.to_numeric(pd.Series([row.get("breakout_bar_close_location")]), errors="coerce").iloc[0]), 0.10),
                (_market_breadth_score(row.get("market_breadth_state")), 0.15),
                (_gap_score(row.get("gap_environment_state")), 0.10),
                (_leadership_score(row.get("sector_leadership_state")), 0.10),
                (_timing_context_score(row.get("session_timing_bucket")), 0.10),
                (_clamp01(pd.to_numeric(pd.Series([row.get("ker")]), errors="coerce").iloc[0]), 0.05),
                (_clamp01(pd.to_numeric(pd.Series([row.get("volume_percentile")]), errors="coerce").iloc[0]), 0.05),
                (_daily_bias_score(row.get("daily_bias")), 0.05),
            ]
        )

        narrow_tech = int(
            _safe_text(row.get("market_breadth_state")) == "narrow"
            and _safe_text(row.get("sector_leadership_state")) == "tech_led"
        )
        unstable_gap = int(_safe_text(row.get("gap_environment_state")) == "unstable")
        risk = _weighted_average(
            [
                (_timing_risk_score(row.get("session_timing_bucket")), 0.20),
                (_pressure_from_quantiles(row.get("same_day_candidate_count"), thresholds["same_day_candidate_count_mid"], thresholds["same_day_candidate_count_high"]), 0.15),
                (_pressure_from_quantiles(row.get("same_day_sector_candidate_count"), thresholds["same_day_sector_candidate_count_mid"], thresholds["same_day_sector_candidate_count_high"]), 0.10),
                (_pressure_from_quantiles(row.get("dispersion_20d"), thresholds["dispersion_20d_mid"], thresholds["dispersion_20d_high"]), 0.10),
                (_pressure_from_quantiles(row.get("mean_pairwise_corr"), thresholds["mean_pairwise_corr_mid"], thresholds["mean_pairwise_corr_high"]), 0.10),
                (_pressure_from_quantiles(row.get("semis_concentration_ratio"), thresholds["semis_concentration_ratio_mid"], thresholds["semis_concentration_ratio_high"]), 0.15),
                (1.0 if narrow_tech else 0.2, 0.10),
                (0.8 if unstable_gap else 0.2, 0.10),
            ]
        )

        score = min(max((0.60 * context) + (0.40 * (1.0 - risk)), 0.0), 1.0)
        if score < 0.42 or risk >= 0.80:
            bucket = "blocked_candidate"
        elif score < 0.55 or risk >= 0.55:
            bucket = "fragile_candidate"
        elif score >= 0.68 and context >= 0.65 and risk <= 0.40:
            bucket = "high_quality"
        else:
            bucket = "mixed_quality"

        context_scores.append(round(context, 6))
        risk_scores.append(round(risk, 6))
        buckets.append(bucket)

    frame["prediction_cutoff_ts"] = frame["entry_ts"]
    frame["forward_only_flag"] = True
    frame["feature_set_version"] = FEATURE_SET_VERSION
    frame["context_quality_score"] = context_scores
    frame["risk_pressure_score"] = risk_scores
    frame["forward_breakout_score"] = [round(min(max((0.60 * c) + (0.40 * (1.0 - r)), 0.0), 1.0), 6) for c, r in zip(context_scores, risk_scores)]
    frame["forward_breakout_bucket"] = buckets
    frame["forward_high_quality_flag"] = frame["forward_breakout_bucket"].astype(str).eq("high_quality").astype(int)
    frame["forward_weak_flag"] = frame["forward_breakout_bucket"].astype(str).isin({"fragile_candidate", "blocked_candidate"}).astype(int)
    frame["first_30m_flag"] = frame["session_timing_bucket"].astype(str).eq("first_30m").astype(int)
    frame["tech_led_narrow_flag"] = (
        frame["sector_leadership_state"].astype(str).eq("tech_led")
        & frame["market_breadth_state"].astype(str).eq("narrow")
    ).astype(int)

    keep_columns = [
        "trade_id",
        "symbol",
        "entry_ts",
        "prediction_cutoff_ts",
        "current_split",
        "forward_only_flag",
        "feature_set_version",
        "session_timing_bucket",
        "relative_volume_percentile",
        "price_vs_session_vwap_at_breakout",
        "vwap_deviation_at_breakout",
        "vwap_slope_prebreak",
        "breakout_bar_close_location",
        "market_breadth_state",
        "gap_environment_state",
        "sector_leadership_state",
        "same_day_candidate_count",
        "same_day_sector_candidate_count",
        "dispersion_20d",
        "mean_pairwise_corr",
        "semis_concentration_ratio",
        "ker",
        "volume_percentile",
        "daily_bias",
        "context_quality_score",
        "risk_pressure_score",
        "forward_breakout_score",
        "forward_breakout_bucket",
        "forward_high_quality_flag",
        "forward_weak_flag",
        "first_30m_flag",
        "tech_led_narrow_flag",
    ]
    for column in keep_columns:
        if column not in frame.columns:
            frame[column] = np.nan
    return frame[keep_columns].sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _rulebook() -> pd.DataFrame:
    rows = [
        {
            "rule_group": "context_quality_score",
            "component_name": "relative_volume_percentile",
            "weight": 0.15,
            "logic": "Higher relative volume improves forward breakout quality.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "context_quality_score",
            "component_name": "price_vs_session_vwap_at_breakout",
            "weight": 0.10,
            "logic": "Positive VWAP position at breakout improves quality.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "context_quality_score",
            "component_name": "market_breadth_state",
            "weight": 0.15,
            "logic": "Broad breadth is rewarded, narrow breadth penalized.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "context_quality_score",
            "component_name": "gap_environment_state",
            "weight": 0.10,
            "logic": "Calm gap context is rewarded, unstable gap penalized.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "context_quality_score",
            "component_name": "sector_leadership_state",
            "weight": 0.10,
            "logic": "Broad leadership is rewarded over concentrated tech-led regimes.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "risk_pressure_score",
            "component_name": "session_timing_bucket",
            "weight": 0.20,
            "logic": "first_30m and unknown carry the largest timing pressure.",
            "source_path": "src/risk/staged_gate.py",
        },
        {
            "rule_group": "risk_pressure_score",
            "component_name": "same_day_candidate_count",
            "weight": 0.15,
            "logic": "Higher same-day candidate crowding increases pressure.",
            "source_path": "src/backtest/analysis_structural_breakout_alpha_family_viability_350.py",
        },
        {
            "rule_group": "risk_pressure_score",
            "component_name": "semis_concentration_ratio",
            "weight": 0.15,
            "logic": "Higher semis concentration increases crowding pressure.",
            "source_path": "src/backtest/analysis_structural_breakout_behavior_state_monetization_334.py",
        },
        {
            "rule_group": "risk_pressure_score",
            "component_name": "tech_led_narrow_override",
            "weight": 0.10,
            "logic": "Narrow breadth plus tech-led leadership is treated as fragile pressure.",
            "source_path": "src/risk/state_detector.py",
        },
        {
            "rule_group": "bucketing",
            "component_name": "forward_breakout_bucket",
            "weight": np.nan,
            "logic": "blocked if score<0.42 or risk>=0.80; fragile if score<0.55 or risk>=0.55; high_quality if score>=0.68 and context>=0.65 and risk<=0.40; otherwise mixed.",
            "source_path": "src/backtest/build_forward_pure_breakout_374.py",
        },
    ]
    return pd.DataFrame(rows)


def _prepare_policy_inputs(
    prediction_master: pd.DataFrame,
    policy_pool_df: pd.DataFrame | None = None,
    shadow_log_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if policy_pool_df is None:
        _, _, labeled_pool, _ = _build_task360_context()
        policy_pool = labeled_pool.copy()
    else:
        policy_pool = policy_pool_df.copy()
    policy_pool["trade_id"] = policy_pool["trade_id"].astype(str)
    if "day_key" not in policy_pool.columns:
        policy_pool["day_key"] = pd.to_datetime(policy_pool["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    if shadow_log_df is None:
        shadow_log = _shadow_log_from_baseline(policy_pool.copy(), policy_pool.copy())
    else:
        shadow_log = shadow_log_df.copy()
    shadow_log["trade_id"] = shadow_log["trade_id"].astype(str)

    policy_context_cols = ["trade_id", "event_id", "day_key", "endogenous_state", "day_endogenous_state", "current_split"]
    for col in policy_context_cols:
        if col not in policy_pool.columns:
            policy_pool[col] = np.nan
    return policy_pool[policy_context_cols].drop_duplicates(subset=["trade_id"], keep="first").reset_index(drop=True), shadow_log


def _build_policy_overlap(
    candidates: pd.DataFrame,
    policy_context: pd.DataFrame,
    shadow_log: pd.DataFrame,
) -> pd.DataFrame:
    overlap = candidates.merge(policy_context, on=["trade_id", "current_split"], how="left")
    join_cols = [
        "trade_id",
        "state_label",
        "continuation_risk_score",
        "allow_new_entry",
        "allow_add",
        "factor_exposure_violated",
        "violated_factors",
        "staged_gate_stage",
        "staged_add_allowed",
        "participation_quality_label",
        "participation_expansion_score",
        "participation_fragility_score",
        "participation_confidence",
        "healthy_aggressive_policy_label",
        "healthy_aggressive_final_add_allowed",
        "healthy_aggressive_final_size_multiplier",
        "hypothetical_blocked_entry",
        "hypothetical_blocked_add",
        "hypothetical_reduced_entry",
        "hypothetical_reduced_add",
    ]
    for col in join_cols:
        if col not in shadow_log.columns:
            shadow_log[col] = np.nan
    overlap = overlap.merge(
        shadow_log[join_cols].drop_duplicates(subset=["trade_id"], keep="first"),
        on="trade_id",
        how="left",
    )
    overlap["row_state"] = overlap["state_label"].fillna(overlap["endogenous_state"])
    overlap["day_state"] = overlap["day_endogenous_state"]

    def _bool_flag(series: pd.Series) -> pd.Series:
        return series.astype("boolean").fillna(False).astype(bool)

    overlap["policy_block_flag"] = (
        _bool_flag(overlap["hypothetical_blocked_entry"])
        | _bool_flag(overlap["factor_exposure_violated"])
        | ~_bool_flag(overlap["allow_new_entry"])
    ).astype(int)
    overlap["policy_add_block_flag"] = (
        _bool_flag(overlap["hypothetical_blocked_add"])
        | ~_bool_flag(overlap["allow_add"])
        | ~_bool_flag(overlap["staged_add_allowed"])
        | ~_bool_flag(overlap["healthy_aggressive_final_add_allowed"])
    ).astype(int)
    overlap["policy_reduced_flag"] = (
        _bool_flag(overlap["hypothetical_reduced_entry"])
        | _bool_flag(overlap["hypothetical_reduced_add"])
    ).astype(int)
    overlap["good_but_blocked_flag"] = (
        overlap["forward_high_quality_flag"].astype(int).gt(0) & overlap["policy_block_flag"].astype(int).gt(0)
    ).astype(int)
    overlap["good_but_add_blocked_flag"] = (
        overlap["forward_high_quality_flag"].astype(int).gt(0) & overlap["policy_add_block_flag"].astype(int).gt(0)
    ).astype(int)
    overlap["timing_overlap_block_flag"] = (
        overlap["forward_high_quality_flag"].astype(int).gt(0)
        & overlap["first_30m_flag"].astype(int).gt(0)
        & overlap["policy_block_flag"].astype(int).gt(0)
    ).astype(int)
    overlap["tech_led_narrow_overlap_block_flag"] = (
        overlap["forward_high_quality_flag"].astype(int).gt(0)
        & overlap["tech_led_narrow_flag"].astype(int).gt(0)
        & overlap["policy_block_flag"].astype(int).gt(0)
    ).astype(int)
    overlap["healthy_but_suppressed_flag"] = (
        overlap["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION")
        & overlap["healthy_aggressive_policy_label"].astype(str).eq("KEEP_SUPPRESSED")
    ).astype(int)
    overlap["prediction_policy_disagreement_flag"] = (
        overlap["forward_high_quality_flag"].astype(int).gt(0)
        & (
            overlap["policy_block_flag"].astype(int).gt(0)
            | overlap["policy_add_block_flag"].astype(int).gt(0)
            | overlap["policy_reduced_flag"].astype(int).gt(0)
        )
    ).astype(int)
    overlap["policy_proxy_component"] = overlap[
        ["prediction_policy_disagreement_flag", "good_but_blocked_flag", "healthy_but_suppressed_flag"]
    ].max(axis=1)
    return overlap.sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _prepare_lifecycle_panel(
    lifecycle_panel_df: pd.DataFrame | None = None,
    *,
    db_path: str,
    capture_batch_id: str,
    reuse_existing_batch: bool,
) -> pd.DataFrame:
    if lifecycle_panel_df is not None:
        panel = lifecycle_panel_df.copy()
    else:
        artifacts_372: SourceTimeCapture372Artifacts = build_source_time_capture_372(
            db_path=db_path,
            capture_batch_id=capture_batch_id,
            reuse_existing_batch=reuse_existing_batch,
        )
        panel = artifacts_372.lifecycle_backtest_panel.copy()
    if panel.empty:
        return panel
    if "evaluation_scope" in panel.columns:
        panel = panel[panel["evaluation_scope"].astype(str) == "full_period"].copy()
    panel["raw_trade_id"] = panel["raw_trade_id"].astype(str)
    return panel.reset_index(drop=True)


def _build_evaluation_panel(
    candidates: pd.DataFrame,
    overlap: pd.DataFrame,
    lifecycle_panel: pd.DataFrame,
    master: pd.DataFrame,
) -> pd.DataFrame:
    master_join = master[["trade_id", "current_split", "realized_R"]].drop_duplicates(subset=["trade_id"], keep="first").copy()
    master_join["trade_id"] = master_join["trade_id"].astype(str)
    panel = candidates.merge(master_join, on=["trade_id", "current_split"], how="left", suffixes=("", "_master"))
    if not lifecycle_panel.empty:
        join_cols = [
            "raw_trade_id",
            "event_count",
            "persistence_depth",
            "add_depth",
            "scale_depth",
            "source_linked_flag",
            "fragile_transition_flag",
            "invalidated_flag",
            "add_confirmed_flag",
            "scale_up_flag",
            "persistence_confirmed_flag",
            "lineage_quality",
            "persistence_duration_minutes",
        ]
        for col in join_cols:
            if col not in lifecycle_panel.columns:
                lifecycle_panel[col] = np.nan
        panel = panel.merge(
            lifecycle_panel[join_cols].rename(columns={"raw_trade_id": "trade_id"}),
            on="trade_id",
            how="left",
        )
    else:
        for col in (
            "event_count",
            "persistence_depth",
            "add_depth",
            "scale_depth",
            "source_linked_flag",
            "fragile_transition_flag",
            "invalidated_flag",
            "add_confirmed_flag",
            "scale_up_flag",
            "persistence_confirmed_flag",
            "lineage_quality",
            "persistence_duration_minutes",
        ):
            panel[col] = np.nan
    panel = panel.merge(
        overlap[
            [
                "trade_id",
                "policy_block_flag",
                "policy_add_block_flag",
                "policy_reduced_flag",
                "prediction_policy_disagreement_flag",
            ]
        ],
        on="trade_id",
        how="left",
    )
    rank_base = panel.drop_duplicates(subset=["trade_id"], keep="first").copy()
    rank_base["forward_rank_pct"] = rank_base.groupby("current_split", dropna=False)["forward_breakout_score"].rank(method="average", pct=True)
    rank_base["top_ranked_flag"] = rank_base["forward_rank_pct"].fillna(0.0).ge(0.90).astype(int)
    rank_base["bottom_ranked_flag"] = rank_base["forward_rank_pct"].fillna(0.0).le(0.10).astype(int)
    panel = panel.drop(columns=["top_ranked_flag", "bottom_ranked_flag"], errors="ignore").merge(
        rank_base[["trade_id", "forward_rank_pct", "top_ranked_flag", "bottom_ranked_flag"]],
        on="trade_id",
        how="left",
    )
    panel["legacy_all_flag"] = 1
    return panel.sort_values(["entry_ts", "trade_id"], kind="stable").reset_index(drop=True)


def _bucket_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    bucket_order = ["high_quality", "mixed_quality", "fragile_candidate", "blocked_candidate"]
    for scope_name, scope_df in {
        "full_period": panel.drop_duplicates(subset=["trade_id"], keep="first"),
        "anchored_oos": panel[panel["current_split"].astype(str) == "anchored_oos"].drop_duplicates(subset=["trade_id"], keep="first"),
    }.items():
        if scope_df.empty:
            continue
        grouped = (
            scope_df.groupby("forward_breakout_bucket", dropna=False)
            .agg(
                trade_count=("trade_id", "count"),
                expectancy_realized_R=("realized_R", lambda s: float(pd.to_numeric(s, errors="coerce").mean())),
                min_score=("forward_breakout_score", "min"),
                max_score=("forward_breakout_score", "max"),
                min_risk=("risk_pressure_score", "min"),
                max_risk=("risk_pressure_score", "max"),
            )
            .reset_index()
        )
        grouped = (
            grouped.set_index("forward_breakout_bucket")
            .reindex(bucket_order)
            .reset_index()
        )
        grouped["trade_count"] = pd.to_numeric(grouped["trade_count"], errors="coerce").fillna(0).astype(int)
        for metric_col in ("expectancy_realized_R", "min_score", "max_score", "min_risk", "max_risk"):
            grouped[metric_col] = pd.to_numeric(grouped[metric_col], errors="coerce")
        for row in grouped.itertuples(index=False):
            note = ""
            trade_count = int(row.trade_count) if pd.notna(row.trade_count) else 0
            if str(row.forward_breakout_bucket) == "blocked_candidate" and trade_count == 0:
                note = "structurally_empty_bucket"
            rows.append(
                {
                    "evaluation_scope": scope_name,
                    "forward_breakout_bucket": str(row.forward_breakout_bucket),
                    "trade_count": trade_count,
                    "expectancy_realized_R": round(float(row.expectancy_realized_R), 6) if pd.notna(row.expectancy_realized_R) else 0.0,
                    "min_score": round(float(row.min_score), 6) if pd.notna(row.min_score) else 0.0,
                    "max_score": round(float(row.max_score), 6) if pd.notna(row.max_score) else 0.0,
                    "min_risk": round(float(row.min_risk), 6) if pd.notna(row.min_risk) else 0.0,
                    "max_risk": round(float(row.max_risk), 6) if pd.notna(row.max_risk) else 0.0,
                    "audit_note": note,
                    "gate_status": "",
                    "gate_reason": "",
                    "hard_gate_reactivation_threshold": "",
                }
            )
        ordered = grouped.set_index("forward_breakout_bucket")["expectancy_realized_R"].to_dict()
        monotonic_ok = (
            ordered.get("high_quality", float("-inf")) >= ordered.get("mixed_quality", float("-inf"))
            and ordered.get("mixed_quality", float("-inf")) >= ordered.get("fragile_candidate", float("-inf"))
        )
        trade_count_by_bucket = {str(k): int(v) for k, v in grouped.set_index("forward_breakout_bucket")["trade_count"].to_dict().items()}
        gate_status = "hard_gate"
        gate_reason = "sufficient_bucket_counts"
        total_bucketed = int(len(scope_df))
        if (
            trade_count_by_bucket.get("high_quality", 0) < 30
            or trade_count_by_bucket.get("mixed_quality", 0) < 30
            or trade_count_by_bucket.get("fragile_candidate", 0) < 30
            or total_bucketed < 120
        ):
            gate_status = "diagnostic_only"
            gate_reason = "insufficient_bucket_counts"
        rows.append(
            {
                "evaluation_scope": scope_name,
                "forward_breakout_bucket": "meta_monotonicity_check",
                "trade_count": int(len(scope_df)),
                "expectancy_realized_R": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "min_risk": 0.0,
                "max_risk": 0.0,
                "audit_note": "monotonic_ok" if monotonic_ok else "monotonicity_failure",
                "gate_status": gate_status,
                "gate_reason": gate_reason,
                "hard_gate_reactivation_threshold": "min_30_per_bucket_and_min_120_total_bucketed",
            }
        )
    return pd.DataFrame(rows)


def _summary_rows(panel: pd.DataFrame, overlap: pd.DataFrame, feature_matrix: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scoped_frames = [panel.assign(evaluation_scope="full_period")]
    anchored = panel[panel["current_split"].astype(str) == "anchored_oos"].copy()
    if not anchored.empty:
        scoped_frames.append(anchored.assign(evaluation_scope="anchored_oos"))
    scoped = pd.concat(scoped_frames, ignore_index=True)

    masks = {
        "legacy_all_breakouts": scoped["legacy_all_flag"].astype(int) > 0,
        "forward_high_quality": scoped["forward_breakout_bucket"].astype(str) == "high_quality",
        "forward_mixed_quality": scoped["forward_breakout_bucket"].astype(str) == "mixed_quality",
        "forward_fragile_candidate": scoped["forward_breakout_bucket"].astype(str) == "fragile_candidate",
        "forward_blocked_candidate": scoped["forward_breakout_bucket"].astype(str) == "blocked_candidate",
        "top_ranked_forward": scoped["top_ranked_flag"].astype(int) > 0,
        "bottom_ranked_forward": scoped["bottom_ranked_flag"].astype(int) > 0,
    }

    for scope, scope_df in scoped.groupby("evaluation_scope", dropna=False, sort=False):
        for cut_name, mask in masks.items():
            cut_df = scope_df.loc[mask.loc[scope_df.index]].copy()
            realized = pd.to_numeric(cut_df["realized_R"], errors="coerce")
            rows.append(
                {
                    "evaluation_scope": _safe_text(scope),
                    "evaluation_cut": cut_name,
                    "lifecycle_count": int(len(cut_df)),
                    "expectancy_realized_R": round(float(realized.mean()), 6) if not cut_df.empty else 0.0,
                    "total_realized_R": round(float(realized.sum()), 6) if not cut_df.empty else 0.0,
                    "win_rate": round(float((realized > 0).mean()), 6) if not cut_df.empty else 0.0,
                    "invalidation_share": round(float(pd.to_numeric(cut_df["invalidated_flag"], errors="coerce").fillna(0.0).gt(0).mean()), 6) if not cut_df.empty else 0.0,
                    "persistence_share": round(float(pd.to_numeric(cut_df["persistence_confirmed_flag"], errors="coerce").fillna(0.0).gt(0).mean()), 6) if not cut_df.empty else 0.0,
                    "add_confirm_share": round(float(pd.to_numeric(cut_df["add_confirmed_flag"], errors="coerce").fillna(0.0).gt(0).mean()), 6) if not cut_df.empty else 0.0,
                    "scale_up_share": round(float(pd.to_numeric(cut_df["scale_up_flag"], errors="coerce").fillna(0.0).gt(0).mean()), 6) if not cut_df.empty else 0.0,
                }
            )

    leakage_count = int(feature_matrix["allowed_for_task_374"].astype(bool).eq(False).sum())
    ambiguous_count = int(feature_matrix["feature_name"].astype(str).isin({"vwap_response", "breakout_response", "volume_persistence_3bars"}).sum())

    rows.extend(
        [
            {
                "evaluation_scope": "meta",
                "evaluation_cut": "feature_registry",
                "lifecycle_count": int(len(feature_matrix)),
                "expectancy_realized_R": float(leakage_count),
                "total_realized_R": float(ambiguous_count),
                "win_rate": round(float(feature_matrix["allowed_for_task_374"].astype(bool).mean()), 6),
                "invalidation_share": 0.0,
                "persistence_share": 0.0,
                "add_confirm_share": 0.0,
                "scale_up_share": 0.0,
            }
        ]
    )

    if not overlap.empty:
        anchored_overlap = overlap[overlap["current_split"].astype(str) == "anchored_oos"].copy()
        negatives = anchored_overlap.merge(
            panel[["trade_id", "realized_R"]].drop_duplicates("trade_id"),
            on="trade_id",
            how="left",
        )
        negatives = negatives[pd.to_numeric(negatives["realized_R"], errors="coerce").lt(0)].copy()
        selection_proxy = float(negatives["forward_weak_flag"].fillna(0).mean()) if not negatives.empty else 0.0
        policy_disagreement_proxy = float(negatives["prediction_policy_disagreement_flag"].fillna(0).mean()) if not negatives.empty else 0.0
        high_quality_blocked = float(overlap["good_but_blocked_flag"].mean())
        healthy_suppressed = float(overlap["healthy_but_suppressed_flag"].mean())
        policy_proxy = max(policy_disagreement_proxy, high_quality_blocked, healthy_suppressed)
        proxy_gap = policy_proxy - selection_proxy
        if max(selection_proxy, policy_proxy) < 0.05:
            degradation_class = "indeterminate_low_signal"
        elif policy_proxy >= 0.10 and policy_proxy >= selection_proxy + 0.05:
            degradation_class = "policy_contamination"
        elif selection_proxy >= 0.10 and selection_proxy >= policy_proxy + 0.05:
            degradation_class = "selection_failure"
        else:
            degradation_class = "mixed"
        rows.extend(
            [
                {
                    "evaluation_scope": "anchored_oos",
                    "evaluation_cut": "policy_overlap_meta",
                    "lifecycle_count": int(len(anchored_overlap)),
                    "expectancy_realized_R": round(high_quality_blocked, 6),
                    "total_realized_R": round(float(overlap["good_but_add_blocked_flag"].mean()), 6),
                    "win_rate": round(float(overlap["timing_overlap_block_flag"].mean()), 6),
                    "invalidation_share": round(float(overlap["tech_led_narrow_overlap_block_flag"].mean()), 6),
                    "persistence_share": round(healthy_suppressed, 6),
                    "add_confirm_share": round(selection_proxy, 6),
                    "scale_up_share": round(policy_disagreement_proxy, 6),
                },
                {
                    "evaluation_scope": "anchored_oos",
                    "evaluation_cut": "degradation_classification",
                    "lifecycle_count": int(len(anchored_overlap)),
                    "expectancy_realized_R": round(selection_proxy, 6),
                    "total_realized_R": round(policy_proxy, 6),
                    "win_rate": round(proxy_gap, 6),
                    "invalidation_share": 0.0,
                    "persistence_share": 0.0,
                    "add_confirm_share": 0.0,
                    "scale_up_share": 0.0,
                    "degradation_class": degradation_class,
                }
            ]
        )

    return pd.DataFrame(rows)


def _task_375_interface_ready() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "interface_name": "task_375_forward_persistence_base",
                "prediction_cutoff_rule": "prediction_features_must_be_available_by_entry_ts",
                "suggested_post_entry_window": "first_3_bars_default_plan_only_not_yet_used_in_task_374",
                "target_source": "task_372_lifecycle_backtest_panel_full_period",
                "positive_target_draft": "persistence_confirmed_flag_or_add_confirmed_flag_or_scale_up_flag",
                "prediction_frame_boundary": "forward_pure_breakout_candidates_only_no_outcomes",
                "evaluation_frame_boundary": "task_372_lifecycle_panel_outcomes_only",
            }
        ]
    )


def build_forward_pure_breakout_374(
    *,
    db_path: str = str(DB_PATH),
    capture_batch_id: str = "task374_default",
    reuse_existing_batch: bool = False,
    master_df: pd.DataFrame | None = None,
    policy_pool_df: pd.DataFrame | None = None,
    shadow_log_df: pd.DataFrame | None = None,
    lifecycle_panel_df: pd.DataFrame | None = None,
) -> ForwardPureBreakout374Artifacts:
    master = _prepare_prediction_master(master_df)
    feature_matrix = _feature_registry(master)
    input_completeness = _prediction_input_completeness(master, feature_matrix)
    leakage_audit = feature_matrix[
        ~feature_matrix["allowed_for_task_374"].astype(bool)
        | feature_matrix["uses_future_bars"].astype(bool)
    ].copy().reset_index(drop=True)
    thresholds = _train_thresholds(master)
    candidates = _build_candidates(master, thresholds)
    rulebook = _rulebook()

    policy_context, shadow_log = _prepare_policy_inputs(master, policy_pool_df, shadow_log_df)
    overlap = _build_policy_overlap(candidates, policy_context, shadow_log)

    lifecycle_panel = _prepare_lifecycle_panel(
        lifecycle_panel_df,
        db_path=db_path,
        capture_batch_id=capture_batch_id,
        reuse_existing_batch=reuse_existing_batch,
    )
    evaluation_panel = _build_evaluation_panel(candidates, overlap, lifecycle_panel, master)
    bucket_audit = _bucket_audit(evaluation_panel)
    summary = _summary_rows(evaluation_panel, overlap, feature_matrix)
    task_375_interface_ready = _task_375_interface_ready()

    return ForwardPureBreakout374Artifacts(
        forward_only_feature_matrix=feature_matrix,
        prediction_leakage_audit=leakage_audit,
        prediction_input_completeness=input_completeness,
        forward_breakout_rulebook=rulebook,
        forward_pure_breakout_candidates=candidates,
        prediction_vs_policy_overlap=overlap,
        forward_breakout_evaluation_panel=evaluation_panel,
        forward_breakout_bucket_audit=bucket_audit,
        breakout_purity_summary=summary,
        task_375_interface_ready=task_375_interface_ready,
    )


def write_forward_pure_breakout_374(
    artifacts: ForwardPureBreakout374Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.forward_only_feature_matrix.to_csv(out_dir / "forward_only_feature_matrix.csv", index=False, encoding="utf-8-sig")
    artifacts.prediction_leakage_audit.to_csv(out_dir / "prediction_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.prediction_input_completeness.to_csv(out_dir / "prediction_input_completeness.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_breakout_rulebook.to_csv(out_dir / "forward_breakout_rulebook.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_pure_breakout_candidates.to_csv(out_dir / "forward_pure_breakout_candidates.csv", index=False, encoding="utf-8-sig")
    artifacts.prediction_vs_policy_overlap.to_csv(out_dir / "prediction_vs_policy_overlap.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_breakout_evaluation_panel.to_csv(out_dir / "forward_breakout_evaluation_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_breakout_bucket_audit.to_csv(out_dir / "forward_breakout_bucket_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.breakout_purity_summary.to_csv(out_dir / "breakout_purity_summary.csv", index=False, encoding="utf-8-sig")
    artifacts.task_375_interface_ready.to_csv(out_dir / "task_375_interface_ready.csv", index=False, encoding="utf-8-sig")
