from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.trader_brain_graph_batch_validate import build_report_rows, write_report
from scripts.trader_brain_provenance_manifest_linker_validate import validate_graph_provenance
FOOTER = """Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN"""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "gate_status",
        "packet_count",
        "failure_count",
        "provenance_failure_count",
        "strategy_acceptance",
        "deployment_status",
        "real_capital",
        "validation_authority",
        "footer",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--provenance-manifest", required=True, type=Path)
    parser.add_argument("--failure-report", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    report, all_expected = build_report_rows(args.manifest)
    write_report(args.failure_report, report)
    manifest_rows = read_csv(args.manifest)
    provenance_errors: list[str] = []
    for row in manifest_rows:
        if row.get("packet_type") == "graph":
            provenance_errors.extend(
                validate_graph_provenance(resolve_path(row.get("packet_path", "")), args.provenance_manifest)
            )
    failure_count = sum(1 for row in report if row["observed_status"] == "fail")
    gate_status = "diagnostic_only_pass" if all_expected and failure_count == 0 and not provenance_errors else "diagnostic_only_fail"
    write_summary(
        args.summary,
        [
            {
                "gate_status": gate_status,
                "packet_count": str(len(manifest_rows)),
                "failure_count": str(failure_count),
                "provenance_failure_count": str(len(provenance_errors)),
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "validation_authority": "GOVERNANCE_HEALTH",
                "footer": FOOTER,
            }
        ],
    )
    if gate_status != "diagnostic_only_pass":
        for error in provenance_errors:
            print(f"[TRADER_BRAIN_GOVERNANCE_GATE_ERROR] {error}")
        print(f"[TRADER_BRAIN_GOVERNANCE_GATE_FAIL] summary={args.summary}")
        sys.exit(1)
    print(f"[TRADER_BRAIN_GOVERNANCE_GATE_OK] summary={args.summary}")


if __name__ == "__main__":
    main()
