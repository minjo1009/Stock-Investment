from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2201_2230_latest_brain_full_universe_replay"
REPORT = ROOT / "docs/reports/task_2201_2230_latest_brain_full_universe_replay/task_2201_2230_latest_brain_full_universe_replay.md"
DECISION = ROOT / "docs/reports/task_2201_2230_latest_brain_full_universe_replay/task_2201_2230_decision.csv"
SKILL = Path("C:/Users/minjo/.codex/skills/trader-brain-source-acquisition/SKILL.md")
AUTHORITY = "DIAGNOSTIC_LATEST_BRAIN_FULL_UNIVERSE_REPLAY_ONLY"


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
    contract = read_csv(OUT_DIR / "task2201_latest_brain_freeze_contract.csv")
    scope = read_csv(OUT_DIR / "task2202_full_universe_scope.csv")
    source_plan = read_csv(OUT_DIR / "task2203_source_family_plan.csv")
    join_audit = read_csv(OUT_DIR / "task2204_full_candidate_join_audit.csv")
    features = read_csv(OUT_DIR / "task2205_l2_l5_latest_brain_feature_panel.csv")
    ranks = read_csv(OUT_DIR / "task2206_full_universe_rank_panel.csv")
    policies = read_csv(OUT_DIR / "task2207_full_universe_policy_specs.csv")
    trades = read_csv(OUT_DIR / "task2208_full_universe_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task2209_full_universe_replay_equity.csv")
    metrics = read_csv(OUT_DIR / "task2210_full_universe_replay_metrics.csv")
    comparison = read_csv(OUT_DIR / "task2211_comparison_matrix.csv")
    gaps = read_csv(OUT_DIR / "task2212_gap_ledger.csv")
    closeout = read_csv(OUT_DIR / "task2230_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(SKILL.exists(), "missing repeated acquisition skill")
    require(len(contract) >= 10, "brain contract incomplete")
    require(len(scope) == 1, "scope row missing")
    require(scope[0]["candidate_rows"] == "3100", "full universe candidate count is not 3100")
    require(scope[0]["same_trade_sizing_only"] == "0", "scope still same-trade sizing only")
    require(len(features) == 3100, "feature panel is not full candidate pool")
    require(len(ranks) == 3100, "rank panel is not full candidate pool")
    require(len(join_audit) == 3100, "join audit is not full candidate pool")
    require(len(policies) == 5, "expected five full-universe policy variants")
    require(len(metrics) == 5, "expected five metric rows")
    require(len(comparison) >= 9, "comparison matrix missing reference rows")
    require(len(gaps) > 0, "gap ledger should report missing source families")
    require(len(trades) > 116, "replay did not leave selected 116-trade scope")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 12, "manifest incomplete")

    validate_flags(contract, "contract")
    validate_flags(features, "features", "0")
    validate_flags(ranks, "ranks")
    validate_flags(policies, "policies")
    validate_flags(trades, "trades", "1")
    validate_flags(equity, "equity", "1")
    validate_flags(metrics, "metrics", "1")
    validate_flags(closeout, "closeout", "1")

    api_row = next(row for row in source_plan if row["source_family"] == "api_hardened_overlay")
    require(api_row["exact_covered_rows"] == closeout[0]["api_exact_covered_rows"], "api coverage mismatch")
    require(int(api_row["missing_rows"]) > 0, "api coverage unexpectedly full; validate source contract")
    require(api_row["assignment_policy"] == "exact_api_rows_only_missing_neutral_no_penalty", "bad api missing policy")
    require(any(row["api_cards_join_status"] == "missing_neutral" for row in join_audit), "api missing rows not marked neutral")
    require(all(row["returns_join_status"] == "exact_key_match" for row in join_audit), "returns exact join missing")
    require(all(row["l5_state_join_status"] == "exact_key_match" for row in join_audit), "l5 exact join missing")
    require(all(row["collapse_join_status"] == "exact_key_match" for row in join_audit), "collapse exact join missing")
    require(all(row["payoff_join_status"] == "exact_key_match" for row in join_audit), "payoff exact join missing")
    require(any(row["selection_allowed"] == "1" for row in features), "no selectable candidates")
    require(all(row["missing_source_policy"] == "missing_sources_are_neutral_not_negative" for row in features), "missing source policy violated")

    for row in metrics + closeout:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
        require(row["real_capital"] == "FORBIDDEN", "real capital changed")
    require(closeout[0]["verdict"] == "latest_brain_full_universe_replay_complete_diagnostic_only", "bad verdict")
    require(closeout[0]["same_trade_sizing_only"] == "0", "closeout says same-trade sizing")

    print("[TASK2201_2230_VALIDATE_OK] full_universe=pass leakage_flags=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
