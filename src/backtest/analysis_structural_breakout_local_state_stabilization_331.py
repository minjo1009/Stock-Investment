from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    DEFAULT_BASE_DIR,
    RANKED_INPUT,
    _labeled_trade_frames,
    _series_entropy,
)
from src.backtest.analysis_structural_breakout_state_model_stabilization_330 import (
    DEFAULT_OUT_DIR as TASK330_OUT_DIR,
    _build_current_state_frames,
    _build_generic_fold_map,
    _feature_band_mix_shift,
    _missing_axis_value,
    _path_mix_string,
    _select_axes,
    _state_linkage_instability,
    _state_model_summary,
    _strong_trend_subtype,
    _vulnerable_state_buckets,
)
from src.backtest.analysis_structural_breakout_state_model_redesign_329 import _attach_axis_states


DEFAULT_OUT_DIR = Path("docs/reports/task_331_local_state_stabilization")
TARGET_VULNERABLE_STATES = [
    "extension_pressure:medium|trend_quality:neutral|participation_quality:narrow",
    "extension_pressure:medium|trend_quality:neutral|participation_quality:broad",
    "extension_pressure:medium|trend_quality:strong|participation_quality:broad",
]
SPARSE_OOS_MIN_COUNT = 5


def _split_columns() -> list[str]:
    return [
        "noise_pressure_state",
        "reversal_pressure_state",
        "breakout_strength_pct_band",
        "ret_20d_pre_band",
        "strong_trend_subtype",
    ]


