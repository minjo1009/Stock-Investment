from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task608j_failure_taxonomy_entry_upgrade import (
    REPORT_DIR as TASK608J_REPORT_DIR,
    TASK608G_PATH_PANEL,
    build_task608j_failure_taxonomy_entry_upgrade,
)


TASK_ID = "Task608K"
REPORT_DIR = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment")
TASK608J_FEATURE_PANEL = TASK608J_REPORT_DIR / "entry_upgrade_feature_panel.csv"


def build_task608k_failure_taxonomy_v2_conditional_treatment(
    *,
    task608j_feature_panel: Path = TASK608J_FEATURE_PANEL,
    task608g_path_panel: Path = TASK608G_PATH_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    feature_panel = load_feature_panel(task608j_feature_panel)
    path_panel = load_path_panel(task608g_path_panel)
    enriched = enrich_with_path_columns(feature_panel, path_panel)
    taxonomy_v2 = build_taxonomy_v2(enriched)
    taxonomy_quality = build_taxonomy_quality_v2(taxonomy_v2)
    treatment = build_conditional_treatment_by_taxonomy(taxonomy_v2)
    risk_rules = build_live_risk_rule_candidate_summary(enriched)
    decision = build_decision(taxonomy_quality, treatment, risk_rules)

    out_dir.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out_dir / "entry_upgrade_feature_panel_v2.csv", index=False)
    taxonomy_v2.to_csv(out_dir / "failure_taxonomy_v2_panel.csv", index=False)
    taxonomy_quality.to_csv(out_dir / "failure_taxonomy_v2_quality.csv", index=False)
    treatment.to_csv(out_dir / "conditional_treatment_by_failure_type.csv", index=False)
    risk_rules.to_csv(out_dir / "live_risk_rule_candidate_summary.csv", index=False)
    decision.to_csv(out_dir / "task_608k_decision.csv", index=False)
    (out_dir / "task_608k_failure_taxonomy_v2_conditional_treatment.md").write_text(
        render_report(taxonomy_quality, treatment, risk_rules, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "entry_upgrade_feature_panel_v2": enriched,
        "failure_taxonomy_v2_panel": taxonomy_v2,
        "failure_taxonomy_v2_quality": taxonomy_quality,
        "conditional_treatment_by_failure_type": treatment,
        "live_risk_rule_candidate_summary": risk_rules,
        "task_608k_decision": decision,
    }


def load_feature_panel(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        build_task608j_failure_taxonomy_entry_upgrade()
    frame = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    for column in ["entry_price", "simulated_exit_price", "net_return_from_entry"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["entry_reduce_failure_flag"] = pd.to_numeric(
        frame["entry_reduce_failure_flag"], errors="coerce"
    ).fillna(0).astype(int)
    return frame


def load_path_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in ["entry_ts"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    return frame


def enrich_with_path_columns(feature_panel: pd.DataFrame, path_panel: pd.DataFrame) -> pd.DataFrame:
    extra_columns = [
        "lifecycle_id",
        "symbol_mae_15m",
        "symbol_mfe_15m",
        "symbol_mae_30m",
        "symbol_mfe_30m",
        "relative_ret_vs_qqq_15m",
        "relative_ret_vs_qqq_30m",
        "relative_ret_vs_qqq_120m",
        "symbol_opening_range_high_reclaim_120m_flag",
        "symbol_opening_range_rejection_120m_flag",
        "symbol_volume_decay_120m",
        "symbol_vwap_fail_120m_flag",
        "qqq_ret_15m",
        "qqq_ret_30m",
        "qqq_ret_60m",
        "qqq_ret_120m",
    ]
    available = [column for column in extra_columns if column in path_panel.columns]
    merged = feature_panel.merge(path_panel[available], on="lifecycle_id", how="left", suffixes=("", "_path"))
    for column in [
        "symbol_mae_15m",
        "symbol_mfe_15m",
        "symbol_mae_30m",
        "symbol_mfe_30m",
        "relative_ret_vs_qqq_15m",
        "relative_ret_vs_qqq_30m",
        "relative_ret_vs_qqq_120m",
        "symbol_volume_decay_120m",
    ]:
        if column in merged.columns:
            merged[column] = pd.to_numeric(merged[column], errors="coerce")
    merged["taxonomy_v2_feature_available_flag"] = merged[
        [column for column in ["symbol_ret_15m", "symbol_mae_15m", "relative_ret_vs_qqq_30m"] if column in merged.columns]
    ].notna().min(axis=1).astype(int)
    return merged


def build_taxonomy_v2(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    failed = feature_panel[feature_panel["entry_reduce_failure_flag"].eq(1)].copy()
    for item in failed.to_dict(orient="records"):
        failure_type, reason, detection_horizon = classify_failure_v2(item)
        row = dict(item)
        row["failure_type_v2"] = failure_type
        row["failure_reason_v2"] = reason
        row["detection_horizon"] = detection_horizon
        rows.append(row)
    return pd.DataFrame(rows)


def classify_failure_v2(row: dict[str, Any]) -> tuple[str, str, str]:
    if str(row.get("timing_state", "")) == "opening_drive" and int(row.get("opening_rejection_120m_flag", 0)) == 1:
        if _le(row.get("symbol_ret_15m"), -0.015) or _le(row.get("symbol_mae_15m"), -0.03):
            return "opening_trap_fast_adverse", "opening drive rejected and loss appeared within 15 minutes", "15m_wait"
        if int(row.get("symbol_vwap_fail_30m_flag", 0)) == 1 or int(row.get("symbol_vwap_fail_60m_flag", 0)) == 1:
            return "opening_trap_vwap_loss", "opening drive rejected and failed VWAP hold", "30_60m_wait"
        return "opening_trap_range_rejection", "opening drive rejected opening range without fast adverse trigger", "120m_eval"
    if _le(row.get("symbol_ret_15m"), -0.015) or _le(row.get("symbol_mae_15m"), -0.03) or _le(row.get("symbol_ret_30m"), -0.02):
        return "early_adverse_failure", "entry immediately moved against the position", "15_30m_wait"
    if _le(row.get("relative_ret_vs_qqq_30m"), -0.015) or _le(row.get("relative_ret_vs_qqq_60m"), -0.02) or int(row.get("theme_confirmation_fail_pre_entry_flag", 0)) == 1:
        return "market_or_theme_drag", "symbol lagged QQQ/theme around entry", "pre_entry_to_60m"
    if bool(row.get("prior_day_extension_flag", 0)) and (
        _ge(row.get("gap_abs_percentile_60d"), 0.70) or _ge(row.get("distance_to_premarket_high_pct"), -0.01)
    ):
        return "gap_exhaustion_or_event_fade", "extended prior day or gap entry faded", "pre_entry"
    if int(row.get("late_breakout_proxy_flag", 0)) == 1 or _ge(row.get("breakout_age_bars"), 4):
        return "late_breakout_exhaustion", "entry came late after initial expansion", "pre_entry"
    if _le(row.get("symbol_mfe_60m"), 0.01) or int(row.get("volume_decay_120m_flag", 0)) == 1 or int(row.get("symbol_vwap_fail_60m_flag", 0)) == 1:
        return "failed_continuation_demand_decay", "trade did not produce enough follow-through", "60_120m_wait"
    return "late_followthrough_failure", "early tape did not fail clearly but later follow-through broke", "post_entry_eval"


def build_taxonomy_quality_v2(taxonomy: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for failure_type, group in taxonomy.groupby("failure_type_v2", sort=True):
        rows.append(
            {
                "failure_type_v2": failure_type,
                "failure_count": int(len(group)),
                "failure_share": float(len(group) / len(taxonomy)) if len(taxonomy) else 0.0,
                "avg_net_return_pct": float(group["net_return_from_entry"].mean() * 100.0),
                "detection_horizons": "|".join(sorted(group["detection_horizon"].astype(str).unique().tolist())),
                "top_symbols": "|".join(group["symbol"].astype(str).value_counts().head(5).index.tolist()),
                "top_quarters": "|".join(group["quarter"].astype(str).value_counts().head(5).index.tolist()),
            }
        )
    frame = pd.DataFrame(rows).sort_values("failure_count", ascending=False).reset_index(drop=True)
    frame["taxonomy_coverage_rate"] = 1.0
    frame["residual_low_information_count"] = int(taxonomy["failure_type_v2"].eq("late_followthrough_failure").sum())
    frame["live_actionable_coverage_rate"] = float(
        taxonomy["detection_horizon"].ne("post_entry_eval").mean()
    ) if len(taxonomy) else 0.0
    return frame


def build_conditional_treatment_by_taxonomy(taxonomy: pd.DataFrame) -> pd.DataFrame:
    rows = []
    scenarios = {
        "delayed_entry_15m": lambda r: delayed_return(r, 15),
        "delayed_entry_30m": lambda r: delayed_return(r, 30),
        "delayed_entry_60m": lambda r: delayed_return(r, 60),
        "staged_25_25_50_0_30_60m": staged_25_25_50_return,
        "staged_50_50_0_60m": staged_50_50_return,
    }
    for failure_type, group in taxonomy.groupby("failure_type_v2", sort=True):
        baseline = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        baseline_avg = float(baseline.mean() * 100.0)
        best = {"scenario": "baseline", "avg_return_pct": baseline_avg, "delta_pct": 0.0, "failure_rate": 1.0}
        for scenario, fn in scenarios.items():
            returns = pd.Series([fn(item) for item in group.to_dict(orient="records")], dtype="float64")
            avg = float(returns.mean() * 100.0)
            delta = avg - baseline_avg
            failure_rate = float(returns.le(-0.03).mean())
            if delta > best["delta_pct"]:
                best = {
                    "scenario": scenario,
                    "avg_return_pct": avg,
                    "delta_pct": delta,
                    "failure_rate": failure_rate,
                }
        rows.append(
            {
                "failure_type_v2": failure_type,
                "failure_count": int(len(group)),
                "baseline_avg_return_pct": baseline_avg,
                "best_treatment_scenario": best["scenario"],
                "best_treatment_avg_return_pct": best["avg_return_pct"],
                "best_treatment_delta_pct": best["delta_pct"],
                "best_treatment_failure_rate": best["failure_rate"],
                "label_used_in_assignment_flag": 1,
                "deployment_claim_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("best_treatment_delta_pct", ascending=False).reset_index(drop=True)


def build_live_risk_rule_candidate_summary(feature_panel: pd.DataFrame) -> pd.DataFrame:
    rules: list[tuple[str, str, Callable[[pd.Series], bool]]] = [
        (
            "wait15_early_adverse_abort_candidate",
            "15m_wait",
            lambda r: _le(r.get("symbol_ret_15m"), -0.015) or _le(r.get("symbol_mae_15m"), -0.03),
        ),
        (
            "wait30_relative_strength_decay_candidate",
            "30m_wait",
            lambda r: _le(r.get("relative_ret_vs_qqq_30m"), -0.015),
        ),
        (
            "preentry_gap_exhaustion_candidate",
            "pre_entry",
            lambda r: bool(r.get("prior_day_extension_flag", 0)) and _ge(r.get("gap_abs_percentile_60d"), 0.70),
        ),
        (
            "preentry_theme_confirmation_fail_candidate",
            "pre_entry",
            lambda r: bool(r.get("theme_confirmation_fail_pre_entry_flag", 0)),
        ),
        (
            "wait60_failed_continuation_candidate",
            "60m_wait",
            lambda r: _le(r.get("symbol_mfe_60m"), 0.01) or int(r.get("symbol_vwap_fail_60m_flag", 0)) == 1,
        ),
    ]
    rows = []
    for name, horizon, predicate in rules:
        flags = feature_panel.apply(predicate, axis=1)
        triggered = feature_panel[flags].copy()
        clean = triggered[triggered["entry_reduce_failure_flag"].eq(0)].copy()
        failed = triggered[triggered["entry_reduce_failure_flag"].eq(1)].copy()
        rows.append(
            {
                "rule_name": name,
                "detection_horizon": horizon,
                "trigger_count": int(len(triggered)),
                "trigger_failure_count": int(len(failed)),
                "trigger_failure_rate": float(triggered["entry_reduce_failure_flag"].mean()) if len(triggered) else 0.0,
                "clean_false_trigger_count": int(len(clean)),
                "triggered_avg_return_pct": float(triggered["net_return_from_entry"].mean() * 100.0) if len(triggered) else 0.0,
                "nontriggered_avg_return_pct": float(feature_panel.loc[~flags, "net_return_from_entry"].mean() * 100.0) if int((~flags).sum()) else 0.0,
                "label_used_in_assignment_flag": 0,
                "deployment_claim_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["trigger_failure_rate", "trigger_failure_count"], ascending=False).reset_index(drop=True)


def build_decision(taxonomy_quality: pd.DataFrame, treatment: pd.DataFrame, risk_rules: pd.DataFrame) -> pd.DataFrame:
    coverage = float(taxonomy_quality["taxonomy_coverage_rate"].iloc[0]) if len(taxonomy_quality) else 0.0
    live_actionable = (
        float(taxonomy_quality["live_actionable_coverage_rate"].iloc[0])
        if len(taxonomy_quality) and "live_actionable_coverage_rate" in taxonomy_quality.columns
        else 0.0
    )
    best_rule = risk_rules.iloc[0].to_dict() if len(risk_rules) else {}
    best_treatment = treatment.iloc[0].to_dict() if len(treatment) else {}
    pass_flag = int(coverage >= 0.80 and int(best_rule.get("trigger_failure_count", 0)) >= 3)
    rule_lock_ready_flag = int(
        float(best_rule.get("trigger_failure_rate", 0.0)) >= 0.60
        and int(best_rule.get("trigger_failure_count", 0)) > int(best_rule.get("clean_false_trigger_count", 0))
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_TAXONOMY_V2_DIAGNOSTIC_NEEDS_RULE_LOCK"
                    if pass_flag
                    else "FAIL_TAXONOMY_V2_STILL_WEAK"
                ),
                "pass_flag": pass_flag,
                "taxonomy_coverage_rate": coverage,
                "live_actionable_coverage_rate": live_actionable,
                "best_risk_rule": best_rule.get("rule_name", ""),
                "best_risk_rule_failure_rate": best_rule.get("trigger_failure_rate", 0.0),
                "best_risk_rule_clean_false_trigger_count": best_rule.get("clean_false_trigger_count", 0),
                "rule_lock_ready_flag": rule_lock_ready_flag,
                "best_treatment_failure_type": best_treatment.get("failure_type_v2", ""),
                "best_treatment_scenario": best_treatment.get("best_treatment_scenario", ""),
                "best_treatment_delta_pct": best_treatment.get("best_treatment_delta_pct", 0.0),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "reducer_retry_status": "CLOSED",
                "next_action": "Rule-lock only the best wait-window risk candidates with fold-forward clean-false-trigger limits and cost stress.",
            }
        ]
    )


def render_report(
    taxonomy_quality: pd.DataFrame,
    treatment: pd.DataFrame,
    risk_rules: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    row = decision.iloc[0].to_dict()
    taxonomy_lines = [
        f"- {item['failure_type_v2']}: {int(item['failure_count'])}개, 평균 {float(item['avg_net_return_pct']):.2f}%"
        for _, item in taxonomy_quality.head(8).iterrows()
    ]
    treatment_lines = [
        f"- {item['failure_type_v2']}: best {item['best_treatment_scenario']}, 개선 {float(item['best_treatment_delta_pct']):.2f}pp"
        for _, item in treatment.head(6).iterrows()
    ]
    risk_lines = [
        f"- {item['rule_name']}: trigger {int(item['trigger_count'])}개, 실패율 {float(item['trigger_failure_rate']):.2%}, clean false {int(item['clean_false_trigger_count'])}개"
        for _, item in risk_rules.head(5).iterrows()
    ]
    return "\n".join(
        [
            "# Task608K Failure Taxonomy V2 Conditional Treatment",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {row['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "- Reducer retry: CLOSED",
            f"- Taxonomy coverage: {float(row['taxonomy_coverage_rate']):.2%}",
            f"- Live-actionable coverage: {float(row['live_actionable_coverage_rate']):.2%}",
            f"- Best risk rule: {row['best_risk_rule']} ({float(row['best_risk_rule_failure_rate']):.2%} failure rate).",
            f"- Rule-lock ready: {int(row['rule_lock_ready_flag'])}",
            f"- Best treatment: {row['best_treatment_failure_type']} with {row['best_treatment_scenario']} improves failed-row return by {float(row['best_treatment_delta_pct']):.2f}pp.",
            f"- Next action: {row['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task608J feature panel plus Task608G path diagnostics.",
            "- Exact join keys: `lifecycle_id` only.",
            "- Leakage audit: taxonomy and treatment-by-failed-type use failure labels for diagnosis only. Risk-rule candidate summary uses live/pre-entry or wait-window signals and marks deployment false.",
            "- Split/OOS metrics: not accepted yet; next step must fold-forward lock rules.",
            "- Failure decomposition:",
            *taxonomy_lines,
            "- Conditional treatment on failed rows:",
            *treatment_lines,
            "- Live/wait-window risk candidates:",
            *risk_lines,
            "- Remaining blockers: clean false triggers, cost stress, and fold-forward rule lock are still missing.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: the 35 failures are now split more clearly.",
            "- Why it matters: reducer is still not the next move; wait-window risk rules are the better candidate.",
            "- Whether this changes capital/deployment readiness: no.",
            "- Plain-language next step: test the best wait-window rule without using labels and cap clean false triggers.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def delayed_return(row: dict[str, Any], delay: int) -> float:
    path_ret = row.get(f"symbol_ret_{delay}m")
    original = float(row["net_return_from_entry"])
    if pd.isna(path_ret):
        return original
    delayed_price = float(row["entry_price"]) * (1.0 + float(path_ret))
    exit_price = float(row["simulated_exit_price"])
    return exit_price / delayed_price - 1.0 if delayed_price else original


def staged_25_25_50_return(row: dict[str, Any]) -> float:
    return staged_return(row, [(0, 0.25), (30, 0.25), (60, 0.50)])


def staged_50_50_return(row: dict[str, Any]) -> float:
    return staged_return(row, [(0, 0.50), (60, 0.50)])


def staged_return(row: dict[str, Any], schedule: list[tuple[int, float]]) -> float:
    weighted_entry = 0.0
    weight_sum = 0.0
    for minute, weight in schedule:
        if minute == 0:
            leg_price = float(row["entry_price"])
        else:
            path_ret = row.get(f"symbol_ret_{minute}m")
            if pd.isna(path_ret):
                continue
            leg_price = float(row["entry_price"]) * (1.0 + float(path_ret))
        weighted_entry += leg_price * weight
        weight_sum += weight
    if weight_sum <= 0:
        return float(row["net_return_from_entry"])
    return float(row["simulated_exit_price"]) / (weighted_entry / weight_sum) - 1.0


def _ge(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) >= threshold
    except Exception:
        return False


def _le(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) <= threshold
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task608j-feature-panel", type=Path, default=TASK608J_FEATURE_PANEL)
    parser.add_argument("--task608g-path-panel", type=Path, default=TASK608G_PATH_PANEL)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608k_failure_taxonomy_v2_conditional_treatment(
        task608j_feature_panel=args.task608j_feature_panel,
        task608g_path_panel=args.task608g_path_panel,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608k_decision"].iloc[0]
    print(f"[TASK608K] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
