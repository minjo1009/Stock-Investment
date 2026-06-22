from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions"
OUT_DIR = ROOT / "data/artifacts/task_1161_1170_sec_bulk_public_filer_universe"
REPORT_DIR = ROOT / "docs/reports/task_1161_1170_sec_bulk_public_filer_universe"

SEC_BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
ZIP_PATH = RAW_DIR / "submissions.zip"
HIST_START = date(2021, 1, 1)
HIST_END = date(2026, 3, 31)
USER_AGENT = "minjo-trader-brain-research contact@example.com"
AUTHORITY = "DIAGNOSTIC_SEC_PUBLIC_FILER_ASOF_UNIVERSE_ONLY"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def head_url(url: str, timeout: int = 45) -> dict[str, object]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    checked_at = now_utc()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return {
                "url": url,
                "head_status": "ok",
                "http_status": getattr(response, "status", 200),
                "content_length": int(response.headers.get("Content-Length", "0") or 0),
                "content_type": response.headers.get("Content-Type", ""),
                "checked_at_utc": checked_at,
                "error": "",
            }
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {
            "url": url,
            "head_status": "failed",
            "http_status": "",
            "content_length": 0,
            "content_type": "",
            "checked_at_utc": checked_at,
            "error": str(exc)[:500],
        }


