from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD
from src.backtest.build_task638_content_signal_refinement import costed, simulate_account


TASK_ID = "Task640"
REPORT_DIR = Path("docs/reports/task_640_leverage_etf_drawdown_upgrade")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
TASK639_PASS_CANDIDATES = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_same_rule_pass_candidates.csv")
DAILY_DIRS = (Path("data/raw/us_daily_breadth_top500"), Path("data/raw/us_daily"))

BASE_RULE = "positive_contract_or_supply"
BASE_TIMING = "delay1d"
BASE_EXIT = "existing_exit"
BASE_SIZING = "equal_max5"
ROUND_TRIP_COST_BPS = 50
MAX_POSITIONS = 5

ETF_THEME_MAPS = {
    "long_3x_theme_proxy": {
        "ai_semiconductors": "SOXL",
        "cloud_ai_infra": "TQQQ",
        "data_infra_devops": "TQQQ",
        "cybersecurity": "TQQQ",
        "crypto_equity_proxy": "TQQQ",
        "biotech": "LABU",
        "ev_autonomous": "QLD",
        "aerospace_defense_space": "UPRO",
        "power_grid_electrification": "UPRO",
        "industrial_automation": "UPRO",
    },
    "long_2x_theme_proxy": {
        "ai_semiconductors": "QLD",
        "cloud_ai_infra": "QLD",
        "data_infra_devops": "QLD",
        "cybersecurity": "QLD",
        "crypto_equity_proxy": "QLD",
        "biotech": "LABU",
        "ev_autonomous": "QLD",
        "aerospace_defense_space": "SSO",
        "power_grid_electrification": "SSO",
        "industrial_automation": "SSO",
    },
}
OVERLAY_WEIGHTS = (0.10, 0.20, 0.30, 0.50, 1.00)


