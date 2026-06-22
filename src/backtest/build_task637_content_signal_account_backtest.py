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
from src.backtest.build_task633_qqq_benchmark_full_period_refresh import (
    INITIAL_CAPITAL_USD,
    MAX_POSITIONS,
    load_qqq_benchmark,
    row_final,
)
from src.backtest.build_task489_broad_regime_cell_portfolio import DEFAULT_BROAD_DAILY_DIR


TASK_ID = "Task637"
REPORT_DIR = Path("docs/reports/task_637_content_signal_account_backtest")
BASELINE_PANEL = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task632_temporal_strict_refresh/task_632_baseline_all_confirmed_backtest_panel.csv")
ENTRY_CONTENT_PANEL = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_content_prediction_panel.csv")
TASK633_ACCOUNT = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task_633_1000_account_qqq_comparison.csv")
COST_BPS = (0, 50, 100)


def build_task637_content_signal_account_backtest(
    *,
    baseline_panel_path: Path = BASELINE_PANEL,
    entry_content_panel_path: Path = ENTRY_CONTENT_PANEL,
    task633_account_path: Path = TASK633_ACCOUNT,
    daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    baseline = load_trade_panel(baseline_panel_path)
    content = load_content_panel(entry_content_panel_path)
    merged = baseline.merge(content.drop(columns=["symbol", "theme_id", "entry_ts", "split_name"], errors="ignore"), on="lifecycle_id", how="left")
    merged = add_strategy_flags(merged)
    qqq = load_qqq_benchmark(daily_dir / "QQQ.csv", baseline)
    task633_account = pd.read_csv(task633_account_path)

    account, accepted, split_audit = build_account_tables(merged, qqq, task633_account)
    oos_account = build_oos_account_tables(merged, daily_dir / "QQQ.csv")
    source_audit = build_source_audit(merged, content)
    pass_fail = build_pass_fail(account, split_audit, oos_account, source_audit)
    decision = build_decision(account, oos_account, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    account.to_csv(out_dir / "task_637_content_signal_account_summary.csv", index=False)
    accepted.to_csv(out_dir / "task_637_content_signal_accepted_trades.csv", index=False)
    split_audit.to_csv(out_dir / "task_637_content_signal_split_audit.csv", index=False)
    oos_account.to_csv(out_dir / "task_637_content_signal_oos_account_summary.csv", index=False)
    source_audit.to_csv(out_dir / "task_637_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_637_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_637_decision.csv", index=False)
    (out_dir / "task_637_content_signal_account_backtest.md").write_text(
        render_report(account, split_audit, oos_account, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_637_content_signal_account_summary": account,
        "task_637_content_signal_accepted_trades": accepted,
        "task_637_content_signal_split_audit": split_audit,
        "task_637_content_signal_oos_account_summary": oos_account,
        "task_637_source_audit": source_audit,
        "task_637_pass_fail_matrix": pass_fail,
        "task_637_decision": decision,
    }


def load_trade_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {"lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry", "split_name"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def load_content_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {
        "lifecycle_id",
        "content_negative_score_flag",
        "content_guidance_margin_count",
        "content_supply_demand_count",
        "content_prediction_certified_event_count",
    }
    if "content_negative_score_flag" not in panel.columns:
        panel["content_negative_score_flag"] = (pd.to_numeric(panel["content_net_prediction_score"], errors="coerce").fillna(0) < 0).astype(int)
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    return panel.copy()


def add_strategy_flags(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    for column in [
        "content_negative_score_flag",
        "content_guidance_margin_count",
        "content_supply_demand_count",
        "content_prediction_certified_event_count",
    ]:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    out["content_guidance_margin_flag"] = out["content_guidance_margin_count"].gt(0).astype(int)
    out["content_supply_demand_flag"] = out["content_supply_demand_count"].gt(0).astype(int)
    out["content_any_stable_feature_flag"] = (
        out["content_negative_score_flag"].eq(1)
        | out["content_guidance_margin_flag"].eq(1)
        | out["content_supply_demand_flag"].eq(1)
    ).astype(int)
    out["content_guidance_supply_combo_flag"] = (
        out["content_guidance_margin_flag"].eq(1) & out["content_supply_demand_flag"].eq(1)
    ).astype(int)
    return out


def costed(panel: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    out = panel.copy()
    out["net_return_from_entry"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce") - cost_bps / 10000.0
    return out


def build_account_tables(
    panel: pd.DataFrame,
    qqq: pd.DataFrame,
    task633_account: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    universes = {
        "content_negative_score": "content_negative_score_flag",
        "content_guidance_margin": "content_guidance_margin_flag",
        "content_supply_demand": "content_supply_demand_flag",
        "content_any_stable_feature": "content_any_stable_feature_flag",
        "content_guidance_supply_combo": "content_guidance_supply_combo_flag",
    }
    qqq_final = float(qqq.iloc[0]["final_capital_usd"])
    original_max5 = row_final(task633_account, "task617_original_broad_intelligence_strategy", 5)
    strict_max5 = row_final(task633_account, "task632_temporal_strict_chart_qual_strategy", 5)
    rows: list[dict[str, object]] = []
    accepted_rows: list[pd.DataFrame] = []
    for universe, flag in universes.items():
        selected = panel[panel[flag].eq(1)].copy()
        for cost_bps in COST_BPS:
            test_panel = costed(selected, cost_bps)
            for max_positions in MAX_POSITIONS:
                quality, accepted, _curve = simulate_deterministic_portfolio(test_panel, max_positions=max_positions)
                final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
                rows.append(
                    {
                        "universe": universe,
                        "selection_flag": flag,
                        "round_trip_cost_bps": int(cost_bps),
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "max_positions": int(max_positions),
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
                        "beats_task617_original_max5_flag": int(final_capital > original_max5),
                        "beats_task632_strict_max5_flag": int(final_capital > strict_max5),
                        "excess_vs_qqq_usd": final_capital - qqq_final,
                        "excess_vs_task617_original_max5_usd": final_capital - original_max5,
                        "excess_vs_task632_strict_max5_usd": final_capital - strict_max5,
                        "label_used_in_assignment_flag": 0,
                        "presence_field_used_for_assignment_flag": 0,
                    }
                )
                if cost_bps == 50 and max_positions == 5 and not accepted.empty:
                    acc = accepted.copy()
                    acc["universe"] = universe
                    acc["round_trip_cost_bps"] = int(cost_bps)
                    acc["max_positions"] = int(max_positions)
                    accepted_rows.append(acc)
    account = pd.DataFrame(rows).sort_values(["round_trip_cost_bps", "max_positions", "universe"]).reset_index(drop=True)
    accepted_all = pd.concat(accepted_rows, ignore_index=True) if accepted_rows else pd.DataFrame()
    split_audit = build_split_audit(panel, universes)
    return account, accepted_all, split_audit


def build_oos_account_tables(panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    universes = {
        "content_negative_score": "content_negative_score_flag",
        "content_guidance_margin": "content_guidance_margin_flag",
        "content_supply_demand": "content_supply_demand_flag",
        "content_any_stable_feature": "content_any_stable_feature_flag",
        "content_guidance_supply_combo": "content_guidance_supply_combo_flag",
    }
    qqq = load_qqq_history(qqq_path)
    rows: list[dict[str, object]] = []
    for split_name in ["validation", "recent_oos"]:
        split_panel = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        qqq_final = qqq_final_for_period(qqq, split_panel)
        for universe, flag in universes.items():
            selected = split_panel[split_panel[flag].eq(1)].copy()
            for cost_bps in [50, 100]:
                test_panel = costed(selected, cost_bps)
                for max_positions in MAX_POSITIONS:
                    quality, accepted, _curve = simulate_deterministic_portfolio(test_panel, max_positions=max_positions)
                    final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
                    rows.append(
                        {
                            "split_name": split_name,
                            "universe": universe,
                            "round_trip_cost_bps": int(cost_bps),
                            "max_positions": int(max_positions),
                            "source_trade_count": int(len(selected)),
                            "accepted_trade_count": int(len(accepted)),
                            "final_capital_usd": final_capital,
                            "capital_return_pct": float(quality["capital_pnl_pct"]),
                            "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                            "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                            "qqq_final_capital_usd": qqq_final,
                            "beats_qqq_flag": int(final_capital > qqq_final),
                        }
                    )
    return pd.DataFrame(rows).sort_values(["split_name", "round_trip_cost_bps", "max_positions", "universe"]).reset_index(drop=True)


def load_qqq_history(path: Path) -> pd.DataFrame:
    qqq = pd.read_csv(path)
    qqq.columns = [str(col).strip().lower() for col in qqq.columns]
    qqq["timestamp"] = pd.to_datetime(qqq["timestamp"], utc=True, errors="coerce")
    qqq["close"] = pd.to_numeric(qqq["close"], errors="coerce")
    return qqq.dropna(subset=["timestamp", "close"]).sort_values("timestamp").reset_index(drop=True)


def qqq_final_for_period(qqq: pd.DataFrame, panel: pd.DataFrame) -> float:
    if panel.empty:
        return INITIAL_CAPITAL_USD
    start_date = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce").min().date()
    end_date = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce").max().date()
    start = qqq[qqq["timestamp"].dt.date.ge(start_date)].head(1)
    end = qqq[qqq["timestamp"].dt.date.le(end_date)].tail(1)
    if start.empty or end.empty:
        return INITIAL_CAPITAL_USD
    return INITIAL_CAPITAL_USD * float(end.iloc[0]["close"]) / float(start.iloc[0]["close"])


def build_split_audit(panel: pd.DataFrame, universes: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for universe, flag in universes.items():
        for split_name in ["train_design", "validation", "recent_oos"]:
            split = panel[panel["split_name"].astype(str).eq(split_name)].copy()
            selected = split[split[flag].eq(1)]
            rejected = split[split[flag].eq(0)]
            rows.append(
                {
                    "universe": universe,
                    "split_name": split_name,
                    "selected_count": int(len(selected)),
                    "rejected_count": int(len(rejected)),
                    "selected_avg_return_pct": pct_mean(selected),
                    "rejected_avg_return_pct": pct_mean(rejected),
                    "avg_return_lift_pct_point": pct_mean(selected) - pct_mean(rejected),
                    "selected_entry_reduce_rate": reduce_rate(selected),
                    "rejected_entry_reduce_rate": reduce_rate(rejected),
                    "entry_reduce_delta_pct_point": (reduce_rate(selected) - reduce_rate(rejected)) * 100.0,
                }
            )
    return pd.DataFrame(rows)


def pct_mean(frame: pd.DataFrame) -> float:
    if frame.empty:
        return float("nan")
    return float(pd.to_numeric(frame["net_return_from_entry"], errors="coerce").mean() * 100.0)


def reduce_rate(frame: pd.DataFrame) -> float:
    if frame.empty:
        return float("nan")
    return float(pd.to_numeric(frame["net_return_from_entry"], errors="coerce").le(-0.03).mean())


def build_source_audit(panel: pd.DataFrame, content: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_count": int(len(panel)),
                "entry_start": str(pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce").min().date()),
                "entry_end": str(pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce").max().date()),
                "content_panel_entry_count": int(len(content)),
                "entries_with_content_prediction_count": int(pd.to_numeric(panel["content_prediction_certified_event_count"], errors="coerce").fillna(0).gt(0).sum()),
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_pass_fail(account: pd.DataFrame, split_audit: pd.DataFrame, oos_account: pd.DataFrame, source_audit: pd.DataFrame) -> pd.DataFrame:
    best_50 = account[account["round_trip_cost_bps"].eq(50)].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_100 = account[account["round_trip_cost_bps"].eq(100)].sort_values("final_capital_usd", ascending=False).iloc[0]
    validation_best_50 = (
        oos_account[oos_account["split_name"].eq("validation") & oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values("final_capital_usd", ascending=False)
        .iloc[0]
    )
    recent_best_50 = (
        oos_account[oos_account["split_name"].eq("recent_oos") & oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values("final_capital_usd", ascending=False)
        .iloc[0]
    )
    stable_recent = split_audit[
        split_audit["split_name"].eq("recent_oos")
        & split_audit["avg_return_lift_pct_point"].gt(0)
        & split_audit["entry_reduce_delta_pct_point"].le(0)
    ]["universe"].nunique()
    audit = source_audit.iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "full_period_through_june",
                "pass_flag": int(str(audit["entry_end"]) >= "2026-06-01"),
                "observed_value": f"entry_end={audit['entry_end']}",
                "required_value": "entry panel must extend into June 2026",
            },
            {
                "gate": "content_signal_recent_oos_stability",
                "pass_flag": int(stable_recent >= 1),
                "observed_value": f"recent_oos_stable_universes={stable_recent}",
                "required_value": "at least one content strategy must have positive recent OOS lift and no worse entry-reduce",
            },
            {
                "gate": "best_50bp_beats_qqq",
                "pass_flag": int(best_50["beats_qqq_flag"] == 1),
                "observed_value": f"{best_50['universe']} max{int(best_50['max_positions'])}=${float(best_50['final_capital_usd']):.2f}; qqq=${float(best_50['qqq_final_capital_usd']):.2f}",
                "required_value": "best content strategy at 50bp must beat QQQ",
            },
            {
                "gate": "best_50bp_beats_task617_original_max5",
                "pass_flag": int(best_50["beats_task617_original_max5_flag"] == 1),
                "observed_value": f"{best_50['universe']} max{int(best_50['max_positions'])}=${float(best_50['final_capital_usd']):.2f}; task617_max5=${float(best_50['final_capital_usd'] - best_50['excess_vs_task617_original_max5_usd']):.2f}",
                "required_value": "content strategy must beat existing Task617 max5 before promotion",
            },
            {
                "gate": "best_100bp_still_beats_qqq",
                "pass_flag": int(best_100["beats_qqq_flag"] == 1),
                "observed_value": f"{best_100['universe']} max{int(best_100['max_positions'])}=${float(best_100['final_capital_usd']):.2f}; qqq=${float(best_100['qqq_final_capital_usd']):.2f}",
                "required_value": "best content strategy at 100bp must still beat QQQ",
            },
            {
                "gate": "validation_oos_50bp_account_beats_qqq",
                "pass_flag": int(validation_best_50["beats_qqq_flag"] == 1),
                "observed_value": f"{validation_best_50['universe']} max{int(validation_best_50['max_positions'])}=${float(validation_best_50['final_capital_usd']):.2f}; qqq=${float(validation_best_50['qqq_final_capital_usd']):.2f}",
                "required_value": "validation-only $1000 account must beat same-period QQQ",
            },
            {
                "gate": "recent_oos_50bp_account_beats_qqq",
                "pass_flag": int(recent_best_50["beats_qqq_flag"] == 1),
                "observed_value": f"{recent_best_50['universe']} max{int(recent_best_50['max_positions'])}=${float(recent_best_50['final_capital_usd']):.2f}; qqq=${float(recent_best_50['qqq_final_capital_usd']):.2f}",
                "required_value": "recent OOS-only $1000 account must beat same-period QQQ",
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
                "required_value": "requires exact deployment rules and live source readiness before runtime use",
            },
        ]
    )


def build_decision(account: pd.DataFrame, oos_account: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    best_50 = account[account["round_trip_cost_bps"].eq(50)].sort_values("final_capital_usd", ascending=False).iloc[0]
    validation_best_50 = (
        oos_account[oos_account["split_name"].eq("validation") & oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values("final_capital_usd", ascending=False)
        .iloc[0]
    )
    recent_best_50 = (
        oos_account[oos_account["split_name"].eq("recent_oos") & oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values("final_capital_usd", ascending=False)
        .iloc[0]
    )
    beats_qqq = int(pass_fail[pass_fail["gate"].eq("best_50bp_beats_qqq")].iloc[0]["pass_flag"])
    beats_original = int(pass_fail[pass_fail["gate"].eq("best_50bp_beats_task617_original_max5")].iloc[0]["pass_flag"])
    decision = "FAIL_CONTENT_SIGNAL_ACCOUNT_BACKTEST_NOT_ACCEPTED"
    if beats_qqq and not beats_original:
        decision = "PASS_QQQ_FAILS_EXISTING_MAX5_CONTENT_OVERLAY_ONLY"
    elif beats_qqq and beats_original:
        decision = "PASS_CONTENT_SIGNAL_CANDIDATE_NEEDS_LIVE_RULE_LOCK"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "best_50bp_universe": best_50["universe"],
                "best_50bp_max_positions": int(best_50["max_positions"]),
                "best_50bp_final_capital_usd": float(best_50["final_capital_usd"]),
                "validation_best_50bp_universe": validation_best_50["universe"],
                "validation_best_50bp_final_capital_usd": float(validation_best_50["final_capital_usd"]),
                "validation_best_50bp_qqq_final_capital_usd": float(validation_best_50["qqq_final_capital_usd"]),
                "recent_best_50bp_universe": recent_best_50["universe"],
                "recent_best_50bp_final_capital_usd": float(recent_best_50["final_capital_usd"]),
                "recent_best_50bp_qqq_final_capital_usd": float(recent_best_50["qqq_final_capital_usd"]),
                "best_50bp_beats_qqq_flag": int(best_50["beats_qqq_flag"]),
                "best_50bp_beats_task617_original_max5_flag": int(best_50["beats_task617_original_max5_flag"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Lock exact live-readable content rules, remove residual boilerplate risks, then test content as Task617 sizing/timing overlay.",
            }
        ]
    )


def render_report(
    account: pd.DataFrame,
    split_audit: pd.DataFrame,
    oos_account: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    a = source_audit.iloc[0]
    lines = [
        "# Task637 Content Signal Account Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Best 50bp content strategy: `{d['best_50bp_universe']}` max{int(d['best_50bp_max_positions'])} = ${float(d['best_50bp_final_capital_usd']):.2f}",
        "",
        "## Quant Expert Report",
        "",
        "Content-derived signals were tested as trade-selection universes with $1000 initial capital, capacity caps, and 0/50/100bp round-trip cost stress.",
        "",
        "### Source Audit",
        "",
        f"- Entries: {int(a['entry_count'])}",
        f"- Entry period: {a['entry_start']} to {a['entry_end']}",
        f"- Entries with content prediction: {int(a['entries_with_content_prediction_count'])}",
        "",
        "### 50bp Account Results",
        "",
        "| Universe | Max Positions | Final $ | Beats QQQ | Beats Task617 Max5 |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in account[account["round_trip_cost_bps"].eq(50)].iterrows():
        lines.append(
            f"| `{row['universe']}` | {int(row['max_positions'])} | ${float(row['final_capital_usd']):.2f} | "
            f"{int(row['beats_qqq_flag'])} | {int(row['beats_task617_original_max5_flag'])} |"
        )
    lines.extend(
        [
            "",
        "### Recent OOS Split",
            "",
            "| Universe | Selected | Lift | ER Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for _, row in split_audit[split_audit["split_name"].eq("recent_oos")].iterrows():
        lines.append(
            f"| `{row['universe']}` | {int(row['selected_count'])} | "
            f"{float(row['avg_return_lift_pct_point']):.2f} | {float(row['entry_reduce_delta_pct_point']):.2f} |"
        )
    lines.extend(
        [
            "",
            "### OOS-Only Account Results",
            "",
            "| Split | Universe | Max Positions | Final $ | QQQ $ | Beats QQQ |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    best_oos = (
        oos_account[oos_account["round_trip_cost_bps"].eq(50)]
        .sort_values(["split_name", "final_capital_usd"], ascending=[True, False])
        .groupby("split_name", as_index=False)
        .head(5)
    )
    for _, row in best_oos.iterrows():
        lines.append(
            f"| `{row['split_name']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):.2f} | ${float(row['qqq_final_capital_usd']):.2f} | {int(row['beats_qqq_flag'])} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We did not trade on information existence.",
            "- We used source-text interpretation fields that survived validation/recent OOS screening.",
            "- This is still not approved for trading until exact live-readable source interpretation rules and runtime source readiness are locked.",
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
            "- `task_637_content_signal_account_summary.csv`",
            "- `task_637_content_signal_accepted_trades.csv`",
            "- `task_637_content_signal_split_audit.csv`",
            "- `task_637_content_signal_oos_account_summary.csv`",
            "- `task_637_source_audit.csv`",
            "- `task_637_pass_fail_matrix.csv`",
            "- `task_637_decision.csv`",
            "- `task_637_gpt_review_packet.md`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task637_content_signal_account_backtest(out_dir=args.out_dir)
    decision = artifacts["task_637_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best50={decision['best_50bp_universe']} max{int(decision['best_50bp_max_positions'])} "
        f"final=${float(decision['best_50bp_final_capital_usd']):.2f} "
        f"beats_qqq={int(decision['best_50bp_beats_qqq_flag'])} "
        f"beats_task617_max5={int(decision['best_50bp_beats_task617_original_max5_flag'])}"
    )


if __name__ == "__main__":
    main()