def download_with_resume(url: str, path: Path, expected_size: int) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.stat().st_size if path.exists() else 0
    if expected_size and existing == expected_size:
        return {
            "download_status": "already_complete",
            "downloaded_at_utc": now_utc(),
            "bytes_downloaded": existing,
            "raw_source_path": rel(path),
            "source_hash": sha256(path),
            "error": "",
        }

    headers = {"User-Agent": USER_AGENT}
    mode = "wb"
    if existing > 0 and expected_size and existing < expected_size:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"

    req = urllib.request.Request(url, headers=headers)
    started = now_utc()
    last_report = existing
    try:
        with urllib.request.urlopen(req, timeout=120) as response, path.open(mode + "") as handle:
            while True:
                chunk = response.read(1024 * 1024 * 8)
                if not chunk:
                    break
                handle.write(chunk)
                current = handle.tell()
                if current - last_report >= 256 * 1024 * 1024:
                    print(f"[SEC_BULK_DOWNLOAD_PROGRESS] bytes={current} expected={expected_size}", flush=True)
                    last_report = current
        final_size = path.stat().st_size
        status = "downloaded" if final_size == expected_size or expected_size == 0 else "partial"
        return {
            "download_status": status,
            "downloaded_at_utc": started,
            "bytes_downloaded": final_size,
            "raw_source_path": rel(path),
            "source_hash": sha256(path) if status == "downloaded" or expected_size == final_size else "",
            "error": "" if status == "downloaded" or expected_size == final_size else "download_size_mismatch",
        }
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {
            "download_status": "failed",
            "downloaded_at_utc": started,
            "bytes_downloaded": path.stat().st_size if path.exists() else 0,
            "raw_source_path": rel(path) if path.exists() else "",
            "source_hash": "",
            "error": str(exc)[:500],
        }


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_acceptance(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    if "+" not in normalized and normalized.endswith("00"):
        normalized = normalized + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def month_ends(start: date, end: date) -> list[date]:
    out: list[date] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        if m == 12:
            next_month = date(y + 1, 1, 1)
        else:
            next_month = date(y, m + 1, 1)
        d = next_month.fromordinal(next_month.toordinal() - 1)
        if d < start:
            d = start
        if d > end:
            d = end
        out.append(d)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


def nested_get(payload: dict[str, object], *keys: str) -> object:
    cur: object = payload
    for key in keys:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(key, {})
    return cur


def process_zip(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    entity_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    zip_hash = sha256(path)
    files_processed = 0
    files_failed = 0
    json_members = 0
    compressed_size = 0
    uncompressed_size = 0
    with zipfile.ZipFile(path) as zf:
        infos = [info for info in zf.infolist() if info.filename.lower().endswith(".json")]
        json_members = len(infos)
        compressed_size = sum(info.compress_size for info in infos)
        uncompressed_size = sum(info.file_size for info in infos)
        for info in infos:
            try:
                payload = json.loads(zf.read(info))
            except (json.JSONDecodeError, OSError, zipfile.BadZipFile):
                files_failed += 1
                continue
            files_processed += 1
            if files_processed % 5000 == 0:
                print(f"[SEC_BULK_PARSE_PROGRESS] files={files_processed}/{json_members}", flush=True)
            if not isinstance(payload, dict):
                continue
            cik_raw = str(payload.get("cik", "") or "").strip()
            cik = cik_raw.zfill(10) if cik_raw else ""
            name = str(payload.get("name", "") or "")
            tickers = [str(t).upper() for t in payload.get("tickers", []) if str(t).strip()] if isinstance(payload.get("tickers"), list) else []
            exchanges = [str(e) for e in payload.get("exchanges", []) if str(e).strip()] if isinstance(payload.get("exchanges"), list) else []
            if not tickers:
                continue

            recent = nested_get(payload, "filings", "recent")
            accession_numbers = recent.get("accessionNumber", []) if isinstance(recent, dict) else []
            filing_dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
            acceptance_times = recent.get("acceptanceDateTime", []) if isinstance(recent, dict) else []
            forms = recent.get("form", []) if isinstance(recent, dict) else []

            all_acceptances: list[datetime] = []
            historical_acceptances: list[datetime] = []
            historical_filings = 0
            for idx, accepted_value in enumerate(acceptance_times):
                accepted = parse_acceptance(str(accepted_value))
                if accepted is None:
                    continue
                all_acceptances.append(accepted)
                filing_date = parse_date(str(filing_dates[idx])) if idx < len(filing_dates) else accepted.date()
                if filing_date is not None and HIST_START <= filing_date <= HIST_END:
                    historical_acceptances.append(accepted)
                    historical_filings += 1

            if not all_acceptances:
                continue

            first_acceptance = min(all_acceptances)
            last_acceptance = max(all_acceptances)
            hist_first = min(historical_acceptances) if historical_acceptances else None
            hist_last = max(historical_acceptances) if historical_acceptances else None
            source_path = f"zip://{rel(path)}!{info.filename}"

            entity_id = f"CIK{cik}"
            entity_rows.append(
                {
                    "task_id": "Task1163",
                    "entity_id": entity_id,
                    "cik": cik,
                    "entity_name": name,
                    "tickers": ";".join(tickers),
                    "exchanges": ";".join(exchanges),
                    "filing_count_in_recent_block": len(accession_numbers),
                    "historical_filing_count_2021_2026q1": historical_filings,
                    "first_acceptance_ts": first_acceptance.isoformat(),
                    "last_acceptance_ts": last_acceptance.isoformat(),
                    "first_historical_acceptance_ts": hist_first.isoformat() if hist_first else "",
                    "last_historical_acceptance_ts": hist_last.isoformat() if hist_last else "",
                    "raw_member_path": source_path,
                    "source_zip_hash": zip_hash,
                    "public_filer_proxy_candidate": "1",
                    "exchange_listed_pit_pass": "0",
                    "authority": AUTHORITY,
                }
            )
            effective_start = first_acceptance.isoformat()
            for ticker in tickers:
                for exchange in exchanges or [""]:
                    event_rows.append(
                        {
                            "task_id": "Task1164",
                            "membership_event_id": f"PUBFILER1164-{len(event_rows)+1:08d}",
                            "cik": cik,
                            "symbol": ticker,
                            "exchange": exchange,
                            "entity_name": name,
                            "effective_start_ts": effective_start,
                            "effective_end_ts": "",
                            "published_ts": effective_start,
                            "received_ts": "",
                            "available_to_brain_ts": effective_start,
                            "raw_member_path": source_path,
                            "source_zip_hash": zip_hash,
                            "public_filer_asof_pass": "1",
                            "exchange_listed_pit_pass": "0",
                            "limitation": "SEC_public_filer_proxy_uses_current_ticker_metadata_not_true_exchange_listing_history",
                            "authority": AUTHORITY,
                        }
                    )

    inventory = {
        "json_members": json_members,
        "files_processed": files_processed,
        "files_failed": files_failed,
        "compressed_json_bytes": compressed_size,
        "uncompressed_json_bytes": uncompressed_size,
    }
    return entity_rows, event_rows, inventory


def build_decision_calendar() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1165",
            "decision_date": d.isoformat(),
            "decision_asof_ts": f"{d.isoformat()}T21:00:00+00:00",
            "window": "2021_2026q1_month_end",
            "authority": AUTHORITY,
        }
        for d in month_ends(HIST_START, HIST_END)
    ]


