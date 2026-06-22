from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import PATH_TYPES
from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    DEFAULT_BASE_DIR,
    RANKED_INPUT,
    _distribution,
    _labeled_trade_frames,
    _regime_drift,
    _series_entropy,
    _total_variation_distance,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_329_state_model_redesign")
AXIS_CANDIDATES = [
    "trend_quality",
    "extension_pressure",
    "participation_quality",
    "noise_pressure",
    "reversal_pressure",
]
STATE_MIN_COUNT = 25


def _trend_quality_state(row: pd.Series) -> str:
    ret_band = str(row.get("ret_20d_pre_band", "unknown"))
    dist_band = str(row.get("dist_to_sma200_pct_band", "unknown"))
    if ret_band == "high" and dist_band in {"mid", "high"}:
        return "strong"
    if ret_band == "low" and dist_band == "low":
        return "weak"
    return "neutral"


def _extension_pressure_state(row: pd.Series) -> str:
    dist_band = str(row.get("dist_to_sma200_pct_band", "unknown"))
    breakout_band = str(row.get("breakout_strength_pct_band", "unknown"))
    if dist_band == "high" and breakout_band == "high":
        return "high"
    if dist_band == "low" and breakout_band in {"low", "mid"}:
        return "low"
    return "medium"


def _participation_quality_state(row: pd.Series) -> str:
    breadth_band = str(row.get("sector_breadth_band", "unknown"))
    if breadth_band == "high":
        return "broad"
    if breadth_band == "low":
        return "narrow"
    return "mixed"


def _noise_pressure_state(row: pd.Series) -> str:
    vol_band = str(row.get("vol_contraction_ratio_band", "unknown"))
    if vol_band == "high":
        return "high_noise"
    if vol_band == "low":
        return "compressed"
    return "balanced"


def _reversal_pressure_state(row: pd.Series) -> str:
    regime = str(row.get("regime_state", ""))
    ret_band = str(row.get("ret_20d_pre_band", "unknown"))
    if regime in {"failed_recovery", "risk_off_reversal"} or ret_band == "low":
        return "high"
    if regime in {"late_extension", "narrow_leadership_trend"} and ret_band == "high":
        return "low"
    return "medium"


def _axis_definition_rows() -> list[dict[str, Any]]:
    return [
        {
            "axis_name": "trend_quality",
            "definition": "trend persistence and trend support under the breakout",
            "input_features": "ret_20d_pre|dist_to_sma200_pct",
            "state_values": "weak|neutral|strong",
            "expected_payoff_implication": "strong trend should improve continuation and reduce false starts",
        },
        {
            "axis_name": "extension_pressure",
            "definition": "how late and stretched the breakout is before entry",
            "input_features": "dist_to_sma200_pct|breakout_strength_pct",
            "state_values": "low|medium|high",
            "expected_payoff_implication": "high extension should increase retrace and crowded failure risk",
        },
        {
            "axis_name": "participation_quality",
            "definition": "breadth and participation behind the move",
            "input_features": "sector_breadth",
            "state_values": "narrow|mixed|broad",
            "expected_payoff_implication": "broad participation should improve follow-through stability",
        },
        {
            "axis_name": "noise_pressure",
            "definition": "noise and whipsaw pressure around breakout launch",
            "input_features": "vol_contraction_ratio",
            "state_values": "compressed|balanced|high_noise",
            "expected_payoff_implication": "high noise should raise volatile noise and weak continuation odds",
        },
        {
            "axis_name": "reversal_pressure",
            "definition": "mean-reversion or rebound pressure likely to break continuation",
            "input_features": "ret_20d_pre|regime_state",
            "state_values": "low|medium|high",
            "expected_payoff_implication": "high reversal pressure should increase failed continuation states",
        },
    ]


