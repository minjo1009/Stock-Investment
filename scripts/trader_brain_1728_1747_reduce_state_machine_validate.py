from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1728_1747_reduce_state_machine"
REPORT = ROOT / "docs/reports/task_1728_1747_reduce_state_machine/task_1728_1747_reduce_state_machine.md"
DECISION = ROOT / "docs/reports/task_1728_1747_reduce_state_machine/task_1728_1747_decision.csv"

REQUIRED = [
    "task1728_expert_review.csv",
    "task1729_reduce_contract.csv",
    "task1730_reduce_state_panel.csv",
    "task1731_reduce_state_replay_trades.csv",
    "task1731_reduce_state_replay_equity.csv",
    "task1732_reduce_state_replay_metrics.csv",
    "task1733_split_oos_metrics.csv",
    "task1734_failure_attribution.csv",
    "task1746_acceptance_gate.csv",
    "task1747_closeout.csv",
    "task1747_closeout.json",
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
            print(f"[TASK1728_1747_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1728_expert_review.csv")
    contract = read_csv(OUT_DIR / "task1729_reduce_contract.csv")
    states = read_csv(OUT_DIR / "task1730_reduce_state_panel.csv")
    trades = read_csv(OUT_DIR / "task1731_reduce_state_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1731_reduce_state_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1732_reduce_state_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1733_split_oos_metrics.csv")
    attr = read_csv(OUT_DIR / "task1734_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1746_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1747_closeout.csv")

    if len(experts) < 10:
        errors.append("expected at least ten expert review rows")
    if len(contract) != 5:
        errors.append(f"reduce contract expected 5 rows, got {len(contract)}")
    if len(states) != 377:
        errors.append(f"reduce state panel expected 377 rows, got {len(states)}")
    if len(trades) != 377:
        errors.append(f"replay trades expected 377 rows, got {len(trades)}")
    if len(equity) != 122:
        errors.append(f"equity expected 122 rows, got {len(equity)}")
    if len(metrics) != 2:
        errors.append(f"metrics expected 2 rows, got {len(metrics)}")
    if len(split) != 4:
        errors.append(f"split expected 4 rows, got {len(split)}")
    if not attr:
        errors.append("expected attribution rows")

    states_seen = {row["reduce_state"] for row in states}
    if not {"hold", "preventive_reduce", "damage_reduce", "failed_reduce_to_exit"} & states_seen:
        errors.append("state machine did not produce reduce states")
    if "failed_reduce_to_exit" not in states_seen:
        errors.append("failed_reduce_to_exit did not fire")
    if not any(row["runtime_action"] == "reduce_then_exit" for row in trades):
        errors.append("reduce_then_exit trades missing")
    if not any(row["policy_variant_id"] == "reduce_state_machine_top3_v1" for row in metrics):
        errors.append("missing top3 metrics")
    if not any(row["policy_variant_id"] == "reduce_state_machine_top5_v1" for row in metrics):
        errors.append("missing top5 metrics")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if closeout[0]["verdict"] != "reduce_state_machine_implemented_diagnostic_only":
        errors.append("closeout verdict mismatch")

    for name, rows in [
        ("contract", contract),
        ("states", states),
        ("trades", trades),
        ("metrics", metrics),
    ]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "Reduce is now a state machine",
        "reduce after damage, or exit remaining exposure if recovery fails",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1728_1747_ERROR] {error}")
        return 1
    print("[TASK1728_1747_OK] reduce state machine artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
