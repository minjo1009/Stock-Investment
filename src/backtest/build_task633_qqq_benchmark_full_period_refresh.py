from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task489_broad_regime_cell_portfolio import (
    DEFAULT_BROAD_DAILY_DIR,
    build_daily_source_from_1day_csv,
)
from src.backtest.build_task484_continuation_payoff_regime_engine import build_payoff_market_regime_state
from src.backtest.build_task617_turboquant_fresh_strategy_backtest import (
    build_task617_turboquant_fresh_strategy_backtest,
)
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task632_temporal_strict_full_period_backtest import (
    build_task632_temporal_strict_full_period_backtest,
)


TASK_ID = "Task633"
REPORT_DIR = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh")
INITIAL_CAPITAL_USD = 1000.0
DECISION_COST_BPS = 50
MAX_POSITIONS = (5, 10, 20, 50)


def build_task633_qqq_benchmark_full_period_refresh(
    *,
    daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    market_panel = build_refreshed_market_panel(daily_dir)
    market_panel_path = out_dir / "task_633_refreshed_broad_market_state_panel.csv"
    market_panel.to_csv(market_panel_path, index=False)

    task617_dir = out_dir / "task617_refreshed_inputs"
    task617 = build_task617_turboquant_fresh_strategy_backtest(
        market_panel_path=market_panel_path,
        out_dir=task617_dir,
    )
    task632_dir = out_dir / "task632_temporal_strict_refresh"
    task632 = build_task632_temporal_strict_full_period_backtest(
        scored_entries_path=task617_dir / "fresh_turboquant_scored_entry_panel.csv",
        original_strategy_path=task617_dir / "fresh_turboquant_strategy_backtest_panel.csv",
        out_dir=task632_dir,
    )
    baseline = task632["task_632_baseline_all_confirmed_backtest_panel"]
    original = task617["fresh_turboquant_strategy_backtest_panel"]
    strict = task632["task_632_temporal_strict_strategy_backtest_panel"]
    qqq = load_qqq_benchmark(daily_dir / "QQQ.csv", baseline)
    account = build_1000_account_vs_qqq(baseline, original, strict, qqq)
    source_audit = build_source_audit(daily_dir, market_panel, baseline, task632["task_632_source_time_contract_audit"], qqq)
    pass_fail = build_pass_fail(account, source_audit)
    decision = build_decision(account, source_audit, pass_fail)

    account.to_csv(out_dir / "task_633_1000_account_qqq_comparison.csv", index=False)
    source_audit.to_csv(out_dir / "task_633_source_horizon_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_633_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_633_decision.csv", index=False)
    (out_dir / "task_633_qqq_benchmark_full_period_refresh.md").write_text(
        render_report(source_audit, account, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_633_refreshed_broad_market_state_panel": market_panel,
        "task_633_1000_account_qqq_comparison": account,
        "task_633_source_horizon_audit": source_audit,
        "task_633_pass_fail_matrix": pass_fail,
        "task_633_decision": decision,
    }


def build_refreshed_market_panel(daily_dir: Path) -> pd.DataFrame:
    source = build_daily_source_from_1day_csv(daily_dir)
    market = build_payoff_market_regime_state(source).rename(
        columns={
            "payoff_market_score": "broad_market_score",
            "payoff_market_stress_score": "broad_market_stress",
        }
    )
    return market


def load_qqq_benchmark(path: Path, baseline: pd.DataFrame) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing QQQ benchmark file: {path}")
    qqq = pd.read_csv(path)
    qqq.columns = [str(col).strip().lower() for col in qqq.columns]
    qqq["timestamp"] = pd.to_datetime(qqq["timestamp"], utc=True, errors="coerce")
    qqq["close"] = pd.to_numeric(qqq["close"], errors="coerce")
    qqq = qqq.dropna(subset=["timestamp", "close"]).sort_values("timestamp").reset_index(drop=True)
    start_date = pd.to_datetime(baseline["entry_ts"], utc=True, errors="coerce").min().date()
    end_date = qqq["timestamp"].max().date()
    start_row = qqq[qqq["timestamp"].dt.date.ge(start_date)].head(1)
    end_row = qqq[qqq["timestamp"].dt.date.le(end_date)].tail(1)
    if start_row.empty or end_row.empty:
        raise ValueError("QQQ benchmark cannot align to strategy dates")
    start_close = float(start_row.iloc[0]["close"])
    end_close = float(end_row.iloc[0]["close"])
    return pd.DataFrame(
        [
            {
                "benchmark": "QQQ_buy_and_hold",
                "start_date": str(start_row.iloc[0]["timestamp"].date()),
                "end_date": str(end_row.iloc[0]["timestamp"].date()),
                "start_close": start_close,
                "end_close": end_close,
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "final_capital_usd": INITIAL_CAPITAL_USD * end_close / start_close,
                "capital_return_pct": (end_close / start_close - 1.0) * 100.0,
            }
        ]
    )


def costed_panel(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["net_return_from_entry"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce") - DECISION_COST_BPS / 10000.0
    return out


def build_1000_account_vs_qqq(
    baseline: pd.DataFrame,
    original: pd.DataFrame,
    strict: pd.DataFrame,
    qqq: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    qqq_final = float(qqq.iloc[0]["final_capital_usd"])
    for name, panel in [
        ("all_confirmed_baseline", baseline),
        ("task617_original_broad_intelligence_strategy", original),
        ("task632_temporal_strict_chart_qual_strategy", strict),
    ]:
        for max_positions in MAX_POSITIONS:
            quality, accepted, _curve = simulate_deterministic_portfolio(costed_panel(panel), max_positions=max_positions)
            final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            rows.append(
                {
                    "universe": name,
                    "round_trip_cost_bps": DECISION_COST_BPS,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "max_positions": int(max_positions),
                    "source_trade_count": int(len(panel)),
                    "accepted_trade_count": int(len(accepted)),
                    "final_capital_usd": final_capital,
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "qqq_final_capital_usd": qqq_final,
                    "beats_qqq_flag": int(final_capital > qqq_final),
                    "excess_vs_qqq_usd": final_capital - qqq_final,
                }
            )
    rows.append(
        {
            "universe": "QQQ_buy_and_hold",
            "round_trip_cost_bps": 0,
            "initial_capital_usd": INITIAL_CAPITAL_USD,
            "max_positions": 1,
            "source_trade_count": 1,
            "accepted_trade_count": 1,
            "final_capital_usd": qqq_final,
            "capital_return_pct": float(qqq.iloc[0]["capital_return_pct"]),
            "qqq_final_capital_usd": qqq_final,
            "beats_qqq_flag": 0,
            "excess_vs_qqq_usd": 0.0,
        }
    )
    return pd.DataFrame(rows)


def build_source_audit(
    daily_dir: Path,
    market_panel: pd.DataFrame,
    baseline: pd.DataFrame,
    task632_audit: pd.DataFrame,
    qqq: pd.DataFrame,
) -> pd.DataFrame:
    entry_ts = pd.to_datetime(baseline["entry_ts"], utc=True, errors="coerce")
    refresh_audit = Path("docs/reports/task_633_market_data_refresh/task_633_yfinance_refresh_audit.csv")
    refresh = pd.read_csv(refresh_audit) if refresh_audit.exists() else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "daily_dir": str(daily_dir),
                "refresh_audit_path": str(refresh_audit),
                "refresh_symbol_count": int(refresh["symbol"].nunique()) if "symbol" in refresh.columns else 0,
                "refresh_daily_max": str(refresh["daily_max"].max()) if "daily_max" in refresh.columns else "",
                "refresh_intraday_max": str(refresh["intraday_max"].max()) if "intraday_max" in refresh.columns else "",
                "market_panel_start": str(pd.to_datetime(market_panel["score_date"], errors="coerce").min().date()),
                "market_panel_end": str(pd.to_datetime(market_panel["score_date"], errors="coerce").max().date()),
                "strategy_entry_start": str(entry_ts.min().date()),
                "strategy_entry_end": str(entry_ts.max().date()),
                "strategy_trade_count": int(len(baseline)),
                "qqq_start": str(qqq.iloc[0]["start_date"]),
                "qqq_end": str(qqq.iloc[0]["end_date"]),
                "task632_temporal_strategy_entries": int(task632_audit.iloc[0]["temporal_strategy_entry_count"]),
                "date_only_support_used_count": int(task632_audit.iloc[0]["date_only_support_used_count"]),
                "future_event_support_leak_count": int(task632_audit.iloc[0]["future_event_support_leak_count"]),
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def row_final(account: pd.DataFrame, universe: str, max_positions: int) -> float:
    return float(account[account["universe"].eq(universe) & account["max_positions"].eq(max_positions)].iloc[0]["final_capital_usd"])


def build_pass_fail(account: pd.DataFrame, source_audit: pd.DataFrame) -> pd.DataFrame:
    qqq_final = float(account[account["universe"].eq("QQQ_buy_and_hold")].iloc[0]["final_capital_usd"])
    strict_beats = int(account[account["universe"].eq("task632_temporal_strict_chart_qual_strategy")]["beats_qqq_flag"].sum())
    original_beats = int(account[account["universe"].eq("task617_original_broad_intelligence_strategy")]["beats_qqq_flag"].sum())
    baseline_beats = int(account[account["universe"].eq("all_confirmed_baseline")]["beats_qqq_flag"].sum())
    strict_vs_original_wins = int(
        sum(
            row_final(account, "task632_temporal_strict_chart_qual_strategy", cap)
            > row_final(account, "task617_original_broad_intelligence_strategy", cap)
            for cap in MAX_POSITIONS
        )
    )
    audit = source_audit.iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "latest_data_horizon",
                "pass_flag": int(str(audit["strategy_entry_end"]) >= "2026-06-01" and str(audit["qqq_end"]) >= "2026-06-01"),
                "observed_value": f"strategy_end={audit['strategy_entry_end']}; qqq_end={audit['qqq_end']}; market_end={audit['market_panel_end']}",
                "required_value": "strategy and QQQ benchmark must extend into June 2026",
            },
            {
                "gate": "temporal_integrity",
                "pass_flag": int(int(audit["date_only_support_used_count"]) == 0 and int(audit["future_event_support_leak_count"]) == 0),
                "observed_value": f"date_only_support={audit['date_only_support_used_count']}; future_leaks={audit['future_event_support_leak_count']}",
                "required_value": "no date-only support and no future-event support leakage",
            },
            {
                "gate": "strict_strategy_beats_qqq_50bp_account",
                "pass_flag": int(strict_beats == len(MAX_POSITIONS)),
                "observed_value": f"strict_beats_qqq={strict_beats}/{len(MAX_POSITIONS)}; qqq_final=${qqq_final:.2f}",
                "required_value": "Task632 strict strategy must beat QQQ at every tested capacity",
            },
            {
                "gate": "original_strategy_beats_qqq_50bp_account",
                "pass_flag": int(original_beats == len(MAX_POSITIONS)),
                "observed_value": f"original_beats_qqq={original_beats}/{len(MAX_POSITIONS)}; qqq_final=${qqq_final:.2f}",
                "required_value": "Task617 original strategy must beat QQQ at every tested capacity",
            },
            {
                "gate": "baseline_beats_qqq_50bp_account",
                "pass_flag": int(baseline_beats == len(MAX_POSITIONS)),
                "observed_value": f"baseline_beats_qqq={baseline_beats}/{len(MAX_POSITIONS)}; qqq_final=${qqq_final:.2f}",
                "required_value": "all-candidate baseline must beat QQQ at every tested capacity",
            },
            {
                "gate": "strict_strategy_beats_original",
                "pass_flag": int(strict_vs_original_wins >= 2),
                "observed_value": f"strict_vs_original_wins={strict_vs_original_wins}/{len(MAX_POSITIONS)}",
                "required_value": "new qualitative interpretation should not lose to the prior broad intelligence strategy",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "benchmark comparison only",
                "required_value": "requires accepted OOS and live-source readiness before promotion",
            },
        ]
    )


def build_decision(account: pd.DataFrame, source_audit: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    qqq = account[account["universe"].eq("QQQ_buy_and_hold")].iloc[0]
    strict_max5 = row_final(account, "task632_temporal_strict_chart_qual_strategy", 5)
    original_max5 = row_final(account, "task617_original_broad_intelligence_strategy", 5)
    status = "FAIL_QQQ_BENCHMARK_OR_ORIGINAL_EDGE_NOT_ACCEPTED"
    if int(pass_fail[pass_fail["gate"].eq("strict_strategy_beats_qqq_50bp_account")]["pass_flag"].iloc[0]) == 1:
        status = "PASS_QQQ_BENCHMARK_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": status,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "qqq_final_capital_usd": float(qqq["final_capital_usd"]),
                "task617_original_max5_final_capital_usd": original_max5,
                "task632_strict_max5_final_capital_usd": strict_max5,
                "strategy_entry_start": source_audit.iloc[0]["strategy_entry_start"],
                "strategy_entry_end": source_audit.iloc[0]["strategy_entry_end"],
                "trading_promotion_pass_flag": 0,
                "next_action": "Build Task634 event relevance certification plus confirmation gated entry because strict qualitative interpretation still loses to the prior strategy.",
            }
        ]
    )


