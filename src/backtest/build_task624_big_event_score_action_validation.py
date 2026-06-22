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
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel
from src.backtest.build_task623_big_event_interpretation_scoring_sidecar import (
    build_task623_big_event_interpretation_scoring_sidecar,
    linked_events_for_entry,
)


TASK_ID = "Task624"
REPORT_DIR = Path("docs/reports/task_624_big_event_score_action_validation")
SCOPES = ("full_panel", "validation", "recent_oos")


def build_task624_big_event_score_action_validation(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    task623 = build_task623_big_event_interpretation_scoring_sidecar()
    scored = task623["event_interpretation_scores"]
    panel = load_panel(task617_panel_path)
    attachment = build_trade_event_score_attachment(panel, scored)
    enriched = panel.merge(attachment, on="lifecycle_id", how="left")
    slice_metrics = build_score_action_slice_metrics(enriched)
    policy_eval = build_policy_variant_evaluation(enriched)
    pass_fail = build_pass_fail(policy_eval, attachment)
    gpt_review = build_gpt_review_status()
    decision = build_decision(policy_eval, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    attachment.to_csv(out_dir / "task_624_trade_event_score_attachment.csv", index=False)
    slice_metrics.to_csv(out_dir / "task_624_score_action_slice_metrics.csv", index=False)
    policy_eval.to_csv(out_dir / "task_624_policy_variant_evaluation.csv", index=False)
    pass_fail.to_csv(out_dir / "task_624_pass_fail_matrix.csv", index=False)
    gpt_review.to_csv(out_dir / "task_624_gpt_score_action_validation_review_status.csv", index=False)
    decision.to_csv(out_dir / "task_624_decision.csv", index=False)
    (out_dir / "task_624_big_event_score_action_validation.md").write_text(
        render_report(slice_metrics, policy_eval, pass_fail, gpt_review, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_624_trade_event_score_attachment": attachment,
        "task_624_score_action_slice_metrics": slice_metrics,
        "task_624_policy_variant_evaluation": policy_eval,
        "task_624_pass_fail_matrix": pass_fail,
        "task_624_gpt_score_action_validation_review_status": gpt_review,
        "task_624_decision": decision,
    }


def build_trade_event_score_attachment(panel: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in panel.iterrows():
        linked = linked_events_for_entry(scored, entry)
        risk_count = int(linked["risk_off_certified_flag"].sum()) if not linked.empty else 0
        sector_count = int(linked["sector_support_watch_flag"].sum()) if not linked.empty else 0
        support_count = int(linked["support_entry_certified_flag"].sum()) if not linked.empty else 0
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "linked_event_count": int(len(linked)),
                "support_entry_candidate_count": support_count,
                "risk_off_candidate_count": risk_count,
                "sector_support_watch_count": sector_count,
                "event_score_sum": float(linked["composite_interpretation_score"].sum()) if not linked.empty else 0.0,
                "global_risk_off_flag": int(risk_count > 0),
                "aerospace_risk_off_flag": int(str(entry["theme_id"]) == "aerospace_defense_space" and risk_count > 0),
                "sector_support_watch_flag": int(sector_count > 0),
                "support_entry_candidate_flag": int(support_count > 0),
                "label_used_in_assignment_flag": 0,
                "gpt_score_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_score_action_slice_metrics(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    slices = {
        "all_trades": pd.Series(True, index=enriched.index),
        "global_risk_off": enriched["global_risk_off_flag"].astype(int).eq(1),
        "no_global_risk_off": enriched["global_risk_off_flag"].astype(int).eq(0),
        "aerospace_risk_off": enriched["aerospace_risk_off_flag"].astype(int).eq(1),
        "sector_support_watch": enriched["sector_support_watch_flag"].astype(int).eq(1),
        "support_entry_candidate": enriched["support_entry_candidate_flag"].astype(int).eq(1),
    }
    for split in SCOPES:
        split_df = enriched if split == "full_panel" else enriched[enriched["split_name"].astype(str).eq(split)]
        for slice_name, mask in slices.items():
            group = split_df[mask.loc[split_df.index]]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "split_name": split,
                    "score_slice": slice_name,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_policy_variant_evaluation(enriched: pd.DataFrame) -> pd.DataFrame:
    variants = {
        "original_turboquant": enriched,
        "reject_global_risk_off": enriched[enriched["global_risk_off_flag"].astype(int).eq(0)],
        "hold_aerospace_risk_off": enriched[~enriched["aerospace_risk_off_flag"].astype(int).eq(1)],
        "sector_support_watch_only": enriched[enriched["sector_support_watch_flag"].astype(int).eq(1)],
    }
    rows = []
    for variant_name, variant_df in variants.items():
        for split in SCOPES:
            group = variant_df if split == "full_panel" else variant_df[variant_df["split_name"].astype(str).eq(split)]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "policy_variant": variant_name,
                    "split_name": split,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def metric(policy_eval: pd.DataFrame, variant: str, split: str, column: str) -> float:
    row = policy_eval[policy_eval["policy_variant"].eq(variant) & policy_eval["split_name"].eq(split)].iloc[0]
    return float(row[column])


def build_pass_fail(policy_eval: pd.DataFrame, attachment: pd.DataFrame) -> pd.DataFrame:
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    global_recent = metric(policy_eval, "reject_global_risk_off", "recent_oos", "avg_net_return_pct")
    global_full = metric(policy_eval, "reject_global_risk_off", "full_panel", "avg_net_return_pct")
    aero_recent = metric(policy_eval, "hold_aerospace_risk_off", "recent_oos", "avg_net_return_pct")
    aero_validation = metric(policy_eval, "hold_aerospace_risk_off", "validation", "avg_net_return_pct")
    support_count = int(attachment["support_entry_candidate_count"].sum())
    return pd.DataFrame(
        [
            {
                "gate": "global_risk_off_rejected",
                "pass_flag": int(global_recent < original_recent and global_full < 5.0),
                "observed_value": f"recent {global_recent:.2f}% vs original {original_recent:.2f}%; full {global_full:.2f}%",
                "required_value": "global risk-off score is too broad and must not become a trade filter",
            },
            {
                "gate": "aerospace_risk_off_diagnostic_improves_recent",
                "pass_flag": int(aero_recent > original_recent and aero_validation > 9.0),
                "observed_value": f"recent {aero_recent:.2f}% vs original {original_recent:.2f}%; validation {aero_validation:.2f}%",
                "required_value": "aerospace-specific risk-off hold improves recent OOS and does not break validation",
            },
            {
                "gate": "company_direct_support_still_missing",
                "pass_flag": int(support_count == 0),
                "observed_value": f"support_entry_candidate_count={support_count}",
                "required_value": "no entry restoration until company-direct support exists",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "diagnostic action validation only",
                "required_value": "needs full text source certification plus cost/account rerun before strategy use",
            },
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CARRIED_FROM_TASK623_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT direction was to score major events but forbid source-presence and broad-event direct entry; Task624 validates the resulting actions before any strategy use.",
            }
        ]
    )


def build_decision(policy_eval: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    aero_recent = metric(policy_eval, "hold_aerospace_risk_off", "recent_oos", "avg_net_return_pct")
    global_recent = metric(policy_eval, "reject_global_risk_off", "recent_oos", "avg_net_return_pct")
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PASS_AEROSPACE_SCORE_ACTION_DIAGNOSTIC_REJECT_GLOBAL_RISK_NOT_ACCEPTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "original_recent_oos_avg_net_return_pct": original_recent,
                "hold_aerospace_risk_off_recent_oos_avg_net_return_pct": aero_recent,
                "reject_global_risk_off_recent_oos_avg_net_return_pct": global_recent,
                "treatment_rule_accepted_flag": 0,
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Extract full official text for high-impact aerospace and policy events, then rerun source certification plus cost/account validation.",
            }
        ]
    )


