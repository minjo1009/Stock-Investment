from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PostEntryOverlayConfig,
    PreEntryFilterConfig,
    StructuralConfig,
    _load_stock_symbols,
    _prepare_preloaded_frames,
    _safe_quantile_band,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_best_combo_323plus import _anchored_oos_window
from src.backtest.analysis_structural_breakout_exit_size_324 import _load_validation_bands
from src.backtest.analysis_structural_breakout_regime_entry_325 import (
    DUAL_MAP_FRAME,
    RANKED_INPUT,
    _aggregate_variant_rows,
    _build_entry_feature_lookup,
    _build_regime_lookup,
    _build_universe_state_lookup,
    _build_variant_trade_frame,
    _collect_filter_log,
    _config_from_scenario,
    _drawdown_proxy,
    _enrich_trade_frame,
    _regime_rebuild_table,
    _robustness_check,
    _select_top10_pool,
    _slice_timestamps,
    _summary_table,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_326_regime_conditioned_entry_map")
ENTRY_FEATURES = [
    "rs_percentile_20d",
    "sector_breadth",
    "dist_to_sma200_pct",
    "ret_20d_pre",
    "vol_contraction_ratio",
    "breakout_strength_pct",
    "gap_over_planned_entry_pct",
]
RULE_ELIGIBLE_FEATURES = [
    "rs_percentile_20d",
    "sector_breadth",
    "dist_to_sma200_pct",
    "ret_20d_pre",
    "vol_contraction_ratio",
]
ARCHETYPE_NAMES = [
    "low_extension_clean_breakout",
    "high_rs_crowded_breakout",
    "rebound_breakout",
    "high_vol_noise_breakout",
    "late_trend_breakout",
    "other",
]


def _feature_band_edges(df: pd.DataFrame, features: list[str]) -> dict[str, tuple[float, float]]:
    edges: dict[str, tuple[float, float]] = {}
    for feature in features:
        series = pd.to_numeric(df.get(feature), errors="coerce").dropna()
        if series.empty:
            continue
        edges[feature] = (float(series.quantile(0.30)), float(series.quantile(0.70)))
    return edges


def _assign_feature_bands_to_metadata(
    metadata_lookup: dict[str, dict[str, Any]],
    band_edges: dict[str, tuple[float, float]],
) -> dict[str, dict[str, Any]]:
    for metadata in metadata_lookup.values():
        for feature, (low, high) in band_edges.items():
            value = metadata.get(feature, math.nan)
            if pd.isna(value):
                metadata[f"{feature}_band"] = "unknown"
                continue
            metadata[f"{feature}_band"] = _safe_quantile_band(float(value), low, high, lower_is_bad=False)
    return metadata_lookup


def _annotate_trade_frame_bands(
    df: pd.DataFrame,
    band_edges: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    out = df.copy()
    for feature, (low, high) in band_edges.items():
        col = pd.to_numeric(out.get(feature), errors="coerce")
        out[f"{feature}_band"] = col.map(
            lambda value: _safe_quantile_band(float(value), low, high, lower_is_bad=False)
            if pd.notna(value)
            else "unknown"
        )
    return out


def _interaction_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for regime_state in sorted(df["regime_state"].dropna().astype(str).unique()):
        regime_df = df[df["regime_state"] == regime_state].copy()
        for feature in ENTRY_FEATURES:
            band_column = f"{feature}_band"
            if band_column not in regime_df.columns:
                continue
            for band in ("low", "mid", "high"):
                scoped = regime_df[regime_df[band_column] == band].copy()
                if scoped.empty:
                    continue
                rows.append(
                    {
                        "regime_state": regime_state,
                        "feature": feature,
                        "feature_band": band,
                        "trade_count": int(len(scoped)),
                        "expectancy_r": round(float(scoped["realized_R"].mean()), 6),
                        "win_rate": round(float((pd.to_numeric(scoped["realized_R"], errors="coerce") > 0).mean()), 6),
                        "total_r": round(float(scoped["realized_R"].sum()), 6),
                        "average_r": round(float(scoped["realized_R"].mean()), 6),
                        "drawdown_proxy": round(_drawdown_proxy(scoped["realized_R"]), 6),
                        "avg_follow_through_3d_pct": round(float(pd.to_numeric(scoped["follow_through_3d_pct"], errors="coerce").mean()), 6),
                        "avg_follow_through_5d_pct": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").mean()), 6),
                        "avg_retrace_3d_pct": round(float(pd.to_numeric(scoped["post_breakout_retrace_3d_pct"], errors="coerce").mean()), 6),
                        "avg_retrace_5d_pct": round(float(pd.to_numeric(scoped["post_breakout_retrace_5d_pct"], errors="coerce").mean()), 6),
                    }
                )
    return rows


def _assign_archetype(row: pd.Series) -> str:
    ret20_band = str(row.get("ret_20d_pre_band", "unknown"))
    vol_band = str(row.get("vol_contraction_ratio_band", "unknown"))
    rs_band = str(row.get("rs_percentile_20d_band", "unknown"))
    breadth_band = str(row.get("sector_breadth_band", "unknown"))
    dist200_band = str(row.get("dist_to_sma200_pct_band", "unknown"))
    breakout_band = str(row.get("breakout_strength_pct_band", "unknown"))

    if ret20_band == "low" and vol_band == "low" and breakout_band in {"mid", "high"}:
        return "low_extension_clean_breakout"
    if rs_band == "high" and breadth_band == "high":
        return "high_rs_crowded_breakout"
    if ret20_band == "high" and dist200_band in {"low", "mid"}:
        return "rebound_breakout"
    if vol_band == "high" and breakout_band == "high":
        return "high_vol_noise_breakout"
    if ret20_band == "high" and dist200_band == "high":
        return "late_trend_breakout"
    return "other"


def _regime_archetype_map(df: pd.DataFrame) -> pd.DataFrame:
    scoped = df.copy()
    scoped["entry_archetype"] = scoped.apply(_assign_archetype, axis=1)
    grouped = (
        scoped.groupby(["regime_state", "entry_archetype"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
    )
    return grouped.sort_values(["regime_state", "trade_count", "expectancy_r"], ascending=[True, False, False]).reset_index(drop=True)


def _feature_regime_direction(interaction_df: pd.DataFrame, regime_df: pd.DataFrame) -> pd.DataFrame:
    regime_expectancy = regime_df.set_index("regime")["expectancy_r"].to_dict() if not regime_df.empty else {}
    rows: list[dict[str, Any]] = []
    min_count = 5
    for (regime_state, feature), scoped in interaction_df.groupby(["regime_state", "feature"]):
        eligible = scoped[scoped["trade_count"] >= min_count].copy()
        if eligible.empty:
            continue
        eligible = eligible.sort_values(["expectancy_r", "trade_count"], ascending=[False, False]).reset_index(drop=True)
        best = eligible.iloc[0]
        worst = eligible.sort_values(["expectancy_r", "trade_count"], ascending=[True, False]).iloc[0]
        best_band = str(best["feature_band"])
        worst_band = str(worst["feature_band"])
        best_expectancy = float(best["expectancy_r"])
        worst_expectancy = float(worst["expectancy_r"])
        base_expectancy = float(regime_expectancy.get(regime_state, 0.0))
        edge = best_expectancy - worst_expectancy
        if best_band in {"low", "high"} and worst_band in {"low", "high"} and best_band != worst_band:
            direction = f"{best_band} is good"
        elif best_band == "mid":
            direction = "mid preferred"
        else:
            direction = "no clear edge"
        rows.append(
            {
                "feature": feature,
                "regime": regime_state,
                "direction": direction,
                "regime_expectancy_r": round(base_expectancy, 6),
                "best_band": best_band,
                "best_band_expectancy_r": round(best_expectancy, 6),
                "best_band_trade_count": int(best["trade_count"]),
                "worst_band": worst_band,
                "worst_band_expectancy_r": round(worst_expectancy, 6),
                "worst_band_trade_count": int(worst["trade_count"]),
                "expectancy_edge_r": round(edge, 6),
                "best_band_edge_vs_regime_r": round(best_expectancy - base_expectancy, 6),
                "worst_band_edge_vs_regime_r": round(base_expectancy - worst_expectancy, 6),
                "actionable": bool(edge >= 0.15 and int(worst["trade_count"]) >= min_count),
            }
        )
    return pd.DataFrame(rows).sort_values(["regime", "actionable", "expectancy_edge_r"], ascending=[True, False, False]).reset_index(drop=True)


def _extract_regime_conditioned_rules(direction_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for regime_state, scoped in direction_df.groupby("regime"):
        scoped = scoped[scoped["actionable"] & scoped["feature"].isin(RULE_ELIGIBLE_FEATURES)].copy()
        if scoped.empty:
            continue
        negative_candidates = scoped.sort_values(
            ["worst_band_edge_vs_regime_r", "worst_band_trade_count"],
            ascending=[False, False],
        )
        positive_candidates = scoped.sort_values(
            ["best_band_edge_vs_regime_r", "best_band_trade_count"],
            ascending=[False, False],
        )
        regime_expectancy = float(scoped["regime_expectancy_r"].iloc[0])

        added_features: set[str] = set()
        for record in negative_candidates.to_dict("records"):
            feature = str(record["feature"])
            worst_band = str(record["worst_band"])
            if feature in added_features or worst_band not in {"low", "mid", "high"}:
                continue
            rows.append(
                {
                    "rule_id": f"{regime_state}_skip_{feature}_{worst_band}",
                    "regime_state": regime_state,
                    "action": "skip",
                    "size_multiplier": 0.0,
                    "feature": feature,
                    "operator": "band_in",
                    "values": worst_band,
                    "condition_count": 1,
                    "rationale": f"avoid {feature}={worst_band} in {regime_state}",
                    "train_regime_expectancy_r": round(regime_expectancy, 6),
                    "train_band_expectancy_r": round(float(record["worst_band_expectancy_r"]), 6),
                    "train_trade_count": int(record["worst_band_trade_count"]),
                }
            )
            added_features.add(feature)
            if regime_expectancy <= 0.0 and len(added_features) >= 2:
                break
            if regime_expectancy > 0.0:
                break

        if regime_expectancy > 0.0 and not positive_candidates.empty:
            top_positive = positive_candidates.iloc[0]
            feature = str(top_positive["feature"])
            best_band = str(top_positive["best_band"])
            if best_band in {"low", "mid", "high"} and float(top_positive["best_band_edge_vs_regime_r"]) >= 0.20:
                rows.append(
                    {
                        "rule_id": f"{regime_state}_reduce_without_{feature}_{best_band}",
                        "regime_state": regime_state,
                        "action": "reduce",
                        "size_multiplier": 0.5,
                        "feature": feature,
                        "operator": "band_not_in",
                        "values": best_band,
                        "condition_count": 1,
                        "rationale": f"prefer {feature}={best_band} in {regime_state}",
                        "train_regime_expectancy_r": round(regime_expectancy, 6),
                        "train_band_expectancy_r": round(float(top_positive["best_band_expectancy_r"]), 6),
                        "train_trade_count": int(top_positive["best_band_trade_count"]),
                    }
                )
    return pd.DataFrame(rows)


def _rules_for_filter(rule_df: pd.DataFrame) -> tuple[dict[str, Any], ...]:
    rules: list[dict[str, Any]] = []
    for record in rule_df.to_dict("records"):
        rules.append(
            {
                "rule_id": str(record["rule_id"]),
                "regime_state": str(record["regime_state"]),
                "action": str(record["action"]),
                "size_multiplier": float(record["size_multiplier"]),
                "conditions": (
                    {
                        "feature": str(record["feature"]),
                        "operator": str(record["operator"]),
                        "values": (str(record["values"]),),
                    },
                ),
            }
        )
    return tuple(rules)


def _variant_pre_entry_filter(
    variant: str,
    *,
    metadata_lookup: dict[str, dict[str, Any]],
    rule_df: pd.DataFrame,
) -> PreEntryFilterConfig | None:
    if variant == "baseline":
        return None
    return PreEntryFilterConfig(
        regime_conditioned_filter_mode="rules",
        regime_conditioned_rules=_rules_for_filter(rule_df),
        metadata_lookup=metadata_lookup,
    )


def _variant_overlay(variant: str, validation_bands: dict[str, dict[str, float]]) -> PostEntryOverlayConfig | None:
    if variant != "regime_conditioned_entry_filter + size50":
        return None
    return PostEntryOverlayConfig(
        post_entry_rule_mode="size_only",
        size_reduction_fraction=0.5,
        validation_bands=validation_bands,
    )


def _run_variant_results(
    scenarios: list[str],
    variants: list[str],
    *,
    base_dir: Path,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    full_timestamps: list[pd.Timestamp],
    oos_timestamps: list[pd.Timestamp],
    metadata_lookup: dict[str, dict[str, Any]],
    rule_df: pd.DataFrame,
    validation_bands: dict[str, dict[str, float]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    results: dict[tuple[str, str, str], dict[str, Any]] = {}
    scope_map = {"full_period": full_timestamps, "anchored_oos": oos_timestamps}
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        for variant in variants:
            pre_entry = _variant_pre_entry_filter(
                variant,
                metadata_lookup=metadata_lookup,
                rule_df=rule_df,
            )
            overlay = _variant_overlay(variant, validation_bands)
            for scope_name, scoped_timestamps in scope_map.items():
                results[(scenario, variant, scope_name)] = run_structural_backtest(
                    cfg,
                    base_dir,
                    preloaded_frames=frames,
                    preloaded_timestamps=scoped_timestamps,
                    preloaded_symbols=stocks,
                    pre_entry_filter=pre_entry,
                    overlay=overlay,
                )
    return results


def _decision_label(summary_lookup: dict[tuple[str, str], dict[str, Any]], robustness_df: pd.DataFrame, variant: str) -> str:
    base_oos = summary_lookup.get(("baseline", "anchored_oos"), {})
    var_oos = summary_lookup.get((variant, "anchored_oos"), {})
    base_full = summary_lookup.get(("baseline", "full_period"), {})
    var_full = summary_lookup.get((variant, "full_period"), {})
    oos_expectancy_ok = float(var_oos.get("expectancy_r", -999.0)) > float(base_oos.get("expectancy_r", -999.0))
    oos_return_ok = float(var_oos.get("total_return_pct", -999.0)) > float(base_oos.get("total_return_pct", -999.0))
    full_period_ok = float(var_full.get("total_return_pct", -999.0)) >= float(base_full.get("total_return_pct", -999.0)) - 15.0
    trade_count_ok = float(var_oos.get("trade_count", 0.0)) >= float(base_oos.get("trade_count", 0.0)) * 0.60

    scoped_robustness = robustness_df[robustness_df["variant"] == variant].copy()
    regime_row = scoped_robustness[(scoped_robustness["scope"] == "anchored_oos") & (scoped_robustness["dimension"] == "regime")]
    symbol_row = scoped_robustness[(scoped_robustness["scope"] == "anchored_oos") & (scoped_robustness["dimension"] == "symbol_group")]
    regime_ok = not regime_row.empty and float(regime_row.iloc[0]["positive_delta_share"]) >= 0.50 and float(regime_row.iloc[0]["dominant_group_share"]) < 0.60
    symbol_ok = not symbol_row.empty and float(symbol_row.iloc[0]["dominant_group_share"]) < 0.60

    if all((oos_expectancy_ok, oos_return_ok, full_period_ok, trade_count_ok, regime_ok, symbol_ok)):
        return "PROMOTE"
    return "REJECT"


def _write_markdown_report(
    out_dir: Path,
    regime_oos: pd.DataFrame,
    direction_df: pd.DataFrame,
    rules_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    def _fmt(df: pd.DataFrame) -> list[str]:
        if df.empty:
            return ["_No rows_"]
        cols = [str(column) for column in df.columns]
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for record in df.to_dict("records"):
            row = []
            for col in cols:
                value = record.get(col, "")
                if isinstance(value, float):
                    row.append("" if math.isnan(value) else f"{value:.6g}")
                else:
                    row.append(str(value))
            lines.append("| " + " | ".join(row) + " |")
        return lines

    lines = [
        "# Task 326: Regime-Conditioned Entry Map",
        "",
        "## Core Answer",
        "",
        "Entry was treated as conditional on regime, not as a global score problem.",
        "",
        "## OOS Regime Baseline",
        "",
    ]
    lines.extend(_fmt(regime_oos))
    lines.extend([
        "",
        "## Conditional Feature Directions",
        "",
    ])
    cols = [
        "feature",
        "regime",
        "direction",
        "best_band",
        "worst_band",
        "expectancy_edge_r",
        "actionable",
    ]
    lines.extend(_fmt(direction_df[cols] if not direction_df.empty else direction_df))
    lines.extend([
        "",
        "## Extracted Rules",
        "",
    ])
    lines.extend(_fmt(rules_df))
    lines.extend([
        "",
        "## Integrated Summary",
        "",
    ])
    lines.extend(_fmt(summary_df))
    (out_dir / "task_326_regime_conditioned_entry_map.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 326: regime-conditioned entry map for structural breakout.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--ranked-input", default=str(RANKED_INPUT))
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ranked_input = Path(args.ranked_input)

    stocks = _load_stock_symbols(base_dir, StructuralConfig())
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    scenarios = _select_top10_pool(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
    )

    latest_end = max(timestamps)
    anchored = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored.train_end)
    full_timestamps = timestamps
    oos_timestamps = _slice_timestamps(timestamps, anchored.test_start, anchored.test_end)

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_lookup = _build_regime_lookup(base_dir, universe_state_lookup)
    metadata_lookup = _build_entry_feature_lookup(frames, stocks, universe_state_lookup, regime_lookup)

    train_trade_frames: list[pd.DataFrame] = []
    baseline_trade_frames: list[pd.DataFrame] = []
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        train_result = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=train_timestamps,
            preloaded_symbols=stocks,
        )
        full_result = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=full_timestamps,
            preloaded_symbols=stocks,
        )
        oos_result = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=oos_timestamps,
            preloaded_symbols=stocks,
        )
        train_trade_frames.append(_enrich_trade_frame(scenario, train_result, frames, metadata_lookup, "train"))
        baseline_trade_frames.append(_enrich_trade_frame(scenario, full_result, frames, metadata_lookup, "full_period"))
        baseline_trade_frames.append(_enrich_trade_frame(scenario, oos_result, frames, metadata_lookup, "anchored_oos"))

    train_trade_df = pd.concat(train_trade_frames, ignore_index=True) if train_trade_frames else pd.DataFrame()
    baseline_trade_df = pd.concat(baseline_trade_frames, ignore_index=True) if baseline_trade_frames else pd.DataFrame()
    full_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "full_period"].copy()
    oos_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "anchored_oos"].copy()

    band_edges = _feature_band_edges(train_trade_df, ENTRY_FEATURES)
    metadata_lookup = _assign_feature_bands_to_metadata(metadata_lookup, {feature: band_edges[feature] for feature in RULE_ELIGIBLE_FEATURES if feature in band_edges})
    train_trade_df = _annotate_trade_frame_bands(train_trade_df, band_edges)
    full_trade_df = _annotate_trade_frame_bands(full_trade_df, band_edges)
    oos_trade_df = _annotate_trade_frame_bands(oos_trade_df, band_edges)

    interaction_df = pd.DataFrame(_interaction_rows(train_trade_df))
    archetype_df = _regime_archetype_map(train_trade_df)
    regime_oos_df = _regime_rebuild_table(oos_trade_df)
    direction_df = _feature_regime_direction(interaction_df, _regime_rebuild_table(train_trade_df))
    rules_df = _extract_regime_conditioned_rules(direction_df)

    validation_bands = _load_validation_bands(Path(DUAL_MAP_FRAME))
    variants = [
        "baseline",
        "regime_conditioned_entry_filter",
        "regime_conditioned_entry_filter + size50",
    ]
    integrated_results = _run_variant_results(
        scenarios,
        variants,
        base_dir=base_dir,
        stocks=stocks,
        frames=frames,
        full_timestamps=full_timestamps,
        oos_timestamps=oos_timestamps,
        metadata_lookup=metadata_lookup,
        rule_df=rules_df,
        validation_bands=validation_bands,
    )

    summary_raw_df = _aggregate_variant_rows(integrated_results)
    summary_df = _summary_table(summary_raw_df)
    oos_comparison_df = summary_df[summary_df["scope"] == "anchored_oos"].copy()
    full_comparison_df = summary_df[summary_df["scope"] == "full_period"].copy()
    trade_level_delta_df = _collect_filter_log(integrated_results)
    variant_trade_df = _build_variant_trade_frame(integrated_results, frames, metadata_lookup)
    robustness_df = _robustness_check(variant_trade_df)

    summary_lookup = {(str(row["variant"]), str(row["scope"])): row for row in summary_df.to_dict("records")}
    summary_df["decision"] = summary_df["variant"].map(lambda variant: _decision_label(summary_lookup, robustness_df, str(variant)) if str(variant) != "baseline" else "BASELINE")
    oos_comparison_df["decision"] = oos_comparison_df["variant"].map(lambda variant: _decision_label(summary_lookup, robustness_df, str(variant)) if str(variant) != "baseline" else "BASELINE")
    full_comparison_df["decision"] = full_comparison_df["variant"].map(lambda variant: _decision_label(summary_lookup, robustness_df, str(variant)) if str(variant) != "baseline" else "BASELINE")

    interaction_df.to_csv(out_dir / "task_326_regime_feature_interaction.csv", index=False)
    archetype_df.to_csv(out_dir / "task_326_regime_archetype_map.csv", index=False)
    direction_df.to_csv(out_dir / "task_326_feature_regime_direction.csv", index=False)
    rules_df.to_csv(out_dir / "task_326_regime_conditioned_rules.csv", index=False)
    summary_df.to_csv(out_dir / "task_326_summary.csv", index=False)
    oos_comparison_df.to_csv(out_dir / "task_326_oos_comparison.csv", index=False)
    full_comparison_df.to_csv(out_dir / "task_326_full_period_comparison.csv", index=False)
    trade_level_delta_df.to_csv(out_dir / "task_326_trade_level_delta.csv", index=False)
    robustness_df.to_csv(out_dir / "task_326_robustness.csv", index=False)

    _write_markdown_report(out_dir, regime_oos_df, direction_df, rules_df, summary_df)


if __name__ == "__main__":
    main()
