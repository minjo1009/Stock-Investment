from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2501_2510_kis_cost_basis_test"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def as_float(value: object) -> float:
    try:
        if value in {"", None, "nan"}:
            return 0.0
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return 0.0


def assert_no_assignment_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(
                row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                f"{name} row {idx} changed deployment status",
            )
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2501_2510_kis_cost_basis_test.md"
    decision = REPORT_DIR / "task_2510_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    contract = read_csv(OUT_DIR / "task2501_kis_cost_contract.csv")
    trades = read_csv(OUT_DIR / "task2502_kis_repriced_trades.csv")
    equity = read_csv(OUT_DIR / "task2503_kis_repriced_equity.csv")
    metrics = read_csv(OUT_DIR / "task2504_kis_repriced_metrics.csv")
    segments = read_csv(OUT_DIR / "task2505_kis_split_oos_metrics.csv")
    checks = read_csv(OUT_DIR / "task2506_kis_cost_acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task2510_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(len(contract) == 1, "contract row count mismatch")
    c = contract[0]
    require(as_float(c["buy_commission_rate"]) == 0.0025, "bad KIS buy commission")
    require(as_float(c["sell_commission_rate"]) == 0.0025, "bad KIS sell commission")
    require(abs(as_float(c["sell_sec_fee_rate"]) - 0.0000206) < 1e-12, "bad KIS SEC fee")
    require(abs(as_float(c["simple_roundtrip_bps"]) - 50.206) < 1e-9, "bad simple roundtrip bps")
    assert_status(contract, "contract")

    require(len(trades) == 124, f"expected 124 repriced trades, got {len(trades)}")
    assert_no_assignment_leak(trades, "trades")
    require(all(as_float(row["kis_total_cost"]) > 0 for row in trades), "KIS cost missing")
    require(sum(as_float(row["pnl_delta_vs_task2381"]) for row in trades) < 0, "KIS cost should reduce PnL")

    require(len(equity) >= 50, "equity rows too small")
    assert_no_assignment_leak(equity, "equity")
    require(len(metrics) == 1, "metrics row count mismatch")
    assert_status(metrics, "metrics")
    m = metrics[0]
    require(m["policy_variant_id"] == "kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1", "wrong policy id")
    require(as_float(m["final_equity"]) > 0, "missing final equity")
    require(as_float(m["cagr"]) > 0.30, "KIS CAGR should remain over 30% in this diagnostic")
    require(as_float(m["max_drawdown"]) < -0.30, "KIS MDD should expose drawdown failure")
    require(m["target_cagr_30pct_met"] == "1", "KIS CAGR target flag mismatch")
    require(m["target_mdd_minus30pct_met"] == "0", "KIS MDD target flag mismatch")
    require(m["joint_target_met"] == "0", "KIS joint target should fail on MDD")

    require(len(segments) == 3, "segments row count mismatch")
    assert_no_assignment_leak(segments, "segments")
    require(any(row["split_id"] == "OOS_2025_2026Q1" for row in segments), "missing OOS segment")
    require(len(checks) >= 5, "acceptance checks incomplete")
    assert_status(checks, "checks")
    require(any(row["check_name"] == "kis_full_period_mdd_minus30pct" and row["pass"] == "0" for row in checks), "missing MDD fail check")

    require(len(closeout) == 1, "closeout row count mismatch")
    assert_status(closeout, "closeout")
    co = closeout[0]
    require(co["verdict"] == "kis_cost_passes_return_but_fails_mdd_gate", "bad verdict")
    require(co["joint_target_met"] == "0", "closeout joint target should fail")
    require(len(manifest) >= 7, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2501, 2511)), "registry missing Task2501-2510 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("120. Task2501-Task2510" in op_state, "operating state missing Task2501-2510 line")

    print("[TASK2501_2510_KIS_COST_BASIS_TEST_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
