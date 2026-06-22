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
class TestValidationRow:
    path: str
    test_role: str
    task_id: str
    task_family: str
    workstream: str
    owner_team: str
    reviewer_team: str
    validation_lane: str
    speed_risk_lane: str
    authority_tag: str
    pass_implication: str
    pass_does_not_mean: str
    canonical_target_hint: str
    registry_status: str
    registry_canonical_state: str
    next_action: str


TASK_PATTERNS = [
    re.compile(r"task[_-]?(\d{2,4}[a-z]?)", re.IGNORECASE),
    re.compile(r"_task(\d{2,4}[a-z]?)", re.IGNORECASE),
    re.compile(r"_(\d{3,4}r?)\.py$", re.IGNORECASE),
]

EXTERNAL_RISK_TOKENS = {
    "kis",
    "broker",
    "order",
    "fill",
    "slack",
    "frontend",
    "mobile",
    "runtime",
    "supervisor",
    "alpaca",
    "microstructure",
}

CANONICAL_TARGETS = {
    "engine": "src/backtest/engine.py",
    "engine_full": "src/backtest/engine_full.py",
    "data_quality": "data/quality.py",
    "execution_policies": "src/execution",
    "risk_policies": "src/risk",
    "state": "src/state/store.py",
    "slack_client": "src/integration/slack_client.py",
    "kis": "src/integration/kis_client.py",
    "frontend": "frontend or src/ui/app.py",
    "registry": "tasks/task_registry.csv and governance scripts",
    "artifact": "scripts/task_artifact_manifest.py",
}


