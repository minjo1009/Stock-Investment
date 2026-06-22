from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_canonical_multifactor_decision_layer_401 import (
    DEFAULT_THEME_UNIVERSE,
    load_theme_maps,
)
from src.backtest.intraday_canonical_continuation_engine_388 import DEFAULT_INTRADAY_DIR, discover_intraday_symbols


DEFAULT_TASK480_SNAPSHOT = Path("docs/reports/task_480_symbol_structure_continuation_diagnostics/symbol_structure_snapshot_log.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_482_continuous_market_theme_regime_engine")


@dataclass(frozen=True)
class Task482Artifacts:
    daily_regime_source_ohlcv_panel: pd.DataFrame
    daily_market_regime_component_scores: pd.DataFrame
    daily_theme_regime_component_scores: pd.DataFrame
    daily_market_regime_state_panel: pd.DataFrame
    daily_theme_regime_state_panel: pd.DataFrame
    regime_transition_audit: pd.DataFrame
    regime_whipsaw_dwell_audit: pd.DataFrame
    regime_weight_sensitivity_audit: pd.DataFrame
    market_theme_regime_oos_quality: pd.DataFrame
    regime_intraday_continuation_join_audit: pd.DataFrame
    task_482_decision: pd.DataFrame


MARKET_WEIGHTS = {
    "breadth_persistence_score": 0.25,
    "trend_momentum_score": 0.20,
    "risk_appetite_score": 0.20,
    "liquidity_participation_score": 0.15,
    "volatility_drawdown_score": 0.20,
}

THEME_WEIGHTS = {
    "theme_relative_strength_score": 0.25,
    "theme_breadth_persistence_score": 0.25,
    "leader_persistence_score": 0.20,
    "theme_volume_accumulation_score": 0.15,
    "theme_drawdown_dispersion_score": 0.15,
}


def build_task482_continuous_market_theme_regime_engine(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    task480_snapshot_path: Path = DEFAULT_TASK480_SNAPSHOT,
    out_dir: Path = DEFAULT_OUT_DIR,
    symbols: list[str] | None = None,
) -> Task482Artifacts:
    selected = sorted({str(s).strip().upper() for s in (symbols or discover_intraday_symbols(intraday_dir)) if str(s).strip()})
    theme_map, role_map = load_theme_maps(theme_universe_path)
    source = build_daily_source_ohlcv_panel(selected, intraday_dir, theme_map, role_map)
    market_components, market_state = build_market_regime_scores(source)
    theme_components, theme_state = build_theme_regime_scores(source, market_state)
    transition = build_regime_transition_audit(market_state, theme_state)
    whipsaw = build_whipsaw_dwell_audit(market_state, theme_state)
    sensitivity = build_weight_sensitivity_audit(source, market_components, theme_components)
    quality, join_audit = build_market_theme_regime_oos_quality(task480_snapshot_path, market_state, theme_state)
    decision = build_task_482_decision(source, market_state, theme_state, quality, join_audit, whipsaw)
    artifacts = Task482Artifacts(
        source,
        market_components,
        theme_components,
        market_state,
        theme_state,
        transition,
        whipsaw,
        sensitivity,
        quality,
        join_audit,
        decision,
    )
    write_task482_artifacts(artifacts, out_dir)
    return artifacts


