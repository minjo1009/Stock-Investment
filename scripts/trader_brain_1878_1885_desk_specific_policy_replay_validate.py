from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
REPORT = ROOT / "docs/reports/task_1878_1885_desk_specific_policy_replay/task_1878_1885_desk_specific_policy_replay.md"
DECISION = ROOT / "docs/reports/task_1878_1885_desk_specific_policy_replay/task_1878_1885_decision.csv"
AUTHORITY = "DIAGNOSTIC_DESK_SPECIFIC_POLICY_REPLAY_ONLY"

REQUIRED_FILES = [
    "task1878_expert_implementation_review.csv",
    "task1878_input_manifest.csv",
    "task1878_sec_financing_specificity_panel.csv",
    "task1879_winner_thesis_override_panel.csv",
    "task1880_theme_breadth_panel.csv",
    "task1881_l3_desk_relation_edges.csv",
    "task1882_speculative_live_financing_block.csv",
    "task1883_defensive_buffer_validation_panel.csv",
    "task1884_l4_desk_thesis_cards.csv",
    "task1884_l5_desk_specific_budget.csv",
    "task1884_desk_action_audit.csv",
    "task1884_earnings_vendor_block_panel.csv",
    "task1884_frozen_policy_config.csv",
    "task1885_controlled_desk_replay_trades.csv",
    "task1885_controlled_desk_replay_equity.csv",
    "task1885_desk_replay_metrics.csv",
    "task1885_split_oos_metrics.csv",
    "task1885_cost_stress_metrics.csv",
    "task1885_failure_attribution.csv",
    "task1885_acceptance_gate.csv",
    "task1885_closeout.csv",
    "task1885_closeout.json",
    "task1878_1885_task_plan_status.csv",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_FILES:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    expected_counts = {
        "task1878_expert_implementation_review.csv": 5,
        "task1884_frozen_policy_config.csv": 2,
        "task1885_desk_replay_metrics.csv": 2,
        "task1885_split_oos_metrics.csv": 4,
        "task1885_cost_stress_metrics.csv": 8,
        "task1885_acceptance_gate.csv": 1,
        "task1885_closeout.csv": 1,
        "task1878_1885_task_plan_status.csv": 8,
    }
    for name, expected in expected_counts.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} rows got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome guard")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment guard")


def validate_sec_specificity() -> None:
    sec = read_csv(OUT_DIR / "task1878_sec_financing_specificity_panel.csv")
    states = Counter(row["financing_specificity_state"] for row in sec)
    fail_if("live_active_dilution" not in states, "SEC specificity never detects live_active_dilution")
    fail_if(len(states) < 3, f"SEC specificity too narrow: {states}")
    fail_if(states["live_active_dilution"] >= 300, f"live_active_dilution still too broad: {states['live_active_dilution']}")
    for idx, row in enumerate(sec, start=2):
        fail_if(row["asof_guard_pass"] != "1", f"SEC asof guard failed row {idx}")
        fail_if(row["source_gap_is_negative"] != "0", f"source gap became negative row {idx}")
        fail_if(row["financing_specificity_state"] == "source_gap_neutral" and row["financing_current_flag"] != "0", f"source gap current flag row {idx}")
        if row["financing_specificity_state"] == "historical_or_closed_financing":
            fail_if(row["financing_closed_flag"] != "1", f"historical financing missing closed flag row {idx}")
        if row["financing_specificity_state"] == "live_active_dilution":
            fail_if(row["live_terms_detected_flag"] != "1", f"live dilution missing live terms row {idx}")


def validate_winner_and_desk_rules() -> None:
    budget = read_csv(OUT_DIR / "task1884_l5_desk_specific_budget.csv")
    winner = [row for row in budget if row["strategy_sleeve"] == "winner_compounder"]
    fail_if(not winner, "no winner_compounder rows")
    winner_actions = Counter(row["desk_action"] for row in winner)
    fail_if(winner_actions["trim"] >= 50, f"winner broad trim recurred: {winner_actions}")
    fail_if(winner_actions["hold"] < 80, f"winner hold did not recover: {winner_actions}")
    fail_if(sum(1 for row in winner if row["winner_thesis_intact_flag"] == "1") < 50, "winner intact flags too sparse")
    actions_by_sleeve = defaultdict_counter((row["strategy_sleeve"], row["desk_action"]) for row in budget)
    fail_if(len(set(action for (_, action) in actions_by_sleeve)) < 3, "desk actions are not differentiated")
    rule_ids = {row.get("desk_rule_id", "") for row in budget}
    fail_if("" in rule_ids or len(rule_ids) < 6, "desk_rule_id coverage too weak")


def defaultdict_counter(items: object) -> Counter:
    return Counter(items)


def validate_breadth_and_earnings() -> None:
    breadth = read_csv(OUT_DIR / "task1880_theme_breadth_panel.csv")
    fail_if(len(breadth) < 30, "theme breadth panel too small")
    states = {row["theme_breadth_state"] for row in breadth}
    fail_if(not states <= {"theme_breadth_supportive", "theme_breadth_weak", "theme_breadth_neutral", "theme_breadth_sparse_neutral"}, "unexpected breadth state")
    earnings = read_csv(OUT_DIR / "task1884_earnings_vendor_block_panel.csv")
    fail_if(earnings[0]["earnings_revision_state"] != "vendor_blocked_schema_only", "earnings gate changed")
    fail_if(earnings[0]["assignment_effect"] != "blocked_no_score_change", "earnings changed assignment")


def validate_metrics_status() -> None:
    metrics = read_csv(OUT_DIR / "task1885_desk_replay_metrics.csv")
    fail_if({row["policy_variant_id"] for row in metrics} != {"desk_specific_top3_v1", "desk_specific_top5_v1"}, "unexpected policy set")
    for row in metrics:
        fail_if(row["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
        fail_if(row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
        fail_if(row["real_capital"] != "FORBIDDEN", "real capital status changed")
        fail_if(row["beats_qqq"] not in {"0", "1"}, "invalid QQQ flag")
    closeout = read_csv(OUT_DIR / "task1885_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    payload = json.loads((OUT_DIR / "task1885_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["strategy_acceptance"] != "NOT_ACCEPTED", "json strategy status changed")


def validate_report_text() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "SEC financing was repaired",
        "Winner desk gained a thesis-intact override",
        "Theme breadth",
        "no new price matching",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_sec_specificity()
        validate_winner_and_desk_rules()
        validate_breadth_and_earnings()
        validate_metrics_status()
        validate_report_text()
    except AssertionError as exc:
        print(f"[TASK1878_1885_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1878_1885_VALIDATE_OK] desk-specific policy replay artifacts are valid")


if __name__ == "__main__":
    main()
