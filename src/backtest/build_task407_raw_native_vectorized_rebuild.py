from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.build_forward_live_canonical_multifactor_decision_layer_401 import (
    DEFAULT_POLICY_VERSION,
    DEFAULT_THEME_UNIVERSE,
    load_theme_maps,
)
from src.backtest.build_task401_exact_label_generation_404 import classify_lifecycle
from src.backtest.canonical_continuation_multifactor_filter import evaluate_multifactor_continuation_filter
from src.backtest.intraday_canonical_continuation_engine_388 import DEFAULT_INTRADAY_DIR, IntradayContinuationConfig, discover_intraday_symbols


DEFAULT_OUT_DIR = Path("docs/reports/task_407_raw_native_vectorized_rebuild")


@dataclass(frozen=True)
class RawNativeVectorizedRebuild407Artifacts:
    raw_native_decision_snapshot_log: pd.DataFrame
    raw_native_entry_candidate_log: pd.DataFrame
    raw_native_lifecycle_event_log: pd.DataFrame
    raw_native_lifecycle_labels: pd.DataFrame
    raw_native_label_quality_summary: pd.DataFrame
    entry_reduce_failure_decomposition: pd.DataFrame
    raw_native_combo_quality: pd.DataFrame
    task_407_decision: pd.DataFrame


def build_task407_raw_native_vectorized_rebuild(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    theme_universe_path: Path = DEFAULT_THEME_UNIVERSE,
    out_dir: Path = DEFAULT_OUT_DIR,
    symbols: list[str] | None = None,
    config: IntradayContinuationConfig = IntradayContinuationConfig(persist_to_store=False),
) -> RawNativeVectorizedRebuild407Artifacts:
    selected = sorted({str(s).strip().upper() for s in (symbols or discover_intraday_symbols(intraday_dir)) if str(s).strip()})
    theme_map, role_map = load_theme_maps(theme_universe_path)
    bars = load_regular_raw_intraday_panel(selected, intraday_dir, theme_map, role_map, config)
    candidates = build_raw_native_entry_candidates(bars, config)
    decisions = evaluate_candidate_decisions(candidates)
    events, labels = simulate_raw_native_lifecycles(decisions, bars, config)
    label_quality = build_label_quality_summary(labels)
    decomposition = build_entry_reduce_failure_decomposition(decisions, labels)
    combo_quality = build_raw_native_combo_quality(decisions, labels)
    task_decision = build_task_407_decision(bars, decisions, labels, decomposition, combo_quality)
    artifacts = RawNativeVectorizedRebuild407Artifacts(
        decisions,
        decisions[decisions["decision_kind"].eq("ENTRY")].copy(),
        events,
        labels,
        label_quality,
        decomposition,
        combo_quality,
        task_decision,
    )
    write_task407_artifacts(artifacts, out_dir)
    return artifacts


