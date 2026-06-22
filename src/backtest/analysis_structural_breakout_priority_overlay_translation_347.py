from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import (
    INITIAL_CAPITAL,
    OverlayVariant,
    _apply_cost_scaled,
    _f,
    _portfolio_metrics,
)
from src.backtest.analysis_structural_breakout_coverage_corrected_revalidation_346 import (
    _corrected_build_split_frames,
    _corrected_entry_only_master,
    _corrected_overlay_master,
)
from src.backtest.analysis_structural_breakout_intraday_signal_strengthening_339 import _sector_group
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import (
    DB_PATH,
    DEFAULT_COST_SCENARIOS,
    ROLLING_WINDOWS,
    _rolling_label,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import _load_intraday_bars


DEFAULT_OUT_DIR = Path("docs/reports/task_347_priority_overlay_translation")
TARGET_REGIME_SECTOR = "software_internet"
SIZE_OVERLAY_50 = OverlayVariant("size_overlay_50", 2.0, 0.5, 1.0, "size_overlay_reference")
MAX_POSITIONS_OPTIONS: tuple[int, ...] = (3, 5, 10)
SECTOR_CAP_OPTIONS: tuple[str, ...] = ("none", "50", "30")
PRIORITY_VARIANTS: tuple[str, ...] = (
    "priority_top1_only",
    "priority_top2",
    "priority_top3",
    "priority_threshold_ge_2",
    "priority_threshold_ge_3",
)


@dataclass(frozen=True)
class SelectionVariant:
    name: str
    variant_type: str


VARIANTS: tuple[SelectionVariant, ...] = (
    SelectionVariant("baseline", "baseline"),
    SelectionVariant(SIZE_OVERLAY_50.name, SIZE_OVERLAY_50.variant_type),
    SelectionVariant("priority_top1_only", "priority_overlay"),
    SelectionVariant("priority_top2", "priority_overlay"),
    SelectionVariant("priority_top3", "priority_overlay"),
    SelectionVariant("priority_threshold_ge_2", "priority_overlay"),
    SelectionVariant("priority_threshold_ge_3", "priority_overlay"),
)


def _sector_cap_limit(max_positions: int, sector_cap: str) -> int | None:
    if sector_cap == "none":
        return None
    ratio = 0.5 if sector_cap == "50" else 0.3
    return max(1, int(math.floor(max_positions * ratio)))


def _prepare_master() -> tuple[pd.DataFrame, pd.DataFrame]:
    intraday_df = _load_intraday_bars(DB_PATH)
    coverage_df, feature_parts = _corrected_build_split_frames(intraday_df)
    covered_entry_master = _corrected_entry_only_master(feature_parts)
    master_df, covered_entry_master = _corrected_overlay_master(coverage_df, covered_entry_master)

    covered_entry_master = covered_entry_master.copy()
    covered_entry_master["trade_id"] = covered_entry_master["trade_id"].astype(str)
    covered_entry_master["entry_ts"] = pd.to_datetime(covered_entry_master["entry_ts"], errors="coerce", utc=True)
    covered_entry_master["entry_day"] = covered_entry_master["entry_ts"].dt.strftime("%Y-%m-%d")
    covered_entry_master["baseline_momentum"] = pd.to_numeric(covered_entry_master["ret_20d_pre"], errors="coerce").fillna(0.0)
    covered_entry_master["baseline_avg_dollar_volume"] = pd.to_numeric(
        covered_entry_master["dollar_volume_pre"], errors="coerce"
    ).fillna(0.0)
    covered_entry_master["baseline_volatility"] = pd.to_numeric(
        covered_entry_master["range_width_10_pre"], errors="coerce"
    ).fillna(0.0)
    covered_entry_master["is_high_atr"] = covered_entry_master["atr_regime"].astype(str) == "high_atr"
    covered_entry_master["is_vol_expanding"] = covered_entry_master["contraction_regime"].astype(str) == "vol_expanding"
    covered_entry_master["is_entry_only_component"] = covered_entry_master["window_mode"].astype(str) == "entry_only"
    covered_entry_master["is_software_internet_component"] = (
        covered_entry_master["sector_group"].astype(str) == TARGET_REGIME_SECTOR
    )
    covered_entry_master["priority_score"] = (
        covered_entry_master["is_high_atr"].astype(int)
        + covered_entry_master["is_vol_expanding"].astype(int)
        + covered_entry_master["is_entry_only_component"].astype(int)
        + covered_entry_master["is_software_internet_component"].astype(int)
    )

    covered_flags = covered_entry_master[
        [
            "trade_id",
            "baseline_momentum",
            "baseline_avg_dollar_volume",
            "baseline_volatility",
            "is_high_atr",
            "is_vol_expanding",
            "is_entry_only_component",
            "is_software_internet_component",
            "priority_score",
        ]
    ].drop_duplicates("trade_id")

    master_df = master_df.copy()
    master_df["trade_id"] = master_df["trade_id"].astype(str)
    master_df = master_df.merge(covered_flags, on="trade_id", how="left")
    master_df["entry_day"] = pd.to_datetime(master_df["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    master_df["sector_group"] = master_df["sector_group"].fillna(master_df["sector_bucket"].map(_sector_group))
    master_df["baseline_momentum"] = pd.to_numeric(master_df["baseline_momentum"], errors="coerce").fillna(
        pd.to_numeric(master_df.get("ret_20d_pre"), errors="coerce").fillna(0.0)
    )
    master_df["baseline_avg_dollar_volume"] = pd.to_numeric(
        master_df["baseline_avg_dollar_volume"], errors="coerce"
    ).fillna(pd.to_numeric(master_df.get("dollar_volume_pre"), errors="coerce").fillna(0.0))
    master_df["baseline_volatility"] = pd.to_numeric(master_df["baseline_volatility"], errors="coerce").fillna(
        pd.to_numeric(master_df.get("range_width_10_pre"), errors="coerce").fillna(0.0)
    )
    for col in (
        "is_high_atr",
        "is_vol_expanding",
        "is_entry_only_component",
        "is_software_internet_component",
    ):
        master_df[col] = np.where(master_df[col].isna(), False, master_df[col]).astype(bool)
    master_df["is_software_internet_component"] = master_df["sector_group"].astype(str) == TARGET_REGIME_SECTOR
    master_df["priority_score"] = (
        master_df["is_high_atr"].astype(int)
        + master_df["is_vol_expanding"].astype(int)
        + master_df["is_entry_only_component"].astype(int)
        + master_df["is_software_internet_component"].astype(int)
    )
    master_df["realized_R"] = pd.to_numeric(master_df["realized_R"], errors="coerce")
    return master_df.reset_index(drop=True), covered_entry_master.reset_index(drop=True)


def _add_baseline_rank(group_df: pd.DataFrame) -> pd.DataFrame:
    ranked = group_df.copy()
    ranked["momentum_rank"] = pd.to_numeric(ranked["baseline_momentum"], errors="coerce").rank(
        pct=True, method="average"
    )
    ranked["volume_rank"] = pd.to_numeric(ranked["baseline_avg_dollar_volume"], errors="coerce").rank(
        pct=True, method="average"
    )
    ranked["volatility_rank"] = pd.to_numeric(ranked["baseline_volatility"], errors="coerce").rank(
        pct=True, method="average"
    )
    ranked["baseline_score"] = (
        0.5 * ranked["momentum_rank"] + 0.35 * ranked["volume_rank"] - 0.15 * ranked["volatility_rank"]
    )
    return ranked


def _sort_candidates(df: pd.DataFrame, by_priority: bool) -> pd.DataFrame:
    scoped = _add_baseline_rank(df)
    sort_cols = ["baseline_score", "baseline_momentum", "baseline_avg_dollar_volume", "symbol"]
    ascending = [False, False, False, True]
    if by_priority:
        sort_cols = ["priority_score"] + sort_cols
        ascending = [False] + ascending
    return scoped.sort_values(sort_cols, ascending=ascending).reset_index(drop=True)


def _sector_allowed(selected: list[dict[str, Any]], row: pd.Series, sector_limit: int | None) -> bool:
    if sector_limit is None:
        return True
    sector = str(row.get("sector_group", ""))
    current = sum(1 for item in selected if str(item.get("sector_group", "")) == sector)
    return current < sector_limit


def _greedy_select(
    sorted_df: pd.DataFrame,
    max_positions: int,
    sector_limit: int | None,
    *,
    existing: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = list(existing or [])
    for _, row in sorted_df.iterrows():
        if len(selected) >= max_positions:
            break
        if _sector_allowed(selected, row, sector_limit):
            selected.append(row.to_dict())
    return selected


def _priority_eligible(group_df: pd.DataFrame, variant_name: str) -> pd.DataFrame:
    ranked = _sort_candidates(group_df, by_priority=True)
    if variant_name == "priority_top1_only":
        return ranked.head(1).copy()
    if variant_name == "priority_top2":
        return ranked.head(2).copy()
    if variant_name == "priority_top3":
        return ranked.head(3).copy()
    if variant_name == "priority_threshold_ge_2":
        return ranked[ranked["priority_score"] >= 2].copy()
    if variant_name == "priority_threshold_ge_3":
        return ranked[ranked["priority_score"] >= 3].copy()
    return ranked.iloc[0:0].copy()


def _select_group(group_df: pd.DataFrame, variant_name: str, max_positions: int, sector_cap: str) -> pd.DataFrame:
    sector_limit = _sector_cap_limit(max_positions, sector_cap)
    ranked = _sort_candidates(group_df, by_priority=False)
    if variant_name in {"baseline", SIZE_OVERLAY_50.name}:
        selected_rows = _greedy_select(ranked, max_positions, sector_limit)
        source = "baseline_ranking"
    else:
        priority_bucket = _priority_eligible(group_df, variant_name)
        selected_rows = _greedy_select(priority_bucket, max_positions, sector_limit)
        selected_ids = {str(row["trade_id"]) for row in selected_rows}
        fill_source = _greedy_select(
            ranked[~ranked["trade_id"].astype(str).isin(selected_ids)].copy(),
            max_positions,
            sector_limit,
            existing=selected_rows,
        )
        selected_rows = fill_source
        source = "priority_then_baseline"
    selected_df = pd.DataFrame(selected_rows)
    if selected_df.empty:
        selected_df = group_df.iloc[0:0].copy()
        selected_df["selection_source"] = pd.Series(dtype=str)
        selected_df["candidate_count_day"] = pd.Series(dtype=int)
        selected_df["filtered_out_count_day"] = pd.Series(dtype=int)
        selected_df["selected_rank_day"] = pd.Series(dtype=int)
        return selected_df
    selected_df["selection_source"] = source
    selected_df["candidate_count_day"] = int(len(group_df))
    selected_df["filtered_out_count_day"] = int(len(group_df) - len(selected_df))
    selected_df["selected_rank_day"] = np.arange(1, len(selected_df) + 1)
    return selected_df.reset_index(drop=True)


def _condition_mask(df: pd.DataFrame) -> pd.Series:
    return (
        df["is_high_atr"].astype(bool)
        & df["is_vol_expanding"].astype(bool)
        & df["is_entry_only_component"].astype(bool)
        & (df["sector_group"].astype(str) == TARGET_REGIME_SECTOR)
    )


def _apply_size_overlay_50(df: pd.DataFrame) -> pd.DataFrame:
    scoped = df.copy()
    cond = _condition_mask(scoped)
    scoped["size_multiplier"] = np.where(cond, 2.0, np.where(scoped["is_covered"].astype(bool), 0.5, 1.0))
    scoped["condition_met_effective"] = cond.astype(bool)
    scoped["scaled_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce") * pd.to_numeric(
        scoped["size_multiplier"], errors="coerce"
    )
    return scoped


def _select_universe(
    scope_df: pd.DataFrame,
    universe_name: str,
    variant_name: str,
    max_positions: int,
    sector_cap: str,
) -> pd.DataFrame:
    scoped = scope_df.copy()
    if universe_name == "covered_only":
        scoped = scoped[scoped["is_covered"].astype(bool)].copy()
    scoped = scoped.dropna(subset=["entry_day", "entry_ts"]).copy()
    if scoped.empty:
        return scoped
    selected_parts: list[pd.DataFrame] = []
    for _entry_day, group_df in scoped.groupby("entry_day", sort=True):
        selected_parts.append(_select_group(group_df.copy(), variant_name, max_positions, sector_cap))
    selected_df = pd.concat(selected_parts, ignore_index=True) if selected_parts else scoped.iloc[0:0].copy()
    if selected_df.empty:
        selected_df["size_multiplier"] = pd.Series(dtype=float)
        selected_df["scaled_R"] = pd.Series(dtype=float)
        selected_df["condition_met_effective"] = pd.Series(dtype=bool)
        return selected_df
    if variant_name == SIZE_OVERLAY_50.name:
        selected_df = _apply_size_overlay_50(selected_df)
    else:
        selected_df["size_multiplier"] = 1.0
        selected_df["scaled_R"] = pd.to_numeric(selected_df["realized_R"], errors="coerce")
        selected_df["condition_met_effective"] = _condition_mask(selected_df)
    return selected_df.reset_index(drop=True)


def _variant_rows(master_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[tuple[str, str, str, int, str], pd.DataFrame], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    scoped_frames: dict[tuple[str, str, str, int, str], pd.DataFrame] = {}
    oos_rows: list[dict[str, Any]] = []
    split_frames = {
        "full_period": master_df.copy(),
        "anchored_oos": master_df[master_df["current_split"] == "anchored_oos"].copy(),
    }
    for universe_name in ("covered_only", "hybrid_full"):
        for scope_name, scope_df in split_frames.items():
            for max_positions in MAX_POSITIONS_OPTIONS:
                for sector_cap in SECTOR_CAP_OPTIONS:
                    base_row: dict[str, Any] | None = None
                    for variant in VARIANTS:
                        selected = _select_universe(scope_df, universe_name, variant.name, max_positions, sector_cap)
                        metrics = _portfolio_metrics(selected)
                        row = {
                            "universe": universe_name,
                            "scope": scope_name,
                            "variant": variant.name,
                            "variant_type": variant.variant_type,
                            "max_positions": max_positions,
                            "sector_cap": sector_cap,
                            "cagr": metrics["cagr"],
                            "sharpe": metrics["sharpe"],
                            "max_drawdown_pct": metrics["max_drawdown_pct"],
                            "expectancy": metrics["expectancy"],
                            "profit_factor": metrics["profit_factor"],
                            "win_rate": metrics["win_rate"],
                            "trade_count": metrics["trade_count"],
                            "final_capital_proxy": metrics["final_capital_proxy"],
                            "return_pct": metrics["return_pct"],
                        }
                        rows.append(row)
                        scoped_frames[(universe_name, scope_name, variant.name, max_positions, sector_cap)] = selected
                        if variant.name == "baseline":
                            base_row = row
                    if base_row is None:
                        continue
                    for row in [r for r in rows if r["universe"] == universe_name and r["scope"] == scope_name and r["max_positions"] == max_positions and r["sector_cap"] == sector_cap]:
                        if row["variant"] == "baseline":
                            continue
                        oos_rows.append(
                            {
                                "universe": universe_name,
                                "scope": scope_name,
                                "variant": row["variant"],
                                "variant_type": row["variant_type"],
                                "max_positions": max_positions,
                                "sector_cap": sector_cap,
                                "baseline_sharpe": base_row["sharpe"],
                                "overlay_sharpe": row["sharpe"],
                                "sharpe_delta": _f(float(row["sharpe"]) - float(base_row["sharpe"])),
                                "baseline_max_drawdown_pct": base_row["max_drawdown_pct"],
                                "overlay_max_drawdown_pct": row["max_drawdown_pct"],
                                "mdd_delta": _f(float(row["max_drawdown_pct"]) - float(base_row["max_drawdown_pct"])),
                                "baseline_expectancy": base_row["expectancy"],
                                "overlay_expectancy": row["expectancy"],
                                "expectancy_delta": _f(float(row["expectancy"]) - float(base_row["expectancy"]))
                                if not pd.isna(row["expectancy"]) and not pd.isna(base_row["expectancy"])
                                else math.nan,
                                "baseline_return_pct": base_row["return_pct"],
                                "overlay_return_pct": row["return_pct"],
                                "return_delta": _f(float(row["return_pct"]) - float(base_row["return_pct"])),
                                "trade_count": row["trade_count"],
                            }
                        )
    portfolio_df = pd.DataFrame(rows)
    oos_df = pd.DataFrame([row for row in oos_rows if row["scope"] == "anchored_oos"])
    return portfolio_df, scoped_frames, oos_df


def _slot_utilization(scoped_frames: dict[tuple[str, str, str, int, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for key, frame in scoped_frames.items():
        universe_name, scope_name, variant_name, max_positions, sector_cap = key
        if frame.empty:
            rows.append(
                {
                    "universe": universe_name,
                    "scope": scope_name,
                    "variant": variant_name,
                    "max_positions": max_positions,
                    "sector_cap": sector_cap,
                    "avg_candidates_per_day": 0.0,
                    "avg_selected_per_day": 0.0,
                    "pct_filtered_out": 0.0,
                    "avg_selected_priority_score": math.nan,
                    "priority_concentration": 0.0,
                }
            )
            continue
        by_day = frame.groupby("entry_day", sort=True)
        avg_candidates = float(pd.to_numeric(frame["candidate_count_day"], errors="coerce").groupby(frame["entry_day"]).max().mean())
        avg_selected = float(by_day.size().mean())
        filtered_share = float(
            pd.to_numeric(frame["filtered_out_count_day"], errors="coerce").groupby(frame["entry_day"]).max().sum()
            / max(pd.to_numeric(frame["candidate_count_day"], errors="coerce").groupby(frame["entry_day"]).max().sum(), 1.0)
        )
        priority_share = float((_condition_mask(frame) | (pd.to_numeric(frame["priority_score"], errors="coerce") >= 3)).mean())
        rows.append(
            {
                "universe": universe_name,
                "scope": scope_name,
                "variant": variant_name,
                "max_positions": max_positions,
                "sector_cap": sector_cap,
                "avg_candidates_per_day": _f(avg_candidates),
                "avg_selected_per_day": _f(avg_selected),
                "pct_filtered_out": _f(filtered_share * 100.0),
                "avg_selected_priority_score": _f(float(pd.to_numeric(frame["priority_score"], errors="coerce").mean())),
                "priority_concentration": _f(priority_share),
            }
        )
    return pd.DataFrame(rows)


def _sector_exposure(scoped_frames: dict[tuple[str, str, str, int, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for key, frame in scoped_frames.items():
        universe_name, scope_name, variant_name, max_positions, sector_cap = key
        if frame.empty:
            continue
        total = max(len(frame), 1)
        top_sector_share = float(frame["sector_group"].astype(str).value_counts(normalize=True).iloc[0])
        top_symbol_share = float(frame["symbol"].astype(str).value_counts(normalize=True).iloc[0])
        for sector_name, sector_count in frame["sector_group"].astype(str).value_counts().items():
            rows.append(
                {
                    "universe": universe_name,
                    "scope": scope_name,
                    "variant": variant_name,
                    "max_positions": max_positions,
                    "sector_cap": sector_cap,
                    "sector_group": sector_name,
                    "sector_trade_share": _f(float(sector_count / total)),
                    "top_sector_share": _f(top_sector_share),
                    "top_symbol_share": _f(top_symbol_share),
                }
            )
    return pd.DataFrame(rows)


def _rolling_priority_flags(covered_entry_master: pd.DataFrame, window: Any) -> pd.DataFrame:
    train_start = pd.Timestamp(window.train_start, tz="UTC")
    train_end = pd.Timestamp(window.train_end, tz="UTC")
    oos_start = pd.Timestamp(window.oos_start, tz="UTC")
    oos_end = pd.Timestamp(window.oos_end, tz="UTC")
    train_df = covered_entry_master[(covered_entry_master["entry_ts"] >= train_start) & (covered_entry_master["entry_ts"] <= train_end)].copy()
    oos_df = covered_entry_master[(covered_entry_master["entry_ts"] >= oos_start) & (covered_entry_master["entry_ts"] <= oos_end)].copy()
    labeled = _rolling_label(train_df, oos_df) if not train_df.empty and not oos_df.empty else oos_df.copy()
    labeled["is_high_atr"] = labeled["atr_regime"].astype(str) == "high_atr"
    labeled["is_vol_expanding"] = labeled["contraction_regime"].astype(str) == "vol_expanding"
    labeled["is_entry_only_component"] = labeled["window_mode"].astype(str) == "entry_only"
    labeled["is_software_internet_component"] = labeled["sector_group"].astype(str) == TARGET_REGIME_SECTOR
    labeled["priority_score"] = (
        labeled["is_high_atr"].astype(int)
        + labeled["is_vol_expanding"].astype(int)
        + labeled["is_entry_only_component"].astype(int)
        + labeled["is_software_internet_component"].astype(int)
    )
    return labeled[
        [
            "trade_id",
            "is_high_atr",
            "is_vol_expanding",
            "is_entry_only_component",
            "is_software_internet_component",
            "priority_score",
        ]
    ].drop_duplicates("trade_id")


def _rolling_oos(master_df: pd.DataFrame, covered_entry_master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for universe_name in ("covered_only", "hybrid_full"):
        for window in ROLLING_WINDOWS:
            oos_start = pd.Timestamp(window.oos_start, tz="UTC")
            oos_end = pd.Timestamp(window.oos_end, tz="UTC")
            oos_full = master_df[(master_df["entry_ts"] >= oos_start) & (master_df["entry_ts"] <= oos_end)].copy()
            flags = _rolling_priority_flags(covered_entry_master, window)
            if not flags.empty:
                flag_cols = [
                    "is_high_atr",
                    "is_vol_expanding",
                    "is_entry_only_component",
                    "is_software_internet_component",
                    "priority_score",
                ]
                oos_full = oos_full.drop(columns=[c for c in flag_cols if c in oos_full.columns], errors="ignore")
                oos_full = oos_full.merge(flags.assign(trade_id=flags["trade_id"].astype(str)), on="trade_id", how="left")
                for col in (
                    "is_high_atr",
                    "is_vol_expanding",
                    "is_entry_only_component",
                    "is_software_internet_component",
                ):
                    oos_full[col] = np.where(oos_full[col].isna(), False, oos_full[col]).astype(bool)
                oos_full["is_software_internet_component"] = oos_full["sector_group"].astype(str) == TARGET_REGIME_SECTOR
                oos_full["priority_score"] = pd.to_numeric(oos_full["priority_score"], errors="coerce").fillna(0).astype(int)
            baseline_cache: dict[tuple[int, str], dict[str, Any]] = {}
            for max_positions in MAX_POSITIONS_OPTIONS:
                for sector_cap in SECTOR_CAP_OPTIONS:
                    baseline = _select_universe(oos_full, universe_name, "baseline", max_positions, sector_cap)
                    base_metrics = _portfolio_metrics(baseline)
                    baseline_cache[(max_positions, sector_cap)] = {
                        "metrics": base_metrics,
                        "trade_count": int(len(baseline)),
                        "condition_count": int(_condition_mask(baseline).sum()) if not baseline.empty else 0,
                    }
                    for variant in VARIANTS:
                        if variant.name == "baseline":
                            continue
                        selected = _select_universe(oos_full, universe_name, variant.name, max_positions, sector_cap)
                        metrics = _portfolio_metrics(selected)
                        rows.append(
                            {
                                "universe": universe_name,
                                "window_id": window.window_id,
                                "variant": variant.name,
                                "variant_type": variant.variant_type,
                                "max_positions": max_positions,
                                "sector_cap": sector_cap,
                                "subset_trade_count": baseline_cache[(max_positions, sector_cap)]["trade_count"],
                                "condition_met_trade_count": baseline_cache[(max_positions, sector_cap)]["condition_count"],
                                "baseline_expectancy": base_metrics["expectancy"],
                                "overlay_expectancy": metrics["expectancy"],
                                "baseline_sharpe_proxy": base_metrics["sharpe"],
                                "overlay_sharpe_proxy": metrics["sharpe"],
                                "baseline_mdd_proxy": base_metrics["max_drawdown_pct"],
                                "overlay_mdd_proxy": metrics["max_drawdown_pct"],
                                "status": "ok" if len(selected) > 0 else "insufficient_sample",
                            }
                        )
    return pd.DataFrame(rows)


def _execution_stress(scoped_frames: dict[tuple[str, str, str, int, str], pd.DataFrame]) -> pd.DataFrame:
    scenarios = [
        ("cost_1x", DEFAULT_COST_SCENARIOS[0].slippage_rate, DEFAULT_COST_SCENARIOS[0].fee_rate),
        ("cost_2x", DEFAULT_COST_SCENARIOS[1].slippage_rate, DEFAULT_COST_SCENARIOS[1].fee_rate),
        ("cost_3x", DEFAULT_COST_SCENARIOS[2].slippage_rate, DEFAULT_COST_SCENARIOS[2].fee_rate),
    ]
    rows = []
    for key, frame in scoped_frames.items():
        universe_name, scope_name, variant_name, max_positions, sector_cap = key
        if scope_name != "anchored_oos":
            continue
        for scenario_name, slippage, fee in scenarios:
            adjusted = frame.copy()
            adjusted["scaled_R"] = _apply_cost_scaled(frame, slippage, fee)
            metrics = _portfolio_metrics(adjusted)
            rows.append(
                {
                    "universe": universe_name,
                    "variant": variant_name,
                    "max_positions": max_positions,
                    "sector_cap": sector_cap,
                    "scenario": scenario_name,
                    "expectancy_after_cost": metrics["expectancy"],
                    "sharpe_after_cost": metrics["sharpe"],
                    "return_after_cost": metrics["return_pct"],
                    "mdd_after_cost": metrics["max_drawdown_pct"],
                    "trade_count": metrics["trade_count"],
                    "edge_survives_cost": bool(metrics["expectancy"] > 0),
                }
            )
    return pd.DataFrame(rows)


def _best_priority_variant(oos_df: pd.DataFrame) -> pd.Series:
    anchored = oos_df[
        (oos_df["universe"] == "hybrid_full")
        & (oos_df["variant"].isin(PRIORITY_VARIANTS))
    ].copy()
    anchored = anchored.sort_values(
        ["sharpe_delta", "mdd_delta", "expectancy_delta", "return_delta"],
        ascending=[False, False, False, False],
    )
    return anchored.iloc[0]


def _final_decision(
    portfolio_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    rolling_df: pd.DataFrame,
    sector_df: pd.DataFrame,
    stress_df: pd.DataFrame,
) -> pd.DataFrame:
    best = _best_priority_variant(oos_df)
    best_variant = str(best["variant"])
    max_positions = int(best["max_positions"])
    sector_cap = str(best["sector_cap"])
    rolling_best = rolling_df[
        (rolling_df["universe"] == "hybrid_full")
        & (rolling_df["variant"] == best_variant)
        & (rolling_df["max_positions"] == max_positions)
        & (rolling_df["sector_cap"] == sector_cap)
    ].copy()
    rolling_positive = int(
        (
            (pd.to_numeric(rolling_best["overlay_sharpe_proxy"], errors="coerce")
             > pd.to_numeric(rolling_best["baseline_sharpe_proxy"], errors="coerce"))
            & (pd.to_numeric(rolling_best["overlay_expectancy"], errors="coerce")
               >= pd.to_numeric(rolling_best["baseline_expectancy"], errors="coerce"))
        ).sum()
    )
    best_sector = sector_df[
        (sector_df["universe"] == "hybrid_full")
        & (sector_df["scope"] == "anchored_oos")
        & (sector_df["variant"] == best_variant)
        & (sector_df["max_positions"] == max_positions)
        & (sector_df["sector_cap"] == sector_cap)
    ].copy()
    top_sector_share = float(pd.to_numeric(best_sector["top_sector_share"], errors="coerce").max()) if not best_sector.empty else 1.0
    top_symbol_share = float(pd.to_numeric(best_sector["top_symbol_share"], errors="coerce").max()) if not best_sector.empty else 1.0
    stress_best = stress_df[
        (stress_df["universe"] == "hybrid_full")
        & (stress_df["variant"] == best_variant)
        & (stress_df["max_positions"] == max_positions)
        & (stress_df["sector_cap"] == sector_cap)
    ].copy()
    survives_2x = bool(stress_best.loc[stress_best["scenario"] == "cost_2x", "edge_survives_cost"].astype(bool).any())
    survives_3x = bool(stress_best.loc[stress_best["scenario"] == "cost_3x", "edge_survives_cost"].astype(bool).any())

    sharpe_up = float(best["sharpe_delta"]) > 0
    mdd_down = float(best["mdd_delta"]) < 0
    expectancy_up = float(best["expectancy_delta"]) >= 0
    concentration_ok = top_sector_share <= 0.60 and top_symbol_share <= 0.45

    if (not sharpe_up) or (not mdd_down) or (not expectancy_up) or rolling_positive < 2 or (not survives_2x):
        decision = "NO_TRANSLATION_EDGE"
        reason = f"{best_variant} did not convert corrected subset edge into robust hybrid_full portfolio improvement"
    elif rolling_positive < 3 or (not concentration_ok):
        decision = "WEAK_TRANSLATION"
        reason = f"{best_variant} improved anchored OOS but remains fragile on rolling stability or concentration"
    elif survives_2x and sharpe_up and mdd_down and expectancy_up and concentration_ok:
        if survives_3x:
            decision = "DEPLOYABLE_PORTFOLIO_EDGE"
            reason = f"{best_variant} improved hybrid_full OOS and survived severe cost stress under slot allocation"
        else:
            decision = "PARTIAL_TRANSLATION_EDGE"
            reason = f"{best_variant} improved hybrid_full OOS and rolling behavior but remains cost-fragile"
    else:
        decision = "WEAK_TRANSLATION"
        reason = f"{best_variant} showed only partial allocation improvement"

    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_variant": best_variant,
                "best_max_positions": max_positions,
                "best_sector_cap": sector_cap,
                "anchored_oos_sharpe_delta": _f(float(best["sharpe_delta"])),
                "anchored_oos_mdd_delta": _f(float(best["mdd_delta"])),
                "anchored_oos_expectancy_delta": _f(float(best["expectancy_delta"])),
                "rolling_positive_windows": rolling_positive,
                "survives_cost_2x": survives_2x,
                "survives_cost_3x": survives_3x,
                "top_sector_share": _f(top_sector_share),
                "top_symbol_share": _f(top_symbol_share),
            }
        ]
    )


def _markdown_report(
    out_dir: Path,
    portfolio_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    rolling_df: pd.DataFrame,
    slot_df: pd.DataFrame,
    sector_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    final_df: pd.DataFrame,
) -> None:
    final_row = final_df.iloc[0]
    best_variant = str(final_row["best_variant"])
    best_max_positions = int(final_row["best_max_positions"])
    best_sector_cap = str(final_row["best_sector_cap"])
    best_oos = oos_df[
        (oos_df["universe"] == "hybrid_full")
        & (oos_df["variant"] == best_variant)
        & (oos_df["max_positions"] == best_max_positions)
        & (oos_df["sector_cap"] == best_sector_cap)
    ].iloc[0]
    best_slot = slot_df[
        (slot_df["universe"] == "hybrid_full")
        & (slot_df["scope"] == "anchored_oos")
        & (slot_df["variant"] == best_variant)
        & (slot_df["max_positions"] == best_max_positions)
        & (slot_df["sector_cap"] == best_sector_cap)
    ].iloc[0]
    lines = [
        "# Task 347 - Conditional Priority / Slot Allocation Overlay",
        "",
        f"- decision: {final_row['decision']}",
        f"- best_variant: {best_variant}",
        f"- best_max_positions: {best_max_positions}",
        f"- best_sector_cap: {best_sector_cap}",
        f"- anchored_oos_sharpe_delta: {final_row['anchored_oos_sharpe_delta']}",
        f"- anchored_oos_mdd_delta: {final_row['anchored_oos_mdd_delta']}",
        f"- anchored_oos_expectancy_delta: {final_row['anchored_oos_expectancy_delta']}",
        f"- rolling_positive_windows: {final_row['rolling_positive_windows']}",
        f"- survives_cost_2x: {final_row['survives_cost_2x']}",
        f"- survives_cost_3x: {final_row['survives_cost_3x']}",
        "",
        "## Key Answer",
        (
            "Priority/slot allocation converts subset edge into portfolio improvement only if anchored OOS Sharpe rises, "
            "drawdown falls, and that improvement survives rolling windows and cost stress."
        ),
        "",
        "## Best Anchored OOS Comparison",
        *(
            _markdown_table(
                pd.DataFrame(
                    [
                        {
                            "variant": best_variant,
                            "sharpe_delta": best_oos["sharpe_delta"],
                            "mdd_delta": best_oos["mdd_delta"],
                            "expectancy_delta": best_oos["expectancy_delta"],
                            "return_delta": best_oos["return_delta"],
                            "trade_count": best_oos["trade_count"],
                        }
                    ]
                )
            )
        ),
        "",
        "## Slot Utilization",
        *(
            _markdown_table(
                pd.DataFrame(
                    [
                        {
                            "avg_candidates_per_day": best_slot["avg_candidates_per_day"],
                            "avg_selected_per_day": best_slot["avg_selected_per_day"],
                            "pct_filtered_out": best_slot["pct_filtered_out"],
                            "avg_selected_priority_score": best_slot["avg_selected_priority_score"],
                            "priority_concentration": best_slot["priority_concentration"],
                        }
                    ]
                )
            )
        ),
    ]
    (out_dir / "task_347_translation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 347 priority / slot allocation overlay")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master_df, covered_entry_master = _prepare_master()
    portfolio_df, scoped_frames, oos_df = _variant_rows(master_df)
    rolling_df = _rolling_oos(master_df, covered_entry_master)
    slot_df = _slot_utilization(scoped_frames)
    sector_df = _sector_exposure(scoped_frames)
    stress_df = _execution_stress(scoped_frames)
    final_df = _final_decision(portfolio_df, oos_df, rolling_df, sector_df, stress_df)

    portfolio_df.to_csv(out_dir / "task_347_portfolio_comparison.csv", index=False)
    oos_df.to_csv(out_dir / "task_347_oos_comparison.csv", index=False)
    rolling_df.to_csv(out_dir / "task_347_rolling_oos_validation.csv", index=False)
    slot_df.to_csv(out_dir / "task_347_slot_utilization.csv", index=False)
    sector_df.to_csv(out_dir / "task_347_sector_exposure.csv", index=False)
    stress_df.to_csv(out_dir / "task_347_execution_stress.csv", index=False)
    final_df.to_csv(out_dir / "task_347_final_decision.csv", index=False)
    _markdown_report(out_dir, portfolio_df, oos_df, rolling_df, slot_df, sector_df, stress_df, final_df)


if __name__ == "__main__":
    main()
