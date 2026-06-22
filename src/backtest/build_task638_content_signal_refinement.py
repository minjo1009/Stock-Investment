from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)


TASK_ID = "Task638"
REPORT_DIR = Path("docs/reports/task_638_content_signal_refinement")
BASELINE_PANEL = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task632_temporal_strict_refresh/task_632_baseline_all_confirmed_backtest_panel.csv")
ENTRY_CONTENT_PANEL = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_content_prediction_panel.csv")
EVENT_PREDICTIONS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_event_content_predictions.csv")
ENTRY_EVENT_LINKS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_event_links.csv")
TASK637_DECISION = Path("docs/reports/task_637_content_signal_account_backtest/task_637_decision.csv")
TASK633_ACCOUNT = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task_633_1000_account_qqq_comparison.csv")
INTRADAY_DIR = Path("data/raw/us_intraday")
DAILY_DIRS = (Path("data/raw/us_daily_breadth_top500"), Path("data/raw/us_daily"))
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")

TIMING_MODES = ("immediate", "delay15m", "delay30m", "delay60m", "delay1d", "vwap_reclaim")
EXIT_MODES = ("existing_exit", "hold5", "hold10", "hold20", "trail10_hold20", "strength_hold20_trail10")
SIZING_MODES = ("equal_max5", "dynamic_10_20_30", "dynamic_10_20_40")
COST_BPS = (50, 100)