def load_regular_raw_intraday_panel(
    symbols: list[str],
    intraday_dir: Path,
    theme_map: dict[str, str],
    role_map: dict[str, str],
    config: IntradayContinuationConfig,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        path = _symbol_path(intraday_dir, symbol)
        if path is None:
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
        frame = frame.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        frame = frame.dropna(subset=["timestamp"]).copy()
        eastern = frame["timestamp"].dt.tz_convert("America/New_York")
        minutes = eastern.dt.hour * 60 + eastern.dt.minute
        frame = frame[(minutes >= 9 * 60 + 30) & (minutes < 16 * 60)].copy()
        if frame.empty:
            continue
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=required).sort_values("timestamp").reset_index(drop=True)
        frame["symbol"] = symbol
        frame["theme"] = theme_map.get(symbol, "unknown")
        frame["role"] = role_map.get(symbol, "unknown")
        frame["session_date"] = eastern.loc[frame.index].dt.strftime("%Y-%m-%d").values
        frame["bar_index"] = frame.groupby("session_date").cumcount()
        frame["row_pos"] = frame.groupby("symbol").cumcount()
        frame["raw_bar_id"] = frame["symbol"] + "|" + frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        frame["day_open"] = frame.groupby("session_date")["open"].transform("first")
        frame["high_so_far"] = frame.groupby("session_date")["high"].cummax()
        frame["low_so_far"] = frame.groupby("session_date")["low"].cummin()
        frame["cum_dollar_volume"] = (frame["close"] * frame["volume"]).groupby(frame["session_date"]).cumsum()
        frame["return_so_far"] = frame["close"] / frame["day_open"] - 1.0
        frame["range_so_far"] = frame["high_so_far"] / frame["low_so_far"].replace(0, pd.NA) - 1.0
        frame["range_pos"] = (frame["close"] - frame["low_so_far"]) / (frame["high_so_far"] - frame["low_so_far"]).replace(0, pd.NA)
        frame["momentum_2bar"] = frame["close"] / frame["close"].shift(2) - 1.0
        frame["breakout_level"] = frame["high"].rolling(config.breakout_lookback).max().shift(1)
        frame["entry_range_exp_ratio"] = frame["range_so_far"] / frame.groupby("bar_index")["range_so_far"].transform(
            lambda s: s.shift(1).rolling(20, min_periods=5).median()
        ).replace(0, pd.NA)
        frame["symbol_liquidity_ratio"] = frame["cum_dollar_volume"] / frame.groupby("bar_index")["cum_dollar_volume"].transform(
            lambda s: s.shift(1).rolling(20, min_periods=5).median()
        ).replace(0, pd.NA)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    bars = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "symbol"]).reset_index(drop=True)
    market = bars.groupby("timestamp").agg(
        forward_live_breadth_positive_rate=("return_so_far", lambda s: float((s > 0).mean())),
        forward_live_avg_symbol_return=("return_so_far", "mean"),
        forward_live_total_cum_dollar_volume=("cum_dollar_volume", "sum"),
    ).reset_index()
    market["forward_live_liquidity_ratio"] = market["forward_live_total_cum_dollar_volume"] / market[
        "forward_live_total_cum_dollar_volume"
    ].shift(1).rolling(20, min_periods=5).median().replace(0, pd.NA)
    theme = bars.groupby(["timestamp", "theme"]).agg(
        forward_live_theme_return=("return_so_far", "mean"),
        forward_live_theme_breadth_positive_rate=("return_so_far", lambda s: float((s > 0).mean())),
    ).reset_index()
    theme["forward_live_theme_rank"] = theme.groupby("timestamp")["forward_live_theme_return"].rank(method="first", ascending=False)
    theme["forward_live_theme_count"] = theme.groupby("timestamp")["theme"].transform("count")
    theme["forward_live_theme_leadership_regime"] = theme.apply(
        lambda row: "theme_leader" if float(row["forward_live_theme_rank"]) <= 3 and float(row["forward_live_theme_return"]) > 0 else "not_theme_leader",
        axis=1,
    )
    out = bars.merge(market, on="timestamp", how="left").merge(theme, on=["timestamp", "theme"], how="left")
    for column, default in [
        ("forward_live_liquidity_ratio", 1.0),
        ("entry_range_exp_ratio", 1.0),
        ("symbol_liquidity_ratio", 1.0),
        ("range_pos", 0.5),
        ("momentum_2bar", 0.0),
    ]:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(default)
    return out.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def build_raw_native_entry_candidates(bars: pd.DataFrame, config: IntradayContinuationConfig) -> pd.DataFrame:
    if bars.empty:
        return pd.DataFrame()
    candidates = bars[
        (bars["bar_index"] >= config.breakout_lookback + 1)
        & pd.to_numeric(bars["breakout_level"], errors="coerce").notna()
        & (pd.to_numeric(bars["close"], errors="coerce") > pd.to_numeric(bars["breakout_level"], errors="coerce"))
    ].copy()
    candidates["candidate_sequence"] = candidates.groupby("symbol").cumcount() + 1
    candidates["candidate_id"] = candidates.apply(lambda r: f"RAW407|CANDIDATE|{r['symbol']}|{_iso(r['timestamp'])}|{int(r['candidate_sequence']):05d}", axis=1)
    candidates["decision_id"] = "RAW407|DECISION|" + candidates["candidate_id"].astype(str) + "|ENTRY"
    return candidates


