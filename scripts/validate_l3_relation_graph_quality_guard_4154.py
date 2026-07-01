from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.l3_relation_graph_quality_guard_4154.validator import validate_quality_guard


TASK_ID = "TASK-4154"
REPORT_DIR = Path("docs/reports/task_4154_l3_relation_graph_v2_quality_guard")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="data/artifacts/task_4154_l3_relation_graph_v2_quality_guard")
    parser.add_argument("--source-dir", default="data/artifacts/task_4152_l3_relation_graph_v2")
    args = parser.parse_args()
    result = validate_quality_guard(output_dir=args.artifact_dir, source_dir=args.source_dir)
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "l3_quality_guard_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_validation_results(result)
    print(f"[{TASK_ID}] {result['status']} passes={len(result['passes'])} failures={len(result['failures'])}")
    for failure in result["failures"]:
        print(f"FAIL: {failure}")
    return 0 if result["status"] == "PASS" else 1


def write_validation_results(result: dict[str, object]) -> None:
    lines = [f"# {TASK_ID} Validation Results", "", f"status: {result['status']}", "", "## Passes"]
    lines.extend(f"- {item}" for item in result["passes"])
    lines.extend(["", "## Failures"])
    failures = result["failures"]
    if failures:
        lines.extend(f"- {item}" for item in failures)
    else:
        lines.append("- none")
    (REPORT_DIR / "validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())

