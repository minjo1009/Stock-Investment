from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task619"
REPORT_DIR = Path("docs/reports/task_619_promotion_gate_update")
TASK617_DIR = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest")
TASK618_DIR = Path("docs/reports/task_618_1000_capital_portfolio_comparison")


def build_task619_promotion_gate_update(
    *,
    task617_dir: Path = TASK617_DIR,
    task618_dir: Path = TASK618_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    task617_decision = pd.read_csv(task617_dir / "task_617_decision.csv")
    split = pd.read_csv(task617_dir / "fresh_turboquant_split_summary.csv")
    task618_summary = pd.read_csv(task618_dir / "task_618_1000_capital_portfolio_summary.csv")
    task618_decision = pd.read_csv(task618_dir / "task_618_decision.csv")

    source_snapshot = build_source_snapshot(task617_decision, split, task618_summary, task618_decision)
    gpt_review = build_gpt_review_status()
    gate_priority = build_gate_priority(source_snapshot)
    implementation_packet = build_implementation_packet()
    pass_fail = build_pass_fail(gate_priority, gpt_review)
    decision = build_decision(source_snapshot, gate_priority, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    source_snapshot.to_csv(out_dir / "task_619_source_snapshot.csv", index=False)
    gpt_review.to_csv(out_dir / "task_619_gpt_gate_review_status.csv", index=False)
    gate_priority.to_csv(out_dir / "task_619_gate_priority_matrix.csv", index=False)
    implementation_packet.to_csv(out_dir / "task_619_implementation_packet.csv", index=False)
    pass_fail.to_csv(out_dir / "task_619_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_619_decision.csv", index=False)
    (out_dir / "task_619_promotion_gate_update.md").write_text(
        render_report(source_snapshot, gpt_review, gate_priority, implementation_packet, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_619_source_snapshot": source_snapshot,
        "task_619_gpt_gate_review_status": gpt_review,
        "task_619_gate_priority_matrix": gate_priority,
        "task_619_implementation_packet": implementation_packet,
        "task_619_pass_fail_matrix": pass_fail,
        "task_619_decision": decision,
    }


def build_source_snapshot(
    task617_decision: pd.DataFrame,
    split: pd.DataFrame,
    task618_summary: pd.DataFrame,
    task618_decision: pd.DataFrame,
) -> pd.DataFrame:
    d617 = task617_decision.iloc[0]
    d618 = task618_decision.iloc[0]
    validation = split[split["split_name"].astype(str).eq("validation")].iloc[0]
    recent = split[split["split_name"].astype(str).eq("recent_oos")].iloc[0]
    t618 = task618_summary[task618_summary["universe"].astype(str).eq("turboquant")].copy()
    max5 = t618[t618["max_positions"].astype(int).eq(5)].iloc[0]
    max50 = t618[t618["max_positions"].astype(int).eq(50)].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "task617_decision": d617["decision"],
                "task618_decision": d618["decision"],
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "baseline_candidate_count": int(d617["baseline_candidate_count"]),
                "strategy_trade_count": int(d617["strategy_trade_count"]),
                "strategy_avg_net_return_pct": float(d617["strategy_avg_net_return_pct"]),
                "strategy_entry_reduce_failure_rate": float(d617["strategy_entry_reduce_failure_rate"]),
                "validation_avg_net_return_pct": float(validation["avg_net_return_pct"]),
                "validation_win_rate": float(validation["win_rate"]),
                "validation_entry_reduce_failure_rate": float(validation["entry_reduce_failure_rate"]),
                "recent_oos_trade_count": int(recent["lifecycle_count"]),
                "recent_oos_avg_net_return_pct": float(recent["avg_net_return_pct"]),
                "recent_oos_win_rate": float(recent["win_rate"]),
                "recent_oos_entry_reduce_failure_rate": float(recent["entry_reduce_failure_rate"]),
                "recent_oos_avg_delta_vs_validation_pct_point": float(recent["avg_net_return_pct"]) - float(validation["avg_net_return_pct"]),
                "recent_oos_entry_reduce_delta_vs_validation_pct_point": (
                    float(recent["entry_reduce_failure_rate"]) - float(validation["entry_reduce_failure_rate"])
                )
                * 100.0,
                "turboquant_final_usd_max5": float(max5["final_capital_usd"]),
                "turboquant_final_usd_max50": float(max50["final_capital_usd"]),
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "captured_at_kst": "2026-06-07",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "gpt_priority_recommendation": "P1 recent OOS stability, P2 cost/slippage, P3 live source readiness",
                "gpt_summary": (
                    "GPT review agrees strategy refinement should wait. Recent OOS weakness is the first blocker, "
                    "cost/slippage is second, and live source readiness is third."
                ),
            }
        ]
    )


