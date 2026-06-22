from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2361_2380_full_exit_quality_parity_backtest"
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_no_secret_text(rows: list[dict[str, str]], name: str) -> None:
    forbidden = ("apikey", "token", "authorization", "bearer")
    for idx, row in enumerate(rows, start=1):
        haystack = " ".join(str(v).lower() for v in row.values())
        require(not any(term in haystack for term in forbidden), f"{name} row {idx} leaks secret-like text")


def assert_no_assignment_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")


def main() -> None:
    report = REPORT_DIR / "task_2361_2380_full_exit_quality_parity_backtest.md"
    decision = REPORT_DIR / "task_2361_2380_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2361_scope_freeze.csv")
    plan = read_csv(OUT_DIR / "task2362_source_family_plan.csv")
    ledger = read_csv(OUT_DIR / "task2363_api_or_raw_call_ledger.csv")
    packets = read_csv(OUT_DIR / "task2364_normalized_exit_quality_packets.csv")
    gaps = read_csv(OUT_DIR / "task2364_source_gap_ledger.csv")
    sources = read_csv(OUT_DIR / "task2365_full_exit_quality_return_source_rows.csv")
    coverage = read_csv(OUT_DIR / "task2366_exit_quality_coverage.csv")
    guard_rows = read_csv(OUT_DIR / "task2367_guard_rows.csv")
    trades = read_csv(OUT_DIR / "task2368_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2369_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2370_replay_metrics.csv")
    comparison = read_csv(OUT_DIR / "task2371_comparison_matrix.csv")
    overlap = read_csv(OUT_DIR / "task2372_selection_overlap_audit.csv")
    attribution = read_csv(OUT_DIR / "task2373_failure_attribution.csv")
    closeout = read_csv(OUT_DIR / "task2380_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(len(scope) == 1, "scope row count mismatch")
    require(scope[0].get("candidate_rows") == "3100", "scope is not full 3100")
    require(scope[0].get("same_selected_trades_only") == "0", "scope is selected-trades-only")
    require(len(plan) >= 4, "source family plan too small")
    assert_no_assignment_leak(plan, "plan")
    assert_no_secret_text(ledger, "ledger")

    require(len(packets) == 3100, f"exit packets should cover 3100, got {len(packets)}")
    require(len(sources) == 3100, f"return sources should cover 3100, got {len(sources)}")
    require(len(gaps) == 0, f"price gaps should be zero for parity run, got {len(gaps)}")
    assert_no_assignment_leak(packets, "packets")
    assert_no_assignment_leak(sources, "sources")
    require(all(row.get("outcome_used_for_audit_only") == "1" for row in packets), "packets must be audit-only")
    require(all(row.get("outcome_used_for_audit_only") == "1" for row in sources), "sources must be audit-only")
    require(all(row.get("return_source_policy") == "full_exit_quality_task1704_compatible" for row in sources), "wrong return source policy")
    require(all(row.get("policy_variant_id") == "winner_defense_budget_top5_v1" for row in sources), "wrong source policy id")

    checked_hashes = 0
    for row in ledger:
        raw = row.get("raw_path", "")
        digest = row.get("raw_sha256", "")
        if row.get("request_status") == "cache_hit":
            path = ROOT / raw
            require(path.exists(), f"ledger raw path missing: {raw}")
            require(digest == sha256(path), f"raw sha mismatch: {raw}")
            checked_hashes += 1
    require(checked_hashes > 0, "no raw hashes checked")

    cov = {row["metric"]: row for row in coverage}
    require(cov["l5_candidate_rows"]["rows"] == "3100", "coverage l5 rows not 3100")
    require(cov["exit_quality_packet_rows"]["rows"] == "3100", "coverage packets not 3100")
    require(cov["return_source_rows"]["rows"] == "3100", "coverage return source not 3100")
    require(cov["price_gap_rows"]["rows"] == "0", "coverage price gaps nonzero")

    require(len(metrics) == 3, "metrics should contain three guard variants")
    require(len(guard_rows) >= 100, "guard rows too small")
    require(len(trades) >= 100, "trades too small")
    require(len(equity) >= 50, "equity too small")
    require(len(comparison) >= 10, "comparison too small")
    require(len(overlap) == 1, "overlap audit should have one winner-preserve comparison")
    require(len(attribution) >= 20, "failure attribution too small")
    require(any(row.get("failure_area") == "worst_selected_trade" for row in attribution), "worst-trade attribution missing")
    require(len(manifest) >= 10, "manifest too small")
    require(all(row.get("policy_variant_id", "").startswith("full_exit_quality_") for row in metrics), "policy namespace mismatch")
    require(all(row.get("strategy_acceptance") == "NOT_ACCEPTED" for row in metrics), "strategy status changed")
    require(all(row.get("deployment_readiness") == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" for row in metrics), "deployment status changed")
    require(all(row.get("real_capital") == "FORBIDDEN" for row in metrics), "real capital status changed")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co.get("verdict") == "full_exit_quality_parity_backtest_complete_diagnostic_only", "bad verdict")
    require(co.get("full_universe_candidate_rows") == "3100", "closeout not full universe")
    require(co.get("exit_quality_rows") == "3100", "closeout not full exit quality")
    require(co.get("price_gap_rows") == "0", "closeout price gaps nonzero")
    require(co.get("scheduled_fallback_rows") == "0", "scheduled fallback should be zero")
    require(co.get("same_selected_trades_only") == "0", "closeout selected-trades-only")
    require(co.get("selector_brain_preserved") == "1", "selector brain not preserved")
    require(co.get("strict_raw_asof_complete") == "0", "strict raw/asof should remain diagnostic 0")
    require(as_float(co.get("best_final_equity", "0")) > 0, "best final equity missing")
    print("[TASK2361_2380_FULL_EXIT_QUALITY_PARITY_BACKTEST_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
