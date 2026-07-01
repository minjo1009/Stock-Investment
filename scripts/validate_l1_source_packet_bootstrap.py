from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TASK_ID = "TASK-4133"
SLUG = "task_4133_l1_development_plan"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(title: str, passes: list[str], warnings: list[str], failures: list[str]) -> int:
    print(title)
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print(f"RESULT: {result}")
    report = {
        "task_id": TASK_ID,
        "result": result,
        "passes": passes,
        "warnings": warnings,
        "failures": failures,
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "validator_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    validation_md = "# TASK-4133 Validation Results\n\n"
    validation_md += f"Result: `{result}`\n\n"
    for label, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        validation_md += f"## {label}\n\n"
        if items:
            validation_md += "\n".join(f"- {item}" for item in items) + "\n\n"
        else:
            validation_md += "- none\n\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "validation_results.md").write_text(validation_md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from tools.db.source_acquisition.l1_bootstrap import build_and_write

    build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        ARTIFACT_DIR / "l1_packet_schema.json",
        ARTIFACT_DIR / "l1_normalized_source_packets_sample.csv",
        ARTIFACT_DIR / "l1_source_time_gate.csv",
        ARTIFACT_DIR / "l1_raw_integrity_gate.csv",
        ARTIFACT_DIR / "l1_mapping_gate.csv",
        ARTIFACT_DIR / "l1_authority_gate.csv",
        ARTIFACT_DIR / "l1_source_gap_ledger.csv",
        ARTIFACT_DIR / "l1_l2_handoff_candidates_sample.csv",
        ARTIFACT_DIR / "l1_gate_summary.csv",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l1_scope_and_safety_boundaries.md",
        REPORT_DIR / "l1_bootstrap_summary.json",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    if failures:
        return emit("L1 SOURCE PACKET BOOTSTRAP VALIDATION", passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    schema = json.loads((ARTIFACT_DIR / "l1_packet_schema.json").read_text(encoding="utf-8"))
    packets = read_csv(ARTIFACT_DIR / "l1_normalized_source_packets_sample.csv")
    handoffs = read_csv(ARTIFACT_DIR / "l1_l2_handoff_candidates_sample.csv")
    gaps = read_csv(ARTIFACT_DIR / "l1_source_gap_ledger.csv")
    required_columns = set(schema["required_columns"])
    packet_columns = set(packets[0].keys()) if packets else set()
    if not required_columns.issubset(packet_columns):
        failures.append("normalized packet sample missing required source packet columns")
    else:
        passes.append("required_packet_columns_present")
    if not packets:
        failures.append("normalized packet sample has no rows")
    else:
        passes.append(f"packet_rows: {len(packets)}")

    for row in packets:
        if row["task_id"] != TASK_ID:
            failures.append(f"unexpected task_id in packet: {row['source_packet_id']}")
        if row["missing_source_is_negative"] != "0":
            failures.append(f"missing source used as negative evidence: {row['source_packet_id']}")
        if row["assignment_uses_future_outcome"] != "0" or row["outcome_used_for_assignment"] != "0":
            failures.append(f"future outcome leakage flag open: {row['source_packet_id']}")
        if row["proxy_feature_allowed"] != "0":
            failures.append(f"proxy feature gate unexpectedly open: {row['source_packet_id']}")
        if row["l1_gate_classification"].startswith("BLOCKED") and row["strict_gate_pass"] == "1":
            failures.append(f"blocked row has strict pass: {row['source_packet_id']}")
        if row["endpoint_or_source_family"] == "market_bars_5m" and row["raw_locator_type"] != "sqlite_partition_hash":
            failures.append("market_bars_5m row must use sqlite_partition_hash raw locator")
        if row["authority"] == "DISCOVERY_HINT" and row["l1_gate_classification"] != "DISCOVERY_ONLY":
            failures.append("discovery hint row promoted outside DISCOVERY_ONLY")
        if row["authority"] == "PUBLIC_CONTEXT_PRIMARY" and row["l1_gate_classification"] == "STRICT_SOURCE_TIME_CERTIFIED":
            failures.append("macro/context row promoted to strict trading feature class")

    trading_authority_rows = [row for row in handoffs if row.get("trading_authority") != "0" or row.get("write_l2_materialization") != "0"]
    if trading_authority_rows:
        failures.append("handoff candidate opens trading authority or writes L2 materialization")
    else:
        passes.append(f"handoff_candidates_diagnostic_only: {len(handoffs)}")
    if any(row.get("missing_source_is_negative") != "0" for row in gaps):
        failures.append("gap ledger has missing_source_is_negative != 0")
    else:
        passes.append(f"gap_rows_unknown_not_negative: {len(gaps)}")
    daily_packets = [row for row in packets if row.get("endpoint_or_source_family") == "daily_bars"]
    daily_gaps = [row for row in gaps if row.get("source_family") == "daily_bars"]
    if daily_packets:
        passes.append("daily_bars_data_present_sampled")
    elif not daily_gaps:
        warnings.append("daily_bars has neither packet nor gap row")

    return emit("L1 SOURCE PACKET BOOTSTRAP VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
