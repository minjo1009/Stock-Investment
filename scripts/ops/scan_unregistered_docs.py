from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops_common import ROOT, doc_registry, ensure_parent, match_path, rel, write_yaml


REPORT_DIR = ROOT / "docs" / "reports" / "task_4109_doc_registry_closure_and_obsolete_doc_cleanup"
DEFAULT_INVENTORY = REPORT_DIR / "unregistered_docs_inventory.csv"
DEFAULT_APPLIED = REPORT_DIR / "applied_doc_registry_entries.csv"
DEFAULT_DELETED = REPORT_DIR / "deleted_obsolete_docs.csv"

DEFAULT_EXCLUDES = [
    "docs/generated_context/*_context.md",
]


@dataclass(frozen=True)
class Finding:
    path: str
    action: str
    type: str
    domain: str
    status: str
    priority: str
    codex_read: str
    owner: str
    created_by_task: str
    reason: str


def docs_markdown_files() -> list[str]:
    docs = ROOT / "docs"
    if not docs.exists():
        return []
    return sorted(rel(path) for path in docs.rglob("*.md") if path.is_file())


def registered_paths(registry: dict[str, Any]) -> set[str]:
    return {
        str(doc.get("path", "")).replace("\\", "/")
        for doc in registry.get("documents", [])
        if doc.get("path")
    }


def task_from_report_path(path: str) -> str:
    match = re.search(r"docs/reports/task_([^/]+)", path)
    if not match:
        return "TASK-4109"
    raw = match.group(1)
    token = raw.split("_", 1)[0].upper()
    return f"TASK-{token}"


def desktop_counterpart_exists(path: str) -> bool:
    name = Path(path).name
    counterpart = re.sub(r"-DESKTOP-[A-Za-z0-9]+", "", name)
    if counterpart == name:
        return False
    return (ROOT / Path(path).with_name(counterpart)).exists()


def classify(path: str) -> Finding:
    if "-DESKTOP-" in path and desktop_counterpart_exists(path):
        return Finding(
            path=path,
            action="DELETE_CONFLICT_DUPLICATE",
            type="ARCHIVE",
            domain="OPS",
            status="ARCHIVED",
            priority="P3",
            codex_read="NEVER",
            owner="codex_governance",
            created_by_task="TASK-4109",
            reason="machine conflict duplicate with canonical counterpart present",
        )

    if path.startswith("docs/archive/"):
        return Finding(
            path=path,
            action="REGISTER_ARCHIVED",
            type="ARCHIVE",
            domain="ARCHIVE",
            status="ARCHIVED",
            priority="P3",
            codex_read="NEVER",
            owner="research_governance",
            created_by_task="TASK-4109",
            reason="archive material retained but excluded from normal Codex read scope",
        )

    if path.startswith("docs/reports/task_410"):
        return Finding(
            path=path,
            action="REGISTER_ACTIVE_TASK_ARTIFACT",
            type="TASK_REPORT",
            domain="OPS",
            status="ACTIVE",
            priority="P1",
            codex_read="TASK_PROFILE_ONLY",
            owner="codex_governance",
            created_by_task="TASK-4109",
            reason="current governance cleanup task artifact",
        )

    if path.startswith("docs/reports/task_"):
        doc_type = "TASK_REPORT"
        if path.endswith("gpt_review_notes.md") or "gpt_" in Path(path).name:
            doc_type = "REFERENCE"
        return Finding(
            path=path,
            action="REGISTER_HISTORICAL_TASK_REPORT",
            type=doc_type,
            domain="REPORTS",
            status="HISTORICAL",
            priority="P3",
            codex_read="ONLY_IF_REFERENCED",
            owner="research_governance",
            created_by_task=task_from_report_path(path),
            reason="historical task report retained only when explicitly referenced",
        )

    active_dirs = {
        "docs/acceptance/": ("SSOT", "ACCEPTANCE"),
        "docs/active/": ("SSOT", "GLOBAL"),
        "docs/candidate_funnel/": ("SSOT", "CANDIDATE_FUNNEL"),
        "docs/contracts/": ("SSOT", "CONTRACTS"),
        "docs/db/": ("GOVERNANCE", "DB"),
        "docs/execution/": ("SSOT", "EXECUTION"),
        "docs/frontend_app_ssot/": ("SSOT", "FRONTEND"),
        "docs/frontend_ios/": ("REFERENCE", "FRONTEND"),
        "docs/frontend_web/": ("REFERENCE", "FRONTEND"),
        "docs/operating_system/": ("GOVERNANCE", "OPS"),
        "docs/ownership/": ("GOVERNANCE", "OWNERSHIP"),
        "docs/replay/": ("SSOT", "REPLAY"),
        "docs/specs/": ("SSOT", "STRATEGY_SPEC"),
    }
    for prefix, (doc_type, domain) in active_dirs.items():
        if path.startswith(prefix):
            return Finding(
                path=path,
                action="REGISTER_ACTIVE_DOC",
                type=doc_type,
                domain=domain,
                status="ACTIVE",
                priority="P1",
                codex_read="TASK_PROFILE_ONLY",
                owner="research_governance",
                created_by_task="TASK-4109",
                reason="current operating or domain source document",
            )

    if path.startswith("docs/architecture/"):
        return Finding(
            path=path,
            action="REGISTER_ACTIVE_DOC",
            type="GOVERNANCE",
            domain="ARCHITECTURE",
            status="ACTIVE",
            priority="P1",
            codex_read="TASK_PROFILE_ONLY",
            owner="research_governance",
            created_by_task="TASK-4109",
            reason="architecture governance document",
        )

    if path.startswith("docs/llm_wiki/"):
        return Finding(
            path=path,
            action="REGISTER_REFERENCE_DOC",
            type="REFERENCE",
            domain="LLM_WIKI",
            status="ACTIVE",
            priority="P2",
            codex_read="ONLY_IF_REFERENCED",
            owner="research_governance",
            created_by_task="TASK-4109",
            reason="routing memory, not primary source of truth",
        )

    if path.startswith("docs/obsidian/"):
        return Finding(
            path=path,
            action="REGISTER_LOCAL_REFERENCE_DOC",
            type="REFERENCE",
            domain="OBSIDIAN",
            status="LOCAL_ONLY",
            priority="P2",
            codex_read="ONLY_IF_REFERENCED",
            owner="research_governance",
            created_by_task="TASK-4109",
            reason="human cockpit note, not primary source of truth",
        )

    if path.startswith("docs/audits/") or path.startswith("docs/graphify/") or path.startswith("docs/phases/"):
        return Finding(
            path=path,
            action="REGISTER_HISTORICAL_REFERENCE",
            type="REFERENCE",
            domain="AUDIT",
            status="HISTORICAL",
            priority="P3",
            codex_read="ONLY_IF_REFERENCED",
            owner="research_governance",
            created_by_task="TASK-4109",
            reason="historical audit or phase material retained for traceability",
        )

    return Finding(
        path=path,
        action="REGISTER_REFERENCE_DOC",
        type="REFERENCE",
        domain="GLOBAL",
        status="ACTIVE",
        priority="P2",
        codex_read="ONLY_IF_REFERENCED",
        owner="research_governance",
        created_by_task="TASK-4109",
        reason="remaining registered document with limited read scope",
    )


