from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
REPORT = ROOT / "docs/reports/task_1788_1807_winner_defense_budget/task_1788_1807_winner_defense_budget.md"
DECISION = ROOT / "docs/reports/task_1788_1807_winner_defense_budget/task_1788_1807_decision.csv"
AUTHORITY = "DIAGNOSTIC_WINNER_DEFENSE_BUDGET_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    raise SystemExit(f"[TASK1788_1807_FAIL] {message}")


def require(path: Path) -> None:
    if not path.exists():
        fail(f"missing artifact: {path}")


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    required = [
        OUT_DIR / "task1788_expert_review.csv",
        OUT_DIR / "task1790_winner_defense_panel.csv",
        OUT_DIR / "task1791_winner_defense_action_panel.csv",
        OUT_DIR / "task1792_winner_defense_replay_trades.csv",
        OUT_DIR / "task1792_winner_defense_replay_equity.csv",
        OUT_DIR / "task1793_winner_defense_replay_metrics.csv",
        OUT_DIR / "task1794_split_oos_metrics.csv",
        OUT_DIR / "task1795_failure_attribution.csv",
        OUT_DIR / "task1806_acceptance_gate.csv",
        OUT_DIR / "task1807_closeout.csv",
        OUT_DIR / "task1807_closeout.json",
        OUT_DIR / "artifact_manifest.csv",
        REPORT,
        DECISION,
    ]
    for path in required:
        require(path)

    experts = read_csv(OUT_DIR / "task1788_expert_review.csv")
    panel = read_csv(OUT_DIR / "task1790_winner_defense_panel.csv")
    actions = read_csv(OUT_DIR / "task1791_winner_defense_action_panel.csv")
    trades = read_csv(OUT_DIR / "task1792_winner_defense_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1792_winner_defense_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1793_winner_defense_replay_metrics.csv")
    splits = read_csv(OUT_DIR / "task1794_split_oos_metrics.csv")
    gate = read_csv(OUT_DIR / "task1806_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1807_closeout.csv")

    if len(experts) < 6:
        fail("expert review rows below minimum")
    if len(panel) != 377:
        fail(f"panel row count expected 377 got {len(panel)}")
    if len(actions) != 377:
        fail(f"action row count expected 377 got {len(actions)}")
    if not (340 <= len(trades) <= 377):
        fail(f"trade row count outside expected range: {len(trades)}")
    if len(equity) != 122:
        fail(f"equity row count expected 122 got {len(equity)}")
    if len(metrics) != 2:
        fail(f"metrics row count expected 2 got {len(metrics)}")
    if len(splits) != 4:
        fail(f"split row count expected 4 got {len(splits)}")
    if len(gate) != 1 or len(closeout) != 1:
        fail("gate or closeout row count invalid")

    if any(row.get("assignment_uses_future_outcome") != "0" for row in panel + actions + trades + metrics):
        fail("future outcome assignment flag detected")
    if any(row.get("outcome_used_for_assignment", "0") != "0" for row in panel + trades + metrics):
        fail("outcome assignment use detected")
    if any(row.get("authority") != AUTHORITY for row in panel + actions + trades + metrics + gate + closeout):
        fail("authority mismatch")

    causes = {row["volatility_cause"] for row in panel}
    if "normal_winner_volatility" not in causes and "leader_momentum_volatility" not in causes:
        fail("winner volatility cause never fired")
    buckets = {row["winner_defense_bucket"] for row in panel}
    if "strong_winner_defense" not in buckets:
        fail("strong winner defense never fired")
    if not any(to_float(row["winner_defense_credit"]) > 0 for row in panel):
        fail("winner defense credit never fired")
    if not any(to_float(row["winner_defense_multiplier_v3"]) > to_float(row["risk_budget_multiplier_v2"]) for row in panel):
        fail("v3 never releases size relative to v2")

    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    if best["strategy_acceptance"] != "NOT_ACCEPTED":
        fail("strategy acceptance changed")
    if best["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        fail("deployment readiness changed")
    if best["real_capital"] != "FORBIDDEN":
        fail("real capital status changed")
    if not any(row["target_mdd_minus30pct_met"] == "1" for row in metrics):
        fail("no variant keeps MDD target")
    if to_float(best["final_equity"]) <= 3440.6109:
        fail("best variant did not improve over Task1768 v2 top3 final equity")

    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Winner Defense Budget",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
    ]:
        if phrase not in text:
            fail(f"report missing phrase: {phrase}")

    print("[TASK1788_1807_OK] winner defense budget artifacts validated")


if __name__ == "__main__":
    main()
