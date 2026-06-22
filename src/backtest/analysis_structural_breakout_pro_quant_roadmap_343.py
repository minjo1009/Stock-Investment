from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table


DEFAULT_OUT_DIR = Path("docs/reports/task_343_pro_quant_development_roadmap")
TASK340_FINAL = Path("docs/reports/task_340_subset_validation/task_340_final_decision.csv")
TASK341_FINAL = Path("docs/reports/task_341_subset_refinement/task_341_final_decision.csv")
TASK342_FINAL = Path("docs/reports/task_342_conditional_edge_integration/task_342_final_decision.csv")


def _load_snapshot() -> dict[str, dict[str, Any]]:
    task340 = pd.read_csv(TASK340_FINAL).iloc[0].to_dict()
    task341 = pd.read_csv(TASK341_FINAL).iloc[0].to_dict()
    task342 = pd.read_csv(TASK342_FINAL).iloc[0].to_dict()
    return {"task340": task340, "task341": task341, "task342": task342}


def _priority_focus(snapshot: dict[str, dict[str, Any]]) -> str:
    task341 = str(snapshot["task341"]["decision"])
    task342 = str(snapshot["task342"]["decision"])
    if task341 == "REGIME_CONDITIONAL_EDGE" and task342 == "NO_IMPROVEMENT":
        return "portfolio_translation_before_new_signal_search"
    if task342 in {"WEAK_IMPROVEMENT", "MEANINGFUL_IMPROVEMENT"}:
        return "shadow_deployment_preparation"
    return "evidence_strengthening"


def _phase_roadmap(snapshot: dict[str, dict[str, Any]]) -> pd.DataFrame:
    focus = _priority_focus(snapshot)
    rows = [
        {
            "phase_id": "A",
            "phase_name": "intraday_evidence_expansion",
            "priority": 1,
            "current_focus": focus,
            "objective": "Expand covered intraday sample, especially software_internet OOS trades, before making stronger deployment claims.",
            "key_actions": "extend historical intraday archive; rerun tasks 338-342; produce sample-growth sensitivity report",
            "success_gate": "conditional edge persists with larger covered sample and longer rolling history",
            "stop_gate": "edge vanishes after coverage expansion or recent-only effect becomes obvious",
        },
        {
            "phase_id": "B",
            "phase_name": "conditional_priority_overlay",
            "priority": 2,
            "current_focus": focus,
            "objective": "Translate the regime-conditional edge into ranking and slot-priority rather than direct size scaling.",
            "key_actions": "rank condition_met trades higher; compare same-day candidate competition; test max-position and sector-cap priority rules",
            "success_gate": "priority overlay improves Sharpe and drawdown without trade-count collapse",
            "stop_gate": "priority overlay still fails to beat baseline after cost and concentration checks",
        },
        {
            "phase_id": "C",
            "phase_name": "portfolio_construction_integration",
            "priority": 3,
            "current_focus": focus,
            "objective": "Validate whether the conditional edge helps under slot scarcity, sector caps, and crowding pressure.",
            "key_actions": "run contribution decomposition; measure condition-met selection under candidate congestion; inspect symbol/sector dependence",
            "success_gate": "portfolio-level improvement survives cross-section and crowding stress",
            "stop_gate": "benefit is driven by few trades, one sector, or one symbol cluster",
        },
        {
            "phase_id": "D",
            "phase_name": "shadow_monitoring_framework",
            "priority": 4,
            "current_focus": focus,
            "objective": "Build a repeatable live-process monitor before any capital deployment.",
            "key_actions": "define daily logging spec; build edge decay and drift checks; compare live condition bucket vs historical expectation",
            "success_gate": "shadow results align with historical direction and no hidden execution drift appears",
            "stop_gate": "shadow drift diverges materially from backtest behavior",
        },
        {
            "phase_id": "E",
            "phase_name": "live_go_no_go",
            "priority": 5,
            "current_focus": focus,
            "objective": "Allow tiny live capital only after historical and shadow evidence both hold.",
            "key_actions": "small capital overlay; monitor slippage, concentration, and condition-bucket performance; scale only after repeated validation",
            "success_gate": "historical edge + shadow evidence + tiny-live evidence all align",
            "stop_gate": "slippage, concentration, or live decay breaks the edge",
        },
    ]
    return pd.DataFrame(rows)


