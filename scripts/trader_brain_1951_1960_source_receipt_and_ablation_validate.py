from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1951_1960_source_receipt_and_ablation"
REPORT = ROOT / "docs/reports/task_1951_1960_source_receipt_and_ablation/task_1951_1960_source_receipt_and_ablation.md"
DECISION = ROOT / "docs/reports/task_1951_1960_source_receipt_and_ablation/task_1951_1960_decision.csv"
AUTHORITY = "DIAGNOSTIC_SOURCE_RECEIPT_ABLATION_ONLY"

REQUIRED_COUNTS = {
    "task1951_source_receipt_input_manifest.csv": 11,
    "task1952_event_breadth_source_receipt_manifest.csv": 687,
    "task1953_macro_vintage_attempt_ledger.csv": 69,
    "task1954_issuer_public_guidance_probe.csv": 377,
    "task1955_expectation_source_recertification.csv": 377,
    "task1956_primitive_ablation_replay_metrics.csv": 6,
    "task1957_source_receipt_hardened_l4.csv": 377,
    "task1958_source_receipt_top3_replay_trades.csv": 160,
    "task1958_source_receipt_top3_replay_equity.csv": 61,
    "task1958_source_receipt_top3_replay_metrics.csv": 1,
    "task1958_split_oos_metrics.csv": 2,
    "task1958_cost_stress_metrics.csv": 4,
    "task1959_top5_promotion_blocker_audit.csv": 217,
    "task1960_acceptance_gate.csv": 1,
    "task1960_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_COUNTS:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1960_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts_and_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment")


def validate_source_receipt_gates() -> None:
    receipts = read_csv(OUT_DIR / "task1952_event_breadth_source_receipt_manifest.csv")
    fail_if(sum(1 for row in receipts if row["source_family"] == "price_event_window") != 377, "event receipt count mismatch")
    fail_if(sum(1 for row in receipts if row["source_family"] == "theme_breadth") != 310, "breadth receipt count mismatch")
    fail_if(any(row["raw_source_certification"] not in {"raw_ohlcv_manifest_not_in_this_task", "raw_candidate_cross_section_manifest_not_in_this_task"} for row in receipts), "raw source certification overclaim")
    macro = read_csv(OUT_DIR / "task1953_macro_vintage_attempt_ledger.csv")
    fail_if(any(row["alfred_vintage_certified"] != "0" for row in macro), "ALFRED vintage should not be certified")
    fail_if(any(row["active_score_permission"] != "shadow_only" for row in macro), "macro active score not shadow-only")
    series_rows = [row for row in macro if row["series_id"] != "DECISION_GATE"]
    fail_if(not series_rows, "missing macro series rows")
    fail_if(any(to_float(row.get("vintage_asof_certified_row_count")) != 0 for row in series_rows), "macro vintage certified row count should be zero")


def validate_guidance_and_analyst_separation() -> None:
    guidance = read_csv(OUT_DIR / "task1954_issuer_public_guidance_probe.csv")
    fail_if(not any(row["issuer_public_guidance_receipt_state"] == "issuer_public_text_hit_asof" for row in guidance), "no issuer-public guidance hits")
    for idx, row in enumerate(guidance, start=2):
        fail_if(row["analyst_revision_certified"] != "0", f"analyst revision incorrectly certified at row {idx}")
        fail_if(row["asof_guard_pass"] != "1", f"issuer guidance asof guard failed at row {idx}")
        if row["issuer_public_guidance_receipt_state"] == "issuer_public_text_hit_asof":
            fail_if(not row["cik"] or not row["accession"] or not row["sha256"], f"missing SEC identity/hash at row {idx}")
            fail_if(not row["snippet_hash"], f"missing snippet hash at row {idx}")
    expectation = read_csv(OUT_DIR / "task1955_expectation_source_recertification.csv")
    fail_if(any(row["analyst_revision_certified"] != "0" for row in expectation), "expectation gate certified analyst revision")
    fail_if(any(row["vendor_gate_verdict"] != "vendor_blocked_schema_only" for row in expectation), "vendor gate should remain blocked")
    fail_if(not any(row["active_score_permission"] == "small_support_credit_only" for row in expectation), "issuer support credit never applied")
    fail_if(not any(row["active_score_permission"] == "remove_remaining_proxy_credit" for row in expectation), "proxy removal never applied")


def validate_replay_ablation_top5_and_closeout() -> None:
    metric = read_csv(OUT_DIR / "task1958_source_receipt_top3_replay_metrics.csv")[0]
    fail_if(metric["policy_variant_id"] != "source_receipt_hardened_top3_v1", "unexpected policy")
    fail_if(metric["joint_target_met"] != "1", "diagnostic joint target not met")
    fail_if(to_float(metric["final_equity"]) <= to_float(metric["baseline_final_equity"]), "receipt replay did not beat baseline")
    fail_if(metric["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    ablations = read_csv(OUT_DIR / "task1956_primitive_ablation_replay_metrics.csv")
    fail_if(any(row["outcome_used_for_assignment"] != "0" for row in ablations), "ablation used outcome for assignment")
    fail_if(not any(to_float(row["delta_vs_full_receipt_final_audit_only"]) < 0 for row in ablations), "no ablation degraded result")
    top5 = read_csv(OUT_DIR / "task1959_top5_promotion_blocker_audit.csv")
    fail_if(any(row["replay_executed"] != "0" for row in top5), "top5 replay should not execute")
    fail_if(any(row["receipt_top5_gate"] == "shadow_candidate_requires_frozen_top5_replay" for row in top5), "top5 candidate unexpectedly promoted")
    closeout = read_csv(OUT_DIR / "task1960_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "closeout strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")
    payload = json.loads((OUT_DIR / "task1960_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "source_receipt_ablation_complete_diagnostic_only", "json verdict mismatch")


def validate_report() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Source Receipt And Ablation",
        "Macro remains shadow-only",
        "Analyst revision remains vendor-gated",
        "Event and breadth receipts are explicit derived as-of fields",
        "Strategy acceptance status: `NOT_ACCEPTED`",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in text, f"report missing phrase {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_source_receipt_gates()
        validate_guidance_and_analyst_separation()
        validate_replay_ablation_top5_and_closeout()
        validate_report()
    except AssertionError as exc:
        print(f"[TASK1951_1960_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1951_1960_VALIDATE_OK] source receipt and ablation artifacts are valid")


if __name__ == "__main__":
    main()
