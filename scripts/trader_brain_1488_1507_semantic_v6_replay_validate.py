from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
REPORT = ROOT / "docs/reports/task_1488_1507_semantic_v6_replay/task_1488_1507_semantic_v6_replay.md"

REQUIRED = [
    "task1488_expert_review_loop.csv",
    "task1489_v6_preregistered_spec.csv",
    "task1490_source_evidence_audit.csv",
    "task1491_l2_semantic_v6_panel.csv",
    "task1492_l3_mechanism_v3_edges.csv",
    "task1493_l4_thesis_cards_v6.csv",
    "task1494_payoff_ranker_v6.csv",
    "task1495_policy_specs.csv",
    "task1496_source_receipt_exit_panel.csv",
    "task1496_price_path_exit_panel.csv",
    "task1496_hold_receipt_panel.csv",
    "task1497_replay_trades.csv",
    "task1497_replay_equity.csv",
    "task1497_replay_metrics.csv",
    "task1502_displacement_audit.csv",
    "task1503_summary.csv",
    "task1506_acceptance_gate.csv",
    "task1507_closeout.csv",
    "task1507_closeout.json",
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
            print(f"[TASK1488_1507_ERROR] {error}")
        return 1

    reviews = read_csv(OUT_DIR / "task1488_expert_review_loop.csv")
    specs = read_csv(OUT_DIR / "task1489_v6_preregistered_spec.csv")
    l2 = read_csv(OUT_DIR / "task1491_l2_semantic_v6_panel.csv")
    l3 = read_csv(OUT_DIR / "task1492_l3_mechanism_v3_edges.csv")
    thesis = read_csv(OUT_DIR / "task1493_l4_thesis_cards_v6.csv")
    ranks = read_csv(OUT_DIR / "task1494_payoff_ranker_v6.csv")
    policy = read_csv(OUT_DIR / "task1495_policy_specs.csv")
    trades = read_csv(OUT_DIR / "task1497_replay_trades.csv")
    metrics = read_csv(OUT_DIR / "task1497_replay_metrics.csv")
    audit = read_csv(OUT_DIR / "task1502_displacement_audit.csv")
    gate = read_csv(OUT_DIR / "task1506_acceptance_gate.csv")

    if len(reviews) < 10:
        errors.append("expert review loop too small")
    required_rules = {"event_family_first", "no_standalone_materiality_bonus", "source_gap_neutral", "good_words_not_surprise", "strict_absorption", "audit_only_outcomes"}
    present_rules = {row["rule_name"] for row in specs}
    if not required_rules <= present_rules:
        errors.append(f"missing preregistered rules: {sorted(required_rules - present_rules)}")
    if len(l2) != 3100 or len(thesis) != 3100 or len(ranks) != 3100:
        errors.append(f"expected 3100 L2/thesis/rank rows, got {len(l2)}/{len(thesis)}/{len(ranks)}")
    if len(l3) != 15500:
        errors.append(f"expected 15500 L3 edges, got {len(l3)}")
    event_families = {row["event_family"] for row in l2}
    required_families = {"positive", "survival", "financing", "dilution", "mixed", "unknown"}
    if not required_families <= event_families:
        errors.append(f"event family coverage missing: {sorted(required_families - event_families)}")
    expectation_states = {row["expectation_v6_state"] for row in l2}
    for required in ["good_words_only", "true_surprise_proxy", "guidance_change_proxy", "expectation_source_gap"]:
        if required not in expectation_states:
            errors.append(f"missing expectation state: {required}")
    absorption_states = {row["absorption_v6_state"] for row in l2}
    for required in ["sustained_market_acceptance", "initial_reaction_only", "neutral_absorption"]:
        if required not in absorption_states:
            errors.append(f"missing absorption state: {required}")
    for row in l2 + l3 + thesis + ranks + policy:
        if row.get("assignment_uses_future_outcome") != "0":
            errors.append(f"future assignment flag nonzero: {row.get('candidate_source_id') or row.get('edge_id')}")
    for row in l2:
        if row["event_family"] in {"survival", "dilution"} and float(row["materiality_v6_score"]) > 0:
            errors.append(f"negative event family received positive materiality: {row['candidate_source_id']}")
        if row["expectation_v6_state"] == "good_words_only" and row["expectation_v6_score"] == "18.0":
            errors.append(f"good words mis-scored as true surprise: {row['candidate_source_id']}")

    counts: dict[str, int] = {}
    for row in policy:
        counts[row["policy_variant_id"]] = counts.get(row["policy_variant_id"], 0) + 1
    expected_counts = {"semantic_v6_top3_v1": 186, "semantic_v6_top5_v1": 310, "semantic_v6_top10_v1": 620}
    if counts != expected_counts:
        errors.append(f"policy counts mismatch: {counts}")
    if len(metrics) != 3:
        errors.append(f"expected 3 metric rows, found {len(metrics)}")
    if len(trades) != 1116:
        errors.append(f"expected 1116 replay trades, found {len(trades)}")
    for row in metrics:
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append(f"strategy overclaim: {row['policy_variant_id']}")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append(f"deployment overclaim: {row['policy_variant_id']}")
        if row["real_capital"] != "FORBIDDEN":
            errors.append(f"real capital overclaim: {row['policy_variant_id']}")
    for row in audit:
        if row["outcome_used_for_assignment"] != "0" or row["outcome_used_for_audit_only"] != "1":
            errors.append(f"audit outcome misuse: {row['audit_id']}")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED" or gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("acceptance gate overclaims")
    report_text = REPORT.read_text(encoding="utf-8")
    if "큰 이벤트를 바로 좋은 이벤트로 보지 않는다." not in report_text:
        errors.append("report missing no-background semantic explanation")
    if "Test results do not modify strategy acceptance status." not in report_text:
        errors.append("report missing validation footer")

    if errors:
        for error in errors:
            print(f"[TASK1488_1507_ERROR] {error}")
        return 1
    print("[TASK1488_1507_OK] semantic v6 replay artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
