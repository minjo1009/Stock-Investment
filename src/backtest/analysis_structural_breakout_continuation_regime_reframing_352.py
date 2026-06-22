from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import _f
from src.backtest.analysis_structural_breakout_continuation_regime_persistence_351 import (
    _artifact_vs_structure,
    _candidate_rows,
    _filter_candidate,
    _positive_skew_proxy,
    _positive_tail_persistence,
    _prepare_continuation_master,
    _rolling_regime_outputs,
    _rolling_robustness,
    _rolling_tail_survival,
    _top_decile_contribution,
)
from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import _annual_trade_frequency


DEFAULT_OUT_DIR = Path("docs/reports/task_352_continuation_regime_reframing")


def _percentile_rank(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() <= 1:
        return pd.Series(np.where(values.notna(), 1.0, math.nan), index=series.index, dtype=float)
    return values.rank(method="average", pct=True)


def _artifact_structural_map(artifact_df: pd.DataFrame) -> pd.DataFrame:
    if artifact_df.empty:
        return pd.DataFrame(columns=["regime_id", "structural_share", "artifact_dependence"])
    structural = artifact_df[artifact_df["scenario"] == "structural_only"].copy()
    structural = structural[["regime_id", "structural_share"]].drop_duplicates("regime_id")
    structural["artifact_dependence"] = 1.0 - pd.to_numeric(structural["structural_share"], errors="coerce").fillna(0.0)
    return structural


def _relative_ranking(candidates_df: pd.DataFrame, artifact_df: pd.DataFrame, tail_df: pd.DataFrame) -> pd.DataFrame:
    ranked = candidates_df.copy()
    structural_map = _artifact_structural_map(artifact_df)
    tail_map = tail_df[["regime_id", "top_decile_contribution", "positive_skew_proxy", "rolling_tail_survival"]].copy() if not tail_df.empty else pd.DataFrame(columns=["regime_id", "top_decile_contribution", "positive_skew_proxy", "rolling_tail_survival"])
    ranked = ranked.merge(structural_map, on="regime_id", how="left")
    ranked = ranked.merge(tail_map, on="regime_id", how="left")
    ranked["structural_share"] = pd.to_numeric(ranked["structural_share"], errors="coerce").fillna(0.0)
    ranked["artifact_dependence"] = pd.to_numeric(ranked["artifact_dependence"], errors="coerce").fillna(1.0)
    ranked["top_decile_contribution"] = pd.to_numeric(ranked["top_decile_contribution"], errors="coerce").fillna(0.0)
    ranked["positive_skew_proxy"] = pd.to_numeric(ranked["positive_skew_proxy"], errors="coerce")
    ranked["rolling_tail_survival"] = pd.to_numeric(ranked["rolling_tail_survival"], errors="coerce").fillna(0.0)

    ranked["cost_adjusted_expectancy_pct"] = _percentile_rank(ranked["cost_adjusted_expectancy"])
    ranked["positive_tail_ratio_pct"] = _percentile_rank(ranked["positive_tail_ratio"])
    ranked["rolling_robustness_pct"] = _percentile_rank(ranked["rolling_robustness"])
    ranked["rolling_tail_survival_pct"] = _percentile_rank(ranked["rolling_tail_survival"])
    ranked["structural_share_pct"] = _percentile_rank(ranked["structural_share"])
    ranked["participation_durability_pct"] = _percentile_rank(ranked["participation_durability"])
    ranked["top_decile_contribution_pct"] = _percentile_rank(ranked["top_decile_contribution"])

    sparse_penalty = np.where(pd.to_numeric(ranked["trade_count"], errors="coerce") < 10, 0.85, 1.0)
    ranked["continuation_quality_score"] = (
        0.25 * pd.to_numeric(ranked["cost_adjusted_expectancy_pct"], errors="coerce").fillna(0.0)
        + 0.20 * pd.to_numeric(ranked["rolling_robustness_pct"], errors="coerce").fillna(0.0)
        + 0.20 * pd.to_numeric(ranked["structural_share_pct"], errors="coerce").fillna(0.0)
        + 0.15 * pd.to_numeric(ranked["positive_tail_ratio_pct"], errors="coerce").fillna(0.0)
        + 0.10 * pd.to_numeric(ranked["rolling_tail_survival_pct"], errors="coerce").fillna(0.0)
        + 0.10 * pd.to_numeric(ranked["participation_durability_pct"], errors="coerce").fillna(0.0)
    ) * sparse_penalty
    ranked["continuation_quality_score"] = ranked["continuation_quality_score"].round(6)
    ranked["candidate_type"] = np.where(ranked["axes"].astype(str).str.contains(r"\|"), "interaction", "single_axis")
    ranked = ranked.sort_values(
        ["continuation_quality_score", "cost_adjusted_expectancy", "rolling_robustness", "trade_count"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    return ranked


def _top_regime_utility(master: pd.DataFrame, ranked_df: pd.DataFrame) -> pd.DataFrame:
    selected_ids: list[str] = []
    selected_ids.extend(ranked_df.head(5)["regime_id"].astype(str).tolist())
    selected_ids.extend(ranked_df[ranked_df["candidate_type"] == "single_axis"].head(3)["regime_id"].astype(str).tolist())
    selected_ids.extend(ranked_df[ranked_df["candidate_type"] == "interaction"].head(3)["regime_id"].astype(str).tolist())
    selected_ids = list(dict.fromkeys(selected_ids))
    rows: list[dict[str, Any]] = []
    for regime_id in selected_ids:
        row = ranked_df[ranked_df["regime_id"] == regime_id].iloc[0]
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        structural_share = float(pd.to_numeric(pd.Series([row["structural_share"]]), errors="coerce").iloc[0])
        cost_adj = float(pd.to_numeric(pd.Series([row["cost_adjusted_expectancy"]]), errors="coerce").iloc[0])
        rolling = float(pd.to_numeric(pd.Series([row["rolling_robustness"]]), errors="coerce").iloc[0])
        trade_count = int(pd.to_numeric(pd.Series([row["trade_count"]]), errors="coerce").iloc[0])
        tail_strength = (
            "high"
            if float(pd.to_numeric(pd.Series([row["positive_tail_ratio_pct"]]), errors="coerce").iloc[0]) >= 0.8
            and float(pd.to_numeric(pd.Series([row["top_decile_contribution_pct"]]), errors="coerce").iloc[0]) >= 0.8
            else "moderate"
            if float(pd.to_numeric(pd.Series([row["positive_tail_ratio_pct"]]), errors="coerce").iloc[0]) >= 0.5
            else "low"
        )
        economic_usefulness = (
            "high"
            if cost_adj > 0 and rolling >= 0.75 and trade_count >= 20 and structural_share >= 0.35
            else "moderate"
            if cost_adj > 0 and rolling >= 0.5 and trade_count >= 10
            else "low"
        )
        rows.append(
            {
                "selection_bucket": (
                    "top5_overall"
                    if regime_id in ranked_df.head(5)["regime_id"].astype(str).tolist()
                    else "top3_single_axis"
                    if regime_id in ranked_df[ranked_df["candidate_type"] == "single_axis"].head(3)["regime_id"].astype(str).tolist()
                    else "top3_interaction"
                ),
                "regime_id": regime_id,
                "trade_count": trade_count,
                "annual_trade_frequency": _f(_annual_trade_frequency(scoped)),
                "cost_adjusted_expectancy": row["cost_adjusted_expectancy"],
                "rolling_robustness": row["rolling_robustness"],
                "structural_share": _f(structural_share),
                "tail_profile_strength": tail_strength,
                "economic_usefulness": economic_usefulness,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["selection_bucket", "economic_usefulness", "cost_adjusted_expectancy"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def _positive_vs_convex_vs_structural(ranked_df: pd.DataFrame) -> pd.DataFrame:
    out = ranked_df.copy()
    out["positive_drift_continuation"] = (
        (pd.to_numeric(out["cost_adjusted_expectancy"], errors="coerce") > 0)
        & (pd.to_numeric(out["rolling_robustness"], errors="coerce") >= 0.5)
    )
    out["offensive_convex_continuation"] = (
        (pd.to_numeric(out["continuation_quality_score"], errors="coerce") >= float(pd.to_numeric(ranked_df["continuation_quality_score"], errors="coerce").quantile(0.8)))
        & (pd.to_numeric(out["positive_tail_ratio_pct"], errors="coerce") >= 0.6)
        & (pd.to_numeric(out["top_decile_contribution_pct"], errors="coerce") >= 0.6)
    )
    out["structural_continuation"] = (
        (pd.to_numeric(out["structural_share"], errors="coerce") >= 0.35)
        & (pd.to_numeric(out["rolling_tail_survival"], errors="coerce") >= 0.5)
    )
    return out[
        [
            "regime_id",
            "candidate_type",
            "trade_count",
            "cost_adjusted_expectancy",
            "rolling_robustness",
            "positive_tail_ratio",
            "top_decile_contribution",
            "structural_share",
            "continuation_quality_score",
            "positive_drift_continuation",
            "offensive_convex_continuation",
            "structural_continuation",
        ]
    ].copy()


def _artifact_adjusted_scores(master: pd.DataFrame, ranked_df: pd.DataFrame) -> pd.DataFrame:
    selected_ids = ranked_df.head(10)["regime_id"].astype(str).tolist()
    rows: list[dict[str, Any]] = []
    for regime_id in selected_ids:
        row = ranked_df[ranked_df["regime_id"] == regime_id].iloc[0]
        scoped = _filter_candidate(master, str(row["axes"]).split("|"), str(row["buckets"]).split("|"))
        artifact_df = _artifact_vs_structure(master, pd.DataFrame([row]))
        for _, artifact_row in artifact_df.iterrows():
            rows.append(
                {
                    "regime_id": regime_id,
                    "scenario": artifact_row["scenario"],
                    "trade_count": artifact_row["trade_count"],
                    "expectancy": artifact_row["expectancy"],
                    "positive_tail_ratio": artifact_row["positive_tail_ratio"],
                    "convex_payoff_score": artifact_row["convex_payoff_score"],
                    "structural_share": artifact_row["structural_share"],
                    "temporary_phase_share": artifact_row["temporary_phase_share"],
                    "outside_peak_expectancy": _f(float(pd.to_numeric(scoped["realized_R"], errors="coerce").median())) if not scoped.empty else math.nan,
                }
            )
    return pd.DataFrame(rows)


def _rolling_recheck(master: pd.DataFrame, ranked_df: pd.DataFrame) -> pd.DataFrame:
    selected_ids = ranked_df.head(10)["regime_id"].astype(str).tolist()
    selected = ranked_df[ranked_df["regime_id"].astype(str).isin(selected_ids)].copy()
    if selected.empty:
        return pd.DataFrame(columns=["regime_id", "window_id", "trade_count", "expectancy", "positive_tail_ratio", "convex_payoff_score", "status", "continuation_quality_score"])
    rolling_df, _ = _rolling_regime_outputs(master, selected)
    quality_map = selected.set_index("regime_id")["continuation_quality_score"].to_dict()
    rolling_df["continuation_quality_score"] = rolling_df["regime_id"].map(quality_map)
    return rolling_df


def _final_decision(ranked_df: pd.DataFrame, layers_df: pd.DataFrame, utility_df: pd.DataFrame) -> pd.DataFrame:
    positive_exists = bool(layers_df["positive_drift_continuation"].astype(bool).any()) if not layers_df.empty else False
    convex_exists = bool(layers_df["offensive_convex_continuation"].astype(bool).any()) if not layers_df.empty else False
    structural_exists = bool(layers_df["structural_continuation"].astype(bool).any()) if not layers_df.empty else False
    top_useful = utility_df.sort_values(
        ["economic_usefulness", "cost_adjusted_expectancy"],
        ascending=[False, False],
    ).iloc[0] if not utility_df.empty else None

    if not positive_exists:
        decision = "NO_CONTINUATION_ALPHA"
        reason = "Even relative ranking does not reveal durable positive continuation regimes."
    elif convex_exists and structural_exists and top_useful is not None and str(top_useful["economic_usefulness"]) == "high":
        decision = "PERSISTENT_CONVEX_CONTINUATION_ALPHA"
        reason = "Top-ranked regimes retain offensive convexity and structural persistence after artifact adjustment."
    elif positive_exists and (convex_exists or structural_exists):
        decision = "REGIME_DEPENDENT_CONTINUATION_ALPHA"
        reason = "Top-ranked regimes have usable continuation edge, but persistence remains regime-specific rather than broad."
    else:
        decision = "TACTICAL_ANOMALY_ONLY"
        reason = "Positive continuation remains, but mostly as fragile or artifact-heavy anomaly pockets."
    top_regime = ranked_df.iloc[0] if not ranked_df.empty else pd.Series(dtype=object)
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "top_regime_id": top_regime.get("regime_id", ""),
                "top_continuation_quality_score": top_regime.get("continuation_quality_score", math.nan),
                "positive_drift_exists": positive_exists,
                "offensive_convex_exists": convex_exists,
                "structural_continuation_exists": structural_exists,
            }
        ]
    )


def _report(
    out_dir: Path,
    final_df: pd.DataFrame,
    ranked_df: pd.DataFrame,
    utility_df: pd.DataFrame,
    layers_df: pd.DataFrame,
    artifact_scores_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    top_ranked = ranked_df.head(5)
    top_layers = layers_df.head(5)
    structural = artifact_scores_df[artifact_scores_df["scenario"] == "structural_only"].head(5)
    lines = [
        "# Task 352 - Relative Convexity Reframing of Continuation Regimes",
        "",
        f"- decision: {final_row['decision']}",
        f"- top_regime_id: {final_row['top_regime_id']}",
        f"- top_continuation_quality_score: {final_row['top_continuation_quality_score']}",
        "",
        "## Final Interpretation",
        f"1. Positive continuation exists: `{bool(final_row['positive_drift_exists'])}`",
        f"2. Offensive convex continuation exists: `{bool(final_row['offensive_convex_exists'])}`",
        f"3. Structural continuation survives: `{bool(final_row['structural_continuation_exists'])}`",
        f"4. Best regimes are economically useful: `{not utility_df.empty and utility_df['economic_usefulness'].astype(str).isin(['moderate','high']).any()}`",
        f"5. Result classification: `{final_row['decision']}`",
        "",
        "## Top Relative Regimes",
        *(_markdown_table(top_ranked)),
        "",
        "## Top Utility",
        *(_markdown_table(utility_df.head(10))),
        "",
        "## Positive vs Convex vs Structural",
        *(_markdown_table(top_layers)),
        "",
        "## Artifact-Adjusted Structural Scores",
        *(_markdown_table(structural)),
    ]
    (out_dir / "task_352_continuation_regime_reframing.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 352: relative convexity reframing of continuation regimes")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_continuation_master()
    candidates_df = _candidate_rows(master)
    artifact_df = _artifact_vs_structure(master, candidates_df)
    tail_df = _positive_tail_persistence(master, candidates_df)
    ranked_df = _relative_ranking(candidates_df, artifact_df, tail_df)
    utility_df = _top_regime_utility(master, ranked_df)
    layers_df = _positive_vs_convex_vs_structural(ranked_df)
    artifact_scores_df = _artifact_adjusted_scores(master, ranked_df)
    rolling_recheck_df = _rolling_recheck(master, ranked_df)
    final_df = _final_decision(ranked_df, layers_df, utility_df)

    ranked_df.to_csv(out_dir / "task_352_relative_regime_ranking.csv", index=False)
    utility_df.to_csv(out_dir / "task_352_top_regime_utility.csv", index=False)
    layers_df.to_csv(out_dir / "task_352_positive_vs_convex_vs_structural.csv", index=False)
    artifact_scores_df.to_csv(out_dir / "task_352_artifact_adjusted_regime_scores.csv", index=False)
    rolling_recheck_df.to_csv(out_dir / "task_352_rolling_regime_recheck.csv", index=False)
    final_df.to_csv(out_dir / "task_352_final_decision.csv", index=False)
    _report(out_dir, final_df, ranked_df, utility_df, layers_df, artifact_scores_df)


if __name__ == "__main__":
    main()
