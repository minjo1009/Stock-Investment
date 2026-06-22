from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_lifecycle_identity_reconciliation_379 import (
    DEFAULT_OUT_DIR,
    LifecycleIdentityReconciliation379Artifacts,
    build_lifecycle_identity_reconciliation_379,
    write_lifecycle_identity_reconciliation_379,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: LifecycleIdentityReconciliation379Artifacts) -> None:
    candidates = artifacts.identity_reconciliation_candidates
    audit = artifacts.identity_confidence_audit
    p0p1 = artifacts.p0_p1_identity_review_queue
    high = artifacts.high_confidence_recovered_candidates
    medium = artifacts.medium_confidence_review_queue
    low = artifacts.low_confidence_reject_queue
    namespace = artifacts.identity_namespace_audit
    decision = artifacts.task_379_decision
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(row.get("task_379_verdict", "NOT_YET"))

    lines = [
        "# Task 379 - Lifecycle Identity Reconciliation",
        "",
        "## Core Findings",
        f"- total_rows: {int(row.get('total_rows', 0))}",
        f"- p0_p1_rows: {int(row.get('p0_p1_rows', 0))}",
        f"- high_confidence_rows: {int(row.get('high_confidence_rows', 0))}",
        f"- medium_confidence_rows: {int(row.get('medium_confidence_rows', 0))}",
        f"- low_confidence_rows: {int(row.get('low_confidence_rows', 0))}",
        f"- no_recovery_evidence_rows: {int(row.get('no_recovery_evidence_rows', 0))}",
        f"- accepted_label_update_rows: {int(row.get('accepted_label_update_rows', 0))}",
        f"- strategy_acceptance_status: {row.get('strategy_acceptance_status', 'UNCHANGED_EXPANDED_SAMPLE_REQUIRED')}",
        "",
        "## Required Answers",
        f"- Did Task 379 overwrite labels: `{row.get('labels_overwritten', 'NO')}`",
        f"- Did Task 379 relax Task 376 ontology: `{row.get('task_376_ontology_relaxed', 'NO')}`",
        f"- Did Task 379 promote AMD/semis by theme: `{row.get('theme_promoted_by_task_379', 'NO')}`",
        f"- P0/P1 high confidence candidates: `{int(row.get('p0_p1_high_confidence_rows', 0))}`",
        f"- P0/P1 medium confidence candidates: `{int(row.get('p0_p1_medium_confidence_rows', 0))}`",
        f"- Candidates blocked by price mismatch: `{int(row.get('price_blocked_rows', 0))}`",
        f"- Candidates blocked by timestamp distance: `{int(row.get('time_blocked_rows', 0))}`",
        f"- Replay-derived only candidates: `{int(row.get('replay_derived_only_rows', 0))}`",
        f"- Is Task 381 revalidation ready: `{row.get('task_381_revalidation_ready', 'NO')}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Identity reconciliation candidates generated", not candidates.empty, f"rows={len(candidates)}"),
        _checklist_row("Identity confidence audit generated", not audit.empty, f"rows={len(audit)}"),
        _checklist_row("P0/P1 review queue generated", not p0p1.empty, f"rows={len(p0p1)}"),
        _checklist_row("High confidence candidates generated", high is not None, f"rows={len(high)}"),
        _checklist_row("Medium confidence queue generated", medium is not None, f"rows={len(medium)}"),
        _checklist_row("Low confidence queue generated", low is not None, f"rows={len(low)}"),
        _checklist_row("Identity namespace audit generated", not namespace.empty, f"rows={len(namespace)}"),
        f"- Final Task 379 verdict: `{verdict}`",
        "",
        "## Task 379 Decision",
        *(_markdown_table(decision)),
        "",
        "## Identity Confidence Audit",
        *(_markdown_table(audit)),
        "",
        "## Identity Namespace Audit",
        *(_markdown_table(namespace)),
        "",
        "## P0/P1 Identity Review Queue",
        *(_markdown_table(p0p1.head(50))),
        "",
        "## High Confidence Recovered Candidates",
        *(_markdown_table(high.head(50))),
        "",
        "## Medium Confidence Review Queue",
        *(_markdown_table(medium.head(50))),
        "",
        "## Low Confidence Reject Queue",
        *(_markdown_table(low.head(50))),
    ]
    (out_dir / "task_379_lifecycle_identity_reconciliation.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 379 lifecycle identity reconciliation")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_lifecycle_identity_reconciliation_379()
    write_lifecycle_identity_reconciliation_379(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
