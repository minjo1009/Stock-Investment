from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest"
REPORT = ROOT / "docs/reports/task_2291_2310_plus8000_feature_full_universe_backtest/task_2291_2310_plus8000_feature_full_universe_backtest.md"
DECISION = ROOT / "docs/reports/task_2291_2310_plus8000_feature_full_universe_backtest/task_2291_2310_decision.csv"
AUTHORITY = "DIAGNOSTIC_PLUS8000_FEATURE_FULL_UNIVERSE_BACKTEST_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_flags(rows: list[dict[str, str]], context: str, audit_expected: str | None = None) -> None:
    for row in rows:
        if "authority" in row:
            require(row["authority"] == AUTHORITY, f"{context} authority mismatch")
        if "assignment_uses_future_outcome" in row:
            require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
        if "outcome_used_for_assignment" in row:
            require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
        if audit_expected is not None and "outcome_used_for_audit_only" in row:
            require(row["outcome_used_for_audit_only"] == audit_expected, f"{context} audit flag")


def main() -> None:
    scope = read_csv(OUT_DIR / "task2291_scope.csv")
    sources = read_csv(OUT_DIR / "task2292_source_proxy_coverage.csv")
    api_cards = read_csv(OUT_DIR / "task2293_plus8000_api_l4_cards.csv")
    api_decisions = read_csv(OUT_DIR / "task2294_plus8000_api_l5_decisions.csv")
    join_audit = read_csv(OUT_DIR / "task2295_plus8000_join_audit.csv")
    features = read_csv(OUT_DIR / "task2296_plus8000_feature_panel.csv")
    ranks = read_csv(OUT_DIR / "task2297_plus8000_rank_panel.csv")
    policies = read_csv(OUT_DIR / "task2297_policy_specs.csv")
    trades = read_csv(OUT_DIR / "task2298_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2299_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2300_replay_metrics.csv")
    comparison = read_csv(OUT_DIR / "task2301_comparison_matrix.csv")
    symbols = read_csv(OUT_DIR / "task2302_selected_symbol_breakdown.csv")
    worst = read_csv(OUT_DIR / "task2303_worst_trade_audit.csv")
    closeout = read_csv(OUT_DIR / "task2310_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(scope) == 1, "scope row missing")
    require(scope[0]["candidate_rows"] == "3100", "scope candidate count is not 3100")
    require(scope[0]["same_trade_sizing_only"] == "0", "scope is still same-trade sizing")
    require(scope[0]["strict_raw_asof_complete"] == "0", "scope misstates strict raw/asof completeness")
    require(len(features) == 3100, "feature panel is not full 3100")
    require(len(ranks) == 3100, "rank panel is not full 3100")
    require(len(join_audit) == 3100, "join audit is not full 3100")
    require(len(api_cards) == 3100, "api card panel is not full 3100")
    require(len(api_decisions) == 3100, "api decision panel is not full 3100")
    require(len(policies) == 4, "expected four policy variants")
    require(len(metrics) == 4, "expected four metrics rows")
    require(len(comparison) >= 8, "comparison matrix missing references")
    require(len(trades) > 116, "replay stayed at old selected-trade scope")
    require(len(symbols) > 0, "missing symbol breakdown")
    require(len(worst) > 0, "missing worst trade audit")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 12, "manifest incomplete")

    validate_flags(api_cards, "api_cards")
    validate_flags(api_decisions, "api_decisions")
    validate_flags(features, "features", "0")
    validate_flags(ranks, "ranks")
    validate_flags(policies, "policies")
    validate_flags(trades, "trades", "1")
    validate_flags(equity, "equity", "1")
    validate_flags(metrics, "metrics", "1")
    validate_flags(closeout, "closeout", "1")

    feature_schema = next(row for row in sources if row["source_family"] == "feature_schema_parity")
    non_gap = next(row for row in sources if row["source_family"] == "api_proxy_not_source_gap")
    raw_gate = next(row for row in sources if row["source_family"] == "strict_raw_asof_replay_gate_reference_only")
    require(feature_schema["exact_covered_rows"] == "3100", "feature schema parity not full")
    require(float(non_gap["coverage_ratio"]) >= 0.95, "non-gap +8000 feature coverage below expected proxy standard")
    require(float(raw_gate["coverage_ratio"]) < 0.10, "raw gate unexpectedly high; verify strict parity input")
    require(all(row["missing_source_policy"] == "plus8000_feature_missing_neutral_not_negative" for row in features), "missing source policy violated")
    require(any(row["plus8000_api_proxy_state"] == "api_proxy_source_gap_neutral" for row in features), "source gaps not retained")
    require(any(row["plus8000_api_proxy_state"] == "api_proxy_supportive" for row in features), "supportive proxy state missing")

    for row in metrics + closeout:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")
    require(closeout[0]["verdict"] == "plus8000_feature_full_universe_backtest_complete_diagnostic_only", "bad verdict")
    require(closeout[0]["same_trade_sizing_only"] == "0", "closeout says same-trade sizing")
    require(closeout[0]["strict_raw_asof_complete"] == "0", "closeout overclaims raw/asof completeness")

    print("[TASK2291_2310_VALIDATE_OK] full_universe=pass plus8000_feature_proxy=pass leakage_flags=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
