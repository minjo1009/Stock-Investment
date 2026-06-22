from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1981_1990_current_2026_calibration_pack"
REPORT = ROOT / "docs/reports/task_1981_1990_current_2026_calibration_pack/task_1981_1990_current_2026_calibration_pack.md"
DECISION = ROOT / "docs/reports/task_1981_1990_current_2026_calibration_pack/task_1981_1990_decision.csv"
OPERATING_STATE = ROOT / "docs/operating_system/project_operating_state.md"
REGISTRY = ROOT / "tasks/task_registry.csv"
AUTHORITY = "DESIGN_CALIBRATION_ONLY_NOT_BACKTEST_ASSIGNMENT"

REQUIRED_COUNTS = {
    "task1981_current_2026_source_catalog.csv": 13,
    "task1982_current_source_download_manifest.csv": 13,
    "task1983_design_backtest_boundary.csv": 5,
    "task1984_l0_l5_current_calibration_map.csv": 6,
    "task1985_winner_acceleration_requirements.csv": 7,
    "task1986_expert_review_matrix.csv": 6,
    "task1987_task1991_2000_backlog.csv": 10,
    "task1990_acceptance_gate.csv": 1,
    "task1990_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files_counts_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        path = OUT_DIR / name
        fail_if(not path.exists(), f"missing artifact: {name}")
        rows = read_csv(path)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
        for idx, row in enumerate(rows, start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{name}:{idx} outcome assignment")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1990_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_source_boundary() -> None:
    catalog = read_csv(OUT_DIR / "task1981_current_2026_source_catalog.csv")
    fail_if(sum(1 for row in catalog if row["institution"] == "Federal Reserve") < 2, "Fed sources missing")
    fail_if(sum(1 for row in catalog if row["market_axis"].startswith("ai")) < 2, "AI design sources too thin")
    fail_if(sum(1 for row in catalog if "semiconductor" in row["market_axis"]) < 2, "semiconductor design sources too thin")
    for idx, row in enumerate(catalog, start=2):
        fail_if(row["design_use_permission"] != "1", f"catalog row {idx} design permission mismatch")
        fail_if(row["historical_backtest_input_permission"] != "0", f"catalog row {idx} permits historical assignment")
        fail_if("current_or_post_period_design_calibration_source" not in row["reason_not_backtest_input"], f"catalog row {idx} missing reason")

    boundary = read_csv(OUT_DIR / "task1983_design_backtest_boundary.csv")
    by_type = {row["information_type"]: row for row in boundary}
    fail_if(by_type["current_2026_sources"]["historical_assignment_permission"] != "blocked", "current source historical block missing")
    fail_if(by_type["current_price_or_outcome"]["design_calibration_permission"] != "blocked", "current outcome design block missing")
    fail_if(by_type["historical_asof_sources"]["historical_assignment_permission"] != "allowed", "as-of historical permission missing")


def validate_l0_l5_content() -> None:
    calibration = read_csv(OUT_DIR / "task1984_l0_l5_current_calibration_map.csv")
    layers = {row["layer"] for row in calibration}
    fail_if(layers != {"L0", "L1", "L2", "L3", "L4", "L5"}, f"missing L0-L5 layers: {layers}")
    l5 = next(row for row in calibration if row["layer"] == "L5")
    fail_if("top1/top2 concentration" not in l5["current_2026_calibration_change"], "L5 concentration rule missing")
    l3 = next(row for row in calibration if row["layer"] == "L3")
    fail_if("crowding_to_air_pocket" not in l3["current_2026_calibration_change"], "L3 crowding relation missing")

    reqs = read_csv(OUT_DIR / "task1985_winner_acceleration_requirements.csv")
    primitives = {row["primitive"] for row in reqs}
    for primitive in ["winner_acceleration", "monetization_link", "market_acceptance_persistence", "crowding_budget", "invalidation_trigger"]:
        fail_if(primitive not in primitives, f"missing winner primitive {primitive}")
    fail_if(any(row["historical_assignment_ready_now"] != "0" for row in reqs), "winner requirement incorrectly assignment-ready")


def validate_status_and_docs() -> None:
    gate = read_csv(OUT_DIR / "task1990_acceptance_gate.csv")[0]
    fail_if(gate["historical_backtest_assignment_permission"] != "0", "gate permits historical assignment")
    fail_if(gate["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(gate["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(gate["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1990_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "current_2026_calibration_pack_complete_design_only", "json verdict mismatch")

    report_text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Current 2026 Calibration Pack",
        "Historical backtest assignment permission from this pack: `0`",
        "Strategy acceptance status: `NOT_ACCEPTED`",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in report_text, f"report missing phrase {phrase}")

    decision = read_csv(DECISION)[0]
    fail_if(decision["historical_backtest_assignment_permission"] != "0", "decision permits historical assignment")
    state_text = OPERATING_STATE.read_text(encoding="utf-8")
    fail_if("Task1981-Task1990 created a current-2026 design calibration pack" not in state_text, "operating state row missing")
    registry_text = REGISTRY.read_text(encoding="utf-8")
    fail_if("Task1981,Current 2026 Calibration Pack" not in registry_text, "registry row missing")
    fail_if("Task1990,Current 2026 Calibration Step 1990" not in registry_text, "registry closeout row missing")


def main() -> None:
    try:
        validate_files_counts_authority()
        validate_source_boundary()
        validate_l0_l5_content()
        validate_status_and_docs()
    except AssertionError as exc:
        print(f"[TASK1981_1990_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1981_1990_VALIDATE_OK] current 2026 calibration pack is design-only and valid")


if __name__ == "__main__":
    main()
