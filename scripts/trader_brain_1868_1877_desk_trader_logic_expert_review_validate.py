from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1868_1877_desk_trader_logic_expert_review"
REPORT = ROOT / "docs/reports/task_1868_1877_desk_trader_logic_expert_review/task_1868_1877_desk_trader_logic_expert_review.md"
DECISION = ROOT / "docs/reports/task_1868_1877_desk_trader_logic_expert_review/task_1868_1877_decision.csv"
AUTHORITY = "DIAGNOSTIC_DESK_TRADER_LOGIC_EXPERT_REVIEW_ONLY"


EXPECTED_COUNTS = {
    "task1868_expert_review.csv": 8,
    "task1869_professional_source_context.csv": 9,
    "task1871_7how_validation_matrix.csv": 7,
    "task1872_desk_specific_requirements.csv": 8,
    "task1873_implementation_acceptance_contract.csv": 6,
    "task1874_1877_next_task_plan.csv": 8,
    "task1877_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in EXPECTED_COUNTS:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1877_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision")


def validate_counts_authority() -> None:
    for name, expected in EXPECTED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
        for idx, row in enumerate(rows, start=2):
            fail_if(row.get("authority") != AUTHORITY, f"{name}:{idx} authority mismatch")


def validate_review_content() -> None:
    matrix = read_csv(OUT_DIR / "task1871_7how_validation_matrix.csv")
    fail_if(not any(row["expert_verdict"] == "critical" for row in matrix), "missing critical verdict")
    reqs = read_csv(OUT_DIR / "task1872_desk_specific_requirements.csv")
    desks = {row["desk"] for row in reqs}
    fail_if(desks != {"winner_compounder", "cyclical_beta", "speculative_event", "defensive_quality"}, f"unexpected desks {desks}")
    gates = {row["rule"] for row in read_csv(OUT_DIR / "task1873_implementation_acceptance_contract.csv")}
    for rule in ["no_global_trim", "sec_specificity", "earnings_block", "audit_only_outcomes"]:
        fail_if(rule not in gates, f"missing gate {rule}")
    closeout = read_csv(OUT_DIR / "task1877_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1877_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["strategy_acceptance"] != "NOT_ACCEPTED", "json strategy status changed")


def validate_report_text() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "direction is right",
        "SEC financing 신호",
        "winner",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_authority()
        validate_review_content()
        validate_report_text()
    except AssertionError as exc:
        print(f"[TASK1868_1877_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1868_1877_VALIDATE_OK] desk trader logic expert review is valid")


if __name__ == "__main__":
    main()