def _research_priorities(snapshot: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = [
        {
            "priority_rank": 1,
            "research_area": "sample_growth",
            "why_now": "Task 341 found a regime-conditional edge, but Task 342 showed portfolio translation weakness under limited coverage.",
            "target_question": "Does the software_internet conditional edge persist when covered intraday sample expands beyond 390 trades?",
            "primary_artifact": "sample_growth_sensitivity_report",
        },
        {
            "priority_rank": 2,
            "research_area": "priority_overlay",
            "why_now": "Current direct sizing overlay improved some metrics but failed the hybrid_full robustness gate.",
            "target_question": "Does ranking condition_met trades higher work better than multiplying size?",
            "primary_artifact": "conditional_priority_allocation_backtest",
        },
        {
            "priority_rank": 3,
            "research_area": "slot_competition",
            "why_now": "Sparse regime edge is more likely to matter when same-day trade slots are scarce.",
            "target_question": "When multiple breakouts compete on the same day, should condition_met trades get execution priority?",
            "primary_artifact": "same_day_candidate_competition_report",
        },
        {
            "priority_rank": 4,
            "research_area": "shadow_monitoring",
            "why_now": "Backtest evidence is not strong enough for direct deployment, but it is strong enough to justify live-process monitoring.",
            "target_question": "Does live condition-met behavior stay aligned with historical expectation after costs and slippage?",
            "primary_artifact": "shadow_overlay_monitoring_dashboard_spec",
        },
    ]
    return pd.DataFrame(rows)


def _overlay_translation_options() -> pd.DataFrame:
    rows = [
        {
            "overlay_type": "direct_size_multiplier",
            "priority_rank": 3,
            "recommended_use": "backup_only",
            "why": "Task 342 already showed this translation is directionally useful but not robust enough at portfolio level.",
            "acceptance_gate": "must beat ranking overlay after cost stress to remain relevant",
        },
        {
            "overlay_type": "trade_priority_ranking",
            "priority_rank": 1,
            "recommended_use": "primary_next_step",
            "why": "Sparse regime-conditional edge is more naturally expressed as which trade gets filled first, not how much every trade gets sized.",
            "acceptance_gate": "Sharpe up, MDD down, no trade-count collapse, concentration controlled",
        },
        {
            "overlay_type": "capital_slot_allocation",
            "priority_rank": 2,
            "recommended_use": "secondary_next_step",
            "why": "Conditional edge may be most valuable when position slots and sector caps force trade selection.",
            "acceptance_gate": "priority logic improves portfolio outcomes under slot scarcity and crowding pressure",
        },
    ]
    return pd.DataFrame(rows)


def _shadow_monitoring_spec() -> pd.DataFrame:
    rows = [
        {
            "metric_name": "condition_met_trade_count",
            "frequency": "daily",
            "purpose": "Monitor how often the regime-conditional edge appears in live flow.",
            "warning_trigger": "material drop versus recent rolling average",
        },
        {
            "metric_name": "condition_met_vs_non_condition_realized_R",
            "frequency": "daily_and_weekly",
            "purpose": "Check whether the condition bucket still outperforms the neutral bucket.",
            "warning_trigger": "condition bucket underperforms for multiple consecutive windows",
        },
        {
            "metric_name": "drawdown_contribution_by_bucket",
            "frequency": "weekly",
            "purpose": "Identify whether drawdowns are being reduced or merely shifted.",
            "warning_trigger": "condition bucket contributes disproportionately to downside",
        },
        {
            "metric_name": "symbol_sector_concentration",
            "frequency": "daily",
            "purpose": "Prevent edge monetization from collapsing into a few names or one cluster.",
            "warning_trigger": "single symbol or sector dominates live PnL contribution",
        },
        {
            "metric_name": "slippage_drift",
            "frequency": "daily",
            "purpose": "Detect whether execution friction invalidates historical edge assumptions.",
            "warning_trigger": "realized slippage materially exceeds backtest stress assumptions",
        },
    ]
    return pd.DataFrame(rows)


def _kill_criteria() -> pd.DataFrame:
    rows = [
        {
            "criterion_id": "K1",
            "criterion": "expanded_sample_no_repeat",
            "definition": "Expanded covered sample still fails to repeat rolling OOS improvement.",
            "action": "pause further deployment work and downgrade edge to research-only",
        },
        {
            "criterion_id": "K2",
            "criterion": "software_internet_dependence_worsens",
            "definition": "Sector dependence becomes stronger rather than more diversified as evidence grows.",
            "action": "treat edge as niche diagnostic, not scalable overlay",
        },
        {
            "criterion_id": "K3",
            "criterion": "priority_overlay_no_gain",
            "definition": "Ranking or slot-allocation overlay still does not improve Sharpe and drawdown versus baseline.",
            "action": "stop portfolio translation experiments and keep signal as descriptive only",
        },
        {
            "criterion_id": "K4",
            "criterion": "cost_or_slippage_erases_edge",
            "definition": "Reasonable execution friction removes the edge in historical or shadow evaluation.",
            "action": "block live deployment",
        },
        {
            "criterion_id": "K5",
            "criterion": "shadow_drift_mismatch",
            "definition": "Shadow bucket behavior diverges materially from historical direction.",
            "action": "investigate data/process drift before any capital deployment",
        },
    ]
    return pd.DataFrame(rows)


def _go_live_gates() -> pd.DataFrame:
    rows = [
        {
            "gate_id": "G1",
            "gate_name": "expanded_intraday_revalidation",
            "required": True,
            "definition": "Tasks 338-342 rerun on enlarged coverage still support the regime-conditional edge.",
        },
        {
            "gate_id": "G2",
            "gate_name": "priority_overlay_beats_size_overlay",
            "required": True,
            "definition": "Trade-priority or slot-allocation overlay is more robust than direct size scaling.",
        },
        {
            "gate_id": "G3",
            "gate_name": "portfolio_sharpe_and_mdd",
            "required": True,
            "definition": "Portfolio-level Sharpe improves and drawdown does not worsen materially.",
        },
        {
            "gate_id": "G4",
            "gate_name": "concentration_control",
            "required": True,
            "definition": "No extreme symbol or sector concentration emerges from the overlay logic.",
        },
        {
            "gate_id": "G5",
            "gate_name": "shadow_alignment",
            "required": True,
            "definition": "Shadow results remain directionally aligned with historical expectation.",
        },
    ]
    return pd.DataFrame(rows)


def _markdown_report(
    out_dir: Path,
    snapshot: dict[str, dict[str, Any]],
    phase_df: pd.DataFrame,
    priority_df: pd.DataFrame,
    overlay_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    kill_df: pd.DataFrame,
    gates_df: pd.DataFrame,
) -> None:
    task340 = snapshot["task340"]
    task341 = snapshot["task341"]
    task342 = snapshot["task342"]
    lines: list[str] = [
        "# Task 343: Pro Quant Development Roadmap From Current State",
        "",
        "## Current Snapshot",
        "",
        f"- Task 340 subset validation: `{task340['decision']}`",
        f"- Task 341 subset refinement: `{task341['decision']}`",
        f"- Task 342 portfolio integration: `{task342['decision']}`",
        f"- Current best regime condition: `entry_only + high_atr + vol_expanding + sector_group=software_internet`",
        "",
        "## Interpretation",
        "",
        "- Behavior state discovery succeeded, but pre-entry proxy prediction did not.",
        "- True intraday information produced a regime-conditional edge, not a universal one.",
        "- Portfolio-level direct sizing overlay improved some OOS metrics but did not pass robustness and cost gates.",
        "",
        "## Phase Roadmap",
        "",
    ]
    lines.extend(_markdown_table(phase_df[["phase_id", "phase_name", "priority", "objective", "success_gate", "stop_gate"]]))
    lines.extend(
        [
            "",
            "## Research Priorities",
            "",
        ]
    )
    lines.extend(_markdown_table(priority_df[["priority_rank", "research_area", "target_question", "primary_artifact"]]))
    lines.extend(
        [
            "",
            "## Overlay Translation Ranking",
            "",
        ]
    )
    lines.extend(_markdown_table(overlay_df[["priority_rank", "overlay_type", "recommended_use", "acceptance_gate"]]))
    lines.extend(
        [
            "",
            "## Shadow Monitoring",
            "",
        ]
    )
    lines.extend(_markdown_table(shadow_df[["metric_name", "frequency", "purpose", "warning_trigger"]]))
    lines.extend(
        [
            "",
            "## Kill Criteria",
            "",
        ]
    )
    lines.extend(_markdown_table(kill_df[["criterion_id", "criterion", "definition", "action"]]))
    lines.extend(
        [
            "",
            "## Go/No-Go Gates",
            "",
        ]
    )
    lines.extend(_markdown_table(gates_df[["gate_id", "gate_name", "definition"]]))
    lines.extend(
        [
            "",
            "## Practical Next Move",
            "",
            "- First expand intraday evidence and rerun Tasks 338-342.",
            "- Then test ranking / trade-priority overlay before trying any further size-based overlay.",
            "- Only after historical revalidation should shadow monitoring and tiny capital live overlay begin.",
        ]
    )
    (out_dir / "task_343_pro_quant_development_roadmap.md").write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path = DEFAULT_OUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot = _load_snapshot()
    phase_df = _phase_roadmap(snapshot)
    priority_df = _research_priorities(snapshot)
    overlay_df = _overlay_translation_options()
    shadow_df = _shadow_monitoring_spec()
    kill_df = _kill_criteria()
    gates_df = _go_live_gates()

    phase_df.to_csv(output_dir / "task_343_phase_roadmap.csv", index=False)
    priority_df.to_csv(output_dir / "task_343_research_track_priorities.csv", index=False)
    overlay_df.to_csv(output_dir / "task_343_overlay_translation_options.csv", index=False)
    shadow_df.to_csv(output_dir / "task_343_shadow_monitoring_spec.csv", index=False)
    kill_df.to_csv(output_dir / "task_343_kill_criteria.csv", index=False)
    gates_df.to_csv(output_dir / "task_343_go_live_gates.csv", index=False)
    _markdown_report(output_dir, snapshot, phase_df, priority_df, overlay_df, shadow_df, kill_df, gates_df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 343: Pro quant development roadmap from current state.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
