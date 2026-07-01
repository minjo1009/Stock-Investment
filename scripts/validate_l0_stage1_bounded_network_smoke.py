from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/reports/task_4119_l0_stage_1_bounded_network_smoke_execution"
SUMMARY_PATH = REPORT_DIR / "stage1_network_smoke_summary.json"
REQUIRED_CSVS = [
    "task_4119_scope_freeze.csv",
    "task_4119_source_family_plan.csv",
    "task_4119_api_or_raw_call_ledger.csv",
    "task_4119_raw_response_classification.csv",
    "task_4119_normalized_source_packets.csv",
    "task_4119_decision_asof_coverage.csv",
    "task_4119_feature_admission_gate.csv",
    "task_4119_source_gap_ledger.csv",
]
REQUIRED_FAMILIES = {
    "official_public_releases",
    "gdelt_news_events",
    "marketaux_news_free",
}
REQUIRED_MICROSTRUCTURE_PREFIX = "microstructure_"
SECRET_PATTERN = re.compile(
    r"(api[_-]?key|apikey|token|authorization|secret|APCA-API-KEY-ID|APCA-API-SECRET-KEY)\s*[:=]\s*[A-Za-z0-9_\-]{12,}",
    flags=re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    if not SUMMARY_PATH.exists():
        return [f"missing summary: {SUMMARY_PATH.relative_to(ROOT)}"]
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8-sig"))
    if summary.get("stage1_status") != "NETWORK_SMOKE_EXECUTED_OWNER_REVIEW_PENDING":
        errors.append(f"unexpected stage1 status: {summary.get('stage1_status')}")
    if int(summary.get("network_calls_made", 0)) <= 0:
        errors.append("network smoke must record at least one network call")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    for name in REQUIRED_CSVS:
        path = REPORT_DIR / name
        if not path.exists():
            errors.append(f"missing required csv: {path.relative_to(ROOT)}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required csv: {path.relative_to(ROOT)}")

    ledger_path = REPORT_DIR / "task_4119_api_or_raw_call_ledger.csv"
    if ledger_path.exists():
        rows = read_csv(ledger_path)
        families = {row.get("source_family", "") for row in rows}
        missing = REQUIRED_FAMILIES - families
        if missing:
            errors.append(f"ledger missing families: {sorted(missing)}")
        if not any(row.get("source_family", "").startswith(REQUIRED_MICROSTRUCTURE_PREFIX) for row in rows):
            errors.append("ledger missing microstructure family")
        for row in rows:
            if row.get("broker_mutation_permitted_flag") not in {"0", 0}:
                errors.append(f"broker mutation flag opened: {row}")
            if row.get("real_capital_permitted_flag") not in {"0", 0}:
                errors.append(f"real capital flag opened: {row}")
            raw_path = row.get("raw_path", "")
            raw_sha = row.get("raw_sha256", "")
            if raw_path and raw_sha:
                path = ROOT / raw_path
                if not path.exists():
                    errors.append(f"raw summary path missing: {raw_path}")
                elif sha256_file(path) != raw_sha:
                    errors.append(f"raw summary sha mismatch: {raw_path}")

    packets_path = REPORT_DIR / "task_4119_normalized_source_packets.csv"
    if packets_path.exists():
        packets = read_csv(packets_path)
        for row in packets:
            if row.get("missing_source_is_negative") not in {"0", 0}:
                errors.append(f"missing source used as negative: {row.get('source_packet_id')}")
            if row.get("assignment_uses_future_outcome") not in {"0", 0}:
                errors.append(f"future outcome assignment opened: {row.get('source_packet_id')}")
            if row.get("outcome_used_for_assignment") not in {"0", 0}:
                errors.append(f"outcome assignment opened: {row.get('source_packet_id')}")
            if row.get("strict_gate_pass") not in {"0", 0}:
                errors.append(f"strict gate opened during smoke: {row.get('source_packet_id')}")
            raw_path = row.get("raw_path", "")
            raw_sha = row.get("raw_sha256", "")
            if raw_path and raw_sha:
                path = ROOT / raw_path
                if not path.exists():
                    errors.append(f"packet raw path missing: {raw_path}")
                elif sha256_file(path) != raw_sha:
                    errors.append(f"packet raw sha mismatch: {raw_path}")

    gate_path = REPORT_DIR / "task_4119_feature_admission_gate.csv"
    if gate_path.exists():
        gates = read_csv(gate_path)
        if not gates or gates[0].get("status") != "BLOCKED_UNTIL_OPERATOR_ACCEPTS_SMOKE_RESULTS":
            errors.append("stage1_to_stage2 gate must remain owner-review blocked")
        for row in gates:
            if row.get("strict_gate_opened") not in {"0", 0}:
                errors.append("strict gate opened in feature admission gate")
            if row.get("replay_permission_granted") not in {"0", 0}:
                errors.append("replay permission opened in feature admission gate")

    for path in [SUMMARY_PATH, *[REPORT_DIR / name for name in REQUIRED_CSVS], *REPORT_DIR.glob("raw_summaries/**/*")]:
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            if SECRET_PATTERN.search(text):
                errors.append(f"secret-like value detected in artifact: {path.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE1_BOUNDED_NETWORK_SMOKE_ERROR] {error}")
        return 1
    print("[L0_STAGE1_BOUNDED_NETWORK_SMOKE_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
