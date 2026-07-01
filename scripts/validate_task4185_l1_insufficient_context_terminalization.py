from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4185"
SLUG = "task_4185_l1_insufficient_context_terminalization"
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
    lines = ["TASK-4185 L1 INSUFFICIENT CONTEXT TERMINALIZATION VALIDATION"]
    lines.extend(f"PASS {item}" for item in passes)
    lines.extend(f"WARN {item}" for item in warnings)
    lines.extend(f"FAIL {item}" for item in failures)
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4185 Validation Results\n\n"
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
    from scripts.run_task4185_l1_insufficient_context_terminalization import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "task_4185_l1_insufficient_context_summary.json",
        ARTIFACT_DIR / "task_4185_l1_insufficient_context_terminal_ledger.csv",
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

    ledger = read_csv(ARTIFACT_DIR / "task_4185_l1_insufficient_context_terminal_ledger.csv")
    summary_disk = read_json(ARTIFACT_DIR / "task_4185_l1_insufficient_context_summary.json")
    if summary_disk.get("task_id") != TASK_ID:
        failures.append("summary task_id mismatch")

    before = as_int(summary.get("insufficient_context_before"))
    after = as_int(summary.get("insufficient_context_after"))
    terminalized = as_int(summary.get("terminalized_count"))
    if before != 5:
        failures.append(f"unexpected insufficient context baseline: {before}")
    else:
        passes.append("insufficient-context baseline rows: 5")
    if len(ledger) != before:
        failures.append(f"ledger row count mismatch: {len(ledger)} != {before}")
    else:
        passes.append(f"ledger row count: {len(ledger)}")
    if after != 0:
        failures.append(f"non-terminal insufficient-context rows remain: {after}")
    else:
        passes.append("non-terminal insufficient-context after: 0")
    if terminalized != 5:
        failures.append(f"terminalized count mismatch: {terminalized}")
    else:
        passes.append("terminalized rows: 5")

    defects = [
        row for row in ledger
        if row.get("wide_reference_found") != "1"
        or row.get("raw_path_exists") != "1"
        or row.get("raw_sha256_match") != "1"
        or row.get("raw_parse_error")
        or as_int(row.get("article_count")) <= 0
        or as_int(row.get("source_time_ready_count")) <= 0
        or as_int(row.get("locator_ready_count")) <= 0
        or as_int(row.get("mapped_article_count")) != 0
        or row.get("terminal_status") != "TERMINAL_CONTEXT_OR_NON_CURRENT_UNIVERSE_ENTITY_BLOCKER"
    ]
    if defects:
        failures.append(f"terminalization evidence defects: {len(defects)}")
    else:
        passes.append("all five rows have terminal blocker evidence and zero mapped articles")

    for key in ["forced_ticker_mapping_count", "llm_entity_inference_count", "negative_evidence_allowed_count"]:
        if summary.get(key) != 0:
            failures.append(f"{key} is nonzero")
        else:
            passes.append(f"{key}: 0")
    if summary.get("diagnostic_only") != 1:
        failures.append("summary is not diagnostic-only")
    else:
        passes.append("diagnostic-only summary")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
