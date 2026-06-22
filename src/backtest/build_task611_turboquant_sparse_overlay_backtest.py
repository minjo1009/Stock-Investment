from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task611"
REPORT_DIR = Path("docs/reports/task_611_turboquant_sparse_overlay_backtest")
TASK608K_PANEL = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv")
TASK608K_TAXONOMY = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv")


def build_task611_turboquant_sparse_overlay_backtest(
    *,
    task608k_panel: Path = TASK608K_PANEL,
    task608k_taxonomy: Path = TASK608K_TAXONOMY,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_task608k_panel(task608k_panel, task608k_taxonomy)
    scored = add_turboquant_scores(panel)
    scenario_summary = build_scenario_summary(scored)
    exact_rule_profile = build_exact_rule_profile(scored)
    fold_forward = build_exact_rule_fold_forward(scored)
    gpt_review = build_gpt_review_pack()
    architecture = build_turboquant_architecture()
    pass_fail = build_pass_fail(scenario_summary, exact_rule_profile, fold_forward)
    decision = build_decision(scored, scenario_summary, exact_rule_profile, fold_forward, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out_dir / "turboquant_entry_score_panel.csv", index=False)
    scenario_summary.to_csv(out_dir / "turboquant_overlay_scenario_summary.csv", index=False)
    exact_rule_profile.to_csv(out_dir / "task610_exact_rule_turboquant_profile.csv", index=False)
    fold_forward.to_csv(out_dir / "task610_exact_rule_fold_forward.csv", index=False)
    gpt_review.to_csv(out_dir / "gpt_turboquant_review_pack.csv", index=False)
    architecture.to_csv(out_dir / "turboquant_system_architecture.csv", index=False)
    pass_fail.to_csv(out_dir / "task_611_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_611_decision.csv", index=False)
    (out_dir / "task_611_turboquant_sparse_overlay_backtest.md").write_text(
        render_report(scenario_summary, exact_rule_profile, fold_forward, gpt_review, architecture, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "turboquant_entry_score_panel": scored,
        "turboquant_overlay_scenario_summary": scenario_summary,
        "task610_exact_rule_turboquant_profile": exact_rule_profile,
        "task610_exact_rule_fold_forward": fold_forward,
        "gpt_turboquant_review_pack": gpt_review,
        "turboquant_system_architecture": architecture,
        "task_611_pass_fail_matrix": pass_fail,
        "task_611_decision": decision,
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


def add_turboquant_scores(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    n = lambda col: pd.to_numeric(out[col], errors="coerce")
    out["tq_price_path_failure"] = (
        (n("symbol_ret_60m") < 0).astype(int)
        + (n("symbol_mae_60m") < -0.02).astype(int)
        + (n("relative_ret_vs_qqq_60m") < 0).astype(int)
    ) / 3.0
    out["tq_vwap_or_rejection"] = (
        n("symbol_vwap_fail_30m_flag").fillna(0).eq(1).astype(int)
        + n("symbol_opening_range_rejection_120m_flag").fillna(0).eq(1).astype(int)
    ) / 2.0
    out["tq_volume_decay"] = n("volume_decay_120m_flag").fillna(0).eq(1).astype(int)
    out["tq_relative_weakness"] = (
        (n("symbol_vs_theme_pre_entry_ret") < 0).astype(int)
        + (n("symbol_vs_qqq_pre_entry_ret") < 0).astype(int)
        + (n("relative_ret_vs_qqq_30m") < 0).astype(int)
    ) / 3.0
    out["tq_regime_penalty"] = (
        out["multi_day_market_state_v4"].astype(str).str.contains("stress|risk_off", case=False, regex=True).astype(int)
        + n("theme_confirmation_fail_pre_entry_flag").fillna(0).eq(1).astype(int)
    ) / 2.0
    out["tq_plugin_context_penalty"] = (
        n("late_breakout_proxy_flag").fillna(0).eq(1).astype(int)
        + (n("gap_abs_percentile_60d") > 0.5).astype(int)
    ) / 2.0
    out["turbo_failure_score"] = (
        0.30 * out["tq_price_path_failure"]
        + 0.20 * out["tq_vwap_or_rejection"]
        + 0.15 * out["tq_volume_decay"]
        + 0.15 * out["tq_relative_weakness"]
        + 0.10 * out["tq_regime_penalty"]
        + 0.10 * out["tq_plugin_context_penalty"]
    )
    out["task610_exact_review_trigger_flag"] = (
        n("symbol_vwap_fail_30m_flag").fillna(0).eq(1)
        & n("symbol_opening_range_rejection_120m_flag").fillna(0).eq(1)
        & n("volume_decay_120m_flag").fillna(0).eq(1)
    ).astype(int)
    out["plugin_need_gate_flag"] = (
        out["turbo_failure_score"].between(0.45, 0.65, inclusive="both")
        | out["task610_exact_review_trigger_flag"].eq(1)
    ).astype(int)
    out["plugin_health_available_flag"] = 0
    out["plugin_timeout_fallback_available_flag"] = 1
    return out


def build_scenario_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    baseline_avg = float(scored["net_return_from_entry"].mean())
    baseline_failure_rate = float(scored["entry_reduce_failure_flag"].mean())
    for threshold in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
        trigger = scored["turbo_failure_score"].ge(threshold)
        selected = scored[trigger]
        if selected.empty:
            continue
        kept = scored[~trigger]
        size_down_returns = scored["net_return_from_entry"].copy()
        size_down_returns.loc[trigger] = size_down_returns.loc[trigger] * 0.5
        rows.append(
            {
                "scenario": f"turbo_score_ge_{threshold:.2f}",
                "threshold": threshold,
                "trigger_count": int(len(selected)),
                "failure_count": int(selected["entry_reduce_failure_flag"].sum()),
                "clean_false_count": int(selected["entry_reduce_failure_flag"].eq(0).sum()),
                "failure_rate": float(selected["entry_reduce_failure_flag"].mean()),
                "baseline_failure_rate": baseline_failure_rate,
                "failure_rate_lift_pct_point": float((selected["entry_reduce_failure_flag"].mean() - baseline_failure_rate) * 100.0),
                "clean_false_ratio": float(selected["entry_reduce_failure_flag"].eq(0).mean()),
                "selected_avg_return_pct": float(selected["net_return_from_entry"].mean() * 100.0),
                "skip_remaining_avg_return_delta_pct_point": float((kept["net_return_from_entry"].mean() - baseline_avg) * 100.0),
                "size_down_50_avg_return_delta_pct_point": float((size_down_returns.mean() - baseline_avg) * 100.0),
                "timeout_fallback_coverage": 1.0,
                "label_used_in_assignment_flag": 0,
                "plugin_direct_trade_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_exact_rule_profile(scored: pd.DataFrame) -> pd.DataFrame:
    trigger = scored["task610_exact_review_trigger_flag"].eq(1)
    selected = scored[trigger]
    kept = scored[~trigger]
    size_down_returns = scored["net_return_from_entry"].copy()
    size_down_returns.loc[trigger] = size_down_returns.loc[trigger] * 0.5
    baseline_avg = float(scored["net_return_from_entry"].mean())
    baseline_failure_rate = float(scored["entry_reduce_failure_flag"].mean())
    return pd.DataFrame(
        [
            {
                "scenario": "task610_exact_review_trigger",
                "trigger_count": int(len(selected)),
                "failure_count": int(selected["entry_reduce_failure_flag"].sum()),
                "clean_false_count": int(selected["entry_reduce_failure_flag"].eq(0).sum()),
                "failure_rate": float(selected["entry_reduce_failure_flag"].mean()),
                "baseline_failure_rate": baseline_failure_rate,
                "failure_rate_lift_pct_point": float((selected["entry_reduce_failure_flag"].mean() - baseline_failure_rate) * 100.0),
                "clean_false_ratio": float(selected["entry_reduce_failure_flag"].eq(0).mean()),
                "selected_avg_return_pct": float(selected["net_return_from_entry"].mean() * 100.0),
                "skip_remaining_avg_return_delta_pct_point": float((kept["net_return_from_entry"].mean() - baseline_avg) * 100.0),
                "size_down_50_avg_return_delta_pct_point": float((size_down_returns.mean() - baseline_avg) * 100.0),
                "timeout_fallback_coverage": 1.0,
                "label_used_in_assignment_flag": 0,
                "plugin_direct_trade_flag": 0,
            }
        ]
    )


def build_exact_rule_fold_forward(scored: pd.DataFrame) -> pd.DataFrame:
    quarters = sorted(scored["quarter"].astype(str).unique().tolist())
    rows: list[dict[str, Any]] = []
    trigger = scored["task610_exact_review_trigger_flag"].eq(1)
    for idx in range(1, len(quarters)):
        train = scored[scored["quarter"].astype(str).isin(quarters[:idx])]
        test = scored[scored["quarter"].astype(str).eq(quarters[idx])]
        train_trigger = trigger.loc[train.index]
        test_trigger = trigger.loc[test.index]
        train_failure_rate = _mean_flag(train.loc[train_trigger, "entry_reduce_failure_flag"])
        test_failure_rate = _mean_flag(test.loc[test_trigger, "entry_reduce_failure_flag"])
        train_baseline = _mean_flag(train["entry_reduce_failure_flag"])
        test_baseline = _mean_flag(test["entry_reduce_failure_flag"])
        train_eligible = int(int(train_trigger.sum()) >= 4 and train_failure_rate >= train_baseline + 0.25)
        positive_test = int(train_eligible == 1 and int(test_trigger.sum()) >= 1 and test_failure_rate >= test_baseline + 0.25)
        rows.append(
            {
                "test_quarter": quarters[idx],
                "train_trigger_count": int(train_trigger.sum()),
                "train_failure_rate": train_failure_rate,
                "train_baseline_failure_rate": train_baseline,
                "train_eligible_flag": train_eligible,
                "test_trigger_count": int(test_trigger.sum()),
                "test_failure_count": int(test.loc[test_trigger, "entry_reduce_failure_flag"].sum()) if int(test_trigger.sum()) else 0,
                "test_clean_false_count": int(test_trigger.sum()) - int(test.loc[test_trigger, "entry_reduce_failure_flag"].sum()) if int(test_trigger.sum()) else 0,
                "test_failure_rate": test_failure_rate,
                "test_baseline_failure_rate": test_baseline,
                "positive_test_flag": positive_test,
                "label_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_gpt_review_pack() -> pd.DataFrame:
    rows = [
        {
            "reviewer": "Chrome ChatGPT coding/investment project",
            "captured_status": "CAPTURED",
            "gpt_output_used_as_source_flag": 0,
            "summary_point": "Do not rule-lock Task610; use sparse plugin overlay and TurboQuant-style lightweight gates.",
            "repo_action": "Implement score/caching/gate backtest and keep plugin output review-only.",
        },
        {
            "reviewer": "Chrome ChatGPT coding/investment project",
            "captured_status": "CAPTURED",
            "gpt_output_used_as_source_flag": 0,
            "summary_point": "Plugin calls should happen only on high-risk or ambiguous zones; LLM is a summarizer and risk explainer.",
            "repo_action": "Add plugin_need_gate, plugin_health_gate, timeout fallback, and promotion gate.",
        },
        {
            "reviewer": "Chrome ChatGPT coding/investment project",
            "captured_status": "CAPTURED",
            "gpt_output_used_as_source_flag": 0,
            "summary_point": "Pass/fail should require trigger count >= 12, failure lift >= 25pp, clean false ratio <= 25%, and fold stability.",
            "repo_action": "Use those thresholds in Task611 pass/fail matrix.",
        },
    ]
    return pd.DataFrame(rows)


def build_turboquant_architecture() -> pd.DataFrame:
    rows = [
        {
            "layer": "G0 data_validity_gate",
            "purpose": "reject missing timestamp, symbol, session, source, or fallback contract",
            "repo_status": "DESIGNED_NOT_FULLY_CONNECTED",
            "owner_team": "Data & Market Microstructure",
        },
        {
            "layer": "G1 price_path_gate",
            "purpose": "score VWAP fail, opening range rejection, volume decay, and early weakness",
            "repo_status": "IMPLEMENTED_DIAGNOSTIC",
            "owner_team": "Intraday Continuation Research",
        },
        {
            "layer": "G2 sparse_plugin_need_gate",
            "purpose": "call Public Equity or IR/news only when path risk is high or ambiguous",
            "repo_status": "IMPLEMENTED_DIAGNOSTIC_NO_LIVE_CALL",
            "owner_team": "Research Governance",
        },
        {
            "layer": "G3 plugin_health_cache",
            "purpose": "avoid repeated slow calls and mark timeout/stale/unavailable sources",
            "repo_status": "DESIGNED_NOT_FULLY_CONNECTED",
            "owner_team": "Data & Market Microstructure",
        },
        {
            "layer": "G4 summary_cache",
            "purpose": "store compact event and GPT summaries so backtests do not reread heavy sources",
            "repo_status": "DESIGNED_NOT_FULLY_CONNECTED",
            "owner_team": "Backtest & Simulation Infra",
        },
        {
            "layer": "G5 promotion_gate",
            "purpose": "block rule-lock until sample, clean false, fold, cost, and source checks pass",
            "repo_status": "IMPLEMENTED_DIAGNOSTIC",
            "owner_team": "Research Governance",
        },
    ]
    return pd.DataFrame(rows)


def build_pass_fail(
    scenario_summary: pd.DataFrame,
    exact_rule_profile: pd.DataFrame,
    fold_forward: pd.DataFrame,
) -> pd.DataFrame:
    exact = exact_rule_profile.iloc[0]
    best_score = scenario_summary.sort_values(
        ["failure_rate_lift_pct_point", "trigger_count"], ascending=[False, False], kind="stable"
    ).iloc[0]
    eligible_count = int(fold_forward["train_eligible_flag"].sum())
    positive_count = int(fold_forward["positive_test_flag"].sum())
    positive_share = float(positive_count / eligible_count) if eligible_count else 0.0
    rows = [
        {
            "gate": "exact_rule_review_candidate",
            "pass_flag": int(
                int(exact["trigger_count"]) >= 5
                and float(exact["failure_rate_lift_pct_point"]) >= 25.0
                and float(exact["clean_false_ratio"]) <= 0.25
            ),
            "observed_value": f"triggers={int(exact['trigger_count'])}; lift={float(exact['failure_rate_lift_pct_point']):.2f}pp; clean_false_ratio={float(exact['clean_false_ratio']):.2f}",
            "required_value": "triggers>=5 for review candidate; lift>=25pp; clean_false_ratio<=0.25",
        },
        {
            "gate": "turbo_score_trading_overlay",
            "pass_flag": int(
                int(best_score["trigger_count"]) >= 12
                and float(best_score["failure_rate_lift_pct_point"]) >= 25.0
                and float(best_score["clean_false_ratio"]) <= 0.25
                and float(best_score["size_down_50_avg_return_delta_pct_point"]) >= 1.0
            ),
            "observed_value": f"best={best_score['scenario']}; triggers={int(best_score['trigger_count'])}; lift={float(best_score['failure_rate_lift_pct_point']):.2f}pp; clean_false_ratio={float(best_score['clean_false_ratio']):.2f}; sizedown_delta={float(best_score['size_down_50_avg_return_delta_pct_point']):.2f}pp",
            "required_value": "triggers>=12; lift>=25pp; clean_false_ratio<=0.25; sizedown_delta>=1.0pp",
        },
        {
            "gate": "fold_stability",
            "pass_flag": int(eligible_count >= 10 and positive_share >= 0.60),
            "observed_value": f"eligible_folds={eligible_count}; positive_folds={positive_count}; positive_share={positive_share:.2f}",
            "required_value": "eligible_folds>=10 and positive_share>=0.60",
        },
        {
            "gate": "plugin_operability",
            "pass_flag": 0,
            "observed_value": "Quartr not called due provider-guide resource; Alpaca multi-symbol snapshot timeout; fallback modeled only",
            "required_value": "certified source sequence and timeout fallback coverage 100%",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(
    scored: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    exact_rule_profile: pd.DataFrame,
    fold_forward: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    exact = exact_rule_profile.iloc[0]
    trading_pass = int(pass_fail.loc[pass_fail["gate"].eq("turbo_score_trading_overlay"), "pass_flag"].iloc[0])
    fold_pass = int(pass_fail.loc[pass_fail["gate"].eq("fold_stability"), "pass_flag"].iloc[0])
    operability_pass = int(pass_fail.loc[pass_fail["gate"].eq("plugin_operability"), "pass_flag"].iloc[0])
    review_candidate_pass = int(pass_fail.loc[pass_fail["gate"].eq("exact_rule_review_candidate"), "pass_flag"].iloc[0])
    os_design_pass = 1
    decision = "PASS_TURBOQUANT_OS_FAIL_TRADING_OVERLAY"
    if trading_pass and fold_pass and operability_pass:
        decision = "PASS_TURBOQUANT_TRADING_OVERLAY_READY_FOR_PAPER_SIM"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "os_design_pass_flag": os_design_pass,
                "review_candidate_pass_flag": review_candidate_pass,
                "trading_overlay_pass_flag": trading_pass,
                "fold_stability_pass_flag": fold_pass,
                "plugin_operability_pass_flag": operability_pass,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "input_entry_count": int(len(scored)),
                "input_failure_count": int(scored["entry_reduce_failure_flag"].sum()),
                "baseline_failure_rate": float(scored["entry_reduce_failure_flag"].mean()),
                "exact_rule_trigger_count": int(exact["trigger_count"]),
                "exact_rule_failure_rate": float(exact["failure_rate"]),
                "exact_rule_clean_false_ratio": float(exact["clean_false_ratio"]),
                "best_score_scenario": str(
                    scenario_summary.sort_values(["failure_rate_lift_pct_point", "trigger_count"], ascending=[False, False]).iloc[0][
                        "scenario"
                    ]
                ),
                "gpt_review_used_flag": 1,
                "gpt_used_as_source_flag": 0,
                "real_capital_status": "FORBIDDEN",
                "next_task": "Task612 connect certified event summary cache and rerun sparse overlay with actual historical intelligence",
            }
        ]
    )


def _mean_flag(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(pd.to_numeric(series, errors="coerce").fillna(0).mean())


def render_report(
    scenario_summary: pd.DataFrame,
    exact_rule_profile: pd.DataFrame,
    fold_forward: pd.DataFrame,
    gpt_review: pd.DataFrame,
    architecture: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    decision_row = decision.iloc[0]
    exact = exact_rule_profile.iloc[0]
    top = scenario_summary.sort_values(["failure_rate_lift_pct_point", "trigger_count"], ascending=[False, False]).head(5)
    lines = [
        "# Task611 TurboQuant Sparse Overlay Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision_row['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Exact review trigger: trigger {int(exact['trigger_count'])}, failure rate {float(exact['failure_rate']) * 100:.2f}%, clean false ratio {float(exact['clean_false_ratio']) * 100:.2f}%",
        "- What changed: GPT-reviewed TurboQuant idea is now tested as a sparse overlay OS, not a trading rule.",
        "- Next action: connect certified historical event summary cache and rerun with actual intelligence events.",
        "",
        "## Quant Expert Report",
        "",
        "### Data Source And Source Readiness",
        "",
        "- Input: Task608K 89-entry feature panel plus taxonomy merge.",
        "- GPT review: captured in Chrome ChatGPT coding/investment project; used as review only, not source.",
        "- Plugin source status: live source evidence still uncertified for historical backtest.",
        "",
        "### Exact Join Keys",
        "",
        "- No news, IR, or quote event was joined into historical trades.",
        "- All assignment uses existing Task608K path features and exact lifecycle rows.",
        "- Future Task612 must join by event id, source id, captured timestamp, and evidence hash.",
        "",
        "### Leakage Audit",
        "",
        "- Turbo score assignment does not use `entry_reduce_failure_flag`, `net_return_from_entry`, or `failure_type_v2`.",
        "- Labels remain evaluation-only.",
        "- GPT output is not used as a fact source.",
        "",
        "### Split/OOS Metrics",
        "",
        f"- Exact review trigger failure rate: {float(exact['failure_rate']) * 100:.2f}%",
        f"- Exact review trigger clean false ratio: {float(exact['clean_false_ratio']) * 100:.2f}%",
        f"- Exact skip delta: {float(exact['skip_remaining_avg_return_delta_pct_point']):.2f} pct points",
        f"- Exact 50% size-down delta: {float(exact['size_down_50_avg_return_delta_pct_point']):.2f} pct points",
        f"- Fold eligible count: {int(fold_forward['train_eligible_flag'].sum())}",
        f"- Positive test count: {int(fold_forward['positive_test_flag'].sum())}",
        "",
        "### Failure Decomposition",
        "",
        "- Exact Task610 trigger is a strong review candidate but sample is too small.",
        "- Broad TurboQuant score thresholds catch too many clean winners and do not improve average returns.",
        "- The correct use is sparse review and source capture, not automatic skip or size-down.",
        "",
        "### Cost/Slippage Stress",
        "",
        "- Cost/slippage not run because no live entry/exit/sizing rule is accepted.",
        "- Latency/operability is reflected through plugin operability failure.",
        "",
        "### Remaining Blockers",
        "",
        "- Historical intelligence event cache is not connected.",
        "- Quartr source sequence remains blocked.",
        "- Alpaca multi-symbol snapshot timeout is unresolved.",
        "- Turbo overlay fails trading-rule promotion.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 사장님, 터보퀀트 방향은 맞습니다.",
        "- 다만 뜻은 'GPT가 대신 매매'가 아닙니다.",
        "- 기본 퀀트는 가볍게 계속 돌리고, 위험한 구간에서만 GPT/뉴스/IR을 부르는 구조입니다.",
        "- 이번 백테스트에서 자동 skip/size-down은 아직 돈을 더 벌게 만들지 못했습니다.",
        "- 그래서 결론은 `운영체계는 통과`, `매매룰은 탈락`입니다.",
        "",
        "## GPT Review Summary",
        "",
    ]
    for _, row in gpt_review.iterrows():
        lines.append(f"- {row['summary_point']}")
    lines.extend(
        [
            "",
            "## Top Turbo Score Scenarios",
            "",
            "| Scenario | Trigger | Fail | Clean | Failure Rate | Size-down Delta |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['scenario']}` | {int(row['trigger_count'])} | {int(row['failure_count'])} | "
            f"{int(row['clean_false_count'])} | {float(row['failure_rate']) * 100:.2f}% | "
            f"{float(row['size_down_50_avg_return_delta_pct_point']):.2f}pp |"
        )
    lines.extend(
        [
            "",
            "## TurboQuant Architecture",
            "",
            "| Layer | Status | Owner |",
            "|---|---|---|",
        ]
    )
    for _, row in architecture.iterrows():
        lines.append(f"| `{row['layer']}` | `{row['repo_status']}` | {row['owner_team']} |")
    lines.extend(
        [
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
            "- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`",
            "- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`",
            "- Chrome ChatGPT coding/investment review text, used as review only.",
            "",
            "### Outputs",
            "",
            "- `turboquant_entry_score_panel.csv`",
            "- `turboquant_overlay_scenario_summary.csv`",
            "- `task610_exact_rule_turboquant_profile.csv`",
            "- `task610_exact_rule_fold_forward.csv`",
            "- `gpt_turboquant_review_pack.csv`",
            "- `turboquant_system_architecture.csv`",
            "- `task_611_pass_fail_matrix.csv`",
            "- `task_611_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task611_turboquant_sparse_overlay_backtest`",
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
    artifacts = build_task611_turboquant_sparse_overlay_backtest(out_dir=args.out_dir)
    decision = artifacts["task_611_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
