from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import StructuralConfig, _load_stock_symbols, _prepare_preloaded_frames
from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import (
    ENTRY_FEATURES,
    PATH_TYPES,
    _annotate_pre_entry_bands,
    _feature_band_edges,
)
from src.backtest.analysis_structural_breakout_regime_entry_325 import (
    RANKED_INPUT,
    _build_entry_feature_lookup,
    _build_regime_lookup,
    _build_universe_state_lookup,
)
from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    DEFAULT_BASE_DIR,
    _distribution,
    _labeled_trade_frames,
    _series_entropy,
    _total_variation_distance,
)
from src.backtest.analysis_structural_breakout_state_model_redesign_329 import (
    STATE_MIN_COUNT,
    _attach_axis_states,
    _drift_sensitivity,
    _oos_retention,
    _state_metrics,
)
from src.backtest.analysis_structural_breakout_state_model_stabilization_330 import _build_generic_fold_map


DEFAULT_OUT_DIR = Path("docs/reports/task_332_state_space_realignment")
OOS_MIN_COUNT = 5
AXIS_INFO = [
    {
        "axis": "noise_pressure",
        "type": "primary",
        "definition": "structured breakout launch versus random or whipsaw-dominated launch environment",
        "rationale": "recent tasks showed noise explains unstable payoff paths more directly than participation alone",
    },
    {
        "axis": "trend_quality",
        "type": "primary",
        "definition": "directional persistence and trend support behind the breakout attempt",
        "rationale": "trend quality still separates continuation from failure, but only conditionally under noise",
    },
    {
        "axis": "extension_pressure",
        "type": "primary",
        "definition": "fresh versus stretched breakout positioning before entry",
        "rationale": "extension continues to explain crowded failure and late continuation decay",
    },
    {
        "axis": "participation_quality",
        "type": "secondary",
        "definition": "breadth confirmation that locally refines already-identified structural states",
        "rationale": "participation helps explain branch-level dispersion but was too weak as a core state axis",
    },
    {
        "axis": "reversal_pressure",
        "type": "exploratory",
        "definition": "mean-reversion pressure likely to interrupt breakout continuation",
        "rationale": "useful as a diagnostic overlay, but not yet stable enough to anchor the primary state space",
    },
]


def _axis_definition_df() -> pd.DataFrame:
    return pd.DataFrame(AXIS_INFO)


def _candidate_a_raw(row: pd.Series) -> str:
    parts = [f"noise:{row.get('noise_pressure_state', 'unknown')}"]
    noise_state = str(row.get("noise_pressure_state", "unknown"))
    trend_state = str(row.get("trend_quality_state", "unknown"))
    extension_state = str(row.get("extension_pressure_state", "unknown"))
    if noise_state != "compressed" or trend_state == "weak":
        parts.append(f"trend:{trend_state}")
    if noise_state == "high_noise" or trend_state == "strong":
        parts.append(f"extension:{extension_state}")
    return "|".join(parts)


def _candidate_b_raw(row: pd.Series) -> str:
    trend_state = str(row.get("trend_quality_state", "unknown"))
    parts = [f"trend:{trend_state}"]
    if trend_state == "weak":
        parts.append(f"noise:{row.get('noise_pressure_state', 'unknown')}")
    else:
        parts.append(f"extension:{row.get('extension_pressure_state', 'unknown')}")
        if trend_state == "strong":
            parts.append(f"noise:{row.get('noise_pressure_state', 'unknown')}")
    return "|".join(parts)


def _candidate_c_builder(dense_parents: set[str]) -> Callable[[pd.Series], str]:
    def _builder(row: pd.Series) -> str:
        noise_state = str(row.get("noise_pressure_state", "unknown"))
        extension_state = str(row.get("extension_pressure_state", "unknown"))
        parent = f"noise:{noise_state}|extension:{extension_state}"
        parts = [parent]
        if parent in dense_parents:
            parts.append(f"participation:{row.get('participation_quality_state', 'unknown')}")
        if noise_state == "high_noise":
            parts.append(f"trend:{row.get('trend_quality_state', 'unknown')}")
        return "|".join(parts)

    return _builder


