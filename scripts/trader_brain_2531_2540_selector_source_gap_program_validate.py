from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2531_2540_selector_source_gap_program"
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


def assert_no_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    forbidden_tokens = ["d826f6", "d8oktf", "UPwwRz", "7RU6"]
    for idx, row in enumerate(rows, start=1):
        blob = " ".join(str(value) for value in row.values())
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        require(row.get("used_as_source_of_truth_for_pnl", "0") == "0", f"{name} row {idx} uses context as pnl truth")
        for token in forbidden_tokens:
            require(token not in blob, f"{name} row {idx} leaks secret-like token")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2531_2540_selector_source_gap_program.md"
    decision = REPORT_DIR / "task_2540_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2531_scope_freeze.csv")
    context = read_csv(OUT_DIR / "task2532_recent_source_context.csv")
    families = read_csv(OUT_DIR / "task2532_source_family_plan.csv")
    states = read_csv(OUT_DIR / "task2533_admission_states.csv")
    gaps = read_csv(OUT_DIR / "task2533_source_gap_ledger.csv")
    coverage = read_csv(OUT_DIR / "task2534_decision_asof_coverage.csv")
    gates = read_csv(OUT_DIR / "task2535_feature_admission_gate.csv")
    providers = read_csv(OUT_DIR / "task2536_provider_feasibility_matrix.csv")
    subagents = read_csv(OUT_DIR / "task2537_subagent_packets.csv")
    queue = read_csv(OUT_DIR / "task2538_next_acquisition_queue.csv")
    assertions = read_csv(OUT_DIR / "task2539_validation_assertions.csv")
    closeout = read_csv(OUT_DIR / "task2540_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("context", context),
        ("families", families),
        ("states", states),
        ("gaps", gaps),
        ("coverage", coverage),
        ("gates", gates),
        ("providers", providers),
        ("subagents", subagents),
        ("queue", queue),
        ("closeout", closeout),
    ]:
        assert_no_leak(rows, name)
    for name, rows in [("scope", scope), ("closeout", closeout)]:
        assert_status(rows, name)

    require(len(scope) == 1, "scope row count mismatch")
    require(scope[0]["download_or_api_call_run"] == "0", "source gap task should not download")
    require(scope[0]["backtest_run"] == "0", "source gap task should not backtest")
    require(int(scope[0]["universe_rows"]) == 3100, "full universe row count mismatch")
    require(int(scope[0]["selected_kis_trade_rows"]) == 124, "selected trade row count mismatch")
    require(int(scope[0]["mdd_window_trade_rows"]) == 14, "mdd trade row count mismatch")
    require(int(scope[0]["strict_raw_asof_complete_rows"]) == 0, "strict raw/as-of should still be zero")

    require(len(context) >= 6, "recent source context too small")
    require(any(row["source_name"] == "SEC" for row in context), "missing SEC context")
    require(any(row["source_name"] == "Frontiers" for row in context), "missing recent transaction cost context")
    require(len(families) >= 8, "source families too small")
    family_names = {row["source_family"] for row in families}
    for required in {"strict_raw_asof_certification", "financing_dilution_sec_events", "liquidity_rates_regime", "earnings_transcript_guidance", "analyst_revision_rating_history"}:
        require(required in family_names, f"missing family {required}")
    priority = {row["source_family"]: row["priority"] for row in families}
    require(priority["strict_raw_asof_certification"] == "P0", "strict source certification must be P0")
    require(priority["financing_dilution_sec_events"] == "P0", "financing/dilution must be P0")
    require(priority["liquidity_rates_regime"] == "P1", "liquidity/rates should be P1")

    state_map = {row["admission_state"]: row for row in states}
    require(set(state_map) == {"strict_pass", "proxy_allowed", "blocked", "unknown"}, "bad admission states")
    require(state_map["strict_pass"]["can_score_assignment"] == "1", "strict pass should score")
    for state in ["proxy_allowed", "blocked", "unknown"]:
        require(state_map[state]["can_score_assignment"] == "0", f"{state} should not score assignment")

    require(len(gaps) >= 40, "gap ledger too small")
    require(all(row["gap_state"] in state_map for row in gaps), "unknown gap state")
    require(all(row["asof_pass"] == "0" for row in gaps), "gap rows should not pass as-of")
    require(len(coverage) >= 60, "decision asof coverage too small")
    require(all(as_float(row["strict_coverage_ratio"]) == 0.0 for row in coverage), "strict coverage should be zero")

    require(len(gates) == int(scope[0]["selected_kis_trade_rows"]) * len(families), "feature gate row count mismatch")
    for row in gates:
        if row["can_score_assignment"] == "1":
            require(row["admission_state"] == "strict_pass", "only strict pass can score")
        if row["admission_state"] == "proxy_allowed":
            require(row["can_annotate_only"] == "1", "proxy should annotate only")
        if row["admission_state"] in {"blocked", "unknown"}:
            require(row["blocks_live"] == "1", "blocked/unknown should block live")
    require(all(row["strict_gate_pass"] == "0" for row in gates), "no strict feature gates should pass yet")

    require(len(providers) >= 8, "provider matrix too small")
    require(any(row["provider"] == "Treasury FiscalData" for row in providers), "missing Treasury provider")
    require(any(row["provider"] == "NY Fed Markets API" for row in providers), "missing NY Fed provider")
    require(len(subagents) == 3, "subagent packet count mismatch")
    require(all(row["write_scope"] == "read-only" for row in subagents), "subagents should be read-only")
    require(all(row["file_edits_allowed"] == "0" for row in subagents), "subagents should not edit files")
    require(len(queue) >= 6, "acquisition queue too small")
    require(queue[0]["source_family"] == "strict_raw_asof_certification", "first queue item should be strict source certification")
    require(queue[1]["source_family"] == "financing_dilution_sec_events", "second queue item should be financing/dilution")
    require(any(row["source_family"] == "earnings_transcript_guidance" for row in queue), "missing transcript queue")
    require(len(assertions) >= 12, "validation assertion table too small")

    require(closeout == decision_rows, "decision and closeout mismatch")
    co = closeout[0]
    require(co["verdict"] == "selector_source_gap_program_built_no_replay_no_download", "bad verdict")
    require(co["download_or_api_call_run"] == "0", "closeout should not claim downloads")
    require(co["backtest_run"] == "0", "closeout should not claim backtest")
    require(co["selector_changed"] == "0", "selector should not change")
    require(int(co["strict_pass_feature_rows"]) == 0, "strict feature rows should be zero")
    require(int(co["blocked_feature_rows"]) > 0, "blocked feature rows should exist")
    require(len(manifest) >= 12, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2531, 2541)), "registry missing Task2531-2540 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("123. Task2531-Task2540" in op_state, "operating state missing Task2531-2540 line")

    print("[TASK2531_2540_SELECTOR_SOURCE_GAP_PROGRAM_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
