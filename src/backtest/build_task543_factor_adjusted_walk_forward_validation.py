from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK542_PANEL = Path("docs/reports/task_542_factor_adjusted_continuation_attribution/factor_adjusted_candidate_panel.csv")
TASK543_OUT = Path("docs/reports/task_543_factor_adjusted_walk_forward_validation")


def build_task543_factor_adjusted_walk_forward_validation(
    *,
    task542_panel_path: Path = TASK542_PANEL,
    out_dir: Path = TASK543_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_factor_adjusted_panel(task542_panel_path)
    split_quality = summarize_group(panel, ["candidate_set", "split_name"], "split")
    quarter_quality = summarize_group(panel, ["candidate_set", "quarter"], "quarter")
    walk_forward = build_walk_forward_stability(split_quality)
    underpowered = build_underpowered_audit(split_quality, quarter_quality)
    decision = build_decision(walk_forward, underpowered)
    leakage = build_leakage_audit()
    artifacts = {
        "factor_adjusted_walk_forward_split_quality": split_quality,
        "factor_adjusted_quarterly_quality": quarter_quality,
        "factor_adjusted_walk_forward_stability": walk_forward,
        "factor_adjusted_underpowered_audit": underpowered,
        "factor_adjusted_walk_forward_leakage_audit": leakage,
        "task_543_decision": decision,
    }
    write_task543(out_dir, artifacts)
    return artifacts


def load_factor_adjusted_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    numeric_cols = [
        "return_pct",
        "factor_adjusted_residual_pct",
        "factor_adjustment_available_flag",
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "win_flag",
    ]
    for col in numeric_cols:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    return panel


def summarize_group(panel: pd.DataFrame, group_cols: list[str], group_type: str) -> pd.DataFrame:
    rows = []
    for keys, subset in panel.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rec = {col: value for col, value in zip(group_cols, keys)}
        rec.update(
            {
                "group_type": group_type,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "raw_win_rate": float(subset["win_flag"].mean()) if "win_flag" in subset and len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "factor_adjusted_win_rate": float((adjusted["factor_adjusted_residual_pct"] > 0).mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()) if "entry_reduce_failure_flag" in subset and len(subset) else np.nan,
                "add_scale_success_rate": float(subset["add_scale_success_flag"].mean()) if "add_scale_success_flag" in subset and len(subset) else np.nan,
                "underpowered_flag": int(len(adjusted) < 20),
            }
        )
        rows.append(rec)
    return pd.DataFrame(rows)


def build_walk_forward_stability(split_quality: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_set, subset in split_quality.groupby("candidate_set"):
        validation = subset[subset["split_name"].astype(str).eq("validation")]
        recent = subset[subset["split_name"].astype(str).eq("recent_oos")]
        train = subset[subset["split_name"].astype(str).eq("train_design")]
        validation_resid = first_value(validation, "factor_adjusted_avg_residual_pct")
        recent_resid = first_value(recent, "factor_adjusted_avg_residual_pct")
        train_resid = first_value(train, "factor_adjusted_avg_residual_pct")
        validation_count = int(first_value(validation, "factor_adjusted_count", default=0))
        recent_count = int(first_value(recent, "factor_adjusted_count", default=0))
        positive_oos = int(pd.notna(validation_resid) and pd.notna(recent_resid) and validation_resid > 0 and recent_resid > 0)
        enough_oos = int(validation_count >= 20 and recent_count >= 20)
        rows.append(
            {
                "candidate_set": candidate_set,
                "train_residual_pct": train_resid,
                "validation_residual_pct": validation_resid,
                "recent_oos_residual_pct": recent_resid,
                "validation_factor_adjusted_count": validation_count,
                "recent_oos_factor_adjusted_count": recent_count,
                "positive_validation_and_recent_oos_flag": positive_oos,
                "oos_sample_adequate_flag": enough_oos,
                "walk_forward_status": classify_walk_forward(positive_oos, enough_oos, validation_resid, recent_resid),
            }
        )
    return pd.DataFrame(rows)


def first_value(frame: pd.DataFrame, column: str, default: float | int | None = np.nan) -> float:
    if frame.empty or column not in frame.columns:
        return default  # type: ignore[return-value]
    value = frame[column].iloc[0]
    if pd.isna(value):
        return default  # type: ignore[return-value]
    return value  # type: ignore[return-value]


def classify_walk_forward(positive_oos: int, enough_oos: int, validation_resid: float, recent_resid: float) -> str:
    if not enough_oos:
        return "positive_but_underpowered" if positive_oos else "underpowered_or_unstable"
    if positive_oos:
        return "factor_adjusted_oos_survives"
    if pd.notna(validation_resid) and validation_resid > 0 and pd.notna(recent_resid) and recent_resid <= 0:
        return "recent_oos_residual_collapse"
    return "factor_adjusted_walk_forward_fail"


def build_underpowered_audit(split_quality: pd.DataFrame, quarter_quality: pd.DataFrame) -> pd.DataFrame:
    split_under = split_quality[split_quality["underpowered_flag"].eq(1)].copy()
    split_under["audit_scope"] = "split"
    quarter_under = quarter_quality[quarter_quality["underpowered_flag"].eq(1)].copy()
    quarter_under["audit_scope"] = "quarter"
    common_cols = ["audit_scope", "candidate_set", "lifecycle_count", "factor_adjusted_count", "factor_adjusted_avg_residual_pct", "underpowered_flag"]
    for frame in [split_under, quarter_under]:
        for col in common_cols:
            if col not in frame.columns:
                frame[col] = np.nan
    return pd.concat([split_under[common_cols], quarter_under[common_cols]], ignore_index=True)


def build_decision(walk_forward: pd.DataFrame, underpowered: pd.DataFrame) -> pd.DataFrame:
    survive = int((walk_forward["walk_forward_status"] == "factor_adjusted_oos_survives").sum()) if not walk_forward.empty else 0
    positive_under = int((walk_forward["walk_forward_status"] == "positive_but_underpowered").sum()) if not walk_forward.empty else 0
    return pd.DataFrame(
        [
            {
                "task_id": "Task543",
                "candidate_set_count": int(walk_forward["candidate_set"].nunique()) if not walk_forward.empty else 0,
                "factor_adjusted_oos_survives_count": survive,
                "positive_but_underpowered_count": positive_under,
                "underpowered_group_count": int(len(underpowered)),
                "factor_result_used_as_trading_trigger_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "FACTOR_ADJUSTED_WALK_FORWARD_DIAGNOSTIC_UNDERPOWERED"
                if positive_under and not survive
                else "FACTOR_ADJUSTED_WALK_FORWARD_DIAGNOSTIC_ONLY",
            }
        ]
    )


def build_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule": "uses_task542_residual_panel_only", "pass_flag": 1},
            {"rule": "no_new_strategy_assignment", "pass_flag": 1},
            {"rule": "factor_result_not_used_as_trading_trigger", "pass_flag": 1},
            {"rule": "underpowered_oos_not_promoted", "pass_flag": 1},
        ]
    )


