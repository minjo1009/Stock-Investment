from __future__ import annotations

import argparse
import math
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PostEntryOverlayConfig,
    StructuralConfig,
    _asset_type,
    _prepare_preloaded_frames,
    _scenario_name,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_best_combo_323plus import (
    DEFAULT_OUT_DIR as TASK323_OUT_DIR,
    RANKED_INPUT,
    _anchored_oos_window,
    _balanced_rank_frame,
    _build_regime_state_lookup,
    _build_universe_state_lookup,
    _cagr_rank_frame,
    _config_from_scenario,
    _load_ranked_input,
    _overlap_groups,
    _recent_six_month_window,
    _select_top_n,
    _sector_bucket,
)
from src.backtest.analysis_structural_breakout_audit_323 import _run_period_reruns, _trade_overlap_matrix


DEFAULT_OUT_DIR = Path("docs/reports/task_324_exit_size_rule_integration")
DUAL_MAP_FRAME = Path(TASK323_OUT_DIR) / "selected_recent_6m_dual_map_trade_frame.csv"


def _slice_timestamps(timestamps: list[pd.Timestamp], start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return [ts for ts in timestamps if start <= ts <= end]


def _load_validation_bands(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        raise FileNotFoundError(f"validation band source missing: {path}")
    df = pd.read_csv(path)
    required = [
        "follow_through_3d_pct",
        "adverse_excursion_3d_pct",
        "follow_through_5d_pct",
        "post_breakout_retrace_5d_pct",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"validation band source missing required columns: {missing}")
    mae3 = pd.to_numeric(df["adverse_excursion_3d_pct"], errors="coerce").abs().dropna()
    return {
        "follow_through_3d_pct": {
            "low": float(pd.to_numeric(df["follow_through_3d_pct"], errors="coerce").quantile(0.35)),
            "high": float(pd.to_numeric(df["follow_through_3d_pct"], errors="coerce").quantile(0.65)),
        },
        "adverse_excursion_3d_pct": {
            "low_abs": float(mae3.quantile(0.35)),
            "high_abs": float(mae3.quantile(0.65)),
        },
        "follow_through_5d_pct": {
            "low": float(pd.to_numeric(df["follow_through_5d_pct"], errors="coerce").quantile(0.35)),
            "high": float(pd.to_numeric(df["follow_through_5d_pct"], errors="coerce").quantile(0.65)),
        },
        "post_breakout_retrace_5d_pct": {
            "low": float(pd.to_numeric(df["post_breakout_retrace_5d_pct"], errors="coerce").quantile(0.35)),
            "high": float(pd.to_numeric(df["post_breakout_retrace_5d_pct"], errors="coerce").quantile(0.65)),
        },
    }


def _select_top10_pool(
    *,
    base_dir: Path,
    ranked_input: Path,
    candidate_pool: int,
    jobs: int,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
) -> list[str]:
    latest_end = max(timestamps)
    anchored_window = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored_window.train_end)
    ranked_input_df = _load_ranked_input(ranked_input)
    balanced_candidates_df = _balanced_rank_frame(ranked_input_df).head(candidate_pool).copy()
    cagr_candidates_df = _cagr_rank_frame(ranked_input_df).head(candidate_pool).copy()
    candidate_df = pd.concat([balanced_candidates_df, cagr_candidates_df], ignore_index=True).drop_duplicates(subset=["scenario"]).reset_index(drop=True)
    candidate_cfgs = [_config_from_scenario(scenario) for scenario in candidate_df["scenario"].tolist()]
    train_results = _run_period_reruns(candidate_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs, frames=frames, timestamps=train_timestamps)
    train_rows = []
    for result in train_results:
        scenario = _scenario_name(StructuralConfig(**result["config"]))
        metrics = result["metrics"]
        train_rows.append(
            {
                "scenario": scenario,
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "label_rank": int(ranked_input_df.loc[ranked_input_df["scenario"] == scenario, "label_rank"].iloc[0]) if scenario in set(ranked_input_df["scenario"]) else 9,
            }
        )
    train_ranked_df = pd.DataFrame(train_rows)
    train_balanced_df = _balanced_rank_frame(train_ranked_df)
    train_cagr_df = _cagr_rank_frame(train_ranked_df)
    train_metrics_by_scenario = {row["scenario"]: row for row in train_rows}
    overlap_df = _trade_overlap_matrix(train_results)
    representative_by_scenario = _overlap_groups(overlap_df, train_metrics_by_scenario)
    combined_ranked = pd.concat([train_balanced_df, train_cagr_df], ignore_index=True).drop_duplicates(subset=["scenario"]).reset_index(drop=True)
    selected = _select_top_n(combined_ranked, representative_by_scenario, top_n=10)
    if len(selected) != 10:
        raise ValueError(f"expected 10 scenarios in Task 324 pool, got {len(selected)}")
    return selected


def _variant_overlay(variant: str, validation_bands: dict[str, dict[str, float]]) -> PostEntryOverlayConfig | None:
    if variant == "baseline":
        return None
    if variant == "exit_only":
        return PostEntryOverlayConfig(post_entry_rule_mode="exit_only", size_reduction_fraction=0.0, validation_bands=validation_bands)
    if variant == "size_only_50":
        return PostEntryOverlayConfig(post_entry_rule_mode="size_only", size_reduction_fraction=0.5, validation_bands=validation_bands)
    if variant == "size_only_30":
        return PostEntryOverlayConfig(post_entry_rule_mode="size_only", size_reduction_fraction=0.3, validation_bands=validation_bands)
    if variant == "exit_plus_size_50":
        return PostEntryOverlayConfig(post_entry_rule_mode="exit_plus_size", size_reduction_fraction=0.5, validation_bands=validation_bands)
    if variant == "exit_plus_size_30":
        return PostEntryOverlayConfig(post_entry_rule_mode="exit_plus_size", size_reduction_fraction=0.3, validation_bands=validation_bands)
    raise ValueError(f"unsupported variant: {variant}")


def _variants() -> list[str]:
    return ["baseline", "exit_only", "size_only_50", "size_only_30", "exit_plus_size_50", "exit_plus_size_30"]


def _run_variant_results(
    scenarios: list[str],
    variants: list[str],
    *,
    base_dir: Path,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
    validation_bands: dict[str, dict[str, float]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    latest_end = max(timestamps)
    anchored_window = _anchored_oos_window(latest_end)
    recent_start, recent_end = _recent_six_month_window(latest_end)
    oos_timestamps = _slice_timestamps(timestamps, anchored_window.test_start, anchored_window.test_end)
    recent_timestamps = _slice_timestamps(timestamps, recent_start, recent_end)
    scope_map = {"full_period": timestamps, "anchored_oos": oos_timestamps, "recent_6m": recent_timestamps}
    results: dict[tuple[str, str, str], dict[str, Any]] = {}
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        for variant in variants:
            overlay = _variant_overlay(variant, validation_bands)
            for scope_name, scope_timestamps in scope_map.items():
                results[(scenario, variant, scope_name)] = run_structural_backtest(
                    cfg,
                    base_dir,
                    preloaded_frames=frames,
                    preloaded_timestamps=scope_timestamps,
                    preloaded_symbols=stocks,
                    overlay=overlay,
                )
    return results


def _trade_subset_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "trade_count": 0,
            "total_r": 0.0,
            "expectancy_r": 0.0,
            "win_rate": 0.0,
            "avg_holding_days": 0.0,
            "avg_loss_r": 0.0,
            "avg_win_r": 0.0,
            "profit_factor": 0.0,
            "worst_month": "",
            "max_losing_streak": 0,
        }
    rs = [float(t["realized_R"]) for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    month_totals: dict[str, float] = {}
    max_losing_streak = 0
    current_losing_streak = 0
    for trade in trades:
        month_key = str(trade.get("exit_date", ""))[:7]
        month_totals[month_key] = month_totals.get(month_key, 0.0) + float(trade["realized_R"])
        if float(trade["realized_R"]) < 0:
            current_losing_streak += 1
            max_losing_streak = max(max_losing_streak, current_losing_streak)
        else:
            current_losing_streak = 0
    return {
        "trade_count": len(rs),
        "total_r": round(float(sum(rs)), 6),
        "expectancy_r": round(float(sum(rs) / len(rs)), 6),
        "win_rate": round(float(len(wins) / len(rs)), 6),
        "avg_holding_days": round(statistics.fmean(float(t.get("holding_days", 0)) for t in trades), 6),
        "avg_loss_r": round(statistics.fmean(losses), 6) if losses else 0.0,
        "avg_win_r": round(statistics.fmean(wins), 6) if wins else 0.0,
        "profit_factor": round(float(sum(wins) / abs(sum(losses))), 6) if losses else (999.0 if wins else 0.0),
        "worst_month": min(month_totals.items(), key=lambda item: item[1])[0] if month_totals else "",
        "max_losing_streak": int(max_losing_streak),
    }


def _enrich_trade_frame(
    scenario: str,
    variant: str,
    scope_name: str,
    result: dict[str, Any],
    regime_state_lookup: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in result["trade_log"]:
        entry_date = str(trade["entry_date"])
        state = regime_state_lookup.get(entry_date, {"regime_state": "risk_off"})
        symbol = str(trade["symbol"])
        rows.append(
            {
                "scenario": scenario,
                "variant": variant,
                "evaluation_scope": scope_name,
                "trade_id": str(trade["trade_id"]),
                "symbol": symbol,
                "symbol_group": "crowded_ai_semis" if symbol in {"AMD", "NVDA", "AVGO", "QCOM", "TSM", "ARM", "SMCI", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "ASML"} else "other",
                "sector_bucket": _sector_bucket(symbol),
                "regime_state": str(state.get("regime_state", "risk_off")),
                "month_bucket": str(trade["exit_date"])[:7],
                "entry_date": entry_date,
                "exit_date": str(trade["exit_date"]),
                "exit_reason": str(trade["exit_reason"]),
                "realized_R": float(trade["realized_R"]),
                "holding_days": int(trade.get("holding_days", 0)),
                "overlay_trigger_rules": str(trade.get("overlay_trigger_rules", "")),
            }
        )
    return pd.DataFrame(rows)


def _aggregate_variant_metrics(scenario_metrics_df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    scoped = scenario_metrics_df[scenario_metrics_df["evaluation_scope"] == scope_name].copy()
    rows: list[dict[str, Any]] = []
    for variant, subset in scoped.groupby("variant"):
        record = {"variant": variant, "evaluation_scope": scope_name, "scenario_count": int(len(subset))}
        for metric in [
            "cagr_pct",
            "sharpe",
            "max_drawdown_pct",
            "total_return_pct",
            "total_r",
            "expectancy_r",
            "win_rate",
            "trade_count",
            "avg_holding_days",
            "avg_loss_r",
            "avg_win_r",
            "profit_factor",
            "max_losing_streak",
        ]:
            record[metric] = round(float(pd.to_numeric(subset[metric], errors="coerce").mean()), 6)
        rows.append(record)
    return pd.DataFrame(rows)


def _delta_vs_baseline(summary_df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    scoped = summary_df[summary_df["evaluation_scope"] == scope_name].copy()
    baseline = scoped[scoped["variant"] == "baseline"].iloc[0]
    rows: list[dict[str, Any]] = []
    for row in scoped.to_dict("records"):
        rows.append(
            {
                **row,
                "oos_return_delta": round(float(row["total_return_pct"]) - float(baseline["total_return_pct"]), 6),
                "mdd_delta": round(float(row["max_drawdown_pct"]) - float(baseline["max_drawdown_pct"]), 6),
                "expectancy_delta": round(float(row["expectancy_r"]) - float(baseline["expectancy_r"]), 6),
                "win_rate_delta": round(float(row["win_rate"]) - float(baseline["win_rate"]), 6),
            }
        )
    return pd.DataFrame(rows)


def _comparison_by_group(trade_df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (variant, scope_name, bucket), subset in trade_df.groupby(["variant", "evaluation_scope", group_col]):
        metrics = _trade_subset_metrics(subset.to_dict("records"))
        rows.append({"variant": variant, "evaluation_scope": scope_name, group_col: bucket, **metrics})
    return pd.DataFrame(rows)


def _build_trade_delta(trade_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scenario, scope_name), scoped in trade_df.groupby(["scenario", "evaluation_scope"]):
        baseline = scoped[scoped["variant"] == "baseline"].set_index("trade_id")
        for variant, variant_df in scoped[scoped["variant"] != "baseline"].groupby("variant"):
            joined = baseline.join(
                variant_df.set_index("trade_id"),
                lsuffix="_baseline",
                rsuffix="_variant",
                how="left",
            )
            for trade_id, row in joined.iterrows():
                rows.append(
                    {
                        "scenario": scenario,
                        "variant": variant,
                        "evaluation_scope": scope_name,
                        "trade_id": trade_id,
                        "symbol": row["symbol_baseline"],
                        "sector": row["sector_bucket_baseline"],
                        "regime": row["regime_state_baseline"],
                        "entry_date": row["entry_date_baseline"],
                        "baseline_exit": row["exit_reason_baseline"],
                        "new_exit": row.get("exit_reason_variant", ""),
                        "baseline_R": row["realized_R_baseline"],
                        "new_R": row.get("realized_R_variant", math.nan),
                        "delta_R": round(float(row.get("realized_R_variant", math.nan)) - float(row["realized_R_baseline"]), 6) if pd.notna(row.get("realized_R_variant")) else math.nan,
                        "rule_trigger": row.get("overlay_trigger_rules_variant", ""),
                    }
                )
    return pd.DataFrame(rows)


def _build_trigger_log(results: dict[tuple[str, str, str], dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scenario, variant, scope_name), result in results.items():
        for record in result["diagnostics"].get("overlay_trigger_log", []):
            rows.append({"scenario": scenario, "variant": variant, "evaluation_scope": scope_name, **record})
    return pd.DataFrame(rows)


def _trigger_analysis(delta_df: pd.DataFrame, trigger_log_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant, subset in delta_df.groupby("variant"):
        triggered_ids = set(trigger_log_df[trigger_log_df["variant"] == variant]["trade_id"].tolist())
        impacted = subset[subset["trade_id"].isin(triggered_ids)].copy()
        if impacted.empty:
            continue
        saved_loss = float(impacted[(impacted["baseline_R"] < 0) & (impacted["delta_R"] > 0)]["delta_R"].sum())
        missed_gain = abs(float(impacted[(impacted["baseline_R"] > 0) & (impacted["delta_R"] < 0)]["delta_R"].sum()))
        rows.append(
            {
                "variant": variant,
                "rule": variant,
                "trigger_count": int(len(impacted)),
                "avg_r_before": round(float(impacted["baseline_R"].mean()), 6),
                "avg_r_after": round(float(impacted["new_R"].mean()), 6),
                "saved_loss": round(saved_loss, 6),
                "missed_gain": round(missed_gain, 6),
            }
        )
    return pd.DataFrame(rows)


def _robustness_check(trade_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dimensions = ["scenario", "sector_bucket", "regime_state", "month_bucket", "symbol_group"]
    for scope_name in sorted(trade_df["evaluation_scope"].unique()):
        scoped = trade_df[trade_df["evaluation_scope"] == scope_name].copy()
        baseline = scoped[scoped["variant"] == "baseline"]
        for variant in sorted(v for v in scoped["variant"].unique() if v != "baseline"):
            variant_df = scoped[scoped["variant"] == variant]
            for dim in dimensions:
                keys = sorted(set(baseline[dim].dropna().tolist()) | set(variant_df[dim].dropna().tolist()))
                for key in keys:
                    base_metrics = _trade_subset_metrics(baseline[baseline[dim] == key].to_dict("records"))
                    var_metrics = _trade_subset_metrics(variant_df[variant_df[dim] == key].to_dict("records"))
                    rows.append(
                        {
                            "variant": variant,
                            "evaluation_scope": scope_name,
                            "dimension": dim,
                            "bucket": key,
                            "baseline_trade_count": base_metrics["trade_count"],
                            "variant_trade_count": var_metrics["trade_count"],
                            "baseline_expectancy_r": base_metrics["expectancy_r"],
                            "variant_expectancy_r": var_metrics["expectancy_r"],
                            "delta_expectancy_r": round(float(var_metrics["expectancy_r"]) - float(base_metrics["expectancy_r"]), 6),
                            "baseline_total_r": base_metrics["total_r"],
                            "variant_total_r": var_metrics["total_r"],
                            "delta_total_r": round(float(var_metrics["total_r"]) - float(base_metrics["total_r"]), 6),
                            "improvement_flag": bool(var_metrics["expectancy_r"] >= base_metrics["expectancy_r"]),
                        }
                    )
    return pd.DataFrame(rows)


def _robustness_level(robustness_df: pd.DataFrame, variant: str) -> str:
    subset = robustness_df[robustness_df["variant"] == variant]
    if subset.empty:
        return "low"
    ratio = float(pd.Series(subset["improvement_flag"]).mean())
    if ratio >= 0.65:
        return "high"
    if ratio >= 0.50:
        return "medium"
    return "low"


def _recommendation(
    variant: str,
    oos_row: pd.Series,
    full_row: pd.Series,
    trigger_row: pd.Series | None,
    robustness_level: str,
    baseline_trade_count: float,
) -> str:
    saved_loss = float(trigger_row["saved_loss"]) if trigger_row is not None and pd.notna(trigger_row["saved_loss"]) else 0.0
    missed_gain = float(trigger_row["missed_gain"]) if trigger_row is not None and pd.notna(trigger_row["missed_gain"]) else 0.0
    full_damage = float(full_row["total_return_pct"]) < float(full_row["baseline_total_return_pct"]) - 3.0 if "baseline_total_return_pct" in full_row else False
    if (
        float(oos_row["expectancy_delta"]) > 0
        and float(oos_row["mdd_delta"]) < 0
        and float(oos_row["trade_count"]) >= 0.75 * float(baseline_trade_count)
        and robustness_level in {"medium", "high"}
        and saved_loss > missed_gain
        and not full_damage
    ):
        return "PROMOTE_TO_NEXT_STAGE"
    if float(oos_row["expectancy_delta"]) > 0 and float(oos_row["mdd_delta"]) < 0 and full_damage:
        return "KEEP_AS_DEFENSIVE_OVERLAY"
    if saved_loss <= missed_gain or robustness_level == "low":
        return "REJECT"
    return "NEEDS_MORE_TESTING"


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    columns = df.columns.tolist()
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for record in df.to_dict("records"):
        values = []
        for column in columns:
            value = record.get(column, "")
            if isinstance(value, float):
                values.append(f"{value:.6f}" if not math.isnan(value) else "")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, sep, *rows])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 324 exit/size rule integration and robustness test")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--ranked-input", type=str, default=str(RANKED_INPUT))
    parser.add_argument("--task323-dual-map", type=str, default=str(DUAL_MAP_FRAME))
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args(argv)

    base_dir = Path(args.data_dir)
    ranked_input = Path(args.ranked_input)
    dual_map_path = Path(args.task323_dual_map)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    validation_bands = _load_validation_bands(dual_map_path)
    stocks = [s for s in sorted(p.stem.upper() for p in base_dir.glob("*.csv")) if _asset_type(s) == "STOCK"]
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    scenarios = _select_top10_pool(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=max(10, int(args.candidate_pool)),
        jobs=max(1, int(args.jobs)),
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
    )
    variants = _variants()
    results = _run_variant_results(
        scenarios,
        variants,
        base_dir=base_dir,
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
        validation_bands=validation_bands,
    )

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_state_lookup = _build_regime_state_lookup(base_dir, universe_state_lookup)

    scenario_rows: list[dict[str, Any]] = []
    trade_frames: list[pd.DataFrame] = []
    for (scenario, variant, scope_name), result in results.items():
        metrics = result["metrics"]
        scenario_rows.append(
            {
                "scenario": scenario,
                "variant": variant,
                "evaluation_scope": scope_name,
                **metrics,
            }
        )
        trade_frames.append(_enrich_trade_frame(scenario, variant, scope_name, result, regime_state_lookup))
    scenario_df = pd.DataFrame(scenario_rows)
    trade_df = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()

    full_summary = _aggregate_variant_metrics(scenario_df, "full_period")
    oos_summary = _aggregate_variant_metrics(scenario_df, "anchored_oos")
    recent_summary = _aggregate_variant_metrics(scenario_df, "recent_6m")
    full_compare = _delta_vs_baseline(full_summary, "full_period")
    oos_compare = _delta_vs_baseline(oos_summary, "anchored_oos")
    recent_compare = _delta_vs_baseline(recent_summary, "recent_6m")

    sector_df = _comparison_by_group(trade_df, "sector_bucket")
    regime_df = _comparison_by_group(trade_df, "regime_state")
    trade_delta_df = _build_trade_delta(trade_df)
    trigger_log_df = _build_trigger_log(results)
    trigger_analysis_df = _trigger_analysis(trade_delta_df[trade_delta_df["evaluation_scope"] == "anchored_oos"], trigger_log_df[trigger_log_df["evaluation_scope"] == "anchored_oos"])
    robustness_df = _robustness_check(trade_df)

    summary_rows: list[dict[str, Any]] = []
    baseline_full = full_summary[full_summary["variant"] == "baseline"].iloc[0]
    baseline_oos = oos_summary[oos_summary["variant"] == "baseline"].iloc[0]
    for variant in variants:
        full_row = full_summary[full_summary["variant"] == variant].iloc[0]
        oos_row = oos_compare[oos_compare["variant"] == variant].iloc[0]
        trigger_row = trigger_analysis_df[trigger_analysis_df["variant"] == variant].iloc[0] if variant in set(trigger_analysis_df["variant"]) else None
        robustness_level = _robustness_level(robustness_df, variant)
        summary_rows.append(
            {
                "variant": variant,
                "full_return_pct": full_row["total_return_pct"],
                "oos_return_pct": oos_row["total_return_pct"],
                "mdd_pct": oos_row["max_drawdown_pct"],
                "sharpe": oos_row["sharpe"],
                "expectancy_r": oos_row["expectancy_r"],
                "trade_count": oos_row["trade_count"],
                "oos_return_delta": oos_row["oos_return_delta"],
                "mdd_delta": oos_row["mdd_delta"],
                "expectancy_delta": oos_row["expectancy_delta"],
                "win_rate_delta": oos_row["win_rate_delta"],
                "saved_loss": trigger_row["saved_loss"] if trigger_row is not None else 0.0,
                "missed_gain": trigger_row["missed_gain"] if trigger_row is not None else 0.0,
                "robustness_level": robustness_level,
                "recommendation": _recommendation(variant, oos_row, pd.Series({**full_row.to_dict(), "baseline_total_return_pct": baseline_full["total_return_pct"]}), trigger_row, robustness_level, float(baseline_oos["trade_count"])),
                "baseline_trade_count": baseline_oos["trade_count"],
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    summary_df.to_csv(out_dir / "task_324_baseline_vs_exit_size_summary.csv", index=False)
    oos_compare.to_csv(out_dir / "task_324_oos_comparison.csv", index=False)
    full_compare.to_csv(out_dir / "task_324_full_period_comparison.csv", index=False)
    scenario_df.to_csv(out_dir / "task_324_scenario_comparison.csv", index=False)
    sector_df.to_csv(out_dir / "task_324_sector_comparison.csv", index=False)
    regime_df.to_csv(out_dir / "task_324_regime_comparison.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_324_trade_level_delta.csv", index=False)
    trigger_log_df.to_csv(out_dir / "task_324_rule_trigger_log.csv", index=False)
    robustness_df.to_csv(out_dir / "task_324_robustness_check.csv", index=False)

    lines = [
        "# Task 324 Exit/Size Rule Integration",
        "",
        "## Executive Summary",
        f"- Scenario pool size: {len(scenarios)}",
        f"- Variants tested: {', '.join(variants)}",
        f"- Primary OOS window: {oos_summary['evaluation_scope'].iloc[0] if not oos_summary.empty else 'anchored_oos'}",
        "",
        "## Baseline vs Variants",
        "| Variant | Full Return | OOS Return | MDD | Sharpe | Expectancy | Trade Count | Recommendation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary_df.to_dict("records"):
        lines.append(
            f"| {row['variant']} | {row['full_return_pct']:.2f} | {row['oos_return_pct']:.2f} | {row['mdd_pct']:.2f} | {row['sharpe']:.3f} | {row['expectancy_r']:.3f} | {row['trade_count']:.1f} | {row['recommendation']} |"
        )
    lines.extend(
        [
            "",
            "## OOS Result",
            "| Variant | OOS Return Delta | MDD Delta | Expectancy Delta | Win Rate Delta |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in oos_compare.to_dict("records"):
        lines.append(
            f"| {row['variant']} | {row['oos_return_delta']:.2f} | {row['mdd_delta']:.2f} | {row['expectancy_delta']:.3f} | {row['win_rate_delta']:.3f} |"
        )
    lines.extend(["", "## Full-period Result", _markdown_table(full_compare), "", "## Rule Trigger Analysis", _markdown_table(trigger_analysis_df) if not trigger_analysis_df.empty else "No overlay triggers.", "", "## Saved Loss vs Missed Gain"])
    for row in summary_df.to_dict("records"):
        lines.append(f"- `{row['variant']}`: saved loss `{row['saved_loss']:.3f}` vs missed gain `{row['missed_gain']:.3f}`")
    lines.extend(["", "## Robustness Review"])
    for variant in variants:
        lines.append(f"- `{variant}` robustness: `{_robustness_level(robustness_df, variant)}`")
    lines.extend(["", "## Final Recommendation"])
    for row in summary_df.to_dict("records"):
        lines.append(f"- `{row['variant']}` -> `{row['recommendation']}`")

    (out_dir / "task_324_exit_size_rule_integration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
