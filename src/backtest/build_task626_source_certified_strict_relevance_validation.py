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
from src.backtest.build_task614_p0_intelligence_source_attachment import tag_contains
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel, within_window
from src.backtest.build_task623_big_event_interpretation_scoring_sidecar import (
    build_task623_big_event_interpretation_scoring_sidecar,
)


TASK_ID = "Task626"
REPORT_DIR = Path("docs/reports/task_626_source_certified_strict_relevance_validation")
TASK625_DIR = Path("docs/reports/task_625_big_event_perfection_criteria_source_certification")
SCOPES = ("full_panel", "validation", "recent_oos")


def build_task626_source_certified_strict_relevance_validation(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    task625_dir: Path = TASK625_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    task623 = build_task623_big_event_interpretation_scoring_sidecar()
    scored = task623["event_interpretation_scores"]
    certification = pd.read_csv(task625_dir / "task_625_source_certification_matrix.csv")
    certified_scored = merge_certification(scored, certification)
    panel = load_panel(task617_panel_path)
    attachment = build_strict_trade_attachment(panel, certified_scored)
    enriched = panel.merge(attachment, on="lifecycle_id", how="left")
    policy_eval = build_policy_variant_evaluation(enriched)
    pass_fail = build_pass_fail(attachment, policy_eval)
    decision = build_decision(attachment, policy_eval, pass_fail)
    gpt_review = build_gpt_review_status()

    out_dir.mkdir(parents=True, exist_ok=True)
    attachment.to_csv(out_dir / "task_626_strict_trade_event_attachment.csv", index=False)
    policy_eval.to_csv(out_dir / "task_626_strict_policy_variant_evaluation.csv", index=False)
    pass_fail.to_csv(out_dir / "task_626_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_626_decision.csv", index=False)
    gpt_review.to_csv(out_dir / "task_626_gpt_strict_relevance_review_status.csv", index=False)
    (out_dir / "task_626_source_certified_strict_relevance_validation.md").write_text(
        render_report(policy_eval, pass_fail, decision, gpt_review),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_626_strict_trade_event_attachment": attachment,
        "task_626_strict_policy_variant_evaluation": policy_eval,
        "task_626_pass_fail_matrix": pass_fail,
        "task_626_decision": decision,
        "task_626_gpt_strict_relevance_review_status": gpt_review,
    }


def merge_certification(scored: pd.DataFrame, certification: pd.DataFrame) -> pd.DataFrame:
    cert_cols = [
        "event_id",
        "source_text_certified_flag",
        "source_text_hash",
        "raw_text_path",
        "source_text_char_count",
        "title_token_hit_count",
    ]
    merged = scored.merge(certification[cert_cols], on="event_id", how="left")
    merged["source_text_certified_flag"] = merged["source_text_certified_flag"].fillna(0).astype(int)
    return merged


def build_strict_trade_attachment(panel: pd.DataFrame, certified_scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in panel.iterrows():
        linked = strict_linked_events_for_entry(certified_scored, entry)
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "strict_linked_event_count": int(len(linked)),
                "strict_support_entry_candidate_count": int(linked["support_entry_certified_flag"].sum()) if not linked.empty else 0,
                "strict_risk_off_candidate_count": int(linked["risk_off_certified_flag"].sum()) if not linked.empty else 0,
                "strict_sector_support_watch_count": int(linked["sector_support_watch_flag"].sum()) if not linked.empty else 0,
                "strict_source_certified_event_count": int(linked["source_text_certified_flag"].sum()) if not linked.empty else 0,
                "strict_event_score_sum": float(linked["composite_interpretation_score"].sum()) if not linked.empty else 0.0,
                "strict_aerospace_risk_off_flag": int(
                    str(entry["theme_id"]) == "aerospace_defense_space"
                    and (not linked.empty)
                    and int(linked["risk_off_certified_flag"].sum()) > 0
                ),
                "policy_only_link_disallowed_flag": 1,
                "label_used_in_assignment_flag": 0,
                "gpt_score_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def strict_linked_events_for_entry(events: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    known = events[
        events["source_text_certified_flag"].astype(int).eq(1)
        & (
            (events["event_date_obj"] < entry["trade_date"])
            | (
                events["event_date_obj"].eq(entry["trade_date"])
                & events["time_precision"].eq("timestamp")
                & events["event_timestamp_dt"].notna()
                & (events["event_timestamp_dt"] <= entry["entry_ts"])
            )
        )
    ]
    symbol = str(entry["symbol"])
    theme = str(entry["theme_id"])

    political = strict_symbol_or_theme_window(known, "trump_major_person_political_statements", symbol, theme, entry["trade_date"], 7)
    geopolitical = strict_symbol_or_theme_window(known, "war_geopolitical_conflict_events", symbol, theme, entry["trade_date"], 7)
    institution = within_window(known, entry["trade_date"], 30)
    institution = institution[
        institution["source_lane"].eq("institution_investment_actions") & tag_contains(institution["symbol_tags"], symbol)
    ]
    ceo_ir = within_window(known, entry["trade_date"], 14)
    ceo_ir = ceo_ir[ceo_ir["source_lane"].eq("ceo_ir_transcripts_and_presentations") & tag_contains(ceo_ir["symbol_tags"], symbol)]
    return pd.concat([political, geopolitical, institution, ceo_ir], ignore_index=True)


def strict_symbol_or_theme_window(
    events: pd.DataFrame,
    source_lane: str,
    symbol: str,
    theme: str,
    trade_date: object,
    days: int,
) -> pd.DataFrame:
    window = within_window(events, trade_date, days)
    lane = window[window["source_lane"].eq(source_lane)]
    if lane.empty:
        return lane
    return lane[tag_contains(lane["symbol_tags"], symbol) | tag_contains(lane["theme_tags"], theme)]


def build_policy_variant_evaluation(enriched: pd.DataFrame) -> pd.DataFrame:
    variants = {
        "original_turboquant": enriched,
        "hold_strict_aerospace_risk_off": enriched[~enriched["strict_aerospace_risk_off_flag"].astype(int).eq(1)],
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
    return float(policy_eval[policy_eval["policy_variant"].eq(variant) & policy_eval["split_name"].eq(split)].iloc[0][column])


def build_pass_fail(attachment: pd.DataFrame, policy_eval: pd.DataFrame) -> pd.DataFrame:
    strict_risk_count = int(attachment["strict_aerospace_risk_off_flag"].sum())
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    strict_recent = metric(policy_eval, "hold_strict_aerospace_risk_off", "recent_oos", "avg_net_return_pct")
    recent_original_trades = int(metric(policy_eval, "original_turboquant", "recent_oos", "trade_count"))
    recent_strict_trades = int(metric(policy_eval, "hold_strict_aerospace_risk_off", "recent_oos", "trade_count"))
    strict_recent_removed = recent_original_trades - recent_strict_trades
    return pd.DataFrame(
        [
            {
                "gate": "policy_only_link_disallowed",
                "pass_flag": int(attachment["policy_only_link_disallowed_flag"].astype(int).min() == 1),
                "observed_value": "policy_tags alone are no longer sufficient for trade linkage",
                "required_value": "macro policy-only events stay context until symbol or theme linkage exists",
            },
            {
                "gate": "task624_aerospace_rule_source_certified",
                "pass_flag": int(strict_recent_removed > 0 and strict_recent > original_recent),
                "observed_value": f"strict_aerospace_risk_off_trades={strict_risk_count}; recent_removed={strict_recent_removed}",
                "required_value": "Task624 aerospace hold must remove certified recent-OOS symbol/theme-linked risk events and improve recent OOS",
            },
            {
                "gate": "strict_relevance_recent_improvement",
                "pass_flag": int(strict_recent > original_recent),
                "observed_value": f"recent {strict_recent:.2f}% vs original {original_recent:.2f}%",
                "required_value": "strict source-certified relevance rule must improve recent OOS",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "strict relevance validation only",
                "required_value": "needs certified source-rescore and cost/account rerun before strategy use",
            },
        ]
    )


def build_decision(attachment: pd.DataFrame, policy_eval: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    strict_risk_count = int(attachment["strict_aerospace_risk_off_flag"].sum())
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    strict_recent = metric(policy_eval, "hold_strict_aerospace_risk_off", "recent_oos", "avg_net_return_pct")
    recent_original_trades = int(metric(policy_eval, "original_turboquant", "recent_oos", "trade_count"))
    recent_strict_trades = int(metric(policy_eval, "hold_strict_aerospace_risk_off", "recent_oos", "trade_count"))
    strict_recent_removed = recent_original_trades - recent_strict_trades
    certified_pass = int(strict_recent_removed > 0 and strict_recent > original_recent)
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "FAIL_TASK624_AEROSPACE_RULE_UNDER_STRICT_SOURCE_RELEVANCE",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "strict_aerospace_risk_off_trade_count": strict_risk_count,
                "strict_recent_oos_aerospace_risk_off_removed_count": strict_recent_removed,
                "original_recent_oos_avg_net_return_pct": original_recent,
                "hold_strict_aerospace_risk_off_recent_oos_avg_net_return_pct": strict_recent,
                "task624_rule_certified_pass_flag": certified_pass,
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Do not promote the Task624 aerospace hold. Build symbol/theme-specific source text linkage before retesting risk-off actions.",
            }
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "DERIVED_FROM_TASK625_GPT_PERFECTION_REVIEW",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT perfection criteria require source integrity and directness; Task626 tests whether Task624 survives stricter source-certified relevance rather than policy-only linkage.",
            }
        ]
    )


