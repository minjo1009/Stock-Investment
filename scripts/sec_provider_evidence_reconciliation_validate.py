"""Validate Task3848 read-only SEC provider evidence reconciliation artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


TASK_ID = "task_3848_sec_provider_evidence_reconciliation"
ARTIFACT_DIR = Path("data/artifacts") / TASK_ID
REPORT_DIR = Path("docs/reports") / TASK_ID

REQUIRED_FILES = [
    ARTIFACT_DIR / "sec_provider_reconciliation.csv",
    ARTIFACT_DIR / "sec_provider_blocker_matrix.csv",
    ARTIFACT_DIR / "sec_provider_evidence_reconciliation_state.json",
    REPORT_DIR / "sec_provider_evidence_reconciliation_report.md",
    REPORT_DIR / "artifact_manifest.csv",
]

FORBIDDEN_TOKENS = ["insert into", "update ", "delete from", "requests.get", "urllib.request", "submit_order", "broker.submit"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing file: {path}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    recon_rows = read_csv(ARTIFACT_DIR / "sec_provider_reconciliation.csv")
    blocker_rows = read_csv(ARTIFACT_DIR / "sec_provider_blocker_matrix.csv")
    providers = {row.get("provider") for row in recon_rows}
    for provider in {"sec_live_delta", "sec_rss_delta", "sec_bulk_baseline", "sec_submissions_cache"}:
        if provider not in providers:
            failures.append(f"missing provider: {provider}")
    if any(row.get("authority_claim_allowed") != "false" for row in recon_rows):
        failures.append("authority claim must be false for every provider")
    if any(row.get("network_call_performed") != "false" for row in recon_rows):
        failures.append("network call performed must be false for every provider")
    if any(row.get("strict_gate_claimed") != "0" for row in recon_rows):
        failures.append("strict gate must not be claimed")
    if not any(row.get("blocker_active") == "true" for row in blocker_rows):
        failures.append("blocker matrix must retain active blockers")

    state = json.loads((ARTIFACT_DIR / "sec_provider_evidence_reconciliation_state.json").read_text(encoding="utf-8"))
    for key, expected in {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "overall_status": "READ_ONLY_SEC_PROVIDER_RECONCILIATION_COMPLETE_WITH_BLOCKERS",
    }.items():
        if state.get(key) != expected:
            failures.append(f"unexpected state {key}: {state.get(key)}")
    for key in ["source_acquisition_run", "scheduler_run", "db_mutation", "broker_mutation_added", "paper_live_permission_granted", "real_capital_permission_granted"]:
        if state.get(key) is not False:
            failures.append(f"{key} must be false")
    if state.get("authority_claim_rows") != 0:
        failures.append("authority claim rows must be zero")
    if state.get("network_call_rows") != 0:
        failures.append("network call rows must be zero")

    report = (REPORT_DIR / "sec_provider_evidence_reconciliation_report.md").read_text(encoding="utf-8")
    for phrase in ["UNKNOWN/BLOCKER", "No SEC live retry", "not source authority certification", "NOT_ACCEPTED", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "FORBIDDEN"]:
        if phrase not in report:
            failures.append(f"report missing phrase: {phrase}")

    script_text = Path("scripts/sec_provider_evidence_reconciliation.py").read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_TOKENS:
        if token in script_text:
            failures.append(f"script contains forbidden token: {token}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("SEC provider evidence reconciliation validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
