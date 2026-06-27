from __future__ import annotations

import csv
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


A005_DIR = Path("docs/reports/A005_full_file_inventory_audit")
A007_DIR = Path("docs/reports/A007_dvc_lfs_artifact_management")
A008_DIR = Path("docs/reports/A008_path_by_path_owner_review")
ARCHIVE_MONTH = "2026_06"
LARGE_THRESHOLD = 50 * 1024 * 1024
TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".py", ".ps1", ".txt", ".yaml", ".yml"}


@dataclass(frozen=True)
class ActionResult:
    action: str
    result: str
    target_path: str
    note: str


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def ensure_inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    return resolved


def task_id_from_report_path(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "reports":
        return parts[2]
    return "unknown_task"


def dvc_target_for_large_report(rel: str) -> str:
    task_id = task_id_from_report_path(rel)
    filename = Path(rel).name
    return f"data/artifacts/{task_id}/{filename}"


def write_pointer(path: Path, *, source_rel: str, target_rel: str, source_hash: str, size_bytes: int) -> None:
    pointer = path.with_name(path.name + ".pointer.md")
    pointer.write_text(
        "\n".join(
            [
                f"# Pointer for `{path.name}`",
                "",
                "This large report payload was moved out of `docs/reports` and is managed as a DVC artifact.",
                "",
                f"- original_path: `{source_rel}`",
                f"- artifact_path: `{target_rel}`",
                f"- size_bytes: `{size_bytes}`",
                f"- sha256: `{source_hash}`",
                "- storage_backend: `DVC`",
                "- strategy_status: `NOT_ACCEPTED`",
                "- deployment_status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
                "- real_capital: `FORBIDDEN`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def move_file_with_pointer(root: Path, source_rel: str, target_rel: str, size_bytes: int) -> ActionResult:
    source = ensure_inside(root, root / source_rel)
    target = ensure_inside(root, root / target_rel)
    if not source.exists():
        pointer = source.with_name(source.name + ".pointer.md")
        if target.exists() and pointer.exists():
            return ActionResult("MOVE_WITH_POINTER", "ALREADY_MOVED", target_rel, "Target and pointer already exist.")
        return ActionResult("MOVE_WITH_POINTER", "MISSING_SOURCE", target_rel, "Source file missing before move.")

    source_hash = sha256(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target_hash = sha256(target)
        if target_hash != source_hash:
            return ActionResult("MOVE_WITH_POINTER", "SKIPPED_TARGET_HASH_MISMATCH", target_rel, "Target exists with a different hash.")
        source.unlink()
        result = "REMOVED_DUPLICATE_SOURCE"
    else:
        shutil.move(str(source), str(target))
        result = "MOVED"
    write_pointer(source, source_rel=source_rel, target_rel=target_rel, source_hash=source_hash, size_bytes=size_bytes)
    return ActionResult("MOVE_WITH_POINTER", result, target_rel, "Large report payload moved to data/artifacts with pointer.")


def compare_public_catalog(root: Path, rel: str) -> tuple[bool, str]:
    source = root / rel
    counterpart = root / rel.replace("frontend_data/catalog", "frontend/trader-terminal/public/catalog", 1)
    if not source.exists() or not counterpart.exists():
        return False, "missing source or public counterpart"
    return sha256(source) == sha256(counterpart), counterpart.as_posix()


def move_simple(root: Path, source_rel: str, target_rel: str) -> ActionResult:
    source = ensure_inside(root, root / source_rel)
    target = ensure_inside(root, root / target_rel)
    if not source.exists():
        return ActionResult("MOVE_TO_ARCHIVE", "MISSING_SOURCE", target_rel, "Source missing before move.")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if source.is_file() and target.is_file() and sha256(source) == sha256(target):
            source.unlink()
            return ActionResult("MOVE_TO_ARCHIVE", "REMOVED_DUPLICATE_SOURCE", target_rel, "Target already had identical content.")
        return ActionResult("MOVE_TO_ARCHIVE", "SKIPPED_TARGET_EXISTS", target_rel, "Target already exists.")
    shutil.move(str(source), str(target))
    return ActionResult("MOVE_TO_ARCHIVE", "MOVED", target_rel, "Path moved to managed archive location.")


def delete_if_identical_generated(root: Path, rel: str) -> ActionResult:
    identical, counterpart_note = compare_public_catalog(root, rel)
    source = ensure_inside(root, root / rel)
    if not source.exists():
        return ActionResult("DELETE_LOGGED", "MISSING_SOURCE", "", "Source missing before delete.")
    if not identical:
        return ActionResult("KEEP", "KEPT_NON_IDENTICAL", "", f"Generated staging differs from public counterpart: {counterpart_note}")
    source.unlink()
    return ActionResult("DELETE_LOGGED", "DELETED", "", f"Generated staging duplicate of {counterpart_note}.")


def decision_for_needs_review(row: dict[str, str], root: Path) -> tuple[str, str, str]:
    rel = row["path"]
    cls = row["class"]
    top_dir = row["top_dir"]
    if rel in {"data/README.md", "data/catalog.py", "data/quality.py"}:
        return "KEEP_PROJECT_SOURCE", rel, "Data package source/documentation reclassified from derived/runtime."
    if cls == "DERIVED_OR_RUNTIME_DATA":
        return "DVC_TRACK", rel, "Derived/runtime artifact retained as DVC-managed project data."
    if cls == "POSSIBLE_DUPLICATE_GENERATED_CATALOG":
        identical, note = compare_public_catalog(root, rel)
        if identical:
            return "DELETE_LOGGED", "", f"Generated staging duplicate of public catalog: {note}"
        return "DVC_TRACK", rel, "Generated catalog differs from public catalog; retain for review as DVC-managed data."
    if cls == "RUN_LOG":
        return "MOVE_TO_ARCHIVE", f"docs/archive/runtime_logs/{ARCHIVE_MONTH}/{rel}", "Runtime log archived instead of deleted."
    if cls == "TMP_OR_CHECKPOINT":
        return "MOVE_TO_ARCHIVE", f"docs/archive/tmp/{ARCHIVE_MONTH}/{rel}", "Temporary/checkpoint evidence archived."
    if cls == "LOCAL_INSTALLER_OR_DOWNLOAD":
        return "DVC_TRACK", f"docs/archive/local_downloads/{ARCHIVE_MONTH}/{rel}", "Installer retained as DVC-managed binary because Git LFS is unavailable."
    if cls == "LOCAL_BINARY_OR_ARCHIVE":
        return "DVC_TRACK", f"docs/archive/external_context/{rel}", "Binary reference artifact retained as DVC-managed external context."
    if cls == "LOCAL_TOOL_STATE":
        return "KEEP", rel, "Local tool state preserved and excluded from normal project source management."
    if cls == "UNKNOWN_NEEDS_REVIEW" and top_dir == "참고 Context":
        return "DVC_TRACK", f"docs/archive/external_context/{rel}", "External reference context retained as DVC-managed project asset."
    if cls == "UNKNOWN_NEEDS_REVIEW" and rel == "trading_continuation_capture.jsonl":
        return "DVC_TRACK", "data/artifacts/runtime_capture/trading_continuation_capture.jsonl", "Runtime capture retained as DVC-managed artifact."
    if cls == "UNKNOWN_NEEDS_REVIEW" and top_dir in {".github", "context", "AGENTS.md", "README.md", ".gitignore", ".graphifyignore"}:
        return "KEEP_PROJECT_SOURCE", rel, "Project source/governance file reclassified from unknown review."
    return "KEEP", rel, "No safe automated move/delete rule; preserved."


def execute_needs_review_action(root: Path, rel: str, decision: str, target_rel: str) -> ActionResult:
    if decision == "DELETE_LOGGED":
        return delete_if_identical_generated(root, rel)
    if decision == "MOVE_TO_ARCHIVE":
        return move_simple(root, rel, target_rel)
    if decision == "DVC_TRACK" and target_rel and target_rel != rel:
        return move_simple(root, rel, target_rel)
    return ActionResult(decision, "NO_PHYSICAL_CHANGE", target_rel, "Decision recorded; no physical move/delete required.")


def text_reference_files(root: Path) -> list[Path]:
    roots = [".github", "src", "tests", "scripts", "tasks", "docs", "context"]
    files: list[Path] = []
    for rel_root in roots:
        base = root / rel_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = safe_rel(root, path)
            if rel.startswith("docs/reports/A005_") or rel.startswith("docs/reports/A006_"):
                continue
            if rel.startswith("docs/reports/A007_") or rel.startswith("docs/reports/A008_"):
                continue
            if ".dvc/cache" in rel:
                continue
            files.append(path)
    for rel in ["README.md", "AGENTS.md", ".gitignore", ".graphifyignore"]:
        path = root / rel
        if path.exists() and path.is_file():
            files.append(path)
    return files


def update_text_references(root: Path, replacements: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in text_reference_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        original = text
        hit_count = 0
        for old, new in replacements.items():
            if old in text:
                hit_count += text.count(old)
                text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            rows.append({"path": safe_rel(root, path), "replacement_count": hit_count})
    return rows


def build_and_execute(root: Path) -> None:
    A007_DIR.mkdir(parents=True, exist_ok=True)
    A008_DIR.mkdir(parents=True, exist_ok=True)

    inventory = read_csv(A005_DIR / "file_inventory.csv")
    needs_review = read_csv(A005_DIR / "needs_review_candidates.csv")
    archive_review = read_csv(A005_DIR / "archive_review_candidates.csv")
    inventory_by_path = {row["path"]: row for row in inventory}

    large_rows = [row for row in inventory if int(row["size_bytes"]) >= LARGE_THRESHOLD]
    replacements: dict[str, str] = {}
    dvc_targets: set[str] = set()
    large_plan: list[dict[str, object]] = []
    move_log: list[dict[str, object]] = []

    for row in sorted(large_rows, key=lambda item: int(item["size_bytes"]), reverse=True):
        rel = row["path"]
        cls = row["class"]
        size_bytes = int(row["size_bytes"])
        owner = "Data and Market Microstructure"
        storage_backend = "DVC"
        action = "DVC_TRACK"
        reason = "Large project payload retained as DVC-managed artifact."
        target_rel = rel
        result = ActionResult(action, "NO_PHYSICAL_CHANGE", target_rel, "DVC tracking planned.")

        if cls == "PROTECTED_DB_AUTHORITY":
            storage_backend = "PROTECTED_LOCAL_DB"
            action = "KEEP_PROTECTED"
            reason = "DB authority file is protected and not converted to DVC without owner-approved snapshot policy."
        elif rel.startswith("frontend/trader-terminal/dist/"):
            storage_backend = "IGNORED_BUILD_OUTPUT"
            action = "KEEP_IGNORED_BUILD_OUTPUT"
            reason = "Generated build output remains ignored; public catalog is the source for app runtime."
        elif cls == "LARGE_REPORT_ARTIFACT" and rel.startswith("docs/reports/"):
            target_rel = dvc_target_for_large_report(rel)
            result = move_file_with_pointer(root, rel, target_rel, size_bytes)
            action = result.action
            reason = result.note
            replacements[rel] = target_rel
            dvc_targets.add(target_rel)
        elif cls in {"DERIVED_OR_RUNTIME_DATA", "PROTECTED_RAW_SOURCE", "FRONTEND_PUBLIC_CATALOG"}:
            dvc_targets.add(rel)
        elif cls == "POSSIBLE_DUPLICATE_GENERATED_CATALOG":
            identical, note = compare_public_catalog(root, rel)
            if identical:
                action = "DELETE_LOGGED"
                storage_backend = "REGENERABLE_STAGING"
                reason = f"Duplicate generated staging catalog; public catalog is retained and DVC-managed: {note}"
            else:
                dvc_targets.add(rel)
                reason = "Generated catalog differs from public counterpart; retained as DVC-managed data."

        large_plan.append(
            {
                "path": rel,
                "size_bytes": size_bytes,
                "class": cls,
                "owner": owner,
                "storage_backend": storage_backend,
                "target_path": target_rel,
                "action": action,
                "reason": reason,
            }
        )
        if result.result != "NO_PHYSICAL_CHANGE":
            move_log.append(
                {
                    "source_path": rel,
                    "target_path": result.target_path,
                    "action": result.action,
                    "result": result.result,
                    "size_bytes": size_bytes,
                    "sha256": sha256(root / result.target_path) if (root / result.target_path).exists() and (root / result.target_path).is_file() else "",
                    "note": result.note,
                }
            )

    owner_rows: list[dict[str, object]] = []
    execution_log: list[dict[str, object]] = []
    for row in needs_review:
        rel = row["path"]
        decision, target_rel, reason = decision_for_needs_review(row, root)
        result = execute_needs_review_action(root, rel, decision, target_rel)
        if decision == "DVC_TRACK":
            dvc_targets.add(result.target_path or target_rel or rel)
        owner_rows.append(
            {
                "path": rel,
                "class": row["class"],
                "size_bytes": row["size_bytes"],
                "owner": "Data and Market Microstructure" if row["class"] == "DERIVED_OR_RUNTIME_DATA" else "Research Governance",
                "reviewer": "Governance Reviewer",
                "decision": decision,
                "action": result.action,
                "target_path": result.target_path or target_rel,
                "delete_allowed": "TRUE" if decision == "DELETE_LOGGED" else "FALSE",
                "result": result.result,
                "reason": reason,
            }
        )
        execution_log.append(
            {
                "path": rel,
                "action": result.action,
                "result": result.result,
                "target_path": result.target_path,
                "size_bytes": row["size_bytes"],
                "note": result.note,
            }
        )

    replacements["docs/archive/external_context/참고 Context/"] = "docs/archive/external_context/docs/archive/external_context/참고 Context/"
    reference_updates = update_text_references(root, replacements)

    dvc_target_rows = []
    for target in sorted(dvc_targets):
        path = root / target
        if path.exists():
            dvc_target_rows.append({"path": target, "exists": "TRUE", "size_bytes": path.stat().st_size if path.is_file() else ""})
        else:
            dvc_target_rows.append({"path": target, "exists": "FALSE", "size_bytes": ""})

    write_csv(
        A007_DIR / "large_payload_tracking_plan.csv",
        large_plan,
        ["path", "size_bytes", "class", "owner", "storage_backend", "target_path", "action", "reason"],
    )
    write_csv(
        A007_DIR / "large_payload_move_log.csv",
        move_log,
        ["source_path", "target_path", "action", "result", "size_bytes", "sha256", "note"],
    )
    write_csv(A007_DIR / "dvc_targets.csv", dvc_target_rows, ["path", "exists", "size_bytes"])
    write_csv(A007_DIR / "reference_update_log.csv", reference_updates, ["path", "replacement_count"])
    write_csv(
        A008_DIR / "owner_review_decision_matrix.csv",
        owner_rows,
        ["path", "class", "size_bytes", "owner", "reviewer", "decision", "action", "target_path", "delete_allowed", "result", "reason"],
    )
    write_csv(
        A008_DIR / "cleanup_execution_log.csv",
        execution_log,
        ["path", "action", "result", "target_path", "size_bytes", "note"],
    )

    summary_rows = [
        {"metric": "large_payload_rows", "value": len(large_plan)},
        {"metric": "large_payload_bytes", "value": sum(int(row["size_bytes"]) for row in large_plan)},
        {"metric": "large_payload_move_log_rows", "value": len(move_log)},
        {"metric": "needs_review_rows", "value": len(owner_rows)},
        {"metric": "dvc_target_rows", "value": len(dvc_target_rows)},
        {"metric": "reference_update_files", "value": len(reference_updates)},
    ]
    write_csv(A007_DIR / "execution_summary.csv", summary_rows, ["metric", "value"])
    print(
        "[A007_A008_CLEANUP] "
        f"large_rows={len(large_plan)} moved_large={len(move_log)} "
        f"needs_review={len(owner_rows)} dvc_targets={len(dvc_target_rows)} "
        f"reference_update_files={len(reference_updates)}"
    )


def main() -> None:
    build_and_execute(Path(".").resolve())


if __name__ == "__main__":
    main()
