from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_lifecycle_coverage_expansion_377 import (
    DEFAULT_OUT_DIR,
    LifecycleCoverage377Artifacts,
    build_lifecycle_coverage_expansion_377,
    write_lifecycle_coverage_expansion_377,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: LifecycleCoverage377Artifacts) -> None:
    coverage = artifacts.coverage_gap_audit
    anchored = artifacts.anchored_oos_core_miss_audit
    theme = artifacts.theme_leader_miss_audit
    queue = artifacts.recovery_priority_queue
    decision = artifacts.summary_decision
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(row.get("task_377_verdict", "NOT_YET"))

    lines = [
        "# Task 377 - Lifecycle Coverage Expansion & Core Miss Audit",
        "",
        "## Core Findings",
        f"- total_candidates: {int(row.get('total_candidates', 0))}",
        f"- coverage_missing_count: {int(row.get('coverage_missing_count', 0))}",
        f"- coverage_missing_share: {row.get('coverage_missing_share', 0)}",
        f"- anchored_oos_missing_count: {int(row.get('anchored_oos_missing_count', 0))}",
        f"- core_or_watchlist_missing_count: {int(row.get('core_or_watchlist_missing_count', 0))}",
        f"- theme_leader_missing_count: {int(row.get('theme_leader_missing_count', 0))}",
        f"- next_priority: {row.get('next_priority', 'lifecycle_coverage_expansion')}",
        f"- strategy_acceptance_status: {row.get('strategy_acceptance_status', 'UNCHANGED_EXPANDED_SAMPLE_REQUIRED')}",
        "",
        "## Required Answers",
        "- Q1 should Task 376 ontology be relaxed now: `NO`",
        "- Q2 is lifecycle coverage the next bottleneck: `YES`",
        "- Q3 are AMD/semis promoted by theme: `NO`, theme remains diagnostic",
        "- Q4 does this task change strategy acceptance: `NO`, acceptance remains expanded-sample-required",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Coverage gap audit generated", not coverage.empty, f"rows={len(coverage)}"),
        _checklist_row("Anchored OOS core miss audit generated", not anchored.empty, f"rows={len(anchored)}"),
        _checklist_row("Theme leader miss audit generated", not theme.empty, f"rows={len(theme)}"),
        _checklist_row("Recovery priority queue generated", not queue.empty, f"rows={len(queue)}"),
        _checklist_row("Summary decision generated", not decision.empty, f"rows={len(decision)}"),
        f"- Final Task 377 verdict: `{verdict}`",
        "",
        "## Summary Decision",
        *(_markdown_table(decision)),
        "",
        "## Coverage Gap Audit",
        *(_markdown_table(coverage.head(50))),
        "",
        "## Anchored OOS Core Miss Audit",
        *(_markdown_table(anchored.head(50))),
        "",
        "## Theme Leader Miss Audit",
        *(_markdown_table(theme.head(50))),
        "",
        "## Recovery Priority Queue",
        *(_markdown_table(queue.head(50))),
    ]
    (out_dir / "task_377_lifecycle_coverage_expansion.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 377 lifecycle coverage expansion and core miss audit")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_lifecycle_coverage_expansion_377()
    write_lifecycle_coverage_expansion_377(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
