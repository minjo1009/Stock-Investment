from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK745_INVENTORY = ROOT / "docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv"
TASK_REGISTRY = ROOT / "tasks/task_registry.csv"


@dataclass(frozen=True)
class SrcCanonicalRow:
    path: str
    src_area: str
    file_role: str
    task_id: str
    task_family: str
    registry_status: str
    registry_canonical_state: str
    workstream: str
    owner_team: str
    reviewer_team: str
    canonical_bucket: str
    next_action: str
    validation_hint: str


TASK_PATTERNS = [
    re.compile(r"task[_-]?(\d{2,4}[a-z]?)", re.IGNORECASE),
    re.compile(r"_task(\d{2,4}[a-z]?)", re.IGNORECASE),
    re.compile(r"_(\d{3,4}r?)\.py$", re.IGNORECASE),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def registry_map(path: Path = TASK_REGISTRY) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    output = {}
    for row in rows:
        task_id = (row.get("task_id") or "").strip()
        if task_id:
            output[task_id.lower()] = row
    return output


def extract_task_id(path: str) -> str:
    lower = path.lower()
    for pattern in TASK_PATTERNS:
        match = pattern.search(lower)
        if match:
            raw = match.group(1).upper()
            if raw.endswith("R"):
                raw = raw[:-1] + "R"
            return f"Task{raw}"
    return ""


def src_area(path: str) -> str:
    parts = path.split("/")
    if len(parts) < 2:
        return "src_root"
    if len(parts) == 2:
        return "src_root"
    return parts[1]


def task_family(task_id: str) -> str:
    if not task_id:
        return "package"
    numeric = re.sub(r"\D", "", task_id)
    if not numeric:
        return "task_unknown"
    task_num = int(numeric)
    if 727 <= task_num <= 742:
        return "current_brain_layer"
    if 617 <= task_num <= 646:
        return "content_backtest_microstructure_research"
    if 582 <= task_num <= 604:
        return "paper_execution_acceptance"
    if 480 <= task_num <= 581:
        return "continuation_microstructure_research"
    if 337 <= task_num <= 479:
        return "structural_breakout_research"
    if task_num < 337:
        return "early_historical_research"
    return "task_research"


def file_role(path: str, task_id: str) -> str:
    name = Path(path).name.lower()
    if path.endswith("__init__.py"):
        return "package_init"
    if task_id:
        if name.startswith("build_"):
            return "task_builder"
        if name.startswith("analysis_"):
            return "task_analysis"
        return "task_runtime_or_utility"
    if name in {"engine.py", "engine_full.py", "analysis.py", "metrics.py", "schemas.py", "policies.py"}:
        return "shared_engine_or_contract"
    if name.startswith("run_") or "runtime" in name:
        return "runtime_entrypoint_or_common"
    return "package_module"


def canonical_bucket(row: dict[str, str], task_id: str, role: str, family: str) -> str:
    suggested = row.get("suggested_class", "")
    path = row["path"]
    if "__pycache__" in path or path.endswith(".pyc"):
        return "local_generated_cache"
    if role in {"package_init", "shared_engine_or_contract"} and suggested == "canonical_candidate":
        return "canonical_package_candidate"
    if task_id:
        if family == "current_brain_layer":
            return "active_task_code_review"
        if family in {"content_backtest_microstructure_research", "paper_execution_acceptance"}:
            return "supporting_task_code_review"
        return "historical_task_code_review"
    if suggested == "canonical_candidate":
        return "canonical_package_candidate"
    return "owner_review_package_candidate"


def next_action(bucket: str) -> str:
    return {
        "canonical_package_candidate": "keep_package_path_and_attach_tests",
        "owner_review_package_candidate": "owner_decides_canonical_or_extract_contract",
        "active_task_code_review": "write_supersession_note_before_reuse",
        "supporting_task_code_review": "preserve_with_task_report_and_select_reusable_parts",
        "historical_task_code_review": "preserve_as_research_history_until_archive_plan",
        "local_generated_cache": "exclude_from_project_surface_no_delete_needed",
    }.get(bucket, "owner_review_required")


def validation_hint(bucket: str, area: str) -> str:
    if bucket == "canonical_package_candidate":
        return f"pytest tests/test_*{area}*.py when available"
    if bucket == "owner_review_package_candidate":
        return "owner review plus import/py_compile before promotion"
    if bucket == "local_generated_cache":
        return "gitignore/cache cleanup policy only"
    return "task report, manifest, and targeted test before reuse"


def build_rows() -> list[SrcCanonicalRow]:
    inventory = [row for row in read_csv(TASK745_INVENTORY) if row.get("top_level") == "src"]
    registry = registry_map()
    rows: list[SrcCanonicalRow] = []
    for row in inventory:
        path = row["path"]
        task_id = extract_task_id(path)
        reg = registry.get(task_id.lower(), {}) if task_id else {}
        family = task_family(task_id)
        role = file_role(path, task_id)
        bucket = canonical_bucket(row, task_id, role, family)
        area = src_area(path)
        rows.append(
            SrcCanonicalRow(
                path=path,
                src_area=area,
                file_role=role,
                task_id=task_id,
                task_family=family,
                registry_status=reg.get("status", ""),
                registry_canonical_state=reg.get("canonical_state", ""),
                workstream=row.get("workstream", ""),
                owner_team=row.get("owner_team", ""),
                reviewer_team=row.get("reviewer_team", ""),
                canonical_bucket=bucket,
                next_action=next_action(bucket),
                validation_hint=validation_hint(bucket, area),
            )
        )
    return rows


def write_csv(path: Path, rows: list[SrcCanonicalRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SrcCanonicalRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_summary(path: Path, rows: list[SrcCanonicalRow]) -> None:
    counters = {
        "canonical_bucket": Counter(row.canonical_bucket for row in rows),
        "src_area": Counter(row.src_area for row in rows),
        "workstream": Counter(row.workstream for row in rows),
        "task_family": Counter(row.task_family for row in rows),
        "owner_team": Counter(row.owner_team for row in rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Task746 Source Code Canonicalization Summary\n\n")
        handle.write("Task746 classifies `src/` only. It does not delete, move, promote, or change trading logic.\n\n")
        handle.write(f"Total src rows: {len(rows)}\n\n")
        for section, counter in counters.items():
            handle.write(f"## {section}\n\n")
            handle.write("| value | count |\n| --- | ---: |\n")
            for value, count in counter.most_common():
                handle.write(f"| {value or 'missing'} | {count} |\n")
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("docs/reports/task_746_src_canonicalization"))
    args = parser.parse_args()
    rows = build_rows()
    write_csv(args.out_dir / "task746_src_canonicalization_inventory.csv", rows)
    write_summary(args.out_dir / "task746_src_canonicalization_summary.md", rows)
    print(f"[Task746] src_rows={len(rows)} out={args.out_dir}")


if __name__ == "__main__":
    main()
