from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2961_2980_frozen_policy_l4_challenger_compare_plan"
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
    report = REPORT_DIR / "task_2961_2980_frozen_policy_l4_challenger_compare_plan.md"
    decision = REPORT_DIR / "task_2980_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2961_scope_freeze.csv")
    freezes = read_csv(OUT_DIR / "task2962_policy_freeze_registry.csv")
    hashes = read_csv(OUT_DIR / "task2963_hash_ledger.csv")
    same_gate = read_csv(OUT_DIR / "task2964_same_experiment_gate.csv")
    split_plan = read_csv(OUT_DIR / "task2965_split_oos_replay_plan.csv")
    blockers = read_csv(OUT_DIR / "task2966_replay_blocker_checklist.csv")
    compare_manifest = read_csv(OUT_DIR / "task2967_comparison_manifest.csv")
    subagents = read_csv(OUT_DIR / "task2968_subagent_review_packets.csv")
    checks = read_csv(OUT_DIR / "task2969_acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task2980_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("freezes", freezes),
        ("hashes", hashes),
        ("same_gate", same_gate),
        ("split_plan", split_plan),
        ("blockers", blockers),
        ("compare_manifest", compare_manifest),
        ("subagents", subagents),
        ("checks", checks),
        ("closeout", closeout),
    ]:
        assert_no_assignment_leak(rows, name)

    assert_status(scope, "scope")
    assert_status(closeout, "closeout")

    require(len(scope) == 1, "scope row count mismatch")
    s = scope[0]
    require(s["replay_performed"] == "0", "scope should not replay")
    require(s["performance_compared"] == "0", "scope should not compare performance")
    require(s["selector_tuning_performed"] == "0", "scope should not tune selector")
    require(s["sizing_tuning_performed"] == "0", "scope should not tune sizing")
    require(s["exit_tuning_performed"] == "0", "scope should not tune exit")
    require(s["paper_order_intents_created"] == "0", "scope should not create paper orders")
    require(s["live_orders_created"] == "0", "scope should not create live orders")
    require(int(s["l4_assignment_rows"]) == 3100, "scope should reference full L4 assignment")

    require(len(freezes) == 2, "expected baseline/challenger freeze rows")
    roles = {row["policy_role"] for row in freezes}
    require({"frozen_baseline", "l4_challenger"}.issubset(roles), f"bad freeze roles: {roles}")
    require(all(row["config_hash"] and len(row["config_hash"]) == 64 for row in freezes), "config hashes must be sha256")
    require(all(row["feature_set_hash"] and len(row["feature_set_hash"]) == 64 for row in freezes), "feature hashes must be sha256")
    require(all(row["policy_change_allowed"] == "0" for row in freezes), "frozen policies should not allow changes")

    require(len(hashes) >= 10, "hash ledger too small")
    require(all(row["exists"] == "1" for row in hashes), "all hash ledger artifacts must exist")
    require(all(row["sha256"] and len(row["sha256"]) == 64 for row in hashes), "hash ledger sha missing")
    require(all(row["frozen_for_compare"] == "1" for row in hashes), "hash rows must be frozen for compare")

    statuses = {row["gate_status"] for row in same_gate}
    require("NOT_SAME_EXPERIMENT" in statuses, "same-experiment gate must classify challenger as not same experiment")
    require("BLOCKED" in statuses, "performance discussion must be blocked")
    require(all(row["performance_compare_allowed_now"] == "0" for row in same_gate), "same gate should block performance compare")

    require(len(split_plan) >= 6, "split/OOS plan too small")
    split_ids = {row["split_id"] for row in split_plan}
    require({"IS_2021_2023", "VALIDATION_2024", "OOS_2025_2026Q1"}.issubset(split_ids), "missing core split rows")
    require(all(row["replay_executed"] == "0" for row in split_plan), "split plan must not execute replay")
    require(all(row["performance_compare_allowed_now"] == "0" for row in split_plan), "split plan must block current performance compare")
    require(all(row["cost_slippage_model"] == "KIS_cost_basis_required" for row in split_plan), "KIS cost model must be declared")

    strict = next((row for row in blockers if row["blocker_name"] == "strict_raw_asof_complete"), None)
    require(strict is not None, "missing strict raw/as-of blocker")
    require(strict["status"] in {"BLOCKED", "PASS"}, "bad strict as-of blocker status")
    require(any(row["blocker_name"] == "no_paper_or_live_orders" and row["status"] == "PASS" for row in blockers), "order blocker missing")

    require(any(row["manifest_name"] == "same_experiment_class" and row["value"] == "not_same_experiment" for row in compare_manifest), "comparison class missing")
    require(len(subagents) == 3, "subagent review packet count mismatch")
    require(all(row["review_only"] == "1" and row["write_scope"] == "read-only" for row in subagents), "subagent packets should be read-only")
    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "frozen_policy_l4_challenger_compare_plan_completed_no_replay", "bad closeout verdict")
    require(co["performance_compare_allowed_now"] == "0", "closeout should block performance compare")
    require(co["replay_performed"] == "0", "closeout should not replay")
    require(co["selector_tuning_performed"] == "0", "closeout should not tune selector")
    require(co["sizing_tuning_performed"] == "0", "closeout should not tune sizing")
    require(co["exit_tuning_performed"] == "0", "closeout should not tune exit")
    require(co["paper_order_intents_created"] == "0", "closeout should not create paper orders")
    require(co["live_orders_created"] == "0", "closeout should not create live orders")
    require(co["all_acceptance_checks_pass"] == "1", "closeout acceptance checks not pass")

    manifest_paths = {row["relative_path"] for row in manifest}
    require("task2962_policy_freeze_registry.csv" in manifest_paths, "manifest missing freeze registry")
    require("task2965_split_oos_replay_plan.csv" in manifest_paths, "manifest missing split plan")
    require("task2980_closeout.csv" in manifest_paths, "manifest missing closeout")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2961, 2981)), "registry missing Task2961-2980 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("145. Task2961-Task2980" in op_state, "operating state missing Task2961-2980 line")
    print("[TASK2961_2980_FROZEN_POLICY_L4_CHALLENGER_COMPARE_PLAN_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
