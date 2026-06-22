from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2581_2600_source_integrated_selector_diagnostic"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def iter_csv(path: Path):
    require(path.exists(), f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan", "."}:
            return default
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def assert_flags(row: dict[str, str], context: str, audit_allowed: bool = False) -> None:
    require(row.get("missing_source_is_negative", "0") == "0", f"{context} treats missing source as negative")
    require(row.get("assignment_uses_future_outcome", "0") == "0", f"{context} uses future outcome")
    require(row.get("outcome_used_for_assignment", "0") == "0", f"{context} uses outcome for assignment")
    if not audit_allowed:
        for forbidden in ["audit_net_return", "pnl", "forward_return", "actual_exit_date", "runtime_action"]:
            require(forbidden not in row, f"{context} contains audit/outcome field in assignment table: {forbidden}")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2581_2600_source_integrated_selector_diagnostic.md"
    decision = REPORT_DIR / "task_2600_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    plan = read_csv(OUT_DIR / "task2581_task_plan.csv")
    contract = read_csv(OUT_DIR / "task2581_selector_diagnostic_contract.csv")
    join = read_csv(OUT_DIR / "task2582_source_join_audit.csv")
    regime = read_csv(OUT_DIR / "task2583_liquidity_rates_regime_by_decision.csv")
    l2 = read_csv(OUT_DIR / "task2584_l2_source_feature_bridge.csv")
    l3 = read_csv(OUT_DIR / "task2585_l3_source_interaction_edges.csv")
    ranks = read_csv(OUT_DIR / "task2586_source_integrated_selector_ranks.csv")
    selection = read_csv(OUT_DIR / "task2587_selector_only_selection_rows.csv")
    metrics = read_csv(OUT_DIR / "task2588_selector_only_audit_metrics.csv")
    overlaps = read_csv(OUT_DIR / "task2589_selection_overlap.csv")
    attribution = read_csv(OUT_DIR / "task2590_change_attribution.csv")
    audit = read_csv(OUT_DIR / "task2591_leakage_pit_audit.csv")
    gaps = read_csv(OUT_DIR / "task2592_source_gap_and_proxy_boundary.csv")
    subagents = read_csv(OUT_DIR / "task2593_subagent_packets.csv")
    closeout = read_csv(OUT_DIR / "task2600_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("plan", plan),
        ("contract", contract),
        ("join", join),
        ("regime", regime),
        ("l2", l2),
        ("l3", l3),
        ("ranks", ranks),
        ("audit", audit),
        ("gaps", gaps),
        ("subagents", subagents),
        ("closeout", closeout),
    ]:
        require(rows or name == "gaps", f"{name} unexpectedly empty")
        for idx, row in enumerate(rows, start=1):
            assert_flags(row, f"{name} row {idx}", audit_allowed=False)
    for name, rows in [("selection", selection), ("metrics", metrics), ("overlaps", overlaps), ("attribution", attribution)]:
        require(rows, f"{name} unexpectedly empty")
        for idx, row in enumerate(rows, start=1):
            assert_flags(row, f"{name} row {idx}", audit_allowed=True)
            require(row.get("outcome_used_for_audit_only", "1") == "1", f"{name} row {idx} missing audit-only flag")

    assert_status(contract, "contract")
    assert_status(closeout, "closeout")
    require(len(plan) == 20, "Task2581-2600 plan row mismatch")
    require(len(contract) == 1, "contract row mismatch")
    c = contract[0]
    require(c["candidate_rows"] == "3100", "contract candidate count mismatch")
    require(c["selector_only"] == "1", "contract should be selector-only")
    require(c["capital_replay_run"] == "0", "contract should not run replay")

    require(len(join) == 2, "join audit row mismatch")
    sec = next(row for row in join if row["input"] == "sec_financing_dilution")
    liq = next(row for row in join if row["input"] == "liquidity_rates_regime")
    require(sec["strict_join_rows"] == "3094" and sec["gap_rows"] == "6", "SEC join counts mismatch")
    require(liq["strict_join_rows"] == "3100" and liq["gap_rows"] == "0", "liquidity join counts mismatch")

    require(len(regime) == 62, "regime row count mismatch")
    require(all(row["strict_gate_pass"] == "1" for row in regime), "regime rows must be strict")
    require(any(row["regime_state"] == "liquidity_rates_stress" for row in regime), "expected at least one stress regime")
    require(any(row["regime_state"] == "liquidity_rates_tailwind_or_benign" for row in regime), "expected at least one benign regime")

    require(len(l2) == 3100, "L2 bridge row count mismatch")
    require(len({row["trade_spec_id"] for row in l2}) == 3100, "L2 duplicate trade spec")
    require(any(row["sec_source_packet_ids_sample"] for row in l2), "L2 missing SEC packet lineage")
    require(any(row["sec_event_family_counts"] != "{}" for row in l2), "L2 missing SEC family counts")
    for idx, row in enumerate(l2, start=1):
        if row["sec_available_to_brain_ts_max"]:
            available = parse_ts(row["sec_available_to_brain_ts_max"])
            decision_ts = parse_ts(row["decision_asof_ts"])
            require(available is not None and decision_ts is not None, f"L2 row {idx} bad timestamp")
            require(available <= decision_ts, f"L2 row {idx} has future SEC source")
        require(row["strict_liquidity_rates_gate_pass"] == "1", f"L2 row {idx} liquidity gate not strict")
        if row["strict_sec_gate_pass"] == "0":
            require(row["sec_state"] == "sec_financing_source_gap_neutral", f"L2 row {idx} SEC gap not neutral")
            require(to_float(row["sec_selector_score"]) == 0.0, f"L2 row {idx} SEC gap scored")

    require(len(l3) >= 6200, "L3 edge count too small")
    require(all(row["strict_gate_pass"] == "1" for row in l3), "L3 edges must be strict")
    require(any(row["edge_type"] == "sec_x_regime_interaction_modifies_selector" for row in l3), "missing interaction edges")

    require(len(ranks) == 3100, "rank row count mismatch")
    by_decision: dict[str, list[dict[str, str]]] = {}
    for row in ranks:
        by_decision.setdefault(row["decision_asof_ts"], []).append(row)
    require(len(by_decision) == 62, "rank decision count mismatch")
    for decision, rows in by_decision.items():
        base_ranks = sorted(int(row["base_rank"]) for row in rows)
        adj_ranks = sorted(int(row["source_integrated_rank"]) for row in rows)
        expected = list(range(1, len(rows) + 1))
        require(base_ranks == expected, f"base rank sequence broken for {decision}")
        require(adj_ranks == expected, f"adjusted rank sequence broken for {decision}")

    require(len(selection) == 2480, "selector-only row count mismatch")
    require({row["top_n"] for row in selection} == {"2", "3", "5", "10"}, "selector topN mismatch")
    require(all(row["capital_replay_run"] == "0" for row in selection), "selection rows should not replay")
    require(len(metrics) == 8, "metrics row count mismatch")
    metric_by_variant = {row["diagnostic_variant_id"]: row for row in metrics}
    require(metric_by_variant["base_top2_selector_only_v1"]["selected_rows"] == "124", "base top2 row count mismatch")
    require(metric_by_variant["source_integrated_top2_selector_only_v1"]["selected_rows"] == "124", "source top2 row count mismatch")
    require(to_float(metric_by_variant["source_integrated_top10_selector_only_v1"]["avg_audit_net_return"]) > to_float(metric_by_variant["base_top10_selector_only_v1"]["avg_audit_net_return"]), "top10 diagnostic should show broad-filter improvement")
    require(to_float(metric_by_variant["source_integrated_top2_selector_only_v1"]["avg_audit_net_return"]) < to_float(metric_by_variant["base_top2_selector_only_v1"]["avg_audit_net_return"]), "top2 diagnostic should not be overstated as improvement")

    require(len(overlaps) == 248, "overlap row count mismatch")
    require(sum(int(row["added_count"]) for row in overlaps if row["top_n"] == "2") == 9, "top2 added mismatch")
    require(sum(int(row["dropped_count"]) for row in overlaps if row["top_n"] == "2") == 9, "top2 dropped mismatch")
    require(len(attribution) >= 4, "attribution too small")
    require(all(row["pass"] == "1" for row in audit), "audit table has failing checks")
    require(len(gaps) == 1, "expected one SEC source-gap family row")
    require(gaps[0]["gap_treatment"] == "neutral_not_negative", "gap treatment mismatch")
    require(gaps[0]["blocks_controlled_replay_design"] == "0", "gap should not block controlled replay design")
    require(gaps[0]["blocks_live"] == "1", "gap should block live readiness")
    require(len(subagents) == 4, "subagent packet count mismatch")
    require(all(row["write_scope"] == "read-only" for row in subagents), "subagents should be read-only")

    require(closeout == decision_rows, "decision and closeout mismatch")
    co = closeout[0]
    require(co["verdict"] == "source_integrated_selector_only_diagnostic_complete_no_replay", "bad closeout verdict")
    require(co["candidate_rows"] == "3100", "closeout candidate mismatch")
    require(co["l2_bridge_rows"] == "3100", "closeout L2 mismatch")
    require(co["selector_only_rows"] == "2480", "closeout selection mismatch")
    require(co["capital_replay_run"] == "0", "closeout should not replay")
    require(co["selector_deployment_changed"] == "0", "closeout should not deploy selector")
    require(co["source_gap_rows"] == "1", "closeout source gap mismatch")
    require(len(manifest) >= 15, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2581, 2601)), "registry missing Task2581-2600 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("126. Task2581-Task2600" in op_state, "operating state missing Task2581-2600 line")
    require("NOT_ACCEPTED" in report.read_text(encoding="utf-8"), "report missing status footer")

    print("[TASK2581_2600_SOURCE_INTEGRATED_SELECTOR_DIAGNOSTIC_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
