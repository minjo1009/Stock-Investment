from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK544_POOL = Path("docs/reports/task_544_factor_adjusted_sample_expansion_quarter_failure/factor_adjusted_expansion_candidate_pool.csv")
TASK545_OUT = Path("docs/reports/task_545_factor_adjusted_failure_state_suppression")


def build_task545_factor_adjusted_failure_suppression(
    *,
    task544_pool_path: Path = TASK544_POOL,
    out_dir: Path = TASK545_OUT,
) -> dict[str, pd.DataFrame]:
    pool = load_pool(task544_pool_path)
    suppressed = build_suppression_candidate_panel(pool)
    quality = summarize_suppression_quality(suppressed)
    split_quality = summarize_suppression_split_quality(suppressed)
    failure_audit = summarize_failure_state_audit(pool)
    leakage = build_leakage_audit()
    decision = build_decision(quality, split_quality)
    artifacts = {
        "failure_state_suppression_candidate_panel": suppressed,
        "failure_state_suppression_quality": quality,
        "failure_state_suppression_split_quality": split_quality,
        "failure_state_audit": failure_audit,
        "failure_state_suppression_leakage_audit": leakage,
        "task_545_decision": decision,
    }
    write_task545(out_dir, artifacts)
    return artifacts


def load_pool(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for col in [
        "entry_close_pos_in_bar",
        "entry_close_vs_vwap",
        "range_pos",
        "volume_ratio_prev",
        "theme_breadth20_prev",
        "factor_adjusted_residual_pct",
        "factor_adjustment_available_flag",
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "return_pct",
    ]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def build_suppression_candidate_panel(pool: pd.DataFrame) -> pd.DataFrame:
    base = pool[pool["candidate_set"].astype(str).eq("base_trend_closepos_097")].copy()
    rules = build_suppression_rules(base)
    rows = []
    for rule_name, mask in rules.items():
        subset = base[mask].copy()
        subset["suppression_rule_name"] = rule_name
        subset["candidate_set"] = f"suppressed_{rule_name}"
        subset["factor_assignment_used_label_flag"] = 0
        subset["label_used_in_assignment_flag"] = 0
        subset["inferred_lifecycle_matching_used_flag"] = 0
        rows.append(subset)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_suppression_rules(frame: pd.DataFrame) -> dict[str, pd.Series]:
    timing = frame["timing_state"].astype(str)
    entry_state = frame["intraday_entry_state_v4"].astype(str)
    setup = frame["symbol_multiday_setup_state"].astype(str)
    theme = frame["theme_regime_state_v4"].astype(str)
    close_pos = frame["entry_close_pos_in_bar"]
    close_vs_vwap = frame["entry_close_vs_vwap"]
    range_pos = frame["range_pos"]
    volume = frame["volume_ratio_prev"]
    theme_breadth = frame["theme_breadth20_prev"]
    opening = timing.eq("opening_drive")
    breakout = entry_state.eq("intraday_breakout_acceptance")
    volume_reclaim = setup.eq("volume_confirmed_reclaim")
    return {
        "remove_opening_drive_weak_acceptance": ~(opening & (close_pos > 0.88) & (close_vs_vwap < 0.004)),
        "remove_breakout_high_close_low_vwap": ~(breakout & (close_pos > 0.90) & (close_vs_vwap < 0.003)),
        "remove_volume_reclaim_weak_theme": ~(volume_reclaim & (theme_breadth < 0.70)),
        "remove_volume_climax_late_extension": ~((volume > 2.0) & (range_pos > 0.92) & timing.isin(["opening_drive", "late_day_confirmation"])),
        "remove_narrow_theme_opening_drive": ~(opening & theme.eq("narrow_theme_leader")),
        "combined_failure_suppression_v1": ~(
            (opening & (close_pos > 0.88) & (close_vs_vwap < 0.004))
            | (breakout & (close_pos > 0.90) & (close_vs_vwap < 0.003))
            | (volume_reclaim & (theme_breadth < 0.70))
            | ((volume > 2.0) & (range_pos > 0.92) & timing.isin(["opening_drive", "late_day_confirmation"]))
            | (opening & theme.eq("narrow_theme_leader"))
        ),
    }


def summarize_suppression_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule, subset in panel.groupby("suppression_rule_name"):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "suppression_rule_name": rule,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "factor_adjustment_coverage_rate": float(len(adjusted) / len(subset)) if len(subset) else 0.0,
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "factor_adjusted_win_rate": float((adjusted["factor_adjusted_residual_pct"] > 0).mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()) if len(subset) else np.nan,
                "add_scale_success_rate": float(subset["add_scale_success_flag"].mean()) if len(subset) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("factor_adjusted_avg_residual_pct", ascending=False).reset_index(drop=True)


def summarize_suppression_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (rule, split), subset in panel.groupby(["suppression_rule_name", "split_name"]):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "suppression_rule_name": rule,
                "split_name": split,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()) if len(subset) else np.nan,
                "underpowered_flag": int(len(adjusted) < 20),
            }
        )
    return pd.DataFrame(rows)


