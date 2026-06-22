from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
REPORT = ROOT / "docs/reports/task_1991_2000_winner_acceleration_surgery/task_1991_2000_winner_acceleration_surgery.md"
DECISION = ROOT / "docs/reports/task_1991_2000_winner_acceleration_surgery/task_1991_2000_decision.csv"
REGISTRY = ROOT / "tasks/task_registry.csv"
OPERATING_STATE = ROOT / "docs/operating_system/project_operating_state.md"
AUTHORITY = "DIAGNOSTIC_WINNER_ACCELERATION_SURGERY_ONLY"

REQUIRED_COUNTS = {
    "task1991_winner_source_contract.csv": 7,
    "task1992_l1_winner_acceleration_packets.csv": 377,
    "task1993_l2_winner_acceleration_semantics.csv": 377,
    "task1994_l3_winner_acceleration_edges.csv": 795,
    "task1995_l4_winner_acceleration_thesis_cards.csv": 377,
    "task1996_l5_winner_acceleration_decisions.csv": 377,
    "task1997_winner_acceleration_replay_trades.csv": 436,
    "task1997_winner_acceleration_replay_equity.csv": 183,
    "task1998_winner_acceleration_replay_metrics.csv": 3,
    "task1998_winner_acceleration_split_oos_metrics.csv": 6,
    "task1998_winner_acceleration_cost_stress.csv": 12,
    "task1999_winner_acceleration_attribution.csv": 12,
    "task1999_expert_review_matrix.csv": 6,
    "task2000_acceptance_gate.csv": 1,
    "task2000_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_files_counts_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
        for idx, row in enumerate(rows, start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{name}:{idx} outcome assignment")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task2000_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision")


def validate_source_and_leakage_boundary() -> None:
    contracts = read_csv(OUT_DIR / "task1991_winner_source_contract.csv")
    fail_if(any(row["current_source_direct_assignment_permission"] != "0" for row in contracts), "current source direct assignment allowed")
    fail_if(any(row["historical_assignment_ready_now"] != "proxy_field_only_not_full_source_extractor" for row in contracts), "contract overstates source readiness")
    packets = read_csv(OUT_DIR / "task1992_l1_winner_acceleration_packets.csv")
    for idx, row in enumerate(packets, start=2):
        fail_if(row["current_2026_direct_input_used"] != "0", f"L1 current input used at row {idx}")
        decision = parse_ts(row["decision_asof_ts"])
        available = parse_ts(row["available_to_brain_ts"])
        published = parse_ts(row["source_published_ts"])
        received = parse_ts(row["source_received_ts"])
        fail_if(available > decision, f"L1 available_to_brain after decision at row {idx}")
        fail_if(published > decision, f"L1 source_published after decision at row {idx}")
        fail_if(received > decision, f"L1 source_received after decision at row {idx}")
        fail_if(row["source_lineage_type"] != "derived_prior_known_repo_field_no_current_source_assignment", f"L1 lineage mismatch at row {idx}")
    for name in [
        "task1993_l2_winner_acceleration_semantics.csv",
        "task1994_l3_winner_acceleration_edges.csv",
        "task1995_l4_winner_acceleration_thesis_cards.csv",
        "task1996_l5_winner_acceleration_decisions.csv",
    ]:
        fail_if(any(row["current_2026_direct_input_used"] != "0" for row in read_csv(OUT_DIR / name)), f"{name} uses current 2026 direct input")


def validate_l0_l5_surgery() -> None:
    l2 = read_csv(OUT_DIR / "task1993_l2_winner_acceleration_semantics.csv")
    states = {row["winner_acceleration_state"] for row in l2}
    for required in ["convex_winner_acceleration", "qualified_winner_acceleration", "watch_winner_acceleration", "ordinary_or_unproven"]:
        fail_if(required not in states, f"missing L2 state {required}")
    l3 = read_csv(OUT_DIR / "task1994_l3_winner_acceleration_edges.csv")
    mechanisms = {row["mechanism_edge"] for row in l3}
    for required in ["ai_capex_chain_supports_payoff", "market_acceptance_confirms_repricing", "winner_quality_defends_normal_volatility", "crowding_or_damage_caps_concentration"]:
        fail_if(required not in mechanisms, f"missing L3 mechanism {required}")
    l4 = read_csv(OUT_DIR / "task1995_l4_winner_acceleration_thesis_cards.csv")
    thesis = {row["winner_thesis_state"] for row in l4}
    fail_if("convex_winner_thesis" not in thesis, "missing convex thesis")
    fail_if("qualified_winner_thesis" not in thesis, "missing qualified thesis")
    l5 = read_csv(OUT_DIR / "task1996_l5_winner_acceleration_decisions.csv")
    actions = {row["l5_action"] for row in l5}
    for required in ["concentrate_hold", "full_hold", "watch_small", "deprioritize"]:
        fail_if(required not in actions, f"missing L5 action {required}")


def validate_replay_metrics_and_status() -> None:
    metrics = read_csv(OUT_DIR / "task1998_winner_acceleration_replay_metrics.csv")
    by_policy = {row["policy_variant_id"]: row for row in metrics}
    fail_if(by_policy["winner_accel_top3_source_v1"]["joint_target_met"] != "1", "balanced top3 joint target not met")
    fail_if(to_float(by_policy["winner_accel_top3_source_v1"]["final_equity"]) <= 4024.7118, "balanced top3 did not improve Task1971")
    fail_if(to_float(by_policy["winner_accel_top5_to_top2_convex_v1"]["max_drawdown"]) >= -0.30, "convex stress unexpectedly inside MDD target")
    for row in metrics:
        fail_if(row["strategy_acceptance"] != "NOT_ACCEPTED", "strategy acceptance changed")
        fail_if(row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
        fail_if(row["real_capital"] != "FORBIDDEN", "real capital changed")
    gate = read_csv(OUT_DIR / "task2000_acceptance_gate.csv")[0]
    fail_if(gate["strategy_acceptance"] != "NOT_ACCEPTED", "gate strategy changed")
    closeout = json.loads((OUT_DIR / "task2000_closeout.json").read_text(encoding="utf-8"))
    fail_if(closeout["verdict"] != "winner_acceleration_surgery_complete_diagnostic_only", "closeout verdict mismatch")


def validate_docs_registry() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Winner Acceleration Surgery",
        "Current 2026 sources are design calibration only",
        "L0 historical source contract",
        "Strategy acceptance status: `NOT_ACCEPTED`",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in report, f"report missing phrase {phrase}")
    registry = REGISTRY.read_text(encoding="utf-8")
    fail_if("Task1991,Winner Acceleration Historical Source Contract" not in registry, "registry task1991 missing")
    fail_if("Task2000,Winner Acceleration Closeout" not in registry, "registry task2000 missing")
    state = OPERATING_STATE.read_text(encoding="utf-8")
    fail_if("Task1991-Task2000 implemented the current-2026 winner-acceleration surgery" not in state, "operating state row missing")


def main() -> None:
    try:
        validate_files_counts_authority()
        validate_source_and_leakage_boundary()
        validate_l0_l5_surgery()
        validate_replay_metrics_and_status()
        validate_docs_registry()
    except AssertionError as exc:
        print(f"[TASK1991_2000_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1991_2000_VALIDATE_OK] winner acceleration surgery artifacts are diagnostic-only and valid")


if __name__ == "__main__":
    main()
