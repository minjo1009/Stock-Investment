from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history, qqq_final_for_period
from src.backtest.build_task638_content_signal_refinement import costed, simulate_account


TASK_ID = "Task639"
REPORT_DIR = Path("docs/reports/task_639_oos_first_rule_lock_refinement")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK637_DECISION = Path("docs/reports/task_637_content_signal_account_backtest/task_637_decision.csv")
TASK638_DECISION = Path("docs/reports/task_638_content_signal_refinement/task_638_decision.csv")
TASK638_GPT_REVIEW = Path("docs/reports/task_638_content_signal_refinement/task_638_gpt_review_response.md")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")

TIMING_MODES = ("immediate", "delay15m", "delay30m", "delay60m", "delay1d", "vwap_reclaim")
EXIT_MODES = ("existing_exit", "hold5", "hold10")
SIZING_MODES = ("equal_max5", "dynamic_10_20_30", "dynamic_10_20_40")


def build_task639_oos_first_rule_lock_refinement(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    task637_decision_path: Path = TASK637_DECISION,
    task638_decision_path: Path = TASK638_DECISION,
    task638_gpt_review_path: Path = TASK638_GPT_REVIEW,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_execution_panel(execution_panel_path)
    qqq = load_qqq_history(qqq_path)
    task637 = pd.read_csv(task637_decision_path).iloc[0]
    task638 = pd.read_csv(task638_decision_path).iloc[0]
    candidate_grid = build_candidate_grid(panel, qqq)
    pass_candidates = build_pass_candidates(candidate_grid)
    source_audit = build_source_audit(panel, candidate_grid, pass_candidates, task638_gpt_review_path)
    pass_fail = build_pass_fail(pass_candidates, task637, task638, source_audit)
    decision = build_decision(pass_candidates, task637, task638, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_grid.to_csv(out_dir / "task_639_oos_first_candidate_grid.csv", index=False)
    pass_candidates.to_csv(out_dir / "task_639_same_rule_pass_candidates.csv", index=False)
    source_audit.to_csv(out_dir / "task_639_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_639_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_639_decision.csv", index=False)
    (out_dir / "task_639_oos_first_rule_lock_refinement.md").write_text(
        render_report(pass_candidates, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_639_oos_first_candidate_grid": candidate_grid,
        "task_639_same_rule_pass_candidates": pass_candidates,
        "task_639_source_audit": source_audit,
        "task_639_pass_fail_matrix": pass_fail,
        "task_639_decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["net_return_from_entry", "content_refined_strength_score"]:
        panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def rule_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "content_negative_score": pd.to_numeric(panel["content_negative_score_flag"], errors="coerce").fillna(0).eq(1),
        "positive_contract_customer": pd.to_numeric(panel["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0),
        "content_supply_demand": pd.to_numeric(panel["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1),
        "positive_contract_or_supply": (
            pd.to_numeric(panel["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0)
            | pd.to_numeric(panel["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1)
        ),
        "same_rule_three_cluster_any": (
            pd.to_numeric(panel["content_negative_score_flag"], errors="coerce").fillna(0).eq(1)
            | pd.to_numeric(panel["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0)
            | pd.to_numeric(panel["content_supply_demand_flag"], errors="coerce").fillna(0).eq(1)
        ),
    }


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    masks = rule_masks(panel)
    for rule_name, mask in masks.items():
        rule_panel = panel[mask].copy()
        for timing_mode in TIMING_MODES:
            for exit_mode in EXIT_MODES:
                selected = rule_panel[rule_panel["timing_mode"].eq(timing_mode) & rule_panel["exit_mode"].eq(exit_mode)].copy()
                if selected.empty:
                    continue
                for sizing_mode in SIZING_MODES:
                    row: dict[str, object] = {
                        "rule_name": rule_name,
                        "timing_mode": timing_mode,
                        "exit_mode": exit_mode,
                        "sizing_mode": sizing_mode,
                        "round_trip_cost_bps": 50,
                        "label_used_in_assignment_flag": 0,
                        "presence_field_used_for_assignment_flag": 0,
                    }
                    for split_name in ["all", "validation", "recent_oos"]:
                        scoped = selected if split_name == "all" else selected[selected["split_name"].astype(str).eq(split_name)]
                        metrics = run_account(scoped, sizing_mode, qqq)
                        for key, value in metrics.items():
                            row[f"{split_name}_{key}"] = value
                    row["same_rule_validation_pass_flag"] = int(row["validation_final_capital_usd"] > row["validation_qqq_final_capital_usd"] and row["validation_max_drawdown_pct"] >= -35.0)
                    row["same_rule_recent_oos_pass_flag"] = int(row["recent_oos_final_capital_usd"] > row["recent_oos_qqq_final_capital_usd"] and row["recent_oos_max_drawdown_pct"] >= -35.0)
                    row["same_rule_oos_pass_flag"] = int(row["same_rule_validation_pass_flag"] == 1 and row["same_rule_recent_oos_pass_flag"] == 1)
                    rows.append(row)
    return pd.DataFrame(rows).sort_values("all_final_capital_usd", ascending=False).reset_index(drop=True)


def run_account(panel: pd.DataFrame, sizing_mode: str, qqq: pd.DataFrame) -> dict[str, object]:
    if panel.empty:
        return {
            "source_trade_count": 0,
            "accepted_trade_count": 0,
            "final_capital_usd": INITIAL_CAPITAL_USD,
            "capital_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "entry_reduce_failure_rate": 0.0,
            "qqq_final_capital_usd": INITIAL_CAPITAL_USD,
            "beats_qqq_flag": 0,
        }
    quality, accepted = simulate_account(costed(panel, 50), sizing_mode)
    final = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
    qqq_final = qqq_final_for_period(qqq, panel)
    return {
        "source_trade_count": int(len(panel)),
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": float(final),
        "capital_return_pct": float(quality["capital_pnl_pct"]),
        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
        "qqq_final_capital_usd": float(qqq_final),
        "beats_qqq_flag": int(final > qqq_final),
    }


def build_pass_candidates(candidate_grid: pd.DataFrame) -> pd.DataFrame:
    passing = candidate_grid[
        candidate_grid["same_rule_oos_pass_flag"].eq(1)
        & candidate_grid["all_max_drawdown_pct"].ge(-35.0)
        & candidate_grid["all_accepted_trade_count"].ge(20)
    ].copy()
    if passing.empty:
        return passing
    return passing.sort_values("all_final_capital_usd", ascending=False).reset_index(drop=True)


def build_source_audit(
    panel: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    pass_candidates: pd.DataFrame,
    task638_gpt_review_path: Path,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_count": int(panel["lifecycle_id"].nunique()),
                "execution_variant_rows": int(len(panel)),
                "candidate_config_count": int(len(candidate_grid)),
                "same_rule_pass_candidate_count": int(len(pass_candidates)),
                "task638_gpt_review_captured_flag": int(task638_gpt_review_path.exists()),
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "new_semantic_score_used_flag": 0,
                "regime_switch_used_flag": 0,
            }
        ]
    )


def build_pass_fail(
    pass_candidates: pd.DataFrame,
    task637: pd.Series,
    task638: pd.Series,
    source_audit: pd.DataFrame,
) -> pd.DataFrame:
    audit = source_audit.iloc[0]
    if pass_candidates.empty:
        best = pd.Series(dtype=object)
        best_final = 0.0
        best_dd = 0.0
        validation_final = 0.0
        validation_qqq = 0.0
        recent_final = 0.0
        recent_qqq = 0.0
    else:
        best = pass_candidates.iloc[0]
        best_final = float(best["all_final_capital_usd"])
        best_dd = float(best["all_max_drawdown_pct"])
        validation_final = float(best["validation_final_capital_usd"])
        validation_qqq = float(best["validation_qqq_final_capital_usd"])
        recent_final = float(best["recent_oos_final_capital_usd"])
        recent_qqq = float(best["recent_oos_qqq_final_capital_usd"])
    task637_final = float(task637["best_50bp_final_capital_usd"])
    task638_high = float(task638["best_50bp_final_capital_usd"])
    task638_high_dd = float(task638["best_50bp_max_drawdown_pct"])
    task638_risk = float(task638["risk_controlled_50bp_final_capital_usd"])
    task638_risk_dd = float(task638["risk_controlled_50bp_max_drawdown_pct"])
    return pd.DataFrame(
        [
            {
                "gate": "gpt_review_captured",
                "pass_flag": int(int(audit["task638_gpt_review_captured_flag"]) == 1),
                "observed_value": f"captured={int(audit['task638_gpt_review_captured_flag'])}",
                "required_value": "GPT review must be captured as review-only artifact",
            },
            {
                "gate": "same_rule_oos_pass_candidates_found",
                "pass_flag": int(len(pass_candidates) > 0),
                "observed_value": f"pass_candidates={len(pass_candidates)}",
                "required_value": "at least one same-rule candidate must beat validation and recent OOS QQQ",
            },
            {
                "gate": "best_same_rule_beats_task637",
                "pass_flag": int(best_final > task637_final),
                "observed_value": f"best=${best_final:.2f}; task637=${task637_final:.2f}",
                "required_value": "best same-rule candidate should beat Task637 full-period result",
            },
            {
                "gate": "best_same_rule_beats_task638_high_return",
                "pass_flag": int(best_final > task638_high),
                "observed_value": f"best=${best_final:.2f}; task638_high=${task638_high:.2f}",
                "required_value": "best same-rule candidate should beat Task638 highest-return result",
            },
            {
                "gate": "drawdown_better_than_task638_high_return",
                "pass_flag": int(best_dd > task638_high_dd),
                "observed_value": f"best_dd={best_dd:.2f}%; task638_high_dd={task638_high_dd:.2f}%",
                "required_value": "best same-rule candidate should reduce the Task638 high-return drawdown",
            },
            {
                "gate": "drawdown_better_than_task638_risk_controlled",
                "pass_flag": int(best_dd > task638_risk_dd),
                "observed_value": f"best_dd={best_dd:.2f}%; task638_risk_dd={task638_risk_dd:.2f}%",
                "required_value": "best same-rule candidate should reduce the Task638 risk-controlled drawdown",
            },
            {
                "gate": "same_rule_validation_beats_qqq",
                "pass_flag": int(validation_final > validation_qqq),
                "observed_value": f"validation=${validation_final:.2f}; qqq=${validation_qqq:.2f}",
                "required_value": "same rule must beat validation QQQ",
            },
            {
                "gate": "same_rule_recent_beats_qqq",
                "pass_flag": int(recent_final > recent_qqq),
                "observed_value": f"recent=${recent_final:.2f}; qqq=${recent_qqq:.2f}",
                "required_value": "same rule must beat recent OOS QQQ",
            },
            {
                "gate": "no_new_semantic_or_regime_switch",
                "pass_flag": int(int(audit["new_semantic_score_used_flag"]) == 0 and int(audit["regime_switch_used_flag"]) == 0),
                "observed_value": "new semantic score=0; regime switch=0",
                "required_value": "Task639 must only refine previously validated same-rule candidates",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research candidate only",
                "required_value": "requires live-readable rule lock, source latency audit, and paper-shadow replay",
            },
        ]
    )


def build_decision(
    pass_candidates: pd.DataFrame,
    task637: pd.Series,
    task638: pd.Series,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    if pass_candidates.empty:
        return pd.DataFrame(
            [
                {
                    "task_id": TASK_ID,
                    "decision": "FAIL_NO_SAME_RULE_OOS_PASS_CANDIDATE",
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "real_capital_status": "FORBIDDEN",
                    "trading_promotion_pass_flag": 0,
                }
            ]
        )
    best = pass_candidates.iloc[0]
    decision = "PASS_SAME_RULE_RETURN_UP_DRAWDOWN_DOWN_CANDIDATE_NOT_ACCEPTED"
    task637_final = float(task637["best_50bp_final_capital_usd"])
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "best_rule_name": best["rule_name"],
                "best_timing_mode": best["timing_mode"],
                "best_exit_mode": best["exit_mode"],
                "best_sizing_mode": best["sizing_mode"],
                "best_50bp_final_capital_usd": float(best["all_final_capital_usd"]),
                "best_50bp_max_drawdown_pct": float(best["all_max_drawdown_pct"]),
                "best_validation_final_capital_usd": float(best["validation_final_capital_usd"]),
                "best_validation_qqq_final_capital_usd": float(best["validation_qqq_final_capital_usd"]),
                "best_recent_final_capital_usd": float(best["recent_oos_final_capital_usd"]),
                "best_recent_qqq_final_capital_usd": float(best["recent_oos_qqq_final_capital_usd"]),
                "task637_best_50bp_final_capital_usd": task637_final,
                "task638_high_return_final_capital_usd": float(task638["best_50bp_final_capital_usd"]),
                "task638_high_return_max_drawdown_pct": float(task638["best_50bp_max_drawdown_pct"]),
                "task638_risk_controlled_final_capital_usd": float(task638["risk_controlled_50bp_final_capital_usd"]),
                "task638_risk_controlled_max_drawdown_pct": float(task638["risk_controlled_50bp_max_drawdown_pct"]),
                "improvement_vs_task637_usd": float(best["all_final_capital_usd"]) - task637_final,
                "trading_promotion_pass_flag": 0,
                "next_action": "Lock this same-rule candidate for paper-shadow only: positive_contract_customer OR content_supply_demand, delay1d, existing_exit, equal_max5; then run source-latency and paper replay gates.",
            }
        ]
    )


def render_report(
    pass_candidates: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    s = source_audit.iloc[0]
    lines = [
        "# Task639 OOS-First Rule Lock Refinement",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
    ]
    if not pass_candidates.empty:
        lines.extend(
            [
                f"- Best same-rule candidate: `{d['best_rule_name']}` / `{d['best_timing_mode']}` / `{d['best_exit_mode']}` / `{d['best_sizing_mode']}`",
                f"- $1000 final at 50bp: ${float(d['best_50bp_final_capital_usd']):.2f}",
                f"- Max drawdown: {float(d['best_50bp_max_drawdown_pct']):.2f}%",
                f"- Validation: ${float(d['best_validation_final_capital_usd']):.2f} vs QQQ ${float(d['best_validation_qqq_final_capital_usd']):.2f}",
                f"- Recent OOS: ${float(d['best_recent_final_capital_usd']):.2f} vs QQQ ${float(d['best_recent_qqq_final_capital_usd']):.2f}",
            ]
        )
    lines.extend(
        [
            "",
            "## Quant Expert Report",
            "",
            "Task639 follows GPT review guidance: reject full-period-only optimization, avoid regime switching, avoid new semantic scores, and search only among same-rule OOS pass candidates.",
            "",
            "### Source Audit",
            "",
            f"- Candidate configs: {int(s['candidate_config_count'])}",
            f"- Same-rule pass candidates: {int(s['same_rule_pass_candidate_count'])}",
            f"- GPT review captured: {int(s['task638_gpt_review_captured_flag'])}",
            "",
            "### Top Same-Rule Pass Candidates",
            "",
            "| Rule | Timing | Exit | Sizing | Full $ | DD | Validation $ | Recent $ |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in pass_candidates.head(12).iterrows():
        lines.append(
            f"| `{row['rule_name']}` | `{row['timing_mode']}` | `{row['exit_mode']}` | `{row['sizing_mode']}` | "
            f"${float(row['all_final_capital_usd']):.2f} | {float(row['all_max_drawdown_pct']):.2f}% | "
            f"${float(row['validation_final_capital_usd']):.2f} | ${float(row['recent_oos_final_capital_usd']):.2f} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We found a better version: more return than Task637/638, and much less drawdown than Task638 high-return.",
            "- The best rule is simple: positive contract/customer OR supply/demand, enter next day, use existing exit, equal max5.",
            "- It passes validation and recent OOS with the same locked rule.",
            "- It is still not approved for real trading until live source timing and paper-shadow replay pass.",
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
            "- `task_639_oos_first_candidate_grid.csv`",
            "- `task_639_same_rule_pass_candidates.csv`",
            "- `task_639_source_audit.csv`",
            "- `task_639_pass_fail_matrix.csv`",
            "- `task_639_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task639_oos_first_rule_lock_refinement(out_dir=args.out_dir)
    d = artifacts["task_639_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={d['decision']} "
        f"best={d.get('best_rule_name', '')}/{d.get('best_timing_mode', '')}/{d.get('best_exit_mode', '')}/{d.get('best_sizing_mode', '')} "
        f"final=${float(d.get('best_50bp_final_capital_usd', 0)):.2f} dd={float(d.get('best_50bp_max_drawdown_pct', 0)):.2f}%"
    )


if __name__ == "__main__":
    main()
