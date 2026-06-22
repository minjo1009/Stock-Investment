from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_CANONICAL_TASKS = {
    "task_489_broad_regime_cell_portfolio",
    "task_490r_firm_grade_intraday_continuation_validation",
    "task_491_intraday_continuation_grid_development",
    "task_492_microstructure_source_collection",
    "task_493_microstructure_enhanced_continuation_grid",
    "task_494_microstructure_goal_synthesis",
    "task_495_microstructure_live_source_readiness",
}


def report_dirs(root: Path) -> list[dict[str, object]]:
    reports = root / "docs" / "reports"
    rows: list[dict[str, object]] = []
    for directory in reports.iterdir() if reports.exists() else []:
        if not directory.is_dir():
            continue
        files = [path for path in directory.rglob("*") if path.is_file()]
        size = sum(path.stat().st_size for path in files)
        name = directory.name
        if name in DEFAULT_CANONICAL_TASKS:
            state = "canonical_or_active"
            action = "keep_in_place"
        elif size >= 10 * 1024 * 1024:
            state = "archive_candidate"
            action = "manifest_then_move_large_panels_to_data_artifacts"
        else:
            state = "historical_keep"
            action = "keep_until_full_registry_backfill"
        rows.append(
            {
                "report_dir": name,
                "archive_state": state,
                "recommended_action": action,
                "file_count": len(files),
                "size_bytes": size,
                "manifest_path": f"docs/reports/{name}/artifact_manifest.csv",
            }
        )
    return sorted(rows, key=lambda row: int(row["size_bytes"]), reverse=True)


def write_registry(root: Path, out: Path) -> None:
    rows = report_dirs(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["report_dir", "archive_state", "recommended_action", "file_count", "size_bytes", "manifest_path"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("tasks/archive_candidate_registry.csv"))
    args = parser.parse_args()
    write_registry(args.root, args.out)
    print(f"[ARCHIVE_CANDIDATE_REGISTRY] wrote={args.out}")


if __name__ == "__main__":
    main()
