from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4134"
SLUG = "task_4134_l1_data_present_risk_burn_down"
DATA_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
TASK4133_DATA_DIR = ROOT / "data" / "artifacts" / "task_4133_l1_development_plan"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("L1 DATA-PRESENT HARDENING VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "validator_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    markdown = f"# TASK-4134 Validation Results\n\nResult: `{result}`\n\n"
    for label, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        markdown += f"## {label}\n\n"
        markdown += "\n".join(f"- {item}" for item in items) if items else "- none"
        markdown += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(markdown, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l1_data_present_hardening import main as run_main

    run_main()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l1_data_present_risk_burn_down_summary.json",
        DATA_DIR / "l1_data_present_inventory.csv",
        DATA_DIR / "l1_data_present_risk_burn_down.csv",
        DATA_DIR / "legacy_l2_bypass_guard.csv",
        TASK4133_DATA_DIR / "l1_normalized_source_packets_sample.csv",
        TASK4133_DATA_DIR / "l1_source_gap_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    if failures:
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")
    packets = read_csv(TASK4133_DATA_DIR / "l1_normalized_source_packets_sample.csv")
    gaps = read_csv(TASK4133_DATA_DIR / "l1_source_gap_ledger.csv")
    inventory = read_csv(DATA_DIR / "l1_data_present_inventory.csv")
    guard = read_csv(DATA_DIR / "legacy_l2_bypass_guard.csv")

    daily_packets = [row for row in packets if row.get("endpoint_or_source_family") == "daily_bars"]
    if not daily_packets:
        failures.append("daily_bars raw data exists but no L1 packet was produced")
    elif daily_packets[0].get("l1_gate_classification") != "STRICT_SOURCE_TIME_CERTIFIED":
        failures.append("daily_bars packet did not pass strict source-time class")
    else:
        passes.append("daily_bars_data_present_packet_strict")
    if any(row.get("source_family") == "daily_bars" for row in gaps):
        failures.append("daily_bars still appears in source gap ledger despite present raw CSV data")
    else:
        passes.append("daily_bars_false_gap_removed")
    if not any(row.get("endpoint_or_source_family") == "market_bars_5m" and row.get("raw_locator_type") == "sqlite_partition_hash" for row in packets):
        failures.append("market_bars_5m packet missing sqlite_partition_hash locator")
    else:
        passes.append("market_bars_5m_partition_hash_retained")
    if any(row.get("authority") == "DISCOVERY_HINT" and row.get("l1_gate_classification") != "DISCOVERY_ONLY" for row in packets):
        failures.append("discovery hint promoted outside DISCOVERY_ONLY")
    else:
        passes.append("discovery_hints_not_promoted")
    if not guard or guard[0].get("blocked_by_default") != "1":
        failures.append("legacy L0-to-L2 ingest is not blocked by default")
    else:
        passes.append("legacy_l2_bypass_blocked_by_default")
    unhandled = [row for row in inventory if row.get("status") != "DATA_PRESENT_L1_HANDLED"]
    if unhandled:
        failures.append(f"data-present source families not handled: {','.join(row.get('source_family', '') for row in unhandled)}")
    else:
        passes.append(f"data_present_families_handled: {len(inventory)}")
    if any(row.get("missing_source_is_negative") != "0" for row in gaps):
        failures.append("gap ledger uses missing source as negative evidence")
    else:
        passes.append("missing_source_remains_unknown_not_negative")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
