from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_identity_review_protocol_380 import (
    DEFAULT_OUT_DIR,
    IdentityReviewProtocol380Artifacts,
    build_identity_review_protocol_380,
    write_identity_review_protocol_380,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: IdentityReviewProtocol380Artifacts) -> None:
    protocol = artifacts.identity_review_protocol_candidates
    reviewed = artifacts.reviewed_recovery_layer
    manual = artifacts.manual_review_required_queue
    rejected = artifacts.rejected_recovery_candidates
    namespace_fix = artifacts.namespace_fix_required_queue
    namespace_audit = artifacts.trade_id_namespace_mismatch_audit
    timestamp_audit = artifacts.timestamp_precision_audit
    decision = artifacts.task_380_decision
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(row.get("task_380_verdict", "NOT_YET"))

    lines = [
        "# Task 380 - Identity Review Protocol & Namespace Reconciliation Audit",
        "",
        "## Core Findings",
        f"- total_rows: {int(row.get('total_rows', 0))}",
        f"- approved_recovery_candidate_count: {int(row.get('approved_recovery_candidate_count', 0))}",
        f"- manual_review_required_count: {int(row.get('manual_review_required_count', 0))}",
        f"- rejected_recovery_candidate_count: {int(row.get('rejected_recovery_candidate_count', 0))}",
        f"- namespace_fix_required_count: {int(row.get('namespace_fix_required_count', 0))}",
        f"- accepted_label_update_rows: {int(row.get('accepted_label_update_rows', 0))}",
        f"- task_381_revalidation_ready: {row.get('task_381_revalidation_ready', 'NO')}",
        "",
        "## Required Answers",
        f"- Did Task 380 overwrite labels: `{row.get('labels_overwritten', 'NO')}`",
        f"- Did Task 380 relax Task 376 ontology: `{row.get('task_376_ontology_relaxed', 'NO')}`",
        f"- Did Task 380 promote AMD/semis by theme: `{row.get('theme_promoted_by_task_380', 'NO')}`",
        f"- Reviewed recovery candidates approved: `{int(row.get('approved_recovery_candidate_count', 0))}`",
        f"- Manual review candidates remaining: `{int(row.get('manual_review_required_count', 0))}`",
        f"- Why exact trade_id match is still 0: `{row.get('exact_trade_id_failure_reason', 'price_anchor_mismatch_plus_date_only_timestamp_namespace')}`",
        f"- Is Task 381 revalidation ready: `{row.get('task_381_revalidation_ready', 'NO')}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Protocol candidates generated", not protocol.empty, f"rows={len(protocol)}"),
        _checklist_row("Reviewed recovery layer generated", reviewed is not None, f"rows={len(reviewed)}"),
        _checklist_row("Manual review queue generated", manual is not None, f"rows={len(manual)}"),
        _checklist_row("Rejected queue generated", rejected is not None, f"rows={len(rejected)}"),
        _checklist_row("Namespace fix queue generated", namespace_fix is not None, f"rows={len(namespace_fix)}"),
        _checklist_row("Namespace mismatch audit generated", not namespace_audit.empty, f"rows={len(namespace_audit)}"),
        _checklist_row("Timestamp precision audit generated", not timestamp_audit.empty, f"rows={len(timestamp_audit)}"),
        f"- Final Task 380 verdict: `{verdict}`",
        "",
        "## Task 380 Decision",
        *(_markdown_table(decision)),
        "",
        "## Trade ID Namespace Mismatch Audit",
        *(_markdown_table(namespace_audit)),
        "",
        "## Timestamp Precision Audit",
        *(_markdown_table(timestamp_audit)),
        "",
        "## Reviewed Recovery Layer",
        *(_markdown_table(reviewed.head(50))),
        "",
        "## Manual Review Required Queue",
        *(_markdown_table(manual.head(50))),
        "",
        "## Namespace Fix Required Queue",
        *(_markdown_table(namespace_fix.head(50))),
        "",
        "## Rejected Recovery Candidates",
        *(_markdown_table(rejected.head(50))),
    ]
    (out_dir / "task_380_identity_review_protocol.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 380 identity review protocol and namespace reconciliation audit")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_identity_review_protocol_380()
    write_identity_review_protocol_380(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
