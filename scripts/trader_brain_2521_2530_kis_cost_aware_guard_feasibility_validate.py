from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2521_2530_kis_cost_aware_guard_feasibility"
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
        require(row.get("used_as_source_of_truth_for_pnl", "0") == "0", f"{name} row {idx} uses research source as PnL truth")
        require(row.get("source_of_truth_for_pnl", "0") == "0", f"{name} row {idx} uses expert source as PnL truth")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2521_2530_kis_cost_aware_guard_feasibility.md"
    decision = REPORT_DIR / "task_2530_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    sources = read_csv(OUT_DIR / "task2521_recent_source_context.csv")
    experts = read_csv(OUT_DIR / "task2522_expert_review_feedback.csv")
    variants = read_csv(OUT_DIR / "task2523_preregistered_guard_variants.csv")
    guard_rows = read_csv(OUT_DIR / "task2524_guard_trade_rows.csv")
    equity_rows = read_csv(OUT_DIR / "task2525_guard_equity_paths.csv")
    metrics = read_csv(OUT_DIR / "task2526_guard_metrics.csv")
    feasibility = read_csv(OUT_DIR / "task2527_feasibility_matrix.csv")
    acceptance = read_csv(OUT_DIR / "task2528_acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task2530_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    decision_rows = read_csv(decision)

    for name, rows in [
        ("sources", sources),
        ("experts", experts),
        ("variants", variants),
        ("guard_rows", guard_rows),
        ("equity_rows", equity_rows),
        ("metrics", metrics),
        ("feasibility", feasibility),
        ("acceptance", acceptance),
        ("closeout", closeout),
    ]:
        assert_no_assignment_leak(rows, name)
    for name, rows in [("variants", variants), ("metrics", metrics), ("acceptance", acceptance), ("closeout", closeout)]:
        assert_status(rows, name)

    require(len(sources) >= 4, "recent source context too small")
    require(all(row["used_as_design_context_only"] == "1" for row in sources), "sources should be design-context only")
    require(any(row["date_basis"].startswith("2024") for row in sources), "missing 2024 recent source")
    require(any(row["date_basis"].startswith("2025") for row in sources), "missing 2025 recent source")
    require(len(experts) >= 3, "expert review too small")
    require(all(row["gpt_or_expert_review_only"] == "1" for row in experts), "expert rows should be review-only")

    variant_ids = {row["guard_variant_id"] for row in variants}
    require("kis_guard_none_baseline_v1" in variant_ids, "missing baseline variant")
    require(len(variant_ids) >= 8, "expected baseline plus cost and portfolio-stress guard variants")
    require(all(row["uses_symbol_specific_hindsight"] == "0" for row in variants), "symbol-specific hindsight guard found")
    require(all(row["uses_future_outcome_for_assignment"] == "0" for row in variants), "future-outcome guard found")
    require(all("symbol" not in row["eligible_condition"] for row in variants), "symbol condition should not be used")
    require(any("monthly_trade_count" in row["eligible_condition"] for row in variants), "missing monthly trade-count guard")
    require(any("cost_rate" in row["eligible_condition"] for row in variants), "missing cost-rate guard")
    require(any(row["eligible_condition"] == "portfolio_stress_all_intents" for row in variants), "missing portfolio-stress guard")

    metrics_by_id = {row["guard_variant_id"]: row for row in metrics}
    require(variant_ids == set(metrics_by_id), "metrics variant coverage mismatch")
    baseline = metrics_by_id["kis_guard_none_baseline_v1"]
    require(abs(as_float(baseline["final_equity"]) - 6016.930785) < 0.02, "baseline final equity mismatch")
    require(abs(as_float(baseline["max_drawdown"]) - (-0.30814728)) < 0.0002, "baseline MDD mismatch")
    require(baseline["guard_triggered_rows"] == "0", "baseline guard should not trigger")
    require(
        any(int(row["guard_triggered_rows"]) > 0 for row in metrics if row["guard_variant_id"] != "kis_guard_none_baseline_v1"),
        "at least one non-baseline guard should trigger",
    )

    require({row["guard_variant_id"] for row in guard_rows} == variant_ids, "guard rows variant coverage mismatch")
    require({row["guard_variant_id"] for row in equity_rows} == variant_ids, "equity rows variant coverage mismatch")
    for row in guard_rows:
        require(as_float(row["trade_cost_rate"]) >= 0.0, "negative trade cost rate")
        require(as_float(row["monthly_cost_rate"]) >= 0.0, "negative monthly cost rate")
        require(int(row["monthly_trade_count"]) >= 1, "invalid monthly trade count")

    success = any(row["return_preserving_mdd_success"] == "1" for row in metrics if row["guard_variant_id"] != "kis_guard_none_baseline_v1")
    co = closeout[0]
    require(len(closeout) == 1, "closeout row count mismatch")
    require(closeout == decision_rows, "decision and closeout should match")
    if success:
        require(co["verdict"] == "return_preserving_mdd_repair_possible_in_diagnostic_replay", "success verdict mismatch")
        require(co["return_preserving_mdd_success"] == "1", "success closeout mismatch")
    else:
        require(co["verdict"] == "return_preserving_mdd_repair_not_found_in_preregistered_variants", "failure verdict mismatch")
        require(co["return_preserving_mdd_success"] == "0", "failure closeout mismatch")
    best = metrics_by_id[co["best_guard_variant_id"]]
    require(abs(as_float(best["final_equity"]) - as_float(co["best_final_equity"])) < 0.0001, "closeout final mismatch")
    require(abs(as_float(best["max_drawdown"]) - as_float(co["best_max_drawdown"])) < 0.000001, "closeout MDD mismatch")
    require(co["selector_changed"] == "0", "selector should not change")
    require(co["strategy_tuning_performed"] == "0", "strategy tuning flag should remain zero for diagnostic guard replay")

    require(len(feasibility) == len(metrics), "feasibility row count mismatch")
    require(len(acceptance) >= 4, "acceptance checks too small")
    require(len(manifest) >= 10, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2521, 2531)), "registry missing Task2521-2530 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("121. Task2511-Task2520 decomposed the KIS-cost MDD failure: base MDD -0.28210924" in op_state, "operating state missing corrected Task2511 line")
    require("122. Task2521-Task2530" in op_state, "operating state missing Task2521-2530 line")

    print("[TASK2521_2530_KIS_COST_AWARE_GUARD_FEASIBILITY_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