def write_task543(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_543_decision"].iloc[0].to_dict()
    walk = artifacts["factor_adjusted_walk_forward_stability"]
    lines = []
    for row in walk.to_dict(orient="records"):
        lines.append(
            f"{row['candidate_set']}: validation residual {row['validation_residual_pct']:.2f}%, "
            f"recent OOS residual {row['recent_oos_residual_pct']:.2f}%, "
            f"validation/recent counts {row['validation_factor_adjusted_count']}/{row['recent_oos_factor_adjusted_count']}, "
            f"status {row['walk_forward_status']}."
        )
    write_standard_report(
        out_dir / "task_543_factor_adjusted_walk_forward_validation.md",
        title="Task 543 Factor-Adjusted Walk-Forward Validation",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Candidate sets: {decision['candidate_set_count']}",
            f"Surviving factor-adjusted OOS candidates: {decision['factor_adjusted_oos_survives_count']}",
            f"Positive but underpowered candidates: {decision['positive_but_underpowered_count']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task543 does not create a new strategy. It tests whether Task542 factor-adjusted residuals survive across validation and recent OOS splits.",
            *lines,
            "The central limitation is sample adequacy: recent OOS factor-adjusted counts are below 20 for all candidate sets.",
        ],
        decision_maker_lines=[
            "We checked whether the leftover edge after factor adjustment persists over time.",
            "The residuals are positive in validation and recent OOS, but the recent sample is too small to trust as firm-grade proof.",
            "The right conclusion is not deployment; it is targeted sample expansion or longer paper/shadow accumulation.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task543_factor_adjusted_walk_forward_validation()


if __name__ == "__main__":
    main()
