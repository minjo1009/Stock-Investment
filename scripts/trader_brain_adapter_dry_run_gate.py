from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from trader_brain_adapter_input_builder import build_adapter_inputs
from trader_brain_adapter_eligibility_validate import write_csv


FOOTER = """Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN"""


SUMMARY_FIELDS = [
    "gate_status",
    "bundle_count",
    "eligible_count",
    "blocked_count",
    "invalid_count",
    "adapter_input_count",
    "strategy_acceptance",
    "deployment_status",
    "real_capital",
    "validation_authority",
    "footer",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundles", required=True, type=Path)
    parser.add_argument("--graph-manifest", required=True, type=Path)
    parser.add_argument("--adapter-output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()
    adapter_rows, audit_rows, errors = build_adapter_inputs(args.bundles, args.graph_manifest)
    write_csv(
        args.adapter_output,
        adapter_rows,
        [
            "adapter_input_id",
            "candidate_bundle_id",
            "source_graph_id",
            "bundle_asof_ts",
            "mechanism_ids",
            "evidence_refs",
            "eligible_reason",
            "blocked_reason",
            "adapter_input_state",
            "validation_authority",
            "pass_does_not_mean",
        ],
    )
    write_csv(
        args.audit_output,
        audit_rows,
        [
            "candidate_bundle_id",
            "source_graph_id",
            "eligibility_state",
            "eligible_reason",
            "blocked_reason",
            "mechanism_ids",
            "evidence_refs",
            "validation_authority",
            "pass_does_not_mean",
        ],
    )
    invalid_count = sum(1 for row in audit_rows if row["eligibility_state"] == "invalid") + len(errors)
    eligible_count = sum(1 for row in audit_rows if row["eligibility_state"] == "eligible")
    blocked_count = sum(1 for row in audit_rows if row["eligibility_state"] == "blocked")
    gate_status = "diagnostic_only_pass" if invalid_count == 0 and eligible_count == len(adapter_rows) else "diagnostic_only_fail"
    write_csv(
        args.summary_output,
        [
            {
                "gate_status": gate_status,
                "bundle_count": str(len(audit_rows)),
                "eligible_count": str(eligible_count),
                "blocked_count": str(blocked_count),
                "invalid_count": str(invalid_count),
                "adapter_input_count": str(len(adapter_rows)),
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "validation_authority": "GOVERNANCE_HEALTH",
                "footer": FOOTER,
            }
        ],
        SUMMARY_FIELDS,
    )
    if gate_status != "diagnostic_only_pass":
        for error in errors:
            print(f"[TRADER_BRAIN_ADAPTER_DRY_RUN_GATE_ERROR] {error}")
        print(f"[TRADER_BRAIN_ADAPTER_DRY_RUN_GATE_FAIL] summary={args.summary_output}")
        raise SystemExit(1)
    print(f"[TRADER_BRAIN_ADAPTER_DRY_RUN_GATE_OK] eligible={eligible_count} blocked={blocked_count} summary={args.summary_output}")


if __name__ == "__main__":
    main()
