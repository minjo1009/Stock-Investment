from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4142"
SLUG = "task_4142_l2_swing_event_admission"
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
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4142 L2 SWING EVENT ADMISSION VALIDATION")
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
    md = "# TASK-4142 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l2_swing_event_admission_4142 import VIEW_COLUMNS, build_and_write

    build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        ARTIFACT_DIR / "l2_swing_event_admission_view.csv",
        ARTIFACT_DIR / "l2_swing_event_admission_view.jsonl",
        ARTIFACT_DIR / "l2_swing_event_admission_validation_report.json",
        ARTIFACT_DIR / "l2_swing_event_admission_validation_report.md",
        ARTIFACT_DIR / "l2_mapping_issues.csv",
        ARTIFACT_DIR / "l2_dedup_clusters.csv",
        ARTIFACT_DIR / "l2_block_reason_summary.csv",
        ARTIFACT_DIR / "l2_family_count_summary.csv",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l2_swing_event_admission_summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    rows = read_csv(ARTIFACT_DIR / "l2_swing_event_admission_view.csv")
    if not rows:
        failures.append("admission view has no rows")
        return emit(passes, warnings, failures)
    passes.append(f"view_rows: {len(rows)}")
    columns = set(rows[0].keys())
    missing_columns = set(VIEW_COLUMNS) - columns
    if missing_columns:
        failures.append(f"view missing columns: {sorted(missing_columns)}")
    else:
        passes.append("required_view_columns_present")
    forbidden = columns & FORBIDDEN_COLUMNS
    if forbidden:
        failures.append(f"forbidden score/signal/outcome columns present: {sorted(forbidden)}")
    else:
        passes.append("no_score_signal_outcome_order_columns")

    target_families = {"public_context_news_feeds", "public_market_macro_news_feeds", "public_newswire_feeds"}
    families = {row["source_family"] for row in rows}
    if not families.issubset(target_families):
        failures.append(f"unexpected source families: {sorted(families - target_families)}")
    else:
        passes.append("only_news_macro_newswire_families")

    for row in rows:
        row_id = row["l2_event_mapping_id"]
        if not row["source_packet_id"] or not row["raw_path"] or not row["raw_sha256"]:
            failures.append(f"missing L1 lineage/raw evidence: {row_id}")
        if row["feature_materialization_allowed"] != "0":
            failures.append(f"feature materialization opened: {row_id}")
        if row["trading_authority_opened"] != "0" or row["paper_live_broker_order_opened"] != "0":
            failures.append(f"trading/paper/live/broker/order opened: {row_id}")
        if row["mapping_scope"] == "UNKNOWN" and row["admission_status"] == "ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE":
            failures.append(f"UNKNOWN mapping admitted as fully mapped row: {row_id}")
        if row["mapping_scope"] == "UNKNOWN" and row["admission_status"] != "MAPPING_REVIEW_REQUIRED_NOT_FEATURE":
            failures.append(f"UNKNOWN mapping must route to mapping review: {row_id}")
        if row["dedup_status"] == "DUPLICATE_BLOCKED" and row["l3_read_allowed"] != "0":
            failures.append(f"duplicate row allowed for L3 read: {row_id}")
        if "wikimedia_current_events" in row["raw_path"] and row["is_publication_time_imputed"] != "1":
            failures.append(f"Wikimedia row must mark imputed time: {row_id}")
        if row["stale_status"] == "ARCHIVE_CONTEXT_ONLY" and str(row["admission_status"]).startswith("BLOCKED"):
            failures.append(f"archive context row hard-blocked only for age: {row_id}")
        source_dt = parse_ts(row["source_ts"])
        available_dt = parse_ts(row["available_to_brain_ts"])
        decision_dt = parse_ts(row["decision_asof_ts"])
        if source_dt and available_dt and decision_dt and not (source_dt <= available_dt <= decision_dt):
            failures.append(f"source/asof order violation: {row_id}")
    if not any("lineage" in failure for failure in failures):
        passes.append("l1_lineage_and_raw_evidence_present")
    if not any("opened" in failure for failure in failures):
        passes.append("feature_trading_paper_live_broker_order_gates_closed")
    if not any("UNKNOWN mapping" in failure for failure in failures):
        passes.append("unknown_mapping_routes_to_review")
    if not any("Wikimedia" in failure for failure in failures):
        passes.append("wikimedia_imputed_time_marked")
    if not any("source/asof" in failure for failure in failures):
        passes.append("source_available_decision_order_valid")

    script_text = (ROOT / "scripts" / "run_l2_swing_event_admission_4142.py").read_text(encoding="utf-8")
    if "news_event_primitives" in script_text or "ingest_l0_news_to_l2" in script_text:
        failures.append("script references legacy L2 news builder or direct L0-to-L2 ingest")
    else:
        passes.append("legacy_l2_news_paths_not_referenced")

    summary = json.loads((REPORT_DIR / "l2_swing_event_admission_summary.json").read_text(encoding="utf-8"))
    if summary.get("feature_materialization_allowed_rows") != 0:
        failures.append("summary reports feature materialization rows")
    if summary.get("trading_authority_opened_rows") != 0:
        failures.append("summary reports trading authority rows")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
