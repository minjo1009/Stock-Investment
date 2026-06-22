from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"
REPORT = ROOT / "docs/reports/task_1388_1407_expert_reviewed_judgment_replay/task_1388_1407_expert_reviewed_judgment_replay.md"
AUTHORITY = "DIAGNOSTIC_EXPERT_REVIEWED_JUDGMENT_REPLAY_ONLY"

REQUIRED_FILES = {
    "task1388_formula_draft.csv": 8,
    "task1389_expert_critique_matrix.csv": 10,
    "task1389_revised_formula_spec.csv": 6,
    "task1390_expectation_gap_panel.csv": 3100,
    "task1391_materiality_denominator_panel.csv": 3100,
    "task1392_source_independence_splitter.csv": 3100,
    "task1393_market_absorption_panel.csv": 3100,
    "task1394_l2_enriched_judgment_panel.csv": 3100,
    "task1394_l3_mechanism_edges_v2.csv": 15500,
    "task1395_l4_payoff_ranker_v2.csv": 3100,
    "task1396_l5_policy_specs_v2.csv": 9300,
    "task1396_dynamic_exit_receipts_v2.csv": 1550,
    "task1397_replay_trades.csv": 1550,
    "task1398_replay_equity.csv": 186,
    "task1399_replay_metrics.csv": 3,
    "task1400_replacement_pair_audit.csv": 1,
    "task1401_split_freeze.csv": 62,
    "task1402_validation_invariant_ledger.csv": 5,
    "task1403_overfit_guard_ledger.csv": 2,
    "task1404_acceptance_gate.csv": 1,
    "task1407_closeout.csv": 1,
    "artifact_manifest.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_date(value: str):
    return datetime.fromisoformat(value).date()


def validate_files() -> None:
    for name, minimum_rows in REQUIRED_FILES.items():
        path = OUT_DIR / name
        require(path.exists(), f"missing artifact: {name}")
        rows = read_csv(path)
        require(len(rows) >= minimum_rows, f"{name} row count {len(rows)} < {minimum_rows}")


def validate_expert_loop() -> None:
    draft = read_csv(OUT_DIR / "task1388_formula_draft.csv")
    critique = read_csv(OUT_DIR / "task1389_expert_critique_matrix.csv")
    spec = read_csv(OUT_DIR / "task1389_revised_formula_spec.csv")
    require({row["formula_area"] for row in draft} >= {"expectation_gap", "materiality_denominator", "market_absorption", "payoff_ranker_v2", "dynamic_exit_v2"}, "missing draft formula areas")
    require(len({row["expert_role"] for row in critique}) >= 10, "expected at least 10 expert roles")
    require(all(row["review_authority"] == "GPT_SUBAGENT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH" for row in critique), "expert review authority mismatch")
    require(all(row["expert_review_incorporated"] == "1" for row in spec), "revised spec did not incorporate expert review")


def validate_no_future_assignment() -> None:
    for filename in [
        "task1390_expectation_gap_panel.csv",
        "task1391_materiality_denominator_panel.csv",
        "task1392_source_independence_splitter.csv",
        "task1393_market_absorption_panel.csv",
        "task1394_l2_enriched_judgment_panel.csv",
        "task1394_l3_mechanism_edges_v2.csv",
        "task1395_l4_payoff_ranker_v2.csv",
        "task1396_l5_policy_specs_v2.csv",
        "task1396_dynamic_exit_receipts_v2.csv",
    ]:
        for row in read_csv(OUT_DIR / filename):
            require(row["assignment_uses_future_outcome"] == "0", f"future assignment in {filename}")
            require(row["authority"] == AUTHORITY, f"authority mismatch in {filename}")


def validate_candidate_panels() -> None:
    expectation = read_csv(OUT_DIR / "task1390_expectation_gap_panel.csv")
    materiality = read_csv(OUT_DIR / "task1391_materiality_denominator_panel.csv")
    absorption = read_csv(OUT_DIR / "task1393_market_absorption_panel.csv")
    enriched = read_csv(OUT_DIR / "task1394_l2_enriched_judgment_panel.csv")
    edges = read_csv(OUT_DIR / "task1394_l3_mechanism_edges_v2.csv")
    rank = read_csv(OUT_DIR / "task1395_l4_payoff_ranker_v2.csv")
    require(len(expectation) == 3100, "expectation panel count mismatch")
    require(all(row["analyst_pit_available"] == "0" and row["analyst_source_gap"] == "1" for row in expectation), "analyst PIT gap must stay explicit")
    require(all(row["denominator_missing_score_increase_allowed"] == "0" for row in materiality), "denominator gap allowed score increase")
    require(
        all(float(row["materiality_denominator_adjusted_score"]) == 0.0 for row in materiality if row["materiality_denominator_quality"] == "denominator_source_gap"),
        "denominator source gap raised materiality adjusted score",
    )
    require(all(row["ranking_window_ends_at_or_before_decision"] == "1" for row in absorption), "absorption rank window boundary broken")
    require(len(enriched) == 3100, "enriched L2 count mismatch")
    require(len(edges) == len(enriched) * 5, "expected five L3 edges per candidate")
    by_decision: dict[str, list[int]] = {}
    for row in rank:
        by_decision.setdefault(row["decision_asof_ts"], []).append(int(row["expert_payoff_rank_within_decision"]))
    require(len(by_decision) == 62, "expected 62 decision cohorts")
    for decision_ts, ranks in by_decision.items():
        require(sorted(ranks) == list(range(1, 51)), f"{decision_ts} ranks are not 1..50")


def validate_policy_replay() -> None:
    specs = read_csv(OUT_DIR / "task1396_l5_policy_specs_v2.csv")
    selected: dict[str, int] = {}
    for row in specs:
        selected[row["policy_variant_id"]] = selected.get(row["policy_variant_id"], 0) + int(row["selected_for_replay"])
    require(selected["expert_payoff_top5_v2"] == 310, "top5 selected count mismatch")
    require(selected["expert_payoff_top10_v2"] == 620, "top10 selected count mismatch")
    require(selected["expert_hurdle_top10_v2"] == 620, "hurdle selected count mismatch")

    exits = read_csv(OUT_DIR / "task1396_dynamic_exit_receipts_v2.csv")
    ready = [row for row in exits if row["dynamic_exit_ready"] == "1"]
    require(len(ready) >= 100, "dynamic exit v2 did not materially expand receipts")
    for row in ready:
        if row["trigger_family"] != "pre_entry_absorption_rejection_cap":
            require(row["trigger_available_to_brain_ts"], "dynamic exit trigger missing timestamp")

    trades = read_csv(OUT_DIR / "task1397_replay_trades.csv")
    trade_by_key = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in trades}
    require(len(trades) == 1550, "trade count mismatch")
    dynamic_trade_count = sum(1 for row in trades if row["exit_reason"] != "scheduled_exit")
    require(dynamic_trade_count == len(ready), "dynamic trade count does not match ready receipts")
    for row in ready:
        trade = trade_by_key[(row["policy_variant_id"], row["trade_spec_id"])]
        if row["trigger_family"] != "pre_entry_absorption_rejection_cap":
            trigger_date = datetime.fromisoformat(row["trigger_available_to_brain_ts"]).date()
            require(trigger_date >= parse_date(trade["entry_date"]), "dynamic trigger before entry")
            require(trigger_date <= parse_date(trade["actual_exit_date"]), "dynamic trigger after actual exit")
            require(parse_date(trade["actual_exit_date"]) <= parse_date(trade["scheduled_exit_date"]), "dynamic exit after scheduled exit")
    for row in trades:
        require(row["assignment_uses_future_outcome"] == "0", "trade assignment used future outcome")
        require(row["exit_uses_post_entry_price_path"] == "1", "trade missing post-entry exit path marker")
        if row["exit_reason"] != "scheduled_exit":
            require(parse_date(row["actual_exit_date"]) >= parse_date(row["entry_date"]), "dynamic exit before entry")


