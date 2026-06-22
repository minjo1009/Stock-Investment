from __future__ import annotations

import argparse
from pathlib import Path

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.build_timestamp_price_namespace_repair_381 import (
    DEFAULT_OUT_DIR,
    TimestampPriceNamespaceRepair381Artifacts,
    build_timestamp_price_namespace_repair_381,
    write_timestamp_price_namespace_repair_381,
)


def _checklist_row(label: str, passed: bool, detail: str) -> str:
    return f"- [{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _write_report(out_dir: Path, artifacts: TimestampPriceNamespaceRepair381Artifacts) -> None:
    repair = artifacts.timestamp_price_repair_candidates
    ready = artifacts.namespace_repair_ready_layer
    manual = artifacts.manual_namespace_review_queue
    rejected = artifacts.namespace_repair_rejected
    ts_audit = artifacts.timestamp_repair_audit
    price_audit = artifacts.price_anchor_repair_audit
    decision = artifacts.namespace_repair_decision
    row = decision.iloc[0].to_dict() if not decision.empty else {}
    verdict = str(row.get("task_381_verdict", "NOT_YET"))

    lines = [
        "# Task 381 - Timestamp & Price Anchor Namespace Repair",
        "",
        "## Core Findings",
        f"- total_rows: {int(row.get('total_rows', 0))}",
        f"- date_only_timestamp_rows: {int(row.get('date_only_timestamp_rows', 0))}",
        f"- intraday_timestamp_repair_candidate_rows: {int(row.get('intraday_timestamp_repair_candidate_rows', 0))}",
        f"- price_anchor_minor_mismatch_rows: {int(row.get('price_anchor_minor_mismatch_rows', 0))}",
        f"- price_anchor_material_mismatch_rows: {int(row.get('price_anchor_material_mismatch_rows', 0))}",
        f"- namespace_repair_ready_rows: {int(row.get('namespace_repair_ready_rows', 0))}",
        f"- accepted_label_update_rows: {int(row.get('accepted_label_update_rows', 0))}",
        f"- persistence_revalidation_ready: {row.get('persistence_revalidation_ready', 'NO')}",
        "",
        "## Required Answers",
        f"- Did Task 381 overwrite labels: `{row.get('labels_overwritten', 'NO')}`",
        f"- Did Task 381 relax Task 376 ontology: `{row.get('task_376_ontology_relaxed', 'NO')}`",
        f"- Did Task 381 promote AMD/semis by theme: `{row.get('theme_promoted_by_task_381', 'NO')}`",
        f"- Date-only rows with intraday timestamp repair candidates: `{int(row.get('intraday_timestamp_repair_candidate_rows', 0))}`",
        f"- Price mismatches minor/material: `{int(row.get('price_anchor_minor_mismatch_rows', 0))}` / `{int(row.get('price_anchor_material_mismatch_rows', 0))}`",
        f"- Rows ready for a future reviewed diagnostic layer: `{int(row.get('namespace_repair_ready_rows', 0))}`",
        f"- Is persistence universe revalidation ready: `{row.get('persistence_revalidation_ready', 'NO')}`",
        "",
        "## Complete-Pass Checklist",
        _checklist_row("Timestamp/price repair candidates generated", not repair.empty, f"rows={len(repair)}"),
        _checklist_row("Namespace repair ready layer generated", ready is not None, f"rows={len(ready)}"),
        _checklist_row("Manual namespace review queue generated", manual is not None, f"rows={len(manual)}"),
        _checklist_row("Namespace repair rejected queue generated", rejected is not None, f"rows={len(rejected)}"),
        _checklist_row("Timestamp repair audit generated", not ts_audit.empty, f"rows={len(ts_audit)}"),
        _checklist_row("Price anchor repair audit generated", not price_audit.empty, f"rows={len(price_audit)}"),
        f"- Final Task 381 verdict: `{verdict}`",
        "",
        "## Namespace Repair Decision",
        *(_markdown_table(decision)),
        "",
        "## Timestamp Repair Audit",
        *(_markdown_table(ts_audit)),
        "",
        "## Price Anchor Repair Audit",
        *(_markdown_table(price_audit)),
        "",
        "## Namespace Repair Ready Layer",
        *(_markdown_table(ready.head(50))),
        "",
        "## Manual Namespace Review Queue",
        *(_markdown_table(manual.head(50))),
        "",
        "## Namespace Repair Rejected",
        *(_markdown_table(rejected.head(50))),
    ]
    (out_dir / "task_381_timestamp_price_namespace_repair.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 381 timestamp and price anchor namespace repair")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    artifacts = build_timestamp_price_namespace_repair_381()
    write_timestamp_price_namespace_repair_381(artifacts, args.out_dir)
    _write_report(args.out_dir, artifacts)


if __name__ == "__main__":
    main()