def path_parts(path: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", path.lower()) if part}


def has_token(path: str, token: str) -> bool:
    lower = path.lower()
    if len(token) <= 5:
        return token in path_parts(path)
    return token in lower


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def registry_map(path: Path = TASK_REGISTRY) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    output = {}
    for row in read_csv(path):
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


def test_role(path: str, task_id: str) -> str:
    name = Path(path).name.lower()
    if not name.startswith("test_") and "fixture" not in name:
        return "test_support_file"
    if "fixture" in name:
        return "fixture_support"
    if task_id:
        return "task_scoped_test"
    if name.startswith("test_"):
        return "package_or_contract_test"
    return "test_support_file"


def validation_lane(path: str, task_id: str, family: str, role: str) -> str:
    lower = path.lower()
    if role in {"fixture_support", "test_support_file"}:
        return "fixture_support_not_quality_gate"
    if any(has_token(path, token) for token in ["broker", "kis", "order", "fill"]):
        return "execution_broker_truth_validation"
    if any(has_token(path, token) for token in ["slack", "frontend", "mobile", "ui", "terminal"]):
        return "frontend_reporting_validation"
    if any(has_token(path, token) for token in ["artifact", "registry", "governance", "readiness", "contract"]):
        return "governance_validation"
    if any(has_token(path, token) for token in ["alpaca", "microstructure", "quote", "trade", "nbbo"]):
        return "microstructure_data_validation"
    if family == "current_brain_layer":
        return "active_brain_validation"
    if family in {"content_backtest_microstructure_research", "paper_execution_acceptance"}:
        return "supporting_task_validation"
    if task_id:
        return "historical_task_validation"
    return "canonical_package_validation_candidate"


def speed_risk_lane(path: str, validation: str) -> str:
    lower = path.lower()
    if validation == "fixture_support_not_quality_gate":
        return "fixture_support"
    if any(has_token(path, token) for token in EXTERNAL_RISK_TOKENS):
        return "integration_or_external_guard"
    if any(token in lower for token in ["full", "backfill", "replay", "walk_forward", "oos", "portfolio"]):
        return "slow_research_validation"
    if validation in {"active_brain_validation", "supporting_task_validation", "historical_task_validation"}:
        return "task_unit_or_research_validation"
    return "package_unit_candidate"


def canonical_target_hint(path: str, task_id: str) -> str:
    lower = path.lower()
    if task_id:
        if "build_" in lower:
            return f"src/backtest/build_{task_id.lower()}*.py"
        return f"task report/code for {task_id}"
    for token, target in CANONICAL_TARGETS.items():
        if token in lower:
            return target
    return "owner must map to src canonical candidate before promotion"


def next_action(validation: str, speed_risk: str) -> str:
    if validation == "fixture_support_not_quality_gate":
        return "keep_as_support_fixture_not_standalone_gate"
    if validation == "canonical_package_validation_candidate":
        return "map_to_task746_canonical_package_candidate"
    if validation == "active_brain_validation":
        return "tie_to_task727_742_supersession_and_output_contract"
    if validation == "supporting_task_validation":
        return "preserve_with_current_supporting_lane_report"
    if validation == "historical_task_validation":
        return "preserve_as_historical_regression_until_archive_plan"
    if speed_risk == "integration_or_external_guard":
        return "separate_from_fast_unit_gate_and_require_mock_or_fixture"
    return "owner_review_required"


def task_number(task_id: str) -> int:
    numeric = re.sub(r"\D", "", task_id)
    return int(numeric) if numeric else 0


def authority_tag(path: str, task_id: str, validation: str) -> str:
    number = task_number(task_id)
    if validation == "fixture_support_not_quality_gate":
        return "SUPPORT_ONLY"
    if validation == "canonical_package_validation_candidate":
        return "PACKAGE_HEALTH"
    if validation == "governance_validation":
        return "GOVERNANCE_HEALTH"
    if validation == "execution_broker_truth_validation":
        if 599 <= number <= 604 or "t603_6" in path.lower():
            return "ACCEPTANCE_EVIDENCE_REVIEW"
        return "EXECUTION_HEALTH"
    if validation == "microstructure_data_validation":
        return "DATA_HEALTH"
    if validation == "frontend_reporting_validation":
        return "REPORTING_HEALTH"
    if validation == "active_brain_validation":
        return "RESEARCH_ONLY"
    if validation in {"supporting_task_validation", "historical_task_validation"}:
        return "EVIDENCE_ONLY"
    return "OWNER_REVIEW"


def pass_implication(tag: str) -> str:
    return {
        "SUPPORT_ONLY": "support file is present and importable when applicable",
        "PACKAGE_HEALTH": "package-level regression was not detected for the mapped target",
        "GOVERNANCE_HEALTH": "governance contract or registry check did not detect a regression",
        "EXECUTION_HEALTH": "execution or broker-adjacent logic check did not detect a regression",
        "ACCEPTANCE_EVIDENCE_REVIEW": "acceptance evidence check produced reviewable evidence",
        "DATA_HEALTH": "data or microstructure contract check did not detect a regression",
        "REPORTING_HEALTH": "frontend or reporting contract check did not detect a regression",
        "RESEARCH_ONLY": "research or brain-layer regression was not detected",
        "EVIDENCE_ONLY": "historical task behavior remains reproducible enough for review",
        "OWNER_REVIEW": "owner must define what pass means before promotion",
    }.get(tag, "owner must define what pass means before promotion")


def pass_does_not_mean(tag: str) -> str:
    common = "strategy accepted; deployment ready; real capital allowed"
    return {
        "SUPPORT_ONLY": f"quality gate passed; {common}",
        "PACKAGE_HEALTH": common,
        "GOVERNANCE_HEALTH": common,
        "EXECUTION_HEALTH": f"broker truth complete; {common}",
        "ACCEPTANCE_EVIDENCE_REVIEW": f"acceptance granted; broker truth complete; {common}",
        "DATA_HEALTH": f"source coverage complete; {common}",
        "REPORTING_HEALTH": f"trading system healthy; {common}",
        "RESEARCH_ONLY": f"brain validated for trading; {common}",
        "EVIDENCE_ONLY": f"current system quality passed; {common}",
        "OWNER_REVIEW": common,
    }.get(tag, common)


def build_rows() -> list[TestValidationRow]:
    inventory = [row for row in read_csv(TASK745_INVENTORY) if row.get("top_level") == "tests"]
    registry = registry_map()
    rows: list[TestValidationRow] = []
    for row in inventory:
        path = row["path"]
        task_id = extract_task_id(path)
        reg = registry.get(task_id.lower(), {}) if task_id else {}
        family = task_family(task_id)
        role = test_role(path, task_id)
        validation = validation_lane(path, task_id, family, role)
        speed = speed_risk_lane(path, validation)
        tag = authority_tag(path, task_id, validation)
        rows.append(
            TestValidationRow(
                path=path,
                test_role=role,
                task_id=task_id,
                task_family=family,
                workstream=row.get("workstream", ""),
                owner_team=row.get("owner_team", ""),
                reviewer_team=row.get("reviewer_team", ""),
                validation_lane=validation,
                speed_risk_lane=speed,
                authority_tag=tag,
                pass_implication=pass_implication(tag),
                pass_does_not_mean=pass_does_not_mean(tag),
                canonical_target_hint=canonical_target_hint(path, task_id),
                registry_status=reg.get("status", ""),
                registry_canonical_state=reg.get("canonical_state", ""),
                next_action=next_action(validation, speed),
            )
        )
    return rows


def write_csv(path: Path, rows: list[TestValidationRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(TestValidationRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_summary(path: Path, rows: list[TestValidationRow]) -> None:
    counters = {
        "validation_lane": Counter(row.validation_lane for row in rows),
        "speed_risk_lane": Counter(row.speed_risk_lane for row in rows),
        "authority_tag": Counter(row.authority_tag for row in rows),
        "task_family": Counter(row.task_family for row in rows),
        "workstream": Counter(row.workstream for row in rows),
        "owner_team": Counter(row.owner_team for row in rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Task747 Test Validation Inventory Summary\n\n")
        handle.write("Task747 classifies formal `tests/` surface only. It does not delete, move, or rewrite tests.\n\n")
        handle.write(f"Total formal test rows: {len(rows)}\n\n")
        for section, counter in counters.items():
            handle.write(f"## {section}\n\n")
            handle.write("| value | count |\n| --- | ---: |\n")
            for value, count in counter.most_common():
                handle.write(f"| {value or 'missing'} | {count} |\n")
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("docs/reports/task_747_test_validation_canonicalization"))
    args = parser.parse_args()
    rows = build_rows()
    write_csv(args.out_dir / "task747_test_validation_inventory.csv", rows)
    write_summary(args.out_dir / "task747_test_validation_summary.md", rows)
    print(f"[Task747] test_rows={len(rows)} out={args.out_dir}")


if __name__ == "__main__":
    main()
