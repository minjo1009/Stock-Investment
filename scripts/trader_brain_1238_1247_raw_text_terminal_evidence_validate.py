from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1238_1247_raw_text_terminal_evidence"
RAW = ROOT / "data/raw/task_1238_1247_sec_filing_text_cache"
REPORT = ROOT / "docs/reports/task_1238_1247_raw_text_terminal_evidence"

REQUIRED_FILES = [
    "task1238_expert_packets.csv",
    "task1239_sec_filing_metadata_asof.csv",
    "task1239_selection_filing_bindings.csv",
    "task1240_raw_filing_download_ledger.csv",
    "task1241_l1_terminal_text_evidence.csv",
    "task1242_l2_survival_primitives.csv",
    "task1243_l3_terminal_invalidation_edges.csv",
    "task1244_independent_distress_audit.csv",
    "task1245_route_transition_audit.csv",
    "task1246_expert_critical_audit_upgrade.csv",
    "task1247_closeout.csv",
    "task1247_closeout.json",
    "artifact_manifest.csv",
]

FORBIDDEN_ASSIGNMENT_COLUMNS = {
    "future_return",
    "return_to_2026q1",
    "diagnostic_net_return",
    "net_return",
    "pnl",
    "exit_reason_from_post_entry",
}


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not RAW.exists():
        errors.append("missing raw SEC filing cache directory")
    if not (REPORT / "task_1238_1247_raw_text_terminal_evidence.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1238_1247_decision.csv").exists():
        errors.append("missing decision csv")
    if errors:
        return errors

    expert = rows("task1238_expert_packets.csv")
    metadata = rows("task1239_sec_filing_metadata_asof.csv")
    bindings = rows("task1239_selection_filing_bindings.csv")
    downloads = rows("task1240_raw_filing_download_ledger.csv")
    evidence = rows("task1241_l1_terminal_text_evidence.csv")
    l2 = rows("task1242_l2_survival_primitives.csv")
    l3 = rows("task1243_l3_terminal_invalidation_edges.csv")
    audit = rows("task1244_independent_distress_audit.csv")
    transitions = rows("task1245_route_transition_audit.csv")
    expert_audit = rows("task1246_expert_critical_audit_upgrade.csv")
    closeout = rows("task1247_closeout.csv")
    closeout_json = json.loads((ART / "task1247_closeout.json").read_text(encoding="utf-8"))

    if len(expert) < 4:
        errors.append("expert packets must include at least four review roles")
    if len(metadata) < 310:
        errors.append("metadata must attach at least one candidate filing per selected row on average")
    if len(bindings) < 310:
        errors.append("bindings must cover selected rows")
    if len(downloads) < 20:
        errors.append("download ledger must contain a meaningful SEC document sample")
    if sum(1 for row in downloads if row["download_status"] in {"downloaded", "cached"}) < 20:
        errors.append("at least 20 raw filings must be downloaded or cached")
    if len(evidence) < 10:
        errors.append("L1 evidence extractor found too few raw text evidence rows")
    if len(l2) != 310 or len(l3) != 310 or len(audit) != 310:
        errors.append("L2, L3, and audit rows must cover the 310 slot5 selections")
    if not transitions:
        errors.append("route transition audit must not be empty")
    if len(expert_audit) < 4:
        errors.append("expert critical audit upgrade rows are missing")
    if len(closeout) != 1:
        errors.append("closeout must contain one row")

    for table_name, table in [
        ("metadata", metadata),
        ("bindings", bindings),
        ("evidence", evidence),
        ("l2", l2),
        ("l3", l3),
        ("audit", audit),
    ]:
        if table and FORBIDDEN_ASSIGNMENT_COLUMNS.intersection(table[0].keys()):
            errors.append(f"{table_name} contains forbidden assignment outcome columns")

    for row in metadata:
        if row["source_time_pass"] == "1":
            if parse_ts(row["available_to_brain_ts"]) > parse_ts(row["decision_asof_ts"]):
                errors.append("metadata has future source-time leakage")
                break
    for row in evidence:
        if row["source_time_pass"] != "1":
            errors.append("evidence rows must be as-of prior-known")
            break
        if not row["raw_file_sha256"] or not row["sec_url"] or not row["excerpt"] or not row["excerpt_locator"]:
            errors.append("evidence rows must carry hash URL excerpt and locator")
            break
        if row["outcome_used_for_assignment"] != "0":
            errors.append("evidence rows must not use outcomes for assignment")
            break
        if parse_ts(row["available_to_brain_ts"]) > parse_ts(row["decision_asof_ts"]):
            errors.append("evidence has future source-time leakage")
            break
    if not any(row["terminal_interpretation_route"] in {"terminal_distress", "watch_distress", "evidence_watch"} for row in l2):
        errors.append("L2 must create at least one raw-evidence-aware watch or distress route")
    if not any(row["relation_primitive"] in {"invalidates", "weakens", "conditions"} for row in l3):
        errors.append("L3 must create reviewable terminal relation edges")
    if any(row["selection_promoted"] != "0" for row in audit):
        errors.append("audit rows must not promote selections")
    if any(row["missing_raw_source_is_not_negative"] != "1" for row in audit):
        errors.append("missing raw source must not be treated as negative")

    co = closeout[0] if closeout else {}
    for row in [co, closeout_json]:
        if str(row.get("replay_executed")) != "0":
            errors.append("replay must not be executed in this task")
        if str(row.get("selection_promoted")) != "0":
            errors.append("selection must not be promoted")
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row.get("real_capital") != "FORBIDDEN":
            errors.append("real capital changed")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1238_1247_RAW_TEXT_TERMINAL_EVIDENCE_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1238_1247_RAW_TEXT_TERMINAL_EVIDENCE_OK] artifacts validated")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
