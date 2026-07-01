from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4135"
SLUG = "task_4135_l1_final_hardening_l2_gpt_consult"
DATA_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
L1_DATA_DIR = ROOT / "data" / "artifacts" / "task_4133_l1_development_plan"
GPT_CAPTURE_STATUSES = {
    "CAPTURED",
    "BLOCKED_AUTOMATION_NO_GPT_CAPTURE",
    "BLOCKED_CHROME_EXTENSION_COMMUNICATION",
    "PENDING_USER_CHROME_PERMISSION",
    "PENDING_CAPTURE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob(pattern) if item.is_file())


def sqlite_scalar(query: str, default: Any = "") -> Any:
    db_path = ROOT / "trading.db"
    if not db_path.exists():
        return default
    try:
        con = sqlite3.connect(str(db_path), timeout=2)
        try:
            return con.execute(query).fetchone()[0]
        finally:
            con.close()
    except Exception:
        return default


def build_handoff_contract(packets: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    scope_by_class = {
        "STRICT_SOURCE_TIME_CERTIFIED": "L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY",
        "CONTEXT_ONLY_CERTIFIED": "L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE",
        "DISCOVERY_ONLY": "L2_REVIEW_QUEUE_ONLY_NOT_FEATURE",
    }
    for packet in packets:
        classification = packet.get("l1_gate_classification", "")
        allowed = scope_by_class.get(classification, "BLOCKED")
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": packet.get("endpoint_or_source_family", ""),
                "l1_classification": classification,
                "l2_allowed_action": allowed,
                "required_l1_gate": "source_time,raw_integrity,mapping,authority",
                "trading_authority": "0",
                "l2_write_allowed_by_task": "0",
                "paper_or_live_permission": "0",
                "notes": "handoff contract only; TASK-4135 does not write L2",
            }
        )
    return rows


def build_coverage_rows(packets: list[dict[str, str]]) -> list[dict[str, Any]]:
    daily_dir = ROOT / "data" / "raw" / "us_daily_alpaca_full_universe"
    rows = [
        {
            "task_id": TASK_ID,
            "source_family": "daily_bars",
            "data_present_evidence": "data/raw/us_daily_alpaca_full_universe",
            "raw_file_count": count_files(daily_dir, "*.csv"),
            "db_or_row_count": "",
            "l1_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "daily_bars"),
            "strict_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "daily_bars" and p.get("strict_gate_pass") == "1"),
            "known_gap_count": 0,
            "coverage_status": "DATA_PRESENT_L1_GATE_READY",
        },
        {
            "task_id": TASK_ID,
            "source_family": "market_bars_5m",
            "data_present_evidence": "trading.db#market_bars_5m",
            "raw_file_count": "",
            "db_or_row_count": sqlite_scalar("select count(*) from market_bars_5m", ""),
            "l1_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "market_bars_5m"),
            "strict_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "market_bars_5m" and p.get("strict_gate_pass") == "1"),
            "known_gap_count": 0,
            "coverage_status": "DATA_PRESENT_L1_GATE_READY",
        },
        {
            "task_id": TASK_ID,
            "source_family": "public_context_news_feeds",
            "data_present_evidence": "data/raw/l0_public_context_news_backfill",
            "raw_file_count": count_files(ROOT / "data" / "raw" / "l0_public_context_news_backfill", "headlines.json"),
            "db_or_row_count": "",
            "l1_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "public_context_news_feeds"),
            "strict_packet_count": 0,
            "known_gap_count": 0,
            "coverage_status": "CONTEXT_ONLY_L1_GATE_READY",
        },
        {
            "task_id": TASK_ID,
            "source_family": "public_market_macro_news_feeds",
            "data_present_evidence": "data/raw/l0_public_market_macro_news_backfill",
            "raw_file_count": count_files(ROOT / "data" / "raw" / "l0_public_market_macro_news_backfill", "headlines.json"),
            "db_or_row_count": "",
            "l1_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "public_market_macro_news_feeds"),
            "strict_packet_count": 0,
            "known_gap_count": 0,
            "coverage_status": "CONTEXT_ONLY_L1_GATE_READY",
        },
        {
            "task_id": TASK_ID,
            "source_family": "public_newswire_feeds",
            "data_present_evidence": "data/raw/l0_public_newswire_backfill",
            "raw_file_count": count_files(ROOT / "data" / "raw" / "l0_public_newswire_backfill", "headlines.json"),
            "db_or_row_count": "",
            "l1_packet_count": sum(1 for p in packets if p.get("endpoint_or_source_family") == "public_newswire_feeds"),
            "strict_packet_count": 0,
            "known_gap_count": 0,
            "coverage_status": "DISCOVERY_ONLY_L1_GATE_READY",
        },
    ]
    return rows


