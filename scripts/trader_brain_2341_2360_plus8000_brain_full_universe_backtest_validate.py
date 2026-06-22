from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2341_2360_plus8000_brain_full_universe_backtest"
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


def as_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def assert_no_assignment_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")


def main() -> None:
    report = REPORT_DIR / "task_2341_2360_plus8000_brain_full_universe_backtest.md"
    decision = REPORT_DIR / "task_2341_2360_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    contract = read_csv(OUT_DIR / "task2341_experiment_contract.csv")
    preentry = read_csv(OUT_DIR / "task2342_full_preentry_panel.csv")
    winner = read_csv(OUT_DIR / "task2343_full_winner_defense_panel.csv")
    l1 = read_csv(OUT_DIR / "task2345_full_l1_packets.csv")
    l2 = read_csv(OUT_DIR / "task2346_full_l2_semantics.csv")
    l3 = read_csv(OUT_DIR / "task2347_full_l3_edges.csv")
    l4 = read_csv(OUT_DIR / "task2348_full_l4_thesis_cards.csv")
    l5 = read_csv(OUT_DIR / "task2349_full_l5_decisions.csv")
    cards = read_csv(OUT_DIR / "task2350_full_api_l4_cards.csv")
    decisions = read_csv(OUT_DIR / "task2351_full_api_l5_decisions.csv")
    api_audit = read_csv(OUT_DIR / "task2352_full_api_overlay_audit.csv")
    return_sources = read_csv(OUT_DIR / "task2353_full_return_source_rows.csv")
    return_audit = read_csv(OUT_DIR / "task2353_full_return_source_audit.csv")
    guard_rows = read_csv(OUT_DIR / "task2354_full_guard_rows.csv")
    trades = read_csv(OUT_DIR / "task2355_full_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2356_full_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2357_full_replay_metrics.csv")
    coverage = read_csv(OUT_DIR / "task2358_full_coverage.csv")
    comparison = read_csv(OUT_DIR / "task2359_comparison_matrix.csv")
    overlap = read_csv(OUT_DIR / "task2359_selection_overlap_audit.csv")
    closeout = read_csv(OUT_DIR / "task2360_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(len(contract) == 1, "contract row count mismatch")
    c = contract[0]
    require(c.get("full_universe_candidate_rows") == "3100", "contract not full 3100")
    require(c.get("original_candidate_set_only") == "0", "contract still old-candidate only")
    require(c.get("plus8000_brain_structure_preserved") == "1", "plus8000 brain structure not preserved")
    require(c.get("same_replay_capital_path_as_plus8000") == "1", "same replay capital path flag missing")
    require(c.get("strict_raw_asof_complete") == "0", "strict raw/asof flag should remain diagnostic 0")

    for name, rows in [
        ("preentry", preentry),
        ("winner", winner),
        ("l1", l1),
        ("l2", l2),
        ("l4", l4),
        ("l5", l5),
        ("cards", cards),
        ("decisions", decisions),
        ("api_audit", api_audit),
    ]:
        require(len(rows) == 3100, f"{name} should cover 3100 rows, got {len(rows)}")
        assert_no_assignment_leak(rows, name)

    require(len(l3) >= 3100, f"l3 should have at least one edge per candidate, got {len(l3)}")
    require(len({row.get("trade_spec_id", "") for row in l3}) == 3100, "l3 unique trade coverage not 3100")
    assert_no_assignment_leak(l3, "l3")

    require(len(return_sources) == 6200, f"return sources should be 2 x 3100, got {len(return_sources)}")
    require(len(return_audit) == 6200, f"return audit should be 2 x 3100, got {len(return_audit)}")
    assert_no_assignment_leak(return_sources, "return_sources")
    assert_no_assignment_leak(return_audit, "return_audit")
    require(all(row.get("outcome_used_for_audit_only") == "1" for row in return_sources), "return sources must be audit-only")

    require(len(metrics) == 6, f"metrics should be 2 return policies x 3 guard policies, got {len(metrics)}")
    require(len(guard_rows) >= 6, "guard rows too small")
    require(len(trades) >= 300, "trade rows too small for full-universe replay")
    require(len(equity) >= 6, "equity rows too small")
    require(len(comparison) >= 10, "comparison matrix too small")
    require(len(overlap) == 3, "selection overlap audit should compare three +8000 guard variants")
    require(all(int(row.get("common_trade_count", "0")) > 0 for row in overlap), "selection overlap common count missing")
    require(len(manifest) >= 10, "manifest too small")

    full_policies = {row.get("policy_variant_id", "") for row in metrics}
    require(all(policy.startswith("plus8000_full_") for policy in full_policies), "metrics policy ids not full-universe namespaced")
    require({row.get("return_source_policy", "") for row in metrics} == {"scheduled_uniform", "actual_else_scheduled"}, "return policies missing")
    require(all(row.get("strategy_acceptance") == "NOT_ACCEPTED" for row in metrics), "strategy status changed")
    require(all(row.get("deployment_readiness") == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" for row in metrics), "deployment status changed")
    require(all(row.get("real_capital") == "FORBIDDEN" for row in metrics), "real capital status changed")

    cov = {row["metric"]: row for row in coverage}
    require(cov["full_universe_candidate_rows"]["rows"] == "3100", "coverage not full universe")
    require(cov["l5_decision_rows"]["rows"] == "3100", "coverage l5 not full universe")
    require(as_float(cov["api_proxy_supportive_rows"]["ratio"]) > 0.40, "api supportive coverage unexpectedly low")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co.get("verdict") == "plus8000_brain_full_universe_backtest_complete_diagnostic_only", "bad verdict")
    require(co.get("full_universe_candidate_rows") == "3100", "closeout not full universe")
    require(co.get("original_candidate_set_only") == "0", "closeout incorrectly old-candidate only")
    require(co.get("plus8000_brain_structure_preserved") == "1", "closeout brain preservation missing")
    require(co.get("same_replay_capital_path_as_plus8000") == "1", "closeout replay path mismatch")
    require(co.get("strict_raw_asof_complete") == "0", "strict raw/asof should remain diagnostic 0")
    require(co.get("best_policy_variant_id", "").startswith("plus8000_full_"), "best policy not full-universe namespaced")
    require(as_float(co.get("best_final_equity", "0")) > 0, "best final equity missing")

    print("[TASK2341_2360_PLUS8000_BRAIN_FULL_UNIVERSE_BACKTEST_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