def _ensure_strong_subtype(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "strong_trend_subtype" not in out.columns:
        out["strong_trend_subtype"] = out.apply(_strong_trend_subtype, axis=1)
    return out


def _bucket_metrics(train_scoped: pd.DataFrame, oos_scoped: pd.DataFrame) -> dict[str, float]:
    train_expectancy = float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").mean()) if not train_scoped.empty else 0.0
    oos_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
    retention = (oos_expectancy / train_expectancy) if abs(train_expectancy) > 1e-9 else 0.0
    failure_share = 0.0
    if not oos_scoped.empty:
        failure_share = float((oos_scoped["path_type"].astype(str) == "early_failure").mean())
    return {
        "train_trade_count": int(len(train_scoped)),
        "oos_trade_count": int(len(oos_scoped)),
        "train_expectancy_r": round(train_expectancy, 6),
        "oos_expectancy_r": round(oos_expectancy, 6),
        "linkage_retention": round(retention, 6),
        "path_entropy": round(_series_entropy(oos_scoped["path_type"]) if not oos_scoped.empty else _series_entropy(train_scoped["path_type"]), 6),
        "realized_r_variance": round(
            float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").var(ddof=0))
            if not oos_scoped.empty
            else float(pd.to_numeric(train_scoped["realized_R"], errors="coerce").var(ddof=0)),
            6,
        ),
        "failure_mode_concentration": round(failure_share, 6),
    }


def _evaluate_bucket_split(
    train_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    target_state: str,
    split_col: str,
) -> dict[str, Any]:
    train_scoped = train_df[train_df["proposed_state_model"].astype(str) == target_state]
    oos_scoped = oos_df[oos_df["proposed_state_model"].astype(str) == target_state]
    before = _bucket_metrics(train_scoped, oos_scoped)
    sub_labels = sorted(set(train_scoped[split_col].astype(str)) | set(oos_scoped[split_col].astype(str)))
    child_rows: list[dict[str, Any]] = []
    for label in sub_labels:
        train_child = train_scoped[train_scoped[split_col].astype(str) == label]
        oos_child = oos_scoped[oos_scoped[split_col].astype(str) == label]
        metrics = _bucket_metrics(train_child, oos_child)
        child_rows.append(
            {
                "child_label": str(label),
                **metrics,
            }
        )
    child_df = pd.DataFrame(child_rows)
    after_entropy = float(pd.to_numeric(child_df["path_entropy"], errors="coerce").fillna(0.0).mean()) if not child_df.empty else before["path_entropy"]
    after_variance = float(pd.to_numeric(child_df["realized_r_variance"], errors="coerce").fillna(0.0).mean()) if not child_df.empty else before["realized_r_variance"]
    after_retention = float(pd.to_numeric(child_df["linkage_retention"], errors="coerce").fillna(0.0).mean()) if not child_df.empty else before["linkage_retention"]
    after_failure = float(pd.to_numeric(child_df["failure_mode_concentration"], errors="coerce").fillna(0.0).max()) if not child_df.empty else before["failure_mode_concentration"]
    sparse_children = int(((pd.to_numeric(child_df["train_trade_count"], errors="coerce") < 25) | (pd.to_numeric(child_df["oos_trade_count"], errors="coerce") < SPARSE_OOS_MIN_COUNT)).sum()) if not child_df.empty else 0
    score = (
        (before["path_entropy"] - after_entropy)
        + (before["realized_r_variance"] - after_variance)
        + (after_retention - before["linkage_retention"])
        + (before["failure_mode_concentration"] - after_failure)
        - 0.25 * sparse_children
    )
    return {
        "target_state": target_state,
        "split_condition": split_col,
        "before_entropy": round(before["path_entropy"], 6),
        "after_entropy": round(after_entropy, 6),
        "before_realized_r_variance": round(before["realized_r_variance"], 6),
        "after_realized_r_variance": round(after_variance, 6),
        "before_retention": round(before["linkage_retention"], 6),
        "after_retention": round(after_retention, 6),
        "before_failure_mode_concentration": round(before["failure_mode_concentration"], 6),
        "after_failure_mode_concentration": round(after_failure, 6),
        "sparse_child_count": sparse_children,
        "split_score": round(score, 6),
    }


def _vulnerable_bucket_split_analysis(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for target_state in TARGET_VULNERABLE_STATES:
        if target_state not in set(train_df["proposed_state_model"].astype(str)) and target_state not in set(oos_df["proposed_state_model"].astype(str)):
            continue
        for split_col in _split_columns():
            rows.append(_evaluate_bucket_split(train_df, oos_df, target_state, split_col))
    return pd.DataFrame(rows).sort_values(["target_state", "split_score"], ascending=[True, False]).reset_index(drop=True)


def _best_split_plan(split_df: pd.DataFrame) -> dict[str, str]:
    plan: dict[str, str] = {}
    if split_df.empty:
        return plan
    for target_state, scoped in split_df.groupby("target_state"):
        best = scoped.sort_values(["split_score", "after_retention"], ascending=[False, False]).iloc[0]
        plan[str(target_state)] = str(best["split_condition"])
    return plan


def _apply_local_split(df: pd.DataFrame, split_plan: dict[str, str], include_noise_on_targets: bool = False) -> pd.DataFrame:
    out = df.copy()

    def _label(row: pd.Series) -> str:
        state = str(row.get("proposed_state_model", "unknown"))
        if state in split_plan:
            split_col = split_plan[state]
            state = f"{state}|local:{split_col}={row.get(split_col, 'unknown')}"
        if include_noise_on_targets and str(row.get("proposed_state_model", "unknown")) in split_plan:
            state = f"{state}|noise:{row.get('noise_pressure_state', 'unknown')}"
        return state

    raw_labels = out.apply(_label, axis=1)
    mapping = _build_generic_fold_map(raw_labels)
    out["proposed_state_model"] = raw_labels.map(lambda value: mapping.get(str(value), str(value)))
    return out


def _secondary_noise_conditioning(
    base_train_df: pd.DataFrame,
    base_oos_df: pd.DataFrame,
    split_plan: dict[str, str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    split_train_df = _apply_local_split(base_train_df, split_plan, include_noise_on_targets=False)
    split_oos_df = _apply_local_split(base_oos_df, split_plan, include_noise_on_targets=False)
    noise_train_df = _apply_local_split(base_train_df, split_plan, include_noise_on_targets=True)
    noise_oos_df = _apply_local_split(base_oos_df, split_plan, include_noise_on_targets=True)
    for target_state in split_plan:
        before_train = split_train_df[split_train_df["proposed_state_model"].astype(str).str.startswith(target_state)]
        before_oos = split_oos_df[split_oos_df["proposed_state_model"].astype(str).str.startswith(target_state)]
        after_train = noise_train_df[noise_train_df["proposed_state_model"].astype(str).str.startswith(target_state)]
        after_oos = noise_oos_df[noise_oos_df["proposed_state_model"].astype(str).str.startswith(target_state)]
        before_metrics = _bucket_metrics(before_train, before_oos)
        after_metrics = _bucket_metrics(after_train, after_oos)
        before_sparsity = float(
            ((before_train["proposed_state_model"].astype(str).value_counts() < 25).sum() if not before_train.empty else 0)
            + ((before_oos["proposed_state_model"].astype(str).value_counts() < SPARSE_OOS_MIN_COUNT).sum() if not before_oos.empty else 0)
        )
        after_sparsity = float(
            ((after_train["proposed_state_model"].astype(str).value_counts() < 25).sum() if not after_train.empty else 0)
            + ((after_oos["proposed_state_model"].astype(str).value_counts() < SPARSE_OOS_MIN_COUNT).sum() if not after_oos.empty else 0)
        )
        rows.append(
            {
                "target_state": target_state,
                "before_entropy": before_metrics["path_entropy"],
                "after_entropy": after_metrics["path_entropy"],
                "before_retention": before_metrics["linkage_retention"],
                "after_retention": after_metrics["linkage_retention"],
                "before_sparsity": round(before_sparsity, 6),
                "after_sparsity": round(after_sparsity, 6),
            }
        )
    return pd.DataFrame(rows).sort_values("target_state").reset_index(drop=True)


def _analyze_sparse_states(train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    states = sorted(set(train_df["proposed_state_model"].astype(str)) | set(oos_df["proposed_state_model"].astype(str)))
    rows: list[dict[str, Any]] = []
    for state in states:
        train_scoped = train_df[train_df["proposed_state_model"].astype(str) == state]
        oos_scoped = oos_df[oos_df["proposed_state_model"].astype(str) == state]
        train_count = int(len(train_scoped))
        oos_count = int(len(oos_scoped))
        if train_count >= 25 and oos_count >= SPARSE_OOS_MIN_COUNT:
            continue
        merge_candidate = "|".join(str(state).split("|")[:-1]) or str(state)
        parent_train = train_df[train_df["proposed_state_model"].astype(str) == merge_candidate]
        parent_oos = oos_df[oos_df["proposed_state_model"].astype(str) == merge_candidate]
        child_expectancy = float(pd.to_numeric(oos_scoped["realized_R"], errors="coerce").mean()) if not oos_scoped.empty else 0.0
        parent_expectancy = float(pd.to_numeric(parent_oos["realized_R"], errors="coerce").mean()) if not parent_oos.empty else 0.0
        separation_benefit = abs(child_expectancy - parent_expectancy)
        rows.append(
            {
                "state": state,
                "train_trade_count": train_count,
                "oos_trade_count": oos_count,
                "expectancy_r": round(child_expectancy, 6),
                "separation_benefit": round(separation_benefit, 6),
                "merge_candidate": merge_candidate,
                "merge_justification": "merge" if separation_benefit < 0.25 or oos_count == 0 else "keep_if_structurally_distinct",
            }
        )
    return pd.DataFrame(rows).sort_values(["oos_trade_count", "separation_benefit"], ascending=[True, True]).reset_index(drop=True)


def _merge_sparse_states(df: pd.DataFrame, sparse_df: pd.DataFrame) -> pd.DataFrame:
    merge_map = {
        str(row["state"]): str(row["merge_candidate"])
        for row in sparse_df.to_dict("records")
        if str(row.get("merge_justification", "")) == "merge"
    }
    out = df.copy()
    out["proposed_state_model"] = out["proposed_state_model"].astype(str).map(lambda value: merge_map.get(str(value), str(value)))
    return out


def _comparison_rows(base_train_df: pd.DataFrame, base_oos_df: pd.DataFrame, split_plan: dict[str, str]) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.DataFrame]]]:
    candidate_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    candidate_frames["current_task_329"] = (base_train_df, base_oos_df)
    local_a_train = _apply_local_split(base_train_df, split_plan, include_noise_on_targets=False)
    local_a_oos = _apply_local_split(base_oos_df, split_plan, include_noise_on_targets=False)
    candidate_frames["local_A"] = (local_a_train, local_a_oos)
    local_b_train = _apply_local_split(base_train_df, split_plan, include_noise_on_targets=True)
    local_b_oos = _apply_local_split(base_oos_df, split_plan, include_noise_on_targets=True)
    candidate_frames["local_B"] = (local_b_train, local_b_oos)
    sparse_df = _analyze_sparse_states(local_b_train, local_b_oos)
    local_c_train = _merge_sparse_states(local_b_train, sparse_df)
    local_c_oos = _merge_sparse_states(local_b_oos, sparse_df)
    candidate_frames["local_C"] = (local_c_train, local_c_oos)

    descriptions = {
        "current_task_329": "current Task 329 base model",
        "local_A": "vulnerable bucket split only",
        "local_B": "vulnerable bucket split + local noise conditioning",
        "local_C": "local_B + sparse bucket merge",
    }
    rows: list[dict[str, Any]] = []
    for candidate, (train_df, oos_df) in candidate_frames.items():
        rows.append({"candidate": candidate, "description": descriptions[candidate], **_state_model_summary(train_df, oos_df)})
    return pd.DataFrame(rows), candidate_frames


def _local_revision_plan(split_plan: dict[str, str], noise_df: pd.DataFrame, sparse_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    priority = 1
    noise_targets = set(noise_df[noise_df["after_retention"] > noise_df["before_retention"]]["target_state"].astype(str)) if not noise_df.empty else set()
    for target_state, split_col in split_plan.items():
        rows.append(
            {
                "revision_id": f"LR{priority}",
                "target_state": target_state,
                "local_change": f"split_by_{split_col}",
                "rationale": "best local split by entropy/variance/retention score",
                "expected_benefit": "reduce internal contradiction inside vulnerable bucket",
                "priority": priority,
            }
        )
        priority += 1
        if target_state in noise_targets:
            rows.append(
                {
                    "revision_id": f"LR{priority}",
                    "target_state": target_state,
                    "local_change": "add_local_noise_pressure_conditioning",
                    "rationale": "noise conditioning improved local retention",
                    "expected_benefit": "improve OOS robustness without full state rebuild",
                    "priority": priority,
                }
            )
            priority += 1
    for row in sparse_df.to_dict("records"):
        if str(row.get("merge_justification", "")) != "merge":
            continue
        rows.append(
            {
                "revision_id": f"LR{priority}",
                "target_state": str(row["state"]),
                "local_change": f"merge_into_{row['merge_candidate']}",
                "rationale": "sparse local split with low separation benefit",
                "expected_benefit": "reduce state explosion and sample sparsity",
                "priority": priority,
            }
        )
        priority += 1
    return pd.DataFrame(rows).sort_values("priority").reset_index(drop=True)


def _decision_df(comparison_df: pd.DataFrame) -> pd.DataFrame:
    current = comparison_df[comparison_df["candidate"] == "current_task_329"].iloc[0]
    refined = comparison_df[comparison_df["candidate"] != "current_task_329"].copy()
    refined["retention_rank_metric"] = refined["oos_linkage_retention"].astype(float)
    best = refined.sort_values(
        ["retention_rank_metric", "vulnerable_bucket_concentration", "sparsity_risk", "within_state_path_entropy_mean"],
        ascending=[False, True, True, True],
    ).iloc[0]
    retention_improved = float(best["oos_linkage_retention"]) > float(current["oos_linkage_retention"])
    concentration_improved = float(best["vulnerable_bucket_concentration"]) < float(current["vulnerable_bucket_concentration"])
    sparsity_ok = float(best["sparsity_risk"]) <= float(current["sparsity_risk"]) + 0.10
    if retention_improved and concentration_improved and sparsity_ok:
        decision = "apply_limited_local_stabilization"
        rationale = f"{best['candidate']} improves retention and vulnerable concentration with acceptable sparsity"
    elif not retention_improved:
        decision = "keep_task_329_state_model_unchanged"
        rationale = "local candidates do not improve OOS retention enough"
    else:
        decision = "current_state_model_requires_broader_rebuild"
        rationale = f"{best['candidate']} only improves metrics by increasing sparsity too much"
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
    decision_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    revision_df: pd.DataFrame,
    vulnerable_df: pd.DataFrame,
) -> None:
    def _fmt(df: pd.DataFrame) -> list[str]:
        if df.empty:
            return ["_No rows_"]
        cols = [str(column) for column in df.columns]
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
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
    lines = [
        "# Task 331: Local State Stabilization",
        "",
        "## Core Answer",
        "",
        f"- Decision: `{decision.get('decision', 'unknown')}`.",
        f"- Recommended candidate: `{decision.get('recommended_candidate', 'unknown')}`.",
        "- This report identifies which vulnerable states should be refined first and whether local stabilization can improve OOS robustness without rebuilding the whole state model.",
        "",
        "## Top Vulnerable States",
        "",
    ]
    lines.extend(_fmt(vulnerable_df.head(5)[["proposed_state_model", "oos_expectancy_r", "expectancy_delta", "contribution_to_oos_underperformance"]]))
    lines.extend(["", "## Candidate Comparison", ""])
    lines.extend(_fmt(comparison_df))
    lines.extend(["", "## Local Revision Plan", ""])
    lines.extend(_fmt(revision_df))
    (out_dir / "task_331_local_state_stabilization.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 331: local breakout state stabilization.")
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
    train_df = _ensure_strong_subtype(_attach_axis_states(train_df))
    oos_df = _ensure_strong_subtype(_attach_axis_states(oos_df))
    full_df = _ensure_strong_subtype(_attach_axis_states(full_df))

    selected_axes, base_train_df, base_oos_df, _ = _build_current_state_frames(train_df, oos_df, full_df)
    base_train_df = _ensure_strong_subtype(base_train_df)
    base_oos_df = _ensure_strong_subtype(base_oos_df)

    vulnerable_df = _vulnerable_state_buckets(_state_linkage_instability(base_train_df, base_oos_df))
    split_df = _vulnerable_bucket_split_analysis(base_train_df, base_oos_df)
    split_plan = _best_split_plan(split_df)
    noise_df = _secondary_noise_conditioning(base_train_df, base_oos_df, split_plan)
    comparison_df, frames = _comparison_rows(base_train_df, base_oos_df, split_plan)
    local_b_train, local_b_oos = frames["local_B"]
    sparse_df = _analyze_sparse_states(local_b_train, local_b_oos)
    revision_df = _local_revision_plan(split_plan, noise_df, sparse_df)
    decision_df = _decision_df(comparison_df)

    split_df.to_csv(out_dir / "task_331_vulnerable_bucket_split_analysis.csv", index=False)
    noise_df.to_csv(out_dir / "task_331_secondary_noise_conditioning.csv", index=False)
    sparse_df.to_csv(out_dir / "task_331_sparse_state_merge_analysis.csv", index=False)
    comparison_df.to_csv(out_dir / "task_331_local_stabilization_comparison.csv", index=False)
    revision_df.to_csv(out_dir / "task_331_local_revision_plan.csv", index=False)
    decision_df.to_csv(out_dir / "task_331_local_stabilization_decision.csv", index=False)
    _write_markdown(out_dir, decision_df, comparison_df, revision_df, vulnerable_df)


if __name__ == "__main__":
    main()
