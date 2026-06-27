from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUT_DIR = Path("docs/reports/A005_full_file_inventory_audit")
EXCLUDED_DIRS = {".git"}
EXCLUDED_PREFIXES = {".dvc/cache", ".dvc/tmp"}
TEXTUAL_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".ps1",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Classification:
    class_name: str
    recommendation: str
    delete_risk: str
    reason: str


def is_under(rel: str, prefix: str) -> bool:
    return rel == prefix or rel.startswith(prefix + "/")


def classify(rel: str, size_bytes: int) -> Classification:
    path = Path(rel)
    parts = rel.split("/")
    name = path.name
    suffix = path.suffix.lower()

    if name in {".env", ".kis_token_cache.json"} or suffix in {".env"} or rel.endswith(".env"):
        return Classification("PROTECTED_SECRET_OR_LOCAL_AUTH", "KEEP", "CRITICAL", "Local secret/auth material; never delete or archive automatically.")

    if suffix in {".db", ".sqlite", ".sqlite3"}:
        return Classification("PROTECTED_DB_AUTHORITY", "KEEP", "CRITICAL", "Database authority or replay evidence; never delete automatically.")

    if is_under(rel, "data/raw"):
        return Classification("PROTECTED_RAW_SOURCE", "KEEP", "CRITICAL", "Raw source data must be preserved or migrated only by source-owner plan.")

    if is_under(rel, "docs/active"):
        return Classification("ACTIVE_OPERATING_LAYER", "KEEP", "LOW", "Default Codex operating layer.")

    if rel in {"tasks/task_registry.csv", "tasks/active_task_registry.csv"}:
        return Classification("REGISTRY", "KEEP", "CRITICAL", "Canonical or active task registry.")

    if is_under(rel, "docs/ownership") or is_under(rel, "docs/acceptance"):
        return Classification("CANONICAL_GOVERNANCE", "KEEP", "CRITICAL", "Governance or acceptance source of truth.")

    if "validate" in name and suffix == ".py":
        return Classification("VALIDATOR", "KEEP", "HIGH", "Validation command or closeout control.")

    if name == "artifact_manifest.csv":
        return Classification("ARTIFACT_MANIFEST", "KEEP", "HIGH", "Artifact manifest and audit trail.")

    if "__pycache__" in parts or name.endswith((".pyc", ".pyo")):
        return Classification("GENERATED_CACHE", "DELETE_SAFE", "LOW", "Regenerable Python cache.")

    if is_under(rel, ".pytest_cache"):
        return Classification("GENERATED_CACHE", "DELETE_SAFE", "LOW", "Regenerable pytest cache.")

    if rel == "graphify-out/needs_update":
        return Classification("GENERATED_MARKER", "DELETE_SAFE", "LOW", "Regenerable stale marker.")

    if is_under(rel, "downloads"):
        return Classification("LOCAL_INSTALLER_OR_DOWNLOAD", "NEEDS_REVIEW", "MEDIUM", "Downloaded local installer; owner should confirm before deletion.")

    if is_under(rel, "docs/tmp"):
        return Classification("TMP_OR_CHECKPOINT", "NEEDS_REVIEW", "MEDIUM", "Temporary/checkpoint file may be historical validation evidence.")

    if is_under(rel, "logs"):
        return Classification("RUN_LOG", "NEEDS_REVIEW", "MEDIUM", "Run log may be summarized elsewhere but needs owner confirmation.")

    if is_under(rel, "graphify-out"):
        return Classification("STALE_DISCOVERY_OUTPUT", "ARCHIVE_REVIEW", "MEDIUM", "Stale Graphify output; archive or regenerate after reference plan.")

    if is_under(rel, "docs/obsidian"):
        return Classification("NAVIGATION_LAYER", "ARCHIVE_REVIEW", "MEDIUM", "Human navigation layer excluded from default Codex scope.")

    if is_under(rel, "docs/reports"):
        if is_under(rel, "docs/reports/A001_project_management_reset") or is_under(rel, "docs/reports/A002_A003_safe_archive_delete_pass") or is_under(rel, "docs/reports/A004_project_management_system_audit") or is_under(rel, "docs/reports/A005_full_file_inventory_audit"):
            return Classification("ACTIVE_GOVERNANCE_REPORT", "KEEP", "LOW", "Current project-management cleanup/audit report.")
        if size_bytes >= 10 * 1024 * 1024:
            return Classification("LARGE_REPORT_ARTIFACT", "ARCHIVE_REVIEW", "HIGH", "Large report artifact; requires dependency-aware migration.")
        return Classification("HISTORICAL_REPORT", "KEEP_OR_ARCHIVE_REVIEW", "MEDIUM", "Historical report evidence; exclude from default read scope.")

    if is_under(rel, "frontend_data/catalog"):
        return Classification("POSSIBLE_DUPLICATE_GENERATED_CATALOG", "NEEDS_REVIEW", "HIGH", "May duplicate frontend public catalog; consumer review required.")

    if is_under(rel, "frontend/trader-terminal/public/catalog"):
        return Classification("FRONTEND_PUBLIC_CATALOG", "KEEP", "HIGH", "Frontend-consumed catalog output.")

    if suffix in {".zip", ".msi"}:
        return Classification("LOCAL_BINARY_OR_ARCHIVE", "NEEDS_REVIEW", "MEDIUM", "Local archive/binary should not be deleted without owner review.")

    if is_under(rel, ".codex") or is_under(rel, ".obsidian"):
        return Classification("LOCAL_TOOL_STATE", "NEEDS_REVIEW", "MEDIUM", "Local tool state; do not manage as project source without owner approval.")

    if parts[0] in {"src", "tests", "scripts", "config", "configs", "frontend"}:
        return Classification("PROJECT_SOURCE_OR_CONFIG", "KEEP", "MEDIUM", "Project code/config/test surface.")

    if parts[0] in {"docs", "tasks", "phases", "prompts", "templates", "skills"}:
        return Classification("PROJECT_DOC_OR_TASK", "KEEP", "LOW", "Project documentation/task support.")

    if parts[0] in {"data", "frontend_data"}:
        return Classification("DERIVED_OR_RUNTIME_DATA", "NEEDS_REVIEW", "HIGH", "Data output or runtime-derived material; owner review required.")

    if suffix not in TEXTUAL_SUFFIXES and size_bytes >= 25 * 1024 * 1024:
        return Classification("LARGE_UNKNOWN_BINARY", "NEEDS_REVIEW", "HIGH", "Large non-text file outside explicit protected classes.")

    return Classification("UNKNOWN_NEEDS_REVIEW", "NEEDS_REVIEW", "MEDIUM", "No specific policy matched; owner review required.")