def validate_audit_split_metrics_and_gate() -> None:
    audit = read_csv(OUT_DIR / "task1400_replacement_pair_audit.csv")
    require(audit, "replacement audit empty")
    for row in audit:
        require(row["outcome_used_for_assignment"] == "0", "replacement audit outcome used for assignment")
        require(row["outcome_used_for_audit_only"] == "1", "replacement audit not audit-only")

    split = read_csv(OUT_DIR / "task1401_split_freeze.csv")
    require(any(row["split_id"] == "oos_2025_2026q1" and row["oos_score_only"] == "1" for row in split), "missing OOS score-only split")
    require(all(row["policy_parameter_tuning_allowed"] == "0" for row in split if row["split_id"] != "train_2021_2023"), "non-train split allows tuning")

    metrics = read_csv(OUT_DIR / "task1399_replay_metrics.csv")
    policies = {row["policy_variant_id"] for row in metrics}
    require(policies == {"expert_payoff_top5_v2", "expert_payoff_top10_v2", "expert_hurdle_top10_v2"}, "unexpected policy set")
    require(any(row["beats_benchmark"] == "1" for row in metrics), "expected at least one QQQ diagnostic beat")
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "metric changed strategy acceptance")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "metric changed deployment readiness")
        require(row["real_capital"] == "FORBIDDEN", "metric changed real capital")
        require(row["target_cagr_30pct_met"] == "0", "metric claims CAGR target met")
    gate = read_csv(OUT_DIR / "task1404_acceptance_gate.csv")[0]
    require(gate["best_policy_variant_id"] == "expert_payoff_top5_v2", "unexpected best policy")
    require(gate["decision"] == "diagnostic_expert_reviewed_replay_not_accepted", "gate overclaimed acceptance")
    require(gate["strategy_acceptance"] == "NOT_ACCEPTED", "gate changed strategy acceptance")
    require(gate["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "gate changed deployment readiness")
    require(gate["real_capital"] == "FORBIDDEN", "gate changed real capital")


def validate_report_footer() -> None:
    text = REPORT.read_text(encoding="utf-8")
    require("Test results do not modify strategy acceptance status." in text, "missing test authority footer")
    require("Strategy: NOT_ACCEPTED" in text, "missing strategy footer")
    require("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in text, "missing deployment footer")
    require("Real Capital: FORBIDDEN" in text, "missing real-capital footer")


def main() -> None:
    validate_files()
    validate_expert_loop()
    validate_no_future_assignment()
    validate_candidate_panels()
    validate_policy_replay()
    validate_audit_split_metrics_and_gate()
    validate_report_footer()
    print("[PASS] Task1388-1407 expert reviewed judgment replay validation")


if __name__ == "__main__":
    main()
