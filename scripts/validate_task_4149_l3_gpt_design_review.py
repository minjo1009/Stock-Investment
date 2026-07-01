from __future__ import annotations

import json
from pathlib import Path


TASK_ID = "TASK-4149"
REPORT_DIR = Path("docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap")
REQUIRED_FILES = [
    REPORT_DIR / "report.md",
    REPORT_DIR / "artifact_manifest.csv",
    REPORT_DIR / "gpt_prompt.md",
    REPORT_DIR / "l3_gpt_local_context_packet.md",
    REPORT_DIR / "gpt_response.md",
    REPORT_DIR / "gpt_review_digest_ko.md",
    REPORT_DIR / "gpt_capture_meta.json",
]


def main() -> int:
    failures: list[str] = []
    passes: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing required file: {path}")
        else:
            passes.append(f"exists: {path}")

    response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8") if (REPORT_DIR / "gpt_response.md").exists() else ""
    report = (REPORT_DIR / "report.md").read_text(encoding="utf-8") if (REPORT_DIR / "report.md").exists() else ""
    prompt = (REPORT_DIR / "gpt_prompt.md").read_text(encoding="utf-8") if (REPORT_DIR / "gpt_prompt.md").exists() else ""
    meta_path = REPORT_DIR / "gpt_capture_meta.json"

    required_response_terms = [
        "핵심 3줄 요약",
        "task-scoped",
        "L3 Diagnostic Strategy View Bootstrap",
        "UNKNOWN mapping",
        "coverage gap",
        "No broker mutation",
    ]
    for term in required_response_terms:
        if term not in response:
            failures.append(f"gpt response missing term: {term}")
        else:
            passes.append(f"gpt response contains: {term}")

    required_report_terms = [
        "Strategy: `NOT_ACCEPTED`",
        "Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital: `FORBIDDEN`",
        "No broker mutation",
        "No live order",
        "No paper promotion",
        "L0 raw 직접",
    ]
    for term in required_report_terms:
        if term not in report:
            failures.append(f"report missing safety/scope term: {term}")
        else:
            passes.append(f"report contains: {term}")

    if "Do not rely on GitHub as current state" not in prompt:
        failures.append("prompt did not forbid relying on GitHub current state")
    else:
        passes.append("prompt forbids relying on GitHub current state")

    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("capture_status") != "CAPTURED":
            failures.append("GPT capture status is not CAPTURED")
        else:
            passes.append("GPT capture status CAPTURED")
        if int(meta.get("response_chars") or 0) < 1000:
            failures.append("GPT response appears too short")
        else:
            passes.append(f"GPT response chars: {meta.get('response_chars')}")

    status = "PASS" if not failures else "FAIL"
    lines = [f"# {TASK_ID} Validation Results", "", f"status: {status}", "", "## Passes"]
    lines.extend(f"- {item}" for item in passes)
    lines.extend(["", "## Failures"])
    lines.extend(f"- {item}" for item in failures)
    if not failures:
        lines.append("- none")
    (REPORT_DIR / "validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"[{TASK_ID}] {status} passes={len(passes)} failures={len(failures)}")
    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
