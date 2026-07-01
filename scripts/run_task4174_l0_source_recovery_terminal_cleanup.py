from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


TASK_ID = "TASK-4174"
OUT_DIR = Path("data/artifacts/task_4174_l0_source_recovery_terminal_cleanup")
RAW_DIR = Path("data/raw/task_4174_l0_source_recovery_terminal_cleanup")
NEWSWIRE_AGG = Path("data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json")
CONTEXT_PROGRESS = Path("data/artifacts/l0_public_context_news_backfill/collector_progress.json")
MARKET_PROGRESS = Path("data/artifacts/l0_public_market_macro_news_backfill/collector_progress.json")


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def federal_register_url(page: int) -> str:
    params = {
        "format": "json",
        "per_page": "100",
        "page": str(page),
        "conditions[publication_date][gte]": "2020-10-01",
        "conditions[publication_date][lte]": "2020-10-31",
        "order": "oldest",
    }
    return f"https://www.federalregister.gov/api/v1/documents.json?{urlencode(params)}"


def fetch_federal_register_page32() -> dict[str, Any]:
    url = federal_register_url(32)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    started = now_z()
    raw_path = RAW_DIR / "federal_register_2020_10_page_32.json"
    meta_path = RAW_DIR / "federal_register_2020_10_page_32_metadata.json"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Codex-L0-Recovery/1.0 contact=operator"})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
            status_code = int(getattr(response, "status", 0) or 0)
            headers = dict(response.headers.items())
        raw_path.write_bytes(payload)
        parsed = json.loads(payload.decode("utf-8"))
        results = parsed.get("results", []) if isinstance(parsed, dict) else []
        proof_status = "FETCHED_ROWS_PRESENT" if results else "FETCHED_VALID_EMPTY_PAGE"
        metadata = {
            "task_id": TASK_ID,
            "started_at": started,
            "finished_at": now_z(),
            "url": url,
            "http_status": status_code,
            "raw_path": str(raw_path),
            "raw_sha256": sha256_bytes(payload),
            "byte_count": len(payload),
            "result_count": len(results),
            "total_pages": parsed.get("total_pages") if isinstance(parsed, dict) else None,
            "count": parsed.get("count") if isinstance(parsed, dict) else None,
            "proof_status": proof_status,
            "headers_redacted": {key: value for key, value in headers.items() if key.lower() not in {"set-cookie"}},
            "negative_evidence_allowed": 0,
        }
    except Exception as exc:
        metadata = {
            "task_id": TASK_ID,
            "started_at": started,
            "finished_at": now_z(),
            "url": url,
            "http_status": "",
            "raw_path": "",
            "raw_sha256": "",
            "byte_count": 0,
            "result_count": 0,
            "total_pages": None,
            "count": None,
            "proof_status": "FETCH_FAILED_RETRYABLE_BLOCKER",
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            "negative_evidence_allowed": 0,
        }
    write_json(meta_path, metadata)
    return metadata


def terminal_state_for_pending(status: str, pending: int, failed: int = 0, partial: int = 0) -> str:
    if failed:
        return "FAILED_RETRYABLE_REPRESENTED_BLOCKER"
    if pending == 0 and partial == 0:
        return "COMPLETED"
    if status == "RUNNING":
        return "RUNNING_RETRYABLE_INCOMPLETE"
    return "EXPLICIT_TERMINAL_BLOCKER_OR_RETRYABLE_INCOMPLETE"