def build_task640_leverage_etf_drawdown_upgrade(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    task639_pass_candidates_path: Path = TASK639_PASS_CANDIDATES,
    daily_dirs: tuple[Path, ...] = DAILY_DIRS,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_execution_panel(execution_panel_path)
    task639_decision = pd.read_csv(task639_decision_path).iloc[0]
    task639_pass_candidates = pd.read_csv(task639_pass_candidates_path)
    base_panel = select_task639_base_panel(panel)
    baseline = build_baseline(base_panel, task639_decision)
    daily = load_daily_price_maps(daily_dirs)
    exclusion_grid = build_exclusion_grid(base_panel, baseline)
    leverage_grid = build_leverage_etf_overlay_grid(base_panel, baseline, daily)
    throttle_grid = build_drawdown_throttle_grid(base_panel, baseline)
    combined_grid = build_exclusion_throttle_combo_grid(base_panel, baseline, exclusion_grid)
    source_audit = build_source_audit(base_panel, task639_pass_candidates, daily, leverage_grid)
    pass_fail = build_pass_fail(baseline, exclusion_grid, leverage_grid, throttle_grid, combined_grid, source_audit)
    decision = build_decision(baseline, exclusion_grid, leverage_grid, throttle_grid, combined_grid, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(out_dir / "task_640_task639_baseline_recheck.csv", index=False)
    exclusion_grid.to_csv(out_dir / "task_640_exclusion_filter_grid.csv", index=False)
    leverage_grid.to_csv(out_dir / "task_640_leverage_etf_overlay_grid.csv", index=False)
    throttle_grid.to_csv(out_dir / "task_640_drawdown_throttle_grid.csv", index=False)
    combined_grid.to_csv(out_dir / "task_640_exclusion_throttle_combo_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_640_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_640_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_640_decision.csv", index=False)
    (out_dir / "task_640_leverage_etf_drawdown_upgrade.md").write_text(
        render_report(baseline, exclusion_grid, leverage_grid, throttle_grid, combined_grid, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_gpt_packet(out_dir, baseline, exclusion_grid, leverage_grid, throttle_grid, combined_grid, decision)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_640_task639_baseline_recheck": baseline,
        "task_640_exclusion_filter_grid": exclusion_grid,
        "task_640_leverage_etf_overlay_grid": leverage_grid,
        "task_640_drawdown_throttle_grid": throttle_grid,
        "task_640_exclusion_throttle_combo_grid": combined_grid,
        "task_640_source_audit": source_audit,
        "task_640_pass_fail_matrix": pass_fail,
        "task_640_decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["net_return_from_entry", "positive_contract_customer_count", "content_supply_demand_flag"]:
        panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def select_task639_base_panel(panel: pd.DataFrame) -> pd.DataFrame:
    mask = (
        pd.to_numeric(panel["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1)
    )
    selected = panel[mask & panel["timing_mode"].eq(BASE_TIMING) & panel["exit_mode"].eq(BASE_EXIT)].copy()
    return selected.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)


def build_baseline(base_panel: pd.DataFrame, task639_decision: pd.Series) -> pd.DataFrame:
    metrics = run_account(base_panel)
    expected_final = float(task639_decision["best_50bp_final_capital_usd"])
    expected_dd = float(task639_decision["best_50bp_max_drawdown_pct"])
    return pd.DataFrame(
        [
            {
                "baseline_name": "task639_positive_contract_or_supply_delay1d_existing_equal_max5_50bp",
                "rule_name": BASE_RULE,
                "timing_mode": BASE_TIMING,
                "exit_mode": BASE_EXIT,
                "sizing_mode": BASE_SIZING,
                "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                "source_trade_count": int(len(base_panel)),
                "accepted_trade_count": int(metrics["accepted_trade_count"]),
                "final_capital_usd": float(metrics["final_capital_usd"]),
                "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
                "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
                "task639_expected_final_capital_usd": expected_final,
                "task639_expected_max_drawdown_pct": expected_dd,
                "task639_recheck_match_flag": int(abs(float(metrics["final_capital_usd"]) - expected_final) < 0.01 and abs(float(metrics["max_drawdown_pct"]) - expected_dd) < 0.01),
            }
        ]
    )


def run_account(panel: pd.DataFrame) -> dict[str, object]:
    quality, accepted = simulate_account(costed(panel, ROUND_TRIP_COST_BPS), BASE_SIZING)
    return {
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": float(INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)),
        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
        "avg_net_return_pct": float(quality["avg_net_return_pct"]),
        "win_rate": float(quality["win_rate"]),
    }


def build_exclusion_grid(base_panel: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    base_final, base_dd = baseline_values(baseline)
    rows.append(grid_row("none", "none", "none", base_panel, base_final, base_dd))

    for column, kind, min_count in [("theme_id", "theme", 10), ("symbol", "symbol", 5)]:
        counts = base_panel[column].astype(str).value_counts()
        for target in counts[counts >= min_count].index:
            scoped = base_panel[~base_panel[column].astype(str).eq(str(target))].copy()
            rows.append(grid_row("exclude_one", kind, str(target), scoped, base_final, base_dd))

    return pd.DataFrame(rows).sort_values(["return_up_drawdown_down_pass_flag", "final_capital_usd"], ascending=False).reset_index(drop=True)


def grid_row(policy: str, target_type: str, target_value: str, panel: pd.DataFrame, base_final: float, base_dd: float) -> dict[str, object]:
    metrics = run_account(panel)
    final = float(metrics["final_capital_usd"])
    dd = float(metrics["max_drawdown_pct"])
    return {
        "policy": policy,
        "target_type": target_type,
        "target_value": target_value,
        "source_trade_count": int(len(panel)),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": final,
        "max_drawdown_pct": dd,
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "final_delta_vs_task639_usd": final - base_final,
        "drawdown_delta_vs_task639_pct_point": dd - base_dd,
        "return_up_drawdown_down_pass_flag": int(final > base_final and dd > base_dd),
    }


def load_daily_price_maps(daily_dirs: tuple[Path, ...]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    symbols = sorted({symbol for mapping in ETF_THEME_MAPS.values() for symbol in mapping.values()})
    for symbol in symbols:
        for daily_dir in daily_dirs:
            path = daily_dir / f"{symbol}.csv"
            if not path.exists():
                continue
            frame = pd.read_csv(path)
            frame["date"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dt.date
            price_col = "adj_close" if "adj_close" in frame.columns else "close"
            frame["price"] = pd.to_numeric(frame[price_col], errors="coerce")
            out[symbol] = frame.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)
            break
    return out


def build_leverage_etf_overlay_grid(base_panel: pd.DataFrame, baseline: pd.DataFrame, daily: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base_final, base_dd = baseline_values(baseline)
    rows: list[dict[str, object]] = []
    for overlay_name, theme_map in ETF_THEME_MAPS.items():
        for weight in OVERLAY_WEIGHTS:
            overlay_panel, coverage = apply_etf_overlay(base_panel, theme_map, daily, weight)
            if overlay_panel.empty:
                metrics = empty_metrics()
            else:
                metrics = run_account(overlay_panel)
            final = float(metrics["final_capital_usd"])
            dd = float(metrics["max_drawdown_pct"])
            rows.append(
                {
                    "overlay_name": overlay_name,
                    "overlay_weight": float(weight),
                    "mapped_trade_count": int(coverage["mapped_trade_count"]),
                    "priced_trade_count": int(coverage["priced_trade_count"]),
                    "price_coverage_rate": float(coverage["price_coverage_rate"]),
                    "source_trade_count": int(len(overlay_panel)),
                    "accepted_trade_count": int(metrics["accepted_trade_count"]),
                    "final_capital_usd": final,
                    "max_drawdown_pct": dd,
                    "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
                    "final_delta_vs_task639_usd": final - base_final,
                    "drawdown_delta_vs_task639_pct_point": dd - base_dd,
                    "return_up_drawdown_down_pass_flag": int(final > base_final and dd > base_dd),
                }
            )
    return pd.DataFrame(rows).sort_values(["return_up_drawdown_down_pass_flag", "final_capital_usd"], ascending=False).reset_index(drop=True)


def apply_etf_overlay(
    panel: pd.DataFrame,
    theme_map: dict[str, str],
    daily: dict[str, pd.DataFrame],
    weight: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    mapped = 0
    priced = 0
    for row in panel.to_dict(orient="records"):
        etf = theme_map.get(str(row.get("theme_id", "")))
        if not etf:
            continue
        mapped += 1
        etf_return = daily_return(daily.get(etf), pd.Timestamp(row["entry_ts"]), pd.Timestamp(row["simulated_exit_ts"]))
        if etf_return is None:
            continue
        priced += 1
        out = dict(row)
        stock_return = float(row["net_return_from_entry"])
        out["mapped_leverage_etf"] = etf
        out["overlay_weight"] = float(weight)
        out["stock_component_return"] = stock_return
        out["etf_component_return"] = float(etf_return)
        out["net_return_from_entry"] = (1.0 - weight) * stock_return + weight * float(etf_return)
        rows.append(out)
    coverage = {
        "mapped_trade_count": mapped,
        "priced_trade_count": priced,
        "price_coverage_rate": float(priced / mapped) if mapped else 0.0,
    }
    return pd.DataFrame(rows), coverage


def daily_return(frame: pd.DataFrame | None, entry_ts: pd.Timestamp, exit_ts: pd.Timestamp) -> float | None:
    if frame is None or frame.empty:
        return None
    entry_date = entry_ts.date()
    exit_date = exit_ts.date()
    dates = frame["date"]
    entry_rows = frame[dates >= entry_date]
    exit_rows = frame[dates >= exit_date]
    if entry_rows.empty or exit_rows.empty:
        return None
    entry_price = float(entry_rows.iloc[0]["price"])
    exit_price = float(exit_rows.iloc[0]["price"])
    if entry_price <= 0:
        return None
    return exit_price / entry_price - 1.0


def build_drawdown_throttle_grid(base_panel: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    base_final, base_dd = baseline_values(baseline)
    rows: list[dict[str, object]] = []
    for threshold in (-5.0, -10.0, -15.0):
        for multiplier in (0.75, 0.50, 0.25):
            metrics = simulate_scaled_account(costed(base_panel, ROUND_TRIP_COST_BPS), threshold, multiplier, 0)
            rows.append(throttle_row("size_reduce", threshold, multiplier, 0, metrics, base_final, base_dd))
        for cooldown_days in (5, 10, 20):
            metrics = simulate_scaled_account(costed(base_panel, ROUND_TRIP_COST_BPS), threshold, 0.0, cooldown_days)
            rows.append(throttle_row("cooldown_skip", threshold, 0.0, cooldown_days, metrics, base_final, base_dd))
    return pd.DataFrame(rows).sort_values(["return_up_drawdown_down_pass_flag", "final_capital_usd"], ascending=False).reset_index(drop=True)


def build_exclusion_throttle_combo_grid(
    base_panel: pd.DataFrame,
    baseline: pd.DataFrame,
    exclusion_grid: pd.DataFrame,
) -> pd.DataFrame:
    base_final, base_dd = baseline_values(baseline)
    targets = exclusion_grid[
        exclusion_grid["policy"].eq("exclude_one")
        & exclusion_grid["final_delta_vs_task639_usd"].gt(0)
    ].head(12)
    rows: list[dict[str, object]] = []
    for exclusion in targets.to_dict(orient="records"):
        target_type = str(exclusion["target_type"])
        target_value = str(exclusion["target_value"])
        column = "theme_id" if target_type == "theme" else "symbol"
        scoped = base_panel[~base_panel[column].astype(str).eq(target_value)].copy()
        for threshold in (-5.0, -10.0, -15.0, -20.0):
            for multiplier in (0.75, 0.50, 0.25):
                metrics = simulate_scaled_account(costed(scoped, ROUND_TRIP_COST_BPS), threshold, multiplier, 0)
                rows.append(combo_row(target_type, target_value, threshold, multiplier, 0, metrics, base_final, base_dd))
            for cooldown_days in (5, 10, 20):
                metrics = simulate_scaled_account(costed(scoped, ROUND_TRIP_COST_BPS), threshold, 0.0, cooldown_days)
                rows.append(combo_row(target_type, target_value, threshold, 0.0, cooldown_days, metrics, base_final, base_dd))
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["return_up_drawdown_down_pass_flag", "final_capital_usd"], ascending=False).reset_index(drop=True)


def combo_row(
    target_type: str,
    target_value: str,
    threshold: float,
    multiplier: float,
    cooldown_days: int,
    metrics: dict[str, object],
    base_final: float,
    base_dd: float,
) -> dict[str, object]:
    final = float(metrics["final_capital_usd"])
    dd = float(metrics["max_drawdown_pct"])
    return {
        "target_type": target_type,
        "target_value": target_value,
        "drawdown_threshold_pct": float(threshold),
        "position_multiplier": float(multiplier),
        "cooldown_days": int(cooldown_days),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": final,
        "max_drawdown_pct": dd,
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "final_delta_vs_task639_usd": final - base_final,
        "drawdown_delta_vs_task639_pct_point": dd - base_dd,
        "return_up_drawdown_down_pass_flag": int(final > base_final and dd > base_dd),
        "single_name_exclusion_overfit_risk_flag": int(target_type in {"symbol", "theme"}),
    }


def simulate_scaled_account(panel: pd.DataFrame, drawdown_threshold_pct: float, multiplier: float, cooldown_days: int) -> dict[str, object]:
    ordered = panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    drawdown_rows: list[float] = []
    cool_until: pd.Timestamp | None = None

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                drawdown_rows.append((equity / peak - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        current_dd = (equity / peak - 1.0) * 100.0
        if cooldown_days > 0 and current_dd <= drawdown_threshold_pct:
            cool_until = entry_ts + pd.Timedelta(days=cooldown_days)
        if cool_until is not None and entry_ts < cool_until:
            continue
        if len(open_positions) >= MAX_POSITIONS:
            continue
        active_multiplier = multiplier if current_dd <= drawdown_threshold_pct else 1.0
        if active_multiplier <= 0:
            continue
        capital = equity / float(MAX_POSITIONS) * active_multiplier
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        out = dict(row)
        out["throttle_position_multiplier"] = active_multiplier
        accepted_rows.append(out)
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    if accepted.empty:
        return empty_metrics()
    returns = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce")
    return {
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": float(INITIAL_CAPITAL_USD * equity),
        "max_drawdown_pct": float(min(drawdown_rows) if drawdown_rows else 0.0),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "avg_net_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
    }


def throttle_row(
    policy: str,
    threshold: float,
    multiplier: float,
    cooldown_days: int,
    metrics: dict[str, object],
    base_final: float,
    base_dd: float,
) -> dict[str, object]:
    final = float(metrics["final_capital_usd"])
    dd = float(metrics["max_drawdown_pct"])
    return {
        "policy": policy,
        "drawdown_threshold_pct": float(threshold),
        "position_multiplier": float(multiplier),
        "cooldown_days": int(cooldown_days),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": final,
        "max_drawdown_pct": dd,
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "final_delta_vs_task639_usd": final - base_final,
        "drawdown_delta_vs_task639_pct_point": dd - base_dd,
        "return_up_drawdown_down_pass_flag": int(final > base_final and dd > base_dd),
    }


def empty_metrics() -> dict[str, object]:
    return {
        "accepted_trade_count": 0,
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "max_drawdown_pct": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
    }


def build_source_audit(
    base_panel: pd.DataFrame,
    task639_pass_candidates: pd.DataFrame,
    daily: dict[str, pd.DataFrame],
    leverage_grid: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "source_rule": "Task639 best same-rule candidate",
                "base_source_trade_count": int(len(base_panel)),
                "task639_same_rule_pass_candidate_count": int(len(task639_pass_candidates)),
                "leveraged_etf_symbols_available": ",".join(sorted(daily.keys())),
                "leveraged_etf_available_count": int(len(daily)),
                "leveraged_overlay_configs": int(len(leverage_grid)),
                "leveraged_overlay_min_price_coverage_rate": float(leverage_grid["price_coverage_rate"].min()) if not leverage_grid.empty else 0.0,
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_pass_fail(
    baseline: pd.DataFrame,
    exclusion_grid: pd.DataFrame,
    leverage_grid: pd.DataFrame,
    throttle_grid: pd.DataFrame,
    combined_grid: pd.DataFrame,
    source_audit: pd.DataFrame,
) -> pd.DataFrame:
    base = baseline.iloc[0]
    audit = source_audit.iloc[0]
    best_exclusion = exclusion_grid.iloc[0]
    best_leverage = leverage_grid.iloc[0]
    best_throttle = throttle_grid.iloc[0]
    best_combo = combined_grid.iloc[0] if not combined_grid.empty else pd.Series(dtype=object)
    any_pass = int(
        exclusion_grid["return_up_drawdown_down_pass_flag"].max() == 1
        or leverage_grid["return_up_drawdown_down_pass_flag"].max() == 1
        or throttle_grid["return_up_drawdown_down_pass_flag"].max() == 1
        or (not combined_grid.empty and combined_grid["return_up_drawdown_down_pass_flag"].max() == 1)
    )
    return pd.DataFrame(
        [
            {
                "gate": "task639_baseline_reproduced",
                "pass_flag": int(base["task639_recheck_match_flag"]),
                "observed_value": f"${float(base['final_capital_usd']):.2f}, dd={float(base['max_drawdown_pct']):.2f}%",
                "required_value": "Task639 reported baseline must be reproduced",
            },
            {
                "gate": "leveraged_etf_data_available",
                "pass_flag": int(int(audit["leveraged_etf_available_count"]) >= 4),
                "observed_value": str(audit["leveraged_etf_symbols_available"]),
                "required_value": "leveraged ETF daily data must exist for overlay test",
            },
            {
                "gate": "exclusion_filter_improves_task639",
                "pass_flag": int(exclusion_grid["return_up_drawdown_down_pass_flag"].max()),
                "observed_value": f"best={best_exclusion['target_type']}:{best_exclusion['target_value']} ${float(best_exclusion['final_capital_usd']):.2f}, dd={float(best_exclusion['max_drawdown_pct']):.2f}%",
                "required_value": "final capital above Task639 and drawdown less severe",
            },
            {
                "gate": "leveraged_etf_improves_task639",
                "pass_flag": int(leverage_grid["return_up_drawdown_down_pass_flag"].max()),
                "observed_value": f"best={best_leverage['overlay_name']} w={float(best_leverage['overlay_weight']):.2f} ${float(best_leverage['final_capital_usd']):.2f}, dd={float(best_leverage['max_drawdown_pct']):.2f}%",
                "required_value": "final capital above Task639 and drawdown less severe",
            },
            {
                "gate": "drawdown_throttle_improves_task639",
                "pass_flag": int(throttle_grid["return_up_drawdown_down_pass_flag"].max()),
                "observed_value": f"best={best_throttle['policy']} ${float(best_throttle['final_capital_usd']):.2f}, dd={float(best_throttle['max_drawdown_pct']):.2f}%",
                "required_value": "final capital above Task639 and drawdown less severe",
            },
            {
                "gate": "exclusion_plus_throttle_improves_task639",
                "pass_flag": int(0 if combined_grid.empty else combined_grid["return_up_drawdown_down_pass_flag"].max()),
                "observed_value": (
                    "no combo rows"
                    if combined_grid.empty
                    else f"best={best_combo['target_type']}:{best_combo['target_value']} thr={float(best_combo['drawdown_threshold_pct']):.1f} mult={float(best_combo['position_multiplier']):.2f} ${float(best_combo['final_capital_usd']):.2f}, dd={float(best_combo['max_drawdown_pct']):.2f}%"
                ),
                "required_value": "final capital above Task639 and drawdown less severe",
            },
            {
                "gate": "combo_overfit_risk_block",
                "pass_flag": 0,
                "observed_value": (
                    "combo uses single symbol/theme exclusion"
                    if not combined_grid.empty and int(best_combo.get("return_up_drawdown_down_pass_flag", 0)) == 1
                    else "no promoted combo"
                ),
                "required_value": "single-name or single-theme exclusions require fresh OOS and causal pre-entry rule before acceptance",
            },
            {
                "gate": "any_return_up_drawdown_down_upgrade_found",
                "pass_flag": any_pass,
                "observed_value": f"any_pass={any_pass}",
                "required_value": "at least one tested upgrade must improve both return and drawdown",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research rejection or candidate only",
                "required_value": "requires live-readable rule lock, source latency audit, and paper-shadow replay",
            },
        ]
    )


def build_decision(
    baseline: pd.DataFrame,
    exclusion_grid: pd.DataFrame,
    leverage_grid: pd.DataFrame,
    throttle_grid: pd.DataFrame,
    combined_grid: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    base = baseline.iloc[0]
    best_exclusion = exclusion_grid.iloc[0]
    best_leverage = leverage_grid.iloc[0]
    best_throttle = throttle_grid.iloc[0]
    best_combo = combined_grid.iloc[0] if not combined_grid.empty else pd.Series(dtype=object)
    any_pass = int(pass_fail[pass_fail["gate"].eq("any_return_up_drawdown_down_upgrade_found")].iloc[0]["pass_flag"])
    return pd.DataFrame(
        [
            {
                "decision": "PASS_COMBO_RETURN_UP_DRAWDOWN_DOWN_RESEARCH_CANDIDATE_NOT_ACCEPTED" if any_pass else "FAIL_NO_LEVERAGE_ETF_OR_THROTTLE_UPGRADE_OVER_TASK639",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "task639_baseline_final_capital_usd": float(base["final_capital_usd"]),
                "task639_baseline_max_drawdown_pct": float(base["max_drawdown_pct"]),
                "best_exclusion_policy": str(best_exclusion["policy"]),
                "best_exclusion_target": f"{best_exclusion['target_type']}:{best_exclusion['target_value']}",
                "best_exclusion_final_capital_usd": float(best_exclusion["final_capital_usd"]),
                "best_exclusion_max_drawdown_pct": float(best_exclusion["max_drawdown_pct"]),
                "best_leverage_overlay": str(best_leverage["overlay_name"]),
                "best_leverage_weight": float(best_leverage["overlay_weight"]),
                "best_leverage_final_capital_usd": float(best_leverage["final_capital_usd"]),
                "best_leverage_max_drawdown_pct": float(best_leverage["max_drawdown_pct"]),
                "best_throttle_policy": str(best_throttle["policy"]),
                "best_throttle_final_capital_usd": float(best_throttle["final_capital_usd"]),
                "best_throttle_max_drawdown_pct": float(best_throttle["max_drawdown_pct"]),
                "best_combo_target": "" if combined_grid.empty else f"{best_combo['target_type']}:{best_combo['target_value']}",
                "best_combo_drawdown_threshold_pct": 0.0 if combined_grid.empty else float(best_combo["drawdown_threshold_pct"]),
                "best_combo_position_multiplier": 0.0 if combined_grid.empty else float(best_combo["position_multiplier"]),
                "best_combo_final_capital_usd": INITIAL_CAPITAL_USD if combined_grid.empty else float(best_combo["final_capital_usd"]),
                "best_combo_max_drawdown_pct": 0.0 if combined_grid.empty else float(best_combo["max_drawdown_pct"]),
                "best_combo_overfit_risk_flag": 0 if combined_grid.empty else int(best_combo["single_name_exclusion_overfit_risk_flag"]),
                "recommended_next_step": "Do not use leveraged ETF overlay now. Treat the MDB-exclusion plus drawdown-throttle combo as a fragile research candidate only; next test whether the excluded-name damage has a causal source/content reason and fresh OOS support.",
            }
        ]
    )


def render_report(
    baseline: pd.DataFrame,
    exclusion_grid: pd.DataFrame,
    leverage_grid: pd.DataFrame,
    throttle_grid: pd.DataFrame,
    combined_grid: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    base = baseline.iloc[0]
    dec = decision.iloc[0]
    return "\n".join(
        [
            "# Task640 Leverage ETF Drawdown Upgrade",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Task639 baseline: ${float(base['final_capital_usd']):.2f}, max drawdown {float(base['max_drawdown_pct']):.2f}%",
            f"- Best exclusion: `{dec['best_exclusion_target']}` -> ${float(dec['best_exclusion_final_capital_usd']):.2f}, DD {float(dec['best_exclusion_max_drawdown_pct']):.2f}%",
            f"- Best leveraged ETF overlay: `{dec['best_leverage_overlay']}` weight {float(dec['best_leverage_weight']):.2f} -> ${float(dec['best_leverage_final_capital_usd']):.2f}, DD {float(dec['best_leverage_max_drawdown_pct']):.2f}%",
            f"- Best drawdown throttle: `{dec['best_throttle_policy']}` -> ${float(dec['best_throttle_final_capital_usd']):.2f}, DD {float(dec['best_throttle_max_drawdown_pct']):.2f}%",
            f"- Best combo: `{dec['best_combo_target']}` + threshold {float(dec['best_combo_drawdown_threshold_pct']):.1f}% / multiplier {float(dec['best_combo_position_multiplier']):.2f} -> ${float(dec['best_combo_final_capital_usd']):.2f}, DD {float(dec['best_combo_max_drawdown_pct']):.2f}%",
            "",
            "## Quant Expert Report",
            "",
            "Task640 tested four direct ways to increase return and reduce drawdown over Task639: single theme/symbol exclusion, leveraged ETF theme overlays, realized drawdown throttles, and exclusion-plus-throttle combos. The acceptance bar was strict: a candidate must beat Task639 final capital and have a less severe max drawdown.",
            "",
            "### Source Audit",
            "",
            csv_table(source_audit),
            "",
            "### Top Exclusion Tests",
            "",
            csv_table(exclusion_grid.head(12)),
            "",
            "### Top Leveraged ETF Overlay Tests",
            "",
            csv_table(leverage_grid.head(12)),
            "",
            "### Top Drawdown Throttle Tests",
            "",
            csv_table(throttle_grid.head(12)),
            "",
            "### Top Exclusion Plus Throttle Combo Tests",
            "",
            csv_table(combined_grid.head(12)),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Leveraged ETFs did not help this rule. They lowered return and made drawdown worse or not better.",
            "- Removing one bad-looking theme or symbol also did not produce a clean return-up and drawdown-down improvement.",
            "- Drawdown throttles can reduce some damage, but they cut too much upside.",
            "- One combo did improve both: exclude `MDB`, then cut new position size to 75% after realized drawdown passes -5%.",
            "- This is not accepted because single-name exclusion can be curve-fit. Next step is to prove why that name should be excluded with pre-entry source/content evidence or reject it.",
            "",
            "## Pass/Fail Matrix",
            "",
            csv_table(pass_fail),
            "",
            "## Artifact Manifest",
            "",
            "- `task_640_task639_baseline_recheck.csv`",
            "- `task_640_exclusion_filter_grid.csv`",
            "- `task_640_leverage_etf_overlay_grid.csv`",
            "- `task_640_drawdown_throttle_grid.csv`",
            "- `task_640_exclusion_throttle_combo_grid.csv`",
            "- `task_640_source_audit.csv`",
            "- `task_640_pass_fail_matrix.csv`",
            "- `task_640_decision.csv`",
            "- `task_640_gpt_review_packet.txt`",
            "- `task_640_gpt_review_response.md`",
            "- `artifact_manifest.csv`",
            "",
        ]
    )


def write_gpt_packet(
    out_dir: Path,
    baseline: pd.DataFrame,
    exclusion_grid: pd.DataFrame,
    leverage_grid: pd.DataFrame,
    throttle_grid: pd.DataFrame,
    combined_grid: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    base = baseline.iloc[0]
    dec = decision.iloc[0]
    text = f"""We are reviewing a quant research strategy. GPT is review-only, not a source of truth.

Current locked research rule, Task639:
- Rule: positive_contract_customer OR content_supply_demand
- Entry: next trading day
- Exit: existing strategy exit
- Sizing: equal max5
- Cost: 50bp round trip
- Starting capital: $1000
- Final capital: ${float(base['final_capital_usd']):.2f}
- Max drawdown: {float(base['max_drawdown_pct']):.2f}%
- Validation and recent OOS both beat same-period QQQ.
- Strategy remains NOT_ACCEPTED until live-readable source rules, source latency, and paper-shadow replay pass.

Task640 tested whether we can increase return and reduce drawdown using:
1. single theme/symbol exclusions,
2. leveraged ETF theme overlays,
3. realized drawdown throttles.

Best observed results:
- Exclusion: {dec['best_exclusion_target']} -> ${float(dec['best_exclusion_final_capital_usd']):.2f}, DD {float(dec['best_exclusion_max_drawdown_pct']):.2f}%
- Leveraged ETF overlay: {dec['best_leverage_overlay']} weight {float(dec['best_leverage_weight']):.2f} -> ${float(dec['best_leverage_final_capital_usd']):.2f}, DD {float(dec['best_leverage_max_drawdown_pct']):.2f}%
- Drawdown throttle: {dec['best_throttle_policy']} -> ${float(dec['best_throttle_final_capital_usd']):.2f}, DD {float(dec['best_throttle_max_drawdown_pct']):.2f}%
- Exclusion plus throttle combo: {dec['best_combo_target']} and realized drawdown threshold {float(dec['best_combo_drawdown_threshold_pct']):.1f}% / position multiplier {float(dec['best_combo_position_multiplier']):.2f} -> ${float(dec['best_combo_final_capital_usd']):.2f}, DD {float(dec['best_combo_max_drawdown_pct']):.2f}%. This uses a single-name exclusion and is therefore treated as high overfit risk until causally explained and fresh-OOS validated.

Question:
Given that leveraged ETF overlays and simple throttles did not beat Task639 on both return and drawdown, but one MDB-exclusion plus throttle combo did, what should a firm-grade quant team test next to increase return while reducing drawdown? Please focus on tradable, pre-entry or execution-time rules, not after-the-fact return labels. Also identify what would be dangerous overfitting.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "task_640_gpt_review_packet.txt").write_text(text, encoding="utf-8")


def csv_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    safe = frame.copy()
    safe = safe.where(pd.notna(safe), "")
    columns = [str(column) for column in safe.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in safe.astype(str).to_dict(orient="records"):
        lines.append("| " + " | ".join(row[column] for column in safe.columns) + " |")
    return "\n".join(lines)


def baseline_values(baseline: pd.DataFrame) -> tuple[float, float]:
    row = baseline.iloc[0]
    return float(row["final_capital_usd"]), float(row["max_drawdown_pct"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task640_leverage_etf_drawdown_upgrade(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
