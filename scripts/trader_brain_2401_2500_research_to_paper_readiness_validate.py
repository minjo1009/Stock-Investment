from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2401_2500_research_to_paper_readiness"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    report = REPORT_DIR / "task_2401_2500_research_to_paper_readiness.md"
    decision = REPORT_DIR / "task_2500_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    attribution = read_csv(OUT_DIR / "task2401_result_attribution.csv")
    trade_decomp = read_csv(OUT_DIR / "task2402_trade_pnl_decomposition.csv")
    mdd = read_csv(OUT_DIR / "task2403_mdd_window_report.csv")
    split = read_csv(OUT_DIR / "task2411_split_oos_regime_metrics.csv")
    stress = read_csv(OUT_DIR / "task2412_cost_slippage_stress.csv")
    source_gate = read_csv(OUT_DIR / "task2421_source_time_gate_ledger.csv")
    source_gap = read_csv(OUT_DIR / "task2422_source_gap_summary.csv")
    freeze = read_csv(OUT_DIR / "task2431_policy_freeze_manifest.csv")
    overfit = read_csv(OUT_DIR / "task2432_overfit_ledger.csv")
    schema = read_csv(OUT_DIR / "task2441_adapter_input_schema.csv")
    adapter = read_csv(OUT_DIR / "task2442_dry_adapter_inputs.csv")
    paper_plan = read_csv(OUT_DIR / "task2451_paper_trading_run_plan.csv")
    safety_contract = read_csv(OUT_DIR / "task2461_execution_safety_gate_contract.csv")
    safety_eval = read_csv(OUT_DIR / "task2462_execution_safety_gate_eval.csv")
    journal_schema = read_csv(OUT_DIR / "task2471_monitoring_journal_schema.csv")
    journal = read_csv(OUT_DIR / "task2472_monitoring_journal_dry_run.csv")
    acceptance = read_csv(OUT_DIR / "task2481_acceptance_checklist.csv")
    dry_run = read_csv(OUT_DIR / "task2491_paper_mode_e2e_dry_run.csv")
    closeout = read_csv(OUT_DIR / "task2500_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("attribution", attribution),
        ("trade_decomp", trade_decomp),
        ("mdd", mdd),
        ("split", split),
        ("stress", stress),
        ("source_gate", source_gate),
        ("source_gap", source_gap),
        ("adapter", adapter),
        ("journal", journal),
    ]:
        assert_no_assignment_leak(rows, name)

    for name, rows in [
        ("freeze", freeze),
        ("adapter", adapter),
        ("acceptance", acceptance),
        ("closeout", closeout),
    ]:
        assert_status(rows, name)

    original_parity = read_csv(TASK2381 / "task2383_selected_116_parity_diff.csv")
    require(len(original_parity) == 116, "Task2381 parity baseline row count changed")
    require(sum(int(row.get("diff_count", "0")) for row in original_parity) == 0, "Task2381 parity baseline no longer zero diff")

    require(len(trade_decomp) == 124, f"expected 124 best-policy trade decompositions, got {len(trade_decomp)}")
    require(any(row["membership_bucket"] == "new_in_current" for row in attribution), "missing new_in_current attribution")
    require(len(split) >= 7, "split/regime rows too small")
    require(any(row["split_id"] == "OOS_2025_2026Q1" for row in split), "missing OOS split")
    require(len(stress) == 4, "cost stress rows should cover 0/25/50/100bps")
    require(len(source_gate) == 3100, f"source gate should cover 3100 rows, got {len(source_gate)}")
    require(sum(1 for row in source_gate if row["strict_raw_asof_complete"] == "1") == 0, "strict raw/asof unexpectedly complete")
    require(any(row["blocker_status"] == "DEPLOYMENT_BLOCKER" for row in source_gap), "missing source deployment blocker")

    require(len(freeze) == 1, "freeze manifest row count mismatch")
    frozen = freeze[0]
    require(frozen["frozen_policy_variant_id"] == "exit_chain_repaired_soft_boost_cap_top2_v1", "wrong frozen policy")
    for hash_field in ["config_hash", "feature_set_hash", "ranking_rule_hash", "sizing_rule_hash", "exit_rule_hash"]:
        require(len(frozen[hash_field]) == 64, f"bad hash field {hash_field}")
    require(len(overfit) >= 100, "overfit ledger should cover Task2191 onward registry rows")

    required_schema = {
        "symbol",
        "side",
        "entry_after",
        "max_position_size",
        "stop_rule",
        "reduce_rule",
        "exit_rule",
        "thesis_id",
        "source_ids",
        "source_time_status",
        "risk_budget",
        "no_trade_reason",
        "order_intent_id",
    }
    schema_fields = {row["field_name"] for row in schema}
    require(required_schema.issubset(schema_fields), "adapter schema missing required fields")
    require(len(adapter) == 124, f"adapter rows should equal 124 selected trades, got {len(adapter)}")
    require(all(row["broker_order_allowed"] == "0" for row in adapter), "adapter permits broker order")
    require(all(row["adapter_intent_state"].startswith("NO_TRADE") for row in adapter), "adapter should be source-blocked until strict PIT passes")

    require(len(paper_plan) >= 8, "paper plan incomplete")
    require(len(safety_contract) >= 10, "safety gate contract incomplete")
    require(len(safety_eval) == len(adapter), "safety eval row count mismatch")
    require(all(row["live_order_allowed"] == "0" for row in safety_eval), "safety eval permits live order")
    require(all(row["blocked"] == "1" for row in safety_eval), "safety eval should block dry rows in this source state")

    require(len(journal_schema) >= 15, "journal schema incomplete")
    require(len(journal) == len(adapter), "journal row count mismatch")
    require(all(row["paper_fill_state"] == "NOT_SENT" for row in journal), "paper fill should not be sent")

    require(len(acceptance) >= 8, "acceptance checklist incomplete")
    require(any(row["check_name"] == "pit_asof_audit_pass" and row["pass"] == "0" for row in acceptance), "PIT gate should fail")
    require(any(row["check_name"] == "paper_minimum_period_pass" and row["pass"] == "0" for row in acceptance), "paper minimum should fail")
    require(len(dry_run) == 1, "dry run closeout mismatch")
    require(dry_run[0]["live_order_created"] == "0", "dry run created live order")
    require(as_float(dry_run[0]["paper_order_intent_created"]) == 0, "dry run should not send paper orders before source/safety gates")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["acceptance_conclusion"] == "NO_GO", "closeout should remain NO_GO")
    require(co["live_order_created"] == "0", "closeout live order created")
    require(co["strict_raw_asof_complete_rows"] == "0", "closeout strict raw/asof should be 0")
    require(co["paper_order_intent_created"] == "0", "closeout should have zero paper order intent")
    require(len(manifest) >= 18, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2401, 2501)), "registry missing Task2401-2500 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("119. Task2401-Task2500" in op_state, "operating state missing Task2401-2500 line")

    print("[TASK2401_2500_RESEARCH_TO_PAPER_READINESS_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
