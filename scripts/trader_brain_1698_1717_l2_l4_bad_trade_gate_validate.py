from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
REPORT = ROOT / "docs/reports/task_1698_1717_l2_l4_bad_trade_gate/task_1698_1717_l2_l4_bad_trade_gate.md"
DECISION = ROOT / "docs/reports/task_1698_1717_l2_l4_bad_trade_gate/task_1698_1717_decision.csv"

REQUIRED = [
    "task1698_expert_review.csv",
    "task1699_collapse_risk_v2_panel.csv",
    "task1700_payoff_quality_v2_panel.csv",
    "task1701_risk_payoff_mechanism_edges.csv",
    "task1702_top3_top5_candidate_compressor.csv",
    "task1703_thesis_break_action_panel.csv",
    "task1704_bad_trade_gate_replay_trades.csv",
    "task1704_bad_trade_gate_replay_equity.csv",
    "task1705_bad_trade_gate_replay_metrics.csv",
    "task1706_split_oos_metrics.csv",
    "task1707_failure_attribution.csv",
    "task1716_acceptance_gate.csv",
    "task1717_closeout.csv",
    "task1717_closeout.json",
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
            print(f"[TASK1698_1717_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1698_expert_review.csv")
    collapse = read_csv(OUT_DIR / "task1699_collapse_risk_v2_panel.csv")
    payoff = read_csv(OUT_DIR / "task1700_payoff_quality_v2_panel.csv")
    edges = read_csv(OUT_DIR / "task1701_risk_payoff_mechanism_edges.csv")
    compressor = read_csv(OUT_DIR / "task1702_top3_top5_candidate_compressor.csv")
    actions = read_csv(OUT_DIR / "task1703_thesis_break_action_panel.csv")
    trades = read_csv(OUT_DIR / "task1704_bad_trade_gate_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1704_bad_trade_gate_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task1705_bad_trade_gate_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1706_split_oos_metrics.csv")
    failures = read_csv(OUT_DIR / "task1707_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1716_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1717_closeout.csv")

    if len(experts) < 10:
        errors.append("expected at least 10 expert review rows")
    for label, rows, expected in [
        ("collapse risk", collapse, 3100),
        ("payoff quality", payoff, 3100),
        ("mechanism edges", edges, 15500),
        ("metrics", metrics, 2),
        ("split", split, 4),
    ]:
        if len(rows) != expected:
            errors.append(f"{label} expected {expected} rows, got {len(rows)}")
    if not 345 <= len(compressor) <= 496:
        errors.append(f"compressor expected between baseline 345 and full-slot 496 rows, got {len(compressor)}")
    if len(actions) != len(compressor):
        errors.append(f"actions expected to match compressor rows, got {len(actions)} vs {len(compressor)}")
    if len(trades) != len(actions):
        errors.append(f"trades expected to match action rows, got {len(trades)} vs {len(actions)}")
    if not 120 <= len(equity) <= 124:
        errors.append(f"equity expected 120-124 rows, got {len(equity)}")

    risk_buckets = {row["collapse_risk_bucket"] for row in collapse}
    for required in {"terminal_business_risk", "dilution_pressure", "theme_volatility", "ordinary_pass"}:
        if required not in risk_buckets:
            errors.append(f"missing collapse risk bucket: {required}")
    if not any(row["pre_entry_gate"] == "block" for row in collapse):
        errors.append("no pre-entry block rows")
    if not any(row["pre_entry_gate"] == "cap" for row in collapse):
        errors.append("no pre-entry cap rows")
    if not any(row["payoff_quality_bucket"] == "top3_payoff_candidate" for row in payoff):
        errors.append("no top3 payoff candidate rows")
    if not any(row["mechanism"] == "invalidates_entry" for row in edges):
        errors.append("no invalidates_entry L3 edges")
    if not any(row["selection_reason"] in {"blocked_baseline_replaced", "high_confidence_open_slot_filled_by_payoff_rank", "payoff_quality_upgrade"} for row in compressor):
        errors.append("candidate compressor did not perform any replacement or fill")
    if not any(row["runtime_action"] in {"reduce", "exit"} for row in actions):
        errors.append("no thesis-break reduce/exit runtime actions")
    if not failures:
        errors.append("expected failure attribution rows")

    policies = {row["policy_variant_id"] for row in metrics}
    for required in {"bad_trade_gate_top3_v1", "bad_trade_gate_top5_v1"}:
        if required not in policies:
            errors.append(f"missing metric policy: {required}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if closeout[0]["verdict"] != "l2_l4_bad_trade_gate_implemented_diagnostic_only":
        errors.append("closeout verdict mismatch")

    for name, rows in [
        ("collapse", collapse),
        ("payoff", payoff),
        ("edges", edges),
        ("compressor", compressor),
        ("actions", actions),
        ("trades", trades),
        ("metrics", metrics),
    ]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "The gate is implemented as one frozen policy family",
        "L2 now separates terminal/listing/dilution risk",
        "L5 now exits only on thesis-break evidence",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1698_1717_ERROR] {error}")
        return 1
    print("[TASK1698_1717_OK] L2/L4 bad-trade gate artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
