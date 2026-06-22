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


DEFAULT_OUT_DIR = Path("docs/reports/task_361_participation_quality")
QUALITY_ORDER = (
    "HEALTHY_EXPANSION",
    "NEUTRAL_PARTICIPATION",
    "FRAGILE_CROWDING",
    "UNKNOWN",
)


def _quality_distribution(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total = max(len(shadow_log), 1)
    for label in QUALITY_ORDER:
        scoped = shadow_log[shadow_log["participation_quality_label"].astype(str) == label].copy()
        rows.append(
            {
                "participation_quality_label": label,
                "trade_count": int(len(scoped)),
                "trade_share": round(float(len(scoped) / total), 6),
                "avg_expansion_score": round(float(_safe_numeric(scoped, "participation_expansion_score").mean()), 6) if not scoped.empty else 0.0,
                "avg_fragility_score": round(float(_safe_numeric(scoped, "participation_fragility_score").mean()), 6) if not scoped.empty else 0.0,
                "avg_confidence": round(float(_safe_numeric(scoped, "participation_confidence").mean()), 6) if not scoped.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _label_pnl_comparison(shadow_log: pd.DataFrame) -> pd.DataFrame:
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
                "avg_old_shadow_size_multiplier": round(float(_safe_numeric(scoped, "shadow_size_multiplier").mean()), 6) if not scoped.empty else 0.0,
                "avg_quality_aware_size_multiplier": round(float(_safe_numeric(scoped, "quality_aware_size_multiplier").mean()), 6) if not scoped.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _failure_window_comparison(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for window_name in ("full_period", "anchored_oos", "2025-12", "2026-01", "semis_bucket", "non_semis_bucket"):
        if window_name in FAILURE_WINDOWS:
            if window_name == "full_period":
                scoped = shadow_log.copy()
            elif window_name == "anchored_oos":
                scoped = shadow_log[shadow_log["current_split"].astype(str) == "anchored_oos"].copy()
            else:
                start, end = FAILURE_WINDOWS[window_name]
                ts = pd.to_datetime(shadow_log["timestamp"], errors="coerce", utc=True)
                scoped = shadow_log[(ts >= pd.Timestamp(start, tz="UTC")) & (ts <= pd.Timestamp(end, tz="UTC"))].copy()
        elif window_name == "semis_bucket":
            scoped = shadow_log[shadow_log["sector_group"].astype(str) == "semis"].copy()
        else:
            scoped = shadow_log[shadow_log["sector_group"].astype(str) != "semis"].copy()
        if scoped.empty:
            continue
        label_mix = "|".join(
            f"{k}:{v}" for k, v in scoped["participation_quality_label"].value_counts(normalize=True).round(4).sort_index().items()
        )
        fragile_share = float(scoped["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING").mean())
        healthy_share = float(scoped["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION").mean())
        rows.append(
            {
                "window_name": window_name,
                "trade_count": int(len(scoped)),
                "baseline_pnl_r": round(float(_safe_numeric(scoped, "baseline_realized_R").sum()), 6),
                "old_shadow_proxy_pnl_r": round(float(_safe_numeric(scoped, "shadow_realized_R_proxy").sum()), 6),
                "quality_aware_proxy_pnl_r": round(float(_safe_numeric(scoped, "quality_aware_realized_R_proxy").sum()), 6),
                "healthy_expansion_share": round(healthy_share, 6),
                "fragile_crowding_share": round(fragile_share, 6),
                "label_distribution": label_mix,
            }
        )
    return pd.DataFrame(rows)


def _add_behavior_by_label(shadow_log: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label in QUALITY_ORDER:
        scoped = shadow_log[shadow_log["participation_quality_label"].astype(str) == label].copy()
        if scoped.empty:
            continue
        for policy_name, stage_col in (
            ("old_shadow_policy", "staged_gate_stage"),
            ("quality_aware_shadow_policy", "quality_aware_policy_stage"),
        ):
            stage_series = scoped[stage_col].fillna("UNKNOWN").astype(str)
            add_allowed = stage_series.eq("stage_2_add").sum() if stage_col == "staged_gate_stage" else stage_series.eq("ADD_ALLOWED").sum()
            probe_only = stage_series.isin({"stage_1_probe", "delayed_probe", "PROBE_ONLY"}).sum()
            block_count = stage_series.eq("BLOCK").sum()
            rows.append(
                {
                    "participation_quality_label": label,
                    "policy_name": policy_name,
                    "trade_count": int(len(scoped)),
                    "ADD_ALLOWED": int(add_allowed),
                    "PROBE_ONLY": int(probe_only),
                    "BLOCK": int(block_count),
                }
            )
    return pd.DataFrame(rows)


def _policy_comparison(artifacts) -> pd.DataFrame:
    shadow_log = artifacts.shadow_log.copy()
    quality_proxy_frame = _proxy_shadow_frame(
        artifacts.baseline_frame.copy(),
        shadow_log,
        realized_proxy_column="quality_aware_realized_R_proxy",
        size_column="quality_aware_size_multiplier",
    )
    eligible_days = int(pd.to_datetime(artifacts.baseline_frame["entry_ts"], errors="coerce", utc=True).dt.normalize().dropna().nunique())
    baseline_metrics = artifacts.baseline_summary.iloc[0].to_dict()
    old_shadow_metrics = _framework_metrics("shadow_gated_proxy", _proxy_shadow_frame(artifacts.baseline_frame.copy(), shadow_log), eligible_days)
    quality_metrics = _framework_metrics("quality_aware_shadow_policy", quality_proxy_frame.copy(), eligible_days)
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
            "monetization_retention_ratio": round(float(old_shadow_metrics.get("net_pnl_r", 0.0)) / max(float(baseline_metrics.get("net_pnl_r", 0.0)), 1e-9), 6),
        },
        {
            "policy_name": "quality_aware_shadow_policy",
            "net_pnl_r": quality_metrics.get("net_pnl_r"),
            "anchored_oos_net_pnl_r": quality_metrics.get("anchored_oos_net_pnl_r"),
            "trade_count": quality_metrics.get("trade_count"),
            "monetization_retention_ratio": round(float(quality_metrics.get("net_pnl_r", 0.0)) / max(float(baseline_metrics.get("net_pnl_r", 0.0)), 1e-9), 6),
        },
    ]
    return pd.DataFrame(rows)


def _diagnostic_answers(
    distribution_df: pd.DataFrame,
    label_pnl_df: pd.DataFrame,
    window_df: pd.DataFrame,
    policy_df: pd.DataFrame,
) -> tuple[str, str, str]:
    healthy = label_pnl_df[label_pnl_df["participation_quality_label"].astype(str) == "HEALTHY_EXPANSION"]
    old_shadow = policy_df[policy_df["policy_name"].astype(str) == "old_shadow_policy"].iloc[0]
    quality_shadow = policy_df[policy_df["policy_name"].astype(str) == "quality_aware_shadow_policy"].iloc[0]
    failure_windows = window_df[window_df["window_name"].astype(str).isin({"2025-12", "2026-01"})].copy()
    fragile_failure_share = float(failure_windows["fragile_crowding_share"].mean()) if not failure_windows.empty else 0.0
    healthy_failure_share = float(failure_windows["healthy_expansion_share"].mean()) if not failure_windows.empty else 0.0

    q1 = (
        "YES"
        if not healthy.empty
        and float(healthy["baseline_pnl_r"].iloc[0]) > float(healthy["old_shadow_proxy_pnl_r"].iloc[0])
        else "NO"
    )
    q2 = "YES" if fragile_failure_share > healthy_failure_share else "NO"
    q3 = (
        "YES"
        if float(quality_shadow["net_pnl_r"]) > float(old_shadow["net_pnl_r"])
        and float(quality_shadow["anchored_oos_net_pnl_r"]) >= float(old_shadow["anchored_oos_net_pnl_r"])
        else "NO"
    )
    return q1, q2, q3


def _report(
    out_dir: Path,
    distribution_df: pd.DataFrame,
    label_pnl_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    add_df: pd.DataFrame,
    policy_df: pd.DataFrame,
) -> None:
    q1, q2, q3 = _diagnostic_answers(distribution_df, label_pnl_df, failure_df, policy_df)
    lines = [
        "# Task 361 - Participation Quality / Crowding Fragility Modeling",
        "",
        "## Core Answers",
        f"1. Did Task 360 suppress healthy expansion too aggressively? {q1}",
        f"2. Did fragile crowding explain failure windows better than generic crowding? {q2}",
        f"3. Should future allocator calibration relax suppression under healthy expansion? {q3}",
        "",
        "## Participation Quality Distribution",
        *(_markdown_table(distribution_df)),
        "",
        "## Baseline vs Shadow PnL by Label",
        *(_markdown_table(label_pnl_df)),
        "",
        "## Failure Window Comparison",
        *(_markdown_table(failure_df)),
        "",
        "## Add Behavior by Label",
        *(_markdown_table(add_df)),
        "",
        "## Shadow Policy Comparison",
        *(_markdown_table(policy_df)),
    ]
    (out_dir / "task_361_participation_quality.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 361: participation quality diagnostics")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)
    shadow_log = artifacts.shadow_log.copy()
    distribution_df = _quality_distribution(shadow_log)
    label_pnl_df = _label_pnl_comparison(shadow_log)
    failure_df = _failure_window_comparison(shadow_log)
    add_df = _add_behavior_by_label(shadow_log)
    policy_df = _policy_comparison(artifacts)

    shadow_log.to_csv(out_dir / "task_361_participation_quality_log.csv", index=False)
    distribution_df.to_csv(out_dir / "task_361_quality_distribution.csv", index=False)
    label_pnl_df.to_csv(out_dir / "task_361_label_pnl_comparison.csv", index=False)
    failure_df.to_csv(out_dir / "task_361_failure_window_comparison.csv", index=False)
    add_df.to_csv(out_dir / "task_361_add_behavior_by_label.csv", index=False)
    policy_df.to_csv(out_dir / "task_361_shadow_policy_comparison.csv", index=False)
    _report(out_dir, distribution_df, label_pnl_df, failure_df, add_df, policy_df)


if __name__ == "__main__":
    main()
