from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2381_2400_plus8000_exit_chain_parity_repair"
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


def assert_no_assignment_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")


def assert_no_secret_text(rows: list[dict[str, str]], name: str) -> None:
    forbidden = ("apikey", "token", "authorization", "bearer")
    for idx, row in enumerate(rows, start=1):
        haystack = " ".join(str(v).lower() for v in row.values())
        require(not any(term in haystack for term in forbidden), f"{name} row {idx} leaks secret-like text")


def main() -> None:
    report = REPORT_DIR / "task_2381_2400_plus8000_exit_chain_parity_repair.md"
    decision = REPORT_DIR / "task_2381_2400_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    contract = read_csv(OUT_DIR / "task2381_exit_chain_contract.csv")
    plan = read_csv(OUT_DIR / "task2381_source_family_plan.csv")
    ledger = read_csv(OUT_DIR / "task2381_api_or_raw_call_ledger.csv")
    lineage = read_csv(OUT_DIR / "task2382_original_chain_lineage.csv")
    parity = read_csv(OUT_DIR / "task2383_selected_116_parity_diff.csv")
    sources = read_csv(OUT_DIR / "task2384_repaired_exit_source_rows.csv")
    gaps = read_csv(OUT_DIR / "task2384_source_gap_ledger.csv")
    methods = read_csv(OUT_DIR / "task2385_full_universe_extension_method_audit.csv")
    guard_rows = read_csv(OUT_DIR / "task2386_replay_guard_rows.csv")
    trades = read_csv(OUT_DIR / "task2386_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2386_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2386_replay_metrics.csv")
    comparison = read_csv(OUT_DIR / "task2387_comparison_matrix.csv")
    attr = read_csv(OUT_DIR / "task2388_failure_attribution.csv")
    coverage = read_csv(OUT_DIR / "task2389_coverage.csv")
    closeout = read_csv(OUT_DIR / "task2400_closeout.csv")
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(len(contract) == 1, "contract row count mismatch")
    c = contract[0]
    require(c.get("full_universe_candidate_rows") == "3100", "contract not full 3100")
    require(c.get("generic_task2361_exit_replaced") == "1", "Task2361 generic exit not marked replaced")
    require(c.get("same_selected_trades_only") == "0", "contract selected-only")
    require(c.get("scheduled_fallback_rows_allowed") == "0", "scheduled fallback allowed")
    assert_no_assignment_leak(plan, "plan")
    assert_no_secret_text(ledger, "ledger")

    checked_hashes = 0
    for row in ledger:
        if row.get("request_status") == "cache_hit":
            raw = row.get("raw_path", "")
            digest = row.get("raw_sha256", "")
            path = ROOT / raw
            require(path.exists(), f"missing raw path {raw}")
            require(digest == sha256(path), f"sha mismatch {raw}")
            checked_hashes += 1
    require(checked_hashes > 0, "no raw hashes checked")

    require(len(lineage) == 116, f"lineage should cover 116 selected specs, got {len(lineage)}")
    require(len(parity) == 116, f"parity should cover 116 selected specs, got {len(parity)}")
    require(all(row.get("parity_pass") == "1" for row in parity), "selected 116 parity did not pass")
    require(sum(int(row.get("diff_count", "0")) for row in parity) == 0, "selected 116 diff_count not zero")
    assert_no_assignment_leak(parity, "parity")

    require(len(sources) == 3100, f"sources should cover 3100, got {len(sources)}")
    require(len(methods) == 3100, f"methods should cover 3100, got {len(methods)}")
    require(len(gaps) == 0, f"price gaps should be zero, got {len(gaps)}")
    assert_no_assignment_leak(sources, "sources")
    assert_no_assignment_leak(methods, "methods")
    require(all(row.get("outcome_used_for_audit_only") == "1" for row in sources), "sources not audit-only")
    require(all(row.get("scheduled_fallback_used") == "0" for row in sources), "scheduled fallback used")
    require(all(row.get("policy_variant_id") == "winner_defense_budget_top5_v1" for row in sources), "wrong source policy")
    require(sum(1 for row in methods if row.get("copied_original_source") == "1") >= 215, "original source copy count too low")
    require(sum(1 for row in methods if row.get("extension_method") == "task1668_decide_action_extended") > 0, "Task1668 extension not used")

    require(len(metrics) == 3, "metrics should contain three guard variants")
    require(len(guard_rows) >= 100, "guard rows too small")
    require(len(trades) >= 100, "trades too small")
    require(len(equity) >= 50, "equity too small")
    require(len(comparison) >= 10, "comparison too small")
    require(len(attr) >= 20, "attribution too small")
    require(len(manifest) >= 10, "manifest too small")
    require(all(row.get("policy_variant_id", "").startswith("exit_chain_repaired_") for row in metrics), "metrics namespace mismatch")
    require(all(row.get("strategy_acceptance") == "NOT_ACCEPTED" for row in metrics), "strategy status changed")
    require(all(row.get("deployment_readiness") == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" for row in metrics), "deployment status changed")
    require(all(row.get("real_capital") == "FORBIDDEN" for row in metrics), "real capital status changed")

    cov = {row["metric"]: row for row in coverage}
    require(cov["full_universe_candidate_rows"]["rows"] == "3100", "coverage full universe mismatch")
    require(cov["repaired_exit_source_rows"]["rows"] == "3100", "coverage source row mismatch")
    require(cov["selected_116_parity_rows"]["rows"] == "116", "coverage parity row mismatch")
    require(cov["selected_116_parity_diff_rows"]["rows"] == "0", "coverage parity diff nonzero")
    require(cov["price_gap_rows"]["rows"] == "0", "coverage price gap nonzero")
    require(cov["scheduled_fallback_rows"]["rows"] == "0", "coverage scheduled fallback nonzero")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co.get("verdict") == "plus8000_exit_chain_parity_repaired_diagnostic_only", "bad verdict")
    require(co.get("full_universe_candidate_rows") == "3100", "closeout not full universe")
    require(co.get("repaired_exit_source_rows") == "3100", "closeout not full source")
    require(co.get("selected_116_parity_diff_rows") == "0", "closeout parity diff nonzero")
    require(co.get("scheduled_fallback_rows") == "0", "closeout scheduled fallback nonzero")
    require(co.get("same_selected_trades_only") == "0", "closeout selected-only")
    require(co.get("generic_task2361_exit_replaced") == "1", "generic exit not replaced")
    require(co.get("selector_brain_preserved") == "1", "selector brain not preserved")
    require(co.get("strict_raw_asof_complete") == "0", "strict raw/asof should remain diagnostic 0")
    require(as_float(co.get("best_final_equity", "0")) > 0, "best final equity missing")
    print("[TASK2381_2400_PLUS8000_EXIT_CHAIN_PARITY_REPAIR_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
