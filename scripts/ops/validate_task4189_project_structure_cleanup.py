from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

try:
    from ops_common import ROOT, print_result
except ModuleNotFoundError:
    from scripts.ops.ops_common import ROOT, print_result


TASK_DIR = ROOT / "docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review"


REQUIRED = [
    TASK_DIR / "cleanup_summary.json",
    TASK_DIR / "root_structure_inventory.csv",
    TASK_DIR / "docs_surface_inventory.csv",
    TASK_DIR / "stale_report_candidates.csv",
    TASK_DIR / "duplicate_axis_review.csv",
    TASK_DIR / "cleanup_execution_log.csv",
    TASK_DIR / "gpt_pro_project_structure_prompt.md",
    TASK_DIR / "gpt_pro_consult_ledger.csv",
    TASK_DIR / "report.md",
    TASK_DIR / "artifact_manifest.csv",
    TASK_DIR / "validation_results.md",
    TASK_DIR / "task_result_contract.yaml",
]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    for path in REQUIRED:
        if path.exists():
            passes.append(f"exists: {path.relative_to(ROOT).as_posix()}")
        else:
            failures.append(f"missing: {path.relative_to(ROOT).as_posix()}")

    summary_path = TASK_DIR / "cleanup_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("automated_deletions", 0) > 1:
            failures.append("automated_deletions exceeds safe limit of 1")
        else:
            passes.append(f"automated_deletions: {summary.get('automated_deletions')}")
        if summary.get("hard_boundaries", {}).get("real_capital") == "FORBIDDEN":
            passes.append("hard boundaries preserved")
        else:
            failures.append("hard boundary real_capital not preserved")

    deletion_log = TASK_DIR / "cleanup_execution_log.csv"
    if deletion_log.exists():
        rows = csv_rows(deletion_log)
        unsafe = [row for row in rows if row.get("path") != ".pytest_cache"]
        if unsafe:
            failures.append(f"unexpected automated cleanup paths: {unsafe}")
        else:
            passes.append("automated cleanup limited to .pytest_cache")

    if (ROOT / ".pytest_cache").exists():
        warnings.append(".pytest_cache still present")
    else:
        passes.append(".pytest_cache absent")

    proc = subprocess.run(
        [sys.executable, "scripts/ops/validate_project_hygiene.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode == 0:
        passes.append("project hygiene validator passes")
        if "PASS_WITH_WARNINGS" in proc.stdout:
            warnings.append("project hygiene validator has known-debt warnings")
    else:
        failures.append(f"project hygiene validator failed:\n{proc.stdout}")

    return print_result("TASK-4189 PROJECT STRUCTURE CLEANUP VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