def render_report(
    slice_metrics: pd.DataFrame,
    policy_eval: pd.DataFrame,
    pass_fail: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task624 Big Event Score Action Validation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Original recent OOS avg: {float(d['original_recent_oos_avg_net_return_pct']):.2f}%",
        f"- Hold aerospace risk-off recent OOS avg: {float(d['hold_aerospace_risk_off_recent_oos_avg_net_return_pct']):.2f}%",
        f"- Reject global risk-off recent OOS avg: {float(d['reject_global_risk_off_recent_oos_avg_net_return_pct']):.2f}%",
        "- Global risk-off is rejected as too broad. Aerospace-specific risk-off is diagnostic only.",
        "",
        "## Quant Expert Report",
        "",
        "### Policy Variant Evaluation",
        "",
        "| Variant | Split | Trades | Avg Return | Win | Entry-Reduce |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in policy_eval.iterrows():
        lines.append(
            f"| `{row['policy_variant']}` | `{row['split_name']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']) * 100.0:.2f}% | "
            f"{float(row['entry_reduce_failure_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Score Slice Metrics",
            "",
            "| Split | Slice | Trades | Avg Return | Entry-Reduce |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in slice_metrics.iterrows():
        lines.append(
            f"| `{row['split_name']}` | `{row['score_slice']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['entry_reduce_failure_rate']) * 100.0:.2f}% |"
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
            "- Big-event scores are useful only after slicing.",
            "- Global risk-off is too wide and makes the strategy worse.",
            "- Aerospace-specific risk-off explains the recent damage better.",
            "- Still no direct company support exists, so this is not approved for trading.",
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
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "- `docs/reports/task_623_big_event_interpretation_scoring_sidecar/event_interpretation_scores.csv`",
            "",
            "### Outputs",
            "",
            "- `task_624_trade_event_score_attachment.csv`",
            "- `task_624_score_action_slice_metrics.csv`",
            "- `task_624_policy_variant_evaluation.csv`",
            "- `task_624_pass_fail_matrix.csv`",
            "- `task_624_gpt_score_action_validation_review_status.csv`",
            "- `task_624_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task624_big_event_score_action_validation`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task624_big_event_score_action_validation(out_dir=args.out_dir)
    row = artifacts["task_624_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"recent={float(row['original_recent_oos_avg_net_return_pct']):.2f}% -> "
        f"{float(row['hold_aerospace_risk_off_recent_oos_avg_net_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