def build_gate_priority(source_snapshot: pd.DataFrame) -> pd.DataFrame:
    s = source_snapshot.iloc[0]
    return pd.DataFrame(
        [
            {
                "priority": "P1",
                "gate": "recent_oos_stability",
                "owner_team": "Intraday Continuation Research",
                "reviewer_team": "Backtest & Simulation Infra",
                "current_status": "BLOCKER_OPEN",
                "observed_problem": (
                    f"recent_oos avg {float(s['recent_oos_avg_net_return_pct']):.2f}% vs validation "
                    f"{float(s['validation_avg_net_return_pct']):.2f}%; recent_oos entry-reduce "
                    f"{float(s['recent_oos_entry_reduce_failure_rate']) * 100.0:.2f}%"
                ),
                "required_test": "Decompose all recent_oos trades by failure taxonomy, regime bucket, and entry-reduce path.",
                "pass_threshold": "promotion candidate only if recent_oos avg >= 5.00%, win_rate >= 50.00%, entry_reduce <= 40.00%, and taxonomy coverage >= 80.00%",
                "fail_threshold": "fail if degradation cannot be explained or recent_oos remains below the pass threshold",
                "next_task": "Task620_recent_oos_failure_decomposition",
            },
            {
                "priority": "P2",
                "gate": "cost_slippage_stress",
                "owner_team": "Backtest & Simulation Infra",
                "reviewer_team": "Execution & Risk",
                "current_status": "BLOCKER_OPEN",
                "observed_problem": "Task618 account comparison is before explicit cost/slippage stress.",
                "required_test": "Rerun Task618 same-capital portfolio comparison under round-trip cost stresses 25bp, 50bp, 100bp, and 200bp.",
                "pass_threshold": "turboquant must stay above all_candidates and above initial $1000 at max_positions 5, 10, and 20 under 50bp round-trip cost",
                "fail_threshold": "fail if 50bp cost removes TurboQuant edge or makes final account <= $1000 in max_positions 5/10/20",
                "next_task": "Task621_cost_slippage_portfolio_stress",
            },
            {
                "priority": "P3",
                "gate": "live_source_readiness",
                "owner_team": "Data & Market Microstructure",
                "reviewer_team": "Research Governance",
                "current_status": "BLOCKER_OPEN",
                "observed_problem": "Intelligence sidecar is collection-only; source health is not yet a promotion gate.",
                "required_test": "Audit at least 20 runtime sessions for availability, timestamp integrity, stale events, duplicates, and missing fields.",
                "pass_threshold": "availability >= 95.00%, stale_rate <= 1.00%, duplicate_rate <= 1.00%, timestamp_reversal_count = 0, trade_signal_used_flag = 0",
                "fail_threshold": "fail if source capture is stale, duplicated, missing required timestamps, or connected to trading decisions",
                "next_task": "Task622_live_source_health_gate",
            },
        ]
    )


def build_implementation_packet() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_name": "Task620_recent_oos_failure_decomposition",
                "write_scope": "docs/reports/task_620_recent_oos_failure_decomposition/",
                "primary_artifacts": "recent_oos_failure_taxonomy.csv; recent_oos_degradation_report.md; task_620_decision.csv",
                "validation_command": "python -m unittest tests.test_task620_recent_oos_failure_decomposition",
                "blocked_actions": "Do not add new alpha factors before recent OOS degradation is explained.",
            },
            {
                "task_name": "Task621_cost_slippage_portfolio_stress",
                "write_scope": "docs/reports/task_621_cost_slippage_portfolio_stress/",
                "primary_artifacts": "cost_stress_portfolio_summary.csv; cost_stress_winner_summary.csv; task_621_decision.csv",
                "validation_command": "python -m unittest tests.test_task621_cost_slippage_portfolio_stress",
                "blocked_actions": "Do not claim portfolio superiority without same-capital cost stress.",
            },
            {
                "task_name": "Task622_live_source_health_gate",
                "write_scope": "docs/reports/task_622_live_source_health_gate/",
                "primary_artifacts": "runtime_source_health_audit.csv; timestamp_integrity_report.md; task_622_decision.csv",
                "validation_command": "python -m unittest tests.test_task622_live_source_health_gate",
                "blocked_actions": "Do not use sidecar events as trade signals before source readiness is accepted.",
            },
        ]
    )


def build_pass_fail(gate_priority: pd.DataFrame, gpt_review: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate": "gpt_review_captured",
                "pass_flag": int(str(gpt_review.iloc[0]["captured_status"]).startswith("CAPTURED")),
                "observed_value": str(gpt_review.iloc[0]["captured_status"]),
                "required_value": "Chrome ChatGPT review captured as non-source interpretation",
            },
            {
                "gate": "promotion_gate_priority_locked",
                "pass_flag": int(gate_priority["priority"].tolist() == ["P1", "P2", "P3"]),
                "observed_value": " -> ".join(gate_priority["gate"].astype(str).tolist()),
                "required_value": "recent_oos_stability -> cost_slippage_stress -> live_source_readiness",
            },
            {
                "gate": "strategy_refinement_allowed",
                "pass_flag": 0,
                "observed_value": "recent OOS and cost gates are still open",
                "required_value": "P1/P2 gates must pass before refinement",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "strategy remains NOT_ACCEPTED; real capital remains FORBIDDEN",
                "required_value": "P1/P2/P3 gates plus existing broker/source gates must pass",
            },
        ]
    )


