from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "project_efficiency_audit.md"


def sizeof_fmt(size: int | float) -> str:
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f}{unit}"
        value /= 1024.0
    return f"{value:.1f}PB"


def collect_file_rows(root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        rows.append(
            {
                "path": rel,
                "top_dir": rel.split("/", 1)[0],
                "suffix": path.suffix.lower() or "<none>",
                "size_bytes": int(stat.st_size),
            }
        )
    return pd.DataFrame(rows)


def summarize_by_top_dir(files: pd.DataFrame) -> pd.DataFrame:
    if files.empty:
        return pd.DataFrame()
    out = (
        files.groupby("top_dir", dropna=False)
        .agg(file_count=("path", "count"), size_bytes=("size_bytes", "sum"))
        .reset_index()
        .sort_values("size_bytes", ascending=False)
    )
    out["size_human"] = out["size_bytes"].map(sizeof_fmt)
    return out


def summarize_reports(root: Path) -> pd.DataFrame:
    reports = root / "docs" / "reports"
    rows: list[dict[str, object]] = []
    if not reports.exists():
        return pd.DataFrame()
    for directory in reports.iterdir():
        if not directory.is_dir():
            continue
        files = [p for p in directory.rglob("*") if p.is_file()]
        rows.append(
            {
                "report_dir": directory.name,
                "file_count": len(files),
                "size_bytes": sum(p.stat().st_size for p in files),
                "md_count": sum(1 for p in files if p.suffix.lower() == ".md"),
                "csv_count": sum(1 for p in files if p.suffix.lower() == ".csv"),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["size_human"] = out["size_bytes"].map(sizeof_fmt)
    return out.sort_values("size_bytes", ascending=False)


def summarize_backtest_files(root: Path) -> pd.DataFrame:
    backtest = root / "src" / "backtest"
    rows: list[dict[str, object]] = []
    if not backtest.exists():
        return pd.DataFrame()
    for path in backtest.glob("*.py"):
        name = path.name
        if name.startswith("build_task") or name.startswith("analysis_structural_breakout_task") or "_task" in name:
            kind = "task_specific"
        elif name.startswith("analysis_") or name.startswith("build_"):
            kind = "legacy_analysis_or_builder"
        else:
            kind = "core_or_shared"
        rows.append({"file": name, "kind": kind, "size_bytes": path.stat().st_size})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["size_human"] = out["size_bytes"].map(sizeof_fmt)
    return out.sort_values(["kind", "size_bytes"], ascending=[True, False])


def build_report(root: Path) -> str:
    files = collect_file_rows(root)
    top_dirs = summarize_by_top_dir(files)
    reports = summarize_reports(root)
    backtest = summarize_backtest_files(root)
    total_size = int(files["size_bytes"].sum()) if not files.empty else 0
    lines = [
        "# Project Efficiency Audit",
        "",
        "## Executive Summary",
        "",
        f"- Total tracked workspace files scanned: {len(files):,}",
        f"- Total scanned size: {sizeof_fmt(total_size)}",
        f"- docs/reports directories: {len(reports):,}",
        f"- src/backtest Python files: {len(backtest):,}",
        "",
        "The project is currently carrying research history, canonical infrastructure, generated CSV panels, markdown reports, and task-specific builders in the same working tree. The main inefficiency is not one bad file; it is the lack of lifecycle rules for artifacts and task code.",
        "",
        "## Main Inefficiencies",
        "",
        "1. Task-specific code is mixed with reusable engine code in `src/backtest`.",
        "2. Large generated CSV artifacts live under `docs/reports`, making reports both documentation and data storage.",
        "3. Each task creates a bespoke builder/analysis pair, so repeated report-writing, split-quality, leakage-audit, and grid-search logic is copied.",
        "4. Markdown reports are not tiered. There is no clear separation between executive summary, quant audit, and raw artifact manifest.",
        "5. Subagent handoff is mostly conversational. There is no stable local task packet format that says input/output/write-scope/validation.",
        "",
        "## Recommended Architecture",
        "",
        "### 1. Keep Canonical Code Small",
        "",
        "Create a narrow reusable layer:",
        "",
        "- `src/backtest/core/`: lifecycle, split, metric, cost-stress, leakage-audit utilities",
        "- `src/backtest/experiments/`: task-specific experiment specs only",
        "- `src/backtest/reports/`: report renderers shared by all tasks",
        "- `src/data/`: raw source collectors and source contracts",
        "",
        "Task files should become thin spec files, not full bespoke pipelines.",
        "",
        "### 2. Split Artifact Storage",
        "",
        "- Keep markdown and small decision CSVs in `docs/reports`.",
        "- Move large panels to `data/artifacts/<task_id>/` or `data/derived/<task_id>/`.",
        "- Keep only manifests and relative artifact links in reports.",
        "- Add an archive policy: old non-canonical task panels can be compressed or moved to `archive/reports` after a milestone.",
        "",
        "### 3. Standardize Report Shape",
        "",
        "Every new task report should have exactly these sections:",
        "",
        "- `Decision Summary`: pass/fail, status, next action",
        "- `Quant Expert Report`: exact metrics, leakage, OOS/split, failure decomposition",
        "- `No-Background Decision-Maker Report`: simple implication and risk",
        "- `Artifact Manifest`: generated files, source inputs, row counts, hashes if applicable",
        "",
        "### 4. Standardize Subagent Packets",
        "",
        "Use one handoff template per delegated task:",
        "",
        "- Objective",
        "- Read scope",
        "- Write scope",
        "- Inputs",
        "- Required outputs",
        "- Forbidden actions",
        "- Validation command",
        "",
        "This prevents parallel agents from duplicating exploration or writing over each other.",
        "",
        "### 5. Introduce Task Registry",
        "",
        "Create a machine-readable registry:",
        "",
        "- `tasks/task_registry.csv`: task_id, status, canonical_flag, parent_task, key_report, key_artifacts, validation_command",
        "- Mark old tasks as `archived`, current canonical tasks as `active`, and failed branches as `superseded`.",
        "",
        "## Size Summary By Top Directory",
        "",
        csv_block(top_dirs.head(20)),
        "",
        "## Largest Report Directories",
        "",
        csv_block(reports.head(30)),
        "",
        "## Backtest Code Classification",
        "",
        csv_block(backtest.groupby("kind", dropna=False).agg(file_count=("file", "count"), size_bytes=("size_bytes", "sum")).reset_index().assign(size_human=lambda df: df["size_bytes"].map(sizeof_fmt))),
        "",
        "## Immediate Low-Risk Actions",
        "",
        "1. Add a report/artifact manifest standard and apply it from the next task onward.",
        "2. Add `tasks/task_registry.csv` before moving files.",
        "3. Extract shared metrics/leakage/cost-stress helpers from recent Task489-493 code.",
        "4. Move only large generated panels first; do not delete historical reports.",
        "5. Keep Task492/493/495 as current canonical microstructure path; mark older reconstruction/recovery tasks as historical.",
        "",
        "## Do Not Do Yet",
        "",
        "- Do not bulk-delete `docs/reports`.",
        "- Do not rename task IDs without a registry.",
        "- Do not move raw data until collectors and report references are updated.",
        "- Do not refactor old task files before extracting current canonical utilities.",
    ]
    return "\n".join(lines)


def csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = build_report(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"[PROJECT_EFFICIENCY_AUDIT] wrote={args.out}")


if __name__ == "__main__":
    main()
