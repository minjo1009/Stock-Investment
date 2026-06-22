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
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD
from src.backtest.build_task638_content_signal_refinement import costed, simulate_account
from src.backtest.build_task640_leverage_etf_drawdown_upgrade import (
    ROUND_TRIP_COST_BPS,
    load_execution_panel,
    select_task639_base_panel,
)


TASK_ID = "Task641"
REPORT_DIR = Path("docs/reports/task_641_firm_grade_gap_diagnosis")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
TASK640_DECISION = Path("docs/reports/task_640_leverage_etf_drawdown_upgrade/task_640_decision.csv")
TASK640_GPT_REVIEW = Path("docs/reports/task_640_leverage_etf_drawdown_upgrade/task_640_gpt_review_response.md")


def build_task641_firm_grade_gap_diagnosis(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    task640_decision_path: Path = TASK640_DECISION,
    task640_gpt_review_path: Path = TASK640_GPT_REVIEW,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_execution_panel(execution_panel_path)
    base_panel = select_task639_base_panel(panel)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    task640 = pd.read_csv(task640_decision_path).iloc[0]
    task640_gpt = task640_gpt_review_path.read_text(encoding="utf-8") if task640_gpt_review_path.exists() else ""
    baseline, accepted = build_baseline(base_panel, task639)
    capacity = build_capacity_sensitivity(base_panel)
    signal_tiers = build_signal_tier_diagnostics(base_panel, accepted)
    drawdown = build_drawdown_damage_table(accepted)
    dimension = build_dimension_diagnostics(accepted)
    gap_matrix = build_gap_matrix(baseline, capacity, signal_tiers, drawdown, dimension)
    decision = build_decision(baseline, task640, gap_matrix)

    out_dir.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(out_dir / "task_641_task639_baseline_diagnostic.csv", index=False)
    accepted.to_csv(out_dir / "task_641_task639_accepted_trades.csv", index=False)
    capacity.to_csv(out_dir / "task_641_capacity_sensitivity.csv", index=False)
    signal_tiers.to_csv(out_dir / "task_641_signal_tier_diagnostics.csv", index=False)
    drawdown.to_csv(out_dir / "task_641_drawdown_damage_table.csv", index=False)
    dimension.to_csv(out_dir / "task_641_dimension_diagnostics.csv", index=False)
    gap_matrix.to_csv(out_dir / "task_641_firm_grade_gap_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_641_decision.csv", index=False)
    (out_dir / "task_641_firm_grade_gap_diagnosis.md").write_text(
        render_report(baseline, capacity, signal_tiers, drawdown, dimension, gap_matrix, decision),
        encoding="utf-8",
    )
    write_gpt_packet(out_dir, baseline, capacity, signal_tiers, drawdown, dimension, gap_matrix, task640, task640_gpt)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_641_task639_baseline_diagnostic": baseline,
        "task_641_task639_accepted_trades": accepted,
        "task_641_capacity_sensitivity": capacity,
        "task_641_signal_tier_diagnostics": signal_tiers,
        "task_641_drawdown_damage_table": drawdown,
        "task_641_dimension_diagnostics": dimension,
        "task_641_firm_grade_gap_matrix": gap_matrix,
        "task_641_decision": decision,
    }


def build_baseline(base_panel: pd.DataFrame, task639: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    quality, accepted = simulate_account(costed(base_panel, ROUND_TRIP_COST_BPS), "equal_max5")
    accepted = accepted.copy()
    accepted["net_return_pct_after_cost"] = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce") * 100.0
    accepted["loss_flag_after_cost"] = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce").lt(0).astype(int)
    accepted["large_loss_flag_after_cost"] = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce").le(-0.10).astype(int)
    source_count = int(len(base_panel))
    accepted_count = int(len(accepted))
    final_capital = float(INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0))
    baseline = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "source_rule": "Task639 positive_contract_customer OR content_supply_demand / delay1d / existing_exit / equal_max5 / 50bp",
                "source_trade_count": source_count,
                "accepted_trade_count": accepted_count,
                "skipped_due_capacity_count": int(source_count - accepted_count),
                "capacity_acceptance_rate": float(accepted_count / source_count) if source_count else 0.0,
                "final_capital_usd": final_capital,
                "task639_reported_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                "task639_reported_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                "win_rate": float(quality["win_rate"]),
                "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                "median_holding_days": float(pd.to_numeric(accepted["holding_days"], errors="coerce").median()),
                "large_loss_trade_count": int(accepted["large_loss_flag_after_cost"].sum()),
                "microstructure_available_rate": float(1.0 - accepted["microstructure_state_v4"].astype(str).eq("microstructure_not_available").mean())
                if "microstructure_state_v4" in accepted.columns
                else 0.0,
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
            }
        ]
    )
    return baseline, accepted


