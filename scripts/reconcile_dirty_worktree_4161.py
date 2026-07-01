from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TASK-4161"
SLUG = "task_4161_dirty_worktree_triage"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_status_rows() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    parts = [part.decode("utf-8", errors="replace") for part in proc.stdout.split(b"\0") if part]
    rows: list[dict[str, str]] = []
    index = 0
    while index < len(parts):
        entry = parts[index]
        status = entry[:2]
        path = entry[3:].replace("\\", "/")
        if status.startswith(("R", "C")):
            index += 1
            if index < len(parts):
                path = parts[index].replace("\\", "/")
        rows.append({"status": status, "path": path})
        index += 1
    return rows


def classify(status: str, path: str) -> tuple[str, str, str, str]:
    deleted = "D" in status
    modified = "M" in status
    untracked = status == "??"

    if path.startswith("docs/reports/task_4161_") or path.startswith("data/artifacts/task_4161_"):
        return ("TASK_4161_OUTPUT", "KEEP_REGISTER", "P0", "Current cleanup task output.")
    if path in {"AGENTS.md", ".gitignore"}:
        return ("ROOT_GOVERNANCE_OR_IGNORE_RULE", "KEEP_REGISTER", "P0", "Root governance or ignore policy file.")
    if path in {"ops/task_registry.yaml", "ops/doc_registry.yaml"} or path.startswith("ops/"):
        return ("GOVERNANCE_REGISTRY", "KEEP_REGISTER", "P0", "Governance files required by AGENTS.md.")
    if path.startswith("docs/reports/task_41"):
        return ("CURRENT_TASK_REPORT", "KEEP_REGISTER", "P0", "Recent task report artifact from current L0-L4 work.")
    if path.startswith("scripts/") and untracked:
        return ("CURRENT_TASK_SCRIPT", "KEEP_PAIR_WITH_TASK", "P0", "New script likely belongs to recent TASK-4100+ work.")
    if path.startswith("src/") and untracked:
        return ("CURRENT_TASK_SRC", "KEEP_PAIR_WITH_TASK", "P0", "New source file likely belongs to recent active layer work.")
    if path.startswith("tests/") and untracked:
        return ("CURRENT_TASK_TEST", "KEEP_PAIR_WITH_TASK", "P0", "New test likely pairs with recent active layer code.")
    if path.startswith("configs/") and untracked:
        return ("CURRENT_TASK_CONFIG", "KEEP_PAIR_WITH_TASK", "P0", "New config likely belongs to recent active layer work.")
    if path.startswith("tools/db/source_acquisition/") and (modified or untracked):
        return ("L0_L1_SOURCE_CODE", "KEEP_PAIR_WITH_TASK", "P0", "Source acquisition code belongs to current L0/L1 work.")
    if path.startswith("configs/source_registry/") or path.startswith("configs/db_source_acquisition"):
        return ("L0_SOURCE_CONFIG", "KEEP_PAIR_WITH_TASK", "P0", "L0 source or scheduler config.")
    if path.startswith("scripts/run_l0") or path.startswith("scripts/start_l0") or path.startswith("scripts/validate_l0"):
        return ("L0_SCRIPT", "KEEP_PAIR_WITH_TASK", "P0", "L0 runtime/validator script.")
    if path.endswith(".dvc") and deleted:
        return ("DELETED_DVC_POINTER", "OWNER_REVIEW_RESTORE_OR_RETIRE", "P0", "DVC pointer deletion can break artifact reproducibility.")
    if deleted and (
        path.startswith("src/brain/")
        or path.startswith("src/l2/")
        or "l2_" in path
        or "l3_" in path
        or path.startswith("tests/test_l3")
    ):
        return ("DELETED_L2_L3_CODE_OR_TEST", "OWNER_REVIEW_RESTORE_OR_CONFIRM_DELETE", "P0", "Layer code/test deletion needs explicit owner review.")
    if deleted and (path.startswith("docs/reports/A") or path.startswith("docs/reports/task_l")):
        return ("DELETED_HISTORICAL_REPORT", "OWNER_REVIEW_ARCHIVE_OR_CONFIRM_DELETE", "P1", "Historical report deletion should follow doc registry/archive policy.")
    if deleted and path.startswith("data/artifacts/"):
        return ("DELETED_DATA_ARTIFACT", "OWNER_REVIEW_DVC_OR_RETENTION_POLICY", "P1", "Data artifact deletion should follow artifact retention policy.")
    if path in {".codex/", ".codex"} or path.startswith(".codex/"):
        return ("LOCAL_CODEX_STATE", "IGNORE_LOCAL_ONLY", "P2", "Local Codex app state should not be project source.")
    if path == "tasks.zip" or path.endswith(".zip"):
        return ("LOCAL_ARCHIVE_FILE", "OWNER_REVIEW_IGNORE_OR_REGISTER", "P2", "Zip archives are usually local transfer artifacts.")
    if path.startswith("data/diagnostics/") and untracked:
        return ("LOCAL_RUNTIME_DIAGNOSTIC", "IGNORE_OR_REGISTER_RUNTIME_ARTIFACT", "P2", "Generated diagnostic artifact.")
    if path.startswith("frontend/"):
        return ("FRONTEND_OR_CATALOG", "KEEP_PAIR_WITH_TASK", "P1", "Frontend/catalog change needs task pairing.")
    if path.startswith("docs/architecture/") or path.startswith("docs/operating_system/") or path.startswith("docs/contracts/"):
        return ("ACTIVE_DOC", "KEEP_REGISTER", "P1", "Architecture or operating document.")
    if path.startswith("docs/") and untracked:
        return ("DOC_UNTRACKED", "REGISTER_OR_ARCHIVE", "P1", "Untracked documentation needs doc registry decision.")
    if deleted:
        return ("DELETED_OTHER", "OWNER_REVIEW_RESTORE_OR_CONFIRM_DELETE", "P1", "Deletion needs explicit review.")
    if modified:
        return ("MODIFIED_OTHER", "KEEP_OR_REVIEW", "P1", "Modified tracked file needs task pairing.")
    if untracked:
        return ("UNTRACKED_OTHER", "CLASSIFY_REGISTER_OR_IGNORE", "P2", "Untracked file needs registration or ignore decision.")
    return ("OTHER_GIT_STATE", "OWNER_REVIEW", "P2", "Other git state.")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def build() -> dict[str, object]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows = git_status_rows()
    rows: list[dict[str, object]] = []
    for item in raw_rows:
        bucket, action, priority, reason = classify(item["status"], item["path"])
        rows.append(
            {
                "task_id": TASK_ID,
                "git_status": item["status"],
                "path": item["path"],
                "bucket": bucket,
                "recommended_action": action,
                "priority": priority,
                "reason": reason,
            }
        )

    fields = ["task_id", "git_status", "path", "bucket", "recommended_action", "priority", "reason"]
    write_csv(ARTIFACT_DIR / "dirty_worktree_inventory.csv", rows, fields)
    write_csv(ARTIFACT_DIR / "dirty_worktree_p0_queue.csv", [row for row in rows if row["priority"] == "P0"], fields)
    write_csv(
        ARTIFACT_DIR / "dirty_worktree_review_required.csv",
        [row for row in rows if str(row["recommended_action"]).startswith("OWNER_REVIEW")],
        fields,
    )
    write_csv(
        ARTIFACT_DIR / "dirty_worktree_keep_register.csv",
        [row for row in rows if row["recommended_action"] in {"KEEP_REGISTER", "KEEP_PAIR_WITH_TASK"}],
        fields,
    )
    write_csv(
        ARTIFACT_DIR / "dirty_worktree_local_ignore_candidates.csv",
        [row for row in rows if "IGNORE" in str(row["recommended_action"])],
        fields,
    )

    summary_rows = []
    for metric, counter in [
        ("git_status", Counter(str(row["git_status"]) for row in rows)),
        ("bucket", Counter(str(row["bucket"]) for row in rows)),
        ("recommended_action", Counter(str(row["recommended_action"]) for row in rows)),
        ("priority", Counter(str(row["priority"]) for row in rows)),
    ]:
        summary_rows.extend({"metric_type": metric, "name": name, "count": count} for name, count in sorted(counter.items()))
    write_csv(ARTIFACT_DIR / "dirty_worktree_summary.csv", summary_rows, ["metric_type", "name", "count"])

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "total_dirty_rows": len(rows),
        "by_status": dict(Counter(str(row["git_status"]) for row in rows)),
        "by_priority": dict(Counter(str(row["priority"]) for row in rows)),
        "by_action": dict(Counter(str(row["recommended_action"]) for row in rows)),
        "automatic_cleanup_performed": False,
        "files_deleted_or_restored_by_this_task": 0,
    }
    (REPORT_DIR / "dirty_worktree_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    report = "# TASK-4161 Dirty Worktree Triage\n\n"
    report += "## Conclusion\n\n"
    report += "The dirty worktree is not a single cleanup problem. It is a mix of recent active task outputs, historical deletion markers, DVC pointer deletions, and local runtime artifacts. This task performs classification only and does not delete or restore files automatically. It also updates `.gitignore` for local Codex state and runtime diagnostics so future status noise is lower.\n\n"
    report += "## Summary\n\n"
    report += "| Metric | Count |\n|---|---:|\n"
    report += f"| Total dirty rows | {len(rows)} |\n"
    for status, count in sorted(summary["by_status"].items()):
        report += f"| Git status `{status}` | {count} |\n"
    report += "\n## Recommended handling\n\n"
    report += "| Priority | Handling |\n|---|---|\n"
    report += "| P0 | Keep/register recent TASK-4100+ outputs and review deleted DVC/L2/L3 files before any restore/delete decision. |\n"
    report += "| P1 | Review historical report/data artifact deletions against doc registry and retention policy. |\n"
    report += "| P2 | Ignore or register local-only files such as `.codex/`, zip archives, and runtime diagnostics. |\n\n"
    report += "## Files produced\n\n"
    report += "- `dirty_worktree_inventory.csv`\n"
    report += "- `dirty_worktree_p0_queue.csv`\n"
    report += "- `dirty_worktree_review_required.csv`\n"
    report += "- `dirty_worktree_keep_register.csv`\n"
    report += "- `dirty_worktree_local_ignore_candidates.csv`\n"
    report += "- `dirty_worktree_summary.csv`\n"
    report += "- `dirty_worktree_summary.json`\n"
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")

    manifest_rows = [
        {"path": ".gitignore", "type": "CONFIG", "purpose": "Ignore local Codex state and runtime diagnostics", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "Task registry update", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "Document registry update", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/reconcile_dirty_worktree_4161.py", "type": "CODE", "purpose": "Dirty worktree triage inventory builder", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_dirty_worktree_4161.py", "type": "VALIDATOR", "purpose": "Dirty worktree triage validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_inventory.csv", "type": "ARTIFACT", "purpose": "Full dirty file inventory", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_p0_queue.csv", "type": "ARTIFACT", "purpose": "P0 dirty file review queue", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_review_required.csv", "type": "ARTIFACT", "purpose": "Owner review required dirty files", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_keep_register.csv", "type": "ARTIFACT", "purpose": "Files to preserve and register or pair with tasks", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_local_ignore_candidates.csv", "type": "ARTIFACT", "purpose": "Local ignore candidates", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"data/artifacts/{SLUG}/dirty_worktree_summary.csv", "type": "ARTIFACT", "purpose": "Dirty worktree summary table", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/dirty_worktree_summary.json", "type": "ARTIFACT", "purpose": "Dirty worktree summary JSON", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "Dirty worktree triage report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "Task artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "Validation results", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    write_csv(REPORT_DIR / "artifact_manifest.csv", manifest_rows, ["path", "type", "purpose", "created_or_modified", "task_id"])

    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
