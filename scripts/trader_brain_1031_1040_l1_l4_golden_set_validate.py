from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1031_1040_l1_l4_golden_set"
SOURCE_CATALOG = ROOT / "data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1021_institutional_source_catalog.csv"

REQUIRED_FILES = [
    "task1031_l1_golden_source_contract_rows.csv",
    "task1032_l2_golden_primitive_rows.csv",
    "task1033_l3_golden_mechanism_rows.csv",
    "task1034_l4_golden_thesis_card_rows.csv",
    "task1035_source_to_thesis_golden_set.csv",
    "task1036_cross_read_chain_golden_rows.csv",
    "task1037_l1_l4_golden_validation_results.csv",
    "task1037_negative_golden_failure_cases.csv",
    "task1038_gpt_expert_feedback_synthesis.csv",
    "task1039_no_replay_gate.csv",
    "task1040_golden_set_closeout.csv",
    "task1031_1040_summary.csv",
    "task1031_1040_summary.json",
    "artifact_manifest.csv",
]

REQUIRED_BUCKETS = {
    "macro",
    "policy",
    "semiconductors",
    "ai",
    "energy_power",
    "space",
    "cyber",
    "contradiction",
    "stale_thesis",
    "cross_read",
}

FORBIDDEN_TOKENS = {
    "future_return",
    "pnl",
    "realized_return",
    "outcome_rank",
    "post_entry_price_change",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def has_forbidden_value(row: dict[str, str]) -> bool:
    text = " ".join(str(value).lower() for value in row.values())
    return any(token in text for token in FORBIDDEN_TOKENS)


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    catalog_names = {row["source_name"] for row in rows(SOURCE_CATALOG)}
    l1 = rows(ART / "task1031_l1_golden_source_contract_rows.csv")
    l2 = rows(ART / "task1032_l2_golden_primitive_rows.csv")
    l3 = rows(ART / "task1033_l3_golden_mechanism_rows.csv")
    l4 = rows(ART / "task1034_l4_golden_thesis_card_rows.csv")
    golden = rows(ART / "task1035_source_to_thesis_golden_set.csv")
    cross_read = rows(ART / "task1036_cross_read_chain_golden_rows.csv")
    validation = rows(ART / "task1037_l1_l4_golden_validation_results.csv")
    negatives = rows(ART / "task1037_negative_golden_failure_cases.csv")
    feedback = rows(ART / "task1038_gpt_expert_feedback_synthesis.csv")
    closeout = rows(ART / "task1040_golden_set_closeout.csv")
    summary = json.loads((ART / "task1031_1040_summary.json").read_text(encoding="utf-8"))

    if len(golden) != 20:
        errors.append("golden set must have exactly 20 cases")
    for name, table in {
        "l1": l1,
        "l2": l2,
        "l3": l3,
        "l4": l4,
        "cross_read": cross_read,
        "validation": validation,
    }.items():
        if len(table) != 20:
            errors.append(f"{name} table must have exactly 20 rows")

    bucket_counts = {bucket: 0 for bucket in REQUIRED_BUCKETS}
    for row in golden:
        bucket = row.get("case_bucket", "")
        if bucket in bucket_counts:
            bucket_counts[bucket] += 1
    if any(count != 2 for count in bucket_counts.values()):
        errors.append(f"golden buckets must be 10 buckets x 2 cases, got {bucket_counts}")

    l1_by_case = {row["case_id"]: row for row in l1}
    l2_by_case = {row["case_id"]: row for row in l2}
    l3_by_case = {row["case_id"]: row for row in l3}
    l4_by_case = {row["case_id"]: row for row in l4}
    validation_by_case = {row["case_id"]: row for row in validation}

    for row in golden:
        case_id = row["case_id"]
        if row["source_name"] not in catalog_names:
            errors.append(f"{case_id} source not in institutional catalog")
        if row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0":
            errors.append(f"{case_id} cannot permit selection or replay")
        if case_id not in l1_by_case or case_id not in l2_by_case or case_id not in l3_by_case or case_id not in l4_by_case:
            errors.append(f"{case_id} missing L1/L2/L3/L4 chain")
            continue
        if row["l1_id"] != l1_by_case[case_id]["l1_id"]:
            errors.append(f"{case_id} L1 id mismatch")
        if row["l2_id"] != l2_by_case[case_id]["l2_id"]:
            errors.append(f"{case_id} L2 id mismatch")
        if row["l3_id"] != l3_by_case[case_id]["l3_id"]:
            errors.append(f"{case_id} L3 id mismatch")
        if row["l4_id"] != l4_by_case[case_id]["l4_id"]:
            errors.append(f"{case_id} L4 id mismatch")

    for row in l1:
        if row["download_state"] == "missing_from_catalog":
            errors.append(f"{row['case_id']} source cannot be missing from catalog")
        if row["source_url"] == "":
            errors.append(f"{row['case_id']} source_url required")
        if row["selection_use_allowed"] != "0" or row["replay_use_allowed"] != "0":
            errors.append(f"{row['case_id']} L1 cannot permit selection or replay")

    for row in l2:
        forbidden = row["forbidden_fields"].lower()
        if not FORBIDDEN_TOKENS <= set(forbidden.split()):
            errors.append(f"{row['case_id']} L2 forbidden field set incomplete")

    for row in l4:
        if row["outcome_used_for_assignment_flag"] != "0":
            errors.append(f"{row['case_id']} L4 outcome assignment flag must be 0")
        if row["trade_instruction_allowed"] != "0":
            errors.append(f"{row['case_id']} L4 trade instruction must be forbidden")
        if has_forbidden_value({k: v for k, v in row.items() if k != "invalidation_path"}):
            errors.append(f"{row['case_id']} L4 contains forbidden outcome token")

    for row in validation_by_case.values():
        required_flags = [
            "l1_present",
            "l2_present",
            "l3_present",
            "l4_present",
            "source_to_l4_chain_complete",
            "leakage_timestamp_guard_present",
            "source_hash_or_gap_reported",
        ]
        if any(row[field] != "1" for field in required_flags):
            errors.append(f"{row['case_id']} validation positive flags incomplete")
        zero_flags = [
            "forbidden_outcome_fields_present",
            "outcome_used_for_assignment_flag",
            "trade_instruction_allowed",
            "selection_use_allowed",
            "replay_use_allowed",
        ]
        if any(row[field] != "0" for field in zero_flags):
            errors.append(f"{row['case_id']} validation zero flags violated")

    if len(negatives) < 6:
        errors.append("negative failure cases must have at least 6 rows")
    if {row["expected_validator_action"] for row in negatives} != {"fail"}:
        errors.append("all negative fixtures must be expected to fail")

    reviewer_roles = {row["reviewer_role"] for row in feedback}
    if not {"gauss_external_audit", "franklin_backend_audit"} <= reviewer_roles:
        errors.append("GPT/subagent audit synthesis missing required reviewers")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["golden_case_count"] != "20":
            errors.append("closeout must record 20 cases")
        if row["bucket_contract"] != "10_buckets_x_2_cases":
            errors.append("closeout must record bucket contract")
        if row["replay_executed"] != "0":
            errors.append("closeout must record no replay")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("closeout changed strategy acceptance")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("closeout changed deployment readiness")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("closeout changed real capital")

    if summary.get("golden_case_count") != 20:
        errors.append("summary must record 20 cases")
    if summary.get("bucket_contract") != "10_buckets_x_2_cases":
        errors.append("summary must record bucket contract")
    if summary.get("replay_executed") != "0":
        errors.append("summary must record no replay")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("summary changed strategy acceptance")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("summary changed deployment readiness")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("summary changed real capital")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1031_1040_L1_L4_GOLDEN_SET_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1031_1040_L1_L4_GOLDEN_SET_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
