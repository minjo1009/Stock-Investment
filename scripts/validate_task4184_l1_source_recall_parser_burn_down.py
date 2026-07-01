from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4184"
SLUG = "task_4184_l1_source_recall_parser_burn_down"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    lines = ["TASK-4184 L1 SOURCE RECALL PARSER BURN-DOWN VALIDATION"]
    lines.extend(f"PASS {item}" for item in passes)
    lines.extend(f"WARN {item}" for item in warnings)
    lines.extend(f"FAIL {item}" for item in failures)
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)

    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4184 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_task4184_l1_source_recall_parser_burn_down import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "task_4184_l1_source_recall_summary.json",
        ARTIFACT_DIR / "task_4184_l1_source_recall_decision_ledger.csv",
        ARTIFACT_DIR / "task_4184_l1_source_recall_entity_rollup.csv",
        REPORT_DIR / "task_result_contract.yaml",
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    ledger = read_csv(ARTIFACT_DIR / "task_4184_l1_source_recall_decision_ledger.csv")
    rollup = read_csv(ARTIFACT_DIR / "task_4184_l1_source_recall_entity_rollup.csv")
    summary_disk = read_json(ARTIFACT_DIR / "task_4184_l1_source_recall_summary.json")
    if summary_disk.get("task_id") != TASK_ID:
        failures.append("summary task_id mismatch")

    before = as_int(summary.get("source_recall_review_before"))
    unresolved = as_int(summary.get("source_recall_review_unresolved_after"))
    if before != 447:
        failures.append(f"unexpected source recall baseline: {before}")
    else:
        passes.append("source recall baseline rows: 447")
    if len(ledger) != before:
        failures.append(f"ledger row count mismatch: {len(ledger)} != {before}")
    else:
        passes.append(f"ledger row count: {len(ledger)}")
    if unresolved != 0:
        failures.append(f"source recall rows remain unresolved: {unresolved}")
    else:
        passes.append("source recall unresolved after: 0")

    bad_raw = [
        row for row in ledger
        if row.get("wide_reference_found") != "1"
        or row.get("raw_path_exists") != "1"
        or row.get("raw_sha256_match") != "1"
        or row.get("raw_parse_error")
    ]
    if bad_raw:
        failures.append(f"raw/wide/hash/parser blockers remain: {len(bad_raw)}")
    else:
        passes.append("wide references, raw paths, sha256, and JSON parsing all pass")

    bad_article = [
        row for row in ledger
        if as_int(row.get("article_count")) <= 0
        or as_int(row.get("source_time_ready_count")) <= 0
        or as_int(row.get("locator_ready_count")) <= 0
        or as_int(row.get("mapped_article_count")) <= 0
    ]
    if bad_article:
        failures.append(f"article/time/locator/mapping blockers remain: {len(bad_article)}")
    else:
        passes.append("all recall rows have article, source-time, locator, and mapped-article evidence")

    statuses = {row.get("decision_status") for row in ledger}
    if statuses != {"RECALL_RECOVERABLE_ARTICLE_READY"}:
        failures.append(f"unexpected decision statuses: {sorted(statuses)}")
    else:
        passes.append("all decisions are RECALL_RECOVERABLE_ARTICLE_READY")

    if summary.get("forced_ticker_mapping_count") != 0:
        failures.append("forced ticker mapping was used")
    else:
        passes.append("forced ticker mapping count is zero")
    if summary.get("llm_entity_inference_count") != 0:
        failures.append("LLM entity inference was used")
    else:
        passes.append("LLM entity inference count is zero")
    if summary.get("negative_evidence_allowed_count") != 0:
        failures.append("negative evidence was allowed")
    else:
        passes.append("negative evidence count is zero")
    if summary.get("diagnostic_only") != 1:
        failures.append("summary is not diagnostic-only")
    else:
        passes.append("diagnostic-only summary")

    if len(rollup) < 3:
        failures.append("entity rollup is too narrow")
    else:
        passes.append(f"entity rollup rows: {len(rollup)}")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
