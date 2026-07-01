from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


DEFAULT_DIR = Path("data/artifacts/task_4175_l1_newswire_recall_mapping_feature_gap_repair")
ALLOWED = {"ACCEPT_MAPPED", "NEEDS_ALIAS", "AMBIGUOUS_BLOCKER", "NON_ISSUER", "INSUFFICIENT_CONTEXT", "FEATURE_BACKFILL_REQUIRED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    failures: list[str] = []
    ledger = args.artifact_dir / "task_4175_l1_mapping_decision_ledger.csv"
    freq = args.artifact_dir / "task_4175_l1_candidate_frequency.csv"
    summary_path = args.artifact_dir / "task_4175_l1_mapping_summary.json"
    for path in [ledger, freq, summary_path]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if failures:
        print("\n".join(f"FAIL {item}" for item in failures))
        return 1
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not rows:
        failures.append("decision ledger is empty")
    bad = [row for row in rows if row.get("decision_state") not in ALLOWED]
    if bad:
        failures.append(f"invalid decision states: {len(bad)}")
    pending = [row for row in rows if "PENDING" in str(row.get("decision_state", ""))]
    if pending:
        failures.append(f"pending decision states remain: {len(pending)}")
    if any(str(row.get("negative_evidence_allowed")) not in {"0", "False", "false", ""} for row in rows):
        failures.append("negative evidence allowed in L1 decision ledger")
    if int(summary.get("pending_after", -1)) != 0:
        failures.append("summary pending_after is not zero")
    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print(f"PASS decision_rows={len(rows)}")
    print(f"PASS reclassified_count={summary.get('reclassified_count')}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
