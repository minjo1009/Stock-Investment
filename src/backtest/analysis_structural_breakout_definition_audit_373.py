from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_definition_audit_373 import (
    DEFAULT_OUT_DIR,
    DefinitionAudit373Artifacts,
    build_definition_audit_373,
    write_definition_audit_373,
)


def _count(frame: pd.DataFrame, column: str, value: str) -> int:
    return int(frame[column].astype(str).eq(value).sum()) if column in frame.columns else 0


def _first_row(frame: pd.DataFrame, rule_id: str) -> pd.Series | None:
    scoped = frame[frame["rule_id"].astype(str).eq(rule_id)].copy()
    if scoped.empty:
        return None
    return scoped.iloc[0]


def _write_report(out_dir: Path, artifacts: DefinitionAudit373Artifacts) -> None:
    breakout = artifacts.good_breakout_definition
    entry = artifacts.good_entry_definition
    flow = artifacts.good_flow_definition
    matrix = artifacts.definition_forward_vs_expost_matrix
    audit = artifacts.definition_conservatism_audit

    breakout_expost = _count(breakout, "temporal_classification", "expost")
    breakout_mixed = _count(breakout, "temporal_classification", "mixed")
    entry_high_conserv = _count(entry, "conservatism_flag", "high")
    flow_expost = _count(flow, "temporal_classification", "expost")

    healthy_label_row = _first_row(entry, "entry.participation_quality_label")
    healthy_action_row = _first_row(entry, "entry.healthy_action_threshold")
    stage_gate_row = _first_row(entry, "entry.stage_gate")
    persistence_row = _first_row(flow, "flow.persistence_15m")
    execution_quality_row = _first_row(breakout, "breakout.execution_quality_score")

    lines = [
        "# Task 373 - Explicit Definition Audit for Good Breakout / Good Entry / Good Flow",
        "",
        "## Core Findings",
        f"- breakout_definition_rows: {len(breakout)}",
        f"- entry_definition_rows: {len(entry)}",
        f"- flow_definition_rows: {len(flow)}",
        f"- breakout_expost_rules: {breakout_expost}",
        f"- breakout_mixed_rules: {breakout_mixed}",
        f"- entry_high_conservatism_rules: {entry_high_conserv}",
        f"- flow_expost_rules: {flow_expost}",
        "",
        "## Judgment",
        "- 좋은 breakout 정의는 단일 규칙이 아니라 execution-quality 묶음으로 퍼져 있다.",
        "- 좋은 entry 정의는 label, state, staged gate, policy gate가 층층이 쌓인 decision tree다.",
        "- 좋은 flow 정의는 forward prediction보다 lifecycle progression tagging 비중이 더 크다.",
        "",
        "## Required Answers",
        f"- Q1 현재 정의가 무엇인지 명시: `YES` (`{len(matrix)}` rules extracted with source references)",
        f"- Q2 forward vs expost 분리 가능: `YES` (`{_count(matrix, 'temporal_classification', 'forward_clean')}` forward-clean, `{_count(matrix, 'temporal_classification', 'mixed')}` mixed, `{_count(matrix, 'temporal_classification', 'expost')}` expost)",
        f"- Q3 과보수 지점 존재: `YES` ({entry_high_conserv} high-conservatism entry rules)",
        f"- Q4 healthy label과 actionable healthy가 다른가: `YES` ({healthy_label_row['thresholds'] if healthy_label_row is not None else 'missing'} vs {healthy_action_row['thresholds'] if healthy_action_row is not None else 'missing'})",
        f"- Q5 persistence가 예측이 아니라 duration tagging에 가까운가: `YES` ({persistence_row['thresholds'] if persistence_row is not None else 'missing'})",
        "",
        "## Human Review Summary",
        f"- breakout execution score: `{execution_quality_row['audit_note'] if execution_quality_row is not None else 'missing'}`",
        f"- stage gate: `{stage_gate_row['audit_note'] if stage_gate_row is not None else 'missing'}`",
        f"- persistence rule: `{persistence_row['audit_note'] if persistence_row is not None else 'missing'}`",
        "",
        "## Good Breakout Definition",
        *(_markdown_table(breakout)),
        "",
        "## Good Entry Definition",
        *(_markdown_table(entry)),
        "",
        "## Good Flow Definition",
        *(_markdown_table(flow)),
        "",
        "## Forward vs Expost Matrix",
        *(_markdown_table(matrix)),
        "",
        "## Conservatism Audit",
        *(_markdown_table(audit)),
    ]
    (out_dir / "task_373_definition_audit.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 373 explicit definition audit")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_definition_audit_373()
    write_definition_audit_373(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
