from __future__ import annotations

import argparse
import csv
from pathlib import Path


SCAN_ROOTS = (".github", "src", "tests", "scripts", "tasks", "docs")
TEXT_SUFFIXES = {".csv", ".md", ".py", ".ps1", ".txt", ".yml", ".yaml", ".toml", ".json"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _iter_reference_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if root / "docs" / "reports" in path.parents:
                continue
            if path.name in {"artifact_migration_plan.csv", "artifact_migration_result.csv"}:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files.append(path)
    return files


def _contains(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def _references(reference_files: list[Path], root: Path, needle: str) -> list[str]:
    refs: list[str] = []
    for path in reference_files:
        if _contains(path, needle):
            refs.append(path.relative_to(root).as_posix())
    return refs


def build_plan(
    root: Path,
    *,
    archive_registry_path: Path | None = None,
    out: Path | None = None,
) -> list[dict[str, object]]:
    archive_registry_path = archive_registry_path or root / "tasks" / "archive_candidate_registry.csv"
    out = out or root / "docs" / "artifact_migration_plan.csv"
    registry_rows = _read_csv(archive_registry_path)
    reference_files = _iter_reference_files(root)

    rows: list[dict[str, object]] = []
    for registry_row in registry_rows:
        report_dir = registry_row.get("report_dir", "")
        archive_state = registry_row.get("archive_state", "")
        manifest_rel = registry_row.get("manifest_path", "")
        manifest = root / manifest_rel
        manifest_rows = _read_csv(manifest)
        directory_rel = f"docs/reports/{report_dir}"
        directory_refs = _references(reference_files, root, directory_rel)

        for manifest_row in manifest_rows:
            relative_path = manifest_row.get("relative_path", "")
            artifact_class = manifest_row.get("artifact_class", "")
            size_bytes = int(manifest_row.get("size_bytes", "0") or 0)
            source_rel = f"{directory_rel}/{relative_path}"
            target_rel = f"data/artifacts/{report_dir}/{relative_path}"
            file_refs = _references(reference_files, root, source_rel)
            reference_paths = sorted(set(file_refs))

            if archive_state != "archive_candidate":
                action = "keep_not_archive_candidate"
            elif artifact_class not in {"large_panel"}:
                action = "keep_small_or_report_artifact"
            elif reference_paths:
                action = "skip_referenced"
            else:
                action = "move_to_data_artifacts"

            rows.append(
                {
                    "report_dir": report_dir,
                    "relative_path": relative_path,
                    "source_path": source_rel,
                    "target_path": target_rel,
                    "artifact_class": artifact_class,
                    "size_bytes": size_bytes,
                    "archive_state": archive_state,
                    "migration_action": action,
                    "reference_count": len(reference_paths),
                    "references": "|".join(reference_paths),
                    "directory_reference_count": len(directory_refs),
                    "directory_references": "|".join(sorted(set(directory_refs))),
                }
            )

    fieldnames = [
        "report_dir",
        "relative_path",
        "source_path",
        "target_path",
        "artifact_class",
        "size_bytes",
        "archive_state",
        "migration_action",
        "reference_count",
        "references",
        "directory_reference_count",
        "directory_references",
    ]
    _write_csv(out, rows, fieldnames)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--archive-registry", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    rows = build_plan(root, archive_registry_path=args.archive_registry, out=args.out)
    movable = [row for row in rows if row["migration_action"] == "move_to_data_artifacts"]
    movable_bytes = sum(int(row["size_bytes"]) for row in movable)
    print(f"[ARTIFACT_MIGRATION_PLAN] rows={len(rows)} movable={len(movable)} movable_bytes={movable_bytes}")


if __name__ == "__main__":
    main()
