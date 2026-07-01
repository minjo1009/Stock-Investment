from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ops_common import ROOT, load_yaml
except ModuleNotFoundError:
    from scripts.ops.ops_common import ROOT, load_yaml


TASK_ID = "TASK-4189"
REPORT_DIR = ROOT / "docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def policy_map() -> dict[str, dict[str, Any]]:
    policy = load_yaml("ops/project_hygiene_policy.yaml")
    return {str(item.get("name")): item for item in policy.get("root_entries", [])}


def root_inventory() -> list[dict[str, Any]]:
    declared = policy_map()
    rows: list[dict[str, Any]] = []
    for item in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        if item.name == ".git":
            last_write = ""
        else:
            last_write = datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()
        policy = declared.get(item.name, {})
        rows.append(
            {
                "path": item.name,
                "kind": "directory" if item.is_dir() else "file",
                "classification": policy.get("classification", "UNCLASSIFIED"),
                "action": policy.get("action", "classify_or_remove"),
                "presence": policy.get("presence", "required"),
                "last_write_utc": last_write,
                "decision": "KEEP_CLASSIFIED" if policy else "FAIL_UNCLASSIFIED",
            }
        )
    return rows


def docs_surface_inventory() -> list[dict[str, Any]]:
    docs = ROOT / "docs"
    rows: list[dict[str, Any]] = []
    if not docs.exists():
        return rows
    canonical = {
        "generated_context": "GENERATED_CONTEXT",
        "reports": "TASK_REPORTS",
        "operating_system": "OPERATING_DOCS",
        "architecture": "ARCHITECTURE",
        "ownership": "OWNERSHIP",
        "llm_wiki": "ROUTING_MEMORY",
        "obsidian": "HUMAN_COCKPIT",
        "archive": "ARCHIVE",
        "graphify": "DISCOVERY_AID_REVIEW",
        "harness": "HARNESS_DOCS_REVIEW",
        "frontend_app_ssot": "FRONTEND_SSOT",
    }
    for item in sorted((p for p in docs.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        last_write = datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()
        classification = canonical.get(item.name, "DOCS_SURFACE_REVIEW")
        rows.append(
            {
                "path": rel(item),
                "classification": classification,
                "last_write_utc": last_write,
                "decision": "KEEP" if classification not in {"DISCOVERY_AID_REVIEW", "HARNESS_DOCS_REVIEW", "DOCS_SURFACE_REVIEW"} else "REVIEW",
            }
        )
    return rows


def stale_report_inventory(limit: int = 200) -> list[dict[str, Any]]:
    reports = ROOT / "docs/reports"
    rows: list[dict[str, Any]] = []
    if not reports.exists():
        return rows
    cutoff = datetime.now(timezone.utc).timestamp() - 7 * 24 * 60 * 60
    for item in sorted((p for p in reports.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        mtime = item.stat().st_mtime
        if mtime >= cutoff:
            continue
        status = "CURRENT_REGISTRY_UNKNOWN"
        if item.name.startswith("task_41") or item.name.startswith("task_418"):
            status = "RECENT_TASK_SERIES_REVIEW_BEFORE_ARCHIVE"
        elif item.name.startswith("task_"):
            status = "HISTORICAL_TASK_REPORT_ARCHIVE_CANDIDATE"
        rows.append(
            {
                "path": rel(item),
                "last_write_utc": datetime.fromtimestamp(mtime, timezone.utc).replace(microsecond=0).isoformat(),
                "age_bucket": "older_than_7_days",
                "decision": status,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def duplicate_axis_inventory() -> list[dict[str, str]]:
    candidates = [
        ("config", "configs", "config/configs duplicate root axis", "configs should remain canonical until imports prove otherwise"),
        ("apps", "frontend", "apps/frontend duplicate app root axis", "apps likely canonical for mobile; frontend needs owner review"),
        (".obsidian", "docs/obsidian", "obsidian local/app cockpit split", ".obsidian is local app state; docs/obsidian is repo cockpit"),
        ("tasks", "ops/task_registry.yaml", "legacy tasks directory vs registry", "ops/task_registry.yaml is canonical"),
    ]
    rows: list[dict[str, str]] = []
    for left, right, issue, recommendation in candidates:
        left_exists = (ROOT / left).exists()
        right_exists = (ROOT / right).exists()
        rows.append(
            {
                "left_path": left,
                "right_path": right,
                "issue": issue,
                "left_exists": str(left_exists).lower(),
                "right_exists": str(right_exists).lower(),
                "decision": "REVIEW_MERGE_OR_ARCHIVE" if left_exists and right_exists else "NO_ACTIVE_DUPLICATE",
                "recommendation": recommendation,
            }
        )
    return rows


def delete_pytest_cache() -> dict[str, Any]:
    target = (ROOT / ".pytest_cache").resolve()
    expected = (ROOT / ".pytest_cache").resolve()
    result = {
        "path": ".pytest_cache",
        "action": "delete_transient_cache",
        "status": "NOT_PRESENT",
        "notes": "No cache directory present.",
    }
    if target != expected or ROOT.resolve() not in target.parents:
        result.update(status="BLOCKED_PATH_SAFETY", notes=f"Unsafe resolved path: {target}")
        return result
    if target.exists():
        shutil.rmtree(target)
        result.update(status="DELETED", notes="Deleted regenerated pytest cache directory only.")
    return result


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    root_rows = root_inventory()
    docs_rows = docs_surface_inventory()
    stale_rows = stale_report_inventory()
    duplicate_rows = duplicate_axis_inventory()
    deletion = delete_pytest_cache()

    write_csv(
        REPORT_DIR / "root_structure_inventory.csv",
        root_rows,
        ["path", "kind", "classification", "action", "presence", "last_write_utc", "decision"],
    )
    write_csv(
        REPORT_DIR / "docs_surface_inventory.csv",
        docs_rows,
        ["path", "classification", "last_write_utc", "decision"],
    )
    write_csv(
        REPORT_DIR / "stale_report_candidates.csv",
        stale_rows,
        ["path", "last_write_utc", "age_bucket", "decision"],
    )
    write_csv(
        REPORT_DIR / "duplicate_axis_review.csv",
        duplicate_rows,
        ["left_path", "right_path", "issue", "left_exists", "right_exists", "decision", "recommendation"],
    )
    write_csv(
        REPORT_DIR / "cleanup_execution_log.csv",
        [deletion],
        ["path", "action", "status", "notes"],
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": NOW,
        "root_entries": len(root_rows),
        "docs_surfaces": len(docs_rows),
        "stale_report_candidates_limited": len(stale_rows),
        "duplicate_axes": len(duplicate_rows),
        "automated_deletions": 1 if deletion["status"] == "DELETED" else 0,
        "deletion_status": deletion["status"],
        "hard_boundaries": {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "broker_mutation": "FORBIDDEN",
            "live_order": "FORBIDDEN",
            "paper_promotion": "FORBIDDEN",
        },
    }
    write_json(REPORT_DIR / "cleanup_summary.json", summary)
    print("RESULT: PASS")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
