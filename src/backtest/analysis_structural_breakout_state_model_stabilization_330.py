from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import ENTRY_FEATURES, PATH_TYPES
from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    DEFAULT_BASE_DIR,
    RANKED_INPUT,
    _distribution,
    _labeled_trade_frames,
    _series_entropy,
    _total_variation_distance,
)
from src.backtest.analysis_structural_breakout_state_model_redesign_329 import (
    AXIS_CANDIDATES,
    STATE_MIN_COUNT,
    _apply_proposed_state,
    _attach_axis_states,
    _axis_selection_score,
    _build_state_fold_map,
    _oos_retention,
    _state_metrics,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_330_state_model_stabilization")


def _select_axes(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> list[str]:
    axis_scores = pd.DataFrame([_axis_selection_score(train_df, oos_df, axis_name) for axis_name in AXIS_CANDIDATES])
    axis_scores = axis_scores.sort_values("selection_score", ascending=False).reset_index(drop=True)
    return axis_scores.head(3)["axis_name"].astype(str).tolist()


def _build_current_state_frames(
    train_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    full_df: pd.DataFrame,
) -> tuple[list[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    selected_axes = _select_axes(train_df, oos_df)
    fold_map = _build_state_fold_map(train_df, selected_axes)
    return (
        selected_axes,
        _apply_proposed_state(train_df, selected_axes, fold_map),
        _apply_proposed_state(oos_df, selected_axes, fold_map),
        _apply_proposed_state(full_df, selected_axes, fold_map),
    )


def _mix_shift(train_scoped: pd.DataFrame, oos_scoped: pd.DataFrame, column: str, categories: list[str] | None = None) -> float:
    lhs = _distribution(train_scoped[column], categories)
    rhs = _distribution(oos_scoped[column], categories)
    return _total_variation_distance(lhs, rhs)


def _feature_band_mix_shift(train_scoped: pd.DataFrame, oos_scoped: pd.DataFrame) -> float:
    shifts: list[float] = []
    for feature in ENTRY_FEATURES:
        band_col = f"{feature}_band"
        if band_col not in train_scoped.columns or band_col not in oos_scoped.columns:
            continue
        shifts.append(_mix_shift(train_scoped, oos_scoped, band_col, ["low", "mid", "high"]))
    if not shifts:
        return 0.0
    return round(float(pd.Series(shifts, dtype=float).mean()), 6)


def _path_mix_string(scoped: pd.DataFrame) -> str:
    dist = _distribution(scoped["path_type"], PATH_TYPES)
    return "|".join(f"{key}:{dist[key]:.3f}" for key in PATH_TYPES if dist.get(key, 0.0) > 0)


def _mix_string(scoped: pd.DataFrame, column: str) -> str:
    dist = _distribution(scoped[column])
    return "|".join(f"{key}:{dist[key]:.3f}" for key in sorted(dist) if dist.get(key, 0.0) > 0)


def _state_linkage_instability(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    states = sorted(set(train_df["proposed_state_model"].astype(str)) | set(oos_df["proposed_state_model"].astype(str)))
    rows: list[dict[str, Any]] = []
    for state in states:
        train_scoped = train_df[train_df["proposed_state_model"].astype(str) == state]
        oos_scoped = oos_df[oos_df["proposed_state_model"].astype(str) == state]
        train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        linkage_retention = (oos_expectancy / train_expectancy) if abs(train_expectancy) > 1e-9 else 0.0
        rows.append(
            {
                "proposed_state_model": state,
                "train_trade_count": int(len(train_scoped)),
                "oos_trade_count": int(len(oos_scoped)),
                "train_expectancy_r": round(train_expectancy, 6),
                "oos_expectancy_r": round(oos_expectancy, 6),
                "expectancy_delta": round(oos_expectancy - train_expectancy, 6),
                "train_path_mix": _path_mix_string(train_scoped),
                "oos_path_mix": _path_mix_string(oos_scoped),
                "path_mix_shift": _mix_shift(train_scoped, oos_scoped, "path_type", PATH_TYPES),
                "train_archetype_mix": _mix_string(train_scoped, "entry_archetype"),
                "oos_archetype_mix": _mix_string(oos_scoped, "entry_archetype"),
                "archetype_mix_shift": _mix_shift(train_scoped, oos_scoped, "entry_archetype"),
                "feature_band_mix_shift": _feature_band_mix_shift(train_scoped, oos_scoped),
                "linkage_retention": round(linkage_retention, 6),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["linkage_retention", "expectancy_delta", "path_mix_shift"]).reset_index(drop=True)


def _vulnerable_state_buckets(instability_df: pd.DataFrame) -> pd.DataFrame:
    out = instability_df.copy()
    oos_count = pd.to_numeric(out["oos_trade_count"], errors="coerce").fillna(0.0)
    expectancy_delta = pd.to_numeric(out["expectancy_delta"], errors="coerce").fillna(0.0)
    oos_expectancy = pd.to_numeric(out["oos_expectancy_r"], errors="coerce").fillna(0.0)
    damage = (-expectancy_delta.clip(upper=0.0)) * oos_count
    oos_damage = (-oos_expectancy.clip(upper=0.0)) * oos_count
    total_damage = float(damage.sum()) if float(damage.sum()) > 0 else 1.0
    out["contribution_to_oos_underperformance"] = (damage / total_damage).round(6)
    out["oos_negative_pressure"] = oos_damage.round(6)
    out["vulnerability_score"] = (damage + oos_damage).round(6)
    return out.sort_values(
        ["vulnerability_score", "contribution_to_oos_underperformance", "path_mix_shift"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def _strong_trend_subtype(row: pd.Series) -> str:
    if str(row.get("trend_quality_state", "")) != "strong":
        return "non_strong_trend"
    extension_state = str(row.get("extension_pressure_state", ""))
    participation_state = str(row.get("participation_quality_state", ""))
    ret_band = str(row.get("ret_20d_pre_band", ""))
    breakout_band = str(row.get("breakout_strength_pct_band", ""))
    if breakout_band == "high" and ret_band == "low":
        return "false_strength"
    if extension_state == "high" and participation_state in {"mixed", "narrow"}:
        return "crowded_continuation"
    if extension_state == "high":
        return "late_extension_continuation"
    if participation_state == "narrow":
        return "narrow_leadership_continuation"
    return "healthy_continuation"


def _strong_trend_decomposition(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    scoped = df[df["trend_quality_state"].astype(str) == "strong"].copy()
    if scoped.empty:
        return pd.DataFrame()
    scoped["strong_trend_subtype"] = scoped.apply(_strong_trend_subtype, axis=1)
    rows: list[dict[str, Any]] = []
    for subtype, bucket in scoped.groupby("strong_trend_subtype"):
        rows.append(
            {
                "scope": scope_name,
                "strong_trend_subtype": str(subtype),
                "trade_count": int(len(bucket)),
                "expectancy_r": round(float(pd.to_numeric(bucket["realized_R"], errors="coerce").mean()), 6),
                "path_entropy": round(_series_entropy(bucket["path_type"]), 6),
                "strong_continuation_share": round(_distribution(bucket["path_type"], PATH_TYPES).get("strong_continuation", 0.0), 6),
                "early_failure_share": round(_distribution(bucket["path_type"], PATH_TYPES).get("early_failure", 0.0), 6),
                "volatile_noise_share": round(_distribution(bucket["path_type"], PATH_TYPES).get("volatile_noise", 0.0), 6),
                "avg_dist_to_sma200_band": _mix_string(bucket, "dist_to_sma200_pct_band"),
                "avg_sector_breadth_band": _mix_string(bucket, "sector_breadth_band"),
                "avg_ret_20d_pre_band": _mix_string(bucket, "ret_20d_pre_band"),
                "dominant_state_share": round(float(bucket["proposed_state_model"].astype(str).value_counts(normalize=True).max()), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "expectancy_r"]).reset_index(drop=True)


def _build_generic_fold_map(raw_labels: pd.Series, min_count: int = STATE_MIN_COUNT) -> dict[str, str]:
    counts = raw_labels.astype(str).value_counts().to_dict()
    kept = {label for label, count in counts.items() if int(count) >= min_count}
    mapping: dict[str, str] = {}
    for label in counts:
        if label in kept:
            mapping[label] = label
            continue
        parts = str(label).split("|")
        folded = str(label)
        while len(parts) > 1:
            parts = parts[:-1]
            candidate = "|".join(parts)
            candidate_matches = [kept_label for kept_label in kept if kept_label.startswith(candidate)]
            if candidate_matches:
                folded = candidate
                break
        if folded == label and parts:
            folded = parts[0]
        mapping[str(label)] = folded
    return mapping


def _candidate_a_raw(row: pd.Series) -> str:
    state = str(row.get("proposed_state_model", "unknown"))
    if str(row.get("trend_quality_state", "")) == "strong":
        state = f"{state}|noise_pressure:{row.get('noise_pressure_state', 'unknown')}"
    return state


def _candidate_b_raw(row: pd.Series) -> str:
    state = str(row.get("proposed_state_model", "unknown"))
    if str(row.get("trend_quality_state", "")) == "strong":
        state = f"{state}|reversal_pressure:{row.get('reversal_pressure_state', 'unknown')}|strong_subtype:{_strong_trend_subtype(row)}"
    return state


def _candidate_c_raw(row: pd.Series, axes: list[str]) -> str:
    all_axes = [*axes, "noise_pressure"]
    seen: list[str] = []
    for axis in all_axes:
        if axis not in seen:
            seen.append(axis)
    return "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in seen)


def _apply_candidate_model(
    train_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    full_df: pd.DataFrame,
    builder: Callable[[pd.Series], str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_raw = train_df.apply(builder, axis=1)
    mapping = _build_generic_fold_map(train_raw)

    def _annotate(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["proposed_state_model"] = df.apply(builder, axis=1).map(lambda value: mapping.get(str(value), str(value)))
        return out

    return _annotate(train_df), _annotate(oos_df), _annotate(full_df)


def _state_model_summary(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> dict[str, float]:
    metrics = _state_metrics(train_df, "proposed_state_model")
    vulnerability_df = _vulnerable_state_buckets(_state_linkage_instability(train_df, oos_df))
    top3_concentration = round(float(pd.to_numeric(vulnerability_df.head(3)["contribution_to_oos_underperformance"], errors="coerce").sum()), 6)
    states = sorted(set(train_df["proposed_state_model"].astype(str)) | set(oos_df["proposed_state_model"].astype(str)))
    train_avg = float(len(train_df) / max(len(set(train_df["proposed_state_model"].astype(str))), 1))
    oos_avg = float(len(oos_df) / max(len(set(oos_df["proposed_state_model"].astype(str))), 1))
    sparse_count = 0
    for state in states:
        train_count = int((train_df["proposed_state_model"].astype(str) == state).sum())
        oos_count = int((oos_df["proposed_state_model"].astype(str) == state).sum())
        if train_count < STATE_MIN_COUNT or oos_count < 5:
            sparse_count += 1
    sparsity_risk = float(sparse_count / max(len(states), 1))
    return {
        **metrics,
        "oos_linkage_retention": _oos_retention(train_df, oos_df, "proposed_state_model"),
        "vulnerable_bucket_concentration": top3_concentration,
        "state_count": float(len(states)),
        "avg_train_trades_per_state": round(train_avg, 6),
        "avg_oos_trades_per_state": round(oos_avg, 6),
        "sparsity_risk": round(sparsity_risk, 6),
    }


def _missing_axis_value(
    base_train_df: pd.DataFrame,
    base_oos_df: pd.DataFrame,
    selected_axes: list[str],
) -> pd.DataFrame:
    base_summary = _state_model_summary(base_train_df, base_oos_df)
    candidate_rows: list[dict[str, Any]] = []
    axis_builders = {
        "noise_pressure": _candidate_a_raw,
        "reversal_pressure": _candidate_b_raw,
    }
    for axis_name, builder in axis_builders.items():
        cand_train, cand_oos, _ = _apply_candidate_model(base_train_df, base_oos_df, base_oos_df, builder)
        summary = _state_model_summary(cand_train, cand_oos)
        candidate_rows.append(
            {
                "axis_name": axis_name,
                "reduces_internal_heterogeneity": summary["within_state_path_entropy_mean"] < base_summary["within_state_path_entropy_mean"],
                "improves_oos_linkage_retention": abs(summary["oos_linkage_retention"]) < abs(base_summary["oos_linkage_retention"]),
                "isolates_failure_modes": summary["vulnerable_bucket_concentration"] >= base_summary["vulnerable_bucket_concentration"],
                "reduces_sparsity_risk": summary["sparsity_risk"] <= base_summary["sparsity_risk"],
                "delta_within_state_realized_r_variance_mean": round(summary["within_state_realized_r_variance_mean"] - base_summary["within_state_realized_r_variance_mean"], 6),
                "delta_within_state_path_entropy_mean": round(summary["within_state_path_entropy_mean"] - base_summary["within_state_path_entropy_mean"], 6),
                "delta_oos_linkage_retention": round(summary["oos_linkage_retention"] - base_summary["oos_linkage_retention"], 6),
                "delta_vulnerable_bucket_concentration": round(summary["vulnerable_bucket_concentration"] - base_summary["vulnerable_bucket_concentration"], 6),
            }
        )
    return pd.DataFrame(candidate_rows).sort_values("delta_oos_linkage_retention").reset_index(drop=True)


def _granularity_tradeoff(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows).sort_values("oos_linkage_retention", ascending=False).reset_index(drop=True)


def _revision_proposals(
    vulnerable_df: pd.DataFrame,
    missing_axis_df: pd.DataFrame,
    refined_comparison_df: pd.DataFrame,
) -> pd.DataFrame:
    top_bucket = vulnerable_df.iloc[0].to_dict() if not vulnerable_df.empty else {}
    best_axis = missing_axis_df.iloc[0].to_dict() if not missing_axis_df.empty else {}
    best_candidate = refined_comparison_df[refined_comparison_df["candidate"] != "current_task_329"].sort_values(
        ["oos_linkage_retention", "within_state_path_entropy_mean"], ascending=[False, True]
    )
    best_candidate_row = best_candidate.iloc[0].to_dict() if not best_candidate.empty else {}
    rows = [
        {
            "revision_id": "R1",
            "change_type": "split_vulnerable_strong_trend_state",
            "rationale": f"top vulnerable bucket={top_bucket.get('proposed_state_model', 'unknown')}",
            "expected_benefit": "reduce OOS linkage failure inside strong-trend states",
            "complexity": "medium",
            "priority": 1,
        },
        {
            "revision_id": "R2",
            "change_type": "reintroduce_secondary_failure_axis",
            "rationale": f"best omitted axis signal={best_axis.get('axis_name', 'unknown')}",
            "expected_benefit": "improve failure-mode isolation without rebuilding the full state model",
            "complexity": "medium",
            "priority": 2,
        },
        {
            "revision_id": "R3",
            "change_type": "merge_sparse_low_value_states",
            "rationale": f"best refined candidate={best_candidate_row.get('candidate', 'unknown')}",
            "expected_benefit": "reduce sparsity risk while preserving payoff separation",
            "complexity": "low",
            "priority": 3,
        },
    ]
    return pd.DataFrame(rows).sort_values("priority").reset_index(drop=True)


def _decision_row(refined_comparison_df: pd.DataFrame) -> pd.DataFrame:
    current = refined_comparison_df[refined_comparison_df["candidate"] == "current_task_329"].iloc[0]
    best_refined = refined_comparison_df[refined_comparison_df["candidate"] != "current_task_329"].sort_values(
        ["oos_linkage_retention", "within_state_path_entropy_mean", "sparsity_risk"],
        ascending=[False, True, True],
    ).iloc[0]
    improved_retention = abs(float(best_refined["oos_linkage_retention"])) < abs(float(current["oos_linkage_retention"]))
    improved_entropy = float(best_refined["within_state_path_entropy_mean"]) < float(current["within_state_path_entropy_mean"])
    acceptable_sparsity = float(best_refined["sparsity_risk"]) <= float(current["sparsity_risk"]) + 0.15
    if improved_retention and improved_entropy and acceptable_sparsity:
        decision = "refine_current_state_model_incrementally"
        rationale = f"best_candidate={best_refined['candidate']} improves retention/homogeneity without excessive sparsity"
    elif improved_retention and not acceptable_sparsity:
        decision = "rebuild_state_model_again_with_new_axes"
        rationale = f"best_candidate={best_refined['candidate']} needs broader structural rebuild to control sparsity"
    else:
        decision = "keep_current_task_329_state_model_as_is"
        rationale = "refined candidates do not beat the current state model clearly enough"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "recommended_candidate": str(best_refined["candidate"]),
                "decision_reason": rationale,
                "current_oos_linkage_retention": round(float(current["oos_linkage_retention"]), 6),
                "recommended_oos_linkage_retention": round(float(best_refined["oos_linkage_retention"]), 6),
            }
        ]
    )


def _write_markdown(
    out_dir: Path,
    decision_df: pd.DataFrame,
    vulnerable_df: pd.DataFrame,
    refined_comparison_df: pd.DataFrame,
    proposals_df: pd.DataFrame,
) -> None:
    top_vulnerable = vulnerable_df.head(3)[
        ["proposed_state_model", "oos_expectancy_r", "expectancy_delta", "contribution_to_oos_underperformance"]
    ]
    best_refined = refined_comparison_df.sort_values(
        ["oos_linkage_retention", "within_state_path_entropy_mean", "sparsity_risk"],
        ascending=[False, True, True],
    ).head(3)
    decision = decision_df.iloc[0].to_dict() if not decision_df.empty else {}

    def _fmt(df: pd.DataFrame) -> list[str]:
        if df.empty:
            return ["_No rows_"]
        cols = [str(column) for column in df.columns]
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for record in df.to_dict("records"):
            row: list[str] = []
            for col in cols:
                value = record.get(col, "")
                if isinstance(value, float):
                    row.append("" if math.isnan(value) else f"{value:.6g}")
                else:
                    row.append(str(value))
            lines.append("| " + " | ".join(row) + " |")
        return lines

    lines = [
        "# Task 330: State Model Stabilization",
        "",
        "## Core Answer",
        "",
        f"- Current bottleneck: `OOS linkage instability concentrated in vulnerable strong-trend buckets`.",
        f"- Decision: `{decision.get('decision', 'unknown')}`.",
        f"- Recommended candidate: `{decision.get('recommended_candidate', 'unknown')}`.",
        "",
        "## Top Vulnerable Buckets",
        "",
    ]
    lines.extend(_fmt(top_vulnerable))
    lines.extend(
        [
            "",
            "## Best Candidate Comparison",
            "",
        ]
    )
    lines.extend(_fmt(best_refined))
    lines.extend(
        [
            "",
            "## Recommended Structural Revisions",
            "",
        ]
    )
    lines.extend(_fmt(proposals_df))
    (out_dir / "task_330_state_model_stabilization.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 330: state model stabilization.")
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

    train_df, oos_df, full_df = _labeled_trade_frames(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
    )
    train_df = _attach_axis_states(train_df)
    oos_df = _attach_axis_states(oos_df)
    full_df = _attach_axis_states(full_df)

    selected_axes, current_train_df, current_oos_df, current_full_df = _build_current_state_frames(train_df, oos_df, full_df)

    instability_df = _state_linkage_instability(current_train_df, current_oos_df)
    vulnerable_df = _vulnerable_state_buckets(instability_df)

    strong_trend_df = pd.concat(
        [
            _strong_trend_decomposition(current_train_df, "train"),
            _strong_trend_decomposition(current_oos_df, "anchored_oos"),
            _strong_trend_decomposition(current_full_df, "full_period"),
        ],
        ignore_index=True,
    )

    missing_axis_df = _missing_axis_value(current_train_df, current_oos_df, selected_axes)

    candidate_rows: list[dict[str, Any]] = []
    current_summary = _state_model_summary(current_train_df, current_oos_df)
    candidate_rows.append({"candidate": "current_task_329", "description": "current Task 329 state model", **current_summary})

    candidate_specs = [
        ("candidate_A", "minimal stabilization revision", _candidate_a_raw),
        ("candidate_B", "stronger structural split", _candidate_b_raw),
        ("candidate_C", "optional axis reintroduction", lambda row: _candidate_c_raw(row, selected_axes)),
    ]
    for candidate_name, description, builder in candidate_specs:
        cand_train_df, cand_oos_df, cand_full_df = _apply_candidate_model(current_train_df, current_oos_df, current_full_df, builder)
        summary = _state_model_summary(cand_train_df, cand_oos_df)
        candidate_rows.append({"candidate": candidate_name, "description": description, **summary})

    refined_comparison_df = pd.DataFrame(candidate_rows).sort_values(
        ["oos_linkage_retention", "within_state_path_entropy_mean", "sparsity_risk"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    granularity_df = refined_comparison_df[
        [
            "candidate",
            "description",
            "state_count",
            "avg_train_trades_per_state",
            "avg_oos_trades_per_state",
            "between_state_expectancy_dispersion",
            "within_state_realized_r_variance_mean",
            "within_state_path_entropy_mean",
            "oos_linkage_retention",
            "sparsity_risk",
        ]
    ].copy()

    proposals_df = _revision_proposals(vulnerable_df, missing_axis_df, refined_comparison_df)
    decision_df = _decision_row(refined_comparison_df)

    instability_df.to_csv(out_dir / "task_330_state_linkage_instability.csv", index=False)
    vulnerable_df.to_csv(out_dir / "task_330_vulnerable_state_buckets.csv", index=False)
    strong_trend_df.to_csv(out_dir / "task_330_strong_trend_decomposition.csv", index=False)
    missing_axis_df.to_csv(out_dir / "task_330_missing_axis_value.csv", index=False)
    granularity_df.to_csv(out_dir / "task_330_state_granularity_tradeoff.csv", index=False)
    proposals_df.to_csv(out_dir / "task_330_state_revision_proposals.csv", index=False)
    refined_comparison_df.to_csv(out_dir / "task_330_refined_state_model_comparison.csv", index=False)
    decision_df.to_csv(out_dir / "task_330_state_stabilization_decision.csv", index=False)
    _write_markdown(out_dir, decision_df, vulnerable_df, refined_comparison_df, proposals_df)


if __name__ == "__main__":
    main()
