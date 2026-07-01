from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from pathlib import Path

from ops_common import ROOT, ensure_parent, rel


ARTIFACT_ROOT = ROOT / "data" / "artifacts"
REPORT_DIR = ROOT / "docs" / "reports" / "task_4110_l0_artifact_retention_cleanup"
DEFAULT_INVENTORY = REPORT_DIR / "l0_artifact_retention_inventory.csv"
DEFAULT_DELETED = REPORT_DIR / "deleted_l0_artifacts.csv"

CANONICAL_KEEP = {
    "l0_bar_daily_full_backfill",
    "l0_bar_daily_full_backfill_shard_0",
    "l0_bar_daily_full_backfill_shard_1",
    "l0_bar_daily_full_backfill_shard_2",
    "l0_bar_daily_full_backfill_shard_3",
    "l0_bar_full_backfill",
    "l0_collection_status",
    "l0_news_background_queue",
    "l0_news_full_backfill",
    "l0_public_context_news",
    "l0_public_context_news_backfill",
    "l0_public_industry_dive_news_backfill",
    "l0_public_market_macro_news",
    "l0_public_market_macro_news_backfill",
    "l0_public_newswire",
    "l0_public_newswire_backfill",
    "l0_reference_snapshot",
    "l0_source_acquisition",
    "microstructure",
    "microstructure_backfill_queue",
    "microstructure_backfill_queue_15m",
}

DELETE_TOKENS = (
    "_smoke",
    "smoke_",
    "_probe",
    "probe_",
    "capability_probe",
    "l2_smoke",
    "token_smoke",
)


@dataclass(frozen=True)
class Finding:
    path: str
    files: int
    bytes: int
    action: str
    reason: str


def folder_stats(path: Path) -> tuple[int, int]:
    files = 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            files += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return files, total


def is_l0_artifact_dir(name: str) -> bool:
    return (
        name.startswith("l0_")
        or name.startswith("ind_dive")
        or name == "sec_live_retry_manual"
    )


def classify(path: Path) -> Finding:
    name = path.name
    files, total = folder_stats(path)
    if name in CANONICAL_KEEP:
        return Finding(rel(path), files, total, "KEEP_CANONICAL", "current L0 collection/status/source artifact")
    if not is_l0_artifact_dir(name):
        return Finding(rel(path), files, total, "IGNORE_NON_L0", "outside L0 artifact cleanup scope")
    if name == "sec_live_retry_manual":
        return Finding(rel(path), files, total, "DELETE_OBSOLETE_L0_ARTIFACT", "manual SEC retry scratch artifact")
    if any(token in name for token in DELETE_TOKENS):
        return Finding(rel(path), files, total, "DELETE_OBSOLETE_L0_ARTIFACT", "smoke/probe/L2 smoke artifact superseded by canonical L0 outputs")
    return Finding(rel(path), files, total, "KEEP_L0_NONCANONICAL_REVIEW", "L0 artifact not deleted without explicit smoke/probe marker")


def scan() -> list[Finding]:
    if not ARTIFACT_ROOT.exists():
        return []
    return [classify(path) for path in sorted(ARTIFACT_ROOT.iterdir()) if path.is_dir()]


def write_csv(path: Path, rows: list[Finding]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(Finding.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def delete_rows(rows: list[Finding]) -> list[Finding]:
    deleted: list[Finding] = []
    artifact_root = ARTIFACT_ROOT.resolve()
    for row in rows:
        if row.action != "DELETE_OBSOLETE_L0_ARTIFACT":
            continue
        target = (ROOT / row.path).resolve()
        if artifact_root not in target.parents:
            raise RuntimeError(f"refusing to delete outside data/artifacts: {target}")
        if target.name in CANONICAL_KEEP:
            raise RuntimeError(f"refusing to delete canonical artifact: {target}")
        if target.exists():
            shutil.rmtree(target)
            deleted.append(row)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--deleted-output", default=str(DEFAULT_DELETED))
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    rows = scan()
    write_csv(ROOT / args.inventory, rows)
    print(f"PASS inventory: {args.inventory}")
    print(f"PASS artifact_dirs_seen: {len(rows)}")
    for action in sorted({row.action for row in rows}):
        subset = [row for row in rows if row.action == action]
        print(f"PASS {action}: {len(subset)} dirs, {sum(row.files for row in subset)} files, {sum(row.bytes for row in subset)} bytes")
    if args.delete:
        deleted = delete_rows(rows)
        write_csv(ROOT / args.deleted_output, deleted)
        print(f"PASS deleted_dirs: {len(deleted)}")
        print(f"PASS deleted_files: {sum(row.files for row in deleted)}")
        print(f"PASS deleted_bytes: {sum(row.bytes for row in deleted)}")
        print(f"PASS deleted_manifest: {args.deleted_output}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
