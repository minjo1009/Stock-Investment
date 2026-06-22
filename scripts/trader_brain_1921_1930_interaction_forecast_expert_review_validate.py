from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1921_1930_interaction_forecast_expert_review"
REPORT = ROOT / "docs/reports/task_1921_1930_interaction_forecast_expert_review/task_1921_1930_interaction_forecast_expert_review.md"
DECISION = ROOT / "docs/reports/task_1921_1930_interaction_forecast_expert_review/task_1921_1930_decision.csv"
RAW_DIR = ROOT / "data/raw/task_1921_1930_interaction_forecast_expert_review"
AUTHORITY = "DIAGNOSTIC_INTERACTION_FORECAST_EXPERT_REVIEW_ONLY"

REQUIRED_FILES = {
    "task1921_existing_material_inventory.csv": 7,
    "task1922_additional_professional_sources.csv": 10,
    "task1923_gpt_expert_review.csv": 12,
    "task1924_direction_verdict.csv": 5,
    "task1925_interaction_primitive_contract.csv": 10,
    "task1926_l0_l5_upgrade_map.csv": 6,
    "task1927_data_gap_priority.csv": 7,
    "task1928_next_task_plan.csv": 10,
    "task1929_governance_gate.csv": 5,
    "task1930_closeout.csv": 1,
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
    for name in REQUIRED_FILES:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1930_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    for name, expected in REQUIRED_FILES.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
        for idx, row in enumerate(rows, start=2):
            fail_if(row.get("authority") != AUTHORITY, f"{name}:{idx} authority mismatch")


def validate_source_collection() -> None:
    sources = read_csv(OUT_DIR / "task1922_additional_professional_sources.csv")
    downloaded = [row for row in sources if row["downloaded"] == "1"]
    fail_if(len(downloaded) < 8, f"expected at least 8 downloaded sources got {len(downloaded)}")
    for row in downloaded:
        path = ROOT / row["local_raw_path"]
        fail_if(not path.exists(), f"downloaded source path missing: {path}")
        fail_if(path.stat().st_size <= 1000, f"downloaded source too small: {path}")
    fail_if(not RAW_DIR.exists(), "missing raw source directory")


def validate_direction_contract() -> None:
    verdicts = read_csv(OUT_DIR / "task1924_direction_verdict.csv")
    verdict_topics = {row["topic"] for row in verdicts}
    for topic in ["direction", "why_not_micro_l5", "where_to_build", "what_not_to_do", "first_replay_scope"]:
        fail_if(topic not in verdict_topics, f"missing verdict topic {topic}")
    primitives = {row["primitive_name"] for row in read_csv(OUT_DIR / "task1925_interaction_primitive_contract.csv")}
    for primitive in [
        "price_accepts_surprise",
        "financing_risk_overrides_growth",
        "quality_defends_volatility",
        "expectation_gap_expands_payoff",
    ]:
        fail_if(primitive not in primitives, f"missing primitive {primitive}")
    upgrades = {row["layer"]: row for row in read_csv(OUT_DIR / "task1926_l0_l5_upgrade_map.csv")}
    fail_if(upgrades["L3"]["priority"] != "highest", "L3 should be highest priority")
    fail_if(upgrades["L4"]["priority"] != "highest", "L4 should be highest priority")
    gaps = {row["gap_name"]: row for row in read_csv(OUT_DIR / "task1927_data_gap_priority.csv")}
    fail_if(gaps["event_window_abnormal_return_panel"]["priority_rank"] != "1", "event window should be priority 1")
    fail_if(gaps["sec_financing_terms_precision"]["priority_rank"] != "1", "SEC financing terms should be priority 1")


def validate_status_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1930_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1930_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["highest_leverage_next_work"] != "L3_L4_information_interaction_forecast_layer", "json closeout mismatch")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "interaction_forecast_direction_approved",
        "L3_L4_information_interaction_forecast_layer",
        "GPT expert roles are critique-only",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_source_collection()
        validate_direction_contract()
        validate_status_and_report()
    except AssertionError as exc:
        print(f"[TASK1921_1930_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1921_1930_VALIDATE_OK] interaction forecast expert review artifacts are valid")


if __name__ == "__main__":
    main()
