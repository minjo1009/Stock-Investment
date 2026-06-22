from __future__ import annotations

from typing import Any

import pandas as pd


def _safe_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _safe_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(bool)


def _quality_type(group: pd.DataFrame) -> str:
    has_healthy = group["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION").any()
    has_fragile = group["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING").any()
    has_neutral = group["participation_quality_label"].astype(str).eq("NEUTRAL_PARTICIPATION").any()
    if has_healthy and has_fragile:
        return "mixed"
    if has_fragile:
        return "fragile"
    if has_healthy:
        return "healthy"
    if has_neutral:
        return "neutral_only"
    return "neutral_only"


def build_continuation_lifecycle_diagnostics(
    shadow_log_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if shadow_log_df.empty:
        empty_lifecycle = pd.DataFrame(
            columns=[
                "lifecycle_id",
                "symbol",
                "trade_date",
                "start_timestamp",
                "end_timestamp",
                "row_count",
                "has_healthy_expansion",
                "has_fragile_crowding",
                "has_neutral_participation",
                "lifecycle_quality_type",
                "max_expansion_score",
                "max_fragility_score",
                "add_allowed_count_old_shadow",
                "add_allowed_count_quality_aware",
                "add_allowed_count_healthy_aggressive",
                "blocked_add_count_old_shadow",
                "blocked_add_count_quality_aware",
                "blocked_add_count_healthy_aggressive",
                "baseline_pnl_r_sum",
                "old_shadow_pnl_proxy_sum",
                "quality_aware_pnl_proxy_sum",
                "healthy_aggressive_pnl_proxy_sum",
            ]
        )
        empty_summary = pd.DataFrame(
            columns=[
                "lifecycle_quality_type",
                "lifecycle_count",
                "avg_row_count",
                "baseline_pnl_r_sum",
                "old_shadow_pnl_proxy_sum",
                "quality_aware_pnl_proxy_sum",
                "healthy_aggressive_pnl_proxy_sum",
                "avg_add_allowed_count_old_shadow",
                "avg_add_allowed_count_quality_aware",
                "avg_add_allowed_count_healthy_aggressive",
            ]
        )
        return empty_lifecycle, empty_summary

    frame = shadow_log_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["trade_date"] = frame["timestamp"].dt.normalize()
    frame = frame.sort_values(["symbol", "trade_date", "timestamp", "trade_id"]).reset_index(drop=True)

    lifecycle_rows: list[dict[str, Any]] = []
    for (symbol, trade_date), group in frame.groupby(["symbol", "trade_date"], dropna=False):
        group = group.sort_values(["timestamp", "trade_id"]).reset_index(drop=True)
        lifecycle_id = f"{symbol}|{trade_date.strftime('%Y-%m-%d') if pd.notna(trade_date) else 'unknown'}"
        row_count = int(len(group))
        quality_type = _quality_type(group)
        add_old = int(_safe_bool(group["staged_add_allowed"]).sum())
        add_quality = int(_safe_bool(group["quality_aware_add_allowed"]).sum())
        add_healthy = int(_safe_bool(group["healthy_aggressive_final_add_allowed"]).sum())
        lifecycle_rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": symbol,
                "trade_date": trade_date,
                "start_timestamp": group["timestamp"].iloc[0],
                "end_timestamp": group["timestamp"].iloc[-1],
                "row_count": row_count,
                "has_healthy_expansion": bool(group["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION").any()),
                "has_fragile_crowding": bool(group["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING").any()),
                "has_neutral_participation": bool(group["participation_quality_label"].astype(str).eq("NEUTRAL_PARTICIPATION").any()),
                "lifecycle_quality_type": quality_type,
                "max_expansion_score": round(float(_safe_float(group["participation_expansion_score"]).max()), 6),
                "max_fragility_score": round(float(_safe_float(group["participation_fragility_score"]).max()), 6),
                "add_allowed_count_old_shadow": add_old,
                "add_allowed_count_quality_aware": add_quality,
                "add_allowed_count_healthy_aggressive": add_healthy,
                "blocked_add_count_old_shadow": row_count - add_old,
                "blocked_add_count_quality_aware": row_count - add_quality,
                "blocked_add_count_healthy_aggressive": row_count - add_healthy,
                "baseline_pnl_r_sum": round(float(_safe_float(group["baseline_realized_R"]).sum()), 6),
                "old_shadow_pnl_proxy_sum": round(float(_safe_float(group["shadow_realized_R_proxy"]).sum()), 6),
                "quality_aware_pnl_proxy_sum": round(float(_safe_float(group["quality_aware_realized_R_proxy"]).sum()), 6),
                "healthy_aggressive_pnl_proxy_sum": round(float(_safe_float(group["healthy_aggressive_realized_R_proxy"]).sum()), 6),
            }
        )
    lifecycle_df = pd.DataFrame(lifecycle_rows)

    summary_rows: list[dict[str, Any]] = []
    for quality_type, group in lifecycle_df.groupby("lifecycle_quality_type", dropna=False):
        summary_rows.append(
            {
                "lifecycle_quality_type": quality_type,
                "lifecycle_count": int(len(group)),
                "avg_row_count": round(float(_safe_float(group["row_count"]).mean()), 6),
                "baseline_pnl_r_sum": round(float(_safe_float(group["baseline_pnl_r_sum"]).sum()), 6),
                "old_shadow_pnl_proxy_sum": round(float(_safe_float(group["old_shadow_pnl_proxy_sum"]).sum()), 6),
                "quality_aware_pnl_proxy_sum": round(float(_safe_float(group["quality_aware_pnl_proxy_sum"]).sum()), 6),
                "healthy_aggressive_pnl_proxy_sum": round(float(_safe_float(group["healthy_aggressive_pnl_proxy_sum"]).sum()), 6),
                "avg_add_allowed_count_old_shadow": round(float(_safe_float(group["add_allowed_count_old_shadow"]).mean()), 6),
                "avg_add_allowed_count_quality_aware": round(float(_safe_float(group["add_allowed_count_quality_aware"]).mean()), 6),
                "avg_add_allowed_count_healthy_aggressive": round(float(_safe_float(group["add_allowed_count_healthy_aggressive"]).mean()), 6),
            }
        )
    lifecycle_summary_df = pd.DataFrame(summary_rows).sort_values("lifecycle_quality_type").reset_index(drop=True)
    return lifecycle_df, lifecycle_summary_df
