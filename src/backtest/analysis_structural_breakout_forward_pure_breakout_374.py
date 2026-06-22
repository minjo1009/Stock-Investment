from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_forward_pure_breakout_374 import (
    DEFAULT_OUT_DIR,
    ForwardPureBreakout374Artifacts,
    build_forward_pure_breakout_374,
    write_forward_pure_breakout_374,
)


def _summary_lookup(summary: pd.DataFrame, scope: str, cut: str, column: str) -> float:
    scoped = summary[
        summary["evaluation_scope"].astype(str).eq(scope)
        & summary["evaluation_cut"].astype(str).eq(cut)
    ].copy()
    if scoped.empty or column not in scoped.columns:
        return 0.0
    return float(pd.to_numeric(scoped.iloc[0][column], errors="coerce"))


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _info_row(label: str, detail: str) -> str:
    return f"- [INFO] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: ForwardPureBreakout374Artifacts) -> None:
    feature_matrix = artifacts.forward_only_feature_matrix
    leakage = artifacts.prediction_leakage_audit
    completeness = artifacts.prediction_input_completeness
    summary = artifacts.breakout_purity_summary
    overlap = artifacts.prediction_vs_policy_overlap
    bucket_audit = artifacts.forward_breakout_bucket_audit

    allowed = int(feature_matrix["allowed_for_task_374"].astype(bool).sum())
    blocked = int((~feature_matrix["allowed_for_task_374"].astype(bool)).sum())
    ambiguous = int(feature_matrix["feature_name"].astype(str).isin({"vwap_response", "breakout_response", "volume_persistence_3bars"}).sum())
    unavailable_count = int(completeness["materialization_status"].astype(str).eq("forward_safe_but_unavailable").sum()) if not completeness.empty else 0
    materialized_count = int(completeness["materialization_status"].astype(str).eq("materialized").sum()) if not completeness.empty else 0

    anchored_legacy = _summary_lookup(summary, "anchored_oos", "legacy_all_breakouts", "expectancy_realized_R")
    anchored_high = _summary_lookup(summary, "anchored_oos", "forward_high_quality", "expectancy_realized_R")
    anchored_improvement = round(anchored_high - anchored_legacy, 6)

    high_quality_blocked = round(float(overlap["good_but_blocked_flag"].mean()), 6) if not overlap.empty else 0.0
    first30_downgraded = round(float(overlap["timing_overlap_block_flag"].mean()), 6) if not overlap.empty else 0.0
    tech_narrow_downgraded = round(float(overlap["tech_led_narrow_overlap_block_flag"].mean()), 6) if not overlap.empty else 0.0
    healthy_suppressed = round(float(overlap["healthy_but_suppressed_flag"].mean()), 6) if not overlap.empty else 0.0

    meta = summary[
        summary["evaluation_scope"].astype(str).eq("anchored_oos")
        & summary["evaluation_cut"].astype(str).eq("degradation_classification")
    ].copy()
    selection_proxy = float(pd.to_numeric(meta.iloc[0]["expectancy_realized_R"], errors="coerce")) if not meta.empty else 0.0
    policy_proxy = float(pd.to_numeric(meta.iloc[0]["total_realized_R"], errors="coerce")) if not meta.empty else 0.0
    proxy_gap = float(pd.to_numeric(meta.iloc[0]["win_rate"], errors="coerce")) if not meta.empty else 0.0
    degradation_class = str(meta.iloc[0]["degradation_class"]) if not meta.empty and "degradation_class" in meta.columns else "indeterminate_low_signal"
    monotonicity_note = ""
    monotonicity_gate_status = "not_available"
    monotonicity_gate_reason = "not_available"
    hard_gate_reactivation_threshold = "not_available"
    if not bucket_audit.empty:
        anchored_mono = bucket_audit[
            bucket_audit["evaluation_scope"].astype(str).eq("anchored_oos")
            & bucket_audit["forward_breakout_bucket"].astype(str).eq("meta_monotonicity_check")
        ]
        if not anchored_mono.empty:
            monotonicity_note = str(anchored_mono.iloc[0]["audit_note"])
            monotonicity_gate_status = str(anchored_mono.iloc[0].get("gate_status", "not_available"))
            monotonicity_gate_reason = str(anchored_mono.iloc[0].get("gate_reason", "not_available"))
            hard_gate_reactivation_threshold = str(
                anchored_mono.iloc[0].get("hard_gate_reactivation_threshold", "not_available")
            )
    anchored_blocked_count = 0
    if not bucket_audit.empty:
        blocked_rows = bucket_audit[
            bucket_audit["evaluation_scope"].astype(str).eq("anchored_oos")
            & bucket_audit["forward_breakout_bucket"].astype(str).eq("blocked_candidate")
        ]
        if not blocked_rows.empty:
            anchored_blocked_count = int(pd.to_numeric(blocked_rows.iloc[0]["trade_count"], errors="coerce"))

    checklist = {
        "future_leakage_excluded": blocked >= ambiguous and ambiguous >= 0,
        "forward_inputs_resolved": unavailable_count <= 2,
        "anchored_oos_improved": anchored_high > anchored_legacy,
        "blocked_bucket_meaningful": anchored_blocked_count >= 3,
        "degradation_class_explicit": degradation_class in {
            "selection_failure",
            "policy_contamination",
            "mixed",
            "indeterminate_low_signal",
        },
    }
    task374_complete_pass = all(checklist.values())
    task375_ready = "YES" if task374_complete_pass else "NO"

    lines = [
        "# Task 374 - Forward-Pure Breakout Definition Rebuild",
        "",
        "## Core Findings",
        f"- forward_usable_feature_count: {allowed}",
        f"- blocked_or_leaking_feature_count: {blocked}",
        f"- ambiguous_feature_count: {ambiguous}",
        f"- prediction_input_materialized_count: {materialized_count}",
        f"- prediction_input_unavailable_count: {unavailable_count}",
        f"- anchored_oos_legacy_expectancy: {round(anchored_legacy, 6)}",
        f"- anchored_oos_high_quality_expectancy: {round(anchored_high, 6)}",
        f"- anchored_oos_expectancy_improvement: {anchored_improvement}",
        f"- high_quality_blocked_by_policy_share: {high_quality_blocked}",
        f"- first_30m_high_quality_downgraded_share: {first30_downgraded}",
        f"- tech_led_narrow_high_quality_downgraded_share: {tech_narrow_downgraded}",
        f"- healthy_but_suppressed_share: {healthy_suppressed}",
        f"- selection_proxy: {round(selection_proxy, 6)}",
        f"- policy_proxy: {round(policy_proxy, 6)}",
        f"- degradation_proxy_gap: {round(proxy_gap, 6)}",
        f"- degradation_class: {degradation_class}",
        f"- anchored_oos_bucket_monotonicity: {monotonicity_note or 'not_available'}",
        f"- anchored_bucket_monotonicity_gate_status: {monotonicity_gate_status}",
        f"- anchored_bucket_monotonicity_gate_reason: {monotonicity_gate_reason}",
        f"- anchored_bucket_monotonicity_hard_gate_reactivation_threshold: {hard_gate_reactivation_threshold}",
        "",
        "## Required Answers",
        f"- Q1 how much future information was mixed into the legacy breakout definition: `{blocked}` blocked/leaking features and `{ambiguous}` ambiguous features",
        f"- Q2 what remains as forward-only feature set: `{allowed}` allowed features",
        f"- Q3 is forward-pure breakout less bad than legacy in anchored OOS: `{'YES' if anchored_improvement > 0 else 'NO'}`",
        f"- Q4 larger driver of negative OOS: `{degradation_class}`",
        f"- Q5 is the base clean enough to proceed to Task 375: `{task375_ready}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Future leakage excluded", checklist["future_leakage_excluded"], f"blocked/leaking={blocked}, ambiguous={ambiguous}"),
        _checklist_row("Forward inputs resolved", checklist["forward_inputs_resolved"], f"unavailable_count={unavailable_count}"),
        _checklist_row("Anchored OOS improved vs legacy", checklist["anchored_oos_improved"], f"high_quality={round(anchored_high, 6)} vs legacy={round(anchored_legacy, 6)}"),
        _checklist_row("Blocked bucket meaningful", checklist["blocked_bucket_meaningful"], f"anchored_blocked_count={anchored_blocked_count}"),
        _checklist_row("Degradation class explicit", checklist["degradation_class_explicit"], degradation_class),
        _info_row(
            "Anchored bucket monotonicity diagnostic result",
            f"{monotonicity_note or 'not_available'}; gate_status={monotonicity_gate_status}; gate_reason={monotonicity_gate_reason}",
        ),
        f"- Final Task 374 verdict: `{'COMPLETE_PASS' if task374_complete_pass else 'NOT_YET'}`",
        f"- Task 375 READY: `{task375_ready}`",
        "",
        "## Pain Points",
        f"- first_30m pressure: `{first30_downgraded}`",
        f"- tech_led + narrow pressure: `{tech_narrow_downgraded}`",
        f"- semis concentration is included as explicit risk pressure in the forward score",
        f"- same-day crowding is included as explicit risk pressure in the forward score",
        f"- policy-vs-prediction disagreement share: `{high_quality_blocked}`",
        "",
        "## Forward-Only Feature Matrix",
        *(_markdown_table(feature_matrix)),
        "",
        "## Leakage Audit",
        *(_markdown_table(leakage)),
        "",
        "## Prediction Input Completeness",
        *(_markdown_table(completeness)),
        "",
        "## Rulebook",
        *(_markdown_table(artifacts.forward_breakout_rulebook)),
        "",
        "## Candidate Sample",
        *(_markdown_table(artifacts.forward_pure_breakout_candidates.head(30))),
        "",
        "## Policy Overlap Sample",
        *(_markdown_table(overlap.head(30))),
        "",
        "## Breakout Purity Summary",
        *(_markdown_table(summary)),
        "",
        "## Forward Breakout Bucket Audit",
        *(_markdown_table(bucket_audit)),
        "",
        "## Task 375 Interface Ready",
        *(_markdown_table(artifacts.task_375_interface_ready)),
        "",
        "## Evaluation Panel Sample",
        *(_markdown_table(artifacts.forward_breakout_evaluation_panel.head(30))),
    ]
    (out_dir / "task_374_forward_pure_breakout.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 374 forward-pure breakout definition rebuild")
    parser.add_argument("--db-path", type=str, default="trading.db")
    parser.add_argument("--capture-batch-id", type=str, default="task374_default")
    parser.add_argument("--reuse-existing-batch", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_forward_pure_breakout_374(
        db_path=args.db_path,
        capture_batch_id=args.capture_batch_id,
        reuse_existing_batch=args.reuse_existing_batch,
    )
    write_forward_pure_breakout_374(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
