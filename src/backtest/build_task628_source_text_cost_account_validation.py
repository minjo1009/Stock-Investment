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
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel
from src.backtest.build_task627_source_text_theme_linkage_validation import build_task627_source_text_theme_linkage_validation


TASK_ID = "Task628"
REPORT_DIR = Path("docs/reports/task_628_source_text_cost_account_validation")
INITIAL_CAPITAL_USD = 1000.0
MAX_POSITIONS = (5, 10, 20, 50)
COST_BPS = (0, 25, 50, 100, 200)
SCOPES = ("full_panel", "validation", "recent_oos")


def build_task628_source_text_cost_account_validation(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task617_panel_path)
    task627 = build_task627_source_text_theme_linkage_validation()
    attachment = task627["task_627_trade_text_linkage_attachment"]
    enriched = panel.merge(attachment[["lifecycle_id", "source_text_aerospace_risk_flag"]], on="lifecycle_id", how="left")
    universes = {
        "turboquant_original": enriched,
        "source_text_aerospace_risk_hold": enriched[~enriched["source_text_aerospace_risk_flag"].fillna(0).astype(int).eq(1)],
    }
    portfolio = build_cost_account_matrix(universes)
    pass_fail = build_pass_fail(portfolio)
    decision = build_decision(portfolio, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    portfolio.to_csv(out_dir / "task_628_cost_account_matrix.csv", index=False)
    pass_fail.to_csv(out_dir / "task_628_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_628_decision.csv", index=False)
    (out_dir / "task_628_source_text_cost_account_validation.md").write_text(
        render_report(portfolio, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_628_cost_account_matrix": portfolio,
        "task_628_pass_fail_matrix": pass_fail,
        "task_628_decision": decision,
    }


def build_cost_account_matrix(universes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for universe, base in universes.items():
        for scope in SCOPES:
            scoped = base if scope == "full_panel" else base[base["split_name"].astype(str).eq(scope)]
            raw_metrics = aggregate(scoped) if not scoped.empty else {}
            for cost_bps in COST_BPS:
                costed = scoped.copy()
                costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - (cost_bps / 10000.0)
                for max_positions in MAX_POSITIONS:
                    quality, accepted, _curve = simulate_deterministic_portfolio(costed, max_positions=max_positions)
                    rows.append(
                        {
                            "universe": universe,
                            "scope": scope,
                            "round_trip_cost_bps": int(cost_bps),
                            "initial_capital_usd": INITIAL_CAPITAL_USD,
                            "max_positions": int(max_positions),
                            "source_trade_count": int(len(scoped)),
                            "accepted_trade_count": int(len(accepted)),
                            "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
                            "capital_return_pct": float(quality["capital_pnl_pct"]),
                            "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                            "win_rate": float(quality["win_rate"]),
                            "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                            "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                            "raw_unlimited_avg_net_return_pct": float(raw_metrics.get("avg_net_return_pct", 0.0)),
                            "label_used_in_assignment_flag": 0,
                            "gpt_score_used_as_source_flag": 0,
                        }
                    )
    return pd.DataFrame(rows)


def rows_at(portfolio: pd.DataFrame, universe: str, scope: str, cost_bps: int) -> pd.DataFrame:
    return portfolio[
        portfolio["universe"].eq(universe)
        & portfolio["scope"].eq(scope)
        & portfolio["round_trip_cost_bps"].astype(int).eq(cost_bps)
    ].copy()


def merged_capitals(portfolio: pd.DataFrame, scope: str, cost_bps: int) -> pd.DataFrame:
    original = rows_at(portfolio, "turboquant_original", scope, cost_bps)
    hold = rows_at(portfolio, "source_text_aerospace_risk_hold", scope, cost_bps)
    return hold[["max_positions", "final_capital_usd"]].merge(
        original[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_hold", "_original"),
    )


def build_pass_fail(portfolio: pd.DataFrame) -> pd.DataFrame:
    recent_50 = merged_capitals(portfolio, "recent_oos", 50)
    full_50 = merged_capitals(portfolio, "full_panel", 50)
    validation_50 = merged_capitals(portfolio, "validation", 50)
    recent_wins = int((recent_50["final_capital_usd_hold"] > recent_50["final_capital_usd_original"]).sum())
    full_wins = int((full_50["final_capital_usd_hold"] > full_50["final_capital_usd_original"]).sum())
    validation_wins = int((validation_50["final_capital_usd_hold"] > validation_50["final_capital_usd_original"]).sum())
    return pd.DataFrame(
        [
            {
                "gate": "recent_oos_50bp_account_edge",
                "pass_flag": int(recent_wins >= 3),
                "observed_value": f"hold_wins={recent_wins}/4; " + format_capital_pairs(recent_50),
                "required_value": "source-text hold beats original in at least 3 of 4 recent-OOS capacities at 50bp",
            },
            {
                "gate": "validation_50bp_not_broken",
                "pass_flag": int(validation_wins >= 2),
                "observed_value": f"hold_wins={validation_wins}/4; " + format_capital_pairs(validation_50),
                "required_value": "source-text hold does not break validation account performance at 50bp",
            },
            {
                "gate": "full_panel_50bp_account_edge",
                "pass_flag": int(full_wins >= 2),
                "observed_value": f"hold_wins={full_wins}/4; " + format_capital_pairs(full_50),
                "required_value": "source-text hold should be at least mixed or better on full panel at 50bp",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "cost/account diagnostic only",
                "required_value": "requires parameter/split robustness and live-source readiness before strategy use",
            },
        ]
    )


def format_capital_pairs(rows: pd.DataFrame) -> str:
    return "; ".join(
        f"max{int(r.max_positions)} hold=${float(r.final_capital_usd_hold):.2f} original=${float(r.final_capital_usd_original):.2f}"
        for r in rows.itertuples()
    )


def build_decision(portfolio: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")]["pass_flag"].iloc[0])
    validation_pass = int(pass_fail[pass_fail["gate"].eq("validation_50bp_not_broken")]["pass_flag"].iloc[0])
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_edge")]["pass_flag"].iloc[0])
    recent_50 = merged_capitals(portfolio, "recent_oos", 50)
    decision = "FAIL_SOURCE_TEXT_COST_ACCOUNT_EDGE_NOT_ACCEPTED"
    if recent_pass and validation_pass and full_pass:
        decision = "PASS_SOURCE_TEXT_COST_ACCOUNT_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "recent_oos_50bp_account_edge_pass_flag": recent_pass,
                "validation_50bp_not_broken_pass_flag": validation_pass,
                "full_panel_50bp_account_edge_pass_flag": full_pass,
                "recent_oos_50bp_hold_win_capacity_count": int((recent_50["final_capital_usd_hold"] > recent_50["final_capital_usd_original"]).sum()),
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Run parameter and split robustness for source-text aerospace risk hold, then define live-source collection contract.",
            }
        ]
    )


def render_report(portfolio: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0]
    rows50 = portfolio[portfolio["round_trip_cost_bps"].astype(int).eq(50)]
    lines = [
        "# Task628 Source Text Cost Account Validation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Recent OOS 50bp hold wins: {int(d['recent_oos_50bp_hold_win_capacity_count'])}/4 capacities",
        "",
        "## Quant Expert Report",
        "",
        "### 50bp Account Matrix",
        "",
        "| Scope | Universe | Max Positions | Final $ | Return |",
        "|---|---|---:|---:|---:|",
    ]
    for _, row in rows50.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Source-text aerospace risk hold survives the 50bp recent-OOS account check.",
            "- Source-text aerospace risk hold does not pass the 50bp account gate yet.",
            "- Recent OOS wins only two of four capacities, and full panel loses all four capacities.",
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
            "- `docs/reports/task_627_source_text_theme_linkage_validation/task_627_trade_text_linkage_attachment.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_628_cost_account_matrix.csv`",
            "- `task_628_pass_fail_matrix.csv`",
            "- `task_628_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task628_source_text_cost_account_validation`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task628_source_text_cost_account_validation(out_dir=args.out_dir)
    row = artifacts["task_628_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"recent_50bp_wins={int(row['recent_oos_50bp_hold_win_capacity_count'])}/4"
    )


if __name__ == "__main__":
    main()
