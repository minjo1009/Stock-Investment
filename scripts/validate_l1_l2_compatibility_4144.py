from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4144"
SLUG = "task_4144_l1_l2_compatibility_bridge"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG

ALLOWED_STATUSES = {
    "L2_CONTEXT_ACTIVE_READY",
    "L2_CONTEXT_ARCHIVE_READY",
    "L2_DISCOVERY_REVIEW_READY",
    "L2_MAPPING_REVIEW_READY",
    "BLOCKED_SOURCE_TIME_FOR_L2",
    "BLOCKED_RAW_INTEGRITY_FOR_L2",
    "BLOCKED_L1_SCOPE_NOT_MATERIALIZED",
    "BLOCKED_POLICY_FOR_L2",
}
FORBIDDEN_COLUMNS = {
    "sentiment_score",
    "bullish",
    "bearish",
    "alpha_score",
    "rank",
    "ranking",
    "realized_return",
    "forward_return",
    "hit_rate",
    "sizing",
    "order_intent",
    "signal",
    "target",
    "score",
    "feature_materialization_allowed",
    "trading_authority_opened",
    "paper_live_broker_order_opened",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4144 L1/L2 COMPATIBILITY VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    (ARTIFACT_DIR / "validator_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l1_l2_compatibility_validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    md = "# TASK-4144 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l1_l2_compatibility_validation_report.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l1_l2_compatibility_4144 import HANDOFF_COLUMNS, build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l1_l2_compatibility_summary.json",
        ARTIFACT_DIR / "l1_l2_compatibility_handoff.csv",
        ARTIFACT_DIR / "l1_l2_compatibility_matrix.csv",
        ARTIFACT_DIR / "l1_l2_scope_gap_report.csv",
        ARTIFACT_DIR / "l1_l2_timestamp_basis_audit.csv",
        ARTIFACT_DIR / "l2_from_compatibility_handoff.csv",
        ARTIFACT_DIR / "l1_l2_block_reason_summary.csv",
        ARTIFACT_DIR / "l1_l2_review_reason_summary.csv",
        ARTIFACT_DIR / "l1_l2_mapping_status_summary.csv",
        ARTIFACT_DIR / "l1_l2_timestamp_basis_summary.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    gpt_response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
    if "L1/L2 Compatibility Bridge" in gpt_response or "Compatibility Bridge" in gpt_response:
        passes.append("gpt_pro_compatibility_review_captured")
    else:
        warnings.append("GPT response exists, but compatibility bridge marker was not found")
    if "capture time" in gpt_response and "HARD CUT" in gpt_response:
        passes.append("gpt_pro_cut_lines_and_capture_time_guidance_captured")
    else:
        warnings.append("GPT response exists, but expected cut-line markers were not found")

    handoff_rows = read_csv(ARTIFACT_DIR / "l1_l2_compatibility_handoff.csv")
    matrix_rows = read_csv(ARTIFACT_DIR / "l1_l2_compatibility_matrix.csv")
    l2_rows = read_csv(ARTIFACT_DIR / "l2_from_compatibility_handoff.csv")
    scope_rows = read_csv(ARTIFACT_DIR / "l1_l2_scope_gap_report.csv")
    timestamp_rows = read_csv(ARTIFACT_DIR / "l1_l2_timestamp_basis_audit.csv")

    if not handoff_rows:
        failures.append("L1 handoff rows are empty")
    else:
        passes.append(f"l1_handoff_rows: {len(handoff_rows)}")
    if len(matrix_rows) <= len(handoff_rows):
        failures.append("compatibility matrix does not include L0 audit gap candidates")
    else:
        passes.append(f"compatibility_matrix_rows: {len(matrix_rows)}")
    if len(scope_rows) != 3:
        failures.append(f"scope gap report should cover 3 target families, got {len(scope_rows)}")
    else:
        passes.append("scope_gap_report_covers_target_families")
    if len(timestamp_rows) != len(matrix_rows):
        failures.append("timestamp basis audit row count does not match compatibility matrix")
    else:
        passes.append("timestamp_basis_audit_matches_matrix")

    handoff_columns = set(handoff_rows[0].keys()) if handoff_rows else set(HANDOFF_COLUMNS)
    missing_columns = set(HANDOFF_COLUMNS) - handoff_columns
    if missing_columns:
        failures.append(f"handoff missing columns: {sorted(missing_columns)}")
    else:
        passes.append("handoff_contract_columns_present")
    forbidden = handoff_columns & FORBIDDEN_COLUMNS
    if forbidden:
        failures.append(f"handoff exposes forbidden trading/scoring columns: {sorted(forbidden)}")
    else:
        passes.append("handoff_has_no_trading_or_scoring_columns")

    bad_statuses = sorted({row.get("compatibility_status", "") for row in matrix_rows} - ALLOWED_STATUSES)
    if bad_statuses:
        failures.append(f"unknown compatibility statuses: {bad_statuses}")
    else:
        passes.append("compatibility_status_values_allowed")

    for row in matrix_rows:
        row_id = row.get("compatibility_row_id", "")
        if row.get("capture_time_used_as") == "publication_time":
            failures.append(f"capture time promoted to publication time: {row_id}")
        if row.get("timestamp_basis_for_l2") == "capture_only_not_publication_time":
            if row.get("source_time_certified") != "0":
                failures.append(f"capture-only row marked source-time certified: {row_id}")
            if row.get("l2_handoff_allowed") == "1" or row.get("l2_review_allowed") == "1":
                failures.append(f"capture-only row allowed to L2 handoff/review: {row_id}")
    if not any("capture" in failure for failure in failures):
        passes.append("capture_time_not_promoted_to_publication_or_l2_ready")

    l0_gap_rows = [row for row in matrix_rows if not row.get("source_packet_id")]
    if not l0_gap_rows:
        failures.append("L0 audit gap rows are missing from compatibility matrix")
    elif any(row.get("l2_handoff_allowed") == "1" or row.get("l2_review_allowed") == "1" for row in l0_gap_rows):
        failures.append("L0 audit gap row was allowed directly into L2")
    else:
        passes.append(f"l0_audit_gap_rows_blocked_from_direct_l2: {len(l0_gap_rows)}")

    for row in l2_rows:
        row_id = row.get("compatibility_row_id", "")
        if not row.get("source_packet_id"):
            failures.append(f"L2 handoff/review row has no L1 source packet id: {row_id}")
        if not row.get("raw_path") or not row.get("raw_sha256"):
            failures.append(f"L2 handoff/review row missing raw lineage: {row_id}")
        if row.get("l2_handoff_allowed") != "1" and row.get("l2_review_allowed") != "1":
            failures.append(f"L2 output row is not allowed as handoff or review: {row_id}")
    if l2_rows and not any("L2 handoff/review" in failure or "L2 output" in failure for failure in failures):
        passes.append(f"l2_output_rows_keep_l1_lineage: {len(l2_rows)}")

    if summary.get("l2_handoff_allowed_rows", 0) == 0 and summary.get("l2_review_allowed_rows", 0) == 0:
        failures.append("bridge is over-blocking: no L2 handoff or review rows survived")
    else:
        passes.append("bridge_is_not_over_blocking_all_rows")
    if summary.get("capture_only_publication_promotions") != 0:
        failures.append("summary reports capture-only publication promotions")
    if summary.get("feature_materialization_allowed_rows") != 0:
        failures.append("feature materialization opened")
    if summary.get("trading_authority_opened_rows") != 0:
        failures.append("trading authority opened")
    if summary.get("paper_live_broker_order_opened_rows") != 0:
        failures.append("paper/live/broker/order opened")
    if not any("opened" in failure or "publication promotions" in failure for failure in failures):
        passes.append("feature_trading_paper_live_broker_order_gates_closed")

    script_text = (ROOT / "scripts" / "run_l1_l2_compatibility_4144.py").read_text(encoding="utf-8")
    if "ingest_l0_news_to_l2" in script_text or "news_event_primitives" in script_text:
        failures.append("script references legacy direct L0-to-L2 news path")
    else:
        passes.append("legacy_direct_l0_to_l2_paths_not_referenced")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
