from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    _load_frozen_behavior_state,
    _markdown_table,
)
from src.backtest.analysis_structural_breakout_intraday_evaluation_fix_338 import _build_split_frames
from src.backtest.analysis_structural_breakout_intraday_signal_strengthening_339 import (
    ENTRY_ONLY,
    _breakout_subtype,
    _prepare_master_frame,
    _sector_group,
    _symbol_concentration_share,
    _train_binary_bucket,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import DB_PATH, _load_intraday_bars


DEFAULT_OUT_DIR = Path("docs/reports/task_340_subset_validation")
INITIAL_CAPITAL = 100.0
RISK_UNIT_PCT = 1.0
MIN_VALID_WINDOW_SUBSET_TRADES = 10
SIGNIFICANCE_ITERATIONS = 1000
RANDOM_STATE = 42
TARGET_WINDOW_MODE = ENTRY_ONLY


@dataclass(frozen=True)
class RollingWindow:
    window_id: str
    train_start: str
    train_end: str
    oos_start: str
    oos_end: str


@dataclass(frozen=True)
class CostScenario:
    name: str
    slippage_rate: float
    fee_rate: float


ROLLING_WINDOWS: tuple[RollingWindow, ...] = (
    RollingWindow("window_1", "2021-06-01", "2022-12-31", "2023-01-01", "2023-12-31"),
    RollingWindow("window_2", "2021-06-01", "2023-12-31", "2024-01-01", "2024-12-31"),
    RollingWindow("window_3", "2021-06-01", "2024-12-31", "2025-01-01", "2025-12-31"),
    RollingWindow("window_4", "2021-06-01", "2025-10-31", "2025-11-01", "2026-04-30"),
)

DEFAULT_COST_SCENARIOS: tuple[CostScenario, ...] = (
    CostScenario(name="Scenario 0 (baseline)", slippage_rate=0.0, fee_rate=0.0),
    CostScenario(name="Scenario 1 (0.05%)", slippage_rate=0.0005, fee_rate=0.0005),
    CostScenario(name="Scenario 2 (0.10%)", slippage_rate=0.0010, fee_rate=0.0005),
    CostScenario(name="Scenario 3 (0.20%)", slippage_rate=0.0020, fee_rate=0.0010),
)


def _max_drawdown_proxy(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    peak = equity_points[0][1]
    max_dd = 0.0
    for _ts, eq in equity_points:
        peak = max(peak, eq)
        if peak <= 0:
            continue
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    return float(max_dd * 100.0)


def _daily_sharpe_proxy(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    series = pd.Series(
        data=[value for _ts, value in equity_points],
        index=pd.to_datetime([ts for ts, _value in equity_points], utc=True),
    ).sort_index()
    daily = series.resample("1D").last().ffill().dropna()
    if len(daily) < 3:
        return 0.0
    rets = daily.pct_change().dropna()
    if rets.empty:
        return 0.0
    std = float(rets.std(ddof=0))
    if std <= 0:
        return 0.0
    return float((rets.mean() / std) * math.sqrt(252))


def _cagr_proxy(initial_capital: float, final_capital: float, start: datetime, end: datetime) -> float:
    if initial_capital <= 0 or final_capital <= 0:
        return -100.0
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1.0 / 365.25)
    return float(((final_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0)


def _assign_current_split(full_df: pd.DataFrame, train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    out = full_df.copy()
    out["identity_key"] = (
        out["symbol"].astype(str)
        + "|"
        + pd.to_datetime(out["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        + "|"
        + out["scenario"].astype(str)
    )
    train_keys = set(
        train_df["symbol"].astype(str)
        + "|"
        + pd.to_datetime(train_df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        + "|"
        + train_df["scenario"].astype(str)
    )
    oos_keys = set(
        oos_df["symbol"].astype(str)
        + "|"
        + pd.to_datetime(oos_df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        + "|"
        + oos_df["scenario"].astype(str)
    )
    out["current_split"] = np.where(
        out["identity_key"].isin(oos_keys),
        "anchored_oos",
        np.where(out["identity_key"].isin(train_keys), "train", "unmapped"),
    )
    return out.drop(columns=["identity_key"])


def _load_entry_only_master(db_path: Path) -> pd.DataFrame:
    intraday_df = _load_intraday_bars(db_path)
    _, feature_parts = _build_split_frames(intraday_df)
    _, frozen_oos, _ = _load_frozen_behavior_state()
    frozen_train, _, frozen_full = _load_frozen_behavior_state()
    master = _prepare_master_frame(feature_parts)
    master = master[master["window_mode"] == TARGET_WINDOW_MODE].copy()
    master = master[master["split"] == "full_period"].copy().reset_index(drop=True)
    master = _assign_current_split(master, frozen_train, frozen_oos)
    master["entry_ts"] = pd.to_datetime(master["entry_date"], errors="coerce")
    master["entry_year"] = master["entry_ts"].dt.year
    master["sector_group"] = master["sector_bucket"].map(_sector_group)
    master["breakout_subtype"] = master["scenario"].map(_breakout_subtype)
    master["size_proxy_bucket"] = pd.qcut(
        pd.to_numeric(master["dollar_volume_pre"], errors="coerce").rank(method="first"),
        q=3,
        labels=["small_proxy", "mid_proxy", "large_proxy"],
    ).astype(str)
    return master.reset_index(drop=True)


def _current_subset_mask(df: pd.DataFrame) -> pd.Series:
    return (df["atr_regime"].astype(str) == "high_atr") & (df["contraction_regime"].astype(str) == "vol_expanding")


def _rolling_label(train_df: pd.DataFrame, eval_df: pd.DataFrame) -> pd.DataFrame:
    labeled = eval_df.copy()
    labeled["atr_regime"] = _train_binary_bucket(train_df["range_width_10_pre"], eval_df["range_width_10_pre"], "low_atr", "high_atr")
    labeled["contraction_regime"] = _train_binary_bucket(
        train_df["vol_contraction_ratio"],
        eval_df["vol_contraction_ratio"],
        "vol_contracting",
        "vol_expanding",
    )
    return labeled


def _expectancy(df: pd.DataFrame, column: str = "realized_R") -> float:
    if df.empty:
        return math.nan
    return float(pd.to_numeric(df[column], errors="coerce").mean())


def _win_rate(df: pd.DataFrame, column: str = "realized_R") -> float:
    if df.empty:
        return math.nan
    realized = pd.to_numeric(df[column], errors="coerce")
    return float((realized > 0).mean())


def _clean_share(df: pd.DataFrame) -> float:
    if df.empty:
        return math.nan
    return float((df["cluster_label_base"].astype(str) == "clean_continuation").mean())


def _trade_ratio(subset_df: pd.DataFrame, full_df: pd.DataFrame) -> float:
    return float(len(subset_df) / max(len(full_df), 1))


def _rolling_oos_validation(master_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for window in ROLLING_WINDOWS:
        train_mask = (master_df["entry_ts"] >= pd.Timestamp(window.train_start)) & (master_df["entry_ts"] <= pd.Timestamp(window.train_end))
        oos_mask = (master_df["entry_ts"] >= pd.Timestamp(window.oos_start)) & (master_df["entry_ts"] <= pd.Timestamp(window.oos_end))
        train_df = master_df[train_mask].copy()
        oos_df = master_df[oos_mask].copy()
        labeled_oos = _rolling_label(train_df, oos_df) if not train_df.empty and not oos_df.empty else oos_df.copy()
        subset_oos = labeled_oos[
            (labeled_oos["atr_regime"].astype(str) == "high_atr")
            & (labeled_oos["contraction_regime"].astype(str) == "vol_expanding")
        ].copy()
        status = "ok" if len(subset_oos) >= MIN_VALID_WINDOW_SUBSET_TRADES else "insufficient_sample"
        baseline_expectancy = _expectancy(oos_df)
        subset_expectancy = _expectancy(subset_oos)
        rows.append(
            {
                "window_id": window.window_id,
                "train_start": window.train_start,
                "train_end": window.train_end,
                "oos_start": window.oos_start,
                "oos_end": window.oos_end,
                "oos_trade_count": int(len(oos_df)),
                "subset_trade_count": int(len(subset_oos)),
                "subset_trade_ratio": round(_trade_ratio(subset_oos, oos_df), 6),
                "oos_expectancy": round(subset_expectancy, 6) if not math.isnan(subset_expectancy) else math.nan,
                "oos_lift": round(_clean_share(subset_oos) - _clean_share(oos_df), 6) if not subset_oos.empty and not oos_df.empty else math.nan,
                "win_rate": round(_win_rate(subset_oos), 6) if not subset_oos.empty else math.nan,
                "expectancy_delta": round(subset_expectancy - baseline_expectancy, 6) if not math.isnan(subset_expectancy) and not math.isnan(baseline_expectancy) else math.nan,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def _cross_section_breakdown(master_df: pd.DataFrame, subset_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dims = [
        ("symbol", "symbol"),
        ("sector_group", "sector_group"),
        ("size_proxy_bucket", "size_proxy_bucket"),
        ("scenario_family", "scenario_family"),
        ("breakout_subtype", "breakout_subtype"),
    ]
    for scope_name in ("anchored_oos", "full_period"):
        scope_all = master_df[master_df["current_split"].isin(["train", "anchored_oos"])].copy() if scope_name == "anchored_oos" else master_df.copy()
        if scope_name == "anchored_oos":
            scope_all = master_df[master_df["current_split"] == "anchored_oos"].copy()
            scope_subset = subset_df[subset_df["current_split"] == "anchored_oos"].copy()
        else:
            scope_subset = subset_df.copy()
        scope_total_abs = pd.to_numeric(scope_subset["realized_R"], errors="coerce").abs().sum()
        for dim_type, column in dims:
            for dim_value, dim_full in scope_all.groupby(column):
                dim_subset = scope_subset[scope_subset[column].astype(str) == str(dim_value)].copy()
                status = "ok" if len(dim_subset) > 0 else "insufficient_sample"
                return_proxy = float(pd.to_numeric(dim_subset["realized_R"], errors="coerce").sum()) if not dim_subset.empty else 0.0
                contribution_share = (
                    float(pd.to_numeric(dim_subset["realized_R"], errors="coerce").abs().sum() / max(scope_total_abs, 1e-9))
                    if scope_total_abs > 0
                    else math.nan
                )
                rows.append(
                    {
                        "scope": scope_name,
                        "dimension_type": dim_type,
                        "dimension_value": str(dim_value),
                        "baseline_trade_count": int(len(dim_full)),
                        "subset_trade_count": int(len(dim_subset)),
                        "subset_expectancy": round(_expectancy(dim_subset), 6) if not dim_subset.empty else math.nan,
                        "expectancy_delta": round(_expectancy(dim_subset) - _expectancy(dim_full), 6) if not dim_subset.empty else math.nan,
                        "return_proxy": round(return_proxy, 6),
                        "symbol_contribution_share": round(contribution_share, 6) if not math.isnan(contribution_share) else math.nan,
                        "status": status,
                    }
                )
    return pd.DataFrame(rows)


def _equity_points(df: pd.DataFrame, column: str = "realized_R") -> tuple[list[tuple[datetime, float]], float]:
    scoped = df.sort_values("entry_ts").copy()
    equity = INITIAL_CAPITAL
    points: list[tuple[datetime, float]] = []
    for _, row in scoped.iterrows():
        realized_r = float(pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0])
        equity *= max(1.0 + ((realized_r * RISK_UNIT_PCT) / 100.0), 0.01)
        ts = pd.to_datetime(row["entry_ts"], utc=True).to_pydatetime()
        points.append((ts, equity))
    return points, equity


def _strategy_metrics(df: pd.DataFrame, scope_name: str) -> dict[str, Any]:
    if df.empty:
        return {
            "scope": scope_name,
            "baseline_trade_count": 0,
            "subset_trade_count": 0,
            "trade_frequency_per_year": 0.0,
            "expectancy": math.nan,
            "total_return_proxy": math.nan,
            "cagr_proxy": math.nan,
            "sharpe_proxy": math.nan,
            "max_drawdown_proxy": math.nan,
            "win_rate": math.nan,
            "status": "insufficient_sample",
        }
    points, final_capital = _equity_points(df)
    start = points[0][0]
    end = points[-1][0]
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1.0 / 365.25)
    return {
        "scope": scope_name,
        "subset_trade_count": int(len(df)),
        "trade_frequency_per_year": round(float(len(df) / years), 6),
        "expectancy": round(_expectancy(df), 6),
        "total_return_proxy": round(final_capital - INITIAL_CAPITAL, 6),
        "cagr_proxy": round(_cagr_proxy(INITIAL_CAPITAL, final_capital, start, end), 6),
        "sharpe_proxy": round(_daily_sharpe_proxy(points), 6),
        "max_drawdown_proxy": round(_max_drawdown_proxy(points), 6),
        "win_rate": round(_win_rate(df), 6),
        "status": "ok",
    }


def _subset_strategy_performance(master_df: pd.DataFrame, subset_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope_name in ("anchored_oos", "full_period"):
        if scope_name == "anchored_oos":
            scope_all = master_df[master_df["current_split"] == "anchored_oos"].copy()
            scope_subset = subset_df[subset_df["current_split"] == "anchored_oos"].copy()
        else:
            scope_all = master_df.copy()
            scope_subset = subset_df.copy()
        metrics = _strategy_metrics(scope_subset, scope_name)
        metrics["baseline_trade_count"] = int(len(scope_all))
        rows.append(metrics)
    return pd.DataFrame(rows)


def _apply_cost_to_r(df: pd.DataFrame, slippage_rate: float, fee_rate: float) -> pd.Series:
    realized = pd.to_numeric(df["realized_R"], errors="coerce")
    cost_r = (float(slippage_rate) + float(fee_rate)) / 0.01
    return realized - cost_r


def _execution_stress_test(subset_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope_name in ("anchored_oos", "full_period"):
        scoped = subset_df[subset_df["current_split"] == "anchored_oos"].copy() if scope_name == "anchored_oos" else subset_df.copy()
        for scenario in DEFAULT_COST_SCENARIOS:
            adjusted = _apply_cost_to_r(scoped, scenario.slippage_rate, scenario.fee_rate)
            rows.append(
                {
                    "scope": scope_name,
                    "scenario": scenario.name,
                    "slippage_rate": scenario.slippage_rate,
                    "fee_rate": scenario.fee_rate,
                    "expectancy_after_cost": round(float(adjusted.mean()), 6) if not adjusted.empty else math.nan,
                    "return_proxy_after_cost": round(float(adjusted.sum()), 6) if not adjusted.empty else math.nan,
                    "win_rate_after_cost": round(float((adjusted > 0).mean()), 6) if not adjusted.empty else math.nan,
                    "trade_count": int(len(scoped)),
                    "edge_survives_cost": bool(float(adjusted.mean()) > 0) if not adjusted.empty else False,
                }
            )
    return pd.DataFrame(rows)


def _statistical_significance(master_df: pd.DataFrame, subset_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)
    oos_all = master_df[master_df["current_split"] == "anchored_oos"].copy()
    oos_subset = subset_df[subset_df["current_split"] == "anchored_oos"].copy()
    observed = _expectancy(oos_subset) - _expectancy(oos_all)
    subset_count = int(len(oos_subset))
    full_values = pd.to_numeric(oos_all["realized_R"], errors="coerce").to_numpy()
    subset_values = pd.to_numeric(oos_subset["realized_R"], errors="coerce").to_numpy()
    permuted = []
    random_subset = []
    if subset_count > 0 and len(full_values) >= subset_count:
        for _ in range(SIGNIFICANCE_ITERATIONS):
            shuffled = rng.permutation(full_values)
            perm_subset = shuffled[:subset_count]
            perm_rest = shuffled[subset_count:]
            permuted.append(float(np.mean(perm_subset) - np.mean(perm_rest if len(perm_rest) else shuffled)))
            sample_idx = rng.choice(len(full_values), size=subset_count, replace=False)
            rand_subset = full_values[sample_idx]
            rand_rest = np.delete(full_values, sample_idx)
            random_subset.append(float(np.mean(rand_subset) - np.mean(rand_rest if len(rand_rest) else full_values)))
    permuted_arr = np.asarray(permuted, dtype=float) if permuted else np.asarray([math.nan])
    random_arr = np.asarray(random_subset, dtype=float) if random_subset else np.asarray([math.nan])
    rows = [
        {
            "test_name": "permutation_test",
            "observed_stat": round(observed, 6) if not math.isnan(observed) else math.nan,
            "null_mean": round(float(np.nanmean(permuted_arr)), 6) if not np.isnan(permuted_arr).all() else math.nan,
            "null_std": round(float(np.nanstd(permuted_arr)), 6) if not np.isnan(permuted_arr).all() else math.nan,
            "p_value": round(float((permuted_arr >= observed).mean()), 6) if not np.isnan(permuted_arr).all() else math.nan,
            "percentile_rank": round(float((permuted_arr <= observed).mean() * 100.0), 6) if not np.isnan(permuted_arr).all() else math.nan,
            "status": "ok",
        },
        {
            "test_name": "random_subset_comparison",
            "observed_stat": round(observed, 6) if not math.isnan(observed) else math.nan,
            "null_mean": round(float(np.nanmean(random_arr)), 6) if not np.isnan(random_arr).all() else math.nan,
            "null_std": round(float(np.nanstd(random_arr)), 6) if not np.isnan(random_arr).all() else math.nan,
            "p_value": round(float((random_arr >= observed).mean()), 6) if not np.isnan(random_arr).all() else math.nan,
            "percentile_rank": round(float((random_arr <= observed).mean() * 100.0), 6) if not np.isnan(random_arr).all() else math.nan,
            "status": "ok",
        },
    ]
    realized = pd.to_numeric(oos_subset["realized_R"], errors="coerce")
    abs_realized = realized.abs().sort_values(ascending=False)
    top3_share = float(abs_realized.head(3).sum() / max(abs_realized.sum(), 1e-9)) if not abs_realized.empty else math.nan
    negative_tail_share = float((realized < 0).mean()) if not realized.empty else math.nan
    for test_name, stat in (
        ("distribution_mean", float(realized.mean()) if not realized.empty else math.nan),
        ("distribution_median", float(realized.median()) if not realized.empty else math.nan),
        ("distribution_skewness", float(realized.skew()) if len(realized.dropna()) >= 3 else math.nan),
        ("distribution_top3_abs_share", top3_share),
        ("distribution_negative_tail_share", negative_tail_share),
    ):
        rows.append(
            {
                "test_name": test_name,
                "observed_stat": round(stat, 6) if not math.isnan(stat) else math.nan,
                "null_mean": math.nan,
                "null_std": math.nan,
                "p_value": math.nan,
                "percentile_rank": math.nan,
                "status": "ok",
            }
        )
    return pd.DataFrame(rows)


def _engine_integration_spec() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "subset_rule_1",
                "window_mode": "entry_only",
                "feature_name": "window_mode",
                "operator": "==",
                "threshold_source": "fixed",
                "real_time_available": True,
                "lookahead_risk": False,
                "integration_note": "Evaluate trade only on the entry-only track using data available by breakout bar close.",
            },
            {
                "rule_id": "subset_rule_2",
                "window_mode": "entry_only",
                "feature_name": "range_width_10_pre",
                "operator": "> train_median",
                "threshold_source": "rolling_train_window_median",
                "real_time_available": True,
                "lookahead_risk": False,
                "integration_note": "ATR proxy is computed from pre-entry daily bars and is available before entry.",
            },
            {
                "rule_id": "subset_rule_3",
                "window_mode": "entry_only",
                "feature_name": "vol_contraction_ratio",
                "operator": "> train_median",
                "threshold_source": "rolling_train_window_median",
                "real_time_available": True,
                "lookahead_risk": False,
                "integration_note": "Volatility expansion proxy uses only pre-entry information and fits current engine flow.",
            },
        ]
    )


def _final_decision(
    rolling_df: pd.DataFrame,
    breakdown_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    significance_df: pd.DataFrame,
    integration_df: pd.DataFrame,
) -> pd.DataFrame:
    valid = rolling_df[rolling_df["status"] == "ok"].copy()
    non_positive = int((pd.to_numeric(valid["oos_expectancy"], errors="coerce") <= 0).sum()) if not valid.empty else 0
    valid_count = int(len(valid))
    perm_row = significance_df[significance_df["test_name"] == "permutation_test"].iloc[0]
    rand_row = significance_df[significance_df["test_name"] == "random_subset_comparison"].iloc[0]
    symbol_rows = breakdown_df[(breakdown_df["scope"] == "anchored_oos") & (breakdown_df["dimension_type"] == "symbol")].copy()
    concentration_flag = bool((pd.to_numeric(symbol_rows["symbol_contribution_share"], errors="coerce") > 0.60).any()) if not symbol_rows.empty else False
    scenario1 = stress_df[(stress_df["scope"] == "anchored_oos") & (stress_df["scenario"].astype(str).str.contains("0.05%"))]
    scenario2 = stress_df[(stress_df["scope"] == "anchored_oos") & (stress_df["scenario"].astype(str).str.contains("0.10%"))]
    survives_s1 = bool(scenario1["edge_survives_cost"].any()) if not scenario1.empty else False
    survives_s2 = bool(scenario2["edge_survives_cost"].any()) if not scenario2.empty else False
    realtime_ok = bool(integration_df["real_time_available"].all() and (~integration_df["lookahead_risk"]).all())

    decision = "WEAK_EDGE_KEEP_RESEARCH"
    reason = "subset keeps some edge, but robustness is not strong enough yet"
    if (
        valid_count == 0
        or non_positive > (valid_count / 2)
        or concentration_flag
        or float(perm_row["p_value"]) > 0.10
        or float(rand_row["percentile_rank"]) < 80.0
        or not survives_s1
    ):
        decision = "REJECT_SUBSET"
        reason = "subset fails one or more core robustness checks across time, concentration, cost, or significance"
    elif (
        valid_count >= 3
        and non_positive <= 1
        and not concentration_flag
        and survives_s1
        and survives_s2
        and float(perm_row["p_value"]) <= 0.10
        and float(rand_row["percentile_rank"]) >= 80.0
        and realtime_ok
    ):
        decision = "STRONG_EDGE_READY_FOR_DEPLOYMENT"
        reason = "subset remains positive across rolling windows, survives cost stress, and is computable in real time"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "valid_rolling_windows": valid_count,
                "non_positive_windows": non_positive,
                "symbol_concentration_flag": concentration_flag,
                "survives_scenario_1": survives_s1,
                "survives_scenario_2": survives_s2,
                "permutation_p_value": perm_row["p_value"],
                "random_subset_percentile_rank": rand_row["percentile_rank"],
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 340: validate strong subset and engine integration feasibility.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master_df = _load_entry_only_master(Path(args.db_path))
    subset_df = master_df[_current_subset_mask(master_df)].copy().reset_index(drop=True)

    rolling_df = _rolling_oos_validation(master_df)
    breakdown_df = _cross_section_breakdown(master_df, subset_df)
    stress_df = _execution_stress_test(subset_df)
    strategy_df = _subset_strategy_performance(master_df, subset_df)
    significance_df = _statistical_significance(master_df, subset_df)
    integration_df = _engine_integration_spec()
    final_decision_df = _final_decision(rolling_df, breakdown_df, stress_df, significance_df, integration_df)

    md_lines = [
        "# Task 340: Strong Subset Validation",
        "",
        f"- Final decision: `{final_decision_df.iloc[0]['decision']}`.",
        f"- Decision reason: {final_decision_df.iloc[0]['decision_reason']}",
        "",
        "## Rolling OOS Validation",
        "",
    ]
    md_lines.extend(_markdown_table(rolling_df))
    md_lines.extend(["", "## Symbol/Sector Breakdown", ""])
    md_lines.extend(_markdown_table(breakdown_df.head(30)))
    md_lines.extend(["", "## Execution Stress Test", ""])
    md_lines.extend(_markdown_table(stress_df))
    md_lines.extend(["", "## Subset Strategy Performance", ""])
    md_lines.extend(_markdown_table(strategy_df))
    md_lines.extend(["", "## Statistical Significance", ""])
    md_lines.extend(_markdown_table(significance_df))
    md_lines.extend(
        [
            "",
            "## Final Answer",
            "",
            "- The strongest subset is validated as a fixed rule: `entry_only + high_atr + vol_expanding`.",
            "- Rolling validation uses train-refit thresholds only and does not change the subset definition.",
            "- Engine integration is feasible only if pre-entry daily features remain available at decision time with no lookahead.",
        ]
    )

    rolling_df.to_csv(out_dir / "task_340_rolling_oos_validation.csv", index=False)
    breakdown_df.to_csv(out_dir / "task_340_symbol_sector_breakdown.csv", index=False)
    stress_df.to_csv(out_dir / "task_340_execution_stress_test.csv", index=False)
    strategy_df.to_csv(out_dir / "task_340_subset_strategy_performance.csv", index=False)
    significance_df.to_csv(out_dir / "task_340_statistical_significance.csv", index=False)
    integration_df.to_csv(out_dir / "task_340_engine_integration_spec.csv", index=False)
    final_decision_df.to_csv(out_dir / "task_340_final_decision.csv", index=False)
    (out_dir / "task_340_subset_validation.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
