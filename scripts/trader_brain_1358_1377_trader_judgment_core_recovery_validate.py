from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1358_1377_trader_judgment_core_recovery"
REPORT = ROOT / "docs/reports/task_1358_1377_trader_judgment_core_recovery/task_1358_1377_trader_judgment_core_recovery.md"
AUTHORITY = "DIAGNOSTIC_TRADER_JUDGMENT_CORE_RECOVERY_ONLY"

REQUIRED_FILES = {
    "task1358_core_requirement_map.csv": 9,
    "task1359_split_freeze.csv": 62,
    "task1360_replacement_pair_audit.csv": 1,
    "task1361_l2_materiality_surprise_primitives.csv": 3100,
    "task1362_l3_mechanism_edges.csv": 15500,
    "task1363_l4_payoff_rank_panel.csv": 3100,
    "task1364_l5_dynamic_exit_receipts.csv": 1550,
    "task1365_overfit_guard_ledger.csv": 2,
    "task1366_policy_catalog.csv": 3,
    "task1367_l5_policy_specs.csv": 9300,
    "task1368_replay_trades.csv": 1550,
    "task1369_replay_equity.csv": 186,
    "task1370_replay_metrics.csv": 3,
    "task1372_acceptance_gate.csv": 1,
    "task1377_closeout.csv": 1,
    "artifact_manifest.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name, minimum_rows in REQUIRED_FILES.items():
        path = OUT_DIR / name
        require(path.exists(), f"missing artifact: {name}")
        rows = read_csv(path)
        require(len(rows) >= minimum_rows, f"{name} row count {len(rows)} < {minimum_rows}")


def validate_requirement_map() -> None:
    rows = read_csv(OUT_DIR / "task1358_core_requirement_map.csv")
    requirements = {row["core_requirement"] for row in rows}
    expected = {
        "materiality",
        "surprise_expectation",
        "source_independence",
        "mechanism_edge",
        "payoff_ranker",
        "dynamic_exit_receipt",
        "oos_split_freeze",
        "overfit_guard",
        "replacement_pair_audit",
    }
    require(expected <= requirements, "missing core recovery requirement")
    require(all(row["authority"] == AUTHORITY for row in rows), "requirement authority mismatch")


def validate_no_future_assignment() -> None:
    for filename in [
        "task1361_l2_materiality_surprise_primitives.csv",
        "task1362_l3_mechanism_edges.csv",
        "task1363_l4_payoff_rank_panel.csv",
        "task1364_l5_dynamic_exit_receipts.csv",
        "task1367_l5_policy_specs.csv",
    ]:
        for row in read_csv(OUT_DIR / filename):
            require(row["assignment_uses_future_outcome"] == "0", f"future outcome assignment in {filename}")
            require(row["authority"] == AUTHORITY, f"authority mismatch in {filename}")


def validate_split_freeze() -> None:
    rows = read_csv(OUT_DIR / "task1359_split_freeze.csv")
    split_counts: dict[str, int] = {}
    for row in rows:
        split_counts[row["split_id"]] = split_counts.get(row["split_id"], 0) + 1
        if row["split_id"] == "train_2021_2023":
            require(row["policy_parameter_tuning_allowed"] == "1", "train split should allow parameter review")
            require(row["oos_score_only"] == "0", "train split cannot be OOS score-only")
        if row["split_id"] == "validation_2024":
            require(row["policy_parameter_tuning_allowed"] == "0", "validation split cannot allow tuning")
            require(row["validation_selection_allowed"] == "1", "validation split should allow selection review")
        if row["split_id"] == "oos_2025_2026q1":
            require(row["policy_parameter_tuning_allowed"] == "0", "OOS split cannot allow tuning")
            require(row["oos_score_only"] == "1", "OOS split must be score-only")
    require(split_counts.get("train_2021_2023", 0) > 0, "missing train split")
    require(split_counts.get("validation_2024", 0) > 0, "missing validation split")
    require(split_counts.get("oos_2025_2026q1", 0) > 0, "missing OOS split")


def validate_l2_l3_l4_shapes() -> None:
    primitives = read_csv(OUT_DIR / "task1361_l2_materiality_surprise_primitives.csv")
    mechanisms = read_csv(OUT_DIR / "task1362_l3_mechanism_edges.csv")
    rank_panel = read_csv(OUT_DIR / "task1363_l4_payoff_rank_panel.csv")
    require(len(primitives) == 3100, "expected 3100 L2 primitives")
    require(len(mechanisms) == len(primitives) * 5, "expected five L3 mechanism edges per candidate")
    require(len(rank_panel) == len(primitives), "expected one L4 payoff row per primitive")
    by_decision: dict[str, list[int]] = {}
    for row in rank_panel:
        by_decision.setdefault(row["decision_asof_ts"], []).append(int(row["payoff_rank_within_decision"]))
    require(len(by_decision) == 62, "expected 62 decision cohorts")
    for decision_ts, ranks in by_decision.items():
        require(sorted(ranks) == list(range(1, 51)), f"{decision_ts} payoff ranks are not 1..50")


def validate_replacement_audit() -> None:
    rows = read_csv(OUT_DIR / "task1360_replacement_pair_audit.csv")
    require(rows, "replacement audit is empty")
    buckets = {row["audit_bucket"] for row in rows}
    require("new_replacement_loser" in buckets or "new_replacement_winner" in buckets, "missing new replacement audit rows")
    require("dropped_missed_winner" in buckets or "dropped_correct_loser" in buckets, "missing dropped baseline audit rows")
    for row in rows:
        require(row["outcome_used_for_assignment"] == "0", "replacement audit outcome used for assignment")
        require(row["outcome_used_for_audit_only"] == "1", "replacement audit is not marked audit-only")
        require(row["authority"] == AUTHORITY, "replacement audit authority mismatch")


def validate_policy_and_replay() -> None:
    specs = read_csv(OUT_DIR / "task1367_l5_policy_specs.csv")
    selected: dict[str, int] = {}
    for row in specs:
        selected[row["policy_variant_id"]] = selected.get(row["policy_variant_id"], 0) + int(row["selected_for_replay"])
    require(selected["payoff_core_top5_v1"] == 310, "top5 selected count mismatch")
    require(selected["payoff_core_top10_v1"] == 620, "top10 selected count mismatch")
    require(selected["payoff_hurdle_top10_v1"] == 620, "hurdle top10 selected count mismatch")

    exits = read_csv(OUT_DIR / "task1364_l5_dynamic_exit_receipts.csv")
    ready_count = sum(1 for row in exits if row["dynamic_exit_ready"] == "1")
    require(ready_count >= 1, "dynamic exit receipt never fired")
    trades = read_csv(OUT_DIR / "task1368_replay_trades.csv")
    require(len(trades) == 1550, "trade count mismatch")
    dynamic_trade_count = sum(1 for row in trades if row["exit_reason"] == "dynamic_exit_post_entry_hard_sec_event")
    require(dynamic_trade_count == ready_count, "dynamic exit trade count does not match receipt count")
    for row in trades:
        require(row["assignment_uses_future_outcome"] == "0", "future assignment used in replay trades")
        require(row["exit_uses_post_entry_price_path"] == "1", "trade must mark post-entry exit path")
        require(row["authority"] == AUTHORITY, "trade authority mismatch")


def validate_metrics_and_gate() -> None:
    metrics = read_csv(OUT_DIR / "task1370_replay_metrics.csv")
    policies = {row["policy_variant_id"] for row in metrics}
    require(policies == {"payoff_core_top5_v1", "payoff_core_top10_v1", "payoff_hurdle_top10_v1"}, "unexpected policy set")
    require(any(row["beats_benchmark"] == "1" for row in metrics), "expected at least one QQQ diagnostic beat")
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "metric changed strategy acceptance")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "metric changed deployment readiness")
        require(row["real_capital"] == "FORBIDDEN", "metric changed real capital")
        require(row["target_cagr_30pct_met"] == "0", "diagnostic unexpectedly claims CAGR target met")
    gate = read_csv(OUT_DIR / "task1372_acceptance_gate.csv")[0]
    require(gate["best_policy_variant_id"] == "payoff_core_top5_v1", "unexpected best policy")
    require(gate["strategy_acceptance"] == "NOT_ACCEPTED", "gate changed strategy acceptance")
    require(gate["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "gate changed deployment readiness")
    require(gate["real_capital"] == "FORBIDDEN", "gate changed real capital")
    require(gate["decision"] == "diagnostic_core_recovery_not_accepted", "gate overclaimed acceptance")


def validate_report_footer() -> None:
    text = REPORT.read_text(encoding="utf-8")
    require("Test results do not modify strategy acceptance status." in text, "missing test authority footer")
    require("Strategy: NOT_ACCEPTED" in text, "missing strategy footer")
    require("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in text, "missing deployment footer")
    require("Real Capital: FORBIDDEN" in text, "missing real-capital footer")


def main() -> None:
    validate_files()
    validate_requirement_map()
    validate_no_future_assignment()
    validate_split_freeze()
    validate_l2_l3_l4_shapes()
    validate_replacement_audit()
    validate_policy_and_replay()
    validate_metrics_and_gate()
    validate_report_footer()
    print("[PASS] Task1358-1377 trader judgment core recovery validation")


if __name__ == "__main__":
    main()
