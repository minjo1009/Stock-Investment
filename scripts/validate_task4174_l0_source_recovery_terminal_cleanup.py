from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


DEFAULT_DIR = Path("data/artifacts/task_4174_l0_source_recovery_terminal_cleanup")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    failures: list[str] = []
    passes: list[str] = []

    ledger = args.artifact_dir / "task_4174_l0_terminal_status_ledger.csv"
    summary_path = args.artifact_dir / "task_4174_l0_recovery_summary.json"
    if not ledger.exists():
        failures.append(f"missing ledger: {ledger}")
    if not summary_path.exists():
        failures.append(f"missing summary: {summary_path}")
    if failures:
        print("\n".join(f"FAIL {item}" for item in failures))
        return 1

    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not rows:
        failures.append("terminal ledger is empty")
    required_sources = {
        "public_newswire_backfill:businesswire",
        "public_newswire_backfill:globenewswire",
        "public_newswire_backfill:prnewswire",
        "public_context_news_backfill:federal_register_documents:2020-10:page_32",
    }
    seen = {f"{row.get('source_family')}:{row.get('source')}" for row in rows}
    missing = sorted(required_sources - seen)
    if missing:
        failures.append(f"missing required source rows: {missing}")
    blank = [row for row in rows if not row.get("terminal_state")]
    if blank:
        failures.append(f"blank terminal_state rows: {len(blank)}")
    negative = [row for row in rows if str(row.get("negative_evidence_allowed")) not in {"0", "False", "false", ""}]
    if negative:
        failures.append("negative evidence allowed in L0 terminal ledger")
    safety = summary.get("safety", {})
    if any(int(safety.get(key, 0) or 0) for key in ["broker_mutation_count", "live_order_count", "paper_promotion_count", "real_capital_flag_count", "negative_evidence_allowed"]):
        failures.append("safety flags are not closed")
    proof = summary.get("federal_register_retry_proof", {})
    if not proof.get("proof_status"):
        failures.append("missing Federal Register retry proof status")
    if int(summary.get("unclassified_l0_terminal_status_count", -1)) != 0:
        failures.append("unclassified L0 terminal status count is not zero")

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    passes.append(f"terminal_rows={len(rows)}")
    passes.append(f"terminalized_count={summary.get('terminalized_count')}")
    passes.append(f"federal_register_proof={proof.get('proof_status')}")
    for item in passes:
        print(f"PASS {item}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
