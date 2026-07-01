from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.validation.l4_thesis_bundle_validator import validate_l4_package


TASK_ID = "TASK-4156"
REPORT_DIR = Path("docs/reports/task_4156_l4_thesis_bundle_bootstrap")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="data/diagnostics/l4")
    args = parser.parse_args()
    result = validate_l4_package(args.artifact_dir)
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "l4_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    patch_manifest_validation_status(artifact_dir / "l4_run_manifest.json", result)
    write_validation_results(result)
    print(f"[{TASK_ID}] {result['status']} passes={len(result['passes'])} failures={len(result['failures'])}")
    for failure in result["failures"]:
        print(f"FAIL: {failure}")
    return 0 if result["status"] == "PASS" else 1


def patch_manifest_validation_status(path: Path, result: dict[str, object]) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["validation_status"] = result["status"]
    manifest["validation_errors"] = result["failures"]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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

