from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from trader_brain_adapter_eligibility_validate import AUDIT_FIELDS, PASS_DOES_NOT_MEAN, validate_bundles, write_csv


ADAPTER_FIELDS = [
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
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_adapter_inputs(bundles_path: Path, graph_manifest_path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    audit_rows, errors = validate_bundles(bundles_path, graph_manifest_path)
    bundle_rows = {row["candidate_bundle_id"]: row for row in read_csv(bundles_path)}
    adapter_rows: list[dict[str, str]] = []
    for audit in audit_rows:
        if audit["eligibility_state"] != "eligible":
            continue
        bundle = bundle_rows[audit["candidate_bundle_id"]]
        adapter_rows.append(
            {
                "adapter_input_id": f"adapter_{audit['candidate_bundle_id']}",
                "candidate_bundle_id": audit["candidate_bundle_id"],
                "source_graph_id": audit["source_graph_id"],
                "bundle_asof_ts": bundle["asof_ts"],
                "mechanism_ids": audit["mechanism_ids"],
                "evidence_refs": audit["evidence_refs"],
                "eligible_reason": audit["eligible_reason"],
                "blocked_reason": "",
                "adapter_input_state": "dry_adapter_input",
                "validation_authority": "GOVERNANCE_HEALTH",
                "pass_does_not_mean": PASS_DOES_NOT_MEAN,
            }
        )
    return adapter_rows, audit_rows, errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundles", required=True, type=Path)
    parser.add_argument("--graph-manifest", required=True, type=Path)
    parser.add_argument("--adapter-output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    args = parser.parse_args()
    adapter_rows, audit_rows, errors = build_adapter_inputs(args.bundles, args.graph_manifest)
    write_csv(args.adapter_output, adapter_rows, ADAPTER_FIELDS)
    write_csv(args.audit_output, audit_rows, AUDIT_FIELDS)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_ADAPTER_BUILDER_ERROR] {error}")
        raise SystemExit(1)
    print(f"[TRADER_BRAIN_ADAPTER_BUILDER_OK] adapter_inputs={len(adapter_rows)} audit_rows={len(audit_rows)}")


if __name__ == "__main__":
    main()