def _attach_axis_states(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["trend_quality_state"] = out.apply(_trend_quality_state, axis=1)
    out["extension_pressure_state"] = out.apply(_extension_pressure_state, axis=1)
    out["participation_quality_state"] = out.apply(_participation_quality_state, axis=1)
    out["noise_pressure_state"] = out.apply(_noise_pressure_state, axis=1)
    out["reversal_pressure_state"] = out.apply(_reversal_pressure_state, axis=1)
    return out


def _framework_group_col(framework: str) -> str:
    return "regime_state" if framework == "old_regime" else "proposed_state_model"


def _state_metrics(df: pd.DataFrame, group_col: str) -> dict[str, float]:
    grouped = df.groupby(group_col, as_index=False).agg(expectancy_r=("realized_R", "mean"))
    between_dispersion = float(pd.to_numeric(grouped["expectancy_r"], errors="coerce").std(ddof=0)) if not grouped.empty else 0.0
    rows = []
    for state_value, scoped in df.groupby(group_col):
        rows.append(
            {
                "state": str(state_value),
                "realized_r_variance": float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)),
                "path_entropy": float(_series_entropy(scoped["path_type"])),
                "expectancy_r": float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()),
            }
        )
    state_df = pd.DataFrame(rows)
    within_var = float(pd.to_numeric(state_df["realized_r_variance"], errors="coerce").mean()) if not state_df.empty else 0.0
    within_entropy = float(pd.to_numeric(state_df["path_entropy"], errors="coerce").mean()) if not state_df.empty else 0.0
    return {
        "between_state_expectancy_dispersion": round(between_dispersion, 6),
        "within_state_realized_r_variance_mean": round(within_var, 6),
        "within_state_path_entropy_mean": round(within_entropy, 6),
    }


def _oos_retention(train_df: pd.DataFrame, oos_df: pd.DataFrame, group_col: str) -> float:
    train_expect = train_df.groupby(group_col)["realized_R"].mean().to_dict()
    oos_expect = oos_df.groupby(group_col)["realized_R"].mean().to_dict()
    states = sorted(set(train_expect) | set(oos_expect))
    scores: list[float] = []
    for state in states:
        train_value = float(train_expect.get(state, 0.0))
        oos_value = float(oos_expect.get(state, 0.0))
        if abs(train_value) <= 1e-9:
            continue
        scores.append(oos_value / train_value)
    if not scores:
        return 0.0
    return round(float(pd.Series(scores, dtype=float).mean()), 6)


def _drift_sensitivity(train_df: pd.DataFrame, oos_df: pd.DataFrame, group_col: str) -> float:
    states = sorted(set(train_df[group_col].astype(str)) | set(oos_df[group_col].astype(str)))
    shifts: list[float] = []
    for state in states:
        train_scoped = train_df[train_df[group_col].astype(str) == state]
        oos_scoped = oos_df[oos_df[group_col].astype(str) == state]
        path_shift = _total_variation_distance(_distribution(train_scoped["path_type"], PATH_TYPES), _distribution(oos_scoped["path_type"], PATH_TYPES))
        archetype_shift = _total_variation_distance(_distribution(train_scoped["entry_archetype"]), _distribution(oos_scoped["entry_archetype"]))
        shifts.append(max(path_shift, archetype_shift))
    if not shifts:
        return 0.0
    return round(float(pd.Series(shifts, dtype=float).mean()), 6)


def _axis_framework(df: pd.DataFrame, axis_name: str) -> str:
    return f"{axis_name}_state"


def _axis_selection_score(train_df: pd.DataFrame, oos_df: pd.DataFrame, axis_name: str) -> dict[str, Any]:
    group_col = _axis_framework(train_df, axis_name)
    metrics = _state_metrics(train_df, group_col)
    retention = _oos_retention(train_df, oos_df, group_col)
    score = (
        metrics["between_state_expectancy_dispersion"]
        - metrics["within_state_realized_r_variance_mean"]
        - metrics["within_state_path_entropy_mean"]
        + retention
    )
    return {
        "axis_name": axis_name,
        "selection_score": round(score, 6),
        "between_state_expectancy_dispersion": metrics["between_state_expectancy_dispersion"],
        "within_state_realized_r_variance_mean": metrics["within_state_realized_r_variance_mean"],
        "within_state_path_entropy_mean": metrics["within_state_path_entropy_mean"],
        "oos_linkage_retention": retention,
    }


