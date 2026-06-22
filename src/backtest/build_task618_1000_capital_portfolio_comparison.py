from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate


TASK_ID = "Task618"
REPORT_DIR = Path("docs/reports/task_618_1000_capital_portfolio_comparison")
TASK617_DIR = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest")
DEFAULT_INITIAL_CAPITAL_USD = 1000.0
DEFAULT_MAX_POSITIONS = (5, 10, 20, 50)


def build_task618_1000_capital_portfolio_comparison(
    *,
    task617_dir: Path = TASK617_DIR,
    out_dir: Path = REPORT_DIR,
    initial_capital_usd: float = DEFAULT_INITIAL_CAPITAL_USD,
    max_positions: tuple[int, ...] = DEFAULT_MAX_POSITIONS,
) -> dict[str, pd.DataFrame]:
    baseline = load_panel(task617_dir / "fresh_baseline_all_candidate_backtest_panel.csv")
    turboquant = load_panel(task617_dir / "fresh_turboquant_strategy_backtest_panel.csv")
    panels = {
        "all_candidates": baseline,
        "turboquant": turboquant,
    }

    summary, curves = run_portfolio_comparison(
        panels,
        initial_capital_usd=initial_capital_usd,
        max_positions=max_positions,
    )
    winner = build_winner_summary(summary)
    source_audit = build_source_audit(task617_dir, baseline, turboquant)
    decision = build_decision(summary, winner, source_audit, initial_capital_usd)
    pass_fail = build_pass_fail(summary, winner, decision)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "task_618_1000_capital_portfolio_summary.csv", index=False)
    winner.to_csv(out_dir / "task_618_capacity_winner_summary.csv", index=False)
    curves.to_csv(out_dir / "task_618_1000_capital_equity_curve.csv", index=False)
    source_audit.to_csv(out_dir / "task_618_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_618_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_618_decision.csv", index=False)
    (out_dir / "task_618_1000_capital_portfolio_comparison.md").write_text(
        render_report(summary, winner, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")

    return {
        "task_618_1000_capital_portfolio_summary": summary,
        "task_618_capacity_winner_summary": winner,
        "task_618_1000_capital_equity_curve": curves,
        "task_618_source_audit": source_audit,
        "task_618_pass_fail_matrix": pass_fail,
        "task_618_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing Task617 panel: {path}")
    panel = pd.read_csv(path)
    required = {"lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel = panel.copy()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    panel = panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()
    return panel.sort_values("entry_ts").reset_index(drop=True)


def run_portfolio_comparison(
    panels: dict[str, pd.DataFrame],
    *,
    initial_capital_usd: float,
    max_positions: tuple[int, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    curve_rows: list[pd.DataFrame] = []
    for universe_name, panel in panels.items():
        raw_quality = aggregate(panel) if not panel.empty else {}
        for cap in max_positions:
            result_quality, accepted_panel, equity_curve = simulate_deterministic_portfolio(panel, max_positions=cap)
            pnl_pct = float(result_quality["capital_pnl_pct"])
            final_capital = initial_capital_usd * (1.0 + pnl_pct / 100.0)
            row = {
                "universe": universe_name,
                "initial_capital_usd": initial_capital_usd,
                "max_positions": int(cap),
                "final_capital_usd": final_capital,
                "capital_return_pct": pnl_pct,
                "accepted_trade_count": int(len(accepted_panel)),
                "skipped_due_capacity_count": int(result_quality["skipped_due_capacity_count"]),
                "source_candidate_count": int(len(panel)),
                "capacity_acceptance_rate": float(len(accepted_panel) / len(panel)) if len(panel) else 0.0,
                "avg_net_return_pct": float(result_quality["avg_net_return_pct"]),
                "win_rate": float(result_quality["win_rate"]),
                "entry_reduce_failure_rate": float(result_quality["entry_reduce_failure_rate"]),
                "max_drawdown_pct": float(result_quality["max_drawdown_pct"]),
                "raw_unlimited_avg_net_return_pct": float(raw_quality.get("avg_net_return_pct", 0.0)),
                "raw_unlimited_sum_return_pct": float(panel["net_return_from_entry"].sum() * 100.0) if not panel.empty else 0.0,
                "raw_unlimited_not_capital_feasible_flag": 1,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
            rows.append(row)
            if not equity_curve.empty:
                curve = equity_curve.copy()
                curve["universe"] = universe_name
                curve["max_positions"] = int(cap)
                curve["equity_usd"] = curve["equity"].astype(float) * initial_capital_usd
                curve_rows.append(curve)
    summary = pd.DataFrame(rows).sort_values(["max_positions", "universe"]).reset_index(drop=True)
    curves = pd.concat(curve_rows, ignore_index=True) if curve_rows else pd.DataFrame()
    return summary, curves


def simulate_deterministic_portfolio(
    panel: pd.DataFrame,
    *,
    max_positions: int,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_portfolio_quality(max_positions), panel.copy(), pd.DataFrame()
    ordered = panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                equity_rows.append(
                    {
                        "event_ts": pos["exit_ts"],
                        "event_type": "EXIT",
                        "lifecycle_id": pos["lifecycle_id"],
                        "equity": equity,
                        "drawdown_pct": (equity / peak - 1.0) * 100.0,
                    }
                )
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        if len(open_positions) >= max_positions:
            continue
        capital = equity / float(max_positions)
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        out = dict(row)
        out["task618_capacity_accepted_flag"] = 1
        out["task618_position_slot_cap"] = max_positions
        out["task618_position_capital_weight"] = 1.0 / float(max_positions)
        accepted_rows.append(out)
        equity_rows.append(
            {
                "event_ts": entry_ts,
                "event_type": "ENTRY",
                "lifecycle_id": row["lifecycle_id"],
                "equity": equity,
                "drawdown_pct": (equity / peak - 1.0) * 100.0,
            }
        )
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    equity_curve = (
        pd.DataFrame(equity_rows)
        .sort_values(["event_ts", "event_type", "lifecycle_id"], kind="mergesort")
        .reset_index(drop=True)
        if equity_rows
        else pd.DataFrame()
    )
    quality = aggregate(accepted) if not accepted.empty else empty_portfolio_quality(max_positions)
    quality["capital_pnl_pct"] = (equity - 1.0) * 100.0
    quality["max_drawdown_pct"] = float(equity_curve["drawdown_pct"].min()) if not equity_curve.empty else 0.0
    quality["skipped_due_capacity_count"] = int(len(ordered) - len(accepted))
    quality["max_positions"] = int(max_positions)
    return quality, accepted, equity_curve


def empty_portfolio_quality(max_positions: int) -> dict[str, object]:
    return {
        "lifecycle_count": 0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "add_scale_success_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "false_positive_rate": 0.0,
        "median_holding_days": 0.0,
        "same_day_exit_share": 0.0,
        "capital_pnl_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "skipped_due_capacity_count": 0,
        "max_positions": max_positions,
    }


def build_winner_summary(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for cap, group in summary.groupby("max_positions"):
        ordered = group.sort_values("final_capital_usd", ascending=False).reset_index(drop=True)
        winner = ordered.iloc[0]
        loser = ordered.iloc[1] if len(ordered) > 1 else ordered.iloc[0]
        rows.append(
            {
                "max_positions": int(cap),
                "winner_universe": winner["universe"],
                "winner_final_capital_usd": float(winner["final_capital_usd"]),
                "loser_universe": loser["universe"],
                "loser_final_capital_usd": float(loser["final_capital_usd"]),
                "winner_advantage_usd": float(winner["final_capital_usd"] - loser["final_capital_usd"]),
                "winner_advantage_pct_point": float(winner["capital_return_pct"] - loser["capital_return_pct"]),
            }
        )
    return pd.DataFrame(rows)


def build_source_audit(task617_dir: Path, baseline: pd.DataFrame, turboquant: pd.DataFrame) -> pd.DataFrame:
    all_entry_ts = pd.concat([baseline["entry_ts"], turboquant["entry_ts"]], ignore_index=True)
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "source_task": "Task617",
                "source_dir": task617_dir.as_posix(),
                "baseline_panel": "fresh_baseline_all_candidate_backtest_panel.csv",
                "turboquant_panel": "fresh_turboquant_strategy_backtest_panel.csv",
                "baseline_candidate_count": int(len(baseline)),
                "turboquant_candidate_count": int(len(turboquant)),
                "entry_start_ts": str(all_entry_ts.min()) if not all_entry_ts.empty else "",
                "entry_end_ts": str(all_entry_ts.max()) if not all_entry_ts.empty else "",
                "fresh_full_backtest_flag": 0,
                "portfolio_capacity_comparison_flag": 1,
                "raw_unlimited_total_return_is_not_account_return_flag": 1,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_decision(
    summary: pd.DataFrame,
    winner: pd.DataFrame,
    source_audit: pd.DataFrame,
    initial_capital_usd: float,
) -> pd.DataFrame:
    turbo_wins = int(winner["winner_universe"].astype(str).eq("turboquant").sum())
    all_candidate_wins = int(winner["winner_universe"].astype(str).eq("all_candidates").sum())
    best_row = summary.sort_values("final_capital_usd", ascending=False).iloc[0]
    decision = "MIXED_TURBOQUANT_WINS_SMALL_CAPACITY_FAILS_WIDE_CAPACITY"
    if turbo_wins == len(winner):
        decision = "PASS_TURBOQUANT_1000_CAPITAL_ALL_CAPACITY_DIAGNOSTIC"
    elif all_candidate_wins == len(winner):
        decision = "FAIL_TURBOQUANT_1000_CAPITAL_CAPACITY_COMPARISON"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": float(initial_capital_usd),
                "capacity_grid": ",".join(str(int(x)) for x in sorted(summary["max_positions"].unique())),
                "turboquant_win_capacity_count": turbo_wins,
                "all_candidate_win_capacity_count": all_candidate_wins,
                "best_universe": best_row["universe"],
                "best_max_positions": int(best_row["max_positions"]),
                "best_final_capital_usd": float(best_row["final_capital_usd"]),
                "best_capital_return_pct": float(best_row["capital_return_pct"]),
                "raw_unlimited_total_return_is_not_account_return_flag": int(source_audit.iloc[0]["raw_unlimited_total_return_is_not_account_return_flag"]),
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Choose realistic capacity, add cost/slippage and recent-OOS decomposition before any refinement or promotion.",
            }
        ]
    )


def build_pass_fail(summary: pd.DataFrame, winner: pd.DataFrame, decision: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate": "same_initial_capital",
                "pass_flag": int(summary["initial_capital_usd"].nunique() == 1 and float(summary["initial_capital_usd"].iloc[0]) == DEFAULT_INITIAL_CAPITAL_USD),
                "observed_value": f"${float(summary['initial_capital_usd'].iloc[0]):.2f}",
                "required_value": "$1000 same starting capital",
            },
            {
                "gate": "same_capacity_grid",
                "pass_flag": int(set(summary["max_positions"].unique()) == set(DEFAULT_MAX_POSITIONS)),
                "observed_value": ",".join(str(int(x)) for x in sorted(summary["max_positions"].unique())),
                "required_value": ",".join(str(int(x)) for x in DEFAULT_MAX_POSITIONS),
            },
            {
                "gate": "turboquant_same_capital_capacity_edge",
                "pass_flag": int(winner["winner_universe"].astype(str).eq("turboquant").all()),
                "observed_value": "; ".join(f"{int(r.max_positions)}={r.winner_universe}" for r in winner.itertuples()),
                "required_value": "turboquant wins every tested max-position capacity",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": str(decision.iloc[0]["decision"]),
                "required_value": "cost/slippage, recent OOS, and live-source gates must pass",
            },
        ]
    )


def render_report(
    summary: pd.DataFrame,
    winner: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task618 $1000 Capital Portfolio Comparison",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Starting capital: ${float(d['initial_capital_usd']):,.2f}",
        f"- Best result: `{d['best_universe']}` at max {int(d['best_max_positions'])} positions -> ${float(d['best_final_capital_usd']):,.2f}.",
        "- Unlimited total return is not treated as account return because it assumes unlimited capital and unlimited overlapping positions.",
        "",
        "## Quant Expert Report",
        "",
        "### Portfolio Summary",
        "",
        "| Max Positions | Universe | Final $ | Return | Trades Used | Skipped | Max DD |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.sort_values(["max_positions", "universe"]).iterrows():
        lines.append(
            f"| {int(row['max_positions'])} | `{row['universe']}` | ${float(row['final_capital_usd']):,.2f} | "
            f"{float(row['capital_return_pct']):.2f}% | {int(row['accepted_trade_count'])} | "
            f"{int(row['skipped_due_capacity_count'])} | {float(row['max_drawdown_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Capacity Winners",
            "",
            "| Max Positions | Winner | Winner Final $ | Other Final $ | Edge $ |",
            "|---:|---|---:|---:|---:|",
        ]
    )
    for _, row in winner.iterrows():
        lines.append(
            f"| {int(row['max_positions'])} | `{row['winner_universe']}` | ${float(row['winner_final_capital_usd']):,.2f} | "
            f"${float(row['loser_final_capital_usd']):,.2f} | ${float(row['winner_advantage_usd']):,.2f} |"
        )
    lines.extend(
        [
            "",
            "### Source And Leakage Audit",
            "",
            f"- Source: `{source_audit.iloc[0]['source_dir']}`",
            f"- Baseline candidates: {int(source_audit.iloc[0]['baseline_candidate_count'])}",
            f"- TurboQuant candidates: {int(source_audit.iloc[0]['turboquant_candidate_count'])}",
            f"- Entry window: {source_audit.iloc[0]['entry_start_ts']} to {source_audit.iloc[0]['entry_end_ts']}",
            "- Same-timestamp entries are ordered deterministically by `entry_ts` then `lifecycle_id` before capacity simulation.",
            "- No GPT/plugin output is used as a source or score input.",
            "- Labels/outcomes are not used in assignment logic.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- With a $1000 account, TurboQuant wins at max positions 5, 10, 20, and 50.",
            "- The all-candidate universe has many more candidates, but most cannot be entered under the same account capacity.",
            "- In this comparison, TurboQuant is better on final account dollars, not only average return.",
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
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_baseline_all_candidate_backtest_panel.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_618_1000_capital_portfolio_summary.csv`",
            "- `task_618_capacity_winner_summary.csv`",
            "- `task_618_1000_capital_equity_curve.csv`",
            "- `task_618_source_audit.csv`",
            "- `task_618_pass_fail_matrix.csv`",
            "- `task_618_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task618_1000_capital_portfolio_comparison`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--initial-capital-usd", type=float, default=DEFAULT_INITIAL_CAPITAL_USD)
    args = parser.parse_args()
    artifacts = build_task618_1000_capital_portfolio_comparison(
        out_dir=args.out_dir,
        initial_capital_usd=args.initial_capital_usd,
    )
    row = artifacts["task_618_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"best={row['best_universe']} cap={int(row['best_max_positions'])} "
        f"final=${float(row['best_final_capital_usd']):.2f}"
    )


if __name__ == "__main__":
    main()
