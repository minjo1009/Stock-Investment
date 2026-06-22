from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1848_1867_source_attached_policy_replay"
REPORT = ROOT / "docs/reports/task_1848_1867_source_attached_policy_replay/task_1848_1867_source_attached_policy_replay.md"
DECISION = ROOT / "docs/reports/task_1848_1867_source_attached_policy_replay/task_1848_1867_decision.csv"
AUTHORITY = "DIAGNOSTIC_SOURCE_ATTACHED_POLICY_REPLAY_ONLY"

REQUIRED_FILES = [
    "task1848_expert_review.csv",
    "task1849_source_attach_input_manifest.csv",
    "task1850_rates_l2_meaning_panel.csv",
    "task1851_sec_financing_l2_meaning_panel.csv",
    "task1852_earnings_vendor_block_panel.csv",
    "task1853_l3_targeted_source_edges.csv",
    "task1854_l4_source_attached_thesis_cards.csv",
    "task1855_l5_source_attached_budget.csv",
    "task1856_frozen_policy_config.csv",
    "task1857_controlled_source_attached_replay_trades.csv",
    "task1857_controlled_source_attached_replay_equity.csv",
    "task1858_source_attached_replay_metrics.csv",
    "task1858_split_oos_metrics.csv",
    "task1858_cost_stress_metrics.csv",
    "task1859_failure_attribution.csv",
    "task1860_acceptance_gate.csv",
    "task1867_closeout.csv",
    "task1867_closeout.json",
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
        "task1848_expert_review.csv": 5,
        "task1856_frozen_policy_config.csv": 2,
        "task1858_source_attached_replay_metrics.csv": 2,
        "task1858_split_oos_metrics.csv": 4,
        "task1858_cost_stress_metrics.csv": 8,
        "task1860_acceptance_gate.csv": 1,
        "task1867_closeout.csv": 1,
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


def validate_asof_and_vendor_gate() -> None:
    rates = read_csv(OUT_DIR / "task1850_rates_l2_meaning_panel.csv")
    for idx, row in enumerate(rates, start=2):
        fail_if(row["asof_guard_pass"] != "1", f"rates asof guard failed row {idx}")
        if row["source_available_to_brain_ts"]:
            fail_if(row["source_available_to_brain_ts"] > row["decision_asof_ts"], f"rates source future row {idx}")
    sec = read_csv(OUT_DIR / "task1851_sec_financing_l2_meaning_panel.csv")
    for idx, row in enumerate(sec, start=2):
        fail_if(row["asof_guard_pass"] != "1", f"SEC asof guard failed row {idx}")
        fail_if(row["source_gap_is_negative"] != "0", f"SEC source gap converted to negative row {idx}")
    earnings = read_csv(OUT_DIR / "task1852_earnings_vendor_block_panel.csv")
    for idx, row in enumerate(earnings, start=2):
        fail_if(row["earnings_revision_state"] != "vendor_blocked_schema_only", f"earnings gate not blocked row {idx}")
        fail_if(row["assignment_effect"] != "blocked_no_score_change", f"earnings assignment effect row {idx}")


def validate_metrics_status() -> None:
    metrics = read_csv(OUT_DIR / "task1858_source_attached_replay_metrics.csv")
    fail_if({row["policy_variant_id"] for row in metrics} != {"source_attached_top3_v1", "source_attached_top5_v1"}, "unexpected policy set")
    for row in metrics:
        fail_if(row["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
        fail_if(row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
        fail_if(row["real_capital"] != "FORBIDDEN", "real capital status changed")
    closeout = read_csv(OUT_DIR / "task1867_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    payload = json.loads((OUT_DIR / "task1867_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["strategy_acceptance"] != "NOT_ACCEPTED", "json strategy status changed")


def validate_report_text() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Rates/liquidity",
        "SEC financing/dilution",
        "Earnings revision: blocked",
        "no new price matching",
        "Strategy: NOT_ACCEPTED",
        "Real Capital: FORBIDDEN",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_asof_and_vendor_gate()
        validate_metrics_status()
        validate_report_text()
    except AssertionError as exc:
        print(f"[TASK1848_1867_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1848_1867_VALIDATE_OK] source-attached replay artifacts are valid")


if __name__ == "__main__":
    main()
