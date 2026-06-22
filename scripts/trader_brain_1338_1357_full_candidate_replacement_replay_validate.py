from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1338_1357_full_candidate_replacement_replay"
REPORT = ROOT / "docs/reports/task_1338_1357_full_candidate_replacement_replay/task_1338_1357_full_candidate_replacement_replay.md"
AUTHORITY = "DIAGNOSTIC_FULL_CANDIDATE_REPLACEMENT_REPLAY_ONLY"

REQUIRED_FILES = {
    "task1338_policy_catalog.csv": 3,
    "task1339_l4_replacement_rank_panel.csv": 3100,
    "task1340_l5_replacement_policy_specs.csv": 9300,
    "task1341_replay_trades.csv": 1116,
    "task1342_replay_equity.csv": 186,
    "task1343_replay_metrics.csv": 3,
    "task1344_interpretation_attribution.csv": 1,
    "task1345_replacement_audit.csv": 186,
    "task1346_acceptance_gate.csv": 1,
    "task1357_closeout.csv": 1,
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


def validate_rank_panel() -> None:
    rows = read_csv(OUT_DIR / "task1339_l4_replacement_rank_panel.csv")
    by_decision: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        require(row["assignment_uses_future_outcome"] == "0", "future assignment used in rank panel")
        require(row["selection_promoted"] == "0", "rank panel promoted selection")
        require(row["authority"] == AUTHORITY, "rank panel authority mismatch")
        by_decision.setdefault(row["decision_asof_ts"], []).append(row)
    require(len(by_decision) == 62, "expected 62 decision cohorts")
    for decision_ts, items in by_decision.items():
        require(len(items) == 50, f"{decision_ts} does not have 50 candidates")
        ranks = sorted(int(row["replacement_rank_within_decision"]) for row in items)
        require(ranks == list(range(1, 51)), f"{decision_ts} replacement ranks are not 1..50")


def validate_policy_specs_and_trades() -> None:
    specs = read_csv(OUT_DIR / "task1340_l5_replacement_policy_specs.csv")
    selected_by_policy: dict[str, int] = {}
    for row in specs:
        require(row["assignment_uses_future_outcome"] == "0", "future assignment used in policy specs")
        require(row["selection_promoted"] == "0", "policy spec promoted selection")
        selected_by_policy[row["policy_variant_id"]] = selected_by_policy.get(row["policy_variant_id"], 0) + int(row["selected_for_replay"])
    require(selected_by_policy["full_candidate_l2l3_replace_top3_v1"] == 186, "top3 selected count mismatch")
    require(selected_by_policy["full_candidate_l2l3_replace_top5_v1"] == 310, "top5 selected count mismatch")
    require(selected_by_policy["full_candidate_l2l3_replace_top10_v1"] == 620, "top10 selected count mismatch")
    trades = read_csv(OUT_DIR / "task1341_replay_trades.csv")
    require(len(trades) == 1116, "trade count mismatch")
    for row in trades:
        require(row["assignment_uses_future_outcome"] == "0", "future assignment used in trades")
        require(row["exit_uses_post_entry_price_path"] == "1", "trade must mark post-entry exit path")
        require(row["authority"] == AUTHORITY, "trade authority mismatch")


def validate_metrics_and_gate() -> None:
    metrics = read_csv(OUT_DIR / "task1343_replay_metrics.csv")
    policies = {row["policy_variant_id"] for row in metrics}
    require(
        policies
        == {
            "full_candidate_l2l3_replace_top3_v1",
            "full_candidate_l2l3_replace_top5_v1",
            "full_candidate_l2l3_replace_top10_v1",
        },
        "unexpected policy set",
    )
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "metric changed strategy acceptance")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "metric changed deployment readiness")
        require(row["real_capital"] == "FORBIDDEN", "metric changed real capital")
    gate = read_csv(OUT_DIR / "task1346_acceptance_gate.csv")[0]
    require(gate["best_policy_variant_id"] == "full_candidate_l2l3_replace_top10_v1", "unexpected best policy")
    require(gate["strategy_acceptance"] == "NOT_ACCEPTED", "gate changed strategy acceptance")
    require(gate["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "gate changed deployment readiness")
    require(gate["real_capital"] == "FORBIDDEN", "gate changed real capital")
    require(gate["decision"] == "diagnostic_replay_not_accepted", "gate overclaimed acceptance")


def validate_report_footer() -> None:
    text = REPORT.read_text(encoding="utf-8")
    require("Test results do not modify strategy acceptance status." in text, "missing test authority footer")
    require("Strategy: NOT_ACCEPTED" in text, "missing strategy footer")
    require("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in text, "missing deployment footer")
    require("Real Capital: FORBIDDEN" in text, "missing real-capital footer")


def main() -> None:
    validate_files()
    validate_rank_panel()
    validate_policy_specs_and_trades()
    validate_metrics_and_gate()
    validate_report_footer()
    print("[PASS] Task1338-1357 full candidate replacement replay validation")


if __name__ == "__main__":
    main()