def build_gpt_context(summary: dict[str, Any], handoff_rows: list[dict[str, str]], coverage_rows: list[dict[str, Any]]) -> str:
    handoff_lines = "\n".join(
        f"- {row['source_family']}: {row['l1_classification']} -> {row['l2_allowed_action']}"
        for row in handoff_rows
    )
    coverage_lines = "\n".join(
        f"- {row['source_family']}: evidence={row['data_present_evidence']}, files/rows={row['raw_file_count'] or row['db_or_row_count']}, status={row['coverage_status']}"
        for row in coverage_rows
    )
    return f"""# TASK-4135 GPT Local Context Packet

## Important Instruction For GPT

Do not read GitHub for this consult. The local worktree contains recent L0/L1 work that has not been committed or pushed. Treat this packet as the source of current project state for L0/L1. If you need more context, ask Codex to provide local file excerpts rather than using GitHub.

## User Goal

We rebuilt and hardened L0/L1 source acquisition locally. The user now wants to move toward L2, but first wants GPT's expert opinion using detailed local L0/L1 context.

## Hard State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence
- GPT is advisory only; repo files and validators remain source of truth

## Current L0 Summary

- L0 background collection lanes include daily bars, 5-minute bars, public context news, public newswire, and public market/macro news.
- Daily raw CSVs exist at `data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv`.
- 5-minute bars exist in `trading.db#market_bars_5m`.
- Public context/news/macro raw files exist under `data/raw/l0_public_*`.
- Backfills may still be incomplete, but missing rows are blockers, not negative labels.

## Current L1 Summary

- L1 is an evidence checkpoint, not a trading layer.
- Normalized packet required columns include task_id, source_packet_id, candidate_id, symbol, decision_asof_ts, provider, endpoint_or_source_family, source_ts, available_to_brain_ts, source_time_basis, source_time_certified, raw_path, raw_sha256, strict_gate_pass, proxy_feature_allowed, missing_source_is_negative, assignment_uses_future_outcome, outcome_used_for_assignment, authority.
- Gates are source_time, raw_integrity, mapping, authority.
- Classifications are STRICT_SOURCE_TIME_CERTIFIED, CONTEXT_ONLY_CERTIFIED, DISCOVERY_ONLY, and BLOCKED_* classes.
- TASK-4134 fixed a false daily-bars gap: daily bars now produce strict L1 packets from the real raw CSV path.
- Legacy direct L0-to-L2 news ingest is blocked by default.

## Handoff Contract

{handoff_lines}

## Coverage Snapshot

{coverage_lines}

## TASK-4135 Local Summary

```json
{json.dumps(summary, indent=2, sort_keys=True)}
```

## Existing L2 Situation

- Visible `src/l2/builders/news_event_primitives.py` exists but imports modules that may be missing in visible source (`src.l2.contracts`, `freshness`, `lineage`, `runtime_context`, `news_runtime`).
- `src/l2/builders/microstructure_primitives.py` is effectively empty.
- Therefore L2 should begin with a small intake contract and validator, not broad production materialization.

## Question For GPT

Given this local L0/L1 state, recommend the safest, highest-leverage L2 development sequence. Please answer:

1. What should L2 be responsible for, and what must remain in L1?
2. What is the first minimal L2 artifact/schema/contract to implement?
3. Which source families should be consumed first: daily bars, 5-minute bars, macro/context, public newswire discovery, or something else?
4. What validators should block L2 if L1 gates are missing or stale?
5. How should we handle the existing broken/legacy L2 news builder/import surfaces?
6. What should explicitly not be built yet?
7. Provide a small Codex-executable TASK-4136 plan.
"""


