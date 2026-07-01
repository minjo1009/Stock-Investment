from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4138"
SLUG = "task_4138_l1_practical_hardening"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4138 L1 PRACTICAL HARDENING VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    report = {
        "task_id": TASK_ID,
        "result": result,
        "passes": passes,
        "warnings": warnings,
        "failures": failures,
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "validator_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    validation_md = "# TASK-4138 Validation Results\n\n"
    validation_md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        validation_md += f"## {title}\n\n"
        validation_md += "\n".join(f"- {item}" for item in items) if items else "- none"
        validation_md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(validation_md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l1_practical_hardening_4138 import build_and_write

    build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "l1_source_time_precision_policy.csv",
        ARTIFACT_DIR / "l1_wikimedia_noon_policy.csv",
        ARTIFACT_DIR / "l1_feature_block_reason_matrix.csv",
        ARTIFACT_DIR / "l1_repeated_validation_run_state.csv",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l1_practical_hardening_summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing required artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    policy_rows = read_csv(ARTIFACT_DIR / "l1_source_time_precision_policy.csv")
    wikimedia_rows = read_csv(ARTIFACT_DIR / "l1_wikimedia_noon_policy.csv")
    block_rows = read_csv(ARTIFACT_DIR / "l1_feature_block_reason_matrix.csv")
    validation_rows = read_csv(ARTIFACT_DIR / "l1_repeated_validation_run_state.csv")

    if len(policy_rows) < 5:
        failures.append("source family policy must cover at least 5 L1 source families")
    else:
        passes.append(f"source_family_policy_rows: {len(policy_rows)}")

    day_rows = [row for row in wikimedia_rows if row["precision"] == "day"]
    month_rows = [row for row in wikimedia_rows if row["precision"] == "month"]
    year_rows = [row for row in wikimedia_rows if row["precision"] == "year"]
    if not day_rows:
        failures.append("Wikimedia day precision row missing")
    else:
        row = day_rows[0]
        if "12:00:00Z" not in row["normalized_time_policy"]:
            failures.append("Wikimedia day precision must explicitly use noon UTC nominal time")
        if row["is_imputed_time"] != "1":
            failures.append("Wikimedia day precision must be marked imputed")
        if row["strict_source_time_allowed"] != "0" or row["feature_allowed_now"] != "0":
            failures.append("Wikimedia day precision must not open strict source time or feature gates")
        passes.append("wikimedia_day_noon_policy_is_imputed_and_blocked")
    for label, rows in [("month", month_rows), ("year", year_rows)]:
        if not rows:
            failures.append(f"Wikimedia {label} precision row missing")
        elif rows[0]["strict_source_time_allowed"] != "0" or rows[0]["feature_allowed_now"] != "0":
            failures.append(f"Wikimedia {label} precision must remain context/block only")
    if not any("Wikimedia" in failure for failure in failures):
        passes.append("wikimedia_month_year_precision_blocked")

    missing_reason = [row["source_family"] for row in block_rows if not row.get("l1_block_reason") or not row.get("plain_korean_meaning")]
    if missing_reason:
        failures.append(f"block reason missing for source families: {missing_reason}")
    else:
        passes.append(f"block_reasons_present: {len(block_rows)}")

    feature_open = [row["source_family"] for row in policy_rows if row.get("feature_allowed_now") != "0"]
    if feature_open:
        failures.append(f"feature gate unexpectedly opened: {feature_open}")
    else:
        passes.append("all_l1_feature_allowed_now_flags_closed")

    failed_validators = [row for row in validation_rows if row.get("status") != "PASS"]
    if failed_validators:
        failures.append(f"repeated validation failures: {[row['validator'] for row in failed_validators]}")
    else:
        passes.append(f"repeated_validators_passed: {len(validation_rows)}")

    summary = json.loads((REPORT_DIR / "l1_practical_hardening_summary.json").read_text(encoding="utf-8"))
    if summary.get("trading_authority_opened") or summary.get("paper_live_broker_order_opened"):
        failures.append("trading/paper/live/broker/order gate unexpectedly opened")
    else:
        passes.append("trading_paper_live_broker_order_gates_closed")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
