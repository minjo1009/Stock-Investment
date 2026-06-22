from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_lifecycle_recovery_378 import (
    DEFAULT_OUT_DIR,
    LifecycleRecovery378Artifacts,
    build_lifecycle_recovery_378,
    write_lifecycle_recovery_378,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: LifecycleRecovery378Artifacts) -> None:
    matches = artifacts.lifecycle_recovery_candidate_matches
    priority = artifacts.recovery_priority_status
    anchored = artifacts.anchored_oos_recovery_audit
    core = artifacts.core_miss_root_cause_audit
    theme = artifacts.theme_leader_root_cause_audit
    adequacy = artifacts.lifecycle_recovery_sample_adequacy
    decision = artifacts.task_378_decision
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(row.get("task_378_verdict", "NOT_YET"))

    lines = [
        "# Task 378 - Lifecycle Recovery & Core Miss Root-Cause Audit",
        "",
        "## Core Findings",
        f"- missing_rows: {int(row.get('missing_rows', 0))}",
        f"- candidate_recovery_rows: {int(row.get('candidate_recovery_rows', 0))}",
        f"- candidate_recovery_share: {row.get('candidate_recovery_share', 0)}",
        f"- p0_p1_missing_rows: {int(row.get('p0_p1_missing_rows', 0))}",
        f"- p0_p1_symbol_session_recovery_rows: {int(row.get('p0_p1_symbol_session_recovery_rows', 0))}",
        f"- accepted_label_update_rows: {int(row.get('accepted_label_update_rows', 0))}",
        f"- strategy_acceptance_status: {row.get('strategy_acceptance_status', 'UNCHANGED_EXPANDED_SAMPLE_REQUIRED')}",
        f"- next_priority: {row.get('next_priority', 'expanded_lifecycle_capture_required')}",
        "",
        "## Required Answers",
        f"- Did Task 378 relax Task 376 ontology: `{row.get('task_376_ontology_relaxed', 'NO')}`",
        f"- Did Task 378 promote AMD/semis by theme: `{row.get('theme_promoted_by_task_378', 'NO')}`",
        f"- How many missing rows have symbol/date recovery candidates: `{int(row.get('candidate_recovery_rows', 0))}`",
        f"- How many P0/P1 rows are recoverable by symbol/date: `{int(row.get('p0_p1_symbol_session_recovery_rows', 0))}`",
        f"- Is anchored OOS core absence now interpretable: `{row.get('anchored_oos_core_absence_interpretable', 'NO')}`",
        f"- Next concrete recovery action: `{row.get('next_priority', 'expanded_lifecycle_capture_required')}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Lifecycle recovery candidate matches generated", not matches.empty, f"rows={len(matches)}"),
        _checklist_row("Recovery priority status generated", not priority.empty, f"rows={len(priority)}"),
        _checklist_row("Anchored OOS recovery audit generated", not anchored.empty, f"rows={len(anchored)}"),
        _checklist_row("Core miss root-cause audit generated", not core.empty, f"rows={len(core)}"),
        _checklist_row("Theme leader root-cause audit generated", not theme.empty, f"rows={len(theme)}"),
        _checklist_row("Sample adequacy generated", not adequacy.empty, f"rows={len(adequacy)}"),
        f"- Final Task 378 verdict: `{verdict}`",
        "",
        "## Task 378 Decision",
        *(_markdown_table(decision)),
        "",
        "## Lifecycle Recovery Sample Adequacy",
        *(_markdown_table(adequacy)),
        "",
        "## Lifecycle Recovery Candidate Matches",
        *(_markdown_table(matches.head(50))),
        "",
        "## Recovery Priority Status",
        *(_markdown_table(priority.head(50))),
        "",
        "## Anchored OOS Recovery Audit",
        *(_markdown_table(anchored.head(50))),
        "",
        "## Core Miss Root-Cause Audit",
        *(_markdown_table(core.head(50))),
        "",
        "## Theme Leader Root-Cause Audit",
        *(_markdown_table(theme.head(50))),
    ]
    (out_dir / "task_378_lifecycle_recovery.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 378 lifecycle recovery and root-cause audit")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_lifecycle_recovery_378()
    write_lifecycle_recovery_378(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
