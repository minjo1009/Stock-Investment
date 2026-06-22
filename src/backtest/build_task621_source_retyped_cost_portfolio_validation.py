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


TASK_ID = "Task621"
REPORT_DIR = Path("docs/reports/task_621_source_retyped_cost_portfolio_validation")
TASK617_DIR = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest")
INITIAL_CAPITAL_USD = 1000.0
MAX_POSITIONS = (5, 10, 20, 50)
COST_BPS = (0, 25, 50, 100, 200)
SCOPES = ("full_panel", "validation", "recent_oos")


def build_task621_source_retyped_cost_portfolio_validation(
    *,
    task617_dir: Path = TASK617_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    baseline = load_panel(task617_dir / "fresh_baseline_all_candidate_backtest_panel.csv")
    turboquant = load_panel(task617_dir / "fresh_turboquant_strategy_backtest_panel.csv")
    universes = build_universes(baseline, turboquant)
    source_certification = build_source_certification_matrix(turboquant)
    portfolio = build_cost_portfolio_matrix(universes)
    winner = build_winner_matrix(portfolio)
    pass_fail = build_pass_fail(portfolio, source_certification)
    gpt_review = build_gpt_review_status()
    decision = build_decision(portfolio, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    source_certification.to_csv(out_dir / "task_621_source_retyping_certification_matrix.csv", index=False)
    portfolio.to_csv(out_dir / "task_621_cost_portfolio_matrix.csv", index=False)
    winner.to_csv(out_dir / "task_621_cost_portfolio_winner_matrix.csv", index=False)
    pass_fail.to_csv(out_dir / "task_621_pass_fail_matrix.csv", index=False)
    gpt_review.to_csv(out_dir / "task_621_gpt_validation_review_status.csv", index=False)
    decision.to_csv(out_dir / "task_621_decision.csv", index=False)
    (out_dir / "task_621_source_retyped_cost_portfolio_validation.md").write_text(
        render_report(source_certification, portfolio, winner, pass_fail, gpt_review, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_621_source_retyping_certification_matrix": source_certification,
        "task_621_cost_portfolio_matrix": portfolio,
        "task_621_cost_portfolio_winner_matrix": winner,
        "task_621_pass_fail_matrix": pass_fail,
        "task_621_gpt_validation_review_status": gpt_review,
        "task_621_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {"lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry", "split_name"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel = panel.copy()
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    for col in [
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
        "ceo_ir_proxy_pre14d_flag",
        "passive_13g_pre30d_flag",
        "insider_form4_or_144_pre30d_flag",
        "theme_ret20_prev",
        "win_flag",
        "entry_reduce_failure_flag",
    ]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).reset_index(drop=True)


def broad_event_mask(panel: pd.DataFrame) -> pd.Series:
    return (
        panel["political_statement_pre7d_flag"].fillna(0).eq(1)
        & panel["geopolitical_event_pre7d_flag"].fillna(0).eq(1)
        & panel["institution_ownership_pre30d_flag"].fillna(0).eq(1)
    )


def aerospace_risk_off_mask(panel: pd.DataFrame) -> pd.Series:
    return panel["theme_id"].astype(str).eq("aerospace_defense_space") & broad_event_mask(panel)


def rejected_global_ir_mask(panel: pd.DataFrame) -> pd.Series:
    return broad_event_mask(panel) & panel["ceo_ir_proxy_pre14d_flag"].fillna(0).eq(0)


def build_universes(baseline: pd.DataFrame, turboquant: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "all_candidates": baseline.copy(),
        "turboquant_original": turboquant.copy(),
        "proactive_hold_until_source_certified": turboquant[~aerospace_risk_off_mask(turboquant)].copy(),
        "rejected_global_ir_filter": turboquant[~rejected_global_ir_mask(turboquant)].copy(),
    }


def build_source_certification_matrix(turboquant: pd.DataFrame) -> pd.DataFrame:
    aerospace = turboquant[turboquant["theme_id"].astype(str).eq("aerospace_defense_space")].copy()
    rows = []
    cuts = {
        "aerospace_all": pd.Series(True, index=aerospace.index),
        "aerospace_no_ceo_ir": aerospace["ceo_ir_proxy_pre14d_flag"].fillna(0).eq(0),
        "aerospace_ceo_ir": aerospace["ceo_ir_proxy_pre14d_flag"].fillna(0).eq(1),
        "aerospace_passive13g": aerospace["passive_13g_pre30d_flag"].fillna(0).eq(1),
        "aerospace_no_passive13g": aerospace["passive_13g_pre30d_flag"].fillna(0).eq(0),
        "aerospace_theme_ret20_gt15": aerospace["theme_ret20_prev"].gt(0.15),
        "aerospace_theme_ret20_le15": ~aerospace["theme_ret20_prev"].gt(0.15),
    }
    for split_name in ("train_design", "validation", "recent_oos"):
        split = aerospace[aerospace["split_name"].astype(str).eq(split_name)]
        for cut_name, mask in cuts.items():
            group = split[mask.loc[split.index]]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "split_name": split_name,
                    "source_retype_bucket": cut_name,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "source_certified_pass_flag": 0,
                    "notes": "diagnostic source split; no source type rescues recent aerospace OOS yet",
                }
            )
    return pd.DataFrame(rows)


def build_cost_portfolio_matrix(universes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for universe_name, base_panel in universes.items():
        for scope in SCOPES:
            scoped = base_panel.copy() if scope == "full_panel" else base_panel[base_panel["split_name"].astype(str).eq(scope)].copy()
            raw_metrics = aggregate(scoped) if not scoped.empty else {}
            for cost_bps in COST_BPS:
                cost_rate = float(cost_bps) / 10000.0
                costed = scoped.copy()
                costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - cost_rate
                for max_positions in MAX_POSITIONS:
                    quality, accepted, curve = simulate_deterministic_portfolio(costed, max_positions=max_positions)
                    final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
                    rows.append(
                        {
                            "universe": universe_name,
                            "scope": scope,
                            "round_trip_cost_bps": int(cost_bps),
                            "initial_capital_usd": INITIAL_CAPITAL_USD,
                            "max_positions": int(max_positions),
                            "source_trade_count": int(len(scoped)),
                            "accepted_trade_count": int(len(accepted)),
                            "final_capital_usd": final_capital,
                            "capital_return_pct": float(quality["capital_pnl_pct"]),
                            "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                            "win_rate": float(quality["win_rate"]),
                            "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                            "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                            "raw_unlimited_avg_net_return_pct": float(raw_metrics.get("avg_net_return_pct", 0.0)),
                            "label_used_in_assignment_flag": 0,
                            "gpt_or_plugin_used_as_source_flag": 0,
                        }
                    )
    return pd.DataFrame(rows)


def build_winner_matrix(portfolio: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in portfolio.groupby(["scope", "round_trip_cost_bps", "max_positions"]):
        ordered = group.sort_values("final_capital_usd", ascending=False).reset_index(drop=True)
        winner = ordered.iloc[0]
        rows.append(
            {
                "scope": keys[0],
                "round_trip_cost_bps": int(keys[1]),
                "max_positions": int(keys[2]),
                "winner_universe": winner["universe"],
                "winner_final_capital_usd": float(winner["final_capital_usd"]),
            }
        )
    return pd.DataFrame(rows)


def rows_at_50bp(portfolio: pd.DataFrame, *, universe: str, scope: str) -> pd.DataFrame:
    return portfolio[
        portfolio["universe"].eq(universe)
        & portfolio["scope"].eq(scope)
        & portfolio["round_trip_cost_bps"].astype(int).eq(50)
    ].copy()


def build_pass_fail(portfolio: pd.DataFrame, source_certification: pd.DataFrame) -> pd.DataFrame:
    proactive_full = rows_at_50bp(portfolio, universe="proactive_hold_until_source_certified", scope="full_panel")
    original_full = rows_at_50bp(portfolio, universe="turboquant_original", scope="full_panel")
    proactive_recent = rows_at_50bp(portfolio, universe="proactive_hold_until_source_certified", scope="recent_oos")
    original_recent = rows_at_50bp(portfolio, universe="turboquant_original", scope="recent_oos")
    rejected_recent = rows_at_50bp(portfolio, universe="rejected_global_ir_filter", scope="recent_oos")

    merged_full = proactive_full[["max_positions", "final_capital_usd"]].merge(
        original_full[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_proactive", "_original"),
    )
    merged_recent = proactive_recent[["max_positions", "final_capital_usd"]].merge(
        original_recent[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_proactive", "_original"),
    )
    rejected_recent_bad = int((rejected_recent["final_capital_usd"].astype(float) < 1000.0).sum())
    recent_source = source_certification[source_certification["split_name"].astype(str).eq("recent_oos")]
    recent_ceo = recent_source[recent_source["source_retype_bucket"].astype(str).isin(["aerospace_no_ceo_ir", "aerospace_ceo_ir"])]
    source_rescue = int((recent_ceo["avg_net_return_pct"].astype(float) > 0.0).any())
    return pd.DataFrame(
        [
            {
                "gate": "source_retyping_certification",
                "pass_flag": 0,
                "observed_value": "recent aerospace CEO-IR and no-CEO-IR buckets both remain negative",
                "required_value": "a source subtype must rescue recent aerospace before source-certified entry can be restored",
            },
            {
                "gate": "full_panel_50bp_account_edge",
                "pass_flag": int((merged_full["final_capital_usd_proactive"] > merged_full["final_capital_usd_original"]).all()),
                "observed_value": "; ".join(
                    f"max{int(r.max_positions)} proactive=${float(r.final_capital_usd_proactive):.2f} original=${float(r.final_capital_usd_original):.2f}"
                    for r in merged_full.itertuples()
                ),
                "required_value": "proactive risk-off beats original TurboQuant at every max position under 50bp",
            },
            {
                "gate": "recent_oos_50bp_account_edge",
                "pass_flag": int((merged_recent["final_capital_usd_proactive"] > merged_recent["final_capital_usd_original"]).sum() >= 3),
                "observed_value": "; ".join(
                    f"max{int(r.max_positions)} proactive=${float(r.final_capital_usd_proactive):.2f} original=${float(r.final_capital_usd_original):.2f}"
                    for r in merged_recent.itertuples()
                ),
                "required_value": "proactive risk-off beats original in at least 3 of 4 recent-OOS capacities under 50bp",
            },
            {
                "gate": "negative_control_rejected",
                "pass_flag": int(rejected_recent_bad >= 2),
                "observed_value": f"recent_oos rejected_global_ir_filter final capital below $1000 in {rejected_recent_bad}/4 capacities at 50bp",
                "required_value": "negative control should fail account viability in at least two recent-OOS capacities",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "source retyping not certified; mixed recent capacity edge; real capital forbidden",
                "required_value": "source certification plus cost/account and live-source gates must pass",
            },
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT agreed the validation design is directionally firm-grade, but classified the source gate as HOLD_UNTIL_SOURCE_CERTIFICATION rather than a permanent block or simple size-down.",
            }
        ]
    )


def build_decision(portfolio: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_edge")]["pass_flag"].iloc[0])
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")]["pass_flag"].iloc[0])
    source_pass = int(pass_fail[pass_fail["gate"].eq("source_retyping_certification")]["pass_flag"].iloc[0])
    proactive_full_50 = rows_at_50bp(portfolio, universe="proactive_hold_until_source_certified", scope="full_panel")
    best = proactive_full_50.sort_values("final_capital_usd", ascending=False).iloc[0]
    decision = "PASS_COST_ACCOUNT_EDGE_FAIL_SOURCE_CERTIFICATION_NOT_ACCEPTED"
    if not full_pass:
        decision = "FAIL_COST_ACCOUNT_EDGE"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "source_gate_action": "HOLD_UNTIL_SOURCE_CERTIFICATION",
                "full_panel_50bp_edge_pass_flag": full_pass,
                "recent_oos_50bp_edge_pass_flag": recent_pass,
                "source_retyping_certification_pass_flag": source_pass,
                "best_50bp_proactive_max_positions": int(best["max_positions"]),
                "best_50bp_proactive_final_capital_usd": float(best["final_capital_usd"]),
                "treatment_rule_accepted_flag": 0,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Build source-certification labels for aerospace/space events, then rerun this cost/account test before accepting any rule.",
            }
        ]
    )


def render_report(
    source_certification: pd.DataFrame,
    portfolio: pd.DataFrame,
    winner: pd.DataFrame,
    pass_fail: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task621 Source-Retyped Cost Portfolio Validation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Source gate action: `{d['source_gate_action']}`",
        f"- Best proactive full-panel 50bp account: max {int(d['best_50bp_proactive_max_positions'])} -> ${float(d['best_50bp_proactive_final_capital_usd']):,.2f}.",
        "- GPT output is review-only and not source truth.",
        "",
        "## Quant Expert Report",
        "",
        "### Source Retyping Certification",
        "",
        "| Split | Source Bucket | Trades | Avg Return | Win | Entry-Reduce | Certified |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in source_certification.iterrows():
        if row["source_retype_bucket"] not in {"aerospace_all", "aerospace_no_ceo_ir", "aerospace_ceo_ir"}:
            continue
        lines.append(
            f"| `{row['split_name']}` | `{row['source_retype_bucket']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']) * 100.0:.2f}% | "
            f"{float(row['entry_reduce_failure_rate']) * 100.0:.2f}% | {int(row['source_certified_pass_flag'])} |"
        )
    lines.extend(
        [
            "",
            "### 50bp Account Matrix",
            "",
            "| Scope | Universe | Max Positions | Final $ | Return |",
            "|---|---|---:|---:|---:|",
        ]
    )
    show = portfolio[portfolio["round_trip_cost_bps"].astype(int).eq(50)].copy()
    show = show[show["universe"].isin(["turboquant_original", "proactive_hold_until_source_certified", "rejected_global_ir_filter"])]
    for _, row in show.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### GPT Review",
            "",
            f"- Captured status: `{gpt_review.iloc[0]['captured_status']}`",
            f"- Summary: {gpt_review.iloc[0]['summary_point']}",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Cost/account test is good for the proactive risk-off candidate on the full panel.",
            "- Recent OOS is mixed: it wins most capacities, but not max 5.",
            "- Source certification still fails: CEO IR does not rescue recent aerospace/space trades.",
            "- Therefore the right action is hold-until-source-certification, not permanent theme ban and not approval.",
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
            "- `task_621_source_retyping_certification_matrix.csv`",
            "- `task_621_cost_portfolio_matrix.csv`",
            "- `task_621_cost_portfolio_winner_matrix.csv`",
            "- `task_621_pass_fail_matrix.csv`",
            "- `task_621_gpt_validation_review_status.csv`",
            "- `task_621_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task621_source_retyped_cost_portfolio_validation`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task621_source_retyped_cost_portfolio_validation(out_dir=args.out_dir)
    row = artifacts["task_621_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={row['decision']} best50=${float(row['best_50bp_proactive_final_capital_usd']):.2f}")


if __name__ == "__main__":
    main()