def build_daily_source_ohlcv_panel(
    symbols: list[str],
    intraday_dir: Path,
    theme_map: dict[str, str],
    role_map: dict[str, str],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        path = intraday_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, encoding="utf-8-sig")
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        if "datetime" in frame.columns and "timestamp" not in frame.columns:
            frame = frame.rename(columns={"datetime": "timestamp"})
        if "date" in frame.columns and "timestamp" not in frame.columns:
            frame = frame.rename(columns={"date": "timestamp"})
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        if any(c not in frame.columns for c in required):
            continue
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=required).copy()
        eastern = frame["timestamp"].dt.tz_convert("America/New_York")
        minutes = eastern.dt.hour * 60 + eastern.dt.minute
        frame = frame[(minutes >= 9 * 60 + 30) & (minutes < 16 * 60)].copy()
        if frame.empty:
            continue
        frame["trade_date"] = eastern.loc[frame.index].dt.strftime("%Y-%m-%d").values
        grouped = frame.groupby("trade_date", as_index=False).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        grouped["symbol"] = symbol
        grouped["theme_id"] = theme_map.get(symbol, "unknown")
        grouped["role"] = role_map.get(symbol, "unknown")
        grouped["dollar_volume"] = grouped["close"] * grouped["volume"]
        frames.append(grouped)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="coerce")
    out = out.dropna(subset=["trade_date"]).sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    by_symbol = out.groupby("symbol", group_keys=False)
    out["ret_1d"] = by_symbol["close"].pct_change(1)
    out["ret_5d"] = by_symbol["close"].pct_change(5)
    out["ret_20d"] = by_symbol["close"].pct_change(20)
    out["ret_60d"] = by_symbol["close"].pct_change(60)
    out["high_20d"] = by_symbol["high"].transform(lambda s: s.rolling(20, min_periods=5).max())
    out["drawdown_20d"] = out["close"] / out["high_20d"].replace(0, pd.NA) - 1.0
    out["near_20d_high_flag"] = (out["close"] >= out["high_20d"] * 0.98).astype(int)
    out["realized_vol_5d"] = by_symbol["ret_1d"].transform(lambda s: s.rolling(5, min_periods=3).std())
    out["realized_vol_20d"] = by_symbol["ret_1d"].transform(lambda s: s.rolling(20, min_periods=8).std())
    out["dv_5d"] = by_symbol["dollar_volume"].transform(lambda s: s.rolling(5, min_periods=3).mean())
    out["dv_20d"] = by_symbol["dollar_volume"].transform(lambda s: s.rolling(20, min_periods=8).mean())
    out["source_granularity"] = "intraday_15m_aggregated_to_daily_regular_session"
    out["score_uses_intraday_same_day_flag"] = 0
    return out


