from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2181_2190_api_overlay_decomposition"
REPORT = ROOT / "docs/reports/task_2181_2190_api_overlay_decomposition/task_2181_2190_api_overlay_decomposition.md"
DECISION = ROOT / "docs/reports/task_2181_2190_api_overlay_decomposition/task_2181_2190_decision.csv"
AUTHORITY = "DIAGNOSTIC_API_OVERLAY_DECOMPOSITION_ONLY"


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
    changes = read_csv(OUT_DIR / "task2181_api_overlay_trade_change_ledger.csv")
    monthly = read_csv(OUT_DIR / "task2182_monthly_equity_delta.csv")
    dd_trades = read_csv(OUT_DIR / "task2183_mdd_window_trade_ledger.csv")
    dd_summary = read_csv(OUT_DIR / "task2184_mdd_window_summary.csv")
    state_agg = read_csv(OUT_DIR / "task2185_pnl_delta_by_api_state.csv")
    symbol_agg = read_csv(OUT_DIR / "task2186_pnl_delta_by_symbol.csv")
    status_agg = read_csv(OUT_DIR / "task2187_pnl_delta_by_change_status.csv")
    closeout = read_csv(OUT_DIR / "task2190_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(changes) >= 116, "change ledger too small")
    require(len(monthly) > 0, "monthly delta missing")
    require(len(dd_trades) > 0, "drawdown trade ledger missing")
    require(len(dd_summary) == 2, "expected new and previous drawdown summary")
    require(len(state_agg) > 0, "state aggregation missing")
    require(len(symbol_agg) > 0, "symbol aggregation missing")
    require(len(status_agg) >= 1, "status aggregation missing")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 9, "manifest incomplete")
    validate_flags(changes, "changes")
    validate_flags(closeout, "closeout")
    for row in closeout:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")
        require(row["verdict"] == "api_overlay_decomposition_complete_diagnostic_only", "bad verdict")

    print("[TASK2181_2190_VALIDATE_OK] decomposition_health=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
