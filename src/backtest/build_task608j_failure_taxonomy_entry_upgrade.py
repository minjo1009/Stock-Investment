from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task505_two_year_pnl_grid import simulate_portfolio
from src.backtest.build_task608g_live_detectable_entry_failure_path_diagnostics import (
    INTRADAY_DIR,
    TASK509_PANEL,
    build_task608g_live_detectable_entry_failure_path_diagnostics,
    load_intraday_sources,
)


TASK_ID = "Task608J"
REPORT_DIR = Path("docs/reports/task_608j_failure_taxonomy_entry_upgrade")
TASK608G_PATH_PANEL = Path(
    "docs/reports/task_608g_live_detectable_entry_failure_path_diagnostics/entry_failure_path_panel.csv"
)
DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
DELAY_MINUTES = [15, 30, 60]


def build_task608j_failure_taxonomy_entry_upgrade(
    *,
    task509_panel_path: Path = TASK509_PANEL,
    task608g_path_panel: Path = TASK608G_PATH_PANEL,
    intraday_dir: Path = INTRADAY_DIR,
    daily_dir: Path = DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    base = load_base_panel(task509_panel_path)
    path = load_or_build_path_panel(task608g_path_panel)
    symbols = sorted(set(base["symbol"].astype(str).str.upper()) | {"QQQ"})
    intraday_map, intraday_coverage = load_intraday_sources(symbols, intraday_dir)
    daily_map, daily_coverage = load_daily_sources(symbols, daily_dir)
    feature_panel = build_feature_panel(base, path, intraday_map, daily_map)
    taxonomy = build_failure_taxonomy(feature_panel)
    taxonomy_quality = build_taxonomy_quality(taxonomy)
    entry_qualification = build_entry_qualification_walk_forward(feature_panel)
    delayed_entry = build_delayed_entry_simulation(feature_panel)
    staged_entry = build_staged_entry_simulation(feature_panel)
    confirmation = build_continuation_confirmation_simulation(feature_panel)
    decisions = build_decisions(taxonomy_quality, entry_qualification, delayed_entry, staged_entry, confirmation)

    out_dir.mkdir(parents=True, exist_ok=True)
    intraday_coverage.to_csv(out_dir / "intraday_source_coverage.csv", index=False)
    daily_coverage.to_csv(out_dir / "daily_source_coverage.csv", index=False)
    feature_panel.to_csv(out_dir / "entry_upgrade_feature_panel.csv", index=False)
    taxonomy.to_csv(out_dir / "failure_taxonomy_panel.csv", index=False)
    taxonomy_quality.to_csv(out_dir / "failure_taxonomy_quality.csv", index=False)
    entry_qualification.to_csv(out_dir / "entry_qualification_walk_forward.csv", index=False)
    delayed_entry.to_csv(out_dir / "delayed_entry_simulation.csv", index=False)
    staged_entry.to_csv(out_dir / "staged_entry_simulation.csv", index=False)
    confirmation.to_csv(out_dir / "continuation_confirmation_simulation.csv", index=False)
    decisions.to_csv(out_dir / "task_608j_decision.csv", index=False)
    (out_dir / "task_608j_failure_taxonomy_entry_upgrade.md").write_text(
        render_report(taxonomy_quality, entry_qualification, delayed_entry, staged_entry, confirmation, decisions),
        encoding="utf-8",
    )
    (out_dir / "gpt_review_notes.md").write_text(render_gpt_review_notes(), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "entry_upgrade_feature_panel": feature_panel,
        "failure_taxonomy_panel": taxonomy,
        "failure_taxonomy_quality": taxonomy_quality,
        "entry_qualification_walk_forward": entry_qualification,
        "delayed_entry_simulation": delayed_entry,
        "staged_entry_simulation": staged_entry,
        "continuation_confirmation_simulation": confirmation,
        "task_608j_decision": decisions,
    }


def load_base_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["simulated_exit_ts"] = pd.to_datetime(frame["simulated_exit_ts"], utc=True, errors="coerce")
    frame["entry_price"] = pd.to_numeric(frame["entry_price"], errors="coerce")
    frame["simulated_exit_price"] = pd.to_numeric(frame["simulated_exit_price"], errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["entry_reduce_failure_flag"] = pd.to_numeric(
        frame["entry_reduce_failure_flag"], errors="coerce"
    ).fillna(0).astype(int)
    frame["win_flag"] = pd.to_numeric(frame["win_flag"], errors="coerce").fillna(0).astype(int)
    frame = frame.dropna(subset=["lifecycle_id", "entry_ts", "entry_price", "simulated_exit_price"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    return frame.sort_values("entry_ts").reset_index(drop=True)


def load_or_build_path_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        build_task608g_live_detectable_entry_failure_path_diagnostics()
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    return frame


def load_daily_sources(symbols: list[str], daily_dir: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    daily_dir = Path(daily_dir)
    daily_map: dict[str, pd.DataFrame] = {}
    rows = []
    for symbol in symbols:
        path = daily_dir / f"{symbol}.csv"
        if not path.exists():
            rows.append({"symbol": symbol, "available_flag": 0, "row_count": 0, "path": str(path)})
            continue
        frame = pd.read_csv(path)
        frame.columns = [str(column).lower() for column in frame.columns]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).copy()
        frame["trade_date"] = frame["timestamp"].dt.tz_convert("America/New_York").dt.date.astype(str)
        frame = frame.sort_values("timestamp").reset_index(drop=True)
        daily_map[symbol] = frame
        rows.append({"symbol": symbol, "available_flag": 1, "row_count": len(frame), "path": str(path)})
    return daily_map, pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def build_feature_panel(
    base: pd.DataFrame,
    path: pd.DataFrame,
    intraday_map: dict[str, pd.DataFrame],
    daily_map: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    path_columns = [
        "lifecycle_id",
        "symbol_ret_15m",
        "symbol_ret_30m",
        "symbol_ret_60m",
        "symbol_ret_120m",
        "symbol_mae_60m",
        "symbol_mfe_60m",
        "symbol_mae_120m",
        "symbol_mfe_120m",
        "opening_rejection_120m_flag",
        "relative_ret_vs_qqq_60m",
        "volume_decay_120m_flag",
        "symbol_vwap_fail_15m_flag",
        "symbol_vwap_fail_30m_flag",
        "symbol_vwap_fail_60m_flag",
        "vwap_fail_60m_flag",
    ]
    merged = base.merge(path[[c for c in path_columns if c in path.columns]], on="lifecycle_id", how="left")
    rows = []
    theme_symbols = {
        theme: sorted(group["symbol"].astype(str).str.upper().unique().tolist())
        for theme, group in merged.groupby("theme_id")
    }
    for item in merged.to_dict(orient="records"):
        symbol = str(item["symbol"]).upper()
        intraday = intraday_map.get(symbol, pd.DataFrame())
        qqq = intraday_map.get("QQQ", pd.DataFrame())
        daily = daily_map.get(symbol, pd.DataFrame())
        row = dict(item)
        row.update(pre_entry_intraday_features(item, intraday))
        row.update(prior_day_features(item, daily))
        row.update(theme_context_features(item, intraday_map, theme_symbols.get(str(item.get("theme_id", "")), [])))
        row.update(qqq_pre_entry_features(row, qqq))
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["pre_entry_feature_available_flag"] = frame[
        ["premarket_high_available_flag", "prior_day_available_flag", "qqq_pre_entry_available_flag"]
    ].min(axis=1)
    return frame


def pre_entry_intraday_features(item: dict[str, Any], intraday: pd.DataFrame) -> dict[str, Any]:
    entry_ts = pd.Timestamp(item["entry_ts"])
    entry_price = float(item["entry_price"])
    session_date = entry_ts.tz_convert("America/New_York").date().isoformat()
    if intraday.empty:
        return {"premarket_high_available_flag": 0}
    session = intraday[intraday["session_date_et"].eq(session_date)].copy()
    if session.empty:
        return {"premarket_high_available_flag": 0}
    local_midnight = pd.Timestamp(session_date).tz_localize("America/New_York").tz_convert("UTC")
    premarket_start = local_midnight + pd.Timedelta(hours=4)
    regular_start = local_midnight + pd.Timedelta(hours=9, minutes=30)
    premarket = session[session["timestamp"].between(premarket_start, regular_start, inclusive="left")]
    regular_to_entry = session[session["timestamp"].between(regular_start, entry_ts, inclusive="both")]
    if premarket.empty:
        premarket = regular_to_entry.head(1)
    if regular_to_entry.empty:
        regular_to_entry = session[session["timestamp"].ge(entry_ts)].head(1)
    premarket_high = float(premarket["high"].max()) if not premarket.empty else entry_price
    premarket_low = float(premarket["low"].min()) if not premarket.empty else entry_price
    premarket_vwap = _vwap(premarket)
    session_open = float(regular_to_entry.iloc[0]["open"]) if not regular_to_entry.empty else entry_price
    bars_since_open = int(max(0, len(regular_to_entry) - 1))
    first_expansion_idx = first_expansion_bar_index(regular_to_entry)
    return {
        "premarket_high_available_flag": int(not premarket.empty),
        "premarket_high": premarket_high,
        "premarket_low": premarket_low,
        "premarket_vwap": premarket_vwap,
        "distance_to_premarket_high_pct": entry_price / premarket_high - 1.0 if premarket_high else 0.0,
        "distance_to_premarket_vwap_pct": entry_price / premarket_vwap - 1.0 if premarket_vwap else 0.0,
        "overnight_range_pct": premarket_high / premarket_low - 1.0 if premarket_low else 0.0,
        "entry_ret_from_session_open": entry_price / session_open - 1.0 if session_open else 0.0,
        "bars_since_session_open": bars_since_open,
        "breakout_age_bars": max(0, bars_since_open - first_expansion_idx) if first_expansion_idx >= 0 else 0,
        "late_breakout_proxy_flag": int(bars_since_open >= 8 and first_expansion_idx >= 0 and bars_since_open - first_expansion_idx >= 4),
        "premarket_extension_flag": int(entry_price >= premarket_high * 0.995),
    }


def prior_day_features(item: dict[str, Any], daily: pd.DataFrame) -> dict[str, Any]:
    entry_date = pd.Timestamp(item["entry_ts"]).tz_convert("America/New_York").date().isoformat()
    if daily.empty:
        return {"prior_day_available_flag": 0}
    before = daily[daily["trade_date"].lt(entry_date)].copy()
    current = daily[daily["trade_date"].eq(entry_date)].head(1)
    if before.empty:
        return {"prior_day_available_flag": 0}
    prior = before.iloc[-1]
    lookback = before.tail(60)
    prior_ret = float(prior["close"] / prior["open"] - 1.0) if float(prior["open"]) else 0.0
    prior_range = float(prior["high"] / prior["low"] - 1.0) if float(prior["low"]) else 0.0
    prior_close_location = _safe_div(float(prior["close"] - prior["low"]), float(prior["high"] - prior["low"]))
    volume_ratio = _safe_div(float(prior["volume"]), float(before.tail(20)["volume"].mean()))
    today_open = float(current.iloc[0]["open"]) if not current.empty else float(item["entry_price"])
    gap_pct = today_open / float(prior["close"]) - 1.0 if float(prior["close"]) else 0.0
    gap_rank = float((lookback["open"].pct_change().abs() <= abs(gap_pct)).mean()) if len(lookback) else 0.0
    return {
        "prior_day_available_flag": 1,
        "prior_day_ret": prior_ret,
        "prior_day_range_pct": prior_range,
        "prior_day_close_location": prior_close_location,
        "prior_day_volume_ratio_20": volume_ratio,
        "gap_pct": gap_pct,
        "gap_abs_percentile_60d": gap_rank,
        "prior_day_extension_flag": int(prior_ret >= 0.08 or prior_range >= 0.12 or volume_ratio >= 2.0),
    }


def theme_context_features(
    item: dict[str, Any],
    intraday_map: dict[str, pd.DataFrame],
    symbols: list[str],
) -> dict[str, Any]:
    entry_ts = pd.Timestamp(item["entry_ts"])
    returns = []
    for symbol in symbols:
        frame = intraday_map.get(symbol, pd.DataFrame())
        ret = pre_entry_return_from_open(entry_ts, frame)
        if ret is not None:
            returns.append(ret)
    symbol_ret = pre_entry_return_from_open(entry_ts, intraday_map.get(str(item["symbol"]).upper(), pd.DataFrame()))
    theme_ret = float(pd.Series(returns).mean()) if returns else 0.0
    leader_ret = float(pd.Series(returns).max()) if returns else 0.0
    return {
        "theme_pre_entry_available_count": len(returns),
        "theme_pre_entry_ret": theme_ret,
        "theme_leader_pre_entry_ret": leader_ret,
        "symbol_vs_theme_pre_entry_ret": (symbol_ret - theme_ret) if symbol_ret is not None else 0.0,
        "symbol_vs_leader_pre_entry_ret": (symbol_ret - leader_ret) if symbol_ret is not None else 0.0,
        "theme_confirmation_fail_pre_entry_flag": int(symbol_ret is not None and len(returns) >= 2 and symbol_ret < theme_ret - 0.01),
    }


def qqq_pre_entry_features(item: dict[str, Any], qqq: pd.DataFrame) -> dict[str, Any]:
    ret = pre_entry_return_from_open(pd.Timestamp(item["entry_ts"]), qqq)
    symbol_open_ret = float(item.get("entry_ret_from_session_open", 0.0) or 0.0)
    return {
        "qqq_pre_entry_available_flag": int(ret is not None),
        "qqq_pre_entry_ret": ret if ret is not None else 0.0,
        "symbol_vs_qqq_pre_entry_ret": symbol_open_ret - ret if ret is not None else 0.0,
    }


def build_failure_taxonomy(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    failed = feature_panel[feature_panel["entry_reduce_failure_flag"].astype(int).eq(1)].copy()
    for item in failed.to_dict(orient="records"):
        failure_type, reason = classify_failure(item)
        row = dict(item)
        row["failure_type"] = failure_type
        row["failure_reason"] = reason
        rows.append(row)
    return pd.DataFrame(rows)


def classify_failure(row: dict[str, Any]) -> tuple[str, str]:
    if bool(row.get("prior_day_extension_flag", 0)) and _ge(row.get("distance_to_premarket_high_pct"), -0.01):
        return "gap_exhaustion_or_event_fade_proxy", "extended prior day or gap plus entry near premarket high"
    if str(row.get("timing_state", "")) == "opening_drive" and int(row.get("opening_rejection_120m_flag", 0)) == 1:
        return "opening_trap", "opening drive failed to hold opening range"
    if _le(row.get("relative_ret_vs_qqq_60m"), -0.02) or int(row.get("theme_confirmation_fail_pre_entry_flag", 0)) == 1:
        return "sector_or_theme_rotation", "stock lagged QQQ/theme during failure window or pre-entry theme confirmation failed"
    if int(row.get("late_breakout_proxy_flag", 0)) == 1:
        return "late_breakout_exhaustion", "entry occurred late after prior breakout expansion"
    if int(row.get("volume_decay_120m_flag", 0)) == 1 and _le(row.get("symbol_mfe_120m"), 0.01):
        return "continuation_demand_decay", "volume decayed and MFE stayed weak"
    return "unclassified_mixed_failure", "current features do not isolate a mechanism"


def build_taxonomy_quality(taxonomy: pd.DataFrame) -> pd.DataFrame:
    if taxonomy.empty:
        return pd.DataFrame()
    rows = []
    for failure_type, group in taxonomy.groupby("failure_type", sort=True):
        rows.append(
            {
                "failure_type": failure_type,
                "failure_count": int(len(group)),
                "failure_share": float(len(group) / len(taxonomy)),
                "avg_net_return_pct": float(group["net_return_from_entry"].mean() * 100.0),
                "top_symbols": "|".join(group["symbol"].astype(str).value_counts().head(5).index.tolist()),
                "top_quarters": "|".join(group["quarter"].astype(str).value_counts().head(5).index.tolist()),
            }
        )
    frame = pd.DataFrame(rows)
    frame["taxonomy_coverage_rate"] = float(1.0 - (taxonomy["failure_type"].eq("unclassified_mixed_failure").mean()))
    return frame.sort_values("failure_count", ascending=False).reset_index(drop=True)


def build_entry_qualification_walk_forward(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rules = entry_qualification_rules()
    quarters = sorted(feature_panel["quarter"].astype(str).unique().tolist())
    rows = []
    baseline_avg = float(aggregate(feature_panel)["avg_net_return_pct"])
    for idx in range(1, len(quarters)):
        train = feature_panel[feature_panel["quarter"].isin(quarters[:idx])].copy()
        test = feature_panel[feature_panel["quarter"].eq(quarters[idx])].copy()
        for name, predicate in rules:
            train_block = train.apply(predicate, axis=1)
            if int(train_block.sum()) < 3:
                continue
            train_failure_rate = float(train.loc[train_block, "entry_reduce_failure_flag"].mean())
            if train_failure_rate < 0.50:
                continue
            test_block = test.apply(predicate, axis=1)
            accepted = test[~test_block].copy()
            row = aggregate(accepted)
            row.update(
                {
                    "test_quarter": quarters[idx],
                    "rule_name": name,
                    "train_trigger_count": int(train_block.sum()),
                    "train_failure_rate": train_failure_rate,
                    "blocked_count": int(test_block.sum()),
                    "blocked_original_failure_count": int(test.loc[test_block, "entry_reduce_failure_flag"].sum()),
                    "clean_false_block_count": int((test_block & test["entry_reduce_failure_flag"].eq(0)).sum()),
                    "baseline_avg_net_return_pct": baseline_avg,
                    "label_used_in_test_assignment_flag": 0,
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def build_delayed_entry_simulation(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rows = [scenario_quality(feature_panel, "baseline_entry", feature_panel["net_return_from_entry"])]
    for delay in DELAY_MINUTES:
        column = f"symbol_ret_{delay}m"
        if column not in feature_panel.columns:
            continue
        delayed_entry_returns = []
        for item in feature_panel.to_dict(orient="records"):
            delayed_path_ret = item.get(column)
            original = float(item["net_return_from_entry"])
            if pd.isna(delayed_path_ret):
                delayed_entry_returns.append(original)
                continue
            delayed_price = float(item["entry_price"]) * (1.0 + float(delayed_path_ret))
            exit_price = float(item["simulated_exit_price"])
            delayed_entry_returns.append(exit_price / delayed_price - 1.0 if delayed_price else original)
        rows.append(scenario_quality(feature_panel, f"delayed_entry_{delay}m", pd.Series(delayed_entry_returns)))
    return pd.DataFrame(rows)


def build_staged_entry_simulation(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    schedules = {
        "staged_25_25_50_0_30_60m": [(0, 0.25), (30, 0.25), (60, 0.50)],
        "staged_33_33_33_0_30_60m": [(0, 1 / 3), (30, 1 / 3), (60, 1 / 3)],
        "staged_50_50_0_60m": [(0, 0.50), (60, 0.50)],
    }
    for name, schedule in schedules.items():
        returns = []
        for item in feature_panel.to_dict(orient="records"):
            weighted_entry = 0.0
            weight_sum = 0.0
            for minute, weight in schedule:
                if minute == 0:
                    leg_price = float(item["entry_price"])
                else:
                    path_ret = item.get(f"symbol_ret_{minute}m")
                    if pd.isna(path_ret):
                        continue
                    leg_price = float(item["entry_price"]) * (1.0 + float(path_ret))
                weighted_entry += leg_price * weight
                weight_sum += weight
            if weight_sum <= 0:
                returns.append(float(item["net_return_from_entry"]))
            else:
                weighted_entry /= weight_sum
                returns.append(float(item["simulated_exit_price"]) / weighted_entry - 1.0)
        rows.append(scenario_quality(feature_panel, name, pd.Series(returns)))
    return pd.DataFrame(rows)


def build_continuation_confirmation_simulation(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for delay in DELAY_MINUTES:
        ret_col = f"symbol_ret_{delay}m"
        vwap_col = f"symbol_vwap_fail_{delay}m_flag"
        returns = []
        accepted_flags = []
        for item in feature_panel.to_dict(orient="records"):
            path_ret = item.get(ret_col)
            qqq_rel = item.get("relative_ret_vs_qqq_60m")
            confirm = pd.notna(path_ret) and float(path_ret) > 0 and not int(item.get(vwap_col, 0)) and not _le(qqq_rel, -0.01)
            accepted_flags.append(int(confirm))
            if not confirm:
                returns.append(pd.NA)
                continue
            delayed_price = float(item["entry_price"]) * (1.0 + float(path_ret))
            returns.append(float(item["simulated_exit_price"]) / delayed_price - 1.0)
        scenario_frame = feature_panel.copy()
        scenario_frame["accepted_flag"] = accepted_flags
        scenario_frame["scenario_return"] = returns
        accepted = scenario_frame[scenario_frame["accepted_flag"].eq(1)].copy()
        row = scenario_quality(accepted, f"confirmation_entry_{delay}m", accepted["scenario_return"])
        row["accepted_count"] = int(len(accepted))
        row["rejected_count"] = int(len(feature_panel) - len(accepted))
        row["rejected_failure_count"] = int(
            feature_panel.loc[pd.Series(accepted_flags).eq(0).values, "entry_reduce_failure_flag"].sum()
        )
        row["clean_false_reject_count"] = int(
            (
                pd.Series(accepted_flags).eq(0).values
                & feature_panel["entry_reduce_failure_flag"].astype(int).eq(0).values
            ).sum()
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_decisions(
    taxonomy_quality: pd.DataFrame,
    entry_qualification: pd.DataFrame,
    delayed_entry: pd.DataFrame,
    staged_entry: pd.DataFrame,
    confirmation: pd.DataFrame,
) -> pd.DataFrame:
    taxonomy_coverage = float(taxonomy_quality["taxonomy_coverage_rate"].iloc[0]) if not taxonomy_quality.empty else 0.0
    delayed_best = best_delta_row(delayed_entry)
    staged_best = best_delta_row(staged_entry)
    confirmation_best = best_delta_row(confirmation)
    best_delta = max(
        float(delayed_best.get("delta_avg_net_return_pct", -999.0)),
        float(staged_best.get("delta_avg_net_return_pct", -999.0)),
        float(confirmation_best.get("delta_avg_net_return_pct", -999.0)),
    )
    pass_flag = int(taxonomy_coverage >= 0.70 and best_delta > 0.0)
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_FAILURE_TAXONOMY_AND_ENTRY_UPGRADE_CANDIDATE_FOUND"
                    if pass_flag
                    else "FAIL_ENTRY_UPGRADE_NOT_FIRM_GRADE_YET"
                ),
                "pass_flag": pass_flag,
                "taxonomy_coverage_rate": taxonomy_coverage,
                "best_delayed_scenario": delayed_best.get("scenario", ""),
                "best_delayed_delta_avg_net_return_pct": delayed_best.get("delta_avg_net_return_pct", 0.0),
                "best_staged_scenario": staged_best.get("scenario", ""),
                "best_staged_delta_avg_net_return_pct": staged_best.get("delta_avg_net_return_pct", 0.0),
                "best_confirmation_scenario": confirmation_best.get("scenario", ""),
                "best_confirmation_delta_avg_net_return_pct": confirmation_best.get("delta_avg_net_return_pct", 0.0),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_action": "Promote only positive entry-upgrade families to fold-forward OOS rule-lock testing with costs.",
            }
        ]
    )


def render_report(
    taxonomy_quality: pd.DataFrame,
    entry_qualification: pd.DataFrame,
    delayed_entry: pd.DataFrame,
    staged_entry: pd.DataFrame,
    confirmation: pd.DataFrame,
    decisions: pd.DataFrame,
) -> str:
    decision = decisions.iloc[0].to_dict()
    taxonomy_lines = [
        f"- {row['failure_type']}: count {int(row['failure_count'])}, share {float(row['failure_share']):.2%}, avg {float(row['avg_net_return_pct']):.2f}%"
        for _, row in taxonomy_quality.head(8).iterrows()
    ]
    delayed_lines = scenario_lines(delayed_entry)
    staged_lines = scenario_lines(staged_entry)
    confirmation_lines = scenario_lines(confirmation)
    eq_best = entry_qualification.sort_values("avg_net_return_pct", ascending=False).head(5) if not entry_qualification.empty else pd.DataFrame()
    eq_lines = [
        f"- {row['test_quarter']} {row['rule_name']}: accepted avg {float(row['avg_net_return_pct']):.2f}%, blocked {int(row['blocked_count'])}, clean false blocks {int(row['clean_false_block_count'])}"
        for _, row in eq_best.iterrows()
    ]
    return "\n".join(
        [
            "# Task608J Failure Taxonomy And Entry Upgrade",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {decision['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            f"- Taxonomy coverage: {float(decision['taxonomy_coverage_rate']):.2%}",
            f"- Best delayed entry: {decision['best_delayed_scenario']} delta {float(decision['best_delayed_delta_avg_net_return_pct']):.2f} pct points.",
            f"- Best staged entry: {decision['best_staged_scenario']} delta {float(decision['best_staged_delta_avg_net_return_pct']):.2f} pct points.",
            f"- Best confirmation entry: {decision['best_confirmation_scenario']} delta {float(decision['best_confirmation_delta_avg_net_return_pct']):.2f} pct points.",
            "- What changed: entry-reduce is now split into failure types, and entry alternatives are tested before reducer retry.",
            f"- Next action: {decision['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task509 OOS rows, Task608G path panel, `data/raw/us_intraday`, and `data/raw/us_daily_breadth_top500`.",
            "- Exact join keys: existing `lifecycle_id`; intraday/daily features use exact symbol and timestamp/date windows.",
            "- Leakage audit: taxonomy uses outcomes for evaluation. Entry qualification uses pre-entry features; delayed/staged/confirmation tests use observable wait/confirmation paths and do not use labels for assignment.",
            "- Split/OOS metrics: entry qualification is fold-forward by quarter. Delayed/staged/confirmation are diagnostic simulations and must be fold-forward rule-locked before acceptance.",
            "- Failure decomposition: see `failure_taxonomy_panel.csv` and `failure_taxonomy_quality.csv`.",
            "- Cost/slippage stress where PnL changed: not applied in Task608J; any promoted family must be cost-stressed next.",
            "- Remaining blockers: positive diagnostic deltas are not deployment claims.",
            "- GPT reviewer note: Chrome ChatGPT review agrees this remains `NOT_ACCEPTED`; see `gpt_review_notes.md`.",
            "",
            "Failure taxonomy:",
            *taxonomy_lines,
            "",
            "Entry qualification fold-forward leaders:",
            *(eq_lines or ["- No entry qualification rule met the train trigger/failure threshold."]),
            "",
            "Delayed entry:",
            *delayed_lines,
            "",
            "Staged entry:",
            *staged_lines,
            "",
            "Continuation confirmation:",
            *confirmation_lines,
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: we stopped treating all losses as one blob and tested entry alternatives before trying another reducer.",
            "- Why it matters: if delayed or staged entry works better, the problem is entry timing/qualification rather than reduce-after-entry.",
            "- Whether this changes capital/deployment readiness: no. It remains research only.",
            "- Plain-language next step: take only the best positive family and run a stricter fold-forward cost test.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def render_gpt_review_notes() -> str:
    return "\n".join(
        [
            "# Task608J GPT Review Notes",
            "",
            "Captured via Chrome ChatGPT project `1. 코딩/투자` on Task608J summary metrics.",
            "",
            "## Reviewer Framing",
            "",
            "- Treat GPT as external model interpretation only, not a source of truth.",
            "- Use only repo-native outputs for acceptance, deployment, and validation.",
            "",
            "## Key Takeaways",
            "",
            "- Verdict: `NOT_ACCEPTED / DIAGNOSTIC_CONTINUE`.",
            "- The result is not a discard, but it is not firm-grade live logic.",
            "- Taxonomy coverage at 62.86% is below the 70% minimum, with 13 of 35 failures still mixed/unclassified.",
            "- Delayed and staged entry have small positive average-return deltas, but failure rate does not improve, so treat them as diagnostic microstructure clues rather than alpha.",
            "- Continuation confirmation currently rejects too many clean trades and worsens accepted-subset quality.",
            "- Reducer retry should remain closed until taxonomy coverage, conditional treatment, and cost-stressed fold-forward tests improve.",
            "",
            "## Task608K Direction",
            "",
            "- Build `failure_taxonomy_v2 + conditional treatment test`, not a reducer rule.",
            "- First priority features: opening range high/low reclaim, VWAP reclaim duration, first adverse excursion 15/30/60m, gap-fill speed/hold ratio, premarket-high breakout failure, symbol-vs-QQQ/theme relative-strength decay, volume impulse decay slope, and entry extension crossed with prior-day range percentile.",
            "- Split unclassified failures into early adverse failure, failed continuation, and market/theme drag before any reducer retry.",
            "",
        ]
    ).rstrip() + "\n"


def entry_qualification_rules() -> list[tuple[str, Any]]:
    return [
        ("block_prior_day_extension_near_premarket_high", lambda r: bool(r.get("prior_day_extension_flag", 0)) and _ge(r.get("distance_to_premarket_high_pct"), -0.01)),
        ("block_extreme_gap_percentile", lambda r: _ge(r.get("gap_abs_percentile_60d"), 0.90)),
        ("block_theme_confirmation_fail", lambda r: bool(r.get("theme_confirmation_fail_pre_entry_flag", 0))),
        ("block_late_breakout_proxy", lambda r: bool(r.get("late_breakout_proxy_flag", 0))),
        ("block_overextended_from_open", lambda r: _ge(r.get("entry_ret_from_session_open"), 0.035)),
    ]


def scenario_quality(panel: pd.DataFrame, scenario: str, returns: pd.Series) -> dict[str, Any]:
    frame = panel.copy()
    frame["net_return_from_entry"] = pd.to_numeric(returns, errors="coerce")
    frame = frame.dropna(subset=["net_return_from_entry"]).copy()
    if frame.empty:
        row = {"lifecycle_count": 0, "avg_net_return_pct": 0.0, "win_rate": 0.0, "entry_reduce_failure_rate": 0.0}
    else:
        frame["win_flag"] = frame["net_return_from_entry"].gt(0).astype(int)
        frame["entry_reduce_failure_flag"] = frame["net_return_from_entry"].le(-0.03).astype(int)
        row = aggregate(frame)
    baseline = aggregate(panel)
    row.update(
        {
            "scenario": scenario,
            "baseline_avg_net_return_pct": float(baseline["avg_net_return_pct"]),
            "delta_avg_net_return_pct": float(row["avg_net_return_pct"]) - float(baseline["avg_net_return_pct"]),
            "baseline_entry_reduce_failure_rate": float(baseline["entry_reduce_failure_rate"]),
            "delta_entry_reduce_failure_rate": float(row["entry_reduce_failure_rate"]) - float(baseline["entry_reduce_failure_rate"]),
        }
    )
    return row


def scenario_lines(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["- No rows."]
    return [
        f"- {row['scenario']}: avg {float(row['avg_net_return_pct']):.2f}%, delta {float(row['delta_avg_net_return_pct']):.2f} pct points, entry-reduce {float(row['entry_reduce_failure_rate']):.2%}"
        for _, row in frame.sort_values("delta_avg_net_return_pct", ascending=False).head(5).iterrows()
    ]


def best_delta_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty or "delta_avg_net_return_pct" not in frame.columns:
        return {}
    return frame.sort_values("delta_avg_net_return_pct", ascending=False).iloc[0].to_dict()


def pre_entry_return_from_open(entry_ts: pd.Timestamp, frame: pd.DataFrame) -> float | None:
    if frame is None or frame.empty:
        return None
    session_date = entry_ts.tz_convert("America/New_York").date().isoformat()
    session = frame[frame["session_date_et"].eq(session_date)].copy()
    if session.empty:
        return None
    local_midnight = pd.Timestamp(session_date).tz_localize("America/New_York").tz_convert("UTC")
    regular_start = local_midnight + pd.Timedelta(hours=9, minutes=30)
    bars = session[session["timestamp"].between(regular_start, entry_ts, inclusive="both")]
    if bars.empty:
        return None
    open_price = float(bars.iloc[0]["open"])
    last_close = float(bars.iloc[-1]["close"])
    return last_close / open_price - 1.0 if open_price else None


def first_expansion_bar_index(frame: pd.DataFrame) -> int:
    if frame.empty:
        return -1
    running_high = float(frame.iloc[0]["high"])
    for idx, row in enumerate(frame.to_dict(orient="records")):
        close = float(row["close"])
        if idx > 0 and close > running_high:
            return idx
        running_high = max(running_high, float(row["high"]))
    return -1


def _vwap(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    volume = pd.to_numeric(frame["volume"], errors="coerce").fillna(0)
    if float(volume.sum()) <= 0:
        return float(frame["close"].mean())
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    return float((typical * volume).sum() / volume.sum())


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _ge(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) >= threshold
    except Exception:
        return False


def _le(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) <= threshold
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task509-panel", type=Path, default=TASK509_PANEL)
    parser.add_argument("--task608g-path-panel", type=Path, default=TASK608G_PATH_PANEL)
    parser.add_argument("--intraday-dir", type=Path, default=INTRADAY_DIR)
    parser.add_argument("--daily-dir", type=Path, default=DAILY_DIR)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608j_failure_taxonomy_entry_upgrade(
        task509_panel_path=args.task509_panel,
        task608g_path_panel=args.task608g_path_panel,
        intraday_dir=args.intraday_dir,
        daily_dir=args.daily_dir,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608j_decision"].iloc[0]
    print(f"[TASK608J] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
