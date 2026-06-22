from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_2791_2800_uiux_reference_context"
REPORT = ROOT / "docs" / "reports" / "task_2791_2800_uiux_reference_context" / "task_2791_2800_uiux_reference_context.md"
DECISION = ROOT / "docs" / "reports" / "task_2791_2800_uiux_reference_context" / "task_2800_decision.csv"
MANIFEST = ARTIFACT_DIR / "reference_source_manifest.csv"
ARTIFACT_MANIFEST = ARTIFACT_DIR / "artifact_manifest.md"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(path: Path) -> None:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")


def main() -> None:
    for path in [REPORT, DECISION, MANIFEST, ARTIFACT_MANIFEST]:
        require(path)

    toss_images = sorted((ARTIFACT_DIR / "images" / "toss_appstore").glob("*.png"))
    web_captures = sorted((ARTIFACT_DIR / "images" / "web_captures").glob("*.png"))
    raw_json = sorted((ARTIFACT_DIR / "raw").glob("*.json"))

    if len(toss_images) < 6:
        fail(f"expected at least 6 Toss screenshots, found {len(toss_images)}")
    if len(web_captures) < 4:
        fail(f"expected at least 4 web captures, found {len(web_captures)}")
    if len(raw_json) < 2:
        fail(f"expected at least 2 raw JSON files, found {len(raw_json)}")

    with MANIFEST.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 15:
        fail(f"expected at least 15 source manifest rows, found {len(rows)}")

    report_text = REPORT.read_text(encoding="utf-8")
    required_terms = [
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "보유 / 관심 / 최근 본",
        "오늘 확인할 일",
        "간단 / 상세",
        "거절 후보",
        "모의 관찰",
    ]
    for term in required_terms:
        if term not in report_text:
            fail(f"report missing required term: {term}")

    decision_text = DECISION.read_text(encoding="utf-8")
    if "uiux_reference_context_primary_pass" not in decision_text:
        fail("decision file missing primary pass decision")

    print("PASS: Task2791-2800 UIUX reference context artifacts are valid")


if __name__ == "__main__":
    main()