def build_capacity_sensitivity(base_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cap in [3, 5, 7, 10, 15, 20, 30, 50]:
        quality, accepted, _curve = simulate_deterministic_portfolio(costed(base_panel, ROUND_TRIP_COST_BPS), max_positions=cap)
        rows.append(
            {
                "max_positions": int(cap),
                "accepted_trade_count": int(len(accepted)),
                "final_capital_usd": float(INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)),
                "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                "skipped_due_capacity_count": int(quality["skipped_due_capacity_count"]),
            }
        )
    return pd.DataFrame(rows)


def build_signal_tier_diagnostics(base_panel: pd.DataFrame, accepted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope_name, frame in [("source_all", base_panel), ("accepted_max5", accepted)]:
        scoped = frame.copy()
        contract = pd.to_numeric(scoped["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0)
        supply = pd.to_numeric(scoped["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1)
        scoped["task639_signal_tier"] = "supply_only"
        scoped.loc[contract & ~supply, "task639_signal_tier"] = "contract_only"
        scoped.loc[contract & supply, "task639_signal_tier"] = "both_contract_and_supply"
        returns = pd.to_numeric(scoped["net_return_from_entry"], errors="coerce")
        scoped["return_after_cost"] = returns - ROUND_TRIP_COST_BPS / 10000.0 if scope_name == "source_all" else returns
        for tier, group in scoped.groupby("task639_signal_tier", dropna=False):
            group_returns = pd.to_numeric(group["return_after_cost"], errors="coerce")
            rows.append(
                {
                    "scope": scope_name,
                    "signal_tier": tier,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(group_returns.mean() * 100.0) if len(group) else 0.0,
                    "win_rate": float(group_returns.gt(0).mean()) if len(group) else 0.0,
                    "large_loss_rate": float(group_returns.le(-0.10).mean()) if len(group) else 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_drawdown_damage_table(accepted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    accepted = accepted.copy()
    accepted["loss_pct"] = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce") * 100.0
    for group_col in ["symbol", "theme_id", "split_name", "timing_state"]:
        for key, group in accepted.groupby(group_col, dropna=False):
            losses = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
            rows.append(
                {
                    "dimension": group_col,
                    "bucket": str(key),
                    "accepted_trade_count": int(len(group)),
                    "avg_net_return_pct": float(losses.mean() * 100.0),
                    "worst_trade_return_pct": float(losses.min() * 100.0),
                    "large_loss_count": int(losses.le(-0.10).sum()),
                    "loss_trade_count": int(losses.lt(0).sum()),
                }
            )
    return pd.DataFrame(rows).sort_values(["large_loss_count", "worst_trade_return_pct"], ascending=[False, True]).reset_index(drop=True)


def build_dimension_diagnostics(accepted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    numeric_buckets = {
        "range_pos": [0.85, 0.95, 0.99],
        "volume_ratio_prev": [1.0, 1.5, 2.0],
        "theme_rank_prev": [2, 5, 10],
        "broad_market_stress": [25, 35, 45],
    }
    for column, cutoffs in numeric_buckets.items():
        if column not in accepted.columns:
            continue
        values = pd.to_numeric(accepted[column], errors="coerce")
        scoped = accepted.copy()
        scoped["_bucket"] = pd.cut(values, [-float("inf")] + cutoffs + [float("inf")], include_lowest=True).astype(str)
        for bucket, group in scoped.groupby("_bucket", dropna=False):
            returns = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
            rows.append(
                {
                    "dimension": column,
                    "bucket": str(bucket),
                    "accepted_trade_count": int(len(group)),
                    "avg_net_return_pct": float(returns.mean() * 100.0),
                    "large_loss_rate": float(returns.le(-0.10).mean()) if len(group) else 0.0,
                }
            )
    for column in ["intraday_entry_state_v4", "microstructure_state_v4", "multi_day_market_state_v4", "theme_regime_state_v4"]:
        if column not in accepted.columns:
            continue
        for bucket, group in accepted.groupby(column, dropna=False):
            returns = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
            rows.append(
                {
                    "dimension": column,
                    "bucket": str(bucket),
                    "accepted_trade_count": int(len(group)),
                    "avg_net_return_pct": float(returns.mean() * 100.0),
                    "large_loss_rate": float(returns.le(-0.10).mean()) if len(group) else 0.0,
                }
            )
    return pd.DataFrame(rows).sort_values(["dimension", "bucket"]).reset_index(drop=True)


def build_gap_matrix(
    baseline: pd.DataFrame,
    capacity: pd.DataFrame,
    signal_tiers: pd.DataFrame,
    drawdown: pd.DataFrame,
    dimension: pd.DataFrame,
) -> pd.DataFrame:
    base = baseline.iloc[0]
    cap3 = capacity[capacity["max_positions"].eq(3)].iloc[0]
    cap10 = capacity[capacity["max_positions"].eq(10)].iloc[0]
    micro = float(base["microstructure_available_rate"])
    top_damage = drawdown[(drawdown["dimension"].eq("theme_id")) & (drawdown["large_loss_count"].gt(0))].head(3)
    damage_text = "; ".join(f"{r.bucket}: large_loss={int(r.large_loss_count)}, avg={float(r.avg_net_return_pct):.2f}%" for r in top_damage.itertuples())
    tier_text = "; ".join(
        f"{r.signal_tier}/{r.scope}: n={int(r.trade_count)}, avg={float(r.avg_net_return_pct):.2f}%"
        for r in signal_tiers[signal_tiers["scope"].eq("accepted_max5")].itertuples()
    )
    rows = [
        {
            "priority": 1,
            "gap": "entry_quality_confirmation_missing",
            "evidence": "All accepted trades share broad intraday_breakout_acceptance; no VWAP/opening-range/relative-strength confirmation has been locked for Task639.",
            "why_it_matters": "May remove large loss trades before capital is committed.",
            "next_test": "Task641A: same Task639 signal plus pre-entry VWAP/opening-range/theme-RS/volume confirmation.",
            "acceptance_bar": "Beat Task639 final capital and max drawdown with same rule in validation and recent OOS.",
        },
        {
            "priority": 2,
            "gap": "risk_normalized_sizing_missing",
            "evidence": f"Equal max5 sizes high-vol and low-vol names the same; large loss count is {int(base['large_loss_trade_count'])}.",
            "why_it_matters": "A few high-vol losers can drive most drawdown even when signal is good.",
            "next_test": "Task641B: ATR/gap/volatility-bucket sizing with fixed max gross exposure.",
            "acceptance_bar": "Lower max drawdown without reducing validation and recent OOS QQQ edge.",
        },
        {
            "priority": 3,
            "gap": "signal_strength_tiering_underused",
            "evidence": tier_text,
            "why_it_matters": "The OR rule treats different economic evidence strength as the same bet.",
            "next_test": "Task641C: both features full size, single-feature normal or confirmation-required size.",
            "acceptance_bar": "Tiered sizing improves return/DD and does not rely on symbol identity.",
        },
        {
            "priority": 4,
            "gap": "capital_turnover_and_exit_policy_underdeveloped",
            "evidence": f"Only {int(base['accepted_trade_count'])}/{int(base['source_trade_count'])} trades accepted; median hold {float(base['median_holding_days']):.1f} days; cap3 final ${float(cap3['final_capital_usd']):.2f} with worse DD, cap10 final ${float(cap10['final_capital_usd']):.2f} with lower DD.",
            "why_it_matters": "The strategy may be using capital inefficiently; current exit wins by long winners but blocks many candidates.",
            "next_test": "Task641D: profit-lock/trailing/partial exit and capital recycling only after entry-quality and risk sizing.",
            "acceptance_bar": "Higher capital turnover with no validation/recent OOS degradation.",
        },
        {
            "priority": 5,
            "gap": "microstructure_source_gap",
            "evidence": f"Accepted-trade microstructure availability rate is {micro:.2%}.",
            "why_it_matters": "Cannot distinguish real continuation from thin/fragile breakout at execution time.",
            "next_test": "Task641E: source-ready microstructure fields before live or paper-shadow promotion.",
            "acceptance_bar": "Live-readable fields with timestamp provenance; no inferred lifecycle matching.",
        },
        {
            "priority": 6,
            "gap": "damage_cluster_causality_missing",
            "evidence": damage_text,
            "why_it_matters": "Single-symbol exclusions are overfit unless converted to causal pre-entry rules.",
            "next_test": "Task641F: explain worst accepted losses by source relevance, price reaction, volatility, and entry tape.",
            "acceptance_bar": "No single-name blacklist; only general rules surviving split/OOS.",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(baseline: pd.DataFrame, task640: pd.Series, gap_matrix: pd.DataFrame) -> pd.DataFrame:
    base = baseline.iloc[0]
    return pd.DataFrame(
        [
            {
                "decision": "DIAGNOSE_FIRM_GRADE_GAPS_BEFORE_MORE_ALPHA_SEARCH",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "task639_final_capital_usd": float(base["final_capital_usd"]),
                "task639_max_drawdown_pct": float(base["max_drawdown_pct"]),
                "task640_combo_final_capital_usd": float(task640["best_combo_final_capital_usd"]),
                "task640_combo_max_drawdown_pct": float(task640["best_combo_max_drawdown_pct"]),
                "top_priority_gap": str(gap_matrix.iloc[0]["gap"]),
                "next_action": "Discuss gap matrix with GPT, then test Task641A entry confirmation, Task641B ATR sizing, and Task641C signal tier sizing in that order.",
            }
        ]
    )


def render_report(
    baseline: pd.DataFrame,
    capacity: pd.DataFrame,
    signal_tiers: pd.DataFrame,
    drawdown: pd.DataFrame,
    dimension: pd.DataFrame,
    gap_matrix: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    dec = decision.iloc[0]
    base = baseline.iloc[0]
    return "\n".join(
        [
            "# Task641 Firm-Grade Gap Diagnosis",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Task639 baseline: ${float(base['final_capital_usd']):.2f}, max drawdown {float(base['max_drawdown_pct']):.2f}%",
            f"- Accepted trades: {int(base['accepted_trade_count'])}/{int(base['source_trade_count'])}",
            f"- Median holding days: {float(base['median_holding_days']):.1f}",
            f"- Top priority gap: `{dec['top_priority_gap']}`",
            "",
            "## Quant Expert Report",
            "",
            "Task641 is a diagnosis task. It does not add a new trading rule. It identifies what must be improved before chasing more alpha.",
            "",
            "### Baseline",
            "",
            table(baseline),
            "",
            "### Capacity Sensitivity",
            "",
            table(capacity),
            "",
            "### Signal Tier Diagnostics",
            "",
            table(signal_tiers),
            "",
            "### Drawdown Damage",
            "",
            table(drawdown.head(20)),
            "",
            "### Dimension Diagnostics",
            "",
            table(dimension.head(40)),
            "",
            "### Firm-Grade Gap Matrix",
            "",
            table(gap_matrix),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- The main missing piece is not leveraged ETF exposure.",
            "- The biggest missing pieces are entry quality, volatility-aware sizing, signal strength tiering, and capital turnover.",
            "- Current Task639 uses only 54 of 1,621 candidate trades because capital is locked for a long time.",
            "- Single-name exclusions are not acceptable until converted into causal pre-entry rules.",
            "- Next tests should keep the Task639 signal fixed and improve execution/risk around it.",
            "",
            "## Artifact Manifest",
            "",
            "- `task_641_task639_baseline_diagnostic.csv`",
            "- `task_641_task639_accepted_trades.csv`",
            "- `task_641_capacity_sensitivity.csv`",
            "- `task_641_signal_tier_diagnostics.csv`",
            "- `task_641_drawdown_damage_table.csv`",
            "- `task_641_dimension_diagnostics.csv`",
            "- `task_641_firm_grade_gap_matrix.csv`",
            "- `task_641_decision.csv`",
            "- `task_641_gpt_review_packet.txt`",
            "- `task_641_gpt_review_response.md`",
            "- `artifact_manifest.csv`",
            "",
        ]
    )


def write_gpt_packet(
    out_dir: Path,
    baseline: pd.DataFrame,
    capacity: pd.DataFrame,
    signal_tiers: pd.DataFrame,
    drawdown: pd.DataFrame,
    dimension: pd.DataFrame,
    gap_matrix: pd.DataFrame,
    task640: pd.Series,
    task640_gpt: str,
) -> None:
    base = baseline.iloc[0]
    packet = f"""Use only supplied facts. Do not invent source claims, prices, filings, news, or live readiness.

You are an external firm-grade quant PM/reviewer. Diagnose what this project is still missing if we want to improve Task639 from both sides:
- increase final capital
- reduce max drawdown

Current baseline:
- Rule: positive_contract_customer OR content_supply_demand
- Entry: next day
- Exit: existing exit
- Sizing: equal max5
- Cost: 50bp round trip
- $1000 final: ${float(base['final_capital_usd']):.2f}
- Max drawdown: {float(base['max_drawdown_pct']):.2f}%
- Source trades: {int(base['source_trade_count'])}
- Accepted trades: {int(base['accepted_trade_count'])}
- Skipped by capacity: {int(base['skipped_due_capacity_count'])}
- Median holding days: {float(base['median_holding_days']):.1f}
- Entry-reduce failure rate: {float(base['entry_reduce_failure_rate']):.2%}
- Microstructure available rate on accepted trades: {float(base['microstructure_available_rate']):.2%}

Task640 finding:
- Leveraged ETF overlays failed.
- Simple exclusions/throttles failed individually.
- One combo improved slightly: {task640['best_combo_target']} + drawdown threshold {task640['best_combo_drawdown_threshold_pct']} / size multiplier {task640['best_combo_position_multiplier']} -> ${float(task640['best_combo_final_capital_usd']):.2f}, DD {float(task640['best_combo_max_drawdown_pct']):.2f}%.
- This combo is NOT accepted due to single-name overfit risk.

Capacity sensitivity:
{capacity.to_csv(index=False)}

Signal tier diagnostics:
{signal_tiers.to_csv(index=False)}

Top drawdown damage:
{drawdown.head(20).to_csv(index=False)}

Dimension diagnostics:
{dimension.head(40).to_csv(index=False)}

Current gap matrix:
{gap_matrix.to_csv(index=False)}

Prior GPT review summary:
{task640_gpt[:2500]}

Question:
1. What are the biggest firm-grade gaps we are still missing?
2. What are we overfitting or fooling ourselves with?
3. What exact next experiments should be run in order?
4. What evidence would make you reject each next experiment?
5. How do we improve return and drawdown without using after-the-fact labels or single-name blacklists?

Return concise Korean, but firm-grade. Label items as interpretation, inference, or source_gap.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "task_641_gpt_review_packet.txt").write_text(packet, encoding="utf-8")


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    safe = frame.copy().where(pd.notna(frame), "")
    columns = [str(column) for column in safe.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in safe.astype(str).to_dict(orient="records"):
        lines.append("| " + " | ".join(row[column] for column in safe.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task641_firm_grade_gap_diagnosis(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