def build_ledger(fr_proof: dict[str, Any]) -> list[dict[str, Any]]:
    newswire = load_json(NEWSWIRE_AGG)
    context = load_json(CONTEXT_PROGRESS)
    market = load_json(MARKET_PROGRESS)
    rows: list[dict[str, Any]] = []

    for source, payload in sorted((newswire.get("by_source") or {}).items()):
        pending = int(payload.get("pending_units", 0) or 0)
        failed = int(payload.get("failed_units", 0) or 0)
        partial = int(payload.get("partial_units", 0) or 0)
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": "public_newswire_backfill",
                "source": source,
                "status": newswire.get("status", ""),
                "completed_units": payload.get("completed_units", 0),
                "pending_units": pending,
                "failed_units": failed,
                "partial_units": partial,
                "terminal_state": terminal_state_for_pending(str(newswire.get("status", "")), pending, failed, partial),
                "required_next_action": "CONTINUE_EXISTING_RUNNER" if pending else "NONE",
                "proof_path": str(NEWSWIRE_AGG),
                "negative_evidence_allowed": 0,
            }
        )

    fr = ((context.get("backfill") or {}).get("federal_register_documents") or {})
    fr_pending = int(fr.get("pending_units", 0) or 0)
    rows.append(
        {
            "task_id": TASK_ID,
            "source_family": "public_context_news_backfill",
            "source": "federal_register_documents:2020-10:page_32",
            "status": fr_proof.get("proof_status", ""),
            "completed_units": len(fr.get("completed_units", []) or []),
            "pending_units": fr_pending,
            "failed_units": 0 if fr_proof.get("proof_status") != "FETCH_FAILED_RETRYABLE_BLOCKER" else 1,
            "partial_units": 1 if fr_pending else 0,
            "terminal_state": "BOUNDED_RETRY_PROOF_CAPTURED" if fr_proof.get("proof_status") != "FETCH_FAILED_RETRYABLE_BLOCKER" else "TERMINAL_RETRYABLE_BLOCKER",
            "required_next_action": "COLLECTOR_STATE_REPLAY_OR_MARK_COMPLETED_BY_PAGINATION_PROOF",
            "proof_path": str(RAW_DIR / "federal_register_2020_10_page_32_metadata.json"),
            "negative_evidence_allowed": 0,
        }
    )

    for source, cycle in sorted((market.get("source_cycles") or {}).items()):
        backfill = ((market.get("backfill") or {}).get(source) or {})
        pending = int(backfill.get("pending_units", 0) or 0)
        last_status = str(cycle.get("last_status", ""))
        if last_status == "BACKFILL_COMPLETE" and pending == 0:
            terminal = "COMPLETED"
            action = "NONE"
        elif last_status == "FAILED_RETRYABLE":
            terminal = "FAILED_RETRYABLE_TERMINAL_BLOCKER"
            action = "BOUNDED_RETRY_WITH_EXISTING_RUNNER"
        else:
            terminal = "RUNNING_OR_EXPORTED_INCOMPLETE"
            action = "CONTINUE_EXISTING_RUNNER"
        rows.append(
            {
                "task_id": TASK_ID,
                "source_family": "public_market_macro_news_backfill",
                "source": source,
                "status": last_status,
                "completed_units": len(backfill.get("completed_units", []) or []),
                "pending_units": pending,
                "failed_units": 1 if last_status == "FAILED_RETRYABLE" else 0,
                "partial_units": 1 if (backfill.get("page_offsets") or backfill.get("entry_offsets")) else 0,
                "terminal_state": terminal,
                "required_next_action": action,
                "proof_path": str(MARKET_PROGRESS),
                "negative_evidence_allowed": 0,
            }
        )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fr_proof = fetch_federal_register_page32()
    rows = build_ledger(fr_proof)
    fields = [
        "task_id",
        "source_family",
        "source",
        "status",
        "completed_units",
        "pending_units",
        "failed_units",
        "partial_units",
        "terminal_state",
        "required_next_action",
        "proof_path",
        "negative_evidence_allowed",
    ]
    ledger_path = OUT_DIR / "task_4174_l0_terminal_status_ledger.csv"
    write_csv(ledger_path, rows, fields)
    summary = {
        "task_id": TASK_ID,
        "generated_at": now_z(),
        "ledger_path": str(ledger_path),
        "source_rows": len(rows),
        "unclassified_l0_terminal_status_count": sum(1 for row in rows if not row.get("terminal_state")),
        "terminalized_count": sum(1 for row in rows if row.get("terminal_state") and row.get("terminal_state") != "COMPLETED"),
        "status_counts": {state: sum(1 for row in rows if row.get("terminal_state") == state) for state in sorted({str(row.get("terminal_state", "")) for row in rows})},
        "federal_register_retry_proof": fr_proof,
        "safety": {
            "broker_mutation_count": 0,
            "live_order_count": 0,
            "paper_promotion_count": 0,
            "real_capital_flag_count": 0,
            "negative_evidence_allowed": 0,
        },
    }
    write_json(OUT_DIR / "task_4174_l0_recovery_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
