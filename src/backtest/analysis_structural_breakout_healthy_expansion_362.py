from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_shadow_integration_360 import (
    FAILURE_WINDOWS,
    _framework_metrics,
    _proxy_shadow_frame,
    _safe_numeric,
    generate_shadow_artifacts,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_362_healthy_expansion_aggressive_policy")
QUALITY_ORDER = (
    "HEALTHY_EXPANSION",
    "NEUTRAL_PARTICIPATION",
    "FRAGILE_CROWDING",
    "UNKNOWN",
)


def _policy_comparison(artifacts) -> pd.DataFrame:
    shadow_log = artifacts.shadow_log.copy()
    old_shadow_frame = _proxy_shadow_frame(artifacts.baseline_frame.copy(), shadow_log)
    quality_frame = _proxy_shadow_frame(
        artifacts.baseline_frame.copy(),
        shadow_log,
        realized_proxy_column="quality_aware_realized_R_proxy",
        size_column="quality_aware_size_multiplier",
    )
    healthy_frame = _proxy_shadow_frame(
        artifacts.baseline_frame.copy(),
        shadow_log,
        realized_proxy_column="healthy_aggressive_realized_R_proxy",
        size_column="healthy_aggressive_final_size_multiplier",
    )
    eligible_days = int(pd.to_datetime(artifacts.baseline_frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique())
    baseline_metrics = artifacts.baseline_summary.iloc[0].to_dict()
    old_shadow_metrics = _framework_metrics("old_shadow_policy", old_shadow_frame.copy(), eligible_days)
    quality_metrics = _framework_metrics("quality_aware_shadow_policy", quality_frame.copy(), eligible_days)
    healthy_metrics = _framework_metrics("healthy_expansion_aggressive_policy", healthy_frame.copy(), eligible_days)
    baseline_net = max(float(baseline_metrics.get("net_pnl_r", 0.0)), 1e-9)
    rows = [
        {
            "policy_name": "baseline",
            "net_pnl_r": baseline_metrics.get("net_pnl_r"),
            "anchored_oos_net_pnl_r": baseline_metrics.get("anchored_oos_net_pnl_r"),
            "trade_count": baseline_metrics.get("trade_count"),
            "monetization_retention_ratio": 1.0,
        },
        {
            "policy_name": "old_shadow_policy",
            "net_pnl_r": old_shadow_metrics.get("net_pnl_r"),
            "anchored_oos_net_pnl_r": old_shadow_metrics.get("anchored_oos_net_pnl_r"),
            "trade_count": old_shadow_metrics.get("trade_count"),
            "monetization_retention_ratio": round(float(old_shadow_metrics.get("net_pnl_r", 0.0)) / baseline_net, 6),
        },
        {
            "policy_name": "quality_aware_shadow_policy",
            "net_pnl_r": quality_metrics.get("net_pnl_r"),
            "anchored_oos_net_pnl_r": quality_metrics.get("anchored_oos_net_pnl_r"),
            "trade_count": quality_metrics.get("trade_count"),
            "monetization_retention_ratio": round(float(quality_metrics.get("net_pnl_r", 0.0)) / baseline_net, 6),
        },
        {
            "policy_name": "healthy_expansion_aggressive_policy",
            "net_pnl_r": healthy_metrics.get("net_pnl_r"),
            "anchored_oos_net_pnl_r": healthy_metrics.get("anchored_oos_net_pnl_r"),
            "trade_count": healthy_metrics.get("trade_count"),
            "monetization_retention_ratio": round(float(healthy_metrics.get("net_pnl_r", 0.0)) / baseline_net, 6),
        },
    ]
    return pd.DataFrame(rows)


def _quality_label_comparison(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label in QUALITY_ORDER:
        scoped = shadow_log[shadow_log["participation_quality_label"].astype(str) == label].copy()
        rows.append(
            {
                "participation_quality_label": label,
                "trade_count": int(len(scoped)),
                "baseline_pnl_r": round(float(_safe_numeric(scoped, "baseline_realized_R").sum()), 6),
                "old_shadow_proxy_pnl_r": round(float(_safe_numeric(scoped, "shadow_realized_R_proxy").sum()), 6),
                "quality_aware_proxy_pnl_r": round(float(_safe_numeric(scoped, "quality_aware_realized_R_proxy").sum()), 6),
                "healthy_aggressive_proxy_pnl_r": round(float(_safe_numeric(scoped, "healthy_aggressive_realized_R_proxy").sum()), 6),
                "avg_quality_aware_size_multiplier": round(float(_safe_numeric(scoped, "quality_aware_size_multiplier").mean()), 6) if not scoped.empty else 0.0,
                "avg_healthy_aggressive_size_multiplier": round(float(_safe_numeric(scoped, "healthy_aggressive_final_size_multiplier").mean()), 6) if not scoped.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _failure_window_comparison(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for window_name in ("full_period", "anchored_oos", "2025-12", "2026-01"):
        if window_name == "full_period":
            scoped = shadow_log.copy()
        elif window_name == "anchored_oos":
            scoped = shadow_log[shadow_log["current_split"].astype(str) == "anchored_oos"].copy()
        else:
            start, end = FAILURE_WINDOWS[window_name]
            ts = pd.to_datetime(shadow_log["timestamp"], errors="coerce", utc=True)
            scoped = shadow_log[(ts >= pd.Timestamp(start, tz="UTC")) & (ts <= pd.Timestamp(end, tz="UTC"))].copy()
        if scoped.empty:
            continue
        rows.append(
            {
                "window_name": window_name,
                "baseline_net_pnl_r": round(float(_safe_numeric(scoped, "baseline_realized_R").sum()), 6),
                "old_shadow_net_pnl_r": round(float(_safe_numeric(scoped, "shadow_realized_R_proxy").sum()), 6),
                "quality_aware_net_pnl_r": round(float(_safe_numeric(scoped, "quality_aware_realized_R_proxy").sum()), 6),
                "healthy_aggressive_net_pnl_r": round(float(_safe_numeric(scoped, "healthy_aggressive_realized_R_proxy").sum()), 6),
                "fragile_crowding_share": round(float(scoped["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING").mean()), 6),
                "healthy_expansion_share": round(float(scoped["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION").mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def _activation_diagnostics(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label in QUALITY_ORDER:
        scoped = shadow_log[shadow_log["participation_quality_label"].astype(str) == label].copy()
        if scoped.empty:
            continue
        rows.append(
            {
                "participation_quality_label": label,
                "trade_count_affected": int(len(scoped)),
                "old_shadow_add_count": int(scoped["staged_gate_stage"].astype(str).eq("stage_2_add").sum()),
                "quality_aware_add_count": int(scoped["quality_aware_policy_stage"].astype(str).eq("ADD_ALLOWED").sum()),
                "healthy_aggressive_add_count": int(scoped["healthy_aggressive_final_add_allowed"].fillna(False).astype(bool).sum()),
                "quality_aware_size_floor_activations": int((_safe_numeric(scoped, "quality_aware_size_multiplier") > _safe_numeric(scoped, "shadow_size_multiplier")).sum()),
                "healthy_aggressive_size_floor_activations": int((_safe_numeric(scoped, "healthy_aggressive_final_size_multiplier") > _safe_numeric(scoped, "quality_aware_size_multiplier")).sum()),
            }
        )
    return pd.DataFrame(rows)


def _violation_checks(shadow_log: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "fragile_crowding_relax_violations": int(shadow_log["fragile_crowding_relax_violation"].fillna(False).astype(bool).sum()),
                "dislocation_relax_violations": int(shadow_log["dislocation_relax_violation"].fillna(False).astype(bool).sum()),
            }
        ]
    )


def _diagnostic_answers(policy_df: pd.DataFrame, activation_df: pd.DataFrame, violation_df: pd.DataFrame) -> tuple[str, str, str, str, str]:
    baseline = policy_df[policy_df["policy_name"].astype(str) == "baseline"].iloc[0]
    quality = policy_df[policy_df["policy_name"].astype(str) == "quality_aware_shadow_policy"].iloc[0]
    healthy = policy_df[policy_df["policy_name"].astype(str) == "healthy_expansion_aggressive_policy"].iloc[0]
    violations = violation_df.iloc[0]
    healthy_activation = activation_df[activation_df["participation_quality_label"].astype(str) == "HEALTHY_EXPANSION"]

    q1 = "YES" if float(healthy["net_pnl_r"]) > float(quality["net_pnl_r"]) else "NO"
    q2 = "YES" if float(healthy["anchored_oos_net_pnl_r"]) > float(baseline["anchored_oos_net_pnl_r"]) else "NO"
    q3 = "YES" if int(violations["fragile_crowding_relax_violations"]) == 0 and int(violations["dislocation_relax_violations"]) == 0 else "NO"
    q4 = "YES" if not healthy_activation.empty and (
        int(healthy_activation["healthy_aggressive_add_count"].iloc[0]) > int(healthy_activation["quality_aware_add_count"].iloc[0])
        or int(healthy_activation["healthy_aggressive_size_floor_activations"].iloc[0]) > 0
    ) else "NO"
    if q4 == "NO":
        q5 = "classifier too conservative or row-level proxy insufficient"
    elif q1 == "NO":
        q5 = "size policy too weak or add gate still too restrictive"
    elif q2 == "NO":
        q5 = "aggressive relaxation is sacrificing anchored OOS protection"
    else:
        q5 = "row-level proxy still limits confidence in lifecycle monetization"
    return q1, q2, q3, q4, q5


def _report(
    out_dir: Path,
    policy_df: pd.DataFrame,
    label_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    activation_df: pd.DataFrame,
    violation_df: pd.DataFrame,
) -> None:
    q1, q2, q3, q4, q5 = _diagnostic_answers(policy_df, activation_df, violation_df)
    lines = [
        "# Task 362 - Healthy Expansion Aggressive Participation Calibration",
        "",
        "## Core Answers",
        f"1. Did aggressive healthy-expansion policy improve full-period monetization vs Task 361 quality-aware policy? {q1}",
        f"2. Did it preserve anchored OOS improvement vs baseline? {q2}",
        f"3. Did it avoid relaxing suppression under FRAGILE_CROWDING? {q3}",
        f"4. Did it actually increase add/size activation under HEALTHY_EXPANSION? {q4}",
        f"5. Current bottleneck assessment: {q5}",
        "",
        "## Policy Comparison",
        *(_markdown_table(policy_df)),
        "",
        "## Quality Label Comparison",
        *(_markdown_table(label_df)),
        "",
        "## Failure Window Comparison",
        *(_markdown_table(failure_df)),
        "",
        "## Activation Diagnostics",
        *(_markdown_table(activation_df)),
        "",
        "## Violation Checks",
        *(_markdown_table(violation_df)),
    ]
    (out_dir / "task_362_healthy_expansion_aggressive_policy.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 362: healthy expansion aggressive participation calibration")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)
    shadow_log = artifacts.shadow_log.copy()
    policy_df = _policy_comparison(artifacts)
    label_df = _quality_label_comparison(shadow_log)
    failure_df = _failure_window_comparison(shadow_log)
    activation_df = _activation_diagnostics(shadow_log)
    violation_df = _violation_checks(shadow_log)

    shadow_log.to_csv(out_dir / "task_362_healthy_aggressive_log.csv", index=False)
    policy_df.to_csv(out_dir / "task_362_policy_comparison.csv", index=False)
    label_df.to_csv(out_dir / "task_362_quality_label_comparison.csv", index=False)
    failure_df.to_csv(out_dir / "task_362_failure_window_comparison.csv", index=False)
    activation_df.to_csv(out_dir / "task_362_activation_diagnostics.csv", index=False)
    violation_df.to_csv(out_dir / "task_362_violation_checks.csv", index=False)
    _report(out_dir, policy_df, label_df, failure_df, activation_df, violation_df)


if __name__ == "__main__":
    main()