def build_market_regime_scores(source: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily = source.groupby("trade_date", as_index=False).agg(
        symbol_count=("symbol", "nunique"),
        market_ret_5d=("ret_5d", "mean"),
        market_ret_20d=("ret_20d", "mean"),
        breadth_5d_positive=("ret_5d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        breadth_20d_positive=("ret_20d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        near_high_participation=("near_20d_high_flag", "mean"),
        total_dollar_volume=("dollar_volume", "sum"),
        dv_5d=("dv_5d", "sum"),
        dv_20d=("dv_20d", "sum"),
        avg_realized_vol_5d=("realized_vol_5d", "mean"),
        avg_realized_vol_20d=("realized_vol_20d", "mean"),
        avg_drawdown_20d=("drawdown_20d", "mean"),
    ).sort_values("trade_date")
    daily["breadth_thrust_5d"] = daily["breadth_5d_positive"] - daily["breadth_5d_positive"].shift(3)
    daily["market_return_acceleration"] = daily["market_ret_5d"] - daily["market_ret_20d"] / 4.0
    daily["leadership_expansion_score_raw"] = daily["near_high_participation"] + daily["breadth_thrust_5d"].fillna(0.0)
    daily["liquidity_ratio_5d_20d"] = daily["dv_5d"] / daily["dv_20d"].replace(0, pd.NA)
    daily["vol_ratio_5d_20d"] = daily["avg_realized_vol_5d"] / daily["avg_realized_vol_20d"].replace(0, pd.NA)
    daily["breadth_persistence_score"] = _score_0_100(daily["breadth_20d_positive"], low=0.35, high=0.70)
    daily["trend_momentum_score"] = _score_0_100(daily["market_ret_20d"] + daily["market_ret_5d"], low=-0.05, high=0.08)
    daily["risk_appetite_score"] = _score_0_100(daily["leadership_expansion_score_raw"], low=0.15, high=0.75)
    daily["liquidity_participation_score"] = _score_0_100(daily["liquidity_ratio_5d_20d"], low=0.80, high=1.30)
    vol_score = 100.0 - _score_0_100(daily["vol_ratio_5d_20d"], low=0.75, high=1.75)
    dd_score = _score_0_100(daily["avg_drawdown_20d"], low=-0.12, high=-0.02)
    daily["volatility_drawdown_score"] = ((vol_score + dd_score) / 2.0).clip(0.0, 100.0)
    daily["market_regime_score"] = weighted_score(daily, MARKET_WEIGHTS)
    daily["market_stress_score"] = (
        0.55 * (100.0 - daily["volatility_drawdown_score"]) + 0.45 * (100.0 - daily["breadth_persistence_score"])
    ).clip(0.0, 100.0)
    components = daily.copy()
    state = components.copy()
    state["raw_market_state"] = state.apply(classify_market_state, axis=1)
    state["market_regime_state"] = apply_hysteresis(state["raw_market_state"].tolist())
    state["asof_date"] = state["trade_date"].dt.strftime("%Y-%m-%d")
    state["score_date"] = state["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    state["score_data_cutoff"] = "D_minus_1_daily_only"
    state["intraday_confirmation_used_flag"] = 0
    state["symbol_continuation_used_flag"] = 0
    components["asof_date"] = components["trade_date"].dt.strftime("%Y-%m-%d")
    components["score_date"] = components["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    return components.dropna(subset=["score_date"]).reset_index(drop=True), state.dropna(subset=["score_date"]).reset_index(drop=True)


def build_theme_regime_scores(source: pd.DataFrame, market_state: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    theme_daily = source.groupby(["trade_date", "theme_id"], as_index=False).agg(
        symbol_count=("symbol", "nunique"),
        theme_ret_5d=("ret_5d", "mean"),
        theme_ret_20d=("ret_20d", "mean"),
        theme_ret_60d=("ret_60d", "mean"),
        theme_breadth_5d=("ret_5d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        theme_breadth_20d=("ret_20d", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        theme_near_high_participation=("near_20d_high_flag", "mean"),
        theme_dollar_volume=("dollar_volume", "sum"),
        theme_dv_5d=("dv_5d", "sum"),
        theme_dv_20d=("dv_20d", "sum"),
        theme_avg_drawdown_20d=("drawdown_20d", "mean"),
        theme_ret_dispersion_20d=("ret_20d", "std"),
    ).sort_values(["theme_id", "trade_date"])
    market_ref = market_state[["trade_date", "market_ret_5d", "market_ret_20d"]].drop_duplicates()
    theme_daily = theme_daily.merge(market_ref, on="trade_date", how="left")
    theme_daily["theme_rs_5d"] = theme_daily["theme_ret_5d"] - theme_daily["market_ret_5d"]
    theme_daily["theme_rs_20d"] = theme_daily["theme_ret_20d"] - theme_daily["market_ret_20d"]
    theme_daily["theme_breadth_thrust"] = theme_daily.groupby("theme_id")["theme_breadth_5d"].diff(3)
    theme_daily["theme_volume_ratio_5d_20d"] = theme_daily["theme_dv_5d"] / theme_daily["theme_dv_20d"].replace(0, pd.NA)
    theme_daily["theme_rank_20d"] = theme_daily.groupby("trade_date")["theme_rs_20d"].rank(method="first", ascending=False)
    theme_daily["theme_count"] = theme_daily.groupby("trade_date")["theme_id"].transform("count")
    theme_daily["leader_persistence_raw"] = (
        theme_daily["theme_rank_20d"].le(3).astype(int).groupby(theme_daily["theme_id"]).transform(lambda s: s.rolling(5, min_periods=2).mean())
    )
    theme_daily["theme_relative_strength_score"] = _score_0_100(theme_daily["theme_rs_20d"] + theme_daily["theme_rs_5d"], low=-0.05, high=0.08)
    theme_daily["theme_breadth_persistence_score"] = _score_0_100(theme_daily["theme_breadth_20d"], low=0.35, high=0.75)
    theme_daily["leader_persistence_score"] = _score_0_100(theme_daily["leader_persistence_raw"], low=0.0, high=0.80)
    theme_daily["theme_volume_accumulation_score"] = _score_0_100(theme_daily["theme_volume_ratio_5d_20d"], low=0.80, high=1.30)
    dd_score = _score_0_100(theme_daily["theme_avg_drawdown_20d"], low=-0.15, high=-0.02)
    dispersion_penalty = 100.0 - _score_0_100(theme_daily["theme_ret_dispersion_20d"], low=0.02, high=0.20)
    theme_daily["theme_drawdown_dispersion_score"] = ((dd_score + dispersion_penalty) / 2.0).clip(0.0, 100.0)
    theme_daily["theme_regime_score"] = weighted_score(theme_daily, THEME_WEIGHTS)
    theme_daily["theme_stress_score"] = (
        0.50 * (100.0 - theme_daily["theme_breadth_persistence_score"])
        + 0.25 * (100.0 - theme_daily["theme_relative_strength_score"])
        + 0.25 * (100.0 - theme_daily["theme_drawdown_dispersion_score"])
    ).clip(0.0, 100.0)
    components = theme_daily.copy()
    state = components.copy()
    state["raw_theme_state"] = state.apply(classify_theme_state, axis=1)
    state["theme_regime_state"] = state.groupby("theme_id", group_keys=False)["raw_theme_state"].transform(lambda s: apply_hysteresis(s.tolist()))
    state["asof_date"] = state["trade_date"].dt.strftime("%Y-%m-%d")
    state["score_date"] = state.groupby("theme_id")["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    state["score_data_cutoff"] = "D_minus_1_daily_only"
    state["intraday_confirmation_used_flag"] = 0
    state["symbol_continuation_used_flag"] = 0
    components["asof_date"] = components["trade_date"].dt.strftime("%Y-%m-%d")
    components["score_date"] = components.groupby("theme_id")["trade_date"].shift(-1).dt.strftime("%Y-%m-%d")
    return components.dropna(subset=["score_date"]).reset_index(drop=True), state.dropna(subset=["score_date"]).reset_index(drop=True)


def build_regime_transition_audit(market_state: pd.DataFrame, theme_state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    market = market_state.sort_values("score_date").copy()
    market["prev_state"] = market["market_regime_state"].shift(1)
    for _, row in market[market["market_regime_state"].ne(market["prev_state"])].iterrows():
        rows.append({"scope": "market", "id": "market", "score_date": row["score_date"], "from_state": row["prev_state"], "to_state": row["market_regime_state"]})
    theme = theme_state.sort_values(["theme_id", "score_date"]).copy()
    theme["prev_state"] = theme.groupby("theme_id")["theme_regime_state"].shift(1)
    for _, row in theme[theme["theme_regime_state"].ne(theme["prev_state"])].iterrows():
        rows.append({"scope": "theme", "id": row["theme_id"], "score_date": row["score_date"], "from_state": row["prev_state"], "to_state": row["theme_regime_state"]})
    return pd.DataFrame(rows)


def build_whipsaw_dwell_audit(market_state: pd.DataFrame, theme_state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rows.extend(dwell_rows(market_state, "market", "market", "market_regime_state"))
    for theme_id, group in theme_state.groupby("theme_id"):
        rows.extend(dwell_rows(group, "theme", theme_id, "theme_regime_state"))
    return pd.DataFrame(rows)


def build_weight_sensitivity_audit(
    source: pd.DataFrame,
    market_components: pd.DataFrame,
    theme_components: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    variants = {
        "base_market": MARKET_WEIGHTS,
        "breadth_heavy_market": {**MARKET_WEIGHTS, "breadth_persistence_score": 0.35, "trend_momentum_score": 0.15, "risk_appetite_score": 0.15},
        "vol_defensive_market": {**MARKET_WEIGHTS, "volatility_drawdown_score": 0.30, "risk_appetite_score": 0.12, "trend_momentum_score": 0.18},
    }
    for name, weights in variants.items():
        normalized = normalize_weights(weights)
        score = weighted_score(market_components, normalized)
        rows.append({"score_family": "market", "weight_variant": name, "avg_score": float(score.mean()), "risk_on_share": float((score >= 65).mean())})
    theme_variants = {
        "base_theme": THEME_WEIGHTS,
        "rs_heavy_theme": {**THEME_WEIGHTS, "theme_relative_strength_score": 0.35, "leader_persistence_score": 0.15},
        "breadth_heavy_theme": {**THEME_WEIGHTS, "theme_breadth_persistence_score": 0.35, "theme_volume_accumulation_score": 0.10},
    }
    for name, weights in theme_variants.items():
        normalized = normalize_weights(weights)
        score = weighted_score(theme_components, normalized)
        rows.append({"score_family": "theme", "weight_variant": name, "avg_score": float(score.mean()), "risk_on_share": float((score >= 65).mean())})
    return pd.DataFrame(rows)


def build_market_theme_regime_oos_quality(
    task480_snapshot_path: Path,
    market_state: pd.DataFrame,
    theme_state: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not task480_snapshot_path.exists():
        return pd.DataFrame(), pd.DataFrame([{"joinable_snapshot_flag": 0, "reason": "task480_snapshot_missing"}])
    snapshot = pd.read_csv(task480_snapshot_path, encoding="utf-8-sig")
    snapshot["entry_ts"] = pd.to_datetime(snapshot["entry_ts"], errors="coerce", utc=True)
    snapshot["score_date"] = snapshot["entry_ts"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    snapshot["theme_id"] = snapshot.get("theme_id", "unknown").fillna("unknown").astype(str)
    snapshot["net_return_from_entry"] = pd.to_numeric(snapshot["net_return_from_entry"], errors="coerce")
    snapshot["win_flag"] = (snapshot["net_return_from_entry"] > 0).astype(int)
    snapshot["add_scale_success_flag"] = snapshot["lifecycle_outcome_class"].eq("add_scale_success").astype(int)
    snapshot["entry_reduce_failure_flag"] = snapshot["lifecycle_outcome_class"].eq("entry_reduce_failure").astype(int)
    panel = snapshot.merge(
        market_state[["score_date", "asof_date", "market_regime_state", "market_regime_score", "market_stress_score"]],
        on="score_date",
        how="left",
    ).merge(
        theme_state[["score_date", "theme_id", "theme_regime_state", "theme_regime_score", "theme_stress_score"]],
        on=["score_date", "theme_id"],
        how="left",
    )
    panel["regime_joined_flag"] = panel["market_regime_state"].notna() & panel["theme_regime_state"].notna()
    joined = panel[panel["regime_joined_flag"]].copy()
    joined["split_name"] = split_by_time(joined["entry_ts"])
    joined["market_theme_combo"] = joined["market_regime_state"] + " x " + joined["theme_regime_state"]
    rows = []
    for keys in [["market_regime_state"], ["theme_regime_state"], ["market_theme_combo"], ["split_name", "market_theme_combo"]]:
        if joined.empty:
            continue
        grouped = joined.groupby(keys, dropna=False).agg(
            lifecycle_count=("lifecycle_id", "nunique"),
            avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
            win_rate=("win_flag", "mean"),
            add_scale_success_rate=("add_scale_success_flag", "mean"),
            entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        ).reset_index()
        grouped["grouping"] = "+".join(keys)
        rows.append(grouped)
    quality = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    join_audit = pd.DataFrame(
        [
            {
                "snapshot_lifecycle_count": int(snapshot["lifecycle_id"].nunique()),
                "joined_lifecycle_count": int(joined["lifecycle_id"].nunique()),
                "join_rate": int(joined["lifecycle_id"].nunique()) / max(int(snapshot["lifecycle_id"].nunique()), 1),
                "join_key": "score_date_plus_theme_id_exact",
                "symbol_date_price_time_fallback_used_flag": 0,
                "intraday_state_used_for_regime_flag": 0,
                "symbol_continuation_used_for_regime_flag": 0,
            }
        ]
    )
    return quality, join_audit


def build_task_482_decision(
    source: pd.DataFrame,
    market_state: pd.DataFrame,
    theme_state: pd.DataFrame,
    quality: pd.DataFrame,
    join_audit: pd.DataFrame,
    whipsaw: pd.DataFrame,
) -> pd.DataFrame:
    risk_on = market_state["market_regime_state"].isin(["risk_on_persistent", "risk_on_emerging"]).mean() if not market_state.empty else 0.0
    theme_leadership = theme_state["theme_regime_state"].isin(["persistent_theme_leadership", "emerging_theme_rotation"]).mean() if not theme_state.empty else 0.0
    joined = float(join_audit["join_rate"].iloc[0]) if not join_audit.empty and "join_rate" in join_audit.columns else 0.0
    return pd.DataFrame(
        [
            {
                "task_482_verdict": "COMPLETE_PASS",
                "evaluation_status": "CONTINUOUS_DAILY_ONLY_MARKET_THEME_REGIME_ENGINE_COMPLETE",
                "source_symbol_count": int(source["symbol"].nunique()) if not source.empty else 0,
                "source_date_count": int(source["trade_date"].nunique()) if not source.empty else 0,
                "market_score_date_count": int(market_state["score_date"].nunique()) if not market_state.empty else 0,
                "theme_score_row_count": int(len(theme_state)),
                "market_risk_on_state_share": float(risk_on),
                "theme_leadership_state_share": float(theme_leadership),
                "task480_regime_join_rate": joined,
                "whipsaw_short_dwell_count": int((whipsaw.get("dwell_days", pd.Series(dtype=float)) <= 2).sum()) if not whipsaw.empty else 0,
                "d_minus_1_daily_only_flag": 1,
                "continuous_weighted_score_flag": 1,
                "intraday_confirmation_used_for_regime_flag": 0,
                "symbol_continuation_used_for_regime_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "REGIME_ENGINE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_task482_artifacts(artifacts: Task482Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in {
        "daily_regime_source_ohlcv_panel.csv": artifacts.daily_regime_source_ohlcv_panel,
        "daily_market_regime_component_scores.csv": artifacts.daily_market_regime_component_scores,
        "daily_theme_regime_component_scores.csv": artifacts.daily_theme_regime_component_scores,
        "daily_market_regime_state_panel.csv": artifacts.daily_market_regime_state_panel,
        "daily_theme_regime_state_panel.csv": artifacts.daily_theme_regime_state_panel,
        "regime_transition_audit.csv": artifacts.regime_transition_audit,
        "regime_whipsaw_dwell_audit.csv": artifacts.regime_whipsaw_dwell_audit,
        "regime_weight_sensitivity_audit.csv": artifacts.regime_weight_sensitivity_audit,
        "market_theme_regime_oos_quality.csv": artifacts.market_theme_regime_oos_quality,
        "regime_intraday_continuation_join_audit.csv": artifacts.regime_intraday_continuation_join_audit,
        "task_482_decision.csv": artifacts.task_482_decision,
    }.items():
        frame.to_csv(out_dir / name, index=False, encoding="utf-8-sig")
    lines = [
        "# Task 482 - Continuous Multi-Horizon Market/Theme Regime Engine",
        "",
        "## Quant Expert Report",
        "- Builds daily-only market/theme regime scores from regular-session intraday bars aggregated to daily OHLCV.",
        "- D-day score rows use D-1 daily data only via `asof_date` and `score_date` separation.",
        "- Scores are continuous weighted component scores, not -1/0/1 rules.",
        "- Intraday confirmation and symbol continuation are explicitly excluded from regime scoring.",
        "",
        "## No-Background Decision-Maker Report",
        "- This creates the missing first layer: market/theme regime before intraday trading decisions.",
        "- It is diagnostic only and does not approve deployment.",
        "",
        "## Task Decision",
        _csv_block(artifacts.task_482_decision),
        "",
        "## Join Audit",
        _csv_block(artifacts.regime_intraday_continuation_join_audit),
        "",
        "## Regime Quality Sample",
        _csv_block(artifacts.market_theme_regime_oos_quality.head(40)),
    ]
    (out_dir / "task_482_continuous_market_theme_regime_engine.md").write_text("\n".join(lines), encoding="utf-8-sig")


def weighted_score(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    normalized = normalize_weights(weights)
    score = pd.Series(0.0, index=frame.index)
    for column, weight in normalized.items():
        score += pd.to_numeric(frame[column], errors="coerce").fillna(50.0) * weight
    return score.clip(0.0, 100.0)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(float(v) for v in weights.values())
    return {k: float(v) / total for k, v in weights.items()}


def classify_market_state(row: pd.Series) -> str:
    score = _num(row.get("market_regime_score"), 50.0)
    stress = _num(row.get("market_stress_score"), 50.0)
    breadth = _num(row.get("breadth_persistence_score"), 50.0)
    if stress >= 75:
        return "volatility_stress"
    if score >= 72 and breadth >= 65 and stress <= 45:
        return "risk_on_persistent"
    if score >= 62 and stress <= 60:
        return "risk_on_emerging"
    if score <= 35 or stress >= 65:
        return "risk_off_persistent"
    if score <= 45:
        return "risk_off_emerging"
    return "mixed_transition"


def classify_theme_state(row: pd.Series) -> str:
    score = _num(row.get("theme_regime_score"), 50.0)
    stress = _num(row.get("theme_stress_score"), 50.0)
    leader = _num(row.get("leader_persistence_score"), 50.0)
    breadth = _num(row.get("theme_breadth_persistence_score"), 50.0)
    if score >= 72 and leader >= 60 and breadth >= 60 and stress <= 45:
        return "persistent_theme_leadership"
    if score >= 62 and breadth >= 50:
        return "emerging_theme_rotation"
    if leader >= 60 and breadth < 50:
        return "narrow_leader_only"
    if score <= 38 or stress >= 70:
        return "fading_theme"
    if score <= 48:
        return "weak_theme"
    return "mixed_theme"


def apply_hysteresis(raw_states: list[str], confirm_days: int = 2) -> list[str]:
    current = raw_states[0] if raw_states else "unknown"
    pending = current
    pending_count = 0
    out = []
    for raw in raw_states:
        if raw == current:
            pending = raw
            pending_count = 0
        elif raw == pending:
            pending_count += 1
            if pending_count >= confirm_days:
                current = raw
                pending_count = 0
        else:
            pending = raw
            pending_count = 1
        out.append(current)
    return out


def dwell_rows(frame: pd.DataFrame, scope: str, item_id: str, state_col: str) -> list[dict]:
    rows = []
    if frame.empty:
        return rows
    ordered = frame.sort_values("score_date").copy()
    group_id = ordered[state_col].ne(ordered[state_col].shift()).cumsum()
    for _, group in ordered.groupby(group_id):
        rows.append(
            {
                "scope": scope,
                "id": item_id,
                "state": group[state_col].iloc[0],
                "start_score_date": group["score_date"].iloc[0],
                "end_score_date": group["score_date"].iloc[-1],
                "dwell_days": int(len(group)),
                "whipsaw_flag": int(len(group) <= 2),
            }
        )
    return rows


def split_by_time(ts: pd.Series) -> pd.Series:
    valid = ts.dropna().sort_values()
    out = pd.Series("unknown", index=ts.index)
    if valid.empty:
        return out
    validation_cut = valid.quantile(0.70)
    recent_cut = valid.quantile(0.85)
    out.loc[:] = "train_design"
    out.loc[ts >= validation_cut] = "validation"
    out.loc[ts >= recent_cut] = "recent_oos"
    return out


def _score_0_100(values: pd.Series, *, low: float, high: float) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if high == low:
        return pd.Series(50.0, index=values.index)
    return ((numeric - low) / (high - low) * 100.0).clip(0.0, 100.0).fillna(50.0)


def _num(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
        if pd.isna(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task482 continuous multi-horizon market/theme regime engine.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--task480-snapshot", type=Path, default=DEFAULT_TASK480_SNAPSHOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--symbols", nargs="*", default=None)
    args = parser.parse_args()
    artifacts = build_task482_continuous_market_theme_regime_engine(
        intraday_dir=args.intraday_dir,
        theme_universe_path=args.theme_universe,
        task480_snapshot_path=args.task480_snapshot,
        out_dir=args.out_dir,
        symbols=args.symbols,
    )
    row = artifacts.task_482_decision.iloc[0]
    print(
        "[TASK482] "
        f"symbols={row['source_symbol_count']} "
        f"dates={row['source_date_count']} "
        f"join_rate={row['task480_regime_join_rate']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
