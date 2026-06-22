from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2921_2940_l2_l3_mdd_attribution_pack"
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
    report = REPORT_DIR / "task_2921_2940_l2_l3_mdd_attribution_pack.md"
    decision = REPORT_DIR / "task_2940_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2921_scope_freeze.csv")
    join = read_csv(OUT_DIR / "task2922_input_join_audit.csv")
    l2 = read_csv(OUT_DIR / "task2923_mdd_trade_l2_attribution.csv")
    l3 = read_csv(OUT_DIR / "task2924_mdd_trade_l3_edges.csv")
    losses = read_csv(OUT_DIR / "task2925_loss_by_sec_regime_state.csv")
    rank = read_csv(OUT_DIR / "task2926_rank_impact_audit.csv")
    survival = read_csv(OUT_DIR / "task2927_top2_selection_survival.csv")
    boundary = read_csv(OUT_DIR / "task2928_source_gap_proxy_boundary.csv")
    avoid = read_csv(OUT_DIR / "task2929_avoidable_unavoidable_audit.csv")
    closeout = read_csv(OUT_DIR / "task2940_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("join", join),
        ("l2", l2),
        ("l3", l3),
        ("losses", losses),
        ("rank", rank),
        ("survival", survival),
        ("boundary", boundary),
        ("avoid", avoid),
        ("closeout", closeout),
    ]:
        assert_no_assignment_leak(rows, name)

    for name, rows in [("scope", scope), ("closeout", closeout)]:
        assert_status(rows, name)

    require(len(scope) == 1, "scope row count mismatch")
    s = scope[0]
    require(s["replay_performed"] == "0", "scope should not replay")
    require(s["selector_tuning_performed"] == "0", "scope should not tune selector")
    require(s["sizing_tuning_performed"] == "0", "scope should not tune sizing")
    require(s["exit_tuning_performed"] == "0", "scope should not tune exit")
    require(int(s["mdd_trade_count"]) == 14, f"expected 14 MDD trades, got {s['mdd_trade_count']}")
    require(s["guard_context_use"] == "context_only_not_logic_input", "guard context should be context-only")

    require(len(join) == 14, f"expected 14 join rows, got {len(join)}")
    require(sum(1 for row in join if row["l2_match"] == "1") == 14, "L2 should match all MDD trades")
    require(sum(1 for row in join if row["rank_match"] == "1") == 14, "rank should match all MDD trades")
    require(sum(1 for row in join if row["kis_trade_match"] == "1") == 14, "KIS trade should match all MDD trades")
    require(sum(int(row["l3_edge_count"]) for row in join) == 28, "expected 28 joined L3 edges")

    require(len(l2) == 14, f"expected 14 L2 rows, got {len(l2)}")
    require(len(l3) == 28, f"expected 28 L3 edges, got {len(l3)}")
    require(len(rank) == 14, "rank audit should cover all MDD trades")
    require(len(survival) == 14, "survival audit should cover all MDD trades")
    require(len(boundary) == 14, "source boundary audit should cover all MDD trades")
    require(len(avoid) == 14, "avoidability audit should cover all MDD trades")
    require(len(losses) >= 1, "loss grouping too small")

    require(any(as_float(row["kis_pnl"]) < 0 for row in l2), "expected at least one negative trade")
    require(any(row["risk_direction"] == "loss_survived_despite_l2_l3_risk_penalty" for row in l2), "missing risk-penalty-survival loss diagnostic")
    require(any(row["rank_effect_bucket"] == "source_rank_top2_loss" for row in rank), "missing top2 loss rank diagnostic")
    require(any(row["survival_read"] == "bad_trade_would_survive_l2_l3_top2" for row in survival), "missing top2 bad-trade survival read")
    require(
        any(row["avoidability_bucket"] in {"not_flagged_by_current_l2_l3", "l2_l3_signal_seen_but_not_invalidated", "l2_l3_regime_warning_seen_but_not_capped"} for row in avoid),
        "missing L2/L3 blind spot bucket",
    )
    require(all(row["allowed_use"] == "diagnostic_rule_design_only_not_assignment" for row in avoid), "avoidability rows must be diagnostic-only")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "l2_l3_mdd_attribution_pack_completed_diagnostic_only", "bad closeout verdict")
    require(int(co["mdd_trade_count"]) == 14, "closeout MDD trade count mismatch")
    require(int(co["l2_match_count"]) == 14, "closeout L2 match mismatch")
    require(int(co["l3_edge_count"]) == 28, "closeout L3 edge mismatch")
    require(co["replay_performed"] == "0", "closeout should not replay")
    require(co["selector_tuning_performed"] == "0", "closeout should not tune selector")
    require(int(co["current_l2_l3_blind_spot_count"]) >= 1, "blind spot count should be positive")

    require(len(manifest) >= 10, "manifest too small")
    manifest_paths = {row["relative_path"] for row in manifest}
    require("task2940_closeout.csv" in manifest_paths, "manifest missing closeout")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2921, 2941)), "registry missing Task2921-2940 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("143. Task2921-Task2940" in op_state, "operating state missing Task2921-2940 line")
    print("[TASK2921_2940_L2_L3_MDD_ATTRIBUTION_PACK_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
