from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2511_2520_kis_mdd_decomposition"
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
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2511_2520_kis_mdd_decomposition.md"
    decision = REPORT_DIR / "task_2520_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    contract = read_csv(OUT_DIR / "task2511_kis_mdd_contract.csv")
    cost_components = read_csv(OUT_DIR / "task2511_cost_component_by_trade.csv")
    cost_summary = read_csv(OUT_DIR / "task2512_cost_component_summary.csv")
    path = read_csv(OUT_DIR / "task2512_peak_trough_path.csv")
    negative_tax = read_csv(OUT_DIR / "task2513_negative_return_trade_taxonomy.csv")
    contributors = read_csv(OUT_DIR / "task2513_mdd_window_trade_contributors.csv")
    dd_map = read_csv(OUT_DIR / "task2514_drawdown_window_map.csv")
    cost_drag = read_csv(OUT_DIR / "task2514_cost_drag_decomposition.csv")
    dd_trade_attr = read_csv(OUT_DIR / "task2515_drawdown_window_trade_attribution.csv")
    monthly = read_csv(OUT_DIR / "task2515_base_vs_kis_monthly_delta.csv")
    symbol_conc = read_csv(OUT_DIR / "task2516_symbol_concentration_attribution.csv")
    taxonomy = read_csv(OUT_DIR / "task2516_failure_taxonomy.csv")
    split_bridge = read_csv(OUT_DIR / "task2517_split_cost_drawdown_bridge.csv")
    repair = read_csv(OUT_DIR / "task2517_repair_candidate_queue.csv")
    subagents = read_csv(OUT_DIR / "task2518_subagent_packets.csv")
    acceptance = read_csv(OUT_DIR / "task2518_acceptance_checks.csv")
    governance = read_csv(OUT_DIR / "task2519_governance_health_checks.csv")
    closeout = read_csv(OUT_DIR / "task2520_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("contract", contract),
        ("cost_components", cost_components),
        ("path", path),
        ("negative_tax", negative_tax),
        ("contributors", contributors),
        ("dd_map", dd_map),
        ("cost_drag", cost_drag),
        ("dd_trade_attr", dd_trade_attr),
        ("monthly", monthly),
        ("symbol_conc", symbol_conc),
        ("taxonomy", taxonomy),
        ("split_bridge", split_bridge),
        ("repair", repair),
        ("closeout", closeout),
    ]:
        assert_no_assignment_leak(rows, name)
    for name, rows in [("contract", contract), ("acceptance", acceptance), ("closeout", closeout)]:
        assert_status(rows, name)

    require(len(contract) == 1, "contract row count mismatch")
    c = contract[0]
    require(c["strategy_tuning_performed"] == "0", "strategy tuning should not be performed")
    require(as_float(c["kis_max_drawdown"]) < -0.30, "KIS MDD failure should be present")
    require(as_float(c["base_max_drawdown"]) > -0.30, "base MDD should remain inside gate")
    require(len(cost_components) == 124, "cost component should cover 124 trades")
    require(sum(1 for row in cost_components if row["cost_flipped_positive_to_negative"] == "1") == 0, "unexpected positive-to-negative flip count")

    overall = next(row for row in cost_summary if row["group_type"] == "overall")
    require(as_float(overall["sec_fee_share"]) < 0.01, "SEC fee share should be small and separated")
    require(len(negative_tax) == 49, f"expected 49 KIS negative trades, got {len(negative_tax)}")
    require(all(row["negative_type"] == "already_negative_before_kis_cost" for row in negative_tax), "negative taxonomy should not claim cost flips")
    require(any(row["drawdown_lte_minus20_flag"] == "1" for row in dd_map), "drawdown window map missing <= -20 months")
    require(len(dd_trade_attr) == 22, f"expected 22 drawdown-window trades, got {len(dd_trade_attr)}")
    require(sum(1 for row in dd_trade_attr if row["kis_negative_trade_flag"] == "1") == 16, "expected 16 negative trades in <= -20 drawdown window")
    require(any(row["symbol"] == "CC" and as_float(row["kis_pnl_sum"]) < -200 for row in symbol_conc), "CC loss concentration missing")
    require(any(row["split_id"] == "IS_2021_2023" and as_float(row["max_drawdown_in_split"]) < -0.30 for row in split_bridge), "IS split MDD failure missing")
    require(len(taxonomy) >= 3, "taxonomy too small")
    require(len(repair) >= 3, "repair queue too small")
    require(len(subagents) == 3, "subagent packet rows mismatch")
    require(all(row["write_scope"] == "read-only" for row in subagents), "subagents should be read-only in this task")
    require(all(row["pass"] == "1" for row in acceptance), "acceptance checks should pass for decomposition completeness")
    require(all(row["pass"] == "1" for row in governance), "governance health checks should pass")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "kis_mdd_gate_failure_is_incremental_cost_drag_on_top_of_loss_cluster", "bad verdict")
    require(co["gate_failure_primary_cause"] == "incremental_kis_cost_drag", "bad gate failure cause")
    require(co["economic_loss_primary_cause"] == "underlying_drawdown_window_trade_losses", "bad economic loss cause")
    require(as_float(co["without_incremental_drag_mdd"]) > -0.30, "without incremental drag should stay inside MDD gate")
    require(co["strategy_tuning_performed"] == "0", "closeout should not tune strategy")
    require(len(manifest) >= 18, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2511, 2521)), "registry missing Task2511-2520 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("121. Task2511-Task2520" in op_state, "operating state missing Task2511-2520 line")
    print("[TASK2511_2520_KIS_MDD_DECOMPOSITION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
