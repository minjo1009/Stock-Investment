from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import _apply_cost_scaled, _f
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import ROLLING_WINDOWS
from src.backtest.analysis_structural_breakout_alpha_family_viability_350 import (
    _add_universe_environment_labels,
    _metrics,
    _prepare_unified_master,
    _scaled_frame,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_351_continuation_regime_persistence")
PRIMARY_AXES = (
    "volatility_state",
    "liquidity_state",
    "market_breadth_state",
    "broad_participation_state",
    "sector_leadership_state",
    "post_risk_off_state",
    "session_timing_bucket",
    "execution_quality_bucket",
)
INTERACTION_AXES = (
    ("volatility_state", "liquidity_state"),
    ("market_breadth_state", "broad_participation_state"),
    ("sector_leadership_state", "post_risk_off_state"),
    ("session_timing_bucket", "execution_quality_bucket"),
)
ARTIFACT_SCENARIOS = (
    "baseline",
    "remove_software_internet",
    "remove_phase_spikes",
    "remove_isolated_bursts",
    "structural_only",
)


def _safe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _prepare_continuation_master() -> pd.DataFrame:
    master = _prepare_unified_master()
    master = _add_universe_environment_labels(master)
    master["execution_quality_bucket"] = master["execution_quality_bucket"].fillna("unknown")
    master["session_timing_bucket"] = master["session_timing_bucket"].fillna("unknown")
    return master.reset_index(drop=True)


def _positive_tail_ratio(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    positives = values[values > 0]
    if positives.empty:
        return 0.0
    cutoff = float(positives.quantile(0.90))
    top_tail = positives[positives >= cutoff]
    return float(top_tail.sum() / max(float(positives.sum()), 1e-9))


def _top_decile_contribution(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    cutoff = float(values.quantile(0.90))
    top = values[values >= cutoff]
    return float(top.sum() / max(float(values.abs().sum()), 1e-9))


def _positive_skew_proxy(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return math.nan
    upper = float(values.quantile(0.90))
    lower = float(values.quantile(0.10))
    if lower >= 0:
        return _f(upper)
    return _f(upper / max(abs(lower), 1e-9))


def _participation_durability(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    days = pd.to_datetime(df["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna()
    if days.empty:
        return 0.0
    span = max((days.max() - days.min()).days + 1, 1)
    return float(days.nunique() / span)


def _rolling_expectancies(df: pd.DataFrame) -> list[float]:
    values: list[float] = []
    for window in ROLLING_WINDOWS:
        scoped = df[
            (df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        values.append(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()))
    return values


def _rolling_tail_survival(df: pd.DataFrame) -> float:
    positive = 0
    total = 0
    for window in ROLLING_WINDOWS:
        scoped = df[
            (df["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
            & (df["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
        ].copy()
        if scoped.empty:
            continue
        total += 1
        if _positive_tail_ratio(pd.to_numeric(scoped["realized_R"], errors="coerce")) >= 0.5:
            positive += 1
    return float(positive / max(total, 1))


def _rolling_robustness(df: pd.DataFrame) -> float:
    positive = 0
    total = 0
    for value in _rolling_expectancies(df):
        total += 1
        if value > 0:
            positive += 1
    return float(positive / max(total, 1))


def _convex_payoff_score(df: pd.DataFrame) -> float:
    metrics = _metrics(_scaled_frame(df))
    tail_ratio = _positive_tail_ratio(_safe_numeric(df, "realized_R"))
    rolling_share = _rolling_robustness(df)
    durability = _participation_durability(df)
    cost_expectancy = float(pd.to_numeric(pd.Series([metrics["cost_adjusted_expectancy"]]), errors="coerce").iloc[0]) if metrics["trade_count"] else 0.0
    cost_component = max(cost_expectancy, 0.0) / max(abs(cost_expectancy) + 0.25, 1e-9)
    trade_count = int(metrics["trade_count"])
    sparse_penalty = 1.0 if trade_count >= 20 else 0.85 if trade_count >= 10 else 0.65
    score = (0.35 * tail_ratio) + (0.25 * cost_component) + (0.25 * rolling_share) + (0.15 * durability)
    return _f(score * sparse_penalty)


def _candidate_rows(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for axis in PRIMARY_AXES:
        for bucket, scoped in master.groupby(axis, dropna=False):
            rows.append(_candidate_row(scoped, [axis], [str(bucket)]))
    for axis_a, axis_b in INTERACTION_AXES:
        for (bucket_a, bucket_b), scoped in master.groupby([axis_a, axis_b], dropna=False):
            rows.append(_candidate_row(scoped, [axis_a, axis_b], [str(bucket_a), str(bucket_b)]))
    out = pd.DataFrame(rows)
    out = out.sort_values(["convex_payoff_score", "cost_adjusted_expectancy", "trade_count"], ascending=[False, False, False]).reset_index(drop=True)
    return out


def _candidate_row(scoped: pd.DataFrame, axes: list[str], buckets: list[str]) -> dict[str, Any]:
    metrics = _metrics(_scaled_frame(scoped))
    positive_tail = _positive_tail_ratio(_safe_numeric(scoped, "realized_R"))
    rolling_share = _rolling_robustness(scoped)
    durability = _participation_durability(scoped)
    return {
        "regime_id": "|".join(f"{axis}={bucket}" for axis, bucket in zip(axes, buckets)),
        "axes": "|".join(axes),
        "buckets": "|".join(buckets),
        "trade_count": metrics["trade_count"],
        "expectancy": metrics["expectancy"],
        "positive_tail_ratio": _f(positive_tail),
        "convex_payoff_score": _convex_payoff_score(scoped),
        "cost_adjusted_expectancy": metrics["cost_adjusted_expectancy"],
        "rolling_robustness": _f(rolling_share),
        "participation_durability": _f(durability),
    }


def _surviving_regimes(candidates_df: pd.DataFrame) -> pd.DataFrame:
    survivors = candidates_df[
        (pd.to_numeric(candidates_df["cost_adjusted_expectancy"], errors="coerce") > 0)
        & (pd.to_numeric(candidates_df["rolling_robustness"], errors="coerce") >= 0.5)
        & (pd.to_numeric(candidates_df["positive_tail_ratio"], errors="coerce") >= 0.45)
        & (pd.to_numeric(candidates_df["trade_count"], errors="coerce") >= 10)
    ].copy()
    survivors["continuation_persistence"] = survivors["rolling_robustness"]
    survivors["offensive_alpha_score"] = (
        0.6 * pd.to_numeric(survivors["convex_payoff_score"], errors="coerce")
        + 0.4 * pd.to_numeric(survivors["cost_adjusted_expectancy"], errors="coerce").clip(lower=0).fillna(0)
    ).round(6)
    return survivors.sort_values(["offensive_alpha_score", "convex_payoff_score"], ascending=[False, False]).reset_index(drop=True)


def _positive_tail_persistence(master: pd.DataFrame, survivors: pd.DataFrame) -> pd.DataFrame:
    if survivors.empty:
        return pd.DataFrame(
            columns=[
                "regime_id",
                "trade_count",
                "positive_tail_ratio",
                "top_decile_contribution",
                "positive_skew_proxy",
                "rolling_tail_survival",
            ]
        )
    rows: list[dict[str, Any]] = []
    for _, row in survivors.iterrows():
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        returns = _safe_numeric(scoped, "realized_R")
        rows.append(
            {
                "regime_id": row["regime_id"],
                "trade_count": int(len(scoped)),
                "positive_tail_ratio": _f(_positive_tail_ratio(returns)),
                "top_decile_contribution": _f(_top_decile_contribution(returns)),
                "positive_skew_proxy": _positive_skew_proxy(returns),
                "rolling_tail_survival": _f(_rolling_tail_survival(scoped)),
            }
        )
    return pd.DataFrame(rows)


def _filter_candidate(master: pd.DataFrame, axes: list[str], buckets: list[str]) -> pd.DataFrame:
    scoped = master.copy()
    mask = pd.Series(True, index=scoped.index)
    for axis, bucket in zip(axes, buckets):
        mask &= scoped[axis].astype(str).eq(bucket)
    return scoped[mask].copy()


def _artifact_tagged(master: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    out["artifact_software_internet"] = out["sector_group"].astype(str) == "software_internet"
    out["artifact_phase_spike"] = (
        out["sector_leadership_state"].astype(str).eq("tech_led")
        | out["post_risk_off_state"].astype(str).eq("post_risk_off")
        | (
            out["volatility_state"].astype(str).eq("high_vol")
            & out["liquidity_state"].astype(str).eq("liquidity_expanding")
        )
    )
    daily_mean = out.groupby(out["entry_ts"].dt.strftime("%Y-%m-%d"))["realized_R"].transform("mean")
    daily_count = out.groupby(out["entry_ts"].dt.strftime("%Y-%m-%d"))["trade_id"].transform("count")
    spike_threshold = float(pd.to_numeric(daily_mean[out["current_split"] == "train"], errors="coerce").quantile(0.9)) if (out["current_split"] == "train").any() else float(pd.to_numeric(daily_mean, errors="coerce").quantile(0.9))
    count_threshold = float(pd.to_numeric(daily_count[out["current_split"] == "train"], errors="coerce").median()) if (out["current_split"] == "train").any() else float(pd.to_numeric(daily_count, errors="coerce").median())
    out["artifact_isolated_burst"] = (pd.to_numeric(daily_mean, errors="coerce") >= spike_threshold) & (pd.to_numeric(daily_count, errors="coerce") <= count_threshold)
    return out


def _artifact_vs_structure(master: pd.DataFrame, survivors: pd.DataFrame) -> pd.DataFrame:
    if survivors.empty:
        return pd.DataFrame(
            columns=[
                "regime_id",
                "scenario",
                "trade_count",
                "expectancy",
                "positive_tail_ratio",
                "convex_payoff_score",
                "structural_share",
                "temporary_phase_share",
            ]
        )
    tagged = _artifact_tagged(master)
    rows: list[dict[str, Any]] = []
    for _, row in survivors.iterrows():
        scoped = _filter_candidate(tagged, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        baseline_positive = float(_safe_numeric(scoped, "realized_R").clip(lower=0).sum())
        scenario_frames = {
            "baseline": scoped,
            "remove_software_internet": scoped[~scoped["artifact_software_internet"].astype(bool)].copy(),
            "remove_phase_spikes": scoped[~scoped["artifact_phase_spike"].astype(bool)].copy(),
            "remove_isolated_bursts": scoped[~scoped["artifact_isolated_burst"].astype(bool)].copy(),
            "structural_only": scoped[
                ~scoped["artifact_software_internet"].astype(bool)
                & ~scoped["artifact_phase_spike"].astype(bool)
                & ~scoped["artifact_isolated_burst"].astype(bool)
            ].copy(),
        }
        for scenario_name in ARTIFACT_SCENARIOS:
            scenario_df = scenario_frames[scenario_name]
            positive_sum = float(_safe_numeric(scenario_df, "realized_R").clip(lower=0).sum())
            rows.append(
                {
                    "regime_id": row["regime_id"],
                    "scenario": scenario_name,
                    "trade_count": int(len(scenario_df)),
                    "expectancy": _f(float(_safe_numeric(scenario_df, "realized_R").mean())) if not scenario_df.empty else math.nan,
                    "positive_tail_ratio": _f(_positive_tail_ratio(_safe_numeric(scenario_df, "realized_R"))) if not scenario_df.empty else math.nan,
                    "convex_payoff_score": _convex_payoff_score(scenario_df) if not scenario_df.empty else math.nan,
                    "structural_share": _f(positive_sum / max(baseline_positive, 1e-9)) if baseline_positive > 0 else 0.0,
                    "temporary_phase_share": _f(1.0 - (positive_sum / max(baseline_positive, 1e-9))) if baseline_positive > 0 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def _rolling_regime_outputs(master: pd.DataFrame, survivors: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if survivors.empty:
        return (
            pd.DataFrame(
                columns=[
                    "regime_id",
                    "window_id",
                    "trade_count",
                    "expectancy",
                    "positive_tail_ratio",
                    "convex_payoff_score",
                    "status",
                ]
            ),
            pd.DataFrame(
                columns=[
                    "regime_id",
                    "time_slope",
                    "decay_speed",
                    "burst_concentration",
                    "outside_peak_expectancy",
                ]
            ),
        )
    rolling_rows: list[dict[str, Any]] = []
    decay_rows: list[dict[str, Any]] = []
    for _, row in survivors.iterrows():
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        window_expectancies: list[float] = []
        for window in ROLLING_WINDOWS:
            win_df = scoped[
                (scoped["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
                & (scoped["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
            ].copy()
            metrics = _metrics(_scaled_frame(win_df))
            positive_tail = _positive_tail_ratio(_safe_numeric(win_df, "realized_R")) if not win_df.empty else math.nan
            convex_score = _convex_payoff_score(win_df) if not win_df.empty else math.nan
            rolling_rows.append(
                {
                    "regime_id": row["regime_id"],
                    "window_id": window.window_id,
                    "trade_count": int(len(win_df)),
                    "expectancy": metrics["expectancy"],
                    "positive_tail_ratio": _f(positive_tail) if not pd.isna(positive_tail) else math.nan,
                    "convex_payoff_score": convex_score,
                    "status": "positive_convexity" if not pd.isna(convex_score) and convex_score >= 0.5 and not pd.isna(metrics["expectancy"]) and metrics["expectancy"] > 0 else "weak_or_empty",
                }
            )
            if not pd.isna(metrics["expectancy"]):
                window_expectancies.append(float(metrics["expectancy"]))
        peak = max(window_expectancies) if window_expectancies else math.nan
        outside_peak = float(np.mean([v for v in window_expectancies if v != peak])) if len(window_expectancies) > 1 else math.nan
        decay_rows.append(
            {
                "regime_id": row["regime_id"],
                "time_slope": _f(window_expectancies[-1] - window_expectancies[0]) if len(window_expectancies) >= 2 else math.nan,
                "decay_speed": _f(min(window_expectancies) - max(window_expectancies)) if window_expectancies else math.nan,
                "burst_concentration": _f(max(window_expectancies) / max(sum(v for v in window_expectancies if v > 0), 1e-9)) if window_expectancies and any(v > 0 for v in window_expectancies) else math.nan,
                "outside_peak_expectancy": _f(outside_peak) if not pd.isna(outside_peak) else math.nan,
            }
        )
    return pd.DataFrame(rolling_rows), pd.DataFrame(decay_rows)


def _regime_persistence_audit(master: pd.DataFrame, survivors: pd.DataFrame) -> pd.DataFrame:
    if survivors.empty:
        return pd.DataFrame(
            columns=[
                "regime_id",
                "full_period_expectancy",
                "anchored_oos_expectancy",
                "rolling_persistence",
                "regime_transition_survival",
                "cost_adjusted_persistence",
            ]
        )
    rows: list[dict[str, Any]] = []
    for _, row in survivors.iterrows():
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        full_metrics = _metrics(_scaled_frame(scoped))
        anchored = scoped[scoped["current_split"] == "anchored_oos"].copy()
        anchored_metrics = _metrics(_scaled_frame(anchored))
        rows.append(
            {
                "regime_id": row["regime_id"],
                "full_period_expectancy": full_metrics["expectancy"],
                "anchored_oos_expectancy": anchored_metrics["expectancy"],
                "rolling_persistence": _f(_rolling_robustness(scoped)),
                "regime_transition_survival": _f(_rolling_tail_survival(scoped)),
                "cost_adjusted_persistence": full_metrics["cost_adjusted_expectancy"],
            }
        )
    return pd.DataFrame(rows)


def _offensive_viability(master: pd.DataFrame, survivors: pd.DataFrame, artifact_df: pd.DataFrame, decay_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if survivors.empty:
        return (
            pd.DataFrame(
                columns=[
                    "regime_id",
                    "trade_count",
                    "annual_trade_frequency",
                    "cost_adjusted_expectancy",
                    "convex_payoff_score",
                    "rolling_robustness",
                    "artifact_dependence",
                    "economic_viability",
                ]
            ),
            pd.DataFrame(
                columns=[
                    "regime_id",
                    "positive_tail_share",
                    "downside_concentration",
                    "holding_persistence",
                    "regime_durability",
                    "time_slope",
                ]
            ),
        )
    artifact_struct = (
        artifact_df[artifact_df["scenario"] == "structural_only"][["regime_id", "structural_share"]]
        .rename(columns={"structural_share": "artifact_dependence"})
        .copy()
    )
    decay_map = decay_df.set_index("regime_id") if not decay_df.empty else pd.DataFrame().set_index(pd.Index([]))
    rows: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    for _, row in survivors.iterrows():
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        returns = _safe_numeric(scoped, "realized_R")
        structural_share = float(
            pd.to_numeric(
                artifact_struct.loc[artifact_struct["regime_id"].eq(row["regime_id"]), "artifact_dependence"],
                errors="coerce",
            ).iloc[0]
        ) if (artifact_struct["regime_id"] == row["regime_id"]).any() else 0.0
        classification = (
            "deployable_continuation_sleeve"
            if float(row["convex_payoff_score"]) >= 0.65 and structural_share >= 0.5 and float(row["rolling_robustness"]) >= 0.75
            else "offensive_tactical_alpha"
            if float(row["convex_payoff_score"]) >= 0.55 and structural_share >= 0.35
            else "regime_specific_alpha_source"
            if structural_share >= 0.2
            else "tactical_anomaly_only"
        )
        rows.append(
            {
                "regime_id": row["regime_id"],
                "trade_count": int(row["trade_count"]),
                "annual_trade_frequency": _f(float(scoped["entry_ts"].dt.year.value_counts().mean())) if not scoped.empty else 0.0,
                "cost_adjusted_expectancy": row["cost_adjusted_expectancy"],
                "convex_payoff_score": row["convex_payoff_score"],
                "rolling_robustness": row["rolling_robustness"],
                "artifact_dependence": _f(1.0 - structural_share),
                "economic_viability": classification,
            }
        )
        profile_rows.append(
            {
                "regime_id": row["regime_id"],
                "positive_tail_share": _f(_positive_tail_ratio(returns)),
                "downside_concentration": _f(float(returns[returns < 0].abs().sum() / max(returns.abs().sum(), 1e-9))) if not returns.empty else math.nan,
                "holding_persistence": _f(float(_safe_numeric(scoped, "follow_through_5d_pct").mean())) if "follow_through_5d_pct" in scoped.columns else math.nan,
                "regime_durability": row["participation_durability"],
                "time_slope": decay_map.loc[row["regime_id"], "time_slope"] if row["regime_id"] in decay_map.index else math.nan,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(profile_rows)


def _final_decision(viability_df: pd.DataFrame, artifact_df: pd.DataFrame, rolling_df: pd.DataFrame) -> pd.DataFrame:
    if viability_df.empty:
        decision = "NO_CONTINUATION_ALPHA"
        reason = "No convex continuation regime survives cost and rolling persistence thresholds."
        return pd.DataFrame([{"decision": decision, "decision_reason": reason}])
    top = viability_df.sort_values(["convex_payoff_score", "rolling_robustness"], ascending=[False, False]).iloc[0]
    top_artifact = artifact_df[(artifact_df["regime_id"] == top["regime_id"]) & (artifact_df["scenario"] == "structural_only")]
    structural_share = float(pd.to_numeric(top_artifact["structural_share"], errors="coerce").iloc[0]) if not top_artifact.empty else 0.0
    positive_windows = int(
        (
            (rolling_df["regime_id"] == top["regime_id"])
            & (rolling_df["status"].astype(str) == "positive_convexity")
        ).sum()
    )
    if float(pd.to_numeric(pd.Series([top["cost_adjusted_expectancy"]]), errors="coerce").iloc[0]) <= 0 or positive_windows == 0:
        decision = "NO_CONTINUATION_ALPHA"
        reason = "Offensive convexity does not survive costs or rolling windows."
    elif structural_share >= 0.55 and float(top["rolling_robustness"]) >= 0.75 and positive_windows >= 3:
        decision = "PERSISTENT_CONVEX_CONTINUATION_ALPHA"
        reason = "Multiple windows retain offensive convexity after artifact removal."
    elif structural_share >= 0.25 and float(top["rolling_robustness"]) >= 0.5:
        decision = "REGIME_DEPENDENT_CONTINUATION_ALPHA"
        reason = "Continuation alpha survives in identifiable liquidity-volatility regimes, but not universally."
    else:
        decision = "TACTICAL_ANOMALY_ONLY"
        reason = "Continuation survives only as sparse or artifact-dominated anomaly pockets."
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "top_regime_id": str(top["regime_id"]),
                "top_convex_payoff_score": _f(float(top["convex_payoff_score"])),
                "top_structural_share": _f(structural_share),
                "top_rolling_positive_windows": positive_windows,
            }
        ]
    )


def _report(
    out_dir: Path,
    final_df: pd.DataFrame,
    survivors: pd.DataFrame,
    artifact_df: pd.DataFrame,
    viability_df: pd.DataFrame,
    profile_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    top_survivors = survivors.head(5)
    structural_rows = artifact_df[artifact_df["scenario"] == "structural_only"].copy().sort_values(
        ["structural_share", "convex_payoff_score"], ascending=[False, False]
    ).head(5)
    top_profiles = profile_df.head(5)
    lines = [
        "# Task 351 - Continuation Regime Persistence Discovery",
        "",
        f"- decision: {final_row['decision']}",
        f"- top_regime_id: {final_row.get('top_regime_id', '')}",
        f"- top_convex_payoff_score: {final_row.get('top_convex_payoff_score', '')}",
        f"- top_structural_share: {final_row.get('top_structural_share', '')}",
        "",
        "## Final Interpretation",
        f"1. Is continuation alpha still structurally alive anywhere? {'yes' if str(final_row['decision']) in {'REGIME_DEPENDENT_CONTINUATION_ALPHA', 'PERSISTENT_CONVEX_CONTINUATION_ALPHA'} else 'no_clear_evidence'}",
        f"2. Which liquidity-volatility regimes preserve offensive convexity? {', '.join(top_survivors['regime_id'].astype(str).head(3).tolist()) if not top_survivors.empty else 'none'}",
        f"3. Is the surviving edge offensive or merely defensive? {'offensive' if str(final_row['decision']) in {'REGIME_DEPENDENT_CONTINUATION_ALPHA', 'PERSISTENT_CONVEX_CONTINUATION_ALPHA'} else 'mostly defensive or artifact-driven'}",
        f"4. Does continuation persistence survive regime transitions? {'yes, partially' if str(final_row['decision']) in {'REGIME_DEPENDENT_CONTINUATION_ALPHA', 'PERSISTENT_CONVEX_CONTINUATION_ALPHA'} else 'not convincingly'}",
        f"5. Is the edge still scalable enough to matter economically? {'yes, selectively' if not viability_df.empty and viability_df['economic_viability'].astype(str).isin({'offensive_tactical_alpha', 'deployable_continuation_sleeve'}).any() else 'not really'}",
        f"6. Is the surviving alpha structural or temporary phase concentration? {'structural within regimes' if str(final_row['decision']) in {'REGIME_DEPENDENT_CONTINUATION_ALPHA', 'PERSISTENT_CONVEX_CONTINUATION_ALPHA'} else 'temporary phase concentration dominates'}",
        "",
        "## Surviving Regimes",
        *(_markdown_table(top_survivors)),
        "",
        "## Structural Share",
        *(_markdown_table(structural_rows)),
        "",
        "## Tactical Convexity Profile",
        *(_markdown_table(top_profiles)),
    ]
    (out_dir / "task_351_continuation_regime_persistence.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 351: continuation regime persistence discovery")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_continuation_master()
    candidates_df = _candidate_rows(master)
    survivors_df = _surviving_regimes(candidates_df)
    tail_df = _positive_tail_persistence(master, survivors_df)
    artifact_df = _artifact_vs_structure(master, survivors_df)
    rolling_df, decay_df = _rolling_regime_outputs(master, survivors_df)
    persistence_df = _regime_persistence_audit(master, survivors_df)
    viability_df, profile_df = _offensive_viability(master, survivors_df, artifact_df, decay_df)
    final_df = _final_decision(viability_df, artifact_df, rolling_df)

    candidates_df.to_csv(out_dir / "task_351_convex_regime_candidates.csv", index=False)
    survivors_df.to_csv(out_dir / "task_351_continuation_regime_extraction.csv", index=False)
    tail_df.to_csv(out_dir / "task_351_positive_tail_persistence.csv", index=False)
    persistence_df.to_csv(out_dir / "task_351_regime_persistence_audit.csv", index=False)
    artifact_df.to_csv(out_dir / "task_351_artifact_vs_structure.csv", index=False)
    viability_df.to_csv(out_dir / "task_351_offensive_alpha_viability.csv", index=False)
    profile_df.to_csv(out_dir / "task_351_tactical_convexity_profile.csv", index=False)
    rolling_df.to_csv(out_dir / "task_351_rolling_regime_validation.csv", index=False)
    decay_df.to_csv(out_dir / "task_351_time_decay_analysis.csv", index=False)
    final_df.to_csv(out_dir / "task_351_final_decision.csv", index=False)
    _report(out_dir, final_df, survivors_df, artifact_df, viability_df, profile_df)


if __name__ == "__main__":
    main()