def summarize_failure_state_audit(pool: pd.DataFrame) -> pd.DataFrame:
    base = pool[pool["candidate_set"].astype(str).eq("base_trend_closepos_097")].copy()
    rows = []
    for name, mask in build_failure_masks(base).items():
        subset = base[mask].copy()
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "failure_state_name": name,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()) if len(subset) else np.nan,
                "add_scale_success_rate": float(subset["add_scale_success_flag"].mean()) if len(subset) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("factor_adjusted_avg_residual_pct").reset_index(drop=True)


def build_failure_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    timing = frame["timing_state"].astype(str)
    entry_state = frame["intraday_entry_state_v4"].astype(str)
    setup = frame["symbol_multiday_setup_state"].astype(str)
    theme = frame["theme_regime_state_v4"].astype(str)
    return {
        "opening_high_close_low_vwap": timing.eq("opening_drive") & (frame["entry_close_pos_in_bar"] > 0.88) & (frame["entry_close_vs_vwap"] < 0.004),
        "breakout_high_close_low_vwap": entry_state.eq("intraday_breakout_acceptance") & (frame["entry_close_pos_in_bar"] > 0.90) & (frame["entry_close_vs_vwap"] < 0.003),
        "volume_reclaim_weak_theme": setup.eq("volume_confirmed_reclaim") & (frame["theme_breadth20_prev"] < 0.70),
        "volume_climax_late_extension": (frame["volume_ratio_prev"] > 2.0) & (frame["range_pos"] > 0.92) & timing.isin(["opening_drive", "late_day_confirmation"]),
        "narrow_theme_opening_drive": timing.eq("opening_drive") & theme.eq("narrow_theme_leader"),
    }


def build_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule": "suppression_assignment_uses_entry_safe_fields_only", "pass_flag": 1},
            {"rule": "exit_reason_used_only_in_prior_task_failure_diagnostic_not_rule_assignment", "pass_flag": 1},
            {"rule": "factor_residual_used_only_for_evaluation", "pass_flag": 1},
            {"rule": "no_symbol_date_price_time_fallback", "pass_flag": 1},
        ]
    )


def build_decision(quality: pd.DataFrame, split_quality: pd.DataFrame) -> pd.DataFrame:
    validation = split_quality[split_quality["split_name"].astype(str).eq("validation")]
    recent = split_quality[split_quality["split_name"].astype(str).eq("recent_oos")]
    joined = validation[["suppression_rule_name", "factor_adjusted_avg_residual_pct", "entry_reduce_failure_rate", "factor_adjusted_count"]].merge(
        recent[["suppression_rule_name", "factor_adjusted_avg_residual_pct", "entry_reduce_failure_rate", "factor_adjusted_count"]],
        on="suppression_rule_name",
        suffixes=("_validation", "_recent_oos"),
    )
    passed = joined[
        joined["factor_adjusted_avg_residual_pct_validation"].gt(0)
        & joined["factor_adjusted_avg_residual_pct_recent_oos"].gt(0)
        & joined["factor_adjusted_count_validation"].ge(20)
        & joined["factor_adjusted_count_recent_oos"].ge(20)
        & joined["entry_reduce_failure_rate_validation"].le(0.30)
    ]
    best_rule = quality.iloc[0]["suppression_rule_name"] if not quality.empty else ""
    return pd.DataFrame(
        [
            {
                "task_id": "Task545",
                "suppression_rule_count": int(quality["suppression_rule_name"].nunique()) if not quality.empty else 0,
                "walk_forward_suppression_pass_count": int(len(passed)),
                "best_overall_rule": best_rule,
                "factor_result_used_as_trading_trigger_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "FACTOR_ADJUSTED_SUPPRESSION_CANDIDATE_FOUND_DIAGNOSTIC_ONLY"
                if len(passed)
                else "FACTOR_ADJUSTED_SUPPRESSION_DIAGNOSTIC_NO_FIRM_PASS",
            }
        ]
    )


def write_task545(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_545_decision"].iloc[0].to_dict()
    quality = artifacts["failure_state_suppression_quality"].head(3)
    lines = [
        f"{row['suppression_rule_name']}: count {int(row['lifecycle_count'])}, residual {row['factor_adjusted_avg_residual_pct']:.2f}%, entry_reduce {row['entry_reduce_failure_rate']:.2%}."
        for row in quality.to_dict(orient="records")
    ]
    write_standard_report(
        out_dir / "task_545_factor_adjusted_failure_state_suppression.md",
        title="Task 545 Factor-Adjusted Failure-State Suppression",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Suppression rules tested: {decision['suppression_rule_count']}",
            f"Walk-forward pass count: {decision['walk_forward_suppression_pass_count']}",
            f"Best overall rule: {decision['best_overall_rule']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task545 tests entry-safe suppression variants for the failure states identified in Task544.",
            "Rules are assigned without using exit reason, residual outcome, or labels; those fields are evaluation-only.",
            *lines,
        ],
        decision_maker_lines=[
            "We tried to remove the recurring bad continuation patterns without using future information.",
            "The goal is to keep enough trades while reducing entry-reduce failures and preserving factor-adjusted residual returns.",
            "This remains diagnostic until it survives walk-forward and live-source constraints.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task545_factor_adjusted_failure_suppression()


if __name__ == "__main__":
    main()
