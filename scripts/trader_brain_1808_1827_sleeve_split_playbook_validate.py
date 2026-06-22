from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
REPORT = ROOT / "docs/reports/task_1808_1827_sleeve_split_playbook/task_1808_1827_sleeve_split_playbook.md"
DECISION = ROOT / "docs/reports/task_1808_1827_sleeve_split_playbook/task_1808_1827_decision.csv"
AUTHORITY = "DIAGNOSTIC_SLEEVE_SPLIT_PLAYBOOK_ONLY"
INITIAL_CAPITAL = 1000.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    raise SystemExit(f"[TASK1808_1827_FAIL] {message}")


def require(path: Path) -> None:
    if not path.exists():
        fail(f"missing artifact: {path}")


def to_float(value: object) -> float:
    try:
        if value in {"", None, "nan"}:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    required = [
        OUT_DIR / "task1808_trade_drawdown_attribution_ledger.csv",
        OUT_DIR / "task1809_sleeve_taxonomy_contract.csv",
        OUT_DIR / "task1810_regime_classifier_panel.csv",
        OUT_DIR / "task1811_l1_source_routing_contract.csv",
        OUT_DIR / "task1812_l2_sleeve_meaning_panel.csv",
        OUT_DIR / "task1813_l3_sleeve_relation_edges.csv",
        OUT_DIR / "task1814_l4_sleeve_thesis_cards.csv",
        OUT_DIR / "task1815_sleeve_risk_budget.csv",
        OUT_DIR / "task1816_l5_sleeve_action_rules.csv",
        OUT_DIR / "task1817_1820_sleeve_playbooks.csv",
        OUT_DIR / "task1821_frozen_policy_config.csv",
        OUT_DIR / "task1822_controlled_sleeve_replay_trades.csv",
        OUT_DIR / "task1822_controlled_sleeve_replay_equity.csv",
        OUT_DIR / "task1823_sleeve_replay_metrics.csv",
        OUT_DIR / "task1823_split_oos_metrics.csv",
        OUT_DIR / "task1823_cost_stress_metrics.csv",
        OUT_DIR / "task1824_failure_attribution.csv",
        OUT_DIR / "task1825_expert_audit.csv",
        OUT_DIR / "task1826_acceptance_gate.csv",
        OUT_DIR / "task1827_closeout.csv",
        OUT_DIR / "task1827_closeout.json",
        OUT_DIR / "artifact_manifest.csv",
        REPORT,
        DECISION,
    ]
    for path in required:
        require(path)

    ledger = read_csv(OUT_DIR / "task1808_trade_drawdown_attribution_ledger.csv")
    contracts = read_csv(OUT_DIR / "task1809_sleeve_taxonomy_contract.csv")
    regimes = read_csv(OUT_DIR / "task1810_regime_classifier_panel.csv")
    meaning = read_csv(OUT_DIR / "task1812_l2_sleeve_meaning_panel.csv")
    edges = read_csv(OUT_DIR / "task1813_l3_sleeve_relation_edges.csv")
    cards = read_csv(OUT_DIR / "task1814_l4_sleeve_thesis_cards.csv")
    budgets = read_csv(OUT_DIR / "task1815_sleeve_risk_budget.csv")
    trades = read_csv(OUT_DIR / "task1822_controlled_sleeve_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1822_controlled_sleeve_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1823_sleeve_replay_metrics.csv")
    splits = read_csv(OUT_DIR / "task1823_split_oos_metrics.csv")
    cost = read_csv(OUT_DIR / "task1823_cost_stress_metrics.csv")
    experts = read_csv(OUT_DIR / "task1825_expert_audit.csv")
    gate = read_csv(OUT_DIR / "task1826_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1827_closeout.csv")

    expected_counts = {
        "ledger": (ledger, 377),
        "contracts": (contracts, 4),
        "regimes": (regimes, 122),
        "meaning": (meaning, 377),
        "edges": (edges, 377),
        "cards": (cards, 377),
        "budgets": (budgets, 377),
        "equity": (equity, 122),
        "metrics": (metrics, 2),
        "splits": (splits, 4),
        "cost": (cost, 8),
        "experts": (experts, 6),
        "gate": (gate, 1),
        "closeout": (closeout, 1),
    }
    for name, (rows, expected) in expected_counts.items():
        if len(rows) != expected:
            fail(f"{name} row count expected {expected} got {len(rows)}")
    if not (360 <= len(trades) <= 377):
        fail(f"trade rows outside expected range: {len(trades)}")

    all_rows = ledger + meaning + edges + cards + budgets + trades + equity + metrics + gate + closeout
    if any(row.get("authority") != AUTHORITY for row in all_rows):
        fail("authority mismatch")
    if any(row.get("assignment_uses_future_outcome", "0") != "0" for row in ledger + meaning + budgets + trades + metrics):
        fail("future outcome assignment flag detected")
    if any(row.get("outcome_used_for_assignment", "0") != "0" for row in ledger + meaning + budgets + trades + metrics):
        fail("outcome assignment use detected")

    ledger_keys = {(row["policy_variant_id"], row["trade_spec_id"]) for row in ledger}
    if len(ledger_keys) != len(ledger):
        fail("duplicate ledger policy/trade_spec_id keys")
    sleeves = {row["sleeve_name"] for row in contracts}
    if sleeves != {"winner_compounder", "cyclical_beta", "speculative_event", "defensive_quality"}:
        fail(f"unexpected sleeve contract set: {sleeves}")
    if {row["strategy_sleeve"] for row in meaning} != sleeves:
        fail("not all sleeves are represented in meaning panel")
    if not any(row["regime_state"] in {"broad_selloff", "valuation_compression"} for row in regimes):
        fail("risk-off regimes never fired")

    by_period: dict[tuple[str, str], float] = defaultdict(float)
    for trade in trades:
        by_period[(trade["policy_variant_id"], trade["decision_asof_ts"])] += to_float(trade["pnl"])
    for eq in equity:
        key = (eq["policy_variant_id"], eq["decision_asof_ts"])
        if abs(by_period.get(key, 0.0) - to_float(eq["period_pnl"])) > 0.15:
            fail(f"period pnl mismatch for {key}")

    for policy_id in {row["policy_variant_id"] for row in equity}:
        peak = INITIAL_CAPITAL
        for eq in sorted([row for row in equity if row["policy_variant_id"] == policy_id], key=lambda row: row["decision_asof_ts"]):
            peak = max(peak, to_float(eq["equity"]))
            # Ledger repeats equity peak; check at least one row carries the period peak.
            period_rows = [row for row in ledger if row["policy_variant_id"] == policy_id and row["decision_asof_ts"] == eq["decision_asof_ts"]]
            if period_rows and abs(to_float(period_rows[0]["equity_peak_to_date"]) - peak) > 0.1:
                fail(f"equity peak mismatch for {policy_id} {eq['decision_asof_ts']}")

    dd_sum: dict[tuple[str, str], float] = defaultdict(float)
    dd_delta: dict[tuple[str, str], float] = {}
    for row in ledger:
        key = (row["policy_variant_id"], row["decision_asof_ts"])
        dd_sum[key] += to_float(row["trade_drawdown_contribution"])
        dd_delta[key] = to_float(row["period_drawdown_delta"])
    for key, delta in dd_delta.items():
        if delta < -1e-9 and abs(dd_sum[key] - delta) > 0.25:
            fail(f"drawdown contribution mismatch for {key}: {dd_sum[key]} vs {delta}")

    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    if best["policy_variant_id"] != "sleeve_split_top3_v1":
        fail("best policy is not top3 sleeve split")
    if best["joint_target_met"] != "1":
        fail("best policy did not meet joint diagnostic target")
    if best["strategy_acceptance"] != "NOT_ACCEPTED":
        fail("strategy acceptance changed")
    if best["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        fail("deployment readiness changed")
    if best["real_capital"] != "FORBIDDEN":
        fail("real capital status changed")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or closeout[0]["real_capital"] != "FORBIDDEN":
        fail("gate/closeout status changed")

    report_text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Sleeve Split Playbook",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "audit-only",
    ]:
        if phrase not in report_text:
            fail(f"report missing phrase: {phrase}")

    print("[TASK1808_1827_OK] sleeve split playbook artifacts validated")


if __name__ == "__main__":
    main()
