from __future__ import annotations

import json
import sys
from pathlib import Path


TASK_ID = "TASK-4153"
REPORT_DIR = Path("docs/reports/task_4153_l3_relation_graph_v2_gpt_review")

REQUIRED_FILES = (
    "context_packet.md",
    "gpt_prompt.md",
    "gpt_response.md",
    "gpt_capture_meta.json",
    "gpt_review_digest_ko.md",
    "report.md",
    "artifact_manifest.csv",
)

RESPONSE_TERMS = (
    "CONDITIONAL PASS",
    "Graph expansion quality metrics",
    "same_event_assertion",
    "unsupported_relation_families",
    "l3_l4_diagnostic_handoff_manifest.json",
    "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE",
    "SOURCE_EVENT_CLUSTER",
    "CONTRADICTION",
)

REPORT_TERMS = (
    "CONDITIONAL PASS",
    "5,398",
    "graph quality",
    "same_event_assertion=false",
    "diagnostic input only",
    "No broker mutation",
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
            passes.append("GPT capture status is CAPTURED")
        else:
            failures.append(f"GPT capture status is not CAPTURED: {meta.get('capture_status')}")
        if int(meta.get("response_chars", 0)) > 5000:
            passes.append(f"GPT response size is sufficient: {meta.get('response_chars')}")
        else:
            failures.append(f"GPT response too small: {meta.get('response_chars')}")

        response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")
        report = (REPORT_DIR / "report.md").read_text(encoding="utf-8")
        digest = (REPORT_DIR / "gpt_review_digest_ko.md").read_text(encoding="utf-8")
        context = (REPORT_DIR / "context_packet.md").read_text(encoding="utf-8")
        prompt = (REPORT_DIR / "gpt_prompt.md").read_text(encoding="utf-8")

        require_terms(response, RESPONSE_TERMS, "gpt_response.md", passes, failures)
        require_terms(report, REPORT_TERMS, "report.md", passes, failures)

        if "27" in context and "5,398" in context and "7,150" in context:
            passes.append("context packet includes baseline and v2 counts")
        else:
            failures.append("context packet missing baseline or v2 counts")

        if "Professional Backend Engineer" in prompt and "Professional Trader" in prompt:
            passes.append("prompt includes requested expert roles")
        else:
            failures.append("prompt missing requested expert roles")

        if "P0" in digest and "L4" in digest and "CONDITIONAL PASS" in digest:
            passes.append("Korean digest records verdict, P0 work, and L4 implications")
        else:
            failures.append("Korean digest missing verdict, P0 work, or L4 implications")

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
    lower = text.lower()
    missing = [term for term in terms if term.lower() not in lower]
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
    (REPORT_DIR / "validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
