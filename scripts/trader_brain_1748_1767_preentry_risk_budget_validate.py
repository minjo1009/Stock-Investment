from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1748_1767_preentry_risk_budget"
REPORT = ROOT / "docs/reports/task_1748_1767_preentry_risk_budget/task_1748_1767_preentry_risk_budget.md"
DECISION = ROOT / "docs/reports/task_1748_1767_preentry_risk_budget/task_1748_1767_decision.csv"

REQUIRED = [
    "task1748_expert_review.csv",
    "task1750_preentry_risk_budget_panel.csv",
    "task1751_budget_action_panel.csv",
    "task1752_preentry_budget_replay_trades.csv",
    "task1752_preentry_budget_replay_equity.csv",
    "task1753_preentry_budget_replay_metrics.csv",
    "task1754_split_oos_metrics.csv",
    "task1755_failure_attribution.csv",
    "task1766_acceptance_gate.csv",
    "task1767_closeout.csv",
    "task1767_closeout.json",
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
            print(f"[TASK1748_1767_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1748_expert_review.csv")
    preentry = read_csv(OUT_DIR / "task1750_preentry_risk_budget_panel.csv")
    actions = read_csv(OUT_DIR / "task1751_budget_action_panel.csv")
    trades = read_csv(OUT_DIR / "task1752_preentry_budget_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1752_preentry_budget_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1753_preentry_budget_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1754_split_oos_metrics.csv")
    attr = read_csv(OUT_DIR / "task1755_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1766_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1767_closeout.csv")

    if len(experts) < 10:
        errors.append("expected at least ten expert review rows")
    if len(preentry) != 377:
        errors.append(f"preentry panel expected 377 rows, got {len(preentry)}")
    if len(actions) != 377:
        errors.append(f"budget action expected 377 rows, got {len(actions)}")
    if not 300 <= len(trades) <= 377:
        errors.append(f"trade rows expected 300-377 after no-entry, got {len(trades)}")
    if len(equity) != 122:
        errors.append(f"equity expected 122 rows, got {len(equity)}")
    if len(metrics) != 2:
        errors.append(f"metrics expected 2 rows, got {len(metrics)}")
    if len(split) != 4:
        errors.append(f"split expected 4 rows, got {len(split)}")
    if not attr:
        errors.append("expected attribution rows")

    states = {row["risk_budget_state"] for row in preentry}
    if "full_size" not in states:
        errors.append("missing full_size state")
    if not ({"half_size_risk_budget", "quarter_size_preplanned_reduce", "cluster_soft_cap", "no_entry"} & states):
        errors.append("no risk budget cap/no-entry state fired")
    if not any(row["budget_action"] == "no_entry" for row in actions):
        errors.append("no no-entry action fired")
    if not any(float(row["risk_budget_multiplier"]) < 1.0 for row in actions):
        errors.append("no size cap fired")
    if not any(row["policy_variant_id"] == "preentry_risk_budget_top3_v1" for row in metrics):
        errors.append("missing top3 metric")
    if not any(row["policy_variant_id"] == "preentry_risk_budget_top5_v1" for row in metrics):
        errors.append("missing top5 metric")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if closeout[0]["verdict"] != "preentry_risk_budget_implemented_diagnostic_only":
        errors.append("closeout verdict mismatch")

    for name, rows in [
        ("preentry", preentry),
        ("actions", actions),
        ("trades", trades),
        ("metrics", metrics),
    ]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "Risk budget is assigned before entry.",
        "This tests whether firm-style pre-trade risk planning is better than late reduce.",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1748_1767_ERROR] {error}")
        return 1
    print("[TASK1748_1767_OK] pre-entry risk budget artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
