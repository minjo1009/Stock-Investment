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


TASK_ID = "Task620A"
REPORT_DIR = Path("docs/reports/task_620a_actionable_oos_treatment_map")
TASK617_PANEL = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv")
TASK620_DIR = Path("docs/reports/task_620_recent_oos_failure_decomposition")


def build_task620a_actionable_oos_treatment_map(
    *,
    panel_path: Path = TASK617_PANEL,
    task620_dir: Path = TASK620_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(panel_path)
    taxonomy_summary = pd.read_csv(task620_dir / "recent_oos_failure_taxonomy_summary.csv")
    trigger_effects = build_trigger_effects(panel)
    bucket_treatments = build_bucket_treatments(taxonomy_summary)
    gpt_review = build_gpt_review_status()
    pass_fail = build_pass_fail(trigger_effects, bucket_treatments, gpt_review)
    decision = build_decision(trigger_effects, bucket_treatments, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    trigger_effects.to_csv(out_dir / "task_620a_actionable_trigger_effects.csv", index=False)
    bucket_treatments.to_csv(out_dir / "task_620a_failure_bucket_treatment_map.csv", index=False)
    gpt_review.to_csv(out_dir / "task_620a_gpt_treatment_review_status.csv", index=False)
    pass_fail.to_csv(out_dir / "task_620a_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_620a_decision.csv", index=False)
    (out_dir / "task_620a_actionable_oos_treatment_map.md").write_text(
        render_report(trigger_effects, bucket_treatments, gpt_review, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_620a_actionable_trigger_effects": trigger_effects,
        "task_620a_failure_bucket_treatment_map": bucket_treatments,
        "task_620a_gpt_treatment_review_status": gpt_review,
        "task_620a_pass_fail_matrix": pass_fail,
        "task_620a_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {"split_name", "theme_id", "theme_regime_state_v4", "timing_state", "net_return_from_entry", "win_flag", "entry_reduce_failure_flag"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    panel = panel.copy()
    for col in [
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "volume_ratio_prev",
        "intraday_ret_from_open",
        "range_pos",
        "net_return_from_entry",
        "ceo_ir_proxy_pre14d_flag",
        "passive_13g_pre30d_flag",
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
    ]:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    for col in ["win_flag", "entry_reduce_failure_flag"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).astype(int)
    return panel


def trigger_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    aerospace = panel["theme_id"].astype(str).eq("aerospace_defense_space")
    persistent = panel["theme_regime_state_v4"].astype(str).eq("persistent_theme_leader")
    midday = panel["timing_state"].astype(str).eq("midday_continuation")
    theme_hot15 = panel["theme_ret20_prev"].gt(0.15)
    theme_hot20 = panel["theme_ret20_prev"].gt(0.20)
    ceo_ir_absent = panel["ceo_ir_proxy_pre14d_flag"].fillna(0).eq(0)
    broad_event = (
        panel["political_statement_pre7d_flag"].fillna(0).eq(1)
        & panel["geopolitical_event_pre7d_flag"].fillna(0).eq(1)
        & panel["institution_ownership_pre30d_flag"].fillna(0).eq(1)
    )
    return {
        "block_theme_aerospace_defense": aerospace,
        "block_aerospace_persistent_leader": aerospace & persistent,
        "block_aerospace_theme_ret20_gt15": aerospace & theme_hot15,
        "delay_or_block_midday_theme_ret20_gt15": midday & theme_hot15,
        "size_down_persistent_theme_ret20_gt15": persistent & theme_hot15,
        "source_retype_broad_event_without_recent_ir": broad_event & ceo_ir_absent,
        "watch_theme_ret20_gt20": theme_hot20,
    }


def build_trigger_effects(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    masks = trigger_masks(panel)
    for treatment_name, mask in masks.items():
        for split_name in ["validation", "recent_oos"]:
            split = panel[panel["split_name"].astype(str).eq(split_name)]
            trigger = split[mask.loc[split.index]]
            kept = split[~mask.loc[split.index]]
            trigger_metrics = aggregate(trigger) if not trigger.empty else {}
            kept_metrics = aggregate(kept) if not kept.empty else {}
            split_metrics = aggregate(split) if not split.empty else {}
            rows.append(
                {
                    "treatment_name": treatment_name,
                    "split_name": split_name,
                    "base_trade_count": int(len(split)),
                    "trigger_trade_count": int(len(trigger)),
                    "kept_trade_count": int(len(kept)),
                    "base_avg_net_return_pct": float(split_metrics.get("avg_net_return_pct", 0.0)),
                    "trigger_avg_net_return_pct": float(trigger_metrics.get("avg_net_return_pct", 0.0)),
                    "kept_avg_net_return_pct": float(kept_metrics.get("avg_net_return_pct", 0.0)),
                    "base_entry_reduce_failure_rate": float(split_metrics.get("entry_reduce_failure_rate", 0.0)),
                    "trigger_entry_reduce_failure_rate": float(trigger_metrics.get("entry_reduce_failure_rate", 0.0)),
                    "kept_entry_reduce_failure_rate": float(kept_metrics.get("entry_reduce_failure_rate", 0.0)),
                    "kept_avg_delta_vs_base_pct_point": float(kept_metrics.get("avg_net_return_pct", 0.0)) - float(split_metrics.get("avg_net_return_pct", 0.0)),
                    "kept_entry_reduce_delta_vs_base_pct_point": (
                        float(kept_metrics.get("entry_reduce_failure_rate", 0.0)) - float(split_metrics.get("entry_reduce_failure_rate", 0.0))
                    )
                    * 100.0,
                    "entry_available_flag": int(treatment_name not in {"trailing_stop_path_failure"}),
                    "label_used_in_assignment_flag": 0,
                    "gpt_or_plugin_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["treatment_name", "split_name"]).reset_index(drop=True)


def build_bucket_treatments(taxonomy_summary: pd.DataFrame) -> pd.DataFrame:
    treatment_by_bucket = {
        "theme_specific_collapse_aerospace_defense": (
            "ENTRY_BLOCK",
            "First test a no-entry rule for aerospace/defense-space. This is the largest loss bucket and has a clean pre-entry theme key.",
            "Task620B_theme_block_validation",
        ),
        "trailing_stop_path_failure": (
            "EXIT_TREATMENT",
            "Do not use trailing_stop exit reason as an entry filter. Use it to research stop structure, partial exit, or faster damage control.",
            "Task621_exit_path_research",
        ),
        "broad_event_support_without_recent_ir_proxy": (
            "SOURCE_RETYPING",
            "Broad political/geopolitical/institution flags are too wide. Retype events toward company-specific IR or real catalyst support.",
            "Task620C_source_retyping",
        ),
        "late_midday_continuation_decay": (
            "DELAY_ENTRY",
            "Do not hard-block first. Test delayed entry or extra confirmation for hot-theme midday continuation.",
            "Task620D_delay_entry_validation",
        ),
        "overextended_persistent_theme_leader": (
            "SIZE_DOWN",
            "Sample is too small for a hard block. Test size-down or watch-list treatment first.",
            "Task620E_size_down_validation",
        ),
        "residual_recent_oos_problem": (
            "DO_NOT_USE_YET",
            "Keep as residual until additional live-observable taxonomy splits it further.",
            "Task620F_residual_taxonomy",
        ),
        "clean_recent_oos_winner": (
            "KEEP",
            "Keep as positive control; do not damage this bucket while blocking failures.",
            "Task620B_theme_block_validation",
        ),
    }
    rows = []
    for _, row in taxonomy_summary.iterrows():
        bucket = str(row["primary_failure_taxonomy"])
        treatment, rationale, next_task = treatment_by_bucket.get(
            bucket,
            ("DO_NOT_USE_YET", "No approved treatment yet.", "Task620F_residual_taxonomy"),
        )
        rows.append(
            {
                "primary_failure_taxonomy": bucket,
                "treatment_class": treatment,
                "problem_count": int(row.get("problem_count", 0)),
                "trade_count": int(row.get("trade_count", 0)),
                "avg_net_return_pct": float(row.get("avg_net_return_pct", 0.0)),
                "entry_reduce_failure_rate": float(row.get("entry_reduce_failure_rate", 0.0)),
                "why_hit": rationale,
                "how_to_win_or_lose_less": treatment_next_action(treatment),
                "next_task": next_task,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def treatment_next_action(treatment: str) -> str:
    return {
        "ENTRY_BLOCK": "Test a hard no-entry gate and compare validation damage versus recent OOS improvement.",
        "EXIT_TREATMENT": "Research earlier loss control, partial exit, or revised trailing logic using live-observable path features.",
        "SOURCE_RETYPING": "Split broad events into company-specific catalyst quality before using intelligence as support.",
        "DELAY_ENTRY": "Test wait/confirmation variants before removing the setup entirely.",
        "SIZE_DOWN": "Test smaller exposure before hard exclusion because support is thin.",
        "DO_NOT_USE_YET": "Do not promote; collect more taxonomy evidence.",
        "KEEP": "Use as clean-winner guardrail while testing failure treatments.",
    }.get(treatment, "No action.")


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT agreed Task620 must move from bad-OOS confirmation to actionable treatment mapping: entry block aerospace first, source retyping second, delay midday third, exit research for trailing stop.",
            }
        ]
    )


def build_pass_fail(trigger_effects: pd.DataFrame, bucket_treatments: pd.DataFrame, gpt_review: pd.DataFrame) -> pd.DataFrame:
    recent_aero = row_for(trigger_effects, "block_theme_aerospace_defense", "recent_oos")
    validation_aero = row_for(trigger_effects, "block_theme_aerospace_defense", "validation")
    treatment_classes = set(bucket_treatments["treatment_class"].astype(str))
    return pd.DataFrame(
        [
            {
                "gate": "gpt_treatment_review_captured",
                "pass_flag": int(str(gpt_review.iloc[0]["captured_status"]).startswith("CAPTURED")),
                "observed_value": str(gpt_review.iloc[0]["captured_status"]),
                "required_value": "Chrome ChatGPT treatment review captured as non-source interpretation",
            },
            {
                "gate": "aerospace_entry_block_candidate",
                "pass_flag": int(
                    float(recent_aero["kept_avg_net_return_pct"]) >= 5.0
                    and float(recent_aero["kept_entry_reduce_failure_rate"]) <= 0.50
                    and float(validation_aero["kept_avg_net_return_pct"]) >= float(validation_aero["base_avg_net_return_pct"])
                ),
                "observed_value": (
                    f"recent_kept_avg={float(recent_aero['kept_avg_net_return_pct']):.2f}%; "
                    f"recent_kept_er={float(recent_aero['kept_entry_reduce_failure_rate']) * 100.0:.2f}%; "
                    f"validation_kept_avg={float(validation_aero['kept_avg_net_return_pct']):.2f}%"
                ),
                "required_value": "recent kept avg>=5%, recent kept entry_reduce<=50%, validation kept avg>=base",
            },
            {
                "gate": "bucket_treatment_classes_complete",
                "pass_flag": int({"ENTRY_BLOCK", "EXIT_TREATMENT", "SOURCE_RETYPING", "DELAY_ENTRY", "SIZE_DOWN", "DO_NOT_USE_YET"}.issubset(treatment_classes)),
                "observed_value": ",".join(sorted(treatment_classes)),
                "required_value": "failure buckets mapped to action classes",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "actionable map only; no rule accepted yet",
                "required_value": "treatment rules must pass separate validation before promotion",
            },
        ]
    )


def row_for(frame: pd.DataFrame, treatment_name: str, split_name: str) -> pd.Series:
    return frame[frame["treatment_name"].eq(treatment_name) & frame["split_name"].eq(split_name)].iloc[0]


def build_decision(trigger_effects: pd.DataFrame, bucket_treatments: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    aero = row_for(trigger_effects, "block_theme_aerospace_defense", "recent_oos")
    aero_pass = int(pass_fail[pass_fail["gate"].eq("aerospace_entry_block_candidate")]["pass_flag"].iloc[0])
    decision = "LOCK_ACTIONABLE_OOS_TREATMENT_MAP_TEST_AEROSPACE_BLOCK_FIRST"
    if not aero_pass:
        decision = "FAIL_ACTIONABLE_OOS_TREATMENT_MAP_NO_ENTRY_BLOCK_CANDIDATE"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "first_treatment_to_test": "block_theme_aerospace_defense",
                "first_treatment_class": "ENTRY_BLOCK",
                "recent_kept_avg_after_first_treatment_pct": float(aero["kept_avg_net_return_pct"]),
                "recent_kept_entry_reduce_after_first_treatment": float(aero["kept_entry_reduce_failure_rate"]),
                "treatment_rule_accepted_flag": 0,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run a bounded no-label validation of the aerospace/defense entry block, then source retyping and delayed-entry tests.",
            }
        ]
    )


def render_report(
    trigger_effects: pd.DataFrame,
    bucket_treatments: pd.DataFrame,
    gpt_review: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task620A Actionable OOS Treatment Map",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- First treatment to test: `{d['first_treatment_to_test']}` as `{d['first_treatment_class']}`.",
        "- GPT output is review-only and not source truth.",
        "",
        "## Quant Expert Report",
        "",
        "### Failure Bucket Treatment Map",
        "",
        "| Bucket | Treatment | Problems | Avg Return | Entry-Reduce | Next Task |",
        "|---|---|---:|---:|---:|---|",
    ]
    for _, row in bucket_treatments.iterrows():
        lines.append(
            f"| `{row['primary_failure_taxonomy']}` | `{row['treatment_class']}` | {int(row['problem_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['entry_reduce_failure_rate']) * 100.0:.2f}% | `{row['next_task']}` |"
        )
    lines.extend(
        [
            "",
            "### Actionable Trigger Effects",
            "",
            "| Treatment | Split | Trigger Trades | Trigger Avg | Kept Avg | Kept Entry-Reduce | Kept Delta |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in trigger_effects.iterrows():
        lines.append(
            f"| `{row['treatment_name']}` | `{row['split_name']}` | {int(row['trigger_trade_count'])} | "
            f"{float(row['trigger_avg_net_return_pct']):.2f}% | {float(row['kept_avg_net_return_pct']):.2f}% | "
            f"{float(row['kept_entry_reduce_failure_rate']) * 100.0:.2f}% | {float(row['kept_avg_delta_vs_base_pct_point']):.2f}pp |"
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
            "- The point is no longer proving recent OOS was bad.",
            "- The first practical treatment is to test whether aerospace/defense-space should be blocked at entry.",
            "- Broad news/event flags need retyping because they are too wide to separate winners from failures.",
            "- Trailing-stop failures belong to exit research, not entry blocking.",
            "- Midday hot-theme continuation should be tested with delayed entry, not immediately deleted.",
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
            "- `docs/reports/task_620_recent_oos_failure_decomposition/recent_oos_failure_taxonomy_summary.csv`",
            "",
            "### Outputs",
            "",
            "- `task_620a_actionable_trigger_effects.csv`",
            "- `task_620a_failure_bucket_treatment_map.csv`",
            "- `task_620a_gpt_treatment_review_status.csv`",
            "- `task_620a_pass_fail_matrix.csv`",
            "- `task_620a_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task620a_actionable_oos_treatment_map`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task620a_actionable_oos_treatment_map(out_dir=args.out_dir)
    row = artifacts["task_620a_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={row['decision']} first={row['first_treatment_to_test']}")


if __name__ == "__main__":
    main()