def _compose_raw_state(row: pd.Series, selected_axes: list[str]) -> str:
    return "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in selected_axes)


def _build_state_fold_map(train_df: pd.DataFrame, selected_axes: list[str]) -> dict[str, str]:
    raw_states = train_df.apply(lambda row: _compose_raw_state(row, selected_axes), axis=1)
    counts = raw_states.value_counts().to_dict()
    kept = {state for state, count in counts.items() if int(count) >= STATE_MIN_COUNT}
    mapping: dict[str, str] = {}
    for state in counts:
        if state in kept:
            mapping[state] = state
            continue
        parts = state.split("|")
        folded = state
        while len(parts) > 1:
            parts = parts[:-1]
            candidate = "|".join(parts)
            candidate_matches = [kept_state for kept_state in kept if kept_state.startswith(candidate)]
            if candidate_matches:
                folded = candidate
                break
        if folded == state and state not in kept:
            folded = parts[0] if parts else state
        mapping[state] = folded
    return mapping


def _apply_proposed_state(df: pd.DataFrame, selected_axes: list[str], fold_map: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    out["raw_proposed_state_model"] = out.apply(lambda row: _compose_raw_state(row, selected_axes), axis=1)
    out["proposed_state_model"] = out["raw_proposed_state_model"].map(lambda value: fold_map.get(str(value), str(value)))
    return out


def _framework_comparison(train_old: pd.DataFrame, oos_old: pd.DataFrame, train_new: pd.DataFrame, oos_new: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for framework, train_df, oos_df in (
        ("old_regime", train_old, oos_old),
        ("new_state_model", train_new, oos_new),
    ):
        group_col = _framework_group_col(framework)
        metrics = _state_metrics(train_df, group_col)
        rows.append(
            {
                "framework": framework,
                **metrics,
                "oos_linkage_retention": _oos_retention(train_df, oos_df, group_col),
                "drift_sensitivity": _drift_sensitivity(train_df, oos_df, group_col),
            }
        )
    return pd.DataFrame(rows)


def _state_path_matrix(df: pd.DataFrame, scope_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for proposed_state, scoped in df.groupby("proposed_state_model"):
        path_dist = _distribution(scoped["path_type"], PATH_TYPES)
        rows.append(
            {
                "scope": scope_name,
                "proposed_state_model": str(proposed_state),
                "trade_count": int(len(scoped)),
                "expectancy_r": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean()), 6),
                "strong_continuation_share": round(path_dist.get("strong_continuation", 0.0), 6),
                "early_failure_share": round(path_dist.get("early_failure", 0.0), 6),
                "volatile_noise_share": round(path_dist.get("volatile_noise", 0.0), 6),
                "path_entropy": round(_series_entropy(scoped["path_type"]), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "expectancy_r"], ascending=[True, False]).reset_index(drop=True)


def _path_mix_string(scoped: pd.DataFrame) -> str:
    dist = _distribution(scoped["path_type"], PATH_TYPES)
    return "|".join(f"{key}:{dist[key]:.3f}" for key in PATH_TYPES if dist.get(key, 0.0) > 0)


def _state_archetype_stability(df: pd.DataFrame, scope_name: str, old_regime_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["proposed_state_model", "entry_archetype"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
    )
    state_disp = grouped.groupby("proposed_state_model")["expectancy_r"].std(ddof=0).to_dict()
    state_totals = grouped.groupby("proposed_state_model")["trade_count"].sum().to_dict()
    old_disp = old_regime_df.groupby("regime_state")["expectancy_r"].std(ddof=0).to_dict() if not old_regime_df.empty else {}
    old_mean_disp = float(pd.Series(old_disp, dtype=float).mean()) if old_disp else 0.0
    rows: list[dict[str, Any]] = []
    for record in grouped.to_dict("records"):
        proposed_state = str(record["proposed_state_model"])
        archetype = str(record["entry_archetype"])
        scoped = df[(df["proposed_state_model"] == proposed_state) & (df["entry_archetype"] == archetype)]
        state_scoped = grouped[grouped["proposed_state_model"] == proposed_state]
        dominant_share = float(state_scoped["trade_count"].max()) / max(int(state_totals.get(proposed_state, 1)), 1)
        local_disp = float(state_disp.get(proposed_state, 0.0) or 0.0)
        rows.append(
            {
                "scope": scope_name,
                "proposed_state_model": proposed_state,
                "entry_archetype": archetype,
                "trade_count": int(record["trade_count"]),
                "expectancy_r": round(float(record["expectancy_r"]), 6),
                "win_rate": round(float(record["win_rate"]), 6),
                "total_r": round(float(record["total_r"]), 6),
                "path_mix": _path_mix_string(scoped),
                "state_internal_archetype_dispersion": round(local_disp, 6),
                "dominant_archetype_share": round(dominant_share, 6),
                "contradiction_reduction_vs_old_regime": bool(local_disp < old_mean_disp),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "proposed_state_model", "trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def _state_internal_homogeneity(df: pd.DataFrame, scope_name: str, old_regime_df: pd.DataFrame) -> pd.DataFrame:
    old_var_mean = float(pd.to_numeric(old_regime_df["realized_r_variance"], errors="coerce").mean()) if not old_regime_df.empty else 0.0
    old_entropy_mean = float(pd.to_numeric(old_regime_df["path_type_entropy"], errors="coerce").mean()) if not old_regime_df.empty else 0.0
    old_ft_mean = float(pd.to_numeric(old_regime_df["follow_through_variance"], errors="coerce").mean()) if not old_regime_df.empty else 0.0
    old_retrace_mean = float(pd.to_numeric(old_regime_df["retrace_variance"], errors="coerce").mean()) if not old_regime_df.empty else 0.0
    rows: list[dict[str, Any]] = []
    for proposed_state, scoped in df.groupby("proposed_state_model"):
        realized_var = float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0))
        path_entropy = float(_series_entropy(scoped["path_type"]))
        ft_var = float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0))
        retrace_var = float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0))
        rows.append(
            {
                "scope": scope_name,
                "proposed_state_model": str(proposed_state),
                "trade_count": int(len(scoped)),
                "realized_r_variance": round(realized_var, 6),
                "path_entropy": round(path_entropy, 6),
                "follow_through_variance": round(ft_var, 6),
                "retrace_variance": round(retrace_var, 6),
                "delta_realized_r_variance_vs_old_mean": round(realized_var - old_var_mean, 6),
                "delta_path_entropy_vs_old_mean": round(path_entropy - old_entropy_mean, 6),
                "delta_follow_through_variance_vs_old_mean": round(ft_var - old_ft_mean, 6),
                "delta_retrace_variance_vs_old_mean": round(retrace_var - old_retrace_mean, 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "realized_r_variance"], ascending=[True, True]).reset_index(drop=True)


def _state_oos_retention(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    states = sorted(set(train_df["proposed_state_model"].astype(str)) | set(oos_df["proposed_state_model"].astype(str)))
    train_total = max(len(train_df), 1)
    oos_total = max(len(oos_df), 1)
    rows: list[dict[str, Any]] = []
    for state in states:
        train_scoped = train_df[train_df["proposed_state_model"].astype(str) == state]
        oos_scoped = oos_df[oos_df["proposed_state_model"].astype(str) == state]
        train_share = float(len(train_scoped) / train_total)
        oos_share = float(len(oos_scoped) / oos_total)
        train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean()) if not train_scoped.empty else 0.0
        oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        linkage_retention = (oos_expectancy / train_expectancy) if abs(train_expectancy) > 1e-9 else 0.0
        rows.append(
            {
                "proposed_state_model": state,
                "train_trade_count": int(len(train_scoped)),
                "oos_trade_count": int(len(oos_scoped)),
                "trade_share_delta": round(oos_share - train_share, 6),
                "expectancy_delta": round(oos_expectancy - train_expectancy, 6),
                "path_mix_shift": _total_variation_distance(_distribution(train_scoped["path_type"], PATH_TYPES), _distribution(oos_scoped["path_type"], PATH_TYPES)),
                "archetype_mix_shift": _total_variation_distance(_distribution(train_scoped["entry_archetype"]), _distribution(oos_scoped["entry_archetype"])),
                "linkage_retention": round(linkage_retention, 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["expectancy_delta", "path_mix_shift"]).reset_index(drop=True)


def _state_model_decision(comparison_df: pd.DataFrame, selected_axes: list[str]) -> pd.DataFrame:
    old_row = comparison_df[comparison_df["framework"] == "old_regime"].iloc[0]
    new_row = comparison_df[comparison_df["framework"] == "new_state_model"].iloc[0]
    separation_improved = float(new_row["between_state_expectancy_dispersion"]) > float(old_row["between_state_expectancy_dispersion"])
    homogeneity_improved = (
        float(new_row["within_state_realized_r_variance_mean"]) < float(old_row["within_state_realized_r_variance_mean"])
        and float(new_row["within_state_path_entropy_mean"]) < float(old_row["within_state_path_entropy_mean"])
    )
    retention_improved = (
        abs(float(new_row["oos_linkage_retention"])) > abs(float(old_row["oos_linkage_retention"]))
        or float(new_row["drift_sensitivity"]) < float(old_row["drift_sensitivity"])
    )
    improvements = sum((1 if separation_improved else 0, 1 if homogeneity_improved else 0, 1 if retention_improved else 0))
    if improvements == 3:
        decision = "fully_replaced"
    elif improvements >= 2:
        decision = "partially_rebuilt"
    else:
        decision = "kept_but_reinterpreted"
    reason = (
        f"selected_axes={','.join(selected_axes)}; "
        f"separation_improved={separation_improved}; "
        f"homogeneity_improved={homogeneity_improved}; "
        f"retention_improved={retention_improved}"
    )
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "selected_axes": "|".join(selected_axes),
                "separation_improved": separation_improved,
                "homogeneity_improved": homogeneity_improved,
                "retention_improved": retention_improved,
            }
        ]
    )


