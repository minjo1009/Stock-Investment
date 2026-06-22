from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task638_content_signal_refinement import (
    DAILY_DIRS,
    INTRADAY_DIR,
    QQQ_PATH,
    costed,
    exit_for,
    load_daily_maps,
    load_intraday,
    simulate_account,
)
from src.backtest.build_task640_leverage_etf_drawdown_upgrade import (
    ROUND_TRIP_COST_BPS,
    load_execution_panel,
    select_task639_base_panel,
)


TASK_ID = "Task643"
REPORT_DIR = Path("docs/reports/task_643_entry_risk_tier_turnover_backtest")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
TASK642_QUEUE = Path("docs/reports/task_642_priority_solution_design/task_642_solution_queue.csv")

ENTRY_POLICIES = ("base_delay1d_open", "vwap_rs_confirm_60m", "vwap_or_volume_confirm_60m", "strict_or_vwap_rs_volume_60m")
SIZING_POLICIES = ("equal_max5", "atr_bucket", "signal_tier", "atr_signal_tier")
EXIT_POLICIES = ("existing_exit", "hold20", "trail10_hold20", "strength_hold20_trail10")


def build_task643_entry_risk_tier_turnover_backtest(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    task642_queue_path: Path = TASK642_QUEUE,
    intraday_dir: Path = INTRADAY_DIR,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    raw_panel = load_execution_panel(execution_panel_path)
    task639_base = select_task639_base_panel(raw_panel)
    task639_decision = pd.read_csv(task639_decision_path).iloc[0]
    task642_queue = pd.read_csv(task642_queue_path)
    symbols = sorted(set(task639_base["symbol"].astype(str).str.upper()) | {"QQQ"})
    daily_maps = load_daily_maps(symbols)
    qqq_intraday = load_intraday("QQQ", intraday_dir, {})
    enriched = add_risk_features(task639_base, daily_maps)
    entry_panel = build_entry_policy_panel(enriched, intraday_dir, qqq_intraday, daily_maps)
    execution_panel = build_exit_policy_panel(entry_panel, daily_maps)
    account_grid = build_account_grid(execution_panel, qqq_path)
    oos_grid = build_oos_grid(execution_panel, qqq_path)
    source_audit = build_source_audit(enriched, entry_panel, execution_panel, task642_queue)
    pass_fail = build_pass_fail(account_grid, oos_grid, source_audit, task639_decision)
    decision = build_decision(account_grid, oos_grid, pass_fail, task639_decision)

    out_dir.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out_dir / "task_643_task639_risk_feature_panel.csv", index=False)
    entry_panel.to_csv(out_dir / "task_643_entry_quality_panel.csv", index=False)
    execution_panel.to_csv(out_dir / "task_643_execution_variant_panel.csv", index=False)
    account_grid.to_csv(out_dir / "task_643_account_grid.csv", index=False)
    oos_grid.to_csv(out_dir / "task_643_oos_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_643_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_643_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_643_decision.csv", index=False)
    (out_dir / "task_643_entry_risk_tier_turnover_backtest.md").write_text(
        render_report(account_grid, oos_grid, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_643_task639_risk_feature_panel": enriched,
        "task_643_entry_quality_panel": entry_panel,
        "task_643_execution_variant_panel": execution_panel,
        "task_643_account_grid": account_grid,
        "task_643_oos_grid": oos_grid,
        "task_643_source_audit": source_audit,
        "task_643_pass_fail_matrix": pass_fail,
        "task_643_decision": decision,
    }


def add_risk_features(panel: pd.DataFrame, daily_maps: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in panel.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        daily = daily_maps.get(symbol)
        entry_ts = pd.Timestamp(row["entry_ts"])
        out = dict(row)
        out.update({"atr20_pct": float("nan"), "gap_pct": float("nan"), "volatility_bucket": "unknown"})
        if daily is not None and not daily.empty:
            entry_date = entry_ts.tz_convert("America/New_York").date()
            prior = daily[daily["trade_date"].lt(entry_date)].tail(21).copy()
            current = daily[daily["trade_date"].eq(entry_date)].head(1)
            if len(prior) >= 5:
                prev_close = prior["close"].shift(1)
                tr = pd.concat(
                    [
                        (prior["high"] - prior["low"]).abs(),
                        (prior["high"] - prev_close).abs(),
                        (prior["low"] - prev_close).abs(),
                    ],
                    axis=1,
                ).max(axis=1)
                atr_pct = float((tr / prior["close"].replace(0, pd.NA)).tail(20).mean())
                out["atr20_pct"] = atr_pct
                if atr_pct >= 0.07:
                    out["volatility_bucket"] = "high_atr"
                elif atr_pct >= 0.04:
                    out["volatility_bucket"] = "mid_atr"
                else:
                    out["volatility_bucket"] = "low_atr"
            if not current.empty and len(prior) >= 1:
                out["gap_pct"] = float(float(current.iloc[0]["open"]) / max(float(prior.iloc[-1]["close"]), 1e-9) - 1.0)
        contract = float(row.get("positive_contract_customer_count", 0) or 0) > 0
        supply = float(row.get("content_supply_demand_flag", 0) or 0) == 1
        if contract and supply:
            out["signal_tier"] = "both_contract_and_supply"
        elif contract:
            out["signal_tier"] = "contract_only"
        else:
            out["signal_tier"] = "supply_only"
        rows.append(out)
    return pd.DataFrame(rows)


def build_entry_policy_panel(
    panel: pd.DataFrame,
    intraday_dir: Path,
    qqq_intraday: pd.DataFrame,
    daily_maps: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    intraday_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, object]] = []
    for row in panel.to_dict(orient="records"):
        rows.append(base_entry_row(row))
        for policy in ENTRY_POLICIES:
            if policy == "base_delay1d_open":
                continue
            confirmed = confirmed_entry_row(row, policy, intraday_dir, intraday_cache, qqq_intraday, daily_maps)
            if confirmed is not None:
                rows.append(confirmed)
    return pd.DataFrame(rows)


def base_entry_row(row: dict[str, object]) -> dict[str, object]:
    out = dict(row)
    out.update(
        {
            "entry_policy": "base_delay1d_open",
            "entry_quality_confirmed_flag": 1,
            "entry_quality_reason": "task639_delay1d_open",
            "entry_quality_source_available_flag": 1,
        }
    )
    return out


def confirmed_entry_row(
    row: dict[str, object],
    policy: str,
    intraday_dir: Path,
    intraday_cache: dict[str, pd.DataFrame],
    qqq_intraday: pd.DataFrame,
    daily_maps: dict[str, pd.DataFrame],
) -> dict[str, object] | None:
    symbol = str(row["symbol"]).upper()
    intraday = load_intraday(symbol, intraday_dir, intraday_cache)
    if intraday.empty or qqq_intraday.empty:
        return None
    entry_ts = pd.Timestamp(row["entry_ts"])
    ny_date = entry_ts.tz_convert("America/New_York").date()
    same = intraday[intraday["ny_date"].eq(ny_date)].copy()
    qqq_same = qqq_intraday[qqq_intraday["ny_date"].eq(ny_date)].copy()
    if len(same) < 5 or len(qqq_same) < 5:
        return None
    same = same.sort_values("timestamp").reset_index(drop=True)
    qqq_same = qqq_same.sort_values("timestamp").reset_index(drop=True)
    open_price = float(same.iloc[0]["open"])
    qqq_open = float(qqq_same.iloc[0]["open"])
    opening_60m = same.head(4)
    opening_30m = same.head(2)
    target_rows = same[same["timestamp"].ge(entry_ts + pd.Timedelta(minutes=60))]
    if target_rows.empty:
        return None
    r = target_rows.iloc[0]
    qqq_hit = qqq_same[qqq_same["timestamp"].ge(pd.Timestamp(r["timestamp"]))].head(1)
    if qqq_hit.empty:
        return None
    close = float(r["close"])
    qqq_close = float(qqq_hit.iloc[0]["close"])
    stock_ret = close / max(open_price, 1e-9) - 1.0
    qqq_ret = qqq_close / max(qqq_open, 1e-9) - 1.0
    above_vwap = close >= float(r.get("session_vwap") or r["vwap"] or close)
    above_or30 = close >= float(opening_30m["high"].max())
    above_or60 = close >= float(opening_60m["high"].max())
    rs_ok = stock_ret >= qqq_ret
    volume_ok = bool(float(row.get("volume_ratio_prev", 1.0) or 1.0) >= 1.0 or opening_60m["volume"].sum() >= same["volume"].median() * 4)
    if policy == "vwap_rs_confirm_60m":
        ok = above_vwap and rs_ok
    elif policy == "vwap_or_volume_confirm_60m":
        ok = above_vwap and above_or30 and volume_ok
    else:
        ok = above_vwap and above_or60 and rs_ok and volume_ok
    if not ok:
        return None
    out = dict(row)
    out.update(
        {
            "entry_policy": policy,
            "entry_quality_confirmed_flag": 1,
            "entry_quality_reason": f"above_vwap={int(above_vwap)};above_or30={int(above_or30)};above_or60={int(above_or60)};rs={int(rs_ok)};volume={int(volume_ok)}",
            "entry_quality_source_available_flag": 1,
            "entry_ts": pd.Timestamp(r["timestamp"]),
            "entry_price": close,
            "entry_vs_qqq_ret_60m": stock_ret - qqq_ret,
        }
    )
    return out


def build_exit_policy_panel(entry_panel: pd.DataFrame, daily_maps: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in entry_panel.to_dict(orient="records"):
        for exit_policy in EXIT_POLICIES:
            exit_info = exit_for(row, exit_policy, pd.Timestamp(row["entry_ts"]), float(row["entry_price"]), daily_maps)
            if exit_info is None:
                continue
            exit_ts, exit_price, exit_reason = exit_info
            if pd.Timestamp(exit_ts) <= pd.Timestamp(row["entry_ts"]):
                continue
            ret = float(exit_price) / max(float(row["entry_price"]), 1e-9) - 1.0
            out = dict(row)
            out.update(
                {
                    "exit_policy": exit_policy,
                    "simulated_exit_ts": pd.Timestamp(exit_ts),
                    "simulated_exit_price": float(exit_price),
                    "exit_reason": exit_reason,
                    "net_return_from_entry": ret,
                    "return_pct": ret * 100.0,
                    "entry_reduce_eval_flag": int(ret <= -0.03),
                }
            )
            rows.append(out)
    return pd.DataFrame(rows)


def build_account_grid(execution_panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    qqq = load_qqq_history(qqq_path)
    for entry_policy in ENTRY_POLICIES:
        entry_selected = execution_panel[execution_panel["entry_policy"].eq(entry_policy)].copy()
        if entry_selected.empty:
            continue
        for exit_policy in EXIT_POLICIES:
            selected = entry_selected[entry_selected["exit_policy"].eq(exit_policy)].copy()
            if selected.empty:
                continue
            for sizing_policy in SIZING_POLICIES:
                metrics, accepted = run_account(selected, sizing_policy)
                qqq_final = qqq_final_for_period(qqq, selected)
                rows.append(account_row("all", entry_policy, exit_policy, sizing_policy, selected, accepted, metrics, qqq_final))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_oos_grid(execution_panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    qqq = load_qqq_history(qqq_path)
    for split_name in ["validation", "recent_oos"]:
        split_panel = execution_panel[execution_panel["split_name"].astype(str).eq(split_name)].copy()
        for entry_policy in ENTRY_POLICIES:
            entry_selected = split_panel[split_panel["entry_policy"].eq(entry_policy)].copy()
            if entry_selected.empty:
                continue
            for exit_policy in EXIT_POLICIES:
                selected = entry_selected[entry_selected["exit_policy"].eq(exit_policy)].copy()
                if selected.empty:
                    continue
                for sizing_policy in SIZING_POLICIES:
                    metrics, accepted = run_account(selected, sizing_policy)
                    qqq_final = qqq_final_for_period(qqq, selected)
                    rows.append(account_row(split_name, entry_policy, exit_policy, sizing_policy, selected, accepted, metrics, qqq_final))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def run_account(panel: pd.DataFrame, sizing_policy: str) -> tuple[dict[str, object], pd.DataFrame]:
    test_panel = costed(panel, ROUND_TRIP_COST_BPS)
    if sizing_policy == "equal_max5":
        quality, accepted = simulate_account(test_panel, "equal_max5")
        return normalize_quality(quality), accepted
    return simulate_weighted_account(test_panel, sizing_policy)


def simulate_weighted_account(panel: pd.DataFrame, sizing_policy: str) -> tuple[dict[str, object], pd.DataFrame]:
    ordered = panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    cash = 1.0
    peak = 1.0
    max_dd = 0.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []

    def equity() -> float:
        return cash + sum(float(pos["capital"]) for pos in open_positions)

    def close_until(ts: pd.Timestamp) -> None:
        nonlocal cash, peak, max_dd, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= ts:
                cash += float(pos["capital"]) * (1.0 + float(pos["return"]))
                eq = equity()
                peak = max(peak, eq)
                max_dd = min(max_dd, (eq / max(peak, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_until(entry_ts)
        if len(open_positions) >= 5:
            continue
        eq = equity()
        weight = position_weight(row, sizing_policy)
        capital = min(cash, eq * weight)
        if capital <= 0:
            continue
        cash -= capital
        open_positions.append({"lifecycle_id": row["lifecycle_id"], "exit_ts": row["simulated_exit_ts"], "capital": capital, "return": row["net_return_from_entry"]})
        out = dict(row)
        out["position_weight"] = capital / max(eq, 1e-9)
        accepted_rows.append(out)
    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    if accepted.empty:
        return empty_quality(), accepted
    returns = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce")
    return {
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": float(INITIAL_CAPITAL_USD * cash),
        "capital_return_pct": float((cash - 1.0) * 100.0),
        "avg_net_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "max_drawdown_pct": float(max_dd),
    }, accepted


def position_weight(row: dict[str, object], sizing_policy: str) -> float:
    base = 0.20
    atr = float(row.get("atr20_pct", 0.05) or 0.05)
    gap = abs(float(row.get("gap_pct", 0.0) or 0.0))
    tier = str(row.get("signal_tier", "supply_only"))
    if sizing_policy in {"atr_bucket", "atr_signal_tier"}:
        if atr >= 0.07 or gap >= 0.08:
            base = 0.10
        elif atr >= 0.04 or gap >= 0.04:
            base = 0.15
        else:
            base = 0.22
    if sizing_policy in {"signal_tier", "atr_signal_tier"}:
        if tier == "both_contract_and_supply":
            base *= 1.10
        elif tier == "contract_only":
            base *= 1.00
        else:
            base *= 0.80
    return float(max(0.08, min(0.30, base)))


def normalize_quality(quality: dict[str, object]) -> dict[str, object]:
    return {
        "accepted_trade_count": int(quality.get("lifecycle_count", 0)),
        "final_capital_usd": float(INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)),
        "capital_return_pct": float(quality["capital_pnl_pct"]),
        "avg_net_return_pct": float(quality["avg_net_return_pct"]),
        "win_rate": float(quality["win_rate"]),
        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
    }


def empty_quality() -> dict[str, object]:
    return {
        "accepted_trade_count": 0,
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "capital_return_pct": 0.0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "max_drawdown_pct": 0.0,
    }


def account_row(
    split_name: str,
    entry_policy: str,
    exit_policy: str,
    sizing_policy: str,
    selected: pd.DataFrame,
    accepted: pd.DataFrame,
    metrics: dict[str, object],
    qqq_final: float,
) -> dict[str, object]:
    final = float(metrics["final_capital_usd"])
    return {
        "split_name": split_name,
        "entry_policy": entry_policy,
        "exit_policy": exit_policy,
        "sizing_policy": sizing_policy,
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "source_trade_count": int(len(selected)),
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": final,
        "capital_return_pct": float(metrics["capital_return_pct"]),
        "avg_net_return_pct": float(metrics["avg_net_return_pct"]),
        "win_rate": float(metrics["win_rate"]),
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
        "qqq_final_capital_usd": float(qqq_final),
        "beats_qqq_flag": int(final > qqq_final),
        "label_used_in_assignment_flag": 0,
        "presence_field_used_for_assignment_flag": 0,
    }


def build_source_audit(
    enriched: pd.DataFrame,
    entry_panel: pd.DataFrame,
    execution_panel: pd.DataFrame,
    task642_queue: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "task642_queue_rows": int(len(task642_queue)),
                "task639_source_trade_count": int(len(enriched)),
                "entry_policy_variant_rows": int(len(entry_panel)),
                "execution_variant_rows": int(len(execution_panel)),
                "entry_quality_source_available_rate": float(entry_panel["entry_quality_source_available_flag"].mean()) if not entry_panel.empty else 0.0,
                "atr20_available_rate": float(pd.to_numeric(enriched["atr20_pct"], errors="coerce").notna().mean()) if not enriched.empty else 0.0,
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "symbol_blacklist_used_flag": 0,
                "theme_blacklist_used_flag": 0,
            }
        ]
    )


def build_pass_fail(
    account_grid: pd.DataFrame,
    oos_grid: pd.DataFrame,
    source_audit: pd.DataFrame,
    task639: pd.Series,
) -> pd.DataFrame:
    best = account_grid.iloc[0]
    base_final = float(task639["best_50bp_final_capital_usd"])
    base_dd = float(task639["best_50bp_max_drawdown_pct"])
    validation_best = matching_oos(oos_grid, best, "validation")
    recent_best = matching_oos(oos_grid, best, "recent_oos")
    same_rule_oos_pass = int(
        not validation_best.empty
        and not recent_best.empty
        and float(validation_best.iloc[0]["final_capital_usd"]) > float(validation_best.iloc[0]["qqq_final_capital_usd"])
        and float(recent_best.iloc[0]["final_capital_usd"]) > float(recent_best.iloc[0]["qqq_final_capital_usd"])
    )
    return pd.DataFrame(
        [
            {
                "gate": "source_features_available",
                "pass_flag": int(float(source_audit.iloc[0]["atr20_available_rate"]) >= 0.95 and float(source_audit.iloc[0]["entry_quality_source_available_rate"]) > 0.0),
                "observed_value": f"atr={float(source_audit.iloc[0]['atr20_available_rate']):.2%}; entry_variants={int(source_audit.iloc[0]['entry_policy_variant_rows'])}",
                "required_value": "ATR risk and entry quality variant data must exist",
            },
            {
                "gate": "best_candidate_beats_task639_return",
                "pass_flag": int(float(best["final_capital_usd"]) > base_final),
                "observed_value": f"best=${float(best['final_capital_usd']):.2f}; task639=${base_final:.2f}",
                "required_value": "full-period final capital above Task639",
            },
            {
                "gate": "best_candidate_reduces_task639_drawdown",
                "pass_flag": int(float(best["max_drawdown_pct"]) > base_dd),
                "observed_value": f"best_dd={float(best['max_drawdown_pct']):.2f}%; task639_dd={base_dd:.2f}%",
                "required_value": "max drawdown less severe than Task639",
            },
            {
                "gate": "same_config_validation_and_recent_beat_qqq",
                "pass_flag": same_rule_oos_pass,
                "observed_value": oos_observed(validation_best, recent_best),
                "required_value": "same config must beat QQQ in validation and recent OOS",
            },
            {
                "gate": "no_blacklist_or_label_shortcut",
                "pass_flag": 1,
                "observed_value": "symbol_blacklist=0; theme_blacklist=0; label_assignment=0",
                "required_value": "no blacklists or after-the-fact labels",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research backtest only",
                "required_value": "requires live-readable rule lock, latency audit, paper-shadow replay, and source readiness",
            },
        ]
    )


def matching_oos(oos_grid: pd.DataFrame, best: pd.Series, split_name: str) -> pd.DataFrame:
    return oos_grid[
        oos_grid["split_name"].eq(split_name)
        & oos_grid["entry_policy"].eq(best["entry_policy"])
        & oos_grid["exit_policy"].eq(best["exit_policy"])
        & oos_grid["sizing_policy"].eq(best["sizing_policy"])
    ].copy()


def oos_observed(validation: pd.DataFrame, recent: pd.DataFrame) -> str:
    if validation.empty or recent.empty:
        return "missing matching OOS rows"
    v = validation.iloc[0]
    r = recent.iloc[0]
    return f"validation=${float(v['final_capital_usd']):.2f}/QQQ ${float(v['qqq_final_capital_usd']):.2f}; recent=${float(r['final_capital_usd']):.2f}/QQQ ${float(r['qqq_final_capital_usd']):.2f}"


def build_decision(account_grid: pd.DataFrame, oos_grid: pd.DataFrame, pass_fail: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    best = account_grid.iloc[0]
    validation_best = matching_oos(oos_grid, best, "validation")
    recent_best = matching_oos(oos_grid, best, "recent_oos")
    pass_map = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
    candidate_pass = int(
        pass_map["best_candidate_beats_task639_return"] == 1
        and pass_map["best_candidate_reduces_task639_drawdown"] == 1
        and pass_map["same_config_validation_and_recent_beat_qqq"] == 1
    )
    return pd.DataFrame(
        [
            {
                "decision": "PASS_ENTRY_RISK_TIER_TURNOVER_CANDIDATE_NOT_ACCEPTED" if candidate_pass else "FAIL_NO_FULL_GATE_ENTRY_RISK_TIER_TURNOVER_CANDIDATE",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "best_entry_policy": str(best["entry_policy"]),
                "best_exit_policy": str(best["exit_policy"]),
                "best_sizing_policy": str(best["sizing_policy"]),
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "task639_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "best_validation_final_capital_usd": 0.0 if validation_best.empty else float(validation_best.iloc[0]["final_capital_usd"]),
                "best_validation_qqq_final_capital_usd": 0.0 if validation_best.empty else float(validation_best.iloc[0]["qqq_final_capital_usd"]),
                "best_recent_final_capital_usd": 0.0 if recent_best.empty else float(recent_best.iloc[0]["final_capital_usd"]),
                "best_recent_qqq_final_capital_usd": 0.0 if recent_best.empty else float(recent_best.iloc[0]["qqq_final_capital_usd"]),
                "next_action": "If pass, run rule-lock robustness and source-latency/paper-shadow gates; if fail, inspect which of A/B/C/D hurt OOS and split tests further.",
            }
        ]
    )


def render_report(
    account_grid: pd.DataFrame,
    oos_grid: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    dec = decision.iloc[0]
    return "\n".join(
        [
            "# Task643 Entry Risk Tier Turnover Backtest",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Best config: `{dec['best_entry_policy']}` / `{dec['best_exit_policy']}` / `{dec['best_sizing_policy']}`",
            f"- Best $1000 final: ${float(dec['best_final_capital_usd']):.2f}",
            f"- Best max drawdown: {float(dec['best_max_drawdown_pct']):.2f}%",
            f"- Task639 baseline: ${float(dec['task639_final_capital_usd']):.2f}, DD {float(dec['task639_max_drawdown_pct']):.2f}%",
            "",
            "## Quant Expert Report",
            "",
            "Task643 tests the Task642 solution order: entry quality confirmation, volatility-aware sizing, signal tier sizing, and exit/capital recycling. The Task639 content signal is kept fixed.",
            "",
            "### Source Audit",
            "",
            table(source_audit),
            "",
            "### Top Full-Period Candidates",
            "",
            table(account_grid.head(20)),
            "",
            "### Matching OOS Grid",
            "",
            table(oos_grid.head(40)),
            "",
            "### Pass/Fail Matrix",
            "",
            table(pass_fail),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We tested the planned fixes without using symbol blacklists or loss labels.",
            "- A candidate must beat Task639 return, reduce drawdown, and also beat QQQ in validation and recent OOS with the same config.",
            "- Even if a candidate passes research gates, real trading remains forbidden until live source and paper-shadow gates pass.",
            "",
            "## Artifact Manifest",
            "",
            "- `task_643_task639_risk_feature_panel.csv`",
            "- `task_643_entry_quality_panel.csv`",
            "- `task_643_execution_variant_panel.csv`",
            "- `task_643_account_grid.csv`",
            "- `task_643_oos_grid.csv`",
            "- `task_643_source_audit.csv`",
            "- `task_643_pass_fail_matrix.csv`",
            "- `task_643_decision.csv`",
            "- `task_643_gpt_review_packet.txt`",
            "- `task_643_gpt_review_response.md`",
            "- `artifact_manifest.csv`",
            "",
        ]
    )


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    safe = frame.copy().where(pd.notna(frame), "")
    columns = [str(column) for column in safe.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in safe.astype(str).to_dict(orient="records"):
        lines.append("| " + " | ".join(row[column] for column in safe.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task643_entry_risk_tier_turnover_backtest(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
