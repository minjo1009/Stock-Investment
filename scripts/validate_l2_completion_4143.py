from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4143"
SLUG = "task_4143_l2_completion_gpt_review_and_read_contract"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
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
    print("TASK-4143 L2 COMPLETION VALIDATION")
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
    (ARTIFACT_DIR / "l2_completion_validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    md = "# TASK-4143 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l2_completion_validation_report.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l2_completion_4143 import L3_READ_COLUMNS, build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l2_completion_summary.json",
        ARTIFACT_DIR / "l2_to_l3_swing_event_read_contract.yaml",
        ARTIFACT_DIR / "l2_to_l3_swing_event_read_view.csv",
        ARTIFACT_DIR / "l2_to_l3_swing_event_read_view.jsonl",
        ARTIFACT_DIR / "l2_mapping_review_queue.csv",
        ARTIFACT_DIR / "l2_input_scope_audit.csv",
        ARTIFACT_DIR / "l2_mapping_scope_summary.csv",
        ARTIFACT_DIR / "l2_dedup_summary.csv",
        ARTIFACT_DIR / "l2_stale_status_summary.csv",
        ARTIFACT_DIR / "l2_completion_cut_list.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    gpt_response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
    if len(gpt_response) < 1000:
        failures.append("GPT response capture is too short")
    elif "입력 범위 확장" in gpt_response and "L3 read" in gpt_response:
        passes.append("gpt_pro_response_captured")
    else:
        warnings.append("GPT response captured but expected section markers were not found")

    read_rows = read_csv(ARTIFACT_DIR / "l2_to_l3_swing_event_read_view.csv")
    queue_rows = read_csv(ARTIFACT_DIR / "l2_mapping_review_queue.csv")
    scope_rows = read_csv(ARTIFACT_DIR / "l2_input_scope_audit.csv")
    if not read_rows:
        failures.append("L3 read view has no rows")
    else:
        passes.append(f"l3_read_rows: {len(read_rows)}")
    read_columns = set(read_rows[0].keys()) if read_rows else set(L3_READ_COLUMNS)
    missing_columns = set(L3_READ_COLUMNS) - read_columns
    if missing_columns:
        failures.append(f"L3 read view missing columns: {sorted(missing_columns)}")
    else:
        passes.append("l3_read_contract_columns_present")
    forbidden = read_columns & FORBIDDEN_COLUMNS
    if forbidden:
        failures.append(f"L3 read view exposes forbidden columns: {sorted(forbidden)}")
    else:
        passes.append("l3_read_view_has_no_forbidden_columns")

    for row in read_rows:
        row_id = row.get("l2_event_mapping_id", "")
        if row.get("mapping_scope") == "UNKNOWN":
            failures.append(f"UNKNOWN mapping exposed to L3 read view: {row_id}")
        if row.get("is_canonical_event") != "1":
            failures.append(f"non-canonical event exposed to L3 read view: {row_id}")
        if not row.get("source_packet_id") or not row.get("raw_path") or not row.get("raw_sha256"):
            failures.append(f"L3 read row missing lineage/raw evidence: {row_id}")
    if not any("UNKNOWN mapping exposed" in failure for failure in failures):
        passes.append("unknown_mapping_not_exposed_to_l3_read")
    if not any("non-canonical" in failure for failure in failures):
        passes.append("l3_read_rows_are_canonical")
    if not any("lineage" in failure for failure in failures):
        passes.append("l3_read_rows_keep_lineage")

    if not queue_rows:
        failures.append("mapping review queue has no rows")
    elif any(row.get("mapping_scope") == "UNKNOWN" for row in queue_rows):
        passes.append(f"mapping_review_queue_rows: {len(queue_rows)}")
    else:
        failures.append("mapping review queue does not include UNKNOWN mapping row")

    if not any(row.get("scope_status") == "BLOCKED_L1_PACKET_SCOPE_TOO_NARROW" for row in scope_rows):
        warnings.append("input scope audit does not flag narrow L1 packet scope")
    else:
        passes.append("narrow_l1_scope_explicitly_reported")

    if summary.get("feature_materialization_allowed_rows") != 0:
        failures.append("feature materialization opened")
    if summary.get("trading_authority_opened_rows") != 0:
        failures.append("trading authority opened")
    if summary.get("paper_live_broker_order_opened_rows") != 0:
        failures.append("paper/live/broker/order opened")
    if not any("opened" in failure for failure in failures):
        passes.append("feature_trading_paper_live_broker_order_gates_closed")

    script_text = (ROOT / "scripts" / "run_l2_completion_4143.py").read_text(encoding="utf-8")
    if "ingest_l0_news_to_l2" in script_text or "news_event_primitives" in script_text:
        failures.append("script references legacy L2 news builder or direct L0-to-L2 ingest")
    else:
        passes.append("legacy_l2_news_paths_not_referenced")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
