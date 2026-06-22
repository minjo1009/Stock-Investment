from __future__ import annotations

import argparse
import csv
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SurfaceRow:
    path: str
    git_status: str
    top_level: str
    extension: str
    size_bytes: int
    workstream: str
    surface_type: str
    suggested_class: str
    owner_team: str
    reviewer_team: str
    next_action: str


WORKSTREAMS = [
    ("brain", ["semantic", "context", "source_packet", "economic", "relation", "interaction", "task727", "task728", "task729", "task730", "task731", "task732", "task733", "task734", "task735", "task736", "task737", "task738", "task739", "task740", "task741", "task742"]),
    ("microstructure_data", ["microstructure", "alpaca", "quote", "trade", "nbbo", "depth", "luld"]),
    ("paper_execution", ["kis", "broker", "order", "fill", "execution", "paper", "runtime", "reconciliation"]),
    ("frontend_reporting", ["frontend", "ui", "slack", "eod", "terminal", "catalog"]),
    ("backtest_replay", ["backtest", "replay", "oos", "slippage", "cost", "portfolio", "walk_forward"]),
    ("regime_intraday", ["regime", "intraday", "vwap", "continuation", "entry", "breakout"]),
    ("governance", ["registry", "governance", "artifact", "manifest", "operating", "ownership", "contract", "architecture"]),
]


OWNER_BY_WORKSTREAM = {
    "brain": ("Research Governance", "Backtest & Simulation Infra"),
    "microstructure_data": ("Data & Market Microstructure", "Research Governance"),
    "paper_execution": ("Execution & Risk", "Data & Market Microstructure"),
    "frontend_reporting": ("Frontend/UI", "Research Governance"),
    "backtest_replay": ("Backtest & Simulation Infra", "Research Governance"),
    "regime_intraday": ("Regime Research", "Backtest & Simulation Infra"),
    "governance": ("Research Governance", "Relevant owner team"),
    "general": ("Research Governance", "Relevant owner team"),
}


def build_inventory(root: Path = ROOT) -> list[SurfaceRow]:
    status_map = git_status_map(root)
    paths = set(status_map) | git_tracked_files(root)
    rows = []
    for rel in sorted(paths):
        path = root / rel
        status = status_map.get(rel, "tracked_or_ignored")
        top = rel.split("/", 1)[0]
        extension = path.suffix.lower() if path.exists() else ""
        size = path.stat().st_size if path.exists() else 0
        workstream = classify_workstream(rel)
        surface_type = classify_surface_type(rel, extension)
        suggested = classify_suggested(rel, status, extension, size, surface_type)
        owner, reviewer = OWNER_BY_WORKSTREAM.get(workstream, OWNER_BY_WORKSTREAM["general"])
        rows.append(
            SurfaceRow(
                path=rel,
                git_status=status,
                top_level=top,
                extension=extension,
                size_bytes=size,
                workstream=workstream,
                surface_type=surface_type,
                suggested_class=suggested,
                owner_team=owner,
                reviewer_team=reviewer,
                next_action=next_action_for(suggested, surface_type),
            )
        )
    return rows


def git_status_map(root: Path) -> dict[str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    mapping = {}
    for item in result.stdout.decode("utf-8", errors="replace").split("\0"):
        if not item:
            continue
        status = item[:2].strip() or item[:2]
        path = item[3:].replace("\\", "/")
        mapping[path] = status
    return mapping


def git_tracked_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return {line.replace("\\", "/") for line in result.stdout.decode("utf-8", errors="replace").split("\0") if line.strip()}


def classify_workstream(path: str) -> str:
    lower = path.lower()
    parts = set(re.split(r"[^a-z0-9]+", lower))
    for name, tokens in WORKSTREAMS:
        for token in tokens:
            if len(token) <= 3:
                if token in parts:
                    return name
            elif token in lower:
                return name
    return "general"


def classify_surface_type(path: str, extension: str) -> str:
    lower = path.lower()
    if lower.startswith("src/"):
        if "/build_task" in lower or "/analysis_" in lower or "task_" in lower:
            return "task_scoped_code"
        return "package_code"
    if lower.startswith("tests/"):
        if "test_task" in lower or "test_analysis" in lower:
            return "task_scoped_test"
        return "package_test"
    if lower.startswith("scripts/"):
        return "script"
    if lower.startswith("docs/reports/"):
        return "task_report_artifact"
    if lower.startswith("docs/contracts/"):
        return "contract"
    if lower.startswith("docs/architecture/"):
        return "architecture_doc"
    if lower.startswith("docs/operating_system/") or lower.startswith("docs/ownership/"):
        return "operating_doc"
    if lower.startswith("skills/"):
        return "skill"
    if lower.startswith("tasks/"):
        return "task_registry_or_note"
    if extension in {".db", ".sqlite", ".jsonl", ".parquet"}:
        return "large_or_runtime_artifact"
    return "other"


def classify_suggested(path: str, status: str, extension: str, size: int, surface_type: str) -> str:
    lower = path.lower()
    if surface_type == "large_or_runtime_artifact" or lower.startswith("data/raw/") or lower.startswith("data/artifacts/"):
        return "local_only"
    if surface_type in {"contract", "architecture_doc", "operating_doc", "skill"}:
        return "canonical_candidate"
    if surface_type in {"task_report_artifact"}:
        if extension == ".md" or "decision" in lower or "pass_fail" in lower or "artifact_manifest" in lower:
            return "summary_commit_candidate"
        return "local_only"
    if surface_type in {"task_scoped_code", "task_scoped_test"}:
        return "needs_owner_review"
    if surface_type in {"package_code", "package_test", "script", "task_registry_or_note"}:
        if status == "??":
            return "needs_owner_review"
        return "canonical_candidate"
    if size > 5 * 1024 * 1024:
        return "local_only"
    return "needs_owner_review"


def next_action_for(suggested: str, surface_type: str) -> str:
    if suggested == "canonical_candidate":
        return "review_for_commit_and_validation"
    if suggested == "summary_commit_candidate":
        return "keep_summary_manifest_only"
    if suggested == "local_only":
        return "exclude_or_manifest_only_no_delete"
    if surface_type in {"task_scoped_code", "task_scoped_test"}:
        return "classify_canonical_experiment_archive"
    return "owner_review_required"


def write_csv(path: Path, rows: list[SurfaceRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()) if rows else list(SurfaceRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def summarize(rows: list[SurfaceRow]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for key in ["top_level", "workstream", "surface_type", "suggested_class", "git_status"]:
        counts: dict[str, int] = {}
        for row in rows:
            value = str(getattr(row, key))
            counts[value] = counts.get(value, 0) + 1
        output[key] = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return output


def write_summary(path: Path, summary: dict[str, dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Project Surface Inventory Summary\n\n")
        for section, counts in summary.items():
            handle.write(f"## {section}\n\n")
            handle.write("| value | count |\n| --- | --- |\n")
            for value, count in counts.items():
                handle.write(f"| {value} | {count} |\n")
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("docs/reports/task_745_project_surface_inventory"))
    args = parser.parse_args()
    rows = build_inventory()
    write_csv(args.out_dir / "task745_project_surface_inventory.csv", rows)
    write_summary(args.out_dir / "task745_project_surface_inventory_summary.md", summarize(rows))
    print(f"[Task745] rows={len(rows)} out={args.out_dir}")


if __name__ == "__main__":
    main()
