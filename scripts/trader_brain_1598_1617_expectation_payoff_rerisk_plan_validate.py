from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1598_1617_expectation_payoff_rerisk_plan"
REPORT = ROOT / "docs/reports/task_1598_1617_expectation_payoff_rerisk_plan/task_1598_1617_expectation_payoff_rerisk_plan.md"
DECISION = ROOT / "docs/reports/task_1598_1617_expectation_payoff_rerisk_plan/task_1598_1617_decision.csv"

REQUIRED = [
    "task1598_expert_review_packet.csv",
    "task1599_learning_source_map.csv",
    "task1600_1606_bridge_schema.csv",
    "task1598_1617_implementation_plan.csv",
    "task1617_acceptance_gate.csv",
    "task1617_closeout.csv",
    "task1617_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (OUT_DIR / name).exists():
            errors.append(f"missing artifact: {name}")
    if not REPORT.exists():
        errors.append(f"missing report: {REPORT}")
    if not DECISION.exists():
        errors.append(f"missing decision: {DECISION}")
    if errors:
        for error in errors:
            print(f"[TASK1598_1617_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1598_expert_review_packet.csv")
    sources = read_csv(OUT_DIR / "task1599_learning_source_map.csv")
    schemas = read_csv(OUT_DIR / "task1600_1606_bridge_schema.csv")
    plan = read_csv(OUT_DIR / "task1598_1617_implementation_plan.csv")
    gate = read_csv(OUT_DIR / "task1617_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1617_closeout.csv")

    if len(experts) < 10:
        errors.append("expected at least ten expert review rows")
    source_names = {row["source_name"] for row in sources}
    for required in {"SEC Form 8-K", "MacKinlay Event Studies", "AQR Value and Momentum Everywhere", "Fama-French Data Library", "ALFRED", "Task1578-1597 Audit"}:
        if required not in source_names:
            errors.append(f"missing learning source: {required}")
    table_names = {row["table_name"] for row in schemas}
    for required in {"tradable_surprise", "payoff_window", "absorption_quality", "rerisk_state"}:
        if required not in table_names:
            errors.append(f"missing schema table: {required}")
    field_names = {row["field_name"] for row in schemas}
    for required in {"tradable_surprise_score", "payoff_window_bucket", "abnormal_return_window", "rerisk_allowed"}:
        if required not in field_names:
            errors.append(f"missing schema field: {required}")
    task_ids = {row["task_id"] for row in plan}
    for required in {f"Task{idx}" for idx in range(1598, 1618)}:
        if required not in task_ids:
            errors.append(f"missing plan task: {required}")
    if not any(row["title"] == "Negative Fixture Suite" for row in plan):
        errors.append("missing negative fixture suite")
    if not any(row["title"] == "Preregistered Replay Family" for row in plan):
        errors.append("missing preregistered replay family")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    if closeout[0]["primary_fix"] != "expectation_to_payoff_to_rerisk_bridge":
        errors.append("closeout primary fix mismatch")
    report_text = REPORT.read_text(encoding="utf-8")
    if "기대 대비 충격 -> payoff 기간/크기 -> 다시 키울지" not in report_text:
        errors.append("report missing plain-language bridge explanation")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1598_1617_ERROR] {error}")
        return 1
    print("[TASK1598_1617_OK] expectation-payoff-re-risk plan artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