def iter_files(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in rel.split("/")):
            continue
        if any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDED_PREFIXES):
            continue
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        cls = classify(rel, int(stat.st_size))
        rows.append(
            {
                "path": rel,
                "top_dir": rel.split("/", 1)[0],
                "suffix": path.suffix.lower() or "<none>",
                "size_bytes": int(stat.st_size),
                "class": cls.class_name,
                "recommendation": cls.recommendation,
                "delete_risk": cls.delete_risk,
                "reason": cls.reason,
            }
        )
    rows.sort(key=lambda row: str(row["path"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]], group_field: str) -> list[dict[str, object]]:
    counts: dict[str, int] = Counter()
    sizes: dict[str, int] = defaultdict(int)
    for row in rows:
        key = str(row[group_field])
        counts[key] += 1
        sizes[key] += int(row["size_bytes"])
    return [
        {"group": key, "file_count": counts[key], "size_bytes": sizes[key]}
        for key in sorted(counts, key=lambda k: sizes[k], reverse=True)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    root = args.root.resolve()
    out_dir = args.out_dir
    rows = iter_files(root)
    fieldnames = ["path", "top_dir", "suffix", "size_bytes", "class", "recommendation", "delete_risk", "reason"]

    write_csv(out_dir / "file_inventory.csv", rows, fieldnames)
    write_csv(out_dir / "classification_summary.csv", summarize(rows, "class"), ["group", "file_count", "size_bytes"])
    write_csv(out_dir / "top_dir_summary.csv", summarize(rows, "top_dir"), ["group", "file_count", "size_bytes"])
    write_csv(out_dir / "delete_safe_candidates.csv", [r for r in rows if r["recommendation"] == "DELETE_SAFE"], fieldnames)
    write_csv(out_dir / "needs_review_candidates.csv", [r for r in rows if r["recommendation"] == "NEEDS_REVIEW"], fieldnames)
    write_csv(out_dir / "archive_review_candidates.csv", [r for r in rows if "ARCHIVE" in str(r["recommendation"])], fieldnames)
    write_csv(out_dir / "protected_keep_files.csv", [r for r in rows if r["delete_risk"] == "CRITICAL" or r["recommendation"] == "KEEP"], fieldnames)

    print(f"[FILE_INVENTORY_AUDIT] files={len(rows)} out_dir={out_dir}")


if __name__ == "__main__":
    main()
