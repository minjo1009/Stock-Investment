from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1828_1847_targeted_data_plan"
REPORT = ROOT / "docs/reports/task_1828_1847_targeted_data_plan/task_1828_1847_targeted_data_plan.md"
DECISION = ROOT / "docs/reports/task_1828_1847_targeted_data_plan/task_1828_1847_decision.csv"
AUTHORITY = "DIAGNOSTIC_TARGETED_DATA_PLAN_ONLY"


EXPECTED_COUNTS = {
    "task1828_sleeve_attribution_decision.csv": 8,
    "task1829_expert_review.csv": 7,
    "task1830_professional_source_context.csv": 8,
    "task1831_targeted_data_priority.csv": 4,
    "task1832_l0_l5_field_contract.csv": 10,
    "task1833_validation_contract.csv": 7,
    "task1834_1847_task_plan.csv": 20,
    "task1846_acceptance_gate.csv": 1,
    "task1847_closeout.csv": 1,
}

EXPECTED_PRIORITY = [
    ("1", "rates_liquidity"),
    ("2", "earnings_revision"),
    ("3", "financing_dilution"),
    ("4", "sector_breadth"),
]

FORBIDDEN_REPLAY_TOKENS = ("replay_trades", "replay_equity", "replay_metrics", "backtest")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def validate_counts() -> None:
    for name, expected in EXPECTED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        assert_equal(len(rows), expected, f"{name} row_count")
    if not (OUT_DIR / "artifact_manifest.csv").exists():
        raise AssertionError("missing artifact manifest")
    if not (OUT_DIR / "task1847_closeout.json").exists():
        raise AssertionError("missing closeout json")
    if not REPORT.exists():
        raise AssertionError("missing report")
    if not DECISION.exists():
        raise AssertionError("missing decision csv")


def validate_priority() -> None:
    rows = read_csv(OUT_DIR / "task1831_targeted_data_priority.csv")
    actual = [(row["priority_rank"], row["data_family"]) for row in rows]
    assert_equal(actual, EXPECTED_PRIORITY, "targeted data priority order")


def validate_authority_and_leakage() -> None:
    for name in EXPECTED_COUNTS:
        rows = read_csv(OUT_DIR / name)
        for idx, row in enumerate(rows, start=2):
            if row.get("authority") != AUTHORITY:
                raise AssertionError(f"{name}:{idx} unexpected authority {row.get('authority')!r}")

    attribution = read_csv(OUT_DIR / "task1828_sleeve_attribution_decision.csv")
    for idx, row in enumerate(attribution, start=2):
        assert_equal(row["assignment_uses_future_outcome"], "0", f"attribution row {idx} future assignment")
        assert_equal(row["outcome_used_for_assignment"], "0", f"attribution row {idx} outcome assignment")
        assert_equal(row["outcome_used_for_audit_only"], "1", f"attribution row {idx} audit only")


def validate_no_replay_outputs() -> None:
    for path in OUT_DIR.iterdir():
        lower_name = path.name.lower()
        if any(token in lower_name for token in FORBIDDEN_REPLAY_TOKENS):
            raise AssertionError(f"unexpected replay/backtest artifact in plan-only task: {path.name}")


def validate_closeout_status() -> None:
    closeout = read_csv(OUT_DIR / "task1847_closeout.csv")
    row = closeout[0]
    assert_equal(row["strategy_acceptance"], "NOT_ACCEPTED", "strategy status")
    assert_equal(row["deployment_readiness"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status")
    assert_equal(row["real_capital"], "FORBIDDEN", "real capital status")
    payload = json.loads((OUT_DIR / "task1847_closeout.json").read_text(encoding="utf-8"))
    assert_equal(payload["priority_1"], "rates_liquidity", "json priority 1")
    assert_equal(payload["priority_2"], "earnings_revision_vendor_gate", "json priority 2")
    assert_equal(payload["priority_3"], "financing_dilution", "json priority 3")
    assert_equal(payload["priority_4"], "sector_breadth_lightweight", "json priority 4")


def validate_report_text() -> None:
    text = REPORT.read_text(encoding="utf-8")
    required = [
        "Do not go back to micro sizing.",
        "No replay executed.",
        "ALFRED",
        "FRED DGS10",
        "FINRA Margin Statistics",
        "Nasdaq Data Link Zacks Analyst Revisions",
        "SEC EDGAR APIs",
        "Kenneth French Data Library",
        "AQR Quality Minus Junk",
        "Test results do not modify strategy acceptance status.",
    ]
    for phrase in required:
        if phrase not in text:
            raise AssertionError(f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_counts()
        validate_priority()
        validate_authority_and_leakage()
        validate_no_replay_outputs()
        validate_closeout_status()
        validate_report_text()
    except AssertionError as exc:
        print(f"[TASK1828_1847_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1828_1847_VALIDATE_OK] targeted data plan artifacts are valid")


if __name__ == "__main__":
    main()
