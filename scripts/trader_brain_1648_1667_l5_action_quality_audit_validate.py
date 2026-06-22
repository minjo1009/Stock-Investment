from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1648_1667_l5_action_quality_audit"
REPORT = ROOT / "docs/reports/task_1648_1667_l5_action_quality_audit/task_1648_1667_l5_action_quality_audit.md"
DECISION = ROOT / "docs/reports/task_1648_1667_l5_action_quality_audit/task_1648_1667_decision.csv"

REQUIRED = [
    "task1648_expert_review.csv",
    "task1649_action_contract.csv",
    "task1650_action_ledger.csv",
    "task1651_action_scorecard.csv",
    "task1652_action_rulebook.csv",
    "task1653_action_rule_revisions.csv",
    "task1654_action_quality_replay_trades.csv",
    "task1654_action_quality_replay_equity.csv",
    "task1655_action_quality_replay_metrics.csv",
    "task1656_split_oos_metrics.csv",
    "task1657_failure_attribution.csv",
    "task1666_acceptance_gate.csv",
    "task1667_closeout.csv",
    "task1667_closeout.json",
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
            print(f"[TASK1648_1667_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1648_expert_review.csv")
    contract = read_csv(OUT_DIR / "task1649_action_contract.csv")
    ledger = read_csv(OUT_DIR / "task1650_action_ledger.csv")
    scorecard = read_csv(OUT_DIR / "task1651_action_scorecard.csv")
    rules = read_csv(OUT_DIR / "task1652_action_rulebook.csv")
    revisions = read_csv(OUT_DIR / "task1653_action_rule_revisions.csv")
    trades = read_csv(OUT_DIR / "task1654_action_quality_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1654_action_quality_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1655_action_quality_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1656_split_oos_metrics.csv")
    failures = read_csv(OUT_DIR / "task1657_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1666_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1667_closeout.csv")

    if len(experts) < 6:
        errors.append("expected at least six expert review rows")
    action_types = {row["action_type"] for row in contract}
    for required in {"hold", "reduce", "exit", "no_reentry", "rerisk"}:
        if required not in action_types:
            errors.append(f"missing action contract: {required}")
    ledger_actions = {row["action_type"] for row in ledger}
    for required in {"hold", "reduce", "exit", "no_reentry", "rerisk"}:
        if required not in ledger_actions:
            errors.append(f"missing action ledger action: {required}")
    if len(ledger) < 360:
        errors.append(f"expected at least 360 action ledger rows, got {len(ledger)}")
    if len(scorecard) != 10:
        errors.append(f"expected 10 scorecard rows, got {len(scorecard)}")
    if not any(row["action_type"] == "hold" and row["quality_verdict"] == "pass" for row in scorecard):
        errors.append("hold action should be the current passing action")
    for weak in {"reduce", "exit", "rerisk"}:
        if not any(row["action_type"] == weak and row["quality_verdict"] == "weak" for row in scorecard):
            errors.append(f"{weak} weakness should be explicit")
    if len(rules) != 4:
        errors.append(f"expected four action rulebook rows, got {len(rules)}")
    if len(metrics) != 8:
        errors.append(f"expected eight replay metric rows, got {len(metrics)}")
    if len(split) != 16:
        errors.append(f"expected sixteen split rows, got {len(split)}")
    if not failures:
        errors.append("expected failure attribution rows")
    if not revisions:
        errors.append("expected rule revision rows")
    if len(trades) < 1300:
        errors.append(f"expected replay trades for eight policies, got {len(trades)}")
    if len(equity) < 400:
        errors.append(f"expected replay equity rows for eight policies, got {len(equity)}")
    if not any(row["policy_variant_id"] == "aq_combo_top3_v1" for row in metrics):
        errors.append("missing combo top3 replay metric")
    if not any(row["policy_variant_id"] == "aq_baseline_damage_top3_v1" for row in metrics):
        errors.append("missing baseline top3 replay metric")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if gate[0]["cagr_30pct_met_by_any"] != "0":
        errors.append("gate should not claim CAGR target met")
    if closeout[0]["verdict"] != "l5_action_quality_audit_implemented_not_accepted":
        errors.append("closeout verdict mismatch")

    for name, rows in [
        ("contract", contract),
        ("ledger", ledger),
        ("scorecard", scorecard),
        ("rules", rules),
        ("revisions", revisions),
        ("trades", trades),
        ("metrics", metrics),
    ]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "Each action was scored against a counterfactual before combined replay.",
        "The action-quality replay did not solve the 30pct CAGR and minus30pct MDD target together.",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1648_1667_ERROR] {error}")
        return 1
    print("[TASK1648_1667_OK] L5 action quality audit artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