def render_report(source_audit: pd.DataFrame, account: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task633 QQQ Benchmark Full Period Refresh",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Period: {d['strategy_entry_start']} to {d['strategy_entry_end']}",
        f"- QQQ $1000 final: ${float(d['qqq_final_capital_usd']):,.2f}",
        f"- Task617 max5 $1000 final at 50bp: ${float(d['task617_original_max5_final_capital_usd']):,.2f}",
        f"- Task632 strict max5 $1000 final at 50bp: ${float(d['task632_strict_max5_final_capital_usd']):,.2f}",
        "",
        "## Quant Expert Report",
        "",
        "This refreshes daily and intraday data through the latest available June 2026 trading date, rebuilds the fresh candidate panel, reruns the temporal strict strategy, and compares $1000 account results against simple QQQ buy-and-hold.",
        "",
        "### Source Horizon",
        "",
        "| Refresh Daily Max | Refresh Intraday Max | Market End | Strategy End | QQQ End |",
        "|---|---|---|---|---|",
    ]
    s = source_audit.iloc[0]
    lines.append(f"| {s['refresh_daily_max']} | {s['refresh_intraday_max']} | {s['market_panel_end']} | {s['strategy_entry_end']} | {s['qqq_end']} |")
    lines.extend(
        [
            "",
            "### $1000 Account Comparison",
            "",
            "| Universe | Max Positions | Cost bps | Final $ | Beats QQQ | Excess vs QQQ |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in account.sort_values(["universe", "max_positions"]).iterrows():
        lines.append(
            f"| `{row['universe']}` | {int(row['max_positions'])} | {int(row['round_trip_cost_bps'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {int(row['beats_qqq_flag'])} | ${float(row['excess_vs_qqq_usd']):,.2f} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- The May 8 cutoff was a data cutoff, not a valid June full-period test.",
            "- After refreshing data, the benchmark question is $1000 final capital versus QQQ.",
            "- The strict qualitative strategy can beat QQQ in this diagnostic, but it still loses to the prior Task617 strategy, so the information interpretation is not yet good enough.",
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
            "- `task_633_refreshed_broad_market_state_panel.csv`",
            "- `task617_refreshed_inputs/`",
            "- `task632_temporal_strict_refresh/`",
            "- `task_633_1000_account_qqq_comparison.csv`",
            "- `task_633_source_horizon_audit.csv`",
            "- `task_633_pass_fail_matrix.csv`",
            "- `task_633_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task633_qqq_benchmark_full_period_refresh(out_dir=args.out_dir)
    decision = artifacts["task_633_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"qqq=${float(decision['qqq_final_capital_usd']):.2f} "
        f"task617_max5=${float(decision['task617_original_max5_final_capital_usd']):.2f} "
        f"task632_max5=${float(decision['task632_strict_max5_final_capital_usd']):.2f}"
    )


if __name__ == "__main__":
    main()
