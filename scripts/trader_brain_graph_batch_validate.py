from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.trader_brain_attention_packet_validate import validate_packet_file
from scripts.trader_brain_relationship_graph_packet_validate import validate_graph_dir

PASS_DOES_NOT_MEAN = (
    "strategy acceptance, deployment readiness, broker truth, backtest validity, "
    "source completeness, or real-capital permission"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def classify_failure(error: str) -> str:
    lowered = error.lower()
    if "missing required_evidence" in lowered:
        return "missing_required_evidence"
    if "missing columns" in lowered or "missing " in lowered and ".csv" in lowered:
        return "schema_missing"
    if "unknown" in lowered:
        return "bad_reference"
    if "cross_layer_jump" in lowered:
        return "unsafe_layer_jump"
    if "sequence" in lowered or "asof_ts" in lowered or "temporal" in lowered:
        return "temporal_order_error"
    if "missing_to_negative" in lowered:
        return "source_gap_conversion"
    if "forbidden output" in lowered:
        return "forbidden_output"
    if "manifest" in lowered or "orphan" in lowered:
        return "manifest_orphan"
    return "validator_error"


def validate_packet(packet_type: str, packet_path: Path) -> tuple[str, list[str], str]:
    if packet_type == "graph":
        return "relationship_graph_packet", validate_graph_dir(packet_path), "RESEARCH_ONLY"
    if packet_type == "attention":
        return "attention_packet", validate_packet_file(packet_path), "RESEARCH_ONLY"
    return "unknown_packet_type", [f"unknown packet_type {packet_type}"], "GOVERNANCE_HEALTH"


def build_report_rows(manifest_path: Path) -> tuple[list[dict[str, str]], bool]:
    rows = read_csv(manifest_path)
    required = {"packet_id", "packet_type", "packet_path", "expected_status"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        return (
            [
                {
                    "packet_id": "<manifest>",
                    "packet_type": "manifest",
                    "packet_path": manifest_path.as_posix(),
                    "validator": "batch_manifest",
                    "expected_status": "pass",
                    "observed_status": "fail",
                    "error_count": "1",
                    "failure_class": "schema_missing",
                    "failure_detail": f"manifest missing columns {','.join(sorted(missing))}",
                    "validation_authority": "GOVERNANCE_HEALTH",
                    "pass_does_not_mean": PASS_DOES_NOT_MEAN,
                }
            ],
            False,
        )

    report: list[dict[str, str]] = []
    all_expected = True
    for row in rows:
        packet_id = row.get("packet_id", "")
        packet_type = row.get("packet_type", "")
        packet_path_raw = row.get("packet_path", "")
        expected = row.get("expected_status", "pass")
        packet_path = resolve_path(packet_path_raw)
        validator, errors, authority = validate_packet(packet_type, packet_path)
        observed = "pass" if not errors else "fail"
        if observed != expected:
            all_expected = False
        if errors:
            for error in errors:
                report.append(
                    {
                        "packet_id": packet_id,
                        "packet_type": packet_type,
                        "packet_path": packet_path_raw,
                        "validator": validator,
                        "expected_status": expected,
                        "observed_status": observed,
                        "error_count": str(len(errors)),
                        "failure_class": classify_failure(error),
                        "failure_detail": error,
                        "validation_authority": authority,
                        "pass_does_not_mean": PASS_DOES_NOT_MEAN,
                    }
                )
        else:
            report.append(
                {
                    "packet_id": packet_id,
                    "packet_type": packet_type,
                    "packet_path": packet_path_raw,
                    "validator": validator,
                    "expected_status": expected,
                    "observed_status": observed,
                    "error_count": "0",
                    "failure_class": "",
                    "failure_detail": "",
                    "validation_authority": authority,
                    "pass_does_not_mean": PASS_DOES_NOT_MEAN,
                }
            )
    return report, all_expected


def write_report(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "packet_id",
        "packet_type",
        "packet_path",
        "validator",
        "expected_status",
        "observed_status",
        "error_count",
        "failure_class",
        "failure_detail",
        "validation_authority",
        "pass_does_not_mean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report, all_expected = build_report_rows(args.manifest)
    write_report(args.output, report)
    observed_failures = sum(1 for row in report if row["observed_status"] == "fail")
    if not all_expected:
        print(f"[TRADER_BRAIN_GRAPH_BATCH_ERROR] unexpected validation status; report={args.output}")
        sys.exit(1)
    print(
        f"[TRADER_BRAIN_GRAPH_BATCH_OK] packets={len({row['packet_id'] for row in report})} "
        f"observed_failures={observed_failures} report={args.output}"
    )


if __name__ == "__main__":
    main()