def _dense_candidate_c_parents(train_df: pd.DataFrame) -> set[str]:
    raw = train_df.apply(lambda row: f"noise:{row.get('noise_pressure_state', 'unknown')}|extension:{row.get('extension_pressure_state', 'unknown')}", axis=1)
    counts = raw.value_counts()
    return {str(label) for label, count in counts.items() if int(count) >= 50}


def _apply_candidate_state(
    train_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    full_df: pd.DataFrame,
    column_name: str,
    builder: Callable[[pd.Series], str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    train_raw = train_df.apply(builder, axis=1)
    fold_map = _build_generic_fold_map(train_raw, min_count=STATE_MIN_COUNT)

    def _annotate(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        raw_values = df.apply(builder, axis=1)
        out[f"raw_{column_name}"] = raw_values
        out[column_name] = raw_values.map(lambda value: fold_map.get(str(value), str(value)))
        return out

    return _annotate(train_df), _annotate(oos_df), _annotate(full_df), fold_map


def _between_state_expectancy_variance(df: pd.DataFrame, group_col: str) -> float:
    grouped = df.groupby(group_col, as_index=False).agg(expectancy_r=("realized_R", "mean"))
    if grouped.empty:
        return 0.0
    return round(float(pd.to_numeric(grouped["expectancy_r"], errors="coerce").var(ddof=0)), 6)


def _state_model_summary(df_train: pd.DataFrame, df_oos: pd.DataFrame, group_col: str) -> dict[str, float]:
    metrics = _state_metrics(df_train, group_col)
    states = sorted(set(df_train[group_col].astype(str)) | set(df_oos[group_col].astype(str)))
    train_avg = float(len(df_train) / max(len(set(df_train[group_col].astype(str))), 1))
    oos_avg = float(len(df_oos) / max(len(set(df_oos[group_col].astype(str))), 1))
    sparse_count = 0
    for state in states:
        train_count = int((df_train[group_col].astype(str) == state).sum())
        oos_count = int((df_oos[group_col].astype(str) == state).sum())
        if train_count < STATE_MIN_COUNT or oos_count < OOS_MIN_COUNT:
            sparse_count += 1
    sparsity_risk = float(sparse_count / max(len(states), 1))
    return {
        **metrics,
        "between_state_expectancy_variance": _between_state_expectancy_variance(df_train, group_col),
        "oos_linkage_retention": _oos_retention(df_train, df_oos, group_col),
        "drift_sensitivity": _drift_sensitivity(df_train, df_oos, group_col),
        "avg_train_trades_per_state": round(train_avg, 6),
        "avg_oos_trades_per_state": round(oos_avg, 6),
        "sparsity_risk": round(sparsity_risk, 6),
    }


def _build_daily_metadata_axis_modes(base_dir: Path, train_df: pd.DataFrame) -> pd.DataFrame:
    stocks = _load_stock_symbols(base_dir, StructuralConfig())
    frames, _ = _prepare_preloaded_frames(base_dir, stocks)
    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_lookup = _build_regime_lookup(base_dir, universe_state_lookup)
    metadata_lookup = _build_entry_feature_lookup(frames, stocks, universe_state_lookup, regime_lookup)
    rows: list[dict[str, Any]] = []
    for _, payload in metadata_lookup.items():
        row = dict(payload)
        rows.append(row)
    metadata_df = pd.DataFrame(rows)
    if metadata_df.empty:
        return pd.DataFrame(columns=["date_key"])
    metadata_df = _annotate_pre_entry_bands(metadata_df, _feature_band_edges(train_df, ENTRY_FEATURES))
    metadata_df = _attach_axis_states(metadata_df)
    mode_rows: list[dict[str, Any]] = []
    axis_cols = [
        "noise_pressure_state",
        "trend_quality_state",
        "extension_pressure_state",
        "participation_quality_state",
        "reversal_pressure_state",
    ]
    for date_key, scoped in metadata_df.groupby("date_key"):
        row = {"date_key": str(date_key)}
        for axis_col in axis_cols:
            modes = scoped[axis_col].astype(str).mode()
            row[axis_col] = str(modes.iloc[0]) if not modes.empty else "unknown"
        mode_rows.append(row)
    return pd.DataFrame(mode_rows).sort_values("date_key").reset_index(drop=True)


def _axis_dependency_matrix(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    relations = [
        ("trend_quality_state", "noise_pressure_state", "trend weak should amplify noise dominance"),
        ("trend_quality_state", "extension_pressure_state", "trend quality should change how stretch translates into payoff"),
        ("noise_pressure_state", "extension_pressure_state", "noise should determine whether extension behaves as structure or failure"),
        ("extension_pressure_state", "participation_quality_state", "stretched states should need more participation confirmation"),
    ]
    rows: list[dict[str, Any]] = []
    for condition_axis, dependent_axis, implication in relations:
        base_dispersion = _state_metrics(train_df, dependent_axis)["between_state_expectancy_dispersion"]
        base_entropy = _state_metrics(train_df, dependent_axis)["within_state_path_entropy_mean"]
        base_retention = _oos_retention(train_df, oos_df, dependent_axis)
        for condition_state, train_scoped in train_df.groupby(condition_axis):
            oos_scoped = oos_df[oos_df[condition_axis].astype(str) == str(condition_state)]
            conditional_metrics = _state_metrics(train_scoped, dependent_axis)
            retention = _oos_retention(train_scoped, oos_scoped, dependent_axis) if not train_scoped.empty else 0.0
            strength = (
                conditional_metrics["between_state_expectancy_dispersion"]
                - base_dispersion
                + (base_entropy - conditional_metrics["within_state_path_entropy_mean"])
                + (retention - base_retention)
            )
            evidence = (
                f"dispersion_delta={conditional_metrics['between_state_expectancy_dispersion'] - base_dispersion:.3f}; "
                f"entropy_delta={base_entropy - conditional_metrics['within_state_path_entropy_mean']:.3f}; "
                f"retention_delta={retention - base_retention:.3f}"
            )
            rows.append(
                {
                    "condition_axis": condition_axis.replace("_state", ""),
                    "condition_state": str(condition_state),
                    "dependent_axis": dependent_axis.replace("_state", ""),
                    "dependency_strength": round(float(strength), 6),
                    "evidence": evidence,
                    "payoff_implication": implication,
                }
            )
    return pd.DataFrame(rows).sort_values(["condition_axis", "dependency_strength"], ascending=[True, False]).reset_index(drop=True)


def _state_candidates_long_form(candidate_name: str, train_df: pd.DataFrame, oos_df: pd.DataFrame, state_col: str, fold_map: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    raw_counts = train_df[f"raw_{state_col}"].astype(str).value_counts().to_dict() if f"raw_{state_col}" in train_df.columns else {}
    merged_parents = {raw_state: merged for raw_state, merged in fold_map.items() if str(raw_state) != str(merged)}
    states = sorted(set(train_df[state_col].astype(str)) | set(oos_df[state_col].astype(str)))
    for state in states:
        raw_children = [raw for raw, merged in fold_map.items() if str(merged) == state]
        construction_rule = raw_children[0] if raw_children else state
        rows.append(
            {
                "candidate": candidate_name,
                "state_label": state,
                "construction_rule": construction_rule,
                "train_trade_count": int((train_df[state_col].astype(str) == state).sum()),
                "oos_trade_count": int((oos_df[state_col].astype(str) == state).sum()),
                "auto_merged": bool(any(str(raw) != str(state) for raw in raw_children)),
                "parent_state_if_merged": state if state in merged_parents.values() else "",
            }
        )
    return pd.DataFrame(rows)


def _path_consistency_score(scoped: pd.DataFrame) -> tuple[float, str, float]:
    if scoped.empty:
        return 0.0, "unknown", 0.0
    path_dist = _distribution(scoped["path_type"], PATH_TYPES)
    dominant_path = max(path_dist.items(), key=lambda item: item[1])[0]
    dominant_share = float(path_dist.get(dominant_path, 0.0))
    entropy = float(_series_entropy(scoped["path_type"]))
    normalized_entropy = entropy / math.log(len(PATH_TYPES), 2) if len(PATH_TYPES) > 1 else 0.0
    realized_var = float(pd.to_numeric(scoped["realized_R"], errors="coerce").var(ddof=0))
    variance_component = 1.0 / (1.0 + max(realized_var, 0.0))
    score = (dominant_share + (1.0 - normalized_entropy) + variance_component) / 3.0
    return round(score, 6), dominant_path, round(dominant_share, 6)


def _state_behavior_validation(candidate_name: str, df: pd.DataFrame, state_col: str, scope_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for state_label, scoped in df.groupby(state_col):
        score, dominant_failure_mode, homogeneity = _path_consistency_score(scoped)
        rows.append(
            {
                "candidate": candidate_name,
                "state_label": str(state_label),
                "scope": scope_name,
                "trade_count": int(len(scoped)),
                "path_consistency_score": score,
                "dominant_failure_mode": dominant_failure_mode,
                "failure_mode_homogeneity": homogeneity,
                "follow_through_variance": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").var(ddof=0)), 6),
                "retrace_variance": round(float(pd.to_numeric(scoped["retrace_5d_pct"], errors="coerce").var(ddof=0)), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["candidate", "scope", "path_consistency_score"], ascending=[True, True, False]).reset_index(drop=True)


def _representative_daily_states(
    candidate_name: str,
    full_df: pd.DataFrame,
    state_col: str,
    metadata_daily_modes: pd.DataFrame,
    metadata_builder: Callable[[pd.Series], str],
    fold_map: dict[str, str],
) -> pd.DataFrame:
    trade_rows = []
    if not full_df.empty:
        date_col = "date_key" if "date_key" in full_df.columns else "entry_date"
        grouped = full_df.groupby(date_col)
        for date_key, scoped in grouped:
            mode = scoped[state_col].astype(str).mode()
            representative_state = str(mode.iloc[0]) if not mode.empty else "unknown"
            avg_payoff = float(pd.to_numeric(scoped["realized_R"], errors="coerce").mean())
            trade_rows.append({"date_key": str(date_key), "representative_state": representative_state, "avg_payoff": avg_payoff, "source": "trade"})
    trade_daily = pd.DataFrame(trade_rows)
    if metadata_daily_modes.empty:
        return trade_daily.sort_values("date_key").reset_index(drop=True)
    metadata_daily = metadata_daily_modes.copy()
    metadata_daily["representative_state"] = metadata_daily.apply(metadata_builder, axis=1).map(lambda value: fold_map.get(str(value), str(value)))
    metadata_daily["avg_payoff"] = math.nan
    metadata_daily["source"] = "metadata"
    combined = metadata_daily[["date_key", "representative_state", "avg_payoff", "source"]]
    if not trade_daily.empty:
        trade_lookup = trade_daily.set_index("date_key")
        combined = combined.set_index("date_key")
        combined.update(trade_lookup)
        combined = combined.reset_index()
    return combined.sort_values("date_key").reset_index(drop=True)


def _transition_rows(
    sequence_df: pd.DataFrame,
    candidate_name: str,
    scope_name: str,
    state_col: str,
    payoff_col: str,
) -> pd.DataFrame:
    if sequence_df.empty or len(sequence_df) < 2:
        return pd.DataFrame(columns=[
            "candidate",
            "transition_scope",
            "state_t",
            "state_t1",
            "transition_probability",
            "persistence_probability",
            "transition_instability",
            "avg_payoff_given_transition",
        ])
    rows: list[dict[str, Any]] = []
    sequence = sequence_df[[state_col, payoff_col]].copy()
    sequence["state_t"] = sequence[state_col].astype(str)
    sequence["state_t1"] = sequence[state_col].astype(str).shift(-1)
    sequence["payoff_next"] = pd.to_numeric(sequence[payoff_col], errors="coerce").shift(-1)
    sequence = sequence.dropna(subset=["state_t1"]).reset_index(drop=True)
    if sequence.empty:
        return pd.DataFrame()
    source_counts = sequence["state_t"].value_counts().to_dict()
    transitions = sequence.groupby(["state_t", "state_t1"], as_index=False).agg(
        transition_count=("state_t1", "size"),
        avg_payoff_given_transition=("payoff_next", "mean"),
    )
    persistence = sequence.assign(is_persist=lambda df: df["state_t"] == df["state_t1"]).groupby("state_t")["is_persist"].mean().to_dict()
    instability = {state: round(1.0 - float(prob), 6) for state, prob in persistence.items()}
    for record in transitions.to_dict("records"):
        state_t = str(record["state_t"])
        rows.append(
            {
                "candidate": candidate_name,
                "transition_scope": scope_name,
                "state_t": state_t,
                "state_t1": str(record["state_t1"]),
                "transition_probability": round(float(record["transition_count"]) / max(int(source_counts.get(state_t, 1)), 1), 6),
                "persistence_probability": round(float(persistence.get(state_t, 0.0)), 6),
                "transition_instability": round(float(instability.get(state_t, 0.0)), 6),
                "avg_payoff_given_transition": round(float(record["avg_payoff_given_transition"]), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["candidate", "transition_scope", "state_t", "state_t1"]).reset_index(drop=True)


def _trade_sequence_transitions(candidate_name: str, full_df: pd.DataFrame, state_col: str) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    if full_df.empty:
        return pd.DataFrame()
    for _, scoped in full_df.groupby(["scenario", "symbol"]):
        sorted_scoped = scoped.sort_values("entry_date").reset_index(drop=True)
        rows.append(_transition_rows(sorted_scoped, candidate_name, "trade_sequence", state_col, "realized_R"))
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    grouped = out.groupby(["candidate", "transition_scope", "state_t", "state_t1"], as_index=False).agg(
        transition_probability=("transition_probability", "mean"),
        persistence_probability=("persistence_probability", "mean"),
        transition_instability=("transition_instability", "mean"),
        avg_payoff_given_transition=("avg_payoff_given_transition", "mean"),
    )
    return grouped


def _day_sequence_transitions(
    candidate_name: str,
    full_df: pd.DataFrame,
    state_col: str,
    metadata_daily_modes: pd.DataFrame,
    metadata_builder: Callable[[pd.Series], str],
    fold_map: dict[str, str],
) -> pd.DataFrame:
    daily_states = _representative_daily_states(candidate_name, full_df, state_col, metadata_daily_modes, metadata_builder, fold_map)
    if daily_states.empty:
        return pd.DataFrame()
    return _transition_rows(daily_states.sort_values("date_key").reset_index(drop=True), candidate_name, "calendar_day", "representative_state", "avg_payoff")


def _final_decision(evaluation_df: pd.DataFrame, transition_df: pd.DataFrame) -> pd.DataFrame:
    base = evaluation_df[evaluation_df["candidate"] == "task_329_state_model"].iloc[0]
    contenders = evaluation_df[evaluation_df["candidate"].isin(["candidate_A", "candidate_B", "candidate_C"])].copy()
    transition_summary = transition_df.groupby("candidate", as_index=False).agg(
        mean_persistence_probability=("persistence_probability", "mean"),
        mean_transition_instability=("transition_instability", "mean"),
    )
    contenders = contenders.merge(transition_summary, on="candidate", how="left")
    contenders = contenders.fillna({"mean_persistence_probability": 0.0, "mean_transition_instability": 1.0})
    contenders["meets_rule"] = (
        (contenders["between_state_expectancy_dispersion"] > float(base["between_state_expectancy_dispersion"]))
        & (contenders["within_state_path_entropy_mean"] < float(base["within_state_path_entropy_mean"]))
        & (contenders["oos_linkage_retention"] > float(base["oos_linkage_retention"]))
        & (contenders["sparsity_risk"] <= float(base["sparsity_risk"]))
        & (contenders["mean_transition_instability"] <= float(transition_summary[transition_summary["candidate"] == "task_329_state_model"]["mean_transition_instability"].iloc[0]) if not transition_summary[transition_summary["candidate"] == "task_329_state_model"].empty else 1.0)
    )
    if not contenders.empty and contenders["meets_rule"].any():
        best = contenders[contenders["meets_rule"]].sort_values(
            ["oos_linkage_retention", "within_state_path_entropy_mean", "sparsity_risk"],
            ascending=[False, True, True],
        ).iloc[0]
        decision = "PROMOTE"
        rationale = f"{best['candidate']} improves separation, entropy, OOS retention, density, and transition stability versus Task 329"
    else:
        best = contenders.sort_values(
            ["oos_linkage_retention", "within_state_path_entropy_mean", "sparsity_risk"],
            ascending=[False, True, True],
        ).iloc[0]
        decision = "REJECT"
        rationale = f"{best['candidate']} is best available but does not satisfy all stability criteria versus Task 329"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "recommended_candidate": str(best["candidate"]),
                "decision_reason": rationale,
            }
        ]
    )


def _write_markdown(
    out_dir: Path,
    axis_df: pd.DataFrame,
    evaluation_df: pd.DataFrame,
    decision_df: pd.DataFrame,
    dependency_df: pd.DataFrame,
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
            row: list[str] = []
            for col in cols:
                value = record.get(col, "")
                if isinstance(value, float):
                    row.append("" if math.isnan(value) else f"{value:.6g}")
                else:
                    row.append(str(value))
            lines.append("| " + " | ".join(row) + " |")
        return lines

    decision = decision_df.iloc[0].to_dict() if not decision_df.empty else {}
    best_candidate = str(decision.get("recommended_candidate", "unknown"))
    lines = [
        "# Task 332: State Space Realignment",
        "",
        "## Core Answer",
        "",
        f"- Final decision: `{decision.get('decision', 'unknown')}`.",
        f"- Recommended candidate: `{best_candidate}`.",
        "- This report answers whether promoting noise to a primary axis and rebuilding the conditional state space improves breakout payoff alignment.",
        "",
        "## Axis Definitions",
        "",
    ]
    lines.extend(_fmt(axis_df))
    lines.extend(["", "## Candidate Evaluation", ""])
    lines.extend(_fmt(evaluation_df))
    lines.extend(["", "## Top Dependencies", ""])
    lines.extend(_fmt(dependency_df.head(8)))
    (out_dir / "task_332_final_recommendation.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 332: state space realignment.")
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

    metadata_daily_modes = _build_daily_metadata_axis_modes(base_dir, train_df)
    axis_df = _axis_definition_df()
    dependency_df = _axis_dependency_matrix(train_df, oos_df)

    task329_axes = ["extension_pressure", "trend_quality", "participation_quality"]
    task329_train_df = train_df.copy()
    task329_oos_df = oos_df.copy()
    task329_full_df = full_df.copy()
    task329_fold_map = _build_generic_fold_map(task329_train_df.apply(lambda row: "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in task329_axes), axis=1))
    for scoped_df in (task329_train_df, task329_oos_df, task329_full_df):
        raw_values = scoped_df.apply(lambda row: "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in task329_axes), axis=1)
        scoped_df["raw_task_329_state_model"] = raw_values
        scoped_df["task_329_state_model"] = raw_values.map(lambda value: task329_fold_map.get(str(value), str(value)))

    dense_parents = _dense_candidate_c_parents(train_df)
    candidate_specs = [
        ("candidate_A", _candidate_a_raw),
        ("candidate_B", _candidate_b_raw),
        ("candidate_C", _candidate_c_builder(dense_parents)),
    ]

    candidate_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]] = {}
    candidate_rows: list[pd.DataFrame] = []
    evaluation_rows: list[dict[str, Any]] = [
        {"candidate": "old_regime", **_state_model_summary(train_df, oos_df, "regime_state")},
        {"candidate": "task_329_state_model", **_state_model_summary(task329_train_df, task329_oos_df, "task_329_state_model")},
    ]
    behavior_rows: list[pd.DataFrame] = []
    transition_rows: list[pd.DataFrame] = []

    behavior_rows.extend(
        [
            _state_behavior_validation("task_329_state_model", task329_train_df, "task_329_state_model", "train"),
            _state_behavior_validation("task_329_state_model", task329_oos_df, "task_329_state_model", "anchored_oos"),
            _state_behavior_validation("task_329_state_model", task329_full_df, "task_329_state_model", "full_period"),
        ]
    )
    transition_rows.extend(
        [
            _day_sequence_transitions("task_329_state_model", task329_full_df, "task_329_state_model", metadata_daily_modes, lambda row: "|".join(f"{axis}:{row.get(f'{axis}_state', 'unknown')}" for axis in task329_axes), task329_fold_map),
            _trade_sequence_transitions("task_329_state_model", task329_full_df, "task_329_state_model"),
        ]
    )

    for candidate_name, builder in candidate_specs:
        state_col = f"{candidate_name}_state"
        cand_train_df, cand_oos_df, cand_full_df, fold_map = _apply_candidate_state(train_df, oos_df, full_df, state_col, builder)
        candidate_frames[candidate_name] = (cand_train_df, cand_oos_df, cand_full_df, fold_map)
        candidate_rows.append(_state_candidates_long_form(candidate_name, cand_train_df, cand_oos_df, state_col, fold_map))
        evaluation_rows.append({"candidate": candidate_name, **_state_model_summary(cand_train_df, cand_oos_df, state_col)})
        behavior_rows.extend(
            [
                _state_behavior_validation(candidate_name, cand_train_df, state_col, "train"),
                _state_behavior_validation(candidate_name, cand_oos_df, state_col, "anchored_oos"),
                _state_behavior_validation(candidate_name, cand_full_df, state_col, "full_period"),
            ]
        )
        transition_rows.extend(
            [
                _day_sequence_transitions(candidate_name, cand_full_df, state_col, metadata_daily_modes, builder, fold_map),
                _trade_sequence_transitions(candidate_name, cand_full_df, state_col),
            ]
        )

    state_candidates_df = pd.concat(candidate_rows, ignore_index=True) if candidate_rows else pd.DataFrame()
    evaluation_df = pd.DataFrame(evaluation_rows)
    behavior_df = pd.concat(behavior_rows, ignore_index=True) if behavior_rows else pd.DataFrame()
    transition_df = pd.concat([df for df in transition_rows if not df.empty], ignore_index=True) if transition_rows else pd.DataFrame()
    decision_df = _final_decision(evaluation_df, transition_df)

    axis_df.to_csv(out_dir / "task_332_axis_definition.csv", index=False)
    dependency_df.to_csv(out_dir / "task_332_axis_dependency_matrix.csv", index=False)
    state_candidates_df.to_csv(out_dir / "task_332_state_candidates.csv", index=False)
    evaluation_df.to_csv(out_dir / "task_332_state_model_evaluation.csv", index=False)
    behavior_df.to_csv(out_dir / "task_332_state_behavior_validation.csv", index=False)
    transition_df.to_csv(out_dir / "task_332_state_transition_matrix.csv", index=False)
    _write_markdown(out_dir, axis_df, evaluation_df, decision_df, dependency_df)


if __name__ == "__main__":
    main()
