from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1468_1487_complete_implementation_contract"
REPORT = ROOT / "docs/reports/task_1468_1487_complete_implementation_contract/task_1468_1487_complete_implementation_contract.md"
RAW_LEDGER = ROOT / "data/raw/task_1468_1487_complete_implementation_context/source_download_ledger.csv"

REQUIRED = [
    "task1468_source_catalog.csv",
    "task1469_expert_complete_implementation_definition.csv",
    "task1470_completion_criteria.csv",
    "task1471_primitive_contract.csv",
    "task1472_sector_rulebook.csv",
    "task1473_validation_contract.csv",
    "task1474_1487_implementation_plan.csv",
    "task1487_acceptance_gate.csv",
    "task1487_closeout.json",
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
    if not RAW_LEDGER.exists():
        errors.append(f"missing raw source ledger: {RAW_LEDGER}")
    if errors:
        for error in errors:
            print(f"[TASK1468_1487_ERROR] {error}")
        return 1

    sources = read_csv(OUT_DIR / "task1468_source_catalog.csv")
    experts = read_csv(OUT_DIR / "task1469_expert_complete_implementation_definition.csv")
    criteria = read_csv(OUT_DIR / "task1470_completion_criteria.csv")
    primitives = read_csv(OUT_DIR / "task1471_primitive_contract.csv")
    sectors = read_csv(OUT_DIR / "task1472_sector_rulebook.csv")
    validations = read_csv(OUT_DIR / "task1473_validation_contract.csv")
    plan = read_csv(OUT_DIR / "task1474_1487_implementation_plan.csv")
    gate = read_csv(OUT_DIR / "task1487_acceptance_gate.csv")

    if len(sources) != 10:
        errors.append(f"expected 10 source rows, found {len(sources)}")
    if any(row["download_state"] != "downloaded" for row in sources):
        errors.append("not all source context rows downloaded")
    if len(experts) < 10:
        errors.append("expert definition rows too few")
    required_layers = {"L1", "L2", "L3", "L4", "L5", "validation", "report", "artifact"}
    layers = {row["layer"] for row in criteria}
    if not required_layers <= layers:
        errors.append(f"completion criteria missing layers: {sorted(required_layers - layers)}")
    primitive_names = {row["primitive_name"] for row in primitives}
    for required in ["positive", "survival", "financing", "dilution", "true_surprise", "persistence", "conditional_score", "displacement"]:
        if required not in primitive_names:
            errors.append(f"missing primitive: {required}")
    sector_names = {row["sector"] for row in sectors}
    for required in ["semiconductor", "ai_software", "space", "power_grid", "biotech", "industrial"]:
        if required not in sector_names:
            errors.append(f"missing sector rule: {required}")
    test_names = {row["test_name"] for row in validations}
    for required in ["source_time_test", "no_future_leakage_test", "audit_only_outcome_test", "golden_fixture_test", "negative_fixture_test", "preregistration_hash_test"]:
        if required not in test_names:
            errors.append(f"missing validation contract: {required}")
    if len(plan) != 14:
        errors.append(f"expected 14 implementation plan rows, found {len(plan)}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    report_text = REPORT.read_text(encoding="utf-8")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")
    if "완벽 구현은 점수식 튜닝이 아니다" not in report_text:
        errors.append("report missing no-background implementation definition")

    if errors:
        for error in errors:
            print(f"[TASK1468_1487_ERROR] {error}")
        return 1
    print("[TASK1468_1487_OK] complete implementation contract artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
