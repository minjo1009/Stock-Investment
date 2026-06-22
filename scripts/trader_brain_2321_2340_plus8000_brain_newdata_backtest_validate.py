from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest"
REPORT = ROOT / "docs/reports/task_2321_2340_plus8000_brain_newdata_backtest/task_2321_2340_plus8000_brain_newdata_backtest.md"
DECISION = ROOT / "docs/reports/task_2321_2340_plus8000_brain_newdata_backtest/task_2321_2340_decision.csv"
AUTHORITY = "DIAGNOSTIC_PLUS8000_BRAIN_NEWDATA_BACKTEST_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_flags(rows: list[dict[str, str]], context: str, audit_expected: str | None = None) -> None:
    for row in rows:
        if "authority" in row:
            require(row["authority"] == AUTHORITY, f"{context} authority mismatch")
        if "assignment_uses_future_outcome" in row:
            require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
        if "outcome_used_for_assignment" in row:
            require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
        if audit_expected is not None and "outcome_used_for_audit_only" in row:
            require(row["outcome_used_for_audit_only"] == audit_expected, f"{context} audit flag")


def main() -> None:
    contract = read_csv(OUT_DIR / "task2321_experiment_contract.csv")
    cards = read_csv(OUT_DIR / "task2322_newdata_l4_cards.csv")
    decisions = read_csv(OUT_DIR / "task2323_newdata_l5_decisions.csv")
    audit = read_csv(OUT_DIR / "task2324_overlay_audit.csv")
    guards = read_csv(OUT_DIR / "task2325_guard_rows.csv")
    trades = read_csv(OUT_DIR / "task2326_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2327_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2328_replay_metrics.csv")
    coverage = read_csv(OUT_DIR / "task2329_overlay_coverage.csv")
    comparison = read_csv(OUT_DIR / "task2330_comparison_matrix.csv")
    closeout = read_csv(OUT_DIR / "task2340_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(contract) == 1, "contract missing")
    require(contract[0]["same_selector_stack_as_plus8000"] == "1", "selector stack not fixed")
    require(contract[0]["same_replay_capital_path_as_plus8000"] == "1", "capital path not fixed")
    require(contract[0]["strict_raw_asof_complete"] == "0", "strict raw/asof overclaimed")
    require(len(cards) == len(audit), "card/audit row mismatch")
    require(len(decisions) == len(audit), "decision/audit row mismatch")
    require(len(audit) == 377, "expected Task1991 decision rows")
    require(len(metrics) == 3, "expected three +8000 guard policies")
    require(len(comparison) >= 6, "comparison matrix incomplete")
    require(len(trades) == 348, "expected three variants times 116 trades")
    require(len(guards) > 0, "guard rows missing")
    require(len(coverage) > 0, "coverage rows missing")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 10, "manifest incomplete")

    validate_flags(cards, "cards")
    validate_flags(decisions, "decisions")
    validate_flags(audit, "audit")
    validate_flags(trades, "trades", "1")
    validate_flags(metrics, "metrics", "1")
    validate_flags(closeout, "closeout", "1")

    require(closeout[0]["verdict"] == "plus8000_brain_newdata_overlay_backtest_complete_diagnostic_only", "bad verdict")
    require(closeout[0]["same_selector_stack_as_plus8000"] == "1", "closeout selector stack mismatch")
    require(closeout[0]["same_replay_capital_path_as_plus8000"] == "1", "closeout capital path mismatch")
    require(closeout[0]["strict_raw_asof_complete"] == "0", "closeout raw/asof overclaim")
    for row in metrics + closeout:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")

    changed_rows = int(closeout[0]["overlay_changed_rows"])
    require(changed_rows > 0, "new data did not affect any overlay row")
    require(any(row["metric"] == "newdata_supportive_boost" for row in coverage), "supportive boost coverage missing")
    require(any(row["metric"] == "api_proxy_supportive" for row in coverage), "proxy supportive state missing")

    print("[TASK2321_2340_VALIDATE_OK] plus8000_brain=pass newdata_overlay=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
