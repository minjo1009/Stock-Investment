from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_4155_l4_goal_definition_gpt_review"

REQUIRED_FILES = [
    "context_packet.md",
    "gpt_prompt.md",
    "gpt_response.md",
    "gpt_capture_meta.json",
    "gpt_review_digest_ko.md",
    "report.md",
    "artifact_manifest.csv",
    "validation_results.md",
]

REQUIRED_RESPONSE_TERMS = [
    "CONDITIONAL PASS",
    "diagnostic thesis bundle",
    "NOT_ACCEPTED",
    "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "FORBIDDEN",
    "UNKNOWN/BLOCKER",
    "NO_CONTRADICTION",
    "SOURCE_EVENT_CLUSTER",
    "same_event_assertion",
    "l4_thesis_bundles.jsonl",
    "l4_thesis_evidence_links.csv",
    "l4_thesis_blockers.csv",
    "l4_run_manifest.json",
]

REQUIRED_PROMPT_TERMS = [
    "Professional Backend Engineer",
    "Quant Data Infrastructure Reviewer",
    "Institutional Equity Research PM",
    "Systematic PM / Trading Research Reviewer",
    "Risk and Trading Controls Reviewer",
    "public_newswire_backfill",
    "public_market_macro_news_backfill",
    "public_context_news_backfill",
    "five_min_bars",
    "TASK-4154",
]

REQUIRED_DIGEST_TERMS = [
    "CONDITIONAL PASS",
    "L4의 목표",
    "L4가 해야 하는 일",
    "L4가 하면 안 되는 일",
    "구현 우선순위",
]


def _read_text(name: str) -> str:
    return (REPORT_DIR / name).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    for name in REQUIRED_FILES:
        path = REPORT_DIR / name
        if not path.exists():
            errors.append(f"missing required file: {path}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required file: {path}")

    if errors:
        return _finish(errors)

    prompt = _read_text("gpt_prompt.md")
    response = _read_text("gpt_response.md")
    digest = _read_text("gpt_review_digest_ko.md")
    report = _read_text("report.md")

    for term in REQUIRED_PROMPT_TERMS:
        if term not in prompt:
            errors.append(f"prompt missing term: {term}")

    for term in REQUIRED_RESPONSE_TERMS:
        if term not in response:
            errors.append(f"response missing term: {term}")

    for term in REQUIRED_DIGEST_TERMS:
        if term not in digest:
            errors.append(f"digest missing term: {term}")

    for term in [
        "Strategy remains `NOT_ACCEPTED`",
        "Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "Real Capital remains `FORBIDDEN`",
        "No broker mutation was added",
        "No live order path was added",
        "No paper promotion was added",
    ]:
        if term not in report:
            errors.append(f"report missing safety term: {term}")

    meta = json.loads((REPORT_DIR / "gpt_capture_meta.json").read_text(encoding="utf-8"))
    if meta.get("task_id") != "TASK-4155":
        errors.append("capture meta task_id is not TASK-4155")
    if meta.get("capture_status") != "CAPTURED":
        errors.append("capture status is not CAPTURED")
    if int(meta.get("response_chars", 0)) < 2000:
        errors.append("captured response is too short")
    if meta.get("verdict_detected") != "CONDITIONAL PASS":
        errors.append("verdict_detected is not CONDITIONAL PASS")

    manifest_path = REPORT_DIR / "artifact_manifest.csv"
    rows = list(csv.DictReader(manifest_path.open(encoding="utf-8", newline="")))
    manifest_paths = {row.get("path") or row.get("artifact_path") for row in rows}
    for name in REQUIRED_FILES:
        rel_path = f"docs/reports/task_4155_l4_goal_definition_gpt_review/{name}"
        if rel_path not in manifest_paths:
            errors.append(f"manifest missing artifact row: {rel_path}")

    return _finish(errors)


def _finish(errors: list[str]) -> int:
    if errors:
        print("TASK-4155 validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK-4155 validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