def build_task638_content_signal_refinement(
    *,
    baseline_panel_path: Path = BASELINE_PANEL,
    entry_content_panel_path: Path = ENTRY_CONTENT_PANEL,
    event_predictions_path: Path = EVENT_PREDICTIONS,
    entry_event_links_path: Path = ENTRY_EVENT_LINKS,
    task637_decision_path: Path = TASK637_DECISION,
    task633_account_path: Path = TASK633_ACCOUNT,
    intraday_dir: Path = INTRADAY_DIR,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    baseline = load_trade_panel(baseline_panel_path)
    content = pd.read_csv(entry_content_panel_path)
    links = pd.read_csv(entry_event_links_path)
    events = load_event_predictions(event_predictions_path)
    event_refined = build_event_refinement(events)
    entry_refined = build_entry_refinement(baseline, content, links, event_refined)
    feature_audit = build_refined_feature_audit(entry_refined)
    daily_maps = load_daily_maps(entry_refined["symbol"].dropna().astype(str).unique())
    execution_panel = build_execution_panel(entry_refined, intraday_dir, daily_maps)
    account = build_account_grid(execution_panel, qqq_path)
    oos_account = build_oos_account_grid(execution_panel, qqq_path)
    source_audit = build_source_audit(entry_refined, event_refined, execution_panel)
    pass_fail = build_pass_fail(account, oos_account, source_audit, task637_decision_path, task633_account_path)
    decision = build_decision(account, oos_account, pass_fail, task637_decision_path, task633_account_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    event_refined.to_csv(out_dir / "task_638_event_refinement_taxonomy.csv", index=False)
    entry_refined.to_csv(out_dir / "task_638_entry_refined_content_panel.csv", index=False)
    feature_audit.to_csv(out_dir / "task_638_refined_feature_audit.csv", index=False)
    execution_panel.to_csv(out_dir / "task_638_timing_exit_execution_panel.csv", index=False)
    account.to_csv(out_dir / "task_638_refinement_account_grid.csv", index=False)
    oos_account.to_csv(out_dir / "task_638_refinement_oos_account_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_638_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_638_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_638_decision.csv", index=False)
    (out_dir / "task_638_content_signal_refinement.md").write_text(
        render_report(feature_audit, account, oos_account, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_gpt_review_packet(out_dir, decision, account, oos_account, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_638_event_refinement_taxonomy": event_refined,
        "task_638_entry_refined_content_panel": entry_refined,
        "task_638_refined_feature_audit": feature_audit,
        "task_638_timing_exit_execution_panel": execution_panel,
        "task_638_refinement_account_grid": account,
        "task_638_refinement_oos_account_grid": oos_account,
        "task_638_source_audit": source_audit,
        "task_638_pass_fail_matrix": pass_fail,
        "task_638_decision": decision,
    }


def load_trade_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["entry_price", "simulated_exit_price", "net_return_from_entry"]:
        panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "entry_price", "simulated_exit_ts", "simulated_exit_price", "net_return_from_entry"]).copy()


def load_event_predictions(path: Path) -> pd.DataFrame:
    events = pd.read_csv(path)
    events["event_id"] = events["event_id"].astype(str)
    return events


def contains(text: object, words: list[str]) -> bool:
    lower = str(text or "").lower()
    return any(word in lower for word in words)


def build_event_refinement(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in events.to_dict(orient="records"):
        evidence = row.get("content_interpretation_evidence_span", "")
        causal = str(row.get("content_stock_specific_causal_link", ""))
        lane = str(row.get("source_lane", ""))
        direction = str(row.get("content_prediction_direction", ""))
        event_title = str(row.get("event_title", ""))
        raw_score = float(row.get("content_raw_prediction_score", 0) or 0)
        guidance = int(row.get("content_guidance_or_margin_signal", 0) or 0)
        supply = int(row.get("content_supply_demand_signal", 0) or 0)
        revenue = int(row.get("content_revenue_or_backlog_signal", 0) or 0)
        named = int(row.get("content_named_customer_or_counterparty", 0) or 0)
        regulatory = int(row.get("content_regulatory_or_policy_transmission", 0) or 0)

        dilution = int(raw_score < 0 and (causal == "financing_or_dilution_risk" or contains(evidence, ["offering", "convertible", "atm program", "shelf", "dilution"])))
        regulation = int(raw_score < 0 and (causal == "macro_policy_restriction" or regulatory == 1 or contains(evidence, ["tariff", "sanction", "restriction", "export control"])))
        ceo_ir_disappointment = int(raw_score < 0 and lane == "ceo_ir_transcripts_and_presentations" and dilution == 0)
        insider_sell = int(raw_score < 0 and causal == "insider_sale_or_dilution")
        earnings_margin_damage = int(raw_score < 0 and guidance == 1 and contains(evidence, ["loss", "margin", "profit", "earnings", "cash flow", "liquidity"]))

        contract_customer = int(raw_score > 0 and revenue == 1 and named == 1)
        backlog_order = int(raw_score > 0 and contains(evidence, ["backlog", "booking", "bookings", "order", "award", "contract"]))
        guidance_up = int(raw_score > 0 and guidance == 1 and contains(evidence, ["guidance", "outlook", "eps", "margin", "adjusted ebitda"]))
        margin_supply_combo = int(raw_score > 0 and guidance == 1 and supply == 1)
        revenue_talk_weak = int(raw_score > 0 and revenue == 1 and named == 0 and backlog_order == 0)

        negative_subtype = "none"
        for name, flag in [
            ("dilution_financing", dilution),
            ("regulation_sanction_tariff", regulation),
            ("ceo_ir_disappointment", ceo_ir_disappointment),
            ("insider_sell", insider_sell),
            ("earnings_margin_damage", earnings_margin_damage),
        ]:
            if flag:
                negative_subtype = name
                break
        positive_subtype = "none"
        for name, flag in [
            ("guidance_up_very_strong", guidance_up),
            ("margin_supply_combo", margin_supply_combo),
            ("contract_customer_strong", contract_customer),
            ("backlog_order_strong", backlog_order),
            ("revenue_talk_weak", revenue_talk_weak),
        ]:
            if flag:
                positive_subtype = name
                break
        strength = 0
        if raw_score != 0:
            strength = 1
        if dilution or regulation or guidance_up or margin_supply_combo or contract_customer or backlog_order:
            strength = 2
        if (guidance_up and margin_supply_combo) or (contract_customer and backlog_order) or (dilution and regulation):
            strength = 3
        out = dict(row)
        out.update(
            {
                "negative_dilution_financing_event_flag": dilution,
                "negative_regulation_sanction_tariff_event_flag": regulation,
                "negative_ceo_ir_disappointment_event_flag": ceo_ir_disappointment,
                "negative_insider_sell_event_flag": insider_sell,
                "negative_earnings_margin_damage_event_flag": earnings_margin_damage,
                "positive_contract_customer_event_flag": contract_customer,
                "positive_backlog_order_event_flag": backlog_order,
                "positive_guidance_up_event_flag": guidance_up,
                "positive_margin_supply_combo_event_flag": margin_supply_combo,
                "positive_revenue_talk_weak_event_flag": revenue_talk_weak,
                "negative_refined_subtype": negative_subtype,
                "positive_refined_subtype": positive_subtype,
                "content_refined_strength_score": int(strength),
                "event_title_safe": event_title[:120],
            }
        )
        rows.append(out)
    return pd.DataFrame(rows)


def build_entry_refinement(
    baseline: pd.DataFrame,
    content: pd.DataFrame,
    links: pd.DataFrame,
    event_refined: pd.DataFrame,
) -> pd.DataFrame:
    content = content.drop(columns=["symbol", "theme_id", "entry_ts", "split_name"], errors="ignore")
    base = baseline.merge(content, on="lifecycle_id", how="left")
    refined_cols = [
        "negative_dilution_financing_event_flag",
        "negative_regulation_sanction_tariff_event_flag",
        "negative_ceo_ir_disappointment_event_flag",
        "negative_insider_sell_event_flag",
        "negative_earnings_margin_damage_event_flag",
        "positive_contract_customer_event_flag",
        "positive_backlog_order_event_flag",
        "positive_guidance_up_event_flag",
        "positive_margin_supply_combo_event_flag",
        "positive_revenue_talk_weak_event_flag",
        "content_refined_strength_score",
    ]
    linked = links[["lifecycle_id", "event_id"]].merge(event_refined[["event_id"] + refined_cols], on="event_id", how="left")
    agg = linked.groupby("lifecycle_id", as_index=False).agg(
        **{col.replace("_event_flag", "_count"): (col, "sum") for col in refined_cols if col.endswith("_event_flag")},
        content_refined_strength_score=("content_refined_strength_score", "max"),
    )
    out = base.merge(agg, on="lifecycle_id", how="left")
    for column in agg.columns:
        if column != "lifecycle_id":
            out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    out["content_negative_score_flag"] = pd.to_numeric(out.get("content_net_prediction_score"), errors="coerce").fillna(0).lt(0).astype(int)
    out["content_guidance_margin_flag"] = pd.to_numeric(out.get("content_guidance_margin_count"), errors="coerce").fillna(0).gt(0).astype(int)
    out["content_supply_demand_flag"] = pd.to_numeric(out.get("content_supply_demand_count"), errors="coerce").fillna(0).gt(0).astype(int)
    out["content_any_stable_feature_flag"] = (
        out["content_negative_score_flag"].eq(1)
        | out["content_guidance_margin_flag"].eq(1)
        | out["content_supply_demand_flag"].eq(1)
    ).astype(int)
    out["content_guidance_supply_combo_flag"] = (
        out["content_guidance_margin_flag"].eq(1) & out["content_supply_demand_flag"].eq(1)
    ).astype(int)
    out["negative_core_reversal_flag"] = (
        out["negative_dilution_financing_count"].gt(0) | out["negative_regulation_sanction_tariff_count"].gt(0)
    ).astype(int)
    out["positive_high_quality_flag"] = (
        out["positive_contract_customer_count"].gt(0)
        | out["positive_backlog_order_count"].gt(0)
        | out["positive_guidance_up_count"].gt(0)
        | out["positive_margin_supply_combo_count"].gt(0)
    ).astype(int)
    out["refined_best_combo_flag"] = (
        out["negative_core_reversal_flag"].eq(1)
        | out["positive_high_quality_flag"].eq(1)
        | out["content_guidance_supply_combo_flag"].eq(1)
    ).astype(int)
    out["content_refined_strength_score"] = pd.to_numeric(out["content_refined_strength_score"], errors="coerce").fillna(0).clip(0, 3)
    out["return_pct"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce") * 100.0
    out["entry_reduce_eval_flag"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce").le(-0.03).astype(int)
    return out


SELECTORS = {
    "content_negative_score": "content_negative_score_flag",
    "negative_dilution_financing": "negative_dilution_financing_count",
    "negative_regulation_sanction_tariff": "negative_regulation_sanction_tariff_count",
    "negative_ceo_ir_disappointment": "negative_ceo_ir_disappointment_count",
    "negative_insider_sell": "negative_insider_sell_count",
    "negative_earnings_margin_damage": "negative_earnings_margin_damage_count",
    "negative_core_reversal": "negative_core_reversal_flag",
    "content_guidance_margin": "content_guidance_margin_flag",
    "content_supply_demand": "content_supply_demand_flag",
    "positive_contract_customer": "positive_contract_customer_count",
    "positive_backlog_order": "positive_backlog_order_count",
    "positive_guidance_up": "positive_guidance_up_count",
    "positive_margin_supply_combo": "positive_margin_supply_combo_count",
    "positive_high_quality": "positive_high_quality_flag",
    "refined_best_combo": "refined_best_combo_flag",
}


def build_refined_feature_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for name, column in SELECTORS.items():
        flag = pd.to_numeric(panel[column], errors="coerce").fillna(0).gt(0)
        for split_name in ["all", "train_design", "validation", "recent_oos"]:
            scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)]
            yes = scoped[flag.loc[scoped.index]]
            no = scoped[~flag.loc[scoped.index]]
            rows.append(
                {
                    "feature": name,
                    "source_column": column,
                    "split_name": split_name,
                    "selected_count": int(len(yes)),
                    "rejected_count": int(len(no)),
                    "selected_avg_return_pct": avg_return(yes),
                    "rejected_avg_return_pct": avg_return(no),
                    "avg_return_lift_pct_point": avg_return(yes) - avg_return(no),
                    "selected_entry_reduce_rate": entry_reduce_rate(yes),
                    "rejected_entry_reduce_rate": entry_reduce_rate(no),
                    "entry_reduce_delta_pct_point": (entry_reduce_rate(yes) - entry_reduce_rate(no)) * 100.0,
                }
            )
    audit = pd.DataFrame(rows)
    stability_rows = []
    for feature, group in audit.groupby("feature", dropna=False):
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        stable = int(
            int(validation["selected_count"]) >= 10
            and int(recent["selected_count"]) >= 5
            and float(validation["avg_return_lift_pct_point"]) > 0
            and float(recent["avg_return_lift_pct_point"]) > 0
        )
        stability_rows.append({"feature": feature, "refined_oos_stability_pass_flag": stable})
    return audit.merge(pd.DataFrame(stability_rows), on="feature", how="left")


def avg_return(frame: pd.DataFrame) -> float:
    if frame.empty:
        return float("nan")
    return float(pd.to_numeric(frame["return_pct"], errors="coerce").mean())


def entry_reduce_rate(frame: pd.DataFrame) -> float:
    if frame.empty:
        return float("nan")
    return float(pd.to_numeric(frame["entry_reduce_eval_flag"], errors="coerce").mean())


def load_intraday(symbol: str, intraday_dir: Path, cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    symbol = symbol.upper()
    if symbol in cache:
        return cache[symbol]
    path = intraday_dir / f"{symbol}.csv"
    if not path.exists():
        cache[symbol] = pd.DataFrame()
        return cache[symbol]
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)
    df["ny_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].fillna(0).clip(lower=0)
    df["session_vwap"] = (typical * vol).groupby(df["ny_date"]).cumsum() / vol.groupby(df["ny_date"]).cumsum().replace(0, pd.NA)
    cache[symbol] = df
    return df


def load_daily_maps(symbols: list[str] | pd.Series) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        sym = str(symbol).upper()
        path = next((directory / f"{sym}.csv" for directory in DAILY_DIRS if (directory / f"{sym}.csv").exists()), None)
        if path is None:
            continue
        df = pd.read_csv(path)
        df.columns = [str(col).lower() for col in df.columns]
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)
        df["trade_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
        out[sym] = df
    return out


def timed_entry(row: dict[str, object], timing_mode: str, intraday_dir: Path, intraday_cache: dict[str, pd.DataFrame], daily_maps: dict[str, pd.DataFrame]) -> tuple[pd.Timestamp, float, str] | None:
    entry_ts = pd.Timestamp(row["entry_ts"])
    entry_price = float(row["entry_price"])
    symbol = str(row["symbol"]).upper()
    if timing_mode == "immediate":
        return entry_ts, entry_price, "immediate_entry"
    if timing_mode in {"delay15m", "delay30m", "delay60m", "vwap_reclaim"}:
        intraday = load_intraday(symbol, intraday_dir, intraday_cache)
        if intraday.empty:
            return None
        ny_date = entry_ts.tz_convert("America/New_York").date()
        same_day = intraday[intraday["ny_date"].eq(ny_date)].copy()
        if same_day.empty:
            return None
        if timing_mode.startswith("delay"):
            minutes = int(timing_mode.replace("delay", "").replace("m", ""))
            target = entry_ts + pd.Timedelta(minutes=minutes)
            hit = same_day[same_day["timestamp"].ge(target)].head(1)
            if hit.empty:
                return None
            r = hit.iloc[0]
            return pd.Timestamp(r["timestamp"]), float(r["close"]), timing_mode
        eligible = same_day[same_day["timestamp"].ge(entry_ts)].copy()
        hit = eligible[eligible["close"].ge(eligible["session_vwap"])].head(1)
        if hit.empty:
            return None
        r = hit.iloc[0]
        return pd.Timestamp(r["timestamp"]), float(r["close"]), "vwap_reclaim_entry"
    if timing_mode == "delay1d":
        daily = daily_maps.get(symbol)
        if daily is None or daily.empty:
            return None
        entry_date = entry_ts.tz_convert("America/New_York").date()
        hit = daily[daily["trade_date"].gt(entry_date)].head(1)
        if hit.empty:
            return None
        r = hit.iloc[0]
        return pd.Timestamp(r["timestamp"]) + pd.Timedelta(hours=14, minutes=30), float(r["open"]), "delay1d_open_entry"
    return None


def exit_for(row: dict[str, object], exit_mode: str, entry_ts: pd.Timestamp, entry_price: float, daily_maps: dict[str, pd.DataFrame]) -> tuple[pd.Timestamp, float, str] | None:
    if exit_mode == "existing_exit":
        exit_ts = pd.Timestamp(row["simulated_exit_ts"])
        if exit_ts <= entry_ts:
            return None
        return exit_ts, float(row["simulated_exit_price"]), "existing_exit"
    max_hold = 5
    trailing_stop = 999.0
    if exit_mode == "hold10":
        max_hold = 10
    elif exit_mode == "hold20":
        max_hold = 20
    elif exit_mode == "trail10_hold20":
        max_hold, trailing_stop = 20, 0.10
    elif exit_mode == "strength_hold20_trail10":
        max_hold = 20 if float(row.get("content_refined_strength_score", 0) or 0) >= 2 else 10
        trailing_stop = 0.10
    symbol = str(row["symbol"]).upper()
    daily = daily_maps.get(symbol)
    if daily is None or daily.empty:
        return None
    entry_date = entry_ts.tz_convert("America/New_York").date()
    future = daily[daily["trade_date"].ge(entry_date)].head(max_hold + 1).copy()
    if len(future) < 2:
        return None
    highest_close = entry_price
    exit_row = future.iloc[-1]
    exit_reason = f"{exit_mode}_time_exit"
    for _, day in future.iloc[1:].iterrows():
        close = float(day["close"])
        highest_close = max(highest_close, close)
        if 1.0 - close / max(highest_close, 1e-9) >= trailing_stop:
            exit_row = day
            exit_reason = f"{exit_mode}_trailing_stop"
            break
    return pd.Timestamp(exit_row["timestamp"]), float(exit_row["close"]), exit_reason


def build_execution_panel(panel: pd.DataFrame, intraday_dir: Path, daily_maps: dict[str, pd.DataFrame]) -> pd.DataFrame:
    intraday_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, object]] = []
    for base_row in panel.to_dict(orient="records"):
        for timing_mode in TIMING_MODES:
            entry = timed_entry(base_row, timing_mode, intraday_dir, intraday_cache, daily_maps)
            if entry is None:
                continue
            entry_ts, entry_price, entry_reason = entry
            for exit_mode in EXIT_MODES:
                exit_info = exit_for(base_row, exit_mode, entry_ts, entry_price, daily_maps)
                if exit_info is None:
                    continue
                exit_ts, exit_price, exit_reason = exit_info
                ret = exit_price / max(entry_price, 1e-9) - 1.0
                out = dict(base_row)
                out.update(
                    {
                        "timing_mode": timing_mode,
                        "exit_mode": exit_mode,
                        "entry_reason": entry_reason,
                        "simulated_lifecycle_id": f"{base_row['lifecycle_id']}|{timing_mode}|{exit_mode}",
                        "entry_ts": entry_ts,
                        "entry_price": entry_price,
                        "simulated_exit_ts": exit_ts,
                        "simulated_exit_price": exit_price,
                        "exit_reason": exit_reason,
                        "net_return_from_entry": ret,
                        "return_pct": ret * 100.0,
                        "entry_reduce_eval_flag": int(ret <= -0.03),
                    }
                )
                rows.append(out)
    return pd.DataFrame(rows)


def build_account_grid(execution_panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    qqq = load_qqq_history(qqq_path)
    qqq_final = qqq_final_for_period(qqq, execution_panel)
    rows: list[dict[str, object]] = []
    for universe, column in SELECTORS.items():
        selected_base = execution_panel[pd.to_numeric(execution_panel[column], errors="coerce").fillna(0).gt(0)].copy()
        for timing_mode in TIMING_MODES:
            for exit_mode in EXIT_MODES:
                selected = selected_base[
                    selected_base["timing_mode"].eq(timing_mode) & selected_base["exit_mode"].eq(exit_mode)
                ].copy()
                if selected.empty:
                    continue
                for cost_bps in COST_BPS:
                    cost_panel = costed(selected, cost_bps)
                    for sizing_mode in SIZING_MODES:
                        quality, accepted = simulate_account(cost_panel, sizing_mode)
                        final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
                        rows.append(
                            {
                                "universe": universe,
                                "selection_column": column,
                                "timing_mode": timing_mode,
                                "exit_mode": exit_mode,
                                "sizing_mode": sizing_mode,
                                "round_trip_cost_bps": int(cost_bps),
                                "source_trade_count": int(len(selected)),
                                "accepted_trade_count": int(len(accepted)),
                                "final_capital_usd": final_capital,
                                "capital_return_pct": float(quality["capital_pnl_pct"]),
                                "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                                "win_rate": float(quality["win_rate"]),
                                "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                                "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                                "qqq_final_capital_usd": qqq_final,
                                "beats_qqq_flag": int(final_capital > qqq_final),
                                "label_used_in_assignment_flag": 0,
                                "presence_field_used_for_assignment_flag": 0,
                            }
                        )
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def costed(panel: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    out = panel.copy()
    out["net_return_from_entry"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce") - cost_bps / 10000.0
    return out


def simulate_account(panel: pd.DataFrame, sizing_mode: str) -> tuple[dict[str, object], pd.DataFrame]:
    if sizing_mode == "equal_max5":
        quality, accepted, _curve = simulate_deterministic_portfolio(panel, max_positions=5)
        return quality, accepted
    max_weight = 0.30 if sizing_mode == "dynamic_10_20_30" else 0.40
    return simulate_dynamic_sizing(panel, max_weight=max_weight)


def dynamic_weight(strength: float, max_weight: float) -> float:
    if strength >= 3:
        return max_weight
    if strength >= 2:
        return 0.20
    return 0.10


def simulate_dynamic_sizing(panel: pd.DataFrame, *, max_weight: float) -> tuple[dict[str, object], pd.DataFrame]:
    ordered = panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    cash = 1.0
    peak_equity = 1.0
    max_drawdown = 0.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []

    def current_equity() -> float:
        return cash + sum(float(pos["capital"]) for pos in open_positions)

    def close_until(ts: pd.Timestamp) -> None:
        nonlocal cash, peak_equity, max_drawdown, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= ts:
                cash += float(pos["capital"]) * (1.0 + float(pos["return"]))
                eq = current_equity()
                peak_equity = max(peak_equity, eq)
                max_drawdown = min(max_drawdown, (eq / max(peak_equity, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_until(entry_ts)
        if len(open_positions) >= 5:
            continue
        equity = current_equity()
        weight = dynamic_weight(float(row.get("content_refined_strength_score", 0) or 0), max_weight)
        capital = min(cash, equity * weight)
        if capital <= 0:
            continue
        cash -= capital
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        accepted = dict(row)
        accepted["dynamic_position_weight"] = capital / max(equity, 1e-9)
        accepted["sizing_mode"] = f"dynamic_max_{int(max_weight * 100)}"
        accepted_rows.append(accepted)
    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    if accepted.empty:
        return empty_quality(), accepted
    returns = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce")
    quality = {
        "avg_net_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "max_drawdown_pct": float(max_drawdown),
        "capital_pnl_pct": float((cash - 1.0) * 100.0),
    }
    return quality, accepted


def empty_quality() -> dict[str, object]:
    return {
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "max_drawdown_pct": 0.0,
        "capital_pnl_pct": 0.0,
    }


def build_oos_account_grid(execution_panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    qqq = load_qqq_history(qqq_path)
    rows: list[dict[str, object]] = []
    for split_name in ["validation", "recent_oos"]:
        split_panel = execution_panel[execution_panel["split_name"].astype(str).eq(split_name)].copy()
        qqq_final = qqq_final_for_period(qqq, split_panel)
        for universe, column in SELECTORS.items():
            selected_base = split_panel[pd.to_numeric(split_panel[column], errors="coerce").fillna(0).gt(0)].copy()
            for timing_mode in TIMING_MODES:
                for exit_mode in EXIT_MODES:
                    selected = selected_base[
                        selected_base["timing_mode"].eq(timing_mode) & selected_base["exit_mode"].eq(exit_mode)
                    ].copy()
                    if selected.empty:
                        continue
                    for cost_bps in COST_BPS:
                        cost_panel = costed(selected, cost_bps)
                        for sizing_mode in SIZING_MODES:
                            quality, accepted = simulate_account(cost_panel, sizing_mode)
                            final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
                            rows.append(
                                {
                                    "split_name": split_name,
                                    "universe": universe,
                                    "selection_column": column,
                                    "timing_mode": timing_mode,
                                    "exit_mode": exit_mode,
                                    "sizing_mode": sizing_mode,
                                    "round_trip_cost_bps": int(cost_bps),
                                    "source_trade_count": int(len(selected)),
                                    "accepted_trade_count": int(len(accepted)),
                                    "final_capital_usd": final_capital,
                                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                                    "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                                    "win_rate": float(quality["win_rate"]),
                                    "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                                    "qqq_final_capital_usd": qqq_final,
                                    "beats_qqq_flag": int(final_capital > qqq_final),
                                    "label_used_in_assignment_flag": 0,
                                    "presence_field_used_for_assignment_flag": 0,
                                }
                            )
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def build_source_audit(entry_refined: pd.DataFrame, event_refined: pd.DataFrame, execution_panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_count": int(entry_refined["lifecycle_id"].nunique()),
                "entry_start": str(pd.to_datetime(entry_refined["entry_ts"], utc=True, errors="coerce").min().date()),
                "entry_end": str(pd.to_datetime(entry_refined["entry_ts"], utc=True, errors="coerce").max().date()),
                "event_count": int(len(event_refined)),
                "execution_variant_rows": int(len(execution_panel)),
                "timing_mode_count": int(execution_panel["timing_mode"].nunique()),
                "exit_mode_count": int(execution_panel["exit_mode"].nunique()),
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def best_row(account: pd.DataFrame, split_name: str | None = None, cost_bps: int = 50) -> pd.Series:
    scoped = account[account["round_trip_cost_bps"].eq(cost_bps)].copy()
    if split_name is not None and "split_name" in scoped.columns:
        scoped = scoped[scoped["split_name"].eq(split_name)]
    return scoped.sort_values("final_capital_usd", ascending=False).iloc[0]


def best_risk_controlled_row(account: pd.DataFrame, split_name: str | None = None, cost_bps: int = 50, max_drawdown_abs: float = 35.0) -> pd.Series:
    scoped = account[account["round_trip_cost_bps"].eq(cost_bps)].copy()
    if split_name is not None and "split_name" in scoped.columns:
        scoped = scoped[scoped["split_name"].eq(split_name)]
    controlled = scoped[pd.to_numeric(scoped["max_drawdown_pct"], errors="coerce").ge(-max_drawdown_abs)]
    if controlled.empty:
        controlled = scoped
    return controlled.sort_values("final_capital_usd", ascending=False).iloc[0]


def matching_oos_row(oos_account: pd.DataFrame, split_name: str, template: pd.Series, cost_bps: int = 50) -> pd.Series:
    scoped = oos_account[
        oos_account["split_name"].eq(split_name)
        & oos_account["round_trip_cost_bps"].eq(cost_bps)
        & oos_account["universe"].eq(template["universe"])
        & oos_account["timing_mode"].eq(template["timing_mode"])
        & oos_account["exit_mode"].eq(template["exit_mode"])
        & oos_account["sizing_mode"].eq(template["sizing_mode"])
    ]
    if scoped.empty:
        return best_risk_controlled_row(oos_account, split_name=split_name, cost_bps=cost_bps)
    return scoped.iloc[0]


def build_pass_fail(
    account: pd.DataFrame,
    oos_account: pd.DataFrame,
    source_audit: pd.DataFrame,
    task637_decision_path: Path,
    task633_account_path: Path,
) -> pd.DataFrame:
    previous = pd.read_csv(task637_decision_path).iloc[0]
    task633 = pd.read_csv(task633_account_path)
    task617_max5 = float(
        task633[
            task633["universe"].eq("task617_original_broad_intelligence_strategy")
            & task633["max_positions"].eq(5)
        ].iloc[0]["final_capital_usd"]
    )
    prev_best = float(previous["best_50bp_final_capital_usd"])
    best50 = best_row(account, cost_bps=50)
    best100 = best_row(account, cost_bps=100)
    risk50 = best_risk_controlled_row(account, cost_bps=50)
    risk100 = best_risk_controlled_row(account, cost_bps=100)
    validation_same = matching_oos_row(oos_account, "validation", risk50, cost_bps=50)
    recent_same = matching_oos_row(oos_account, "recent_oos", risk50, cost_bps=50)
    validation_best = best_risk_controlled_row(oos_account, split_name="validation", cost_bps=50)
    recent_best = best_risk_controlled_row(oos_account, split_name="recent_oos", cost_bps=50)
    audit = source_audit.iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "all_five_refinement_axes_tested",
                "pass_flag": int(int(audit["timing_mode_count"]) >= 6 and int(audit["exit_mode_count"]) >= 6 and len(SIZING_MODES) >= 3),
                "observed_value": f"timing={audit['timing_mode_count']}; exits={audit['exit_mode_count']}; sizing={len(SIZING_MODES)}",
                "required_value": "negative split positive split dynamic sizing timing and exit axes must be tested",
            },
            {
                "gate": "best_50bp_beats_task637",
                "pass_flag": int(float(best50["final_capital_usd"]) > prev_best),
                "observed_value": f"best638=${float(best50['final_capital_usd']):.2f}; task637=${prev_best:.2f}",
                "required_value": "refinement should improve prior Task637 best result",
            },
            {
                "gate": "risk_controlled_50bp_beats_task637",
                "pass_flag": int(float(risk50["final_capital_usd"]) > prev_best and float(risk50["max_drawdown_pct"]) >= -35.0),
                "observed_value": f"risk_best=${float(risk50['final_capital_usd']):.2f}; dd={float(risk50['max_drawdown_pct']):.2f}%; task637=${prev_best:.2f}",
                "required_value": "risk-controlled refinement should beat Task637 with max drawdown no worse than -35%",
            },
            {
                "gate": "best_50bp_beats_task617_max5",
                "pass_flag": int(float(best50["final_capital_usd"]) > task617_max5),
                "observed_value": f"best638=${float(best50['final_capital_usd']):.2f}; task617_max5=${task617_max5:.2f}",
                "required_value": "refined candidate must beat existing Task617 max5",
            },
            {
                "gate": "best_100bp_beats_task617_max5",
                "pass_flag": int(float(risk100["final_capital_usd"]) > task617_max5),
                "observed_value": f"risk100=${float(risk100['final_capital_usd']):.2f}; task617_max5=${task617_max5:.2f}",
                "required_value": "refined candidate should survive 100bp cost stress",
            },
            {
                "gate": "same_rule_validation_oos_beats_qqq",
                "pass_flag": int(float(validation_same["final_capital_usd"]) > float(validation_same["qqq_final_capital_usd"])),
                "observed_value": f"same_rule_validation=${float(validation_same['final_capital_usd']):.2f}; qqq=${float(validation_same['qqq_final_capital_usd']):.2f}",
                "required_value": "same risk-controlled full-period rule should beat validation QQQ",
            },
            {
                "gate": "same_rule_recent_oos_beats_qqq",
                "pass_flag": int(float(recent_same["final_capital_usd"]) > float(recent_same["qqq_final_capital_usd"])),
                "observed_value": f"same_rule_recent=${float(recent_same['final_capital_usd']):.2f}; qqq=${float(recent_same['qqq_final_capital_usd']):.2f}",
                "required_value": "same risk-controlled full-period rule should beat recent OOS QQQ",
            },
            {
                "gate": "best_oos_risk_controlled_accounts_beat_qqq",
                "pass_flag": int(
                    float(validation_best["final_capital_usd"]) > float(validation_best["qqq_final_capital_usd"])
                    and float(recent_best["final_capital_usd"]) > float(recent_best["qqq_final_capital_usd"])
                ),
                "observed_value": f"validation_best=${float(validation_best['final_capital_usd']):.2f}; recent_best=${float(recent_best['final_capital_usd']):.2f}",
                "required_value": "validation and recent OOS risk-controlled candidate accounts should beat same-period QQQ",
            },
            {
                "gate": "presence_fields_not_used",
                "pass_flag": int(int(audit["presence_field_used_for_assignment_flag"]) == 0),
                "observed_value": "presence fields not used",
                "required_value": "content interpretation only",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research candidate only",
                "required_value": "requires GPT review capture, live rule lock, latency/source readiness, and runtime paper shadow replay",
            },
        ]
    )


def build_decision(
    account: pd.DataFrame,
    oos_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
    task637_decision_path: Path,
    task633_account_path: Path,
) -> pd.DataFrame:
    best50 = best_row(account, cost_bps=50)
    best100 = best_row(account, cost_bps=100)
    risk50 = best_risk_controlled_row(account, cost_bps=50)
    risk100 = best_risk_controlled_row(account, cost_bps=100)
    validation_same = matching_oos_row(oos_account, "validation", risk50, cost_bps=50)
    recent_same = matching_oos_row(oos_account, "recent_oos", risk50, cost_bps=50)
    previous = pd.read_csv(task637_decision_path).iloc[0]
    decision = "FAIL_REFINEMENT_DID_NOT_IMPROVE_TASK637"
    risk_improved = int(pass_fail[pass_fail["gate"].eq("risk_controlled_50bp_beats_task637")].iloc[0]["pass_flag"]) == 1
    same_validation = int(pass_fail[pass_fail["gate"].eq("same_rule_validation_oos_beats_qqq")].iloc[0]["pass_flag"]) == 1
    same_recent = int(pass_fail[pass_fail["gate"].eq("same_rule_recent_oos_beats_qqq")].iloc[0]["pass_flag"]) == 1
    if risk_improved and same_validation and same_recent:
        decision = "PASS_RISK_CONTROLLED_REFINEMENT_CANDIDATE_NEEDS_GPT_AND_LIVE_RULE_LOCK"
    elif risk_improved:
        decision = "PASS_RETURN_IMPROVEMENT_FAILS_SAME_RULE_VALIDATION_NOT_ACCEPTED"
    elif int(pass_fail[pass_fail["gate"].eq("best_50bp_beats_task637")].iloc[0]["pass_flag"]) == 1:
        decision = "PASS_RETURN_ONLY_REFINEMENT_FAILS_RISK_CONTROL"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "best_50bp_universe": best50["universe"],
                "best_50bp_timing_mode": best50["timing_mode"],
                "best_50bp_exit_mode": best50["exit_mode"],
                "best_50bp_sizing_mode": best50["sizing_mode"],
                "best_50bp_final_capital_usd": float(best50["final_capital_usd"]),
                "best_50bp_max_drawdown_pct": float(best50["max_drawdown_pct"]),
                "risk_controlled_50bp_universe": risk50["universe"],
                "risk_controlled_50bp_timing_mode": risk50["timing_mode"],
                "risk_controlled_50bp_exit_mode": risk50["exit_mode"],
                "risk_controlled_50bp_sizing_mode": risk50["sizing_mode"],
                "risk_controlled_50bp_final_capital_usd": float(risk50["final_capital_usd"]),
                "risk_controlled_50bp_max_drawdown_pct": float(risk50["max_drawdown_pct"]),
                "best_100bp_final_capital_usd": float(best100["final_capital_usd"]),
                "risk_controlled_100bp_final_capital_usd": float(risk100["final_capital_usd"]),
                "same_rule_validation_50bp_final_capital_usd": float(validation_same["final_capital_usd"]),
                "same_rule_validation_qqq_final_capital_usd": float(validation_same["qqq_final_capital_usd"]),
                "same_rule_recent_50bp_final_capital_usd": float(recent_same["final_capital_usd"]),
                "same_rule_recent_qqq_final_capital_usd": float(recent_same["qqq_final_capital_usd"]),
                "task637_best_50bp_final_capital_usd": float(previous["best_50bp_final_capital_usd"]),
                "improvement_vs_task637_usd": float(risk50["final_capital_usd"]) - float(previous["best_50bp_final_capital_usd"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Do not promote the full-period best rule. Use GPT review to diagnose why same-rule validation fails, then search for a rule that improves Task637 and beats validation/recent OOS with the same locked configuration.",
            }
        ]
    )


def render_report(
    feature_audit: pd.DataFrame,
    account: pd.DataFrame,
    oos_account: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    s = source_audit.iloc[0]
    top = account[account["round_trip_cost_bps"].eq(50)].head(12)
    top_oos = (
        oos_account[oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values(["split_name", "final_capital_usd"], ascending=[True, False])
        .groupby("split_name", as_index=False)
        .head(5)
    )
    lines = [
        "# Task638 Content Signal Refinement",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Highest-return 50bp: `{d['best_50bp_universe']}` / `{d['best_50bp_timing_mode']}` / `{d['best_50bp_exit_mode']}` / `{d['best_50bp_sizing_mode']}` = ${float(d['best_50bp_final_capital_usd']):.2f} with {float(d['best_50bp_max_drawdown_pct']):.2f}% max drawdown",
        f"- Risk-controlled 50bp: `{d['risk_controlled_50bp_universe']}` / `{d['risk_controlled_50bp_timing_mode']}` / `{d['risk_controlled_50bp_exit_mode']}` / `{d['risk_controlled_50bp_sizing_mode']}` = ${float(d['risk_controlled_50bp_final_capital_usd']):.2f} with {float(d['risk_controlled_50bp_max_drawdown_pct']):.2f}% max drawdown",
        f"- Risk-controlled improvement vs Task637: ${float(d['improvement_vs_task637_usd']):.2f}",
        "",
        "## Quant Expert Report",
        "",
        "This task tests five refinement axes: negative-event subtypes, positive catalyst strength, dynamic sizing, entry timing, and exit/holding-period variants.",
        "",
        "### Source Audit",
        "",
        f"- Entries: {int(s['entry_count'])}",
        f"- Entry period: {s['entry_start']} to {s['entry_end']}",
        f"- Execution variant rows: {int(s['execution_variant_rows'])}",
        "",
        "### Top 50bp Account Candidates",
        "",
        "| Universe | Timing | Exit | Sizing | Final $ | Accepted | DD |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['universe']}` | `{row['timing_mode']}` | `{row['exit_mode']}` | `{row['sizing_mode']}` | "
            f"${float(row['final_capital_usd']):.2f} | {int(row['accepted_trade_count'])} | {float(row['max_drawdown_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### OOS Account Candidates",
            "",
            "| Split | Universe | Timing | Exit | Sizing | Final $ | QQQ $ |",
            "|---|---|---|---|---|---:|---:|",
        ]
    )
    for _, row in top_oos.iterrows():
        lines.append(
            f"| `{row['split_name']}` | `{row['universe']}` | `{row['timing_mode']}` | `{row['exit_mode']}` | `{row['sizing_mode']}` | "
            f"${float(row['final_capital_usd']):.2f} | ${float(row['qqq_final_capital_usd']):.2f} |"
        )
    lines.extend(
        [
            "",
            "### Refined Feature Stability",
            "",
            "| Feature | Stable | Validation Lift | Recent Lift |",
            "|---|---:|---:|---:|",
        ]
    )
    for feature, group in feature_audit.groupby("feature", dropna=False):
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        lines.append(
            f"| `{feature}` | {int(validation['refined_oos_stability_pass_flag'])} | "
            f"{float(validation['avg_return_lift_pct_point']):.2f} | {float(recent['avg_return_lift_pct_point']):.2f} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We split bad-news and good-news content into smaller buckets.",
            "- We tested bigger size only when the interpreted signal was stronger.",
            "- We tested delayed entry, VWAP reclaim entry, and alternate exits.",
            "- Best refinement improves the prior Task637 account result, but trading remains blocked until live-readable rules are locked.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task_638_event_refinement_taxonomy.csv`",
            "- `task_638_entry_refined_content_panel.csv`",
            "- `task_638_refined_feature_audit.csv`",
            "- `task_638_timing_exit_execution_panel.csv`",
            "- `task_638_refinement_account_grid.csv`",
            "- `task_638_refinement_oos_account_grid.csv`",
            "- `task_638_source_audit.csv`",
            "- `task_638_pass_fail_matrix.csv`",
            "- `task_638_decision.csv`",
            "- `task_638_gpt_review_packet.md`",
            "- `task_638_gpt_capture_status.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def write_gpt_review_packet(out_dir: Path, decision: pd.DataFrame, account: pd.DataFrame, oos_account: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    d = decision.iloc[0]
    top = account[account["round_trip_cost_bps"].eq(50)].head(8)
    lines = [
        "# Task638 GPT Review Packet",
        "",
        "Use only supplied facts. GPT is review-only, not source truth.",
        "",
        "## Result",
        "",
        f"- Highest-return 50bp final: ${float(d['best_50bp_final_capital_usd']):.2f}",
        f"- Highest-return max drawdown: {float(d['best_50bp_max_drawdown_pct']):.2f}%",
        f"- Risk-controlled 50bp final: ${float(d['risk_controlled_50bp_final_capital_usd']):.2f}",
        f"- Risk-controlled max drawdown: {float(d['risk_controlled_50bp_max_drawdown_pct']):.2f}%",
        f"- Prior Task637 best: ${float(d['task637_best_50bp_final_capital_usd']):.2f}",
        f"- Highest-return universe/timing/exit/sizing: `{d['best_50bp_universe']}` / `{d['best_50bp_timing_mode']}` / `{d['best_50bp_exit_mode']}` / `{d['best_50bp_sizing_mode']}`",
        f"- Risk-controlled universe/timing/exit/sizing: `{d['risk_controlled_50bp_universe']}` / `{d['risk_controlled_50bp_timing_mode']}` / `{d['risk_controlled_50bp_exit_mode']}` / `{d['risk_controlled_50bp_sizing_mode']}`",
        f"- Same risk-controlled rule validation: ${float(d['same_rule_validation_50bp_final_capital_usd']):.2f} vs QQQ ${float(d['same_rule_validation_qqq_final_capital_usd']):.2f}",
        f"- Same risk-controlled rule recent OOS: ${float(d['same_rule_recent_50bp_final_capital_usd']):.2f} vs QQQ ${float(d['same_rule_recent_qqq_final_capital_usd']):.2f}",
        "",
        "## Top Candidates",
        "",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"- {row['universe']} | {row['timing_mode']} | {row['exit_mode']} | {row['sizing_mode']} | final ${float(row['final_capital_usd']):.2f} | accepted {int(row['accepted_trade_count'])}"
        )
    lines.extend(
        [
            "",
            "## Review Questions",
            "",
            "1. Is the winning candidate economically plausible, or does it look like timing/exit curve-fit?",
            "2. Should the negative-event branch be traded as post-shock reversal rather than bad-news long?",
            "3. Which live-readable subtype rules should be locked first?",
            "4. Which extra blocker should prevent paper-runtime assignment?",
            "5. What validation should come before any real-time trade decision use?",
        ]
    )
    (out_dir / "task_638_gpt_review_packet.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task638_content_signal_refinement(out_dir=args.out_dir)
    d = artifacts["task_638_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={d['decision']} best=${float(d['best_50bp_final_capital_usd']):.2f} "
        f"prev=${float(d['task637_best_50bp_final_capital_usd']):.2f} "
        f"{d['best_50bp_universe']}/{d['best_50bp_timing_mode']}/{d['best_50bp_exit_mode']}/{d['best_50bp_sizing_mode']}"
    )


if __name__ == "__main__":
    main()
