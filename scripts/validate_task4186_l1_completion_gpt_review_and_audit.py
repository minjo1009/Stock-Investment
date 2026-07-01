from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4186"
SLUG = "task_4186_l1_completion_gpt_review_and_audit"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    lines = ["TASK-4186 L1 COMPLETION GPT REVIEW AND AUDIT VALIDATION"]
    lines.extend(f"PASS {item}" for item in passes)
    lines.extend(f"WARN {item}" for item in warnings)
    lines.extend(f"FAIL {item}" for item in failures)
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4186 Validation Results\n\n"
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
    from scripts.run_task4186_l1_completion_gpt_review_and_audit import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "task_4186_l1_completion_audit_summary.json",
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

    gpt = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
    if "Verdict: PASS" not in gpt:
        failures.append("GPT Pro PASS verdict not captured")
    else:
        passes.append("GPT Pro verdict captured: PASS")
    if "P0: 없음" not in gpt:
        failures.append("GPT Pro P0-none statement not captured")
    else:
        passes.append("GPT Pro P0 issues: none")

    summary_disk = read_json(ARTIFACT_DIR / "task_4186_l1_completion_audit_summary.json")
    if summary_disk.get("task_id") != TASK_ID:
        failures.append("summary task_id mismatch")
    if summary.get("feature_materialization_gap_unresolved") != 0:
        failures.append("feature materialization gap unresolved is nonzero")
    else:
        passes.append("feature materialization unresolved: 0")
    if summary.get("source_recall_unresolved_after") != 0:
        failures.append("source recall unresolved is nonzero")
    else:
        passes.append("source recall unresolved: 0")
    if summary.get("insufficient_context_non_terminal_after") != 0:
        failures.append("insufficient-context non-terminal is nonzero")
    else:
        passes.append("insufficient-context non-terminal: 0")
    for key in [
        "forced_ticker_mapping_count",
        "llm_entity_inference_count",
        "negative_evidence_allowed_count",
        "unsafe_authority_row_count",
    ]:
        if summary.get(key) != 0:
            failures.append(f"{key} is nonzero")
        else:
            passes.append(f"{key}: 0")
    blockers = summary.get("upstream_l0_worker_blockers") or []
    if blockers:
        warnings.append(f"upstream L0 warning remains explicit: {blockers}")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