def build_asof_panel(events: list[dict[str, object]], calendar: list[dict[str, object]]) -> list[dict[str, object]]:
    event_records = []
    for event in events:
        start = parse_acceptance(str(event["effective_start_ts"]))
        if start is None:
            continue
        event_records.append((start, event))
    event_records.sort(key=lambda pair: pair[0])

    rows: list[dict[str, object]] = []
    active: list[dict[str, object]] = []
    cursor = 0
    for cal in calendar:
        decision_ts = parse_acceptance(str(cal["decision_asof_ts"]))
        if decision_ts is None:
            continue
        while cursor < len(event_records) and event_records[cursor][0] <= decision_ts:
            active.append(event_records[cursor][1])
            cursor += 1
        seen: set[tuple[str, str, str]] = set()
        for event in active:
            key = (str(event["symbol"]), str(event["cik"]), str(event["exchange"]))
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "task_id": "Task1166",
                    "asof_membership_id": f"PUBASOF1166-{len(rows)+1:09d}",
                    "decision_asof_ts": cal["decision_asof_ts"],
                    "symbol": event["symbol"],
                    "cik": event["cik"],
                    "exchange": event["exchange"],
                    "entity_name": event["entity_name"],
                    "effective_start_ts": event["effective_start_ts"],
                    "available_to_brain_ts": event["available_to_brain_ts"],
                    "public_filer_asof_pass": "1",
                    "exchange_listed_pit_pass": "0",
                    "selection_candidate_source": "sec_public_filer_proxy",
                    "replay_use_allowed": "0",
                    "block_reason": "proxy_ready_but_not_true_exchange_listed_universe_and_no_policy_preregistration",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_coverage_panel(asof_rows: list[dict[str, object]], calendar: list[dict[str, object]]) -> list[dict[str, object]]:
    by_date: dict[str, set[str]] = {str(row["decision_asof_ts"]): set() for row in calendar}
    exchange_counts: dict[tuple[str, str], int] = {}
    for row in asof_rows:
        ts = str(row["decision_asof_ts"])
        by_date.setdefault(ts, set()).add(str(row["symbol"]))
        key = (ts, str(row["exchange"]))
        exchange_counts[key] = exchange_counts.get(key, 0) + 1
    rows = []
    for idx, cal in enumerate(calendar, start=1):
        ts = str(cal["decision_asof_ts"])
        rows.append(
            {
                "task_id": "Task1167",
                "coverage_id": f"COVERAGE1167-{idx:03d}",
                "decision_asof_ts": ts,
                "unique_symbol_count": len(by_date.get(ts, set())),
                "asof_membership_rows": sum(v for (date_key, _exchange), v in exchange_counts.items() if date_key == ts),
                "nasdaq_rows": exchange_counts.get((ts, "Nasdaq"), 0),
                "nyse_rows": exchange_counts.get((ts, "NYSE"), 0),
                "other_rows": sum(
                    v
                    for (date_key, exchange), v in exchange_counts.items()
                    if date_key == ts and exchange not in {"Nasdaq", "NYSE"}
                ),
                "authority": AUTHORITY,
            }
        )
    return rows


def build_vendor_gap_panel() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1168",
            "gap_id": "VENDOR-GAP-1168-001",
            "needed_dataset": "historical_exchange_listing_membership",
            "why_needed": "to prove listed universe membership by symbol and date rather than public-filer proxy",
            "free_official_status": "not_acquired",
            "candidate_sources": "NYSE historical market data;Nasdaq historical reference data;CRSP/Compustat;Norgate;Polygon reference data",
            "blocks_true_exchange_listed_replay": "1",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1168",
            "gap_id": "VENDOR-GAP-1168-002",
            "needed_dataset": "historical_ticker_change_and_delisting_events",
            "why_needed": "to avoid current ticker survivorship and renamed-symbol leakage",
            "free_official_status": "not_acquired",
            "candidate_sources": "exchange corporate action feeds;CRSP;Nasdaq reference data;OpenFIGI with dated mappings if available",
            "blocks_true_exchange_listed_replay": "1",
            "authority": AUTHORITY,
        },
    ]


