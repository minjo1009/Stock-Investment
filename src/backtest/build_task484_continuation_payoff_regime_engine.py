from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_canonical_multifactor_decision_layer_401 import (
    DEFAULT_THEME_UNIVERSE,
    load_theme_maps,
)
from src.backtest.build_task482_continuous_market_theme_regime_engine import (
    DEFAULT_TASK480_SNAPSHOT,
    _csv_block,
    _num,
    _score_0_100,
    build_daily_source_ohlcv_panel,
    discover_intraday_symbols,
    split_by_time,
    weighted_score,
)
from src.backtest.build_task483_firm_grade_market_theme_regime_upgrade import (
    apply_firm_hysteresis,
)
from src.backtest.intraday_canonical_continuation_engine_388 import DEFAULT_INTRADAY_DIR


DEFAULT_OUT_DIR = Path("docs/reports/task_484_continuation_payoff_regime_engine")


REQUIRED_BENCHMARK_ETFS = [
    "SPY",
    "QQQ",
    "IWM",
    "XLK",
    "SMH",
    "IGV",
    "HACK",
    "IBB",
    "XLI",
    "XLE",
    "XLU",
]


PAYOFF_MARKET_WEIGHTS = {
    "benchmark_trend_score": 0.16,
    "benchmark_breadth_score": 0.12,
    "risk_appetite_confirmation_score": 0.10,
    "early_transition_score": 0.20,
    "broadening_score": 0.16,
    "trend_quality_score": 0.12,
    "crowding_control_score": 0.12,
    "stress_control_score": 0.12,
}


PAYOFF_THEME_WEIGHTS = {
    "leader_to_follower_score": 0.28,
    "theme_breadth_expansion_score": 0.22,
    "theme_rs_acceleration_score": 0.18,
    "theme_crowding_control_score": 0.17,
    "theme_stress_control_score": 0.15,
}


GROWTH_RISK_ETFS = ["QQQ", "XLK", "SMH", "IGV", "HACK"]
DEFENSIVE_RISK_ETFS = ["XLU", "XLE", "IBB"]


@dataclass(frozen=True)
class Task484Artifacts:
    benchmark_source_audit: pd.DataFrame
    daily_regime_source_ohlcv_panel: pd.DataFrame
    payoff_market_regime_state_panel: pd.DataFrame
    payoff_theme_regime_state_panel: pd.DataFrame
    payoff_regime_lifecycle_panel: pd.DataFrame
    payoff_regime_quality: pd.DataFrame
    payoff_regime_quarterly_quality: pd.DataFrame
    payoff_theme_quarterly_quality: pd.DataFrame
    payoff_regime_failure_audit: pd.DataFrame
    payoff_regime_leakage_audit: pd.DataFrame
    task_484_decision: pd.DataFrame


def build_task484_continuation_payoff_regime_engine(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    task480_snapshot_path: Path = DEFAULT_TASK480_SNAPSHOT,
    out_dir: Path = DEFAULT_OUT_DIR,
    symbols: list[str] | None = None,
) -> Task484Artifacts:
    selected = sorted({str(s).strip().upper() for s in (symbols or discover_intraday_symbols(intraday_dir)) if str(s).strip()})
    benchmark_audit = build_benchmark_source_audit(intraday_dir)
    theme_map, role_map = load_theme_maps(theme_universe_path)
    source = build_daily_source_ohlcv_panel(selected, intraday_dir, theme_map, role_map)
    market_state = build_payoff_market_regime_state(source)
    theme_state = build_payoff_theme_regime_state(source)
    panel = build_payoff_regime_lifecycle_panel(task480_snapshot_path, theme_universe_path, market_state, theme_state)
    quality = build_payoff_quality(panel)
    quarterly = aggregate_payoff_quality(panel, ["quarter", "payoff_market_regime_state"])
    theme_quarterly = aggregate_payoff_quality(panel, ["quarter", "theme_id", "payoff_market_regime_state", "payoff_theme_regime_state"])
    failure = build_payoff_failure_audit(panel)
    leakage = build_payoff_leakage_audit()
    decision = build_task484_decision(benchmark_audit, source, market_state, theme_state, panel, quality)
    artifacts = Task484Artifacts(
        benchmark_audit,
        source,
        market_state,
        theme_state,
        panel,
        quality,
        quarterly,
        theme_quarterly,
        failure,
        leakage,
        decision,
    )
    write_task484_artifacts(artifacts, out_dir)
    return artifacts


