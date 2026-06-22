from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1618_1647_expectation_payoff_rerisk_bridge"
REPORT = ROOT / "docs/reports/task_1618_1647_expectation_payoff_rerisk_bridge/task_1618_1647_expectation_payoff_rerisk_bridge.md"
DECISION = ROOT / "docs/reports/task_1618_1647_expectation_payoff_rerisk_bridge/task_1618_1647_decision.csv"

REQUIRED = [
    "task1618_expert_implementation_review.csv",
    "task1619_data_availability_contract.csv",
    "task1620_tradable_surprise_panel.csv",
    "task1621_payoff_window_panel.csv",
    "task1622_absorption_quality_panel.csv",
    "task1623_l3_payoff_mechanism_edges.csv",
    "task1624_l4_payoff_thesis_cards.csv",
    "task1625_l5_rerisk_state_panel.csv",
    "task1626_negative_fixtures.csv",
    "task1627_preregistered_policy_specs.csv",
    "task1628_rerisk_replay_trades.csv",
    "task1628_rerisk_replay_equity.csv",
    "task1628_rerisk_events.csv",
    "task1629_rerisk_replay_metrics.csv",
    "task1630_split_oos_metrics.csv",
    "task1632_cost_stress_metrics.csv",
    "task1633_failure_attribution.csv",
    "task1646_acceptance_gate.csv",
    "task1647_closeout.csv",
    "task1647_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require_no_future_assignment(rows: list[dict[str, str]], name: str, errors: list[str]) -> None:
    for idx, row in enumerate(rows, 1):
        if row.get("assignment_uses_future_outcome", "0") != "0":
            errors.append(f"{name} row {idx} uses future outcome for assignment")
            return
        if row.get("outcome_used_for_assignment", "0") != "0":
            errors.append(f"{name} row {idx} uses outcome for assignment")
            return


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
            print(f"[TASK1618_1647_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1618_expert_implementation_review.csv")
    data_contract = read_csv(OUT_DIR / "task1619_data_availability_contract.csv")
    surprise = read_csv(OUT_DIR / "task1620_tradable_surprise_panel.csv")
    payoff = read_csv(OUT_DIR / "task1621_payoff_window_panel.csv")
    absorption = read_csv(OUT_DIR / "task1622_absorption_quality_panel.csv")
    edges = read_csv(OUT_DIR / "task1623_l3_payoff_mechanism_edges.csv")
    l4_cards = read_csv(OUT_DIR / "task1624_l4_payoff_thesis_cards.csv")
    states = read_csv(OUT_DIR / "task1625_l5_rerisk_state_panel.csv")
    fixtures = read_csv(OUT_DIR / "task1626_negative_fixtures.csv")
    policies = read_csv(OUT_DIR / "task1627_preregistered_policy_specs.csv")
    trades = read_csv(OUT_DIR / "task1628_rerisk_replay_trades.csv")
    events = read_csv(OUT_DIR / "task1628_rerisk_events.csv")
    metrics = read_csv(OUT_DIR / "task1629_rerisk_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1630_split_oos_metrics.csv")
    stress = read_csv(OUT_DIR / "task1632_cost_stress_metrics.csv")
    failures = read_csv(OUT_DIR / "task1633_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1646_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1647_closeout.csv")

    if len(experts) < 10:
        errors.append("expected at least ten expert implementation review rows")
    if len(data_contract) < 7:
        errors.append("data availability contract too small")
    if not any(row["input_name"] == "analyst_pit_estimate_revision" and row["availability_state"] == "licensed_gap" for row in data_contract):
        errors.append("analyst PIT gap is not explicitly preserved")

    expected_rows = [
        ("tradable surprise", surprise, 3100),
        ("payoff window", payoff, 3100),
        ("absorption quality", absorption, 3100),
        ("L4 payoff thesis cards", l4_cards, 3100),
        ("L3 payoff mechanism edges", edges, 15500),
        ("L5 rerisk state panel", states, 345),
        ("replay trades", trades, 1035),
        ("main metrics", metrics, 6),
        ("split metrics", split, 12),
        ("cost stress metrics", stress, 12),
    ]
    for label, rows, expected in expected_rows:
        if len(rows) != expected:
            errors.append(f"{label} expected {expected} rows, got {len(rows)}")

    if len(fixtures) < 5:
        errors.append("negative fixture suite too small")
    if len(policies) != 6:
        errors.append("expected six preregistered policy variants")
    if not events:
        errors.append("expected at least one runtime rerisk event")
    if not failures:
        errors.append("expected failure attribution rows")

    if {row["analyst_pit_available"] for row in surprise} != {"0"}:
        errors.append("analyst PIT availability should remain unavailable in all surprise rows")
    if not any(row["surprise_quality"] == "good_words_only" for row in surprise):
        errors.append("good-words-only surprise bucket missing")
    if not any(row["persistence_state"] == "persistent" for row in absorption):
        errors.append("persistent absorption bucket missing")
    if not any(row["rerisk_allowed"] == "1" for row in states):
        errors.append("no L5 rerisk-eligible state rows")
    if not any(row["strict_rerisk_allowed"] == "1" for row in states):
        errors.append("no strict L5 rerisk-eligible state rows")
    if not any(row["rerisk_state"] in {"partial_rerisk", "confirmed_rerisk"} for row in trades):
        errors.append("runtime replay did not execute rerisk states")
    if not any(row["policy_variant_id"] == "rerisk_none_top3_v1" for row in metrics):
        errors.append("missing no-rerisk top3 baseline")
    if not any(row["policy_variant_id"] == "rerisk_partial_top3_v1" for row in metrics):
        errors.append("missing partial rerisk top3 policy")
    if not any(row["policy_variant_id"] == "rerisk_confirmed_top3_v1" for row in metrics):
        errors.append("missing confirmed rerisk top3 policy")

    for name, rows in [
        ("surprise", surprise),
        ("payoff", payoff),
        ("absorption", absorption),
        ("edges", edges),
        ("l4_cards", l4_cards),
        ("states", states),
        ("fixtures", fixtures),
        ("policies", policies),
        ("trades", trades),
        ("events", events),
        ("metrics", metrics),
        ("stress", stress),
    ]:
        require_no_future_assignment(rows, name, errors)

    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("acceptance gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("acceptance gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims real capital")
    if gate[0]["cagr_30pct_met_by_any"] != "0":
        errors.append("gate should not claim the 30pct CAGR target was met")
    if closeout[0]["verdict"] != "expectation_payoff_rerisk_bridge_implemented_not_accepted":
        errors.append("closeout verdict mismatch")

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "The planned bridge was implemented as code, panels, replay, and audit artifacts.",
        "Re-risk events fired, but staged re-risk did not beat the no-rerisk diagnostic baseline.",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1618_1647_ERROR] {error}")
        return 1
    print("[TASK1618_1647_OK] expectation-payoff-rerisk bridge artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