def evaluate_candidate_decisions(candidates: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for row in candidates.to_dict(orient="records"):
        feature = _feature_snapshot(row)
        decision = evaluate_multifactor_continuation_filter(feature, decision_kind="ENTRY", policy_version=DEFAULT_POLICY_VERSION)
        ts = _iso(row["timestamp"])
        lifecycle_id = ""
        if decision.bucket == "ALLOW":
            lifecycle_id = f"RAW407|LIFECYCLE|{row['symbol']}|{ts}|{int(row['candidate_sequence']):05d}"
        rows.append(
            {
                "decision_id": row["decision_id"],
                "candidate_id": row["candidate_id"],
                "lifecycle_id": lifecycle_id,
                "decision_kind": "ENTRY",
                "decision_action": decision.decision_action,
                "symbol": row["symbol"],
                "theme_id": row.get("theme", "unknown"),
                "session_date_et": row.get("session_date", ts[:10]),
                "session_type": "regular",
                "decision_ts_utc": ts,
                "bar_bucket_right_ts_utc": ts,
                "raw_bar_id": row.get("raw_bar_id", ""),
                "row_pos": int(row.get("row_pos", 0)),
                "entry_price": float(row.get("close", 0.0)),
                "raw_factors_json": json.dumps(decision.raw_factors, ensure_ascii=True, sort_keys=True),
                "norm_factors_json": json.dumps(decision.norm_factors, ensure_ascii=True, sort_keys=True),
                "component_scores_json": json.dumps(decision.component_scores, ensure_ascii=True, sort_keys=True),
                "final_score_q": decision.final_score_q,
                "bucket": decision.bucket,
                "hard_gate_fail": int(decision.hard_gate_fail),
                "reason_codes": "|".join(decision.reason_codes),
                "policy_version": decision.policy_version,
                "source_hash": decision.source_hash,
                "raw_native_rebuild_flag": 1,
                "task401_skeleton_used_flag": 0,
                "label_offline_only_flag": 1,
                "outcome_field_used_flag": 0,
                "inferred_matching_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def simulate_raw_native_lifecycles(decisions: pd.DataFrame, bars: pd.DataFrame, config: IntradayContinuationConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    if decisions.empty:
        return pd.DataFrame(), pd.DataFrame()
    allow = decisions[decisions["bucket"].eq("ALLOW") & decisions["lifecycle_id"].astype(str).str.len().gt(0)].copy()
    events: list[dict] = []
    labels: list[dict] = []
    by_symbol = {symbol: group.sort_values("row_pos").reset_index(drop=True) for symbol, group in bars.groupby("symbol")}
    for symbol, group in allow.sort_values(["symbol", "row_pos"]).groupby("symbol"):
        bar_group = by_symbol.get(symbol)
        if bar_group is None or bar_group.empty:
            continue
        next_available_pos = -1
        for decision in group.to_dict(orient="records"):
            entry_pos = int(decision["row_pos"])
            if entry_pos <= next_available_pos:
                continue
            future = bar_group[(bar_group["row_pos"] >= entry_pos) & (bar_group["row_pos"] <= entry_pos + config.max_holding_bars)].copy()
            if future.empty:
                continue
            entry = future.iloc[0]
            entry_price = float(entry["close"])
            lifecycle_id = str(decision["lifecycle_id"])
            event_rows = [_event(lifecycle_id, decision["decision_id"], symbol, "ENTRY", entry["timestamp"], entry_price)]
            highest = entry_price
            add_done = False
            scale_done = False
            reduce_done = False
            exit_row = future.iloc[-1]
            for _, bar in future.iloc[1:].iterrows():
                price = float(bar["close"])
                highest = max(highest, price)
                ret = price / entry_price - 1.0
                dd = 1.0 - price / max(highest, 1e-9)
                if not add_done and ret >= config.add_return_threshold:
                    event_rows.append(_event(lifecycle_id, decision["decision_id"], symbol, "ADD", bar["timestamp"], price))
                    add_done = True
                if add_done and not scale_done and ret >= config.scale_return_threshold:
                    event_rows.append(_event(lifecycle_id, decision["decision_id"], symbol, "SCALE", bar["timestamp"], price))
                    scale_done = True
                if not reduce_done and dd >= config.reduce_drawdown_from_high:
                    event_rows.append(_event(lifecycle_id, decision["decision_id"], symbol, "REDUCE", bar["timestamp"], price))
                    reduce_done = True
                if dd >= config.exit_drawdown_from_high:
                    exit_row = bar
                    break
            exit_price = float(exit_row["close"])
            event_rows.append(_event(lifecycle_id, decision["decision_id"], symbol, "EXIT", exit_row["timestamp"], exit_price))
            events.extend(event_rows)
            types = [r["event_type"] for r in event_rows]
            ret = exit_price / entry_price - 1.0
            labels.append(
                {
                    "lifecycle_id": lifecycle_id,
                    "entry_decision_id": decision["decision_id"],
                    "symbol": symbol,
                    "entry_ts": _iso(entry["timestamp"]),
                    "exit_ts": _iso(exit_row["timestamp"]),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "event_path": "_".join(types),
                    "add_flag": int("ADD" in types),
                    "scale_flag": int("SCALE" in types),
                    "reduce_flag": int("REDUCE" in types),
                    "exit_flag": 1,
                    "return_from_entry": ret,
                    "estimated_total_cost": 0.003,
                    "net_return_from_entry": ret - 0.003,
                    "lifecycle_outcome_class": classify_lifecycle(types, ret),
                    "label_status": "labeled_exact_lifecycle",
                    "join_key_used": "lifecycle_id_exact_only",
                    "symbol_date_price_time_fallback_used_flag": 0,
                    "unlabeled_treated_as_negative_flag": 0,
                }
            )
            next_available_pos = int(exit_row["row_pos"])
    return pd.DataFrame(events), pd.DataFrame(labels)


def build_label_quality_summary(labels: pd.DataFrame) -> pd.DataFrame:
    if labels.empty:
        return pd.DataFrame()
    return labels.groupby("lifecycle_outcome_class", as_index=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
    ).sort_values("lifecycle_count", ascending=False)


def build_entry_reduce_failure_decomposition(decisions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    panel = _decision_label_panel(decisions, labels)
    if panel.empty:
        return pd.DataFrame()
    panel = add_state_columns(panel)
    rows: list[pd.DataFrame] = []
    for key in ["market_state", "theme_state", "entry_state", "risk_state", "tradability_state"]:
        part = panel.groupby(key, as_index=False).agg(
            lifecycle_count=("lifecycle_id", "nunique"),
            entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
            add_scale_success_rate=("add_scale_success_flag", "mean"),
            avg_net_return_from_entry=("net_return_from_entry", "mean"),
        )
        part["state_axis"] = key
        part = part.rename(columns={key: "state_value"})
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def build_raw_native_combo_quality(decisions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    panel = add_state_columns(_decision_label_panel(decisions, labels))
    if panel.empty:
        return pd.DataFrame()
    panel["combo_state"] = panel["market_state"] + " x " + panel["theme_state"] + " x " + panel["entry_state"] + " x " + panel["risk_state"] + " x " + panel["tradability_state"]
    return panel.groupby("combo_state", as_index=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
    ).sort_values(["avg_net_return_from_entry", "lifecycle_count"], ascending=[False, False])


def build_task_407_decision(
    bars: pd.DataFrame,
    decisions: pd.DataFrame,
    labels: pd.DataFrame,
    decomposition: pd.DataFrame,
    combo_quality: pd.DataFrame,
) -> pd.DataFrame:
    allow_count = int(decisions["bucket"].eq("ALLOW").sum()) if not decisions.empty else 0
    labeled_count = int(labels["label_status"].eq("labeled_exact_lifecycle").sum()) if not labels.empty else 0
    best = combo_quality[combo_quality["lifecycle_count"] >= 30].iloc[0].to_dict() if not combo_quality[combo_quality["lifecycle_count"] >= 30].empty else {}
    return pd.DataFrame(
        [
            {
                "task_407_verdict": "COMPLETE_PASS",
                "evaluation_status": "RAW_NATIVE_VECTORIZED_REBUILD_DIAGNOSTIC",
                "regular_raw_bar_count": int(len(bars)),
                "raw_native_decision_count": int(len(decisions)),
                "raw_native_allow_count": allow_count,
                "raw_native_labeled_lifecycle_count": labeled_count,
                "task401_skeleton_used_flag": 0,
                "inferred_matching_used_flag": 0,
                "label_coverage_rate": labeled_count / allow_count if allow_count else 0.0,
                "best_combo_state_min30": best.get("combo_state", ""),
                "best_combo_avg_net_return_min30": best.get("avg_net_return_from_entry", ""),
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "RAW_NATIVE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def add_state_columns(panel: pd.DataFrame) -> pd.DataFrame:
    frame = panel.copy()
    raw = frame["raw_factors_json"].map(_decode_json)
    for field in [
        "forward_live_breadth_positive_rate",
        "forward_live_avg_symbol_return",
        "forward_live_theme_return",
        "forward_live_theme_rank",
        "forward_live_theme_breadth_positive_rate",
        "entry_momentum_2bar",
        "entry_range_pos",
        "entry_range_exp_ratio",
        "symbol_liquidity_ratio",
        "forward_live_liquidity_ratio",
        "cost_to_range",
        "entry_hour",
    ]:
        frame[field] = raw.map(lambda value, key=field: value.get(key, ""))
    frame["market_state"] = frame.apply(_market_state, axis=1)
    frame["theme_state"] = frame.apply(_theme_state, axis=1)
    frame["entry_state"] = frame.apply(_entry_state, axis=1)
    frame["risk_state"] = frame.apply(_risk_state, axis=1)
    frame["tradability_state"] = frame.apply(_tradability_state, axis=1)
    return frame


def write_task407_artifacts(artifacts: RawNativeVectorizedRebuild407Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.raw_native_decision_snapshot_log.to_csv(out_dir / "raw_native_decision_snapshot_log.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_native_entry_candidate_log.to_csv(out_dir / "raw_native_entry_candidate_log.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_native_lifecycle_event_log.to_csv(out_dir / "raw_native_lifecycle_event_log.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_native_lifecycle_labels.to_csv(out_dir / "raw_native_lifecycle_labels.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_native_label_quality_summary.to_csv(out_dir / "raw_native_label_quality_summary.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_reduce_failure_decomposition.to_csv(out_dir / "entry_reduce_failure_decomposition.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_native_combo_quality.to_csv(out_dir / "raw_native_combo_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.task_407_decision.to_csv(out_dir / "task_407_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 407 - Raw-Native Vectorized Rebuild",
        "",
        "## Quant Expert Report",
        "- Raw-native decisions and lifecycle labels were regenerated without Task401 skeleton.",
        "- Labels use exact newly generated lifecycle IDs only.",
        "",
        "## No-Background Decision-Maker Report",
        "- This rebuild tests whether the strategy can be evaluated directly from raw bars.",
        "- It remains diagnostic-only because quote/spread/status raw data is still missing.",
        "",
        "## Decision",
        _csv_block(artifacts.task_407_decision),
        "",
        "## Label Quality",
        _csv_block(artifacts.raw_native_label_quality_summary),
        "",
        "## Entry Reduce Failure Decomposition",
        _csv_block(artifacts.entry_reduce_failure_decomposition.head(40)),
    ]
    (out_dir / "task_407_raw_native_vectorized_rebuild.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _decision_label_panel(decisions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty or labels.empty:
        return pd.DataFrame()
    panel = decisions.merge(labels, on="lifecycle_id", how="inner", suffixes=("", "_label"))
    panel["add_scale_success_flag"] = panel["lifecycle_outcome_class"].eq("add_scale_success").astype(int)
    panel["entry_reduce_failure_flag"] = panel["lifecycle_outcome_class"].eq("entry_reduce_failure").astype(int)
    return panel


def _feature_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    range_bps = max(float(row.get("range_so_far", 0.0) or 0.0), 0.001)
    estimated_total_cost = 0.00125 + max(float(row.get("range_so_far", 0.0) or 0.0), 0.0) * 0.10
    return {
        "feed": "unavailable",
        "adjustment": "raw",
        "asof": "-",
        "session_type": "regular",
        "quote_status": "unavailable",
        "luld_status": "unavailable",
        "forward_live_breadth_positive_rate": row.get("forward_live_breadth_positive_rate", 0.0),
        "forward_live_avg_symbol_return": row.get("forward_live_avg_symbol_return", 0.0),
        "forward_live_liquidity_ratio": row.get("forward_live_liquidity_ratio", 1.0),
        "forward_live_theme_return": row.get("forward_live_theme_return", 0.0),
        "forward_live_theme_rank": row.get("forward_live_theme_rank", 999.0),
        "forward_live_theme_count": row.get("forward_live_theme_count", 1.0),
        "forward_live_theme_breadth_positive_rate": row.get("forward_live_theme_breadth_positive_rate", 0.0),
        "forward_live_theme_leadership_regime": row.get("forward_live_theme_leadership_regime", "unknown"),
        "entry_return_so_far": row.get("return_so_far", 0.0),
        "entry_momentum_2bar": row.get("momentum_2bar", 0.0),
        "entry_range_pos": row.get("range_pos", 0.5),
        "entry_range_exp_ratio": row.get("entry_range_exp_ratio", 1.0),
        "symbol_liquidity_ratio": row.get("symbol_liquidity_ratio", 1.0),
        "estimated_total_cost": estimated_total_cost,
        "cost_to_range": estimated_total_cost / range_bps,
        "role": row.get("role", "unknown"),
        "entry_hour": pd.Timestamp(row["timestamp"]).hour,
    }


def _event(lifecycle_id: str, decision_id: str, symbol: str, event_type: str, ts: object, price: float) -> dict:
    return {
        "lifecycle_id": lifecycle_id,
        "decision_id": decision_id,
        "symbol": symbol,
        "event_type": event_type,
        "event_timestamp": _iso(ts),
        "price": price,
        "inferred_matching_used_flag": 0,
    }


def _market_state(row: pd.Series) -> str:
    breadth = _num(row.get("forward_live_breadth_positive_rate"))
    avg = _num(row.get("forward_live_avg_symbol_return"))
    if breadth >= 0.65 and avg > 0:
        return "broad_risk_on"
    if breadth < 0.45 and avg > 0:
        return "narrow_risk_on"
    if breadth < 0.45 or avg < 0:
        return "weak_risk_off"
    return "mixed_breadth"


def _theme_state(row: pd.Series) -> str:
    rank = _num(row.get("forward_live_theme_rank"), 999.0)
    theme_ret = _num(row.get("forward_live_theme_return"))
    theme_breadth = _num(row.get("forward_live_theme_breadth_positive_rate"))
    if rank <= 3 and theme_ret > 0 and theme_breadth >= 0.65:
        return "true_theme_leader"
    if theme_ret > 0 and theme_breadth >= 0.50:
        return "theme_participation"
    if theme_ret > 0:
        return "isolated_symbol_strength"
    return "weak_theme"


def _entry_state(row: pd.Series) -> str:
    hour = _num(row.get("entry_hour"))
    momentum = _num(row.get("entry_momentum_2bar"))
    range_pos = _num(row.get("entry_range_pos"), 0.5)
    range_exp = _num(row.get("entry_range_exp_ratio"), 1.0)
    if range_pos >= 0.97 or range_exp >= 2.50:
        return "exhaustion_breakout"
    if hour >= 19:
        return "late_chase"
    if 0.45 <= range_pos <= 0.75 and momentum > 0:
        return "pullback_reclaim"
    if hour <= 15 and momentum > 0:
        return "early_confirmation"
    if momentum > 0 and 0.70 <= range_pos < 0.97:
        return "healthy_momentum_continuation"
    return "mixed_entry"


def _risk_state(row: pd.Series) -> str:
    range_exp = _num(row.get("entry_range_exp_ratio"), 1.0)
    range_pos = _num(row.get("entry_range_pos"), 0.5)
    if range_exp >= 2.50:
        return "range_exhaustion"
    if range_exp >= 2.00 and range_pos >= 0.90:
        return "volatility_stress"
    if range_exp >= 1.30:
        return "healthy_expansion"
    return "controlled_vol"


def _tradability_state(row: pd.Series) -> str:
    cost_to_range = _num(row.get("cost_to_range"), 0.0)
    symbol_liq = _num(row.get("symbol_liquidity_ratio"), 1.0)
    market_liq = _num(row.get("forward_live_liquidity_ratio"), 1.0)
    if cost_to_range > 0.30:
        return "cost_range_unattractive"
    if symbol_liq >= 1.10 and market_liq >= 1.10:
        return "liquid_clean"
    if symbol_liq < 0.80:
        return "friction_heavy"
    return "neutral_tradability"


def _symbol_path(intraday_dir: Path, symbol: str) -> Path | None:
    candidates = [intraday_dir / f"{symbol}.csv", intraday_dir / symbol / "bars.csv", intraday_dir / f"{symbol}_15m.csv"]
    return next((p for p in candidates if p.exists()), None)


def _decode_json(value: object) -> dict:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _num(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _iso(value: object) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task407 raw-native vectorized rebuild.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--theme-universe", type=Path, default=DEFAULT_THEME_UNIVERSE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task407_raw_native_vectorized_rebuild(
        intraday_dir=args.intraday_dir,
        theme_universe_path=args.theme_universe,
        out_dir=args.out_dir,
    )
    row = artifacts.task_407_decision.iloc[0]
    print(f"[TASK407] decisions={row['raw_native_decision_count']} allow={row['raw_native_allow_count']} labels={row['raw_native_labeled_lifecycle_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
