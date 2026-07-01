from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4137"
REPORT_DIR = ROOT / "docs" / "reports" / "task_4137_l1_1to6_gpt_pro_review"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4137 L1 1-6 GPT REVIEW VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    markdown = f"# TASK-4137 Validation Results\n\nResult: `{result}`\n\n"
    for label, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        markdown += f"## {label}\n\n"
        markdown += "\n".join(f"- {item}" for item in items) if items else "- none"
        markdown += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(markdown, encoding="utf-8", newline="\n")
    (REPORT_DIR / "validator_report.json").write_text(
        json.dumps({"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return 1 if failures else 0


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "gpt_consult_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    if failures:
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    prompt = (REPORT_DIR / "gpt_prompt.md").read_text(encoding="utf-8")
    response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
    ledger = read_csv(REPORT_DIR / "gpt_consult_ledger.csv")

    required_prompt_terms = ["Wikimedia", "매매판단용", "스케줄러", "Validator", "크롬", "티커/뉴스", "과도한 코드를 위한 코드는 지양"]
    missing_terms = [term for term in required_prompt_terms if term not in prompt]
    if missing_terms:
        failures.append(f"prompt missing required terms: {missing_terms}")
    else:
        passes.append("prompt_covers_1_to_6_and_overengineering_guard")
    if "GitHub를 보지 마세요" not in prompt:
        failures.append("prompt must forbid GitHub because local state is newer")
    else:
        passes.append("prompt_forbids_github")
    if not ledger or ledger[0].get("capture_status") != "CAPTURED":
        failures.append("GPT response has not been captured")
    else:
        passes.append("gpt_response_captured")
    if "TASK-4138" not in response:
        warnings.append("GPT response does not mention TASK-4138 explicitly")
    else:
        passes.append("gpt_response_mentions_task_4138")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())

