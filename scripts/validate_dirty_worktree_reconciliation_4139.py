from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4139"
SLUG = "task_4139_dirty_worktree_artifact_reconciliation"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4139 DIRTY WORKTREE RECONCILIATION VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "validator_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    md = "# TASK-4139 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.reconcile_dirty_worktree_4139 import build

    build()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        ARTIFACT_DIR / "dirty_worktree_inventory.csv",
        ARTIFACT_DIR / "dirty_worktree_summary.csv",
        ARTIFACT_DIR / "dirty_worktree_p0_review_queue.csv",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "dirty_reconciliation_summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    inventory = read_csv(ARTIFACT_DIR / "dirty_worktree_inventory.csv")
    p0_rows = read_csv(ARTIFACT_DIR / "dirty_worktree_p0_review_queue.csv")
    if not inventory:
        failures.append("dirty inventory is empty; this task should classify current dirty files")
    else:
        passes.append(f"dirty_inventory_rows: {len(inventory)}")
    if not p0_rows:
        warnings.append("P0 review queue is empty; unusual for current dirty worktree")
    else:
        passes.append(f"p0_review_rows: {len(p0_rows)}")

    forbidden_auto_actions = {"DELETE_NOW", "RESTORE_NOW", "CLEAN_NOW"}
    bad_actions = [row for row in inventory if row.get("recommended_action") in forbidden_auto_actions]
    if bad_actions:
        failures.append("validator found automatic delete/restore/clean action recommendations")
    else:
        passes.append("no_automatic_delete_restore_clean_recommendations")

    summary = json.loads((REPORT_DIR / "dirty_reconciliation_summary.json").read_text(encoding="utf-8"))
    if summary.get("automatic_cleanup_performed") or summary.get("files_deleted_or_restored_by_this_task") != 0:
        failures.append("TASK-4139 must classify only; it must not delete or restore files")
    else:
        passes.append("classification_only_no_file_cleanup")
    if int(summary.get("total_dirty_rows", 0)) != len(inventory):
        failures.append("summary total_dirty_rows does not match inventory")
    else:
        passes.append("summary_matches_inventory")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