def _write_markdown_report(
    out_dir: Path,
    state_axes_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    decision_df: pd.DataFrame,
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

    decision_row = decision_df.iloc[0].to_dict() if not decision_df.empty else {}
    selected_axes = state_axes_df[state_axes_df["selected_for_final_state_model"]]["axis_name"].tolist()
    lines = [
        "# Task 329: Breakout State Model Redesign",
        "",
        "## Core Answer",
        "",
        f"- Decision: `{decision_row.get('decision', 'unknown')}`.",
        f"- Proposed structural axes: `{', '.join(selected_axes)}`.",
        "- The new state model is judged by payoff separation, internal homogeneity, and OOS retention rather than descriptive intuition.",
        "",
        "## State Axes",
        "",
    ]
    lines.extend(_fmt(state_axes_df))
    lines.extend([
        "",
        "## Framework Comparison",
        "",
    ])
    lines.extend(_fmt(comparison_df))
    lines.extend([
        "",
        "## Final Conclusion",
        "",
        "- This report answers what should replace the current regime framework and why the proposed state model is more appropriate for breakout payoff separation.",
        f"- The recommended next step is `state validation` first, then `state-conditioned application` only if this redesign retains OOS structure.",
    ])
    (out_dir / "task_329_breakout_state_model_redesign.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 329: breakout state model redesign.")
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

    axis_scores = pd.DataFrame([_axis_selection_score(train_df, oos_df, axis_name) for axis_name in AXIS_CANDIDATES]).sort_values(
        "selection_score", ascending=False
    ).reset_index(drop=True)
    selected_axes = axis_scores.head(3)["axis_name"].tolist()

    fold_map = _build_state_fold_map(train_df, selected_axes)
    train_df = _apply_proposed_state(train_df, selected_axes, fold_map)
    oos_df = _apply_proposed_state(oos_df, selected_axes, fold_map)
    full_df = _apply_proposed_state(full_df, selected_axes, fold_map)

    state_axes_rows = []
    axis_score_lookup = axis_scores.set_index("axis_name").to_dict("index")
    for row in _axis_definition_rows():
        axis_name = str(row["axis_name"])
        state_axes_rows.append(
            {
                **row,
                "selected_for_final_state_model": axis_name in selected_axes,
                "selection_score": axis_score_lookup.get(axis_name, {}).get("selection_score", math.nan),
            }
        )
    state_axes_df = pd.DataFrame(state_axes_rows)

    comparison_df = _framework_comparison(train_df, oos_df, train_df, oos_df)

    state_path_df = pd.concat(
        [
            _state_path_matrix(train_df, "train"),
            _state_path_matrix(oos_df, "anchored_oos"),
            _state_path_matrix(full_df, "full_period"),
        ],
        ignore_index=True,
    )

    old_train_regime_hom = pd.DataFrame(
        [
            {
                "regime_state": regime_state,
                "realized_r_variance": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)), 6),
                "path_type_entropy": round(float(_series_entropy(scoped["path_type"])), 6),
                "follow_through_variance": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "retrace_variance": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0)), 6),
            }
            for regime_state, scoped in train_df.groupby("regime_state")
        ]
    )
    old_oos_regime_hom = pd.DataFrame(
        [
            {
                "regime_state": regime_state,
                "realized_r_variance": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)), 6),
                "path_type_entropy": round(float(_series_entropy(scoped["path_type"])), 6),
                "follow_through_variance": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "retrace_variance": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0)), 6),
            }
            for regime_state, scoped in oos_df.groupby("regime_state")
        ]
    )
    old_full_regime_hom = pd.DataFrame(
        [
            {
                "regime_state": regime_state,
                "realized_r_variance": round(float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0)), 6),
                "path_type_entropy": round(float(_series_entropy(scoped["path_type"])), 6),
                "follow_through_variance": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "retrace_variance": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0)), 6),
            }
            for regime_state, scoped in full_df.groupby("regime_state")
        ]
    )

    state_archetype_df = pd.concat(
        [
            _state_archetype_stability(train_df, "train", train_df.groupby(["regime_state", "entry_archetype"], as_index=False).agg(expectancy_r=("realized_R", "mean"))),
            _state_archetype_stability(oos_df, "anchored_oos", oos_df.groupby(["regime_state", "entry_archetype"], as_index=False).agg(expectancy_r=("realized_R", "mean"))),
            _state_archetype_stability(full_df, "full_period", full_df.groupby(["regime_state", "entry_archetype"], as_index=False).agg(expectancy_r=("realized_R", "mean"))),
        ],
        ignore_index=True,
    )

    state_homogeneity_df = pd.concat(
        [
            _state_internal_homogeneity(train_df, "train", old_train_regime_hom),
            _state_internal_homogeneity(oos_df, "anchored_oos", old_oos_regime_hom),
            _state_internal_homogeneity(full_df, "full_period", old_full_regime_hom),
        ],
        ignore_index=True,
    )

    state_oos_retention_df = _state_oos_retention(train_df, oos_df)
    decision_df = _state_model_decision(comparison_df, selected_axes)

    state_axes_df.to_csv(out_dir / "task_329_state_axes.csv", index=False)
    comparison_df.to_csv(out_dir / "task_329_state_model_comparison.csv", index=False)
    state_path_df.to_csv(out_dir / "task_329_state_path_matrix.csv", index=False)
    state_archetype_df.to_csv(out_dir / "task_329_state_archetype_stability.csv", index=False)
    state_homogeneity_df.to_csv(out_dir / "task_329_state_internal_homogeneity.csv", index=False)
    state_oos_retention_df.to_csv(out_dir / "task_329_state_oos_retention.csv", index=False)
    decision_df.to_csv(out_dir / "task_329_state_model_decision.csv", index=False)
    _write_markdown_report(out_dir, state_axes_df, comparison_df, decision_df)


if __name__ == "__main__":
    main()
