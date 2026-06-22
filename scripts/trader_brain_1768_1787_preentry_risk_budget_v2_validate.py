from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1768_1787_preentry_risk_budget_v2"
REPORT = ROOT / "docs/reports/task_1768_1787_preentry_risk_budget_v2/task_1768_1787_preentry_risk_budget_v2.md"
DECISION = ROOT / "docs/reports/task_1768_1787_preentry_risk_budget_v2/task_1768_1787_decision.csv"

REQUIRED = [
    "task1768_expert_review.csv",
    "task1770_preentry_risk_budget_v2_panel.csv",
    "task1771_budget_action_panel.csv",
    "task1772_preentry_budget_v2_replay_trades.csv",
    "task1772_preentry_budget_v2_replay_equity.csv",
    "task1773_preentry_budget_v2_replay_metrics.csv",
    "task1774_split_oos_metrics.csv",
    "task1775_failure_attribution.csv",
    "task1786_acceptance_gate.csv",
    "task1787_closeout.csv",
    "task1787_closeout.json",
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
            print(f"[TASK1768_1787_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1768_expert_review.csv")
    panel = read_csv(OUT_DIR / "task1770_preentry_risk_budget_v2_panel.csv")
    actions = read_csv(OUT_DIR / "task1771_budget_action_panel.csv")
    trades = read_csv(OUT_DIR / "task1772_preentry_budget_v2_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1772_preentry_budget_v2_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1773_preentry_budget_v2_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1774_split_oos_metrics.csv")
    attr = read_csv(OUT_DIR / "task1775_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1786_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1787_closeout.csv")

    if len(experts) < 6:
        errors.append("expected at least six expert review rows")
    if len(panel) != 377:
        errors.append(f"panel expected 377 rows, got {len(panel)}")
    if len(actions) != 377:
        errors.append(f"actions expected 377 rows, got {len(actions)}")
    if not 350 <= len(trades) <= 377:
        errors.append(f"trades expected 350-377 rows, got {len(trades)}")
    if len(equity) != 122:
        errors.append(f"equity expected 122 rows, got {len(equity)}")
    if len(metrics) != 2:
        errors.append(f"metrics expected 2 rows, got {len(metrics)}")
    if len(split) != 4:
        errors.append(f"split expected 4 rows, got {len(split)}")
    if not attr:
        errors.append("expected attribution rows")

    states = {row["risk_budget_state_v2"] for row in panel}
    if "full_size_continuous" not in states:
        errors.append("missing full_size_continuous state")
    if not ({"soft_cap_continuous", "half_size_continuous", "quarter_size_continuous", "no_entry"} & states):
        errors.append("no continuous cap/no-entry states fired")
    if not any(float(row["risk_budget_multiplier_v2"]) < 1.0 for row in panel):
        errors.append("no v2 size cap fired")
    if not any(float(row["cluster_corr_63d"]) > 0 for row in panel):
        errors.append("no cluster correlation values computed")
    for required in {"preentry_risk_budget_v2_top3_v1", "preentry_risk_budget_v2_top5_v1"}:
        if not any(row["policy_variant_id"] == required for row in metrics):
            errors.append(f"missing metric policy: {required}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if closeout[0]["verdict"] != "preentry_risk_budget_v2_implemented_diagnostic_only":
        errors.append("closeout verdict mismatch")

    for name, rows in [("panel", panel), ("actions", actions), ("trades", trades), ("metrics", metrics)]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "V2 moves from coarse buckets to continuous pre-entry sizing.",
        "It adds 63-day same-cluster correlation pressure.",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1768_1787_ERROR] {error}")
        return 1
    print("[TASK1768_1787_OK] pre-entry risk budget v2 artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