def build_decision(source_snapshot: pd.DataFrame, gate_priority: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    s = source_snapshot.iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "LOCK_PROMOTION_GATES_RECENT_OOS_FIRST_NOT_ACCEPTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "top_blocker": "recent_oos_stability",
                "recent_oos_avg_net_return_pct": float(s["recent_oos_avg_net_return_pct"]),
                "recent_oos_win_rate": float(s["recent_oos_win_rate"]),
                "recent_oos_entry_reduce_failure_rate": float(s["recent_oos_entry_reduce_failure_rate"]),
                "next_gate_order": " -> ".join(gate_priority["gate"].astype(str).tolist()),
                "strategy_refinement_allowed_flag": 0,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run Task620 recent OOS failure decomposition, then Task621 cost/slippage stress, then Task622 live source health gate.",
            }
        ]
    )


def render_report(
    source_snapshot: pd.DataFrame,
    gpt_review: pd.DataFrame,
    gate_priority: pd.DataFrame,
    implementation_packet: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    s = source_snapshot.iloc[0]
    lines = [
        "# Task619 Promotion Gate Update",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        "- GPT output is review-only and is not used as source truth or score input.",
        f"- Top blocker: `{d['top_blocker']}`",
        f"- Next gate order: `{d['next_gate_order']}`",
        "",
        "## Quant Expert Report",
        "",
        "### Source Snapshot",
        "",
        f"- Task617 decision: `{s['task617_decision']}`",
        f"- Task618 decision: `{s['task618_decision']}`",
        f"- TurboQuant average return: {float(s['strategy_avg_net_return_pct']):.2f}%",
        f"- Recent OOS: {int(s['recent_oos_trade_count'])} trades, avg {float(s['recent_oos_avg_net_return_pct']):.2f}%, win {float(s['recent_oos_win_rate']) * 100.0:.2f}%, entry-reduce {float(s['recent_oos_entry_reduce_failure_rate']) * 100.0:.2f}%.",
        f"- Recent OOS average delta versus validation: {float(s['recent_oos_avg_delta_vs_validation_pct_point']):.2f}pp.",
        "",
        "### GPT Review Capture",
        "",
        f"- Captured status: `{gpt_review.iloc[0]['captured_status']}`",
        f"- Recommendation: {gpt_review.iloc[0]['gpt_priority_recommendation']}",
        "",
        "### Gate Priority Matrix",
        "",
        "| Priority | Gate | Owner | Status | Pass Threshold | Next Task |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in gate_priority.iterrows():
        lines.append(
            f"| `{row['priority']}` | `{row['gate']}` | {row['owner_team']} | `{row['current_status']}` | "
            f"{row['pass_threshold']} | `{row['next_task']}` |"
        )
    lines.extend(
        [
            "",
            "### Implementation Packet",
            "",
            "| Task | Write Scope | Artifacts | Validation | Blocked Actions |",
            "|---|---|---|---|---|",
        ]
    )
    for _, row in implementation_packet.iterrows():
        lines.append(
            f"| `{row['task_name']}` | `{row['write_scope']}` | {row['primary_artifacts']} | "
            f"`{row['validation_command']}` | {row['blocked_actions']} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- The strategy beat the all-candidate universe in the $1000 same-capital portfolio test.",
            "- The next problem is not more refinement. The next problem is recent OOS weakness.",
            "- Work order is fixed: recent OOS explanation first, cost/slippage second, live-source health third.",
            "- Strategy remains blocked until those gates pass.",
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
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/task_617_decision.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_split_summary.csv`",
            "- `docs/reports/task_618_1000_capital_portfolio_comparison/task_618_1000_capital_portfolio_summary.csv`",
            "- `docs/reports/task_618_1000_capital_portfolio_comparison/task_618_decision.csv`",
            "",
            "### Outputs",
            "",
            "- `task_619_source_snapshot.csv`",
            "- `task_619_gpt_gate_review_status.csv`",
            "- `task_619_gate_priority_matrix.csv`",
            "- `task_619_implementation_packet.csv`",
            "- `task_619_pass_fail_matrix.csv`",
            "- `task_619_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task619_promotion_gate_update`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task619_promotion_gate_update(out_dir=args.out_dir)
    row = artifacts["task_619_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={row['decision']} top_blocker={row['top_blocker']}")


if __name__ == "__main__":
    main()