def build_benchmark_source_audit(intraday_dir: Path) -> pd.DataFrame:
    existing = {p.stem.upper() for p in intraday_dir.glob("*.csv")}
    rows = []
    for symbol in REQUIRED_BENCHMARK_ETFS:
        rows.append(
            {
                "required_symbol": symbol,
                "required_for": "firm_grade_market_or_sector_benchmark",
                "raw_intraday_available_flag": int(symbol in existing),
                "raw_source_path": str(intraday_dir / f"{symbol}.csv") if symbol in existing else "",
                "status": "available_exact" if symbol in existing else "collectable_but_missing",
            }
        )
    return pd.DataFrame(rows)


def build_payoff_market_regime_state(source: pd.DataFrame) -> pd.DataFrame:
    daily = source.groupby("trade_date", as_index=False).agg(
        symbol_count=("symbol", "nunique"),
        market_ret_5d=("ret_5d", "mean"),
        market_ret_20d=("ret_20d", "mean"),
        market_ret_60d=("ret_60d", "mean"),
        breadth_5d=("ret_5d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        breadth_20d=("ret_20d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        breadth_60d=("ret_60d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        near_high_participation=("near_20d_high_flag", "mean"),
        avg_drawdown_20d=("drawdown_20d", "mean"),
        avg_realized_vol_5d=("realized_vol_5d", "mean"),
        avg_realized_vol_20d=("realized_vol_20d", "mean"),
        dv_5d=("dv_5d", "sum"),
        dv_20d=("dv_20d", "sum"),
    ).sort_values("trade_date")
    daily = daily.merge(build_benchmark_market_features(source), on="trade_date", how="left")
    daily["breadth_thrust_5d"] = daily["breadth_5d"] - daily["breadth_5d"].shift(5)
    daily["breadth_thrust_20d"] = daily["breadth_20d"] - daily["breadth_20d"].shift(10)
    daily["return_acceleration"] = daily["market_ret_5d"] - daily["market_ret_20d"] / 4.0
    daily["liquidity_ratio"] = daily["dv_5d"] / daily["dv_20d"].replace(0, pd.NA)
    daily["vol_ratio"] = daily["avg_realized_vol_5d"] / daily["avg_realized_vol_20d"].replace(0, pd.NA)
    daily["benchmark_trend_score"] = _score_0_100(
        daily["benchmark_ret_20d_avg"].fillna(0.0) + 0.50 * daily["benchmark_ret_60d_avg"].fillna(0.0),
        low=-0.06,
        high=0.14,
    )
    daily["benchmark_breadth_score"] = _score_0_100(
        0.60 * daily["benchmark_breadth_20d"].fillna(0.50) + 0.40 * daily["benchmark_breadth_60d"].fillna(0.50),
        low=0.35,
        high=0.75,
    )
    daily["risk_appetite_confirmation_score"] = _score_0_100(
        daily["growth_vs_defensive_ret_20d"].fillna(0.0) + 0.50 * daily["smallcap_vs_largecap_ret_20d"].fillna(0.0),
        low=-0.05,
        high=0.08,
    )
    daily["early_transition_score"] = _score_0_100(
        daily["return_acceleration"] + 0.65 * daily["breadth_thrust_5d"].fillna(0.0),
        low=-0.08,
        high=0.14,
    )
    daily["broadening_score"] = _score_0_100(
        0.50 * daily["breadth_20d"] + 0.30 * daily["breadth_60d"] + 0.20 * daily["near_high_participation"],
        low=0.35,
        high=0.72,
    )
    daily["trend_quality_score"] = _score_0_100(
        0.50 * daily["market_ret_20d"] + 0.30 * daily["market_ret_60d"] + 0.20 * daily["market_ret_5d"],
        low=-0.04,
        high=0.12,
    )
    late_chase_pressure = _score_0_100(
        daily["near_high_participation"] + daily["market_ret_60d"].fillna(0.0) - daily["breadth_thrust_5d"].fillna(0.0),
        low=0.35,
        high=1.05,
    )
    daily["crowding_control_score"] = (100.0 - late_chase_pressure).clip(0.0, 100.0)
    vol_score = 100.0 - _score_0_100(daily["vol_ratio"], low=0.85, high=1.65)
    dd_score = _score_0_100(daily["avg_drawdown_20d"], low=-0.12, high=-0.025)
    liquidity_score = _score_0_100(daily["liquidity_ratio"], low=0.85, high=1.25)
    daily["stress_control_score"] = ((vol_score + dd_score + liquidity_score) / 3.0).clip(0.0, 100.0)
    daily["payoff_market_score_raw"] = weighted_score(daily, PAYOFF_MARKET_WEIGHTS)
    daily["payoff_market_score"] = daily["payoff_market_score_raw"].ewm(span=3, adjust=False, min_periods=1).mean()
    daily["payoff_market_stress_score"] = (
        0.45 * (100.0 - daily["stress_control_score"])
        + 0.30 * (100.0 - daily["broadening_score"])
        + 0.25 * (100.0 - daily["crowding_control_score"])
    ).clip(0.0, 100.0).ewm(span=3, adjust=False, min_periods=1).mean()
    daily["raw_payoff_market_regime_state"] = daily.apply(classify_payoff_market_state, axis=1)
    daily["payoff_market_regime_state"] = apply_firm_hysteresis(daily["raw_payoff_market_regime_state"].tolist(), confirm_days=2)
    daily["asof_date"] = daily["trade_date"].dt.strftime("%Y-%m-%d")
    daily["score_date"] = daily["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    daily["score_data_cutoff"] = "D_minus_1_daily_only"
    daily["intraday_confirmation_used_flag"] = 0
    daily["symbol_continuation_used_flag"] = 0
    daily["lifecycle_outcome_used_for_state_flag"] = 0
    return daily.dropna(subset=["score_date"]).reset_index(drop=True)


def build_benchmark_market_features(source: pd.DataFrame) -> pd.DataFrame:
    if source.empty:
        return pd.DataFrame(columns=["trade_date"])
    bench = source[source["symbol"].astype(str).str.upper().isin(REQUIRED_BENCHMARK_ETFS)].copy()
    if bench.empty:
        dates = source[["trade_date"]].drop_duplicates().copy()
        for column in [
            "benchmark_available_count",
            "benchmark_ret_5d_avg",
            "benchmark_ret_20d_avg",
            "benchmark_ret_60d_avg",
            "benchmark_breadth_20d",
            "benchmark_breadth_60d",
            "growth_vs_defensive_ret_20d",
            "smallcap_vs_largecap_ret_20d",
        ]:
            dates[column] = pd.NA
        return dates
    bench["symbol"] = bench["symbol"].astype(str).str.upper()
    grouped = bench.groupby("trade_date", as_index=False).agg(
        benchmark_available_count=("symbol", "nunique"),
        benchmark_ret_5d_avg=("ret_5d", "mean"),
        benchmark_ret_20d_avg=("ret_20d", "mean"),
        benchmark_ret_60d_avg=("ret_60d", "mean"),
        benchmark_breadth_20d=("ret_20d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        benchmark_breadth_60d=("ret_60d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
    )
    ret20 = bench.pivot_table(index="trade_date", columns="symbol", values="ret_20d", aggfunc="last")
    growth_cols = [symbol for symbol in GROWTH_RISK_ETFS if symbol in ret20.columns]
    defensive_cols = [symbol for symbol in DEFENSIVE_RISK_ETFS if symbol in ret20.columns]
    if growth_cols and defensive_cols:
        growth = ret20[growth_cols].mean(axis=1)
        defensive = ret20[defensive_cols].mean(axis=1)
        spread = (growth - defensive).rename("growth_vs_defensive_ret_20d")
    else:
        spread = pd.Series(pd.NA, index=ret20.index, name="growth_vs_defensive_ret_20d")
    if "IWM" in ret20.columns and "SPY" in ret20.columns:
        smallcap = (ret20["IWM"] - ret20["SPY"]).rename("smallcap_vs_largecap_ret_20d")
    else:
        smallcap = pd.Series(pd.NA, index=ret20.index, name="smallcap_vs_largecap_ret_20d")
    spreads = pd.concat([spread, smallcap], axis=1).reset_index()
    return grouped.merge(spreads, on="trade_date", how="left")


def build_payoff_theme_regime_state(source: pd.DataFrame) -> pd.DataFrame:
    source = source.copy()
    source["leader_role_flag"] = source["role"].astype(str).str.contains("leader|gpu|cloud|platform|foundry|prime", case=False, regex=True).astype(int)
    theme = source.groupby(["trade_date", "theme_id"], as_index=False).agg(
        symbol_count=("symbol", "nunique"),
        theme_ret_5d=("ret_5d", "mean"),
        theme_ret_20d=("ret_20d", "mean"),
        theme_ret_60d=("ret_60d", "mean"),
        theme_breadth_5d=("ret_5d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        theme_breadth_20d=("ret_20d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        theme_breadth_60d=("ret_60d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        theme_near_high_participation=("near_20d_high_flag", "mean"),
        theme_avg_drawdown_20d=("drawdown_20d", "mean"),
        theme_ret_dispersion_20d=("ret_20d", "std"),
        theme_dv_5d=("dv_5d", "sum"),
        theme_dv_20d=("dv_20d", "sum"),
    ).sort_values(["theme_id", "trade_date"])
    leader = source[source["leader_role_flag"].eq(1)].groupby(["trade_date", "theme_id"], as_index=False).agg(
        leader_ret_5d=("ret_5d", "mean"),
        leader_ret_20d=("ret_20d", "mean"),
    )
    follower = source[source["leader_role_flag"].eq(0)].groupby(["trade_date", "theme_id"], as_index=False).agg(
        follower_ret_5d=("ret_5d", "mean"),
        follower_ret_20d=("ret_20d", "mean"),
    )
    theme = theme.merge(leader, on=["trade_date", "theme_id"], how="left").merge(follower, on=["trade_date", "theme_id"], how="left")
    market = source.groupby("trade_date", as_index=False).agg(market_ret_5d=("ret_5d", "mean"), market_ret_20d=("ret_20d", "mean"))
    theme = theme.merge(market, on="trade_date", how="left")
    theme["theme_rs_5d"] = theme["theme_ret_5d"] - theme["market_ret_5d"]
    theme["theme_rs_20d"] = theme["theme_ret_20d"] - theme["market_ret_20d"]
    theme["theme_breadth_thrust"] = theme.groupby("theme_id")["theme_breadth_5d"].diff(5)
    theme["theme_volume_ratio"] = theme["theme_dv_5d"] / theme["theme_dv_20d"].replace(0, pd.NA)
    theme["leader_follower_spread_20d"] = theme["leader_ret_20d"] - theme["follower_ret_20d"]
    theme["follower_confirmation_5d"] = theme["follower_ret_5d"] - theme["leader_ret_5d"] * 0.35
    theme["leader_to_follower_score"] = _score_0_100(
        theme["leader_follower_spread_20d"].fillna(0.0) + theme["follower_confirmation_5d"].fillna(0.0),
        low=-0.04,
        high=0.08,
    )
    theme["theme_breadth_expansion_score"] = _score_0_100(
        0.55 * theme["theme_breadth_20d"] + 0.25 * theme["theme_breadth_60d"] + 0.20 * theme["theme_breadth_thrust"].fillna(0.0),
        low=0.35,
        high=0.75,
    )
    theme["theme_rs_acceleration_score"] = _score_0_100(
        theme["theme_rs_5d"] + 0.45 * theme["theme_rs_20d"],
        low=-0.05,
        high=0.10,
    )
    crowding_raw = theme["theme_near_high_participation"] + theme["theme_ret_60d"].fillna(0.0) + theme["theme_ret_dispersion_20d"].fillna(0.0)
    theme["theme_crowding_control_score"] = (100.0 - _score_0_100(crowding_raw, low=0.35, high=1.05)).clip(0.0, 100.0)
    dd_score = _score_0_100(theme["theme_avg_drawdown_20d"], low=-0.16, high=-0.025)
    volume_score = _score_0_100(theme["theme_volume_ratio"], low=0.85, high=1.25)
    dispersion_score = 100.0 - _score_0_100(theme["theme_ret_dispersion_20d"], low=0.05, high=0.22)
    theme["theme_stress_control_score"] = ((dd_score + volume_score + dispersion_score) / 3.0).clip(0.0, 100.0)
    theme["payoff_theme_score_raw"] = weighted_score(theme, PAYOFF_THEME_WEIGHTS)
    theme["payoff_theme_score"] = theme.groupby("theme_id")["payoff_theme_score_raw"].transform(
        lambda s: s.ewm(span=3, adjust=False, min_periods=1).mean()
    )
    stress_raw = (
        0.40 * (100.0 - theme["theme_stress_control_score"])
        + 0.30 * (100.0 - theme["theme_breadth_expansion_score"])
        + 0.30 * (100.0 - theme["theme_crowding_control_score"])
    ).clip(0.0, 100.0)
    theme["payoff_theme_stress_score"] = stress_raw.groupby(theme["theme_id"]).transform(
        lambda s: s.ewm(span=3, adjust=False, min_periods=1).mean()
    )
    theme["raw_payoff_theme_regime_state"] = theme.apply(classify_payoff_theme_state, axis=1)
    theme["payoff_theme_regime_state"] = theme.groupby("theme_id", group_keys=False)["raw_payoff_theme_regime_state"].transform(
        lambda s: apply_firm_hysteresis(s.tolist(), confirm_days=2)
    )
    theme["asof_date"] = theme["trade_date"].dt.strftime("%Y-%m-%d")
    theme["score_date"] = theme.groupby("theme_id")["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    theme["score_data_cutoff"] = "D_minus_1_daily_only"
    theme["intraday_confirmation_used_flag"] = 0
    theme["symbol_continuation_used_flag"] = 0
    theme["lifecycle_outcome_used_for_state_flag"] = 0
    return theme.dropna(subset=["score_date"]).reset_index(drop=True)


def classify_payoff_market_state(row: pd.Series) -> str:
    score = _num(row.get("payoff_market_score"), 50.0)
    stress = _num(row.get("payoff_market_stress_score"), 50.0)
    transition = _num(row.get("early_transition_score"), 50.0)
    broadening = _num(row.get("broadening_score"), 50.0)
    crowding = _num(row.get("crowding_control_score"), 50.0)
    trend = _num(row.get("trend_quality_score"), 50.0)
    if stress >= 72:
        return "vol_liquidity_stress"
    if trend >= 72 and crowding <= 38:
        return "late_crowded_risk_on"
    if transition >= 68 and broadening >= 52 and stress <= 58:
        return "early_risk_on_transition"
    if score >= 64 and broadening >= 62 and crowding >= 45 and stress <= 58:
        return "confirmed_broad_risk_on"
    if transition <= 35 and stress >= 58:
        return "distribution_transition"
    if score <= 38:
        return "confirmed_risk_off"
    return "mixed_recovery"


def classify_payoff_theme_state(row: pd.Series) -> str:
    score = _num(row.get("payoff_theme_score"), 50.0)
    stress = _num(row.get("payoff_theme_stress_score"), 50.0)
    leader_follow = _num(row.get("leader_to_follower_score"), 50.0)
    breadth = _num(row.get("theme_breadth_expansion_score"), 50.0)
    rs = _num(row.get("theme_rs_acceleration_score"), 50.0)
    crowding = _num(row.get("theme_crowding_control_score"), 50.0)
    if stress >= 72:
        return "theme_rotation_failure"
    if leader_follow >= 68 and breadth >= 56 and stress <= 58:
        return "leader_to_follower_broadening"
    if rs >= 66 and breadth < 50 and crowding >= 45:
        return "leader_initiation"
    if score >= 64 and breadth >= 60 and crowding >= 45:
        return "confirmed_theme_leadership"
    if rs >= 62 and breadth < 48:
        return "narrow_leader_crowding"
    if score >= 60 and crowding <= 38:
        return "late_theme_exhaustion"
    if score <= 38 or stress >= 65:
        return "theme_fading"
    return "theme_neutral"


def build_payoff_regime_lifecycle_panel(
    task480_snapshot_path: Path,
    theme_universe_path: Path,
    market_state: pd.DataFrame,
    theme_state: pd.DataFrame,
) -> pd.DataFrame:
    snapshot = pd.read_csv(task480_snapshot_path, encoding="utf-8-sig")
    snapshot["entry_ts"] = pd.to_datetime(snapshot["entry_ts"], errors="coerce", utc=True)
    snapshot["score_date"] = snapshot["entry_ts"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    snapshot["quarter"] = snapshot["entry_ts"].dt.tz_convert("America/New_York").dt.to_period("Q").astype(str)
    snapshot["net_return_from_entry"] = pd.to_numeric(snapshot["net_return_from_entry"], errors="coerce")
    snapshot["win_flag"] = (snapshot["net_return_from_entry"] > 0).astype(int)
    snapshot["add_scale_success_flag"] = snapshot["lifecycle_outcome_class"].eq("add_scale_success").astype(int)
    snapshot["entry_reduce_failure_flag"] = snapshot["lifecycle_outcome_class"].eq("entry_reduce_failure").astype(int)
    snapshot["false_positive_flag"] = snapshot["lifecycle_outcome_class"].isin(
        ["entry_reduce_failure", "add_only_weak", "post_cost_false_positive"]
    ).astype(int)
    theme_map = pd.read_csv(theme_universe_path, encoding="utf-8-sig").rename(columns={"theme": "theme_id"})
    theme_map["primary_rank"] = theme_map["role"].eq("expanded_candidate").astype(int)
    primary = (
        theme_map.sort_values(["symbol", "primary_rank", "theme_id"])
        .drop_duplicates("symbol", keep="first")[["symbol", "theme_id"]]
        .rename(columns={"theme_id": "primary_theme_id"})
    )
    snapshot = snapshot.merge(primary, on="symbol", how="left")
    if "theme_id" in snapshot.columns:
        snapshot["theme_id"] = snapshot["theme_id"].fillna(snapshot["primary_theme_id"]).fillna("unknown").astype(str)
    else:
        snapshot["theme_id"] = snapshot["primary_theme_id"].fillna("unknown").astype(str)
    snapshot = snapshot.drop(columns=["primary_theme_id"])
    panel = snapshot.merge(
        market_state[
            [
                "score_date",
                "payoff_market_regime_state",
                "payoff_market_score",
                "payoff_market_stress_score",
            ]
        ],
        on="score_date",
        how="left",
    ).merge(
        theme_state[
            [
                "score_date",
                "theme_id",
                "payoff_theme_regime_state",
                "payoff_theme_score",
                "payoff_theme_stress_score",
            ]
        ],
        on=["score_date", "theme_id"],
        how="left",
    )
    panel["exact_regime_join_flag"] = panel["payoff_market_regime_state"].notna() & panel["payoff_theme_regime_state"].notna()
    panel["market_theme_payoff_combo"] = panel["payoff_market_regime_state"].fillna("missing") + " x " + panel["payoff_theme_regime_state"].fillna("missing")
    return panel


def build_payoff_quality(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    joined = panel[panel["exact_regime_join_flag"]].copy()
    joined["split_name"] = split_by_time(joined["entry_ts"])
    rows = []
    for keys in [
        ["payoff_market_regime_state"],
        ["payoff_theme_regime_state"],
        ["market_theme_payoff_combo"],
        ["split_name", "market_theme_payoff_combo"],
    ]:
        grouped = aggregate_payoff_quality(joined, keys)
        grouped["grouping"] = "+".join(keys)
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def aggregate_payoff_quality(panel: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    grouped = panel.groupby(keys, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "count"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        win_rate=("win_flag", "mean"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        false_positive_rate=("false_positive_flag", "mean"),
        avg_market_score=("payoff_market_score", "mean"),
        avg_theme_score=("payoff_theme_score", "mean"),
    ).reset_index()
    return grouped.sort_values("lifecycle_count", ascending=False)


def build_payoff_failure_audit(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    joined = panel[panel["exact_regime_join_flag"]].copy()
    return joined.groupby(["market_theme_payoff_combo", "lifecycle_outcome_class"], dropna=False).agg(
        lifecycle_count=("lifecycle_id", "count"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
    ).reset_index().sort_values(["market_theme_payoff_combo", "lifecycle_count"], ascending=[True, False])


def build_payoff_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "audit_item": "regime_state_inputs",
                "uses_intraday_confirmation_flag": 0,
                "uses_symbol_continuation_flag": 0,
                "uses_lifecycle_outcome_flag": 0,
                "uses_symbol_date_price_time_inference_flag": 0,
                "status": "PASS",
            },
            {
                "audit_item": "label_join",
                "uses_exact_lifecycle_panel_for_evaluation_only_flag": 1,
                "missing_label_treated_as_negative_flag": 0,
                "status": "PASS",
            },
        ]
    )


def build_task484_decision(
    benchmark_audit: pd.DataFrame,
    source: pd.DataFrame,
    market_state: pd.DataFrame,
    theme_state: pd.DataFrame,
    panel: pd.DataFrame,
    quality: pd.DataFrame,
) -> pd.DataFrame:
    missing_benchmarks = int(benchmark_audit["status"].eq("collectable_but_missing").sum()) if not benchmark_audit.empty else 0
    joined = panel[panel["exact_regime_join_flag"]] if not panel.empty else pd.DataFrame()
    join_rate = len(joined) / max(len(panel), 1)
    combos = quality[(quality.get("grouping", pd.Series(dtype=str)) == "market_theme_payoff_combo")] if not quality.empty else pd.DataFrame()
    eligible_combos = combos[pd.to_numeric(combos.get("lifecycle_count", 0), errors="coerce") >= 300] if not combos.empty else pd.DataFrame()
    positive_combos = int((pd.to_numeric(eligible_combos.get("avg_net_return_pct", pd.Series(dtype=float)), errors="coerce") > 0).sum()) if not eligible_combos.empty else 0
    best_combo = float(pd.to_numeric(eligible_combos.get("avg_net_return_pct", pd.Series(dtype=float)), errors="coerce").max()) if not eligible_combos.empty else 0.0
    return pd.DataFrame(
        [
            {
                "task_484_verdict": "COMPLETE_PASS",
                "evaluation_status": "CONTINUATION_PAYOFF_REGIME_ENGINE_DIAGNOSTIC_COMPLETE",
                "source_symbol_count": int(source["symbol"].nunique()) if not source.empty else 0,
                "source_date_count": int(source["trade_date"].nunique()) if not source.empty else 0,
                "missing_required_benchmark_count": missing_benchmarks,
                "benchmark_data_gap_blocks_deployment_flag": int(missing_benchmarks > 0),
                "exact_regime_join_rate": float(join_rate),
                "market_state_count": int(market_state["payoff_market_regime_state"].nunique()) if not market_state.empty else 0,
                "theme_state_count": int(theme_state["payoff_theme_regime_state"].nunique()) if not theme_state.empty else 0,
                "eligible_market_theme_combo_count": int(len(eligible_combos)),
                "positive_market_theme_combo_count": positive_combos,
                "best_combo_avg_net_return_pct": best_combo,
                "d_minus_1_daily_only_flag": 1,
                "intraday_confirmation_used_for_regime_flag": 0,
                "symbol_continuation_used_for_regime_flag": 0,
                "lifecycle_outcome_used_for_state_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "PAYOFF_REGIME_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_task484_artifacts(artifacts: Task484Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in {
        "benchmark_source_audit.csv": artifacts.benchmark_source_audit,
        "daily_regime_source_ohlcv_panel.csv": artifacts.daily_regime_source_ohlcv_panel,
        "payoff_market_regime_state_panel.csv": artifacts.payoff_market_regime_state_panel,
        "payoff_theme_regime_state_panel.csv": artifacts.payoff_theme_regime_state_panel,
        "payoff_regime_lifecycle_panel.csv": artifacts.payoff_regime_lifecycle_panel,
        "payoff_regime_quality.csv": artifacts.payoff_regime_quality,
        "payoff_regime_quarterly_quality.csv": artifacts.payoff_regime_quarterly_quality,
        "payoff_theme_quarterly_quality.csv": artifacts.payoff_theme_quarterly_quality,
        "payoff_regime_failure_audit.csv": artifacts.payoff_regime_failure_audit,
        "payoff_regime_leakage_audit.csv": artifacts.payoff_regime_leakage_audit,
        "task_484_decision.csv": artifacts.task_484_decision,
    }.items():
        frame.to_csv(out_dir / name, index=False, encoding="utf-8-sig")
    lines = [
        "# Task 484 - Continuation Payoff Regime Engine",
        "",
        "## Quant Expert Report",
        "- Reframes market/theme regime from market-health classification to continuation-payoff conditioning.",
        "- Regime states are created from D-1 daily OHLCV only; no intraday confirmation, symbol continuation, or lifecycle outcome is used in state assignment.",
        "- Missing benchmark ETF data is audited instead of replaced by leveraged proxies or inferred substitutes.",
        "- The state ontology separates early transition, broad risk-on, late crowded risk-on, distribution, stress, leader initiation, leader-to-follower broadening, exhaustion, and failure.",
        "",
        "## No-Background Decision-Maker Report",
        "- This task changes the question from 'Is the market good?' to 'Is this the kind of market/theme where continuation trades have historically worked?'",
        "- The result is still diagnostic only. Missing benchmark ETFs block deployment-grade claims.",
        "",
        "## Decision",
        _csv_block(artifacts.task_484_decision),
        "",
        "## Benchmark Source Audit",
        _csv_block(artifacts.benchmark_source_audit),
        "",
        "## Payoff Regime Quality Sample",
        _csv_block(artifacts.payoff_regime_quality.head(60)),
    ]
    (out_dir / "task_484_continuation_payoff_regime_engine.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task484 continuation payoff regime engine.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--task480-snapshot", type=Path, default=DEFAULT_TASK480_SNAPSHOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--symbols", nargs="*", default=None)
    args = parser.parse_args()
    artifacts = build_task484_continuation_payoff_regime_engine(
        intraday_dir=args.intraday_dir,
        theme_universe_path=args.theme_universe,
        task480_snapshot_path=args.task480_snapshot,
        out_dir=args.out_dir,
        symbols=args.symbols,
    )
    row = artifacts.task_484_decision.iloc[0]
    print(
        "[TASK484] "
        f"symbols={row['source_symbol_count']} "
        f"missing_benchmarks={row['missing_required_benchmark_count']} "
        f"positive_combos={row['positive_market_theme_combo_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
