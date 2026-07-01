from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4141"
REPORT_DIR = ROOT / "docs" / "reports" / "task_4141_l2_gpt_pro_design_review"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4141_l2_gpt_pro_design_review"


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4141 L2 GPT DESIGN REVIEW VALIDATION")
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
    md = "# TASK-4141 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l2_gpt_design_review_summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
    required_terms = [
        "L2 Swing Primitive Admission View",
        "TASK-4142",
        "mapping",
        "dedup",
        "stale",
        "effect window",
        "feature materialization",
        "No broker mutation",
    ]
    for term in required_terms:
        if term not in response:
            failures.append(f"GPT response missing required term: {term}")
    if not failures:
        passes.append("gpt_response_contains_core_recommendations")

    summary = json.loads((REPORT_DIR / "l2_gpt_design_review_summary.json").read_text(encoding="utf-8"))
    if summary.get("gpt_capture_status") != "CAPTURED":
        failures.append("GPT response was not captured")
    else:
        passes.append("gpt_capture_status_captured")
    if summary.get("feature_materialization_allowed_now") is not False:
        failures.append("summary must keep feature materialization closed")
    if summary.get("trading_authority_opened") or summary.get("paper_live_broker_order_opened"):
        failures.append("summary unexpectedly opens trading/paper/live/broker/order")
    if not any("trading" in failure or "feature materialization" in failure for failure in failures):
        passes.append("safety_boundaries_closed")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
