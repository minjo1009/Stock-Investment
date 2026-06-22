from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
REPORT = ROOT / "docs/reports/task_2191_2200_api_drawdown_sizing_guard/task_2191_2200_api_drawdown_sizing_guard.md"
DECISION = ROOT / "docs/reports/task_2191_2200_api_drawdown_sizing_guard/task_2191_2200_decision.csv"
AUTHORITY = "DIAGNOSTIC_API_DRAWDOWN_SIZING_GUARD_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_flags(rows: list[dict[str, str]], context: str) -> None:
    for row in rows:
        if "authority" in row:
            require(row["authority"] == AUTHORITY, f"{context} authority mismatch")
        if "assignment_uses_future_outcome" in row:
            require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
        if "outcome_used_for_assignment" in row:
            require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
        if "outcome_used_for_audit_only" in row:
            require(row["outcome_used_for_audit_only"] == "1", f"{context} outcome audit flag")


def main() -> None:
    contract = read_csv(OUT_DIR / "task2191_guard_contract.csv")
    guard = read_csv(OUT_DIR / "task2192_guard_decision_ledger.csv")
    summary = read_csv(OUT_DIR / "task2193_guard_action_summary.csv")
    trades = read_csv(OUT_DIR / "task2194_guard_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2195_guard_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2196_guard_replay_metrics.csv")
    closeout = read_csv(OUT_DIR / "task2200_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(contract) == 1, "expected one guard contract")
    require("future_drawdown_window" in contract[0]["forbidden_inputs"], "future window not forbidden")
    require(len(guard) > 0, "guard ledger missing")
    require(len(summary) > 0, "guard summary missing")
    require(len(trades) > 0, "trades missing")
    require(len(equity) > 0, "equity missing")
    require(len(metrics) == 3, "expected 3 policy metrics")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 8, "manifest incomplete")
    validate_flags(guard, "guard")
    validate_flags(trades, "trades")
    validate_flags(metrics, "metrics")
    validate_flags(closeout, "closeout")
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")
    row = closeout[0]
    require(row["verdict"] == "api_drawdown_sizing_guard_complete_diagnostic_only", "bad verdict")
    require(row["strategy_acceptance"] == "NOT_ACCEPTED", "closeout acceptance changed")
    require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "closeout deployment changed")
    require(row["real_capital"] == "FORBIDDEN", "closeout real capital changed")

    print("[TASK2191_2200_VALIDATE_OK] guard_health=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