def scan() -> list[Finding]:
    registry = doc_registry()
    paths = registered_paths(registry)
    findings: list[Finding] = []
    for path in docs_markdown_files():
        if any(match_path(path, pattern) for pattern in DEFAULT_EXCLUDES):
            continue
        if path not in paths:
            findings.append(classify(path))
    return findings


def write_findings(path: Path, findings: list[Finding]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(Finding.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in findings:
            writer.writerow(row.__dict__)


def delete_conflict_duplicates(findings: list[Finding]) -> list[Finding]:
    deleted: list[Finding] = []
    docs_root = (ROOT / "docs").resolve()
    for row in findings:
        if row.action != "DELETE_CONFLICT_DUPLICATE":
            continue
        target = (ROOT / row.path).resolve()
        if docs_root not in target.parents:
            raise RuntimeError(f"refusing to delete outside docs: {target}")
        if "-DESKTOP-" not in target.name:
            raise RuntimeError(f"refusing to delete non-conflict file: {target}")
        if not desktop_counterpart_exists(row.path):
            raise RuntimeError(f"refusing to delete without canonical counterpart: {target}")
        if target.exists():
            target.unlink()
            deleted.append(row)
    return deleted


def apply_registry_entries(findings: list[Finding]) -> list[Finding]:
    registry = doc_registry()
    paths = registered_paths(registry)
    applied: list[Finding] = []
    for row in findings:
        if row.action == "DELETE_CONFLICT_DUPLICATE":
            continue
        if row.path in paths:
            continue
        registry.setdefault("documents", []).append(
            {
                "path": row.path,
                "type": row.type,
                "domain": row.domain,
                "status": row.status,
                "priority": row.priority,
                "codex_read": row.codex_read,
                "owner": row.owner,
                "created_by_task": row.created_by_task,
                "supersedes": [],
                "superseded_by": None,
            }
        )
        paths.add(row.path)
        applied.append(row)
    registry["updated_at"] = "2026-06-29"
    write_yaml("ops/doc_registry.yaml", registry)
    return applied


def remove_empty_conflict_dirs() -> None:
    for path in sorted((ROOT / "docs").rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            try:
                path.rmdir()
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--applied-output", default=str(DEFAULT_APPLIED))
    parser.add_argument("--deleted-output", default=str(DEFAULT_DELETED))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    findings = scan()
    write_findings(ROOT / args.inventory, findings)
    print(f"PASS inventory: {args.inventory}")
    print(f"PASS unregistered_docs_seen: {len(findings)}")
    for action in sorted({row.action for row in findings}):
        print(f"PASS {action}: {sum(1 for row in findings if row.action == action)}")

    if args.apply:
        deleted = delete_conflict_duplicates(findings)
        remove_empty_conflict_dirs()
        applied = apply_registry_entries(findings)
        write_findings(ROOT / args.deleted_output, deleted)
        write_findings(ROOT / args.applied_output, applied)
        print(f"PASS deleted_conflict_duplicates: {len(deleted)}")
        print(f"PASS registry_entries_added: {len(applied)}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
        print(f"PASS applied_manifest: {args.applied_output}")

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
