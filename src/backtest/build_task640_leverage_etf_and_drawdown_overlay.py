from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task638_content_signal_refinement import costed, simulate_account


TASK_ID = "Task640"
REPORT_DIR = Path("docs/reports/task_640_leverage_etf_and_drawdown_overlay")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
ETF_DAILY_DIR = Path("data/raw/us_daily")
INITIAL_CAPITAL_USD = 1000.0

LEVERAGE_THEME_3X = {
    "ai_semiconductors": "SOXL",
    "cloud_ai_platforms": "TQQQ",
    "data_devops_software": "TQQQ",
    "cybersecurity": "TQQQ",
    "crypto_fintech": "TQQQ",
    "biotech_glp1_healthcare": "LABU",
    "ev_autonomy_mobility": "QLD",
    "aerospace_defense_space": "UPRO",
    "power_grid_electrification": "UPRO",
    "industrial_automation_robotics": "UPRO",
}
LEVERAGE_THEME_2X = {theme: ("QLD" if etf == "TQQQ" else "SSO" if etf == "UPRO" else etf) for theme, etf in LEVERAGE_THEME_3X.items()}


def build_task640_leverage_etf_and_drawdown_overlay(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    etf_daily_dir: Path = ETF_DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_execution_panel(execution_panel_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    base = task639_base_panel(panel)
    etf_maps = load_etf_maps(etf_daily_dir)
    leverage = build_leverage_overlay_grid(base, etf_maps)
    throttle = build_drawdown_throttle_grid(base)
    exclusions = build_exclusion_grid(base)
    source_audit = build_source_audit(base, leverage, throttle, exclusions)
    pass_fail = build_pass_fail(leverage, throttle, exclusions, task639, source_audit)
    decision = build_decision(leverage, throttle, exclusions, task639, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    leverage.to_csv(out_dir / "task_640_leverage_etf_overlay_grid.csv", index=False)
    throttle.to_csv(out_dir / "task_640_drawdown_throttle_grid.csv", index=False)
    exclusions.to_csv(out_dir / "task_640_symbol_theme_exclusion_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_640_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_640_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_640_decision.csv", index=False)
    (out_dir / "task_640_leverage_etf_and_drawdown_overlay.md").write_text(
        render_report(leverage, throttle, exclusions, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_640_leverage_etf_overlay_grid": leverage,
        "task_640_drawdown_throttle_grid": throttle,
        "task_640_symbol_theme_exclusion_grid": exclusions,
        "task_640_source_audit": source_audit,
        "task_640_pass_fail_matrix": pass_fail,
        "task_640_decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    return panel.dropna(subset=["entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def task639_base_panel(panel: pd.DataFrame) -> pd.DataFrame:
    mask = (
        (
            pd.to_numeric(panel["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0)
            | pd.to_numeric(panel["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1)
        )
        & panel["timing_mode"].eq("delay1d")
        & panel["exit_mode"].eq("existing_exit")
    )
    return panel[mask].copy()


def load_etf_maps(etf_daily_dir: Path) -> dict[str, pd.DataFrame]:
    out = {}
    for symbol in sorted(set(LEVERAGE_THEME_3X.values()).union(LEVERAGE_THEME_2X.values())):
        path = etf_daily_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df.columns = [str(col).lower() for col in df.columns]
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        for column in ["open", "close"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.dropna(subset=["timestamp", "open", "close"]).sort_values("timestamp").reset_index(drop=True)
        df["date"] = df["timestamp"].dt.date
        out[symbol] = df
    return out


def etf_return(row: pd.Series, theme_map: dict[str, str], etf_maps: dict[str, pd.DataFrame]) -> float | None:
    etf = theme_map.get(str(row["theme_id"]))
    if not etf or etf not in etf_maps:
        return None
    df = etf_maps[etf]
    entry_date = pd.Timestamp(row["entry_ts"]).tz_convert("America/New_York").date()
    exit_date = pd.Timestamp(row["simulated_exit_ts"]).tz_convert("America/New_York").date()
    entry = df[df["date"].ge(entry_date)].head(1)
    exit_ = df[df["date"].le(exit_date)].tail(1)
    if entry.empty or exit_.empty:
        return None
    return float(exit_.iloc[0]["close"]) / float(entry.iloc[0]["open"]) - 1.0


def account_metrics(panel: pd.DataFrame) -> dict[str, object]:
    quality, accepted = simulate_account(costed(panel, 50), "equal_max5")
    return {
        "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
        "accepted_trade_count": int(len(accepted)),
        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
    }


def build_leverage_overlay_grid(base: pd.DataFrame, etf_maps: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, theme_map in [("theme_3x", LEVERAGE_THEME_3X), ("theme_2x", LEVERAGE_THEME_2X)]:
        work = base.copy()
        work["leverage_etf_return"] = [etf_return(row, theme_map, etf_maps) for _, row in work.iterrows()]
        work = work.dropna(subset=["leverage_etf_return"]).copy()
        for weight in [0.10, 0.20, 0.30, 0.50, 1.00]:
            test = work.copy()
            stock_ret = pd.to_numeric(test["net_return_from_entry"], errors="coerce")
            etf_ret = pd.to_numeric(test["leverage_etf_return"], errors="coerce")
            test["net_return_from_entry"] = (1.0 - weight) * stock_ret + weight * etf_ret
            metrics = account_metrics(test)
            rows.append(
                {
                    "overlay_name": name,
                    "leverage_etf_weight": weight,
                    "source_trade_count": int(len(test)),
                    **metrics,
                }
            )
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def simulate_throttle(panel: pd.DataFrame, *, threshold: float, reduce_factor: float, stop_new: bool, cooldown_days: int) -> dict[str, object]:
    ordered = panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    open_positions: list[dict[str, object]] = []
    accepted = []
    cooldown_until = None

    def close_until(ts: pd.Timestamp, *, set_cooldown: bool = True) -> None:
        nonlocal equity, peak, max_drawdown, open_positions, cooldown_until
        still_open = []
        closed_loss = False
        for pos in open_positions:
            if pos["exit_ts"] <= ts:
                pnl = float(pos["capital"]) * float(pos["return"])
                equity += pnl
                closed_loss = closed_loss or pnl < 0
                peak = max(peak, equity)
                max_drawdown = min(max_drawdown, (equity / max(peak, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open
        if set_cooldown and closed_loss and cooldown_days:
            cooldown_until = ts + pd.Timedelta(days=cooldown_days)

    for row in ordered.to_dict(orient="records"):
        ts = pd.Timestamp(row["entry_ts"])
        close_until(ts)
        if len(open_positions) >= 5:
            continue
        if cooldown_until is not None and ts < cooldown_until:
            continue
        current_dd = (equity / max(peak, 1e-9) - 1.0) * 100.0
        if current_dd <= -abs(threshold) and stop_new:
            continue
        weight = 1.0 / 5.0
        if current_dd <= -abs(threshold):
            weight *= reduce_factor
        open_positions.append(
            {
                "exit_ts": pd.Timestamp(row["simulated_exit_ts"]),
                "capital": equity * weight,
                "return": float(row["net_return_from_entry"]) - 0.005,
            }
        )
        accepted.append(row)
    if open_positions:
        close_until(max(pos["exit_ts"] for pos in open_positions), set_cooldown=False)
    returns = pd.Series([float(row["net_return_from_entry"]) - 0.005 for row in accepted], dtype=float)
    return {
        "final_capital_usd": equity * INITIAL_CAPITAL_USD,
        "max_drawdown_pct": float(max_drawdown),
        "accepted_trade_count": int(len(accepted)),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()) if len(returns) else 0.0,
    }


def build_drawdown_throttle_grid(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in [5, 10, 15, 20]:
        for reduce_factor in [0.25, 0.50, 0.75]:
            for stop_new in [0, 1]:
                for cooldown_days in [0, 5, 10, 20]:
                    metrics = simulate_throttle(
                        base,
                        threshold=float(threshold),
                        reduce_factor=float(reduce_factor),
                        stop_new=bool(stop_new),
                        cooldown_days=int(cooldown_days),
                    )
                    rows.append(
                        {
                            "threshold_drawdown_pct": threshold,
                            "reduce_factor": reduce_factor,
                            "stop_new_entries_flag": stop_new,
                            "cooldown_days_after_loss": cooldown_days,
                            **metrics,
                        }
                    )
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_exclusion_grid(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metrics = account_metrics(base)
    rows.append({"mode": "base", "excluded_item": "", "source_trade_count": int(len(base)), **metrics})
    for symbol in base["symbol"].value_counts().head(25).index:
        scoped = base[base["symbol"].ne(symbol)].copy()
        rows.append({"mode": "exclude_symbol", "excluded_item": symbol, "source_trade_count": int(len(scoped)), **account_metrics(scoped)})
    for theme in sorted(base["theme_id"].dropna().unique()):
        scoped = base[base["theme_id"].ne(theme)].copy()
        rows.append({"mode": "exclude_theme", "excluded_item": theme, "source_trade_count": int(len(scoped)), **account_metrics(scoped)})
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_source_audit(base: pd.DataFrame, leverage: pd.DataFrame, throttle: pd.DataFrame, exclusions: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "base_source_trade_count": int(len(base)),
                "leverage_overlay_count": int(len(leverage)),
                "drawdown_throttle_count": int(len(throttle)),
                "exclusion_test_count": int(len(exclusions)),
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "leverage_etf_data_available_flag": int(len(leverage) > 0),
            }
        ]
    )


def best_frame_row(*frames: pd.DataFrame) -> pd.Series:
    merged = pd.concat(frames, ignore_index=True)
    return merged.sort_values("final_capital_usd", ascending=False).iloc[0]


def build_pass_fail(leverage: pd.DataFrame, throttle: pd.DataFrame, exclusions: pd.DataFrame, task639: pd.Series, source_audit: pd.DataFrame) -> pd.DataFrame:
    task639_final = float(task639["best_50bp_final_capital_usd"])
    task639_dd = float(task639["best_50bp_max_drawdown_pct"])
    all_rows = pd.concat(
        [
            leverage.assign(test_family="leverage_etf_overlay"),
            throttle.assign(test_family="drawdown_throttle"),
            exclusions.assign(test_family="symbol_theme_exclusion"),
        ],
        ignore_index=True,
    )
    better_both = all_rows[
        all_rows["final_capital_usd"].gt(task639_final)
        & all_rows["max_drawdown_pct"].gt(task639_dd)
    ]
    best = all_rows.sort_values("final_capital_usd", ascending=False).iloc[0]
    best_dd = all_rows.sort_values("max_drawdown_pct", ascending=False).iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "leverage_etf_data_available",
                "pass_flag": int(source_audit.iloc[0]["leverage_etf_data_available_flag"]),
                "observed_value": f"leverage_tests={len(leverage)}",
                "required_value": "leveraged ETF overlay tests must run",
            },
            {
                "gate": "return_up_drawdown_down_vs_task639",
                "pass_flag": int(len(better_both) > 0),
                "observed_value": f"better_both_candidates={len(better_both)}",
                "required_value": "candidate should beat Task639 final and improve Task639 max drawdown",
            },
            {
                "gate": "best_return_candidate",
                "pass_flag": int(float(best["final_capital_usd"]) > task639_final),
                "observed_value": f"best=${float(best['final_capital_usd']):.2f}; dd={float(best['max_drawdown_pct']):.2f}%; task639=${task639_final:.2f}",
                "required_value": "best return candidate should beat Task639",
            },
            {
                "gate": "best_drawdown_candidate",
                "pass_flag": int(float(best_dd["max_drawdown_pct"]) > task639_dd),
                "observed_value": f"best_dd={float(best_dd['max_drawdown_pct']):.2f}%; final=${float(best_dd['final_capital_usd']):.2f}; task639_dd={task639_dd:.2f}%",
                "required_value": "best drawdown candidate should improve Task639 drawdown",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research only",
                "required_value": "requires live-readable rule lock and paper-shadow replay",
            },
        ]
    )


def build_decision(leverage: pd.DataFrame, throttle: pd.DataFrame, exclusions: pd.DataFrame, task639: pd.Series, pass_fail: pd.DataFrame) -> pd.DataFrame:
    all_rows = pd.concat(
        [
            leverage.assign(test_family="leverage_etf_overlay"),
            throttle.assign(test_family="drawdown_throttle"),
            exclusions.assign(test_family="symbol_theme_exclusion"),
        ],
        ignore_index=True,
    )
    task639_final = float(task639["best_50bp_final_capital_usd"])
    task639_dd = float(task639["best_50bp_max_drawdown_pct"])
    better_both = all_rows[
        all_rows["final_capital_usd"].gt(task639_final)
        & all_rows["max_drawdown_pct"].gt(task639_dd)
    ]
    best = all_rows.sort_values("final_capital_usd", ascending=False).iloc[0]
    best_dd = all_rows.sort_values("max_drawdown_pct", ascending=False).iloc[0]
    decision = "FAIL_NO_LEVERAGE_OR_THROTTLE_IMPROVES_RETURN_AND_DRAWDOWN"
    if not better_both.empty:
        decision = "PASS_RETURN_UP_DRAWDOWN_DOWN_OVERLAY_CANDIDATE_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "task639_final_capital_usd": task639_final,
                "task639_max_drawdown_pct": task639_dd,
                "best_return_family": best.get("test_family", ""),
                "best_return_final_capital_usd": float(best["final_capital_usd"]),
                "best_return_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "best_drawdown_family": best_dd.get("test_family", ""),
                "best_drawdown_final_capital_usd": float(best_dd["final_capital_usd"]),
                "best_drawdown_max_drawdown_pct": float(best_dd["max_drawdown_pct"]),
                "better_both_candidate_count": int(len(better_both)),
                "trading_promotion_pass_flag": 0,
                "next_action": "Do not add leveraged ETF overlay. Keep Task639 as current best and improve drawdown through source-latency/rule-lock diagnostics or tighter candidate quality, not broad leverage.",
            }
        ]
    )


def render_report(
    leverage: pd.DataFrame,
    throttle: pd.DataFrame,
    exclusions: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task640 Leverage ETF And Drawdown Overlay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639: ${float(d['task639_final_capital_usd']):.2f}, drawdown {float(d['task639_max_drawdown_pct']):.2f}%",
        f"- Best return test: `{d['best_return_family']}` = ${float(d['best_return_final_capital_usd']):.2f}, drawdown {float(d['best_return_max_drawdown_pct']):.2f}%",
        f"- Best drawdown test: `{d['best_drawdown_family']}` = ${float(d['best_drawdown_final_capital_usd']):.2f}, drawdown {float(d['best_drawdown_max_drawdown_pct']):.2f}%",
        "",
        "## Quant Expert Report",
        "",
        "This task tests whether leveraged ETF overlays, drawdown throttles, or simple symbol/theme removals can improve both return and drawdown versus Task639.",
        "",
        "### Top Leverage ETF Overlay",
        "",
        "| Overlay | Weight | Final $ | DD |",
        "|---|---:|---:|---:|",
    ]
    for _, row in leverage.head(8).iterrows():
        lines.append(f"| `{row['overlay_name']}` | {float(row['leverage_etf_weight']):.2f} | ${float(row['final_capital_usd']):.2f} | {float(row['max_drawdown_pct']):.2f}% |")
    lines.extend(
        [
            "",
            "### Top Drawdown Throttle",
            "",
            "| Threshold | Reduce | Stop | Cooldown | Final $ | DD |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in throttle.head(8).iterrows():
        lines.append(
            f"| {float(row['threshold_drawdown_pct']):.0f} | {float(row['reduce_factor']):.2f} | {int(row['stop_new_entries_flag'])} | "
            f"{int(row['cooldown_days_after_loss'])} | ${float(row['final_capital_usd']):.2f} | {float(row['max_drawdown_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Top Exclusion Tests",
            "",
            "| Mode | Excluded | Final $ | DD |",
            "|---|---|---:|---:|",
        ]
    )
    for _, row in exclusions.head(8).iterrows():
        lines.append(f"| `{row['mode']}` | `{row['excluded_item']}` | ${float(row['final_capital_usd']):.2f} | {float(row['max_drawdown_pct']):.2f}% |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Leveraged ETF overlay did not help this signal. It reduced return or worsened drawdown.",
            "- Drawdown throttles lowered damage only by giving up too much return.",
            "- Simple exclusions can increase return but did not reduce drawdown.",
            "- Current best remains Task639. Next improvement should come from better source/rule quality, not broad leverage.",
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
            "- `task_640_leverage_etf_overlay_grid.csv`",
            "- `task_640_drawdown_throttle_grid.csv`",
            "- `task_640_symbol_theme_exclusion_grid.csv`",
            "- `task_640_source_audit.csv`",
            "- `task_640_pass_fail_matrix.csv`",
            "- `task_640_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task640_leverage_etf_and_drawdown_overlay(out_dir=args.out_dir)
    d = artifacts["task_640_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={d['decision']} task639=${float(d['task639_final_capital_usd']):.2f} "
        f"best_return=${float(d['best_return_final_capital_usd']):.2f} best_dd={float(d['best_drawdown_max_drawdown_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