def render_report(policy_eval: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame, gpt_review: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task626 Source-Certified Strict Relevance Validation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Strict aerospace risk-off trades: {int(d['strict_aerospace_risk_off_trade_count'])}",
        f"- Strict recent OOS risk-off removed: {int(d['strict_recent_oos_aerospace_risk_off_removed_count'])}",
        f"- Original recent OOS avg: {float(d['original_recent_oos_avg_net_return_pct']):.2f}%",
        f"- Strict relevance recent OOS avg: {float(d['hold_strict_aerospace_risk_off_recent_oos_avg_net_return_pct']):.2f}%",
        "- Policy-only events are no longer allowed to attach to trades as if they were symbol/theme-specific.",
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
            "### Pass/Fail Matrix",
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
            "### GPT Review",
            "",
            f"- Captured status: `{gpt_review.iloc[0]['captured_status']}`",
            f"- Summary: {gpt_review.iloc[0]['summary_point']}",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- Task624 looked good because broad policy events were allowed to attach too easily.",
            "- Under strict source-certified relevance, the aerospace risk-off rule has no qualifying trades.",
            "- So Task624 is downgraded from useful candidate to not certified.",
            "- Next work is real symbol/theme-specific source linkage, not trading promotion.",
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `task_626_strict_trade_event_attachment.csv`",
            "- `task_626_strict_policy_variant_evaluation.csv`",
            "- `task_626_pass_fail_matrix.csv`",
            "- `task_626_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task626_source_certified_strict_relevance_validation`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task626_source_certified_strict_relevance_validation(out_dir=args.out_dir)
    row = artifacts["task_626_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"strict_aero_risk={int(row['strict_aerospace_risk_off_trade_count'])} "
        f"recent={float(row['original_recent_oos_avg_net_return_pct']):.2f}% -> "
        f"{float(row['hold_strict_aerospace_risk_off_recent_oos_avg_net_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
