from __future__ import annotations

import json
import sys
from pathlib import Path

TASK_ID = "TASK-4151"
REPORT_DIR = Path("docs/reports/task_4151_l3_relation_graph_goal_expansion_gpt_review")

REQUIRED_FILES = (
    "l3_relation_graph_gpt_context_packet.md",
    "gpt_prompt.md",
    "gpt_response.md",
    "gpt_capture_meta.json",
    "gpt_review_digest_ko.md",
    "report.md",
    "artifact_manifest.csv",
)

RESPONSE_REQUIRED_TERMS = (
    "ENTITY_EVENT",
    "MACRO_FACTOR",
    "EVENT_CLUSTER",
    "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE",
    "l3_relation_edges.csv",
    "l3_event_clusters.csv",
    "raw_l0_read",
    "validator",
)

PROMPT_REQUIRED_TERMS = (
    "Do not rely on GitHub",
    "professional backend engineer",
    "professional trader",
    "relation graph",
    "27",
)

REPORT_REQUIRED_TERMS = (
    "SOURCE_FAMILY/UNKNOWN",
    "ENTITY_EVENT",
    "MACRO_FACTOR",
    "no broker mutation",
    "no order intent",
    "no strategy acceptance",
)


def main() -> int:
    passes: list[str] = []
    failures: list[str] = []

    for name in REQUIRED_FILES:
        path = REPORT_DIR / name
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing: {path}")

    if not failures:
        meta = json.loads((REPORT_DIR / "gpt_capture_meta.json").read_text(encoding="utf-8"))
        if meta.get("capture_status") == "CAPTURED":
            passes.append("GPT response capture status is CAPTURED")
        else:
            failures.append(f"GPT capture status is not CAPTURED: {meta.get('capture_status')}")
        if int(meta.get("response_chars", 0)) >= 1000:
            passes.append(f"GPT response size is sufficient: {meta.get('response_chars')}")
        else:
            failures.append(f"GPT response too small: {meta.get('response_chars')}")

        response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
        prompt = (REPORT_DIR / "gpt_prompt.md").read_text(encoding="utf-8")
        report = (REPORT_DIR / "report.md").read_text(encoding="utf-8")
        digest = (REPORT_DIR / "gpt_review_digest_ko.md").read_text(encoding="utf-8")

        require_terms(response, RESPONSE_REQUIRED_TERMS, "gpt_response.md", passes, failures)
        require_terms(prompt, PROMPT_REQUIRED_TERMS, "gpt_prompt.md", passes, failures)
        require_terms(report, REPORT_REQUIRED_TERMS, "report.md", passes, failures)

        if "27개" in digest and "초기 단계" in digest:
            passes.append("Korean digest explains the 27 graph concern")
        else:
            failures.append("Korean digest does not explain the 27 graph concern")

        if "raw L0" in report and "직접 읽지" in report:
            passes.append("report records no direct raw L0 bypass boundary")
        else:
            failures.append("report does not record no direct raw L0 bypass boundary")

    status = "PASS" if not failures else "FAIL"
    write_results(status, passes, failures)
    print(f"[{TASK_ID}] {status} passes={len(passes)} failures={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 0 if status == "PASS" else 1


def require_terms(
    text: str,
    terms: tuple[str, ...],
    label: str,
    passes: list[str],
    failures: list[str],
) -> None:
    lower_text = text.lower()
    missing = [term for term in terms if term.lower() not in lower_text]
    if missing:
        failures.append(f"{label} missing terms: {missing}")
    else:
        passes.append(f"{label} contains required review terms")


def write_results(status: str, passes: list[str], failures: list[str]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"# {TASK_ID} Validation Results", "", f"status: {status}", "", "## Passes"]
    lines.extend(f"- {item}" for item in passes)
    lines.extend(["", "## Failures"])
    if failures:
        lines.extend(f"- {item}" for item in failures)
    else:
        lines.append("- none")
    (REPORT_DIR / "validation_results.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    raise SystemExit(main())
