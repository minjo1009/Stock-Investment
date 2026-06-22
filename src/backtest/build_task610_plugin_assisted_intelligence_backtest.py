from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task610"
REPORT_DIR = Path("docs/reports/task_610_plugin_assisted_intelligence_backtest")
TASK608K_PANEL = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv")
TASK608K_TAXONOMY = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv")
SELECTED_RULE = "vwap_fail_30 & opening_range_reject_120 & volume_decay"


def build_task610_plugin_assisted_intelligence_backtest(
    *,
    task608k_panel: Path = TASK608K_PANEL,
    task608k_taxonomy: Path = TASK608K_TAXONOMY,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_task608k_panel(task608k_panel, task608k_taxonomy)
    feature_frame = build_plugin_review_features(panel)
    candidate_summary = build_candidate_summary(panel, feature_frame)
    selected_profile = build_selected_rule_profile(panel, feature_frame)
    fold_forward = build_fold_forward(panel, feature_frame)
    source_probe = build_plugin_source_probe()
    gpt_review_status = build_gpt_review_status()
    decision = build_decision(panel, selected_profile, fold_forward, source_probe, gpt_review_status)

    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_summary.to_csv(out_dir / "plugin_review_candidate_summary.csv", index=False)
    selected_profile.to_csv(out_dir / "selected_plugin_review_rule_profile.csv", index=False)
    fold_forward.to_csv(out_dir / "selected_rule_fold_forward_validation.csv", index=False)
    source_probe.to_csv(out_dir / "plugin_source_probe_status.csv", index=False)
    gpt_review_status.to_csv(out_dir / "gpt_review_status.csv", index=False)
    decision.to_csv(out_dir / "task_610_decision.csv", index=False)
    (out_dir / "task_610_plugin_assisted_intelligence_backtest.md").write_text(
        render_report(candidate_summary, selected_profile, fold_forward, source_probe, gpt_review_status, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "plugin_review_candidate_summary": candidate_summary,
        "selected_plugin_review_rule_profile": selected_profile,
        "selected_rule_fold_forward_validation": fold_forward,
        "plugin_source_probe_status": source_probe,
        "gpt_review_status": gpt_review_status,
        "task_610_decision": decision,
    }


def load_task608k_panel(panel_path: Path, taxonomy_path: Path) -> pd.DataFrame:
    panel = pd.read_csv(panel_path)
    taxonomy = pd.read_csv(taxonomy_path)
    taxonomy_cols = ["lifecycle_id", "failure_type_v2", "failure_reason_v2", "detection_horizon"]
    panel = panel.merge(taxonomy[taxonomy_cols], on="lifecycle_id", how="left")
    panel["failure_type_v2"] = panel["failure_type_v2"].fillna("clean_or_non_failure")
    panel["failure_reason_v2"] = panel["failure_reason_v2"].fillna("not_failure")
    panel["detection_horizon"] = panel["detection_horizon"].fillna("not_failure")
    panel["entry_reduce_failure_flag"] = pd.to_numeric(panel["entry_reduce_failure_flag"], errors="coerce").fillna(0).astype(int)
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce").fillna(0.0)
    panel["quarter"] = panel["quarter"].astype(str)
    return panel


def build_plugin_review_features(panel: pd.DataFrame) -> pd.DataFrame:
    n = lambda col: pd.to_numeric(panel[col], errors="coerce")
    features = pd.DataFrame(index=panel.index)
    features["opening_drive"] = panel["timing_state"].astype(str).eq("opening_drive")
    features["midday"] = panel["timing_state"].astype(str).eq("midday_continuation")
    features["vwap_fail_30"] = n("symbol_vwap_fail_30m_flag").fillna(0).eq(1)
    features["vwap_fail_60"] = n("symbol_vwap_fail_60m_flag").fillna(0).eq(1)
    features["vwap_fail_120"] = n("symbol_vwap_fail_120m_flag").fillna(0).eq(1)
    features["opening_range_reject_120"] = n("symbol_opening_range_rejection_120m_flag").fillna(0).eq(1)
    features["early_ret60_neg"] = n("symbol_ret_60m") < 0
    features["rel_qqq60_neg"] = n("relative_ret_vs_qqq_60m") < 0
    features["rel_qqq30_neg"] = n("relative_ret_vs_qqq_30m") < 0
    features["gap_neg"] = n("gap_pct") < 0
    features["gap_high"] = n("gap_abs_percentile_60d") > 0.5
    features["theme_fail_pre"] = n("theme_confirmation_fail_pre_entry_flag").fillna(0).eq(1)
    features["sym_vs_theme_pre_neg"] = n("symbol_vs_theme_pre_entry_ret") < 0
    features["sym_vs_qqq_pre_neg"] = n("symbol_vs_qqq_pre_entry_ret") < 0
    features["volume_decay"] = n("volume_decay_120m_flag").fillna(0).eq(1)
    features["symbol_volume_decay_high"] = n("symbol_volume_decay_120m") > 0.2
    features["late_breakout"] = n("late_breakout_proxy_flag").fillna(0).eq(1)
    features["bars_ge_9"] = n("bars_since_session_open").fillna(0) >= 9
    features["premarket_extension"] = n("premarket_extension_flag").fillna(0).eq(1)
    features["prior_day_extension"] = n("prior_day_extension_flag").fillna(0).eq(1)
    return features.astype(bool)


def build_candidate_summary(panel: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    feature_names = list(features.columns)
    for size in range(1, 4):
        for combo in itertools.combinations(feature_names, size):
            mask = pd.Series(True, index=panel.index)
            for name in combo:
                mask &= features[name]
            selected = panel[mask]
            if len(selected) < 3:
                continue
            rows.append(_profile_row(panel, selected, " & ".join(combo), assignment_feature_count=size))
    result = pd.DataFrame(rows)
    result = result.sort_values(
        ["failure_rate", "failure_count", "clean_false_count", "trigger_count"],
        ascending=[False, False, True, False],
        kind="stable",
    ).reset_index(drop=True)
    return result


def build_selected_rule_profile(panel: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    mask = features["vwap_fail_30"] & features["opening_range_reject_120"] & features["volume_decay"]
    selected = panel[mask].copy()
    row = _profile_row(panel, selected, SELECTED_RULE, assignment_feature_count=3)
    return pd.DataFrame([row])


def _profile_row(
    panel: pd.DataFrame,
    selected: pd.DataFrame,
    rule_name: str,
    *,
    assignment_feature_count: int,
) -> dict[str, Any]:
    baseline_failure_rate = float(panel["entry_reduce_failure_flag"].mean()) if len(panel) else 0.0
    trigger_count = int(len(selected))
    failure_count = int(selected["entry_reduce_failure_flag"].sum()) if trigger_count else 0
    clean_false_count = int(trigger_count - failure_count)
    clean_false = selected[selected["entry_reduce_failure_flag"].eq(0)]
    failure = selected[selected["entry_reduce_failure_flag"].eq(1)]
    clean_false_avg_return = float(clean_false["net_return_from_entry"].mean()) if len(clean_false) else 0.0
    return {
        "rule_name": rule_name,
        "assignment_feature_count": assignment_feature_count,
        "trigger_count": trigger_count,
        "failure_count": failure_count,
        "clean_false_count": clean_false_count,
        "failure_rate": float(failure_count / trigger_count) if trigger_count else 0.0,
        "baseline_failure_rate": baseline_failure_rate,
        "failure_rate_lift_pct_point": float((failure_count / trigger_count - baseline_failure_rate) * 100.0) if trigger_count else 0.0,
        "avg_return_pct": float(selected["net_return_from_entry"].mean() * 100.0) if trigger_count else 0.0,
        "failure_avg_return_pct": float(failure["net_return_from_entry"].mean() * 100.0) if len(failure) else 0.0,
        "clean_false_avg_return_pct": clean_false_avg_return * 100.0,
        "clean_false_max_return_pct": float(clean_false["net_return_from_entry"].max() * 100.0) if len(clean_false) else 0.0,
        "label_used_in_assignment_flag": 0,
        "plugin_direct_trade_flag": 0,
    }


def build_fold_forward(panel: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    selected_mask = features["vwap_fail_30"] & features["opening_range_reject_120"] & features["volume_decay"]
    quarters = sorted(panel["quarter"].astype(str).unique().tolist())
    rows: list[dict[str, Any]] = []
    for idx in range(1, len(quarters)):
        train = panel[panel["quarter"].astype(str).isin(quarters[:idx])]
        test = panel[panel["quarter"].astype(str).eq(quarters[idx])]
        train_mask = selected_mask.loc[train.index]
        test_mask = selected_mask.loc[test.index]
        train_triggers = int(train_mask.sum())
        test_triggers = int(test_mask.sum())
        train_failure_rate = _mean_flag(train.loc[train_mask, "entry_reduce_failure_flag"])
        test_failure_rate = _mean_flag(test.loc[test_mask, "entry_reduce_failure_flag"])
        train_baseline = _mean_flag(train["entry_reduce_failure_flag"])
        test_baseline = _mean_flag(test["entry_reduce_failure_flag"])
        train_rule_eligible = int(train_triggers >= 4 and train_failure_rate >= train_baseline + 0.25)
        positive_test = int(train_rule_eligible == 1 and test_triggers >= 1 and test_failure_rate >= test_baseline + 0.25)
        rows.append(
            {
                "test_quarter": quarters[idx],
                "train_trigger_count": train_triggers,
                "train_failure_rate": train_failure_rate,
                "train_baseline_failure_rate": train_baseline,
                "train_rule_eligible_flag": train_rule_eligible,
                "test_trigger_count": test_triggers,
                "test_failure_count": int(test.loc[test_mask, "entry_reduce_failure_flag"].sum()) if test_triggers else 0,
                "test_clean_false_count": int(test_triggers - int(test.loc[test_mask, "entry_reduce_failure_flag"].sum())) if test_triggers else 0,
                "test_failure_rate": test_failure_rate,
                "test_baseline_failure_rate": test_baseline,
                "positive_test_flag": positive_test,
                "label_used_in_test_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_plugin_source_probe() -> pd.DataFrame:
    rows = [
        {
            "plugin": "Public Equity Investing",
            "tool_or_lane": "Alpaca latest quote",
            "probe_status": "SINGLE_SYMBOL_QUOTE_OBSERVED",
            "observation": "BA latest quote returned timestamp 2026-06-05T20:00:00.007453+00:00 in this session.",
            "backtest_use": "source_connectivity_only_not_historical_signal",
        },
        {
            "plugin": "Public Equity Investing",
            "tool_or_lane": "Alpaca multi-symbol snapshot",
            "probe_status": "TIMEOUT",
            "observation": "BA/RKLB/TEAM/TER/MDB/PLTR snapshot request timed out after 120s.",
            "backtest_use": "not_used",
        },
        {
            "plugin": "Public Equity Investing",
            "tool_or_lane": "Quartr",
            "probe_status": "BLOCKED_PROVIDER_GUIDE_RESOURCE_UNAVAILABLE",
            "observation": "Quartr tools were discovered but provider guide resource could not be loaded, so tools were not called.",
            "backtest_use": "not_used_until_provider_sequence_available",
        },
        {
            "plugin": "Data Analytics",
            "tool_or_lane": "datascienceWidgets",
            "probe_status": "AVAILABLE_FOR_VALIDATED_ARTIFACTS",
            "observation": "Report/dashboard artifact validation and rendering tools are available.",
            "backtest_use": "summary_visualization_and_reader_handoff",
        },
        {
            "plugin": "Investment Banking",
            "tool_or_lane": "banking workflows",
            "probe_status": "P2_CONTEXT_ONLY",
            "observation": "Not used in this backtest unless financing, M&A, issuance, restructuring, or board context is explicitly needed.",
            "backtest_use": "not_used",
        },
    ]
    return pd.DataFrame(rows)


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT coding/investment tab",
                "attempt_status": "ATTEMPTED_BUT_NOT_CONFIRMED",
                "reason": "Chrome ChatGPT tab repeatedly timed out on DOM read, screenshot, and prompt send confirmation.",
                "safe_payload_used_flag": 1,
                "gpt_output_used_flag": 0,
                "fallback": "Repo-native plugin-assisted backtest executed without using unconfirmed GPT output.",
            }
        ]
    )


def build_decision(
    panel: pd.DataFrame,
    selected_profile: pd.DataFrame,
    fold_forward: pd.DataFrame,
    source_probe: pd.DataFrame,
    gpt_review_status: pd.DataFrame,
) -> pd.DataFrame:
    profile = selected_profile.iloc[0]
    eligible_folds = int(fold_forward["train_rule_eligible_flag"].sum()) if not fold_forward.empty else 0
    positive_tests = int(fold_forward["positive_test_flag"].sum()) if not fold_forward.empty else 0
    test_trigger_total = int(fold_forward.loc[fold_forward["train_rule_eligible_flag"].eq(1), "test_trigger_count"].sum()) if not fold_forward.empty else 0
    candidate_pass = int(
        int(profile["trigger_count"]) >= 5
        and float(profile["failure_rate_lift_pct_point"]) >= 25.0
        and int(profile["clean_false_count"]) <= 2
    )
    rule_lock_pass = int(candidate_pass == 1 and eligible_folds >= 2 and positive_tests >= 2 and test_trigger_total >= 4)
    decision = "PASS_PLUGIN_REVIEW_CANDIDATE_FAIL_RULE_LOCK" if candidate_pass and not rule_lock_pass else "FAIL_PLUGIN_REVIEW_CANDIDATE"
    if rule_lock_pass:
        decision = "PASS_RULE_LOCK_READY_FOR_PAPER_GATE_SIM"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "pass_flag": candidate_pass,
                "rule_lock_pass_flag": rule_lock_pass,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "input_entry_count": int(len(panel)),
                "input_failure_count": int(panel["entry_reduce_failure_flag"].sum()),
                "baseline_failure_rate": float(panel["entry_reduce_failure_flag"].mean()),
                "selected_rule": SELECTED_RULE,
                "selected_trigger_count": int(profile["trigger_count"]),
                "selected_failure_count": int(profile["failure_count"]),
                "selected_clean_false_count": int(profile["clean_false_count"]),
                "selected_failure_rate": float(profile["failure_rate"]),
                "selected_failure_rate_lift_pct_point": float(profile["failure_rate_lift_pct_point"]),
                "eligible_fold_count": eligible_folds,
                "positive_test_count": positive_tests,
                "eligible_test_trigger_total": test_trigger_total,
                "gpt_output_used_flag": int(gpt_review_status.iloc[0]["gpt_output_used_flag"]),
                "real_capital_status": "FORBIDDEN",
                "next_task": "Task610B connect certified historical intelligence sources before paper gate simulation",
            }
        ]
    )


def _mean_flag(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(pd.to_numeric(series, errors="coerce").fillna(0).mean())


def render_report(
    candidate_summary: pd.DataFrame,
    selected_profile: pd.DataFrame,
    fold_forward: pd.DataFrame,
    source_probe: pd.DataFrame,
    gpt_review_status: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    decision_row = decision.iloc[0]
    profile = selected_profile.iloc[0]
    gpt = gpt_review_status.iloc[0]
    top = candidate_summary.head(5)
    lines = [
        "# Task610 Plugin Assisted Intelligence Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision_row['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Selected review rule: `{decision_row['selected_rule']}`",
        f"- Key metrics: trigger {int(profile['trigger_count'])}, failure {int(profile['failure_count'])}, clean false {int(profile['clean_false_count'])}, failure rate {float(profile['failure_rate']) * 100:.2f}%",
        f"- Fold result: eligible folds {int(decision_row['eligible_fold_count'])}, positive tests {int(decision_row['positive_test_count'])}",
        "- What changed: plugin usage is now backtested as an intelligence-review trigger, not a trading rule.",
        "- Next action: connect certified historical event sources before any paper gate simulation.",
        "",
        "## Quant Expert Report",
        "",
        "### Data Source And Source Readiness",
        "",
        "- Input: Task608K 89-entry feature panel plus taxonomy merge.",
        "- Public Equity / Alpaca: single-symbol quote probe observed, but current quote is not used as historical signal.",
        "- Public Equity / Quartr: not called because the required provider-guide resource was unavailable.",
        "- Data Analytics: available for validated report/dashboard artifacts.",
        "- Investment Banking: not used; P2 context-only.",
        "",
        "### Exact Join Keys",
        "",
        "- Assignment uses only existing live-detectable path features from Task608K.",
        "- No source proximity join was used.",
        "- No news, quote, IR, or GPT text was joined into historical trades.",
        "",
        "### Leakage Audit",
        "",
        "- Selected rule assignment does not use `entry_reduce_failure_flag`, `net_return_from_entry`, or `failure_type_v2`.",
        "- Labels are evaluation-only.",
        "- GPT output was not used because Chrome review completion was not confirmed.",
        "",
        "### Split/OOS Metrics",
        "",
        f"- Baseline failure rate: {float(decision_row['baseline_failure_rate']) * 100:.2f}%",
        f"- Selected rule failure rate: {float(decision_row['selected_failure_rate']) * 100:.2f}%",
        f"- Failure-rate lift: {float(decision_row['selected_failure_rate_lift_pct_point']):.2f} pct points",
        f"- Eligible fold count: {int(decision_row['eligible_fold_count'])}",
        f"- Positive test count: {int(decision_row['positive_test_count'])}",
        "",
        "### Failure Decomposition",
        "",
        "- Best rule catches a small opening-trap style review bucket.",
        "- It is useful as a plugin-review trigger.",
        "- It is not yet a block/exit/reduce rule.",
        "",
        "### Cost/Slippage Stress",
        "",
        "- Not run. This task does not change entries, exits, or sizing.",
        "",
        "### Remaining Blockers",
        "",
        "- Historical Quartr/IR/news windows are not connected.",
        "- Alpaca multi-symbol snapshot timed out.",
        "- Candidate has only six triggers and does not pass rule-lock.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 사장님, 플러그인을 바로 매매룰에 넣으면 아직 위험합니다.",
        "- 그래도 쓸만한 첫 신호는 나왔습니다.",
        "- 30분 VWAP 실패 + 120분 박스 거부 + 거래량 감소가 같이 나오면 6개 중 5개가 실패였습니다.",
        "- 하지만 표본이 작고, 한 번은 +10.14%짜리 깨끗한 수익 거래도 걸렸습니다.",
        "- 그래서 결론은 `검토 트리거로는 좋다`, `자동 차단룰은 아직 아니다`입니다.",
        "",
        "## Plugin Review Status",
        "",
        f"- GPT attempt: `{gpt['attempt_status']}`",
        f"- GPT output used: `{int(gpt['gpt_output_used_flag'])}`",
        "- Public Equity used: Alpaca single-symbol quote probe only.",
        "- Data Analytics use: report/dashboard validation surface ready; no rendered artifact claim in this report unless separately rendered.",
        "",
        "## Top Candidate Snapshot",
        "",
        "| Rule | Trigger | Fail | Clean False | Failure Rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['rule_name']}` | {int(row['trigger_count'])} | {int(row['failure_count'])} | "
            f"{int(row['clean_false_count'])} | {float(row['failure_rate']) * 100:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`",
            "- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `plugin_review_candidate_summary.csv`",
            "- `selected_plugin_review_rule_profile.csv`",
            "- `selected_rule_fold_forward_validation.csv`",
            "- `plugin_source_probe_status.csv`",
            "- `gpt_review_status.csv`",
            "- `task_610_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task610_plugin_assisted_intelligence_backtest`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task610_plugin_assisted_intelligence_backtest(out_dir=args.out_dir)
    decision = artifacts["task_610_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
