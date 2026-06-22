from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1448_1467_conditional_materiality_ranker"
REPORT = ROOT / "docs/reports/task_1448_1467_conditional_materiality_ranker/task_1448_1467_conditional_materiality_ranker.md"

REQUIRED = [
    "task1448_expert_review_synthesis.csv",
    "task1449_v5_preregistered_spec.csv",
    "task1450_event_family_panel.csv",
    "task1453_conditional_materiality_score_panel.csv",
    "task1454_payoff_ranker_v5.csv",
    "task1455_policy_specs.csv",
    "task1456_source_receipt_exit_panel.csv",
    "task1456_price_path_exit_panel.csv",
    "task1456_hold_receipt_panel.csv",
    "task1456_replay_trades.csv",
    "task1456_replay_equity.csv",
    "task1456_replay_metrics.csv",
    "task1458_displacement_audit.csv",
    "task1459_summary.csv",
    "task1466_acceptance_gate.csv",
    "task1467_closeout.csv",
    "task1467_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (OUT_DIR / name).exists():
            errors.append(f"missing artifact: {name}")
    if not REPORT.exists():
        errors.append(f"missing report: {REPORT}")
    if errors:
        for error in errors:
            print(f"[TASK1448_1467_ERROR] {error}")
        return 1

    events = read_csv(OUT_DIR / "task1450_event_family_panel.csv")
    scores = read_csv(OUT_DIR / "task1453_conditional_materiality_score_panel.csv")
    ranks = read_csv(OUT_DIR / "task1454_payoff_ranker_v5.csv")
    specs = read_csv(OUT_DIR / "task1455_policy_specs.csv")
    audit = read_csv(OUT_DIR / "task1458_displacement_audit.csv")
    metrics = read_csv(OUT_DIR / "task1456_replay_metrics.csv")
    gate = read_csv(OUT_DIR / "task1466_acceptance_gate.csv")

    if len(events) != 3100 or len(scores) != 3100 or len(ranks) != 3100:
        errors.append("expected 3100 rows for event/score/rank panels")
    event_families = {row["event_family"] for row in events}
    required_families = {"positive", "financing", "dilution", "survival", "unknown"}
    if not required_families <= event_families:
        errors.append(f"event family coverage missing: {sorted(required_families - event_families)}")
    for row in scores + ranks:
        if row.get("assignment_uses_future_outcome") != "0":
            errors.append(f"future assignment flag nonzero: {row.get('candidate_source_id')}")
    for row in scores:
        if row["event_family"] in {"dilution", "survival"} and float(row["conditional_materiality_score"]) > 0:
            errors.append(f"negative event family received positive materiality: {row['candidate_source_id']}")

    counts: dict[str, int] = {}
    for row in specs:
        counts[row["policy_variant_id"]] = counts.get(row["policy_variant_id"], 0) + 1
        if row["assignment_uses_future_outcome"] != "0":
            errors.append(f"policy spec future flag nonzero: {row['policy_spec_id']}")
    expected = {"conditional_materiality_top3_v1": 186, "conditional_materiality_top5_v1": 310, "conditional_materiality_top10_v1": 620}
    if counts != expected:
        errors.append(f"policy counts mismatch: {counts}")

    if len(audit) < 400:
        errors.append(f"displacement audit too small: {len(audit)}")
    for row in audit:
        if row["outcome_used_for_assignment"] != "0" or row["outcome_used_for_audit_only"] != "1":
            errors.append(f"audit outcome misuse: {row['audit_id']}")

    if len(metrics) != 3:
        errors.append(f"expected 3 metric rows, found {len(metrics)}")
    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['policy_variant_id']}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")

    if "Test results do not modify strategy acceptance status." not in REPORT.read_text(encoding="utf-8"):
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1448_1467_ERROR] {error}")
        return 1
    print("[TASK1448_1467_OK] conditional materiality ranker artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