def current_gpt_capture_status() -> tuple[str, str]:
    response_path = REPORT_DIR / "l2_gpt_response.md"
    if response_path.exists():
        text = response_path.read_text(encoding="utf-8", errors="ignore")
        if "CAPTURED" in text or "GPT Recommendation" in text:
            return "CAPTURED", "skipped_preexisting_user_tab"
        if "BLOCKED_CHROME_EXTENSION_COMMUNICATION" in text:
            return "BLOCKED_CHROME_EXTENSION_COMMUNICATION", "FAILED_BEFORE_TAB_CONTROL"
        if "Chrome is installed" in text and "permission" in text.lower():
            return "PENDING_USER_CHROME_PERMISSION", "PENDING"
    ledger_path = DATA_DIR / "gpt_consult_ledger.csv"
    if ledger_path.exists():
        try:
            rows = read_csv(ledger_path)
        except Exception:
            rows = []
        if rows:
            status = rows[0].get("capture_status") or "PENDING_CAPTURE"
            cleanup = rows[0].get("tab_cleanup_status") or "PENDING"
            if status in GPT_CAPTURE_STATUSES:
                return status, cleanup
    return "PENDING_CAPTURE", "PENDING"


def artifact_rows() -> list[dict[str, str]]:
    rows = [
        ("scripts/run_l1_final_hardening_l2_consult_prep.py", "script", "Builds TASK-4135 L1 final hardening and GPT context artifacts.", "created"),
        ("scripts/validate_l1_final_hardening_l2_consult_prep.py", "validator", "Validates TASK-4135 L1 handoff and GPT context artifacts.", "created"),
        ("ops/task_registry.yaml", "registry", "Registers TASK-4135.", "modified"),
        ("ops/doc_registry.yaml", "registry", "Registers TASK-4135 documents.", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "docs", "Adds TASK-4135 to active L0/L1 SSOT index.", "modified"),
        ("docs/active/CURRENT_TASKS.md", "docs", "Adds TASK-4135 to completed task ledger.", "modified"),
        ("docs/active/PROJECT_STATUS.md", "docs", "Records TASK-4135 L1/L2 consult state.", "modified"),
        ("docs/architecture/l0_source_acquisition_project_management_plan.md", "docs", "Adds TASK-4135 handoff/consult note.", "modified"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4135 closeout report.", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4135 changed/output file manifest.", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4135 validation results.", "created"),
        (f"docs/reports/{SLUG}/l2_gpt_local_context_packet.md", "reference", "Local L0/L1 context packet for GPT; GitHub explicitly forbidden.", "created"),
        (f"docs/reports/{SLUG}/l2_gpt_prompt.md", "reference", "Prompt sent or prepared for GPT consult.", "created"),
        (f"docs/reports/{SLUG}/l2_gpt_response.md", "reference", "Captured GPT response or automation blocker note.", "created"),
        (f"docs/reports/{SLUG}/l1_final_hardening_l2_consult_summary.json", "reference", "Machine-readable TASK-4135 summary.", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_handoff_contract.csv", "data_artifact", "Frozen L1-to-L2 handoff contract rows.", "created"),
        (f"data/artifacts/{SLUG}/l1_coverage_audit.csv", "data_artifact", "Data-present L1 coverage audit.", "created"),
        (f"data/artifacts/{SLUG}/l1_remaining_risk_register.csv", "data_artifact", "Remaining L1 risks after practical hardening.", "created"),
        (f"data/artifacts/{SLUG}/gpt_consult_ledger.csv", "data_artifact", "GPT consult mode/capture ledger.", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "data_artifact", "Machine-readable TASK-4135 validator report.", "created"),
    ]
    return [
        {"path": path, "type": typ, "purpose": purpose, "created_or_modified": status, "task_id": TASK_ID}
        for path, typ, purpose, status in rows
    ]


def main() -> int:
    from tools.db.source_acquisition.l1_bootstrap import build_and_write

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l1_summary = build_and_write()
    packets = read_csv(L1_DATA_DIR / "l1_normalized_source_packets_sample.csv")
    handoff_rows = build_handoff_contract(packets)
    coverage_rows = build_coverage_rows(packets)
    remaining_risks = [
        {
            "task_id": TASK_ID,
            "priority": "P0",
            "risk": "Full L1 materialization is still sample/contract level, not full production table.",
            "recommended_handling": "Move to L2 with handoff contract first; materialize full L1 only for L2-consumed families.",
            "status": "DEFER_TO_L2_CONSUMPTION_SCOPE",
        },
        {
            "task_id": TASK_ID,
            "priority": "P1",
            "risk": "Public newswire remains discovery-only and must not become a feature without authority/mapping audit.",
            "recommended_handling": "Keep in review queue only.",
            "status": "CONTROLLED_BY_HANDOFF_CONTRACT",
        },
        {
            "task_id": TASK_ID,
            "priority": "P1",
            "risk": "Some raw public news files may use bounded fingerprints when OneDrive placeholders are not fully materialized.",
            "recommended_handling": "Require full hash only for L2-consumed rows; keep non-consumed rows diagnostic.",
            "status": "CONTROLLED_BY_L2_VALIDATOR_REQUIREMENT",
        },
    ]
    write_csv(DATA_DIR / "l1_l2_handoff_contract.csv", handoff_rows, ["task_id", "source_family", "l1_classification", "l2_allowed_action", "required_l1_gate", "trading_authority", "l2_write_allowed_by_task", "paper_or_live_permission", "notes"])
    write_csv(DATA_DIR / "l1_coverage_audit.csv", coverage_rows, ["task_id", "source_family", "data_present_evidence", "raw_file_count", "db_or_row_count", "l1_packet_count", "strict_packet_count", "known_gap_count", "coverage_status"])
    write_csv(DATA_DIR / "l1_remaining_risk_register.csv", remaining_risks, ["task_id", "priority", "risk", "recommended_handling", "status"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "l1_packet_count": l1_summary["packet_count"],
        "strict_gate_pass_count": l1_summary["strict_gate_pass_count"],
        "gap_count": l1_summary["gap_count"],
        "handoff_contract_rows": len(handoff_rows),
        "coverage_rows": len(coverage_rows),
        "trading_authority_opened": False,
        "l2_materialization_written": False,
        "gpt_github_forbidden": True,
    }
    context = build_gpt_context(summary, handoff_rows, coverage_rows)
    prompt = f"""Use Pro-level reasoning. Do not use GitHub. Do not inspect minjo1009/Stock-Investment on GitHub because the relevant L0/L1 work is local and not committed. Use only the local context packet below.

{context}
"""
    (REPORT_DIR / "l2_gpt_local_context_packet.md").write_text(context, encoding="utf-8", newline="\n")
    (REPORT_DIR / "l2_gpt_prompt.md").write_text(prompt, encoding="utf-8", newline="\n")
    response_path = REPORT_DIR / "l2_gpt_response.md"
    if not response_path.exists():
        response_path.write_text("# GPT Response\n\nPending Chrome GPT capture.\n", encoding="utf-8", newline="\n")
    capture_status, tab_cleanup_status = current_gpt_capture_status()
    write_csv(
        DATA_DIR / "gpt_consult_ledger.csv",
        [
            {
                "task_id": TASK_ID,
                "relay_mode": "single_gpt_consult",
                "gpt_mode": "Pro reasoning, GitHub forbidden, local context packet only",
                "prompt_artifact": f"docs/reports/{SLUG}/l2_gpt_prompt.md",
                "response_artifact": f"docs/reports/{SLUG}/l2_gpt_response.md",
                "capture_status": capture_status,
                "tab_cleanup_status": tab_cleanup_status,
            }
        ],
        ["task_id", "relay_mode", "gpt_mode", "prompt_artifact", "response_artifact", "capture_status", "tab_cleanup_status"],
    )
    (REPORT_DIR / "l1_final_hardening_l2_consult_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    if capture_status == "BLOCKED_CHROME_EXTENSION_COMMUNICATION":
        gpt_note = """
Chrome was launched with user permission. The Codex Chrome Extension, selected
Chrome profile, and native host checks passed, but browser-client tab control
calls repeatedly timed out after the recovery window was opened. The GPT consult
packet is ready, but the GPT response is not captured. Closeout remains pending
until Chrome extension communication is restored or the prompt is manually run
and the response is captured into the response artifact.
"""
    else:
        gpt_note = ""
    report = f"""# TASK-4135 L1 Final Hardening And L2 GPT Consult

## Result

TASK-4135 freezes the practical L1-to-L2 handoff contract and prepares a local L0/L1 context packet for GPT. GitHub is explicitly forbidden for the consult because the newest L0/L1 work is local and not committed.

## L1 Handoff

- l1_packet_count: {summary['l1_packet_count']}
- strict_gate_pass_count: {summary['strict_gate_pass_count']}
- gap_count: {summary['gap_count']}
- handoff_contract_rows: {summary['handoff_contract_rows']}
- trading_authority_opened: false
- l2_materialization_written: false

## GPT Consult

- mode: single_gpt_consult
- GitHub: forbidden
- prompt: `docs/reports/{SLUG}/l2_gpt_prompt.md`
- response: `docs/reports/{SLUG}/l2_gpt_response.md`
- capture_status: {capture_status}
{gpt_note}
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    write_csv(REPORT_DIR / "artifact_manifest.csv", artifact_rows(), ["path", "type", "purpose", "created_or_modified", "task_id"])
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