def build_readiness(
    download_row: dict[str, object],
    inventory: dict[str, object],
    entity_rows: list[dict[str, object]],
    event_rows: list[dict[str, object]],
    asof_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    min_symbols = min(int(row["unique_symbol_count"]) for row in coverage_rows) if coverage_rows else 0
    max_symbols = max(int(row["unique_symbol_count"]) for row in coverage_rows) if coverage_rows else 0
    proxy_ready = (
        download_row["download_status"] in {"downloaded", "already_complete"}
        and int(inventory["files_processed"]) > 1000
        and len(entity_rows) > 1000
        and len(asof_rows) > 10000
    )
    return [
        {
            "task_id": "Task1169",
            "readiness_id": "SEC-PUBLIC-FILER-ASOF-1169-001",
            "sec_bulk_download_status": download_row["download_status"],
            "zip_json_members": inventory["json_members"],
            "files_processed": inventory["files_processed"],
            "public_filer_entities": len(entity_rows),
            "membership_event_rows": len(event_rows),
            "asof_membership_rows": len(asof_rows),
            "min_symbols_per_decision": min_symbols,
            "max_symbols_per_decision": max_symbols,
            "public_filer_proxy_universe_ready": "1" if proxy_ready else "0",
            "true_exchange_listed_universe_ready": "0",
            "policy_preregistration_allowed": "0",
            "replay_executed": "0",
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
    ]


def closeout(readiness: list[dict[str, object]], source_row: dict[str, object]) -> dict[str, object]:
    row = readiness[0]
    return {
        "task_id": "Task1161-1170",
        "verdict": "sec_public_filer_asof_proxy_acquired_true_exchange_listing_still_missing",
        "sec_bulk_download_status": row["sec_bulk_download_status"],
        "sec_bulk_zip_bytes": source_row["bytes_downloaded"],
        "zip_json_members": row["zip_json_members"],
        "files_processed": row["files_processed"],
        "public_filer_entities": row["public_filer_entities"],
        "membership_event_rows": row["membership_event_rows"],
        "asof_membership_rows": row["asof_membership_rows"],
        "min_symbols_per_decision": row["min_symbols_per_decision"],
        "max_symbols_per_decision": row["max_symbols_per_decision"],
        "public_filer_proxy_universe_ready": row["public_filer_proxy_universe_ready"],
        "true_exchange_listed_universe_ready": "0",
        "policy_preregistration_allowed": "0",
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "build_policy_pre_registration_for_public_filer_proxy_or_acquire_true_exchange_listing_vendor_feed",
        "authority": AUTHORITY,
    }


def write_report(decision: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1161_1170_sec_bulk_public_filer_universe.md"
    lines = [
        "# Task1161-1170 SEC Bulk Public-Filer Universe",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision['verdict']}`.",
        f"- SEC bulk download status: `{decision['sec_bulk_download_status']}`.",
        f"- SEC bulk zip bytes: {decision['sec_bulk_zip_bytes']}.",
        f"- Zip JSON members: {decision['zip_json_members']}.",
        f"- Files processed: {decision['files_processed']}.",
        f"- Public-filer entities: {decision['public_filer_entities']}.",
        f"- Membership event rows: {decision['membership_event_rows']}.",
        f"- Asof membership rows: {decision['asof_membership_rows']}.",
        f"- Symbols per decision range: {decision['min_symbols_per_decision']} to {decision['max_symbols_per_decision']}.",
        f"- Public-filer proxy universe ready: `{decision['public_filer_proxy_universe_ready']}`.",
        f"- True exchange-listed universe ready: `{decision['true_exchange_listed_universe_ready']}`.",
        "- Replay executed: 0.",
        "- Selection promoted: 0.",
        "",
        "## Quant Expert Report",
        "",
        "This task downloads the official SEC bulk submissions ZIP and builds a broad public-filer as-of proxy universe.",
        "",
        "Important distinction:",
        "",
        "- This is stronger than the old custom 10x7 universe.",
        "- It is still not the same as a true exchange-listed PIT universe.",
        "- It uses SEC filing acceptance time plus current ticker metadata from submissions JSON.",
        "- It does not fully solve historical ticker changes, delistings, or exchange listing date history.",
        "",
        "Leakage decision:",
        "",
        "- Current ticker metadata is not treated as true historical listing proof.",
        "- Public-filer proxy rows are prepared for future policy pre-registration.",
        "- No backtest or selection promotion was executed in this task.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We acquired the big official SEC dataset.",
        "",
        "That gives us a much wider universe than the handpicked 70 names.",
        "",
        "Now the model can be prepared to choose from a broad public-company universe, not from a winner basket.",
        "",
        "But this is still a proxy. To claim true exchange-listed PIT, we still need historical exchange listing and ticker-change data.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1161_sec_bulk_download_ledger.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1162_sec_bulk_zip_inventory.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1163_public_filer_entity_panel.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1164_public_filer_membership_events.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1165_decision_calendar.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1166_public_filer_asof_universe_panel.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1167_public_filer_universe_coverage.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1168_vendor_exchange_listing_gap.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1169_public_filer_proxy_readiness.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1170_sec_bulk_public_filer_closeout.csv`",
        "- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1170_sec_bulk_public_filer_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1161_1170_decision.csv", [decision])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    head = head_url(SEC_BULK_URL)
    download_row = download_with_resume(SEC_BULK_URL, ZIP_PATH, int(head["content_length"]))
    source_row = {
        "task_id": "Task1161",
        "source_id": "sec_bulk_submissions_zip",
        "source_url": SEC_BULK_URL,
        "head_status": head["head_status"],
        "http_status": head["http_status"],
        "content_length": head["content_length"],
        "content_type": head["content_type"],
        "checked_at_utc": head["checked_at_utc"],
        **download_row,
        "official_source": "1",
        "authority": AUTHORITY,
    }
    if download_row["download_status"] not in {"downloaded", "already_complete"}:
        inventory = {
            "json_members": 0,
            "files_processed": 0,
            "files_failed": 0,
            "compressed_json_bytes": 0,
            "uncompressed_json_bytes": 0,
        }
        entity_rows: list[dict[str, object]] = []
        event_rows: list[dict[str, object]] = []
    else:
        entity_rows, event_rows, inventory = process_zip(ZIP_PATH)

    calendar_rows = build_decision_calendar()
    asof_rows = build_asof_panel(event_rows, calendar_rows)
    coverage_rows = build_coverage_panel(asof_rows, calendar_rows)
    vendor_gap_rows = build_vendor_gap_panel()
    readiness_rows = build_readiness(source_row, inventory, entity_rows, event_rows, asof_rows, coverage_rows)
    decision = closeout(readiness_rows, source_row)

    inventory_row = {
        "task_id": "Task1162",
        "zip_path": rel(ZIP_PATH) if ZIP_PATH.exists() else "",
        "zip_hash": sha256(ZIP_PATH) if ZIP_PATH.exists() else "",
        **inventory,
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1161_sec_bulk_download_ledger.csv", [source_row])
    write_csv(OUT_DIR / "task1162_sec_bulk_zip_inventory.csv", [inventory_row])
    write_csv(OUT_DIR / "task1163_public_filer_entity_panel.csv", entity_rows)
    write_csv(OUT_DIR / "task1164_public_filer_membership_events.csv", event_rows)
    write_csv(OUT_DIR / "task1165_decision_calendar.csv", calendar_rows)
    write_csv(OUT_DIR / "task1166_public_filer_asof_universe_panel.csv", asof_rows)
    write_csv(OUT_DIR / "task1167_public_filer_universe_coverage.csv", coverage_rows)
    write_csv(OUT_DIR / "task1168_vendor_exchange_listing_gap.csv", vendor_gap_rows)
    write_csv(OUT_DIR / "task1169_public_filer_proxy_readiness.csv", readiness_rows)
    write_csv(OUT_DIR / "task1170_sec_bulk_public_filer_closeout.csv", [decision])
    write_json(OUT_DIR / "task1170_sec_bulk_public_filer_closeout.json", decision)
    write_report(decision)

    print(
        "[TRADER_BRAIN_1161_1170_SEC_BULK_PUBLIC_FILER_UNIVERSE_OK] "
        f"download={decision['sec_bulk_download_status']} "
        f"json_members={decision['zip_json_members']} "
        f"entities={decision['public_filer_entities']} "
        f"asof_rows={decision['asof_membership_rows']} "
        f"proxy_ready={decision['public_filer_proxy_universe_ready']} "
        "replay=0"
    )


if __name__ == "__main__":
    main()
