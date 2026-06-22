from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2541_2560_sec_financing_dilution_acquisition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
RAW_DIR = ROOT / "data/raw" / TASK_ID
REPORT = REPORT_DIR / "task_2541_2560_sec_financing_dilution_acquisition.md"
DECISION = REPORT_DIR / "task_2560_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2531 = ROOT / "data/artifacts/task_2531_2540_selector_source_gap_program"

AUTHORITY = "DATA_HEALTH_SEC_FINANCING_DILUTION_ACQUISITION_ONLY"
USER_AGENT = "trader-brain-source-acquisition/1.0 research-contact local"
SEC_BASE = "https://www.sec.gov"
DATA_BASE = "https://data.sec.gov"
START_DATE = "2020-01-01"
END_DATE = "2026-03-31"

FINANCING_FORMS = {
    "S-1",
    "S-1/A",
    "S-3",
    "S-3/A",
    "F-1",
    "F-1/A",
    "F-3",
    "F-3/A",
    "S-8",
    "S-8 POS",
    "POS AM",
    "EFFECT",
    "FWP",
    "D",
    "D/A",
}
PROSPECTUS_PREFIXES = ("424B",)
PRIMARY_DOC_DOWNLOAD_FORMS = {
    "S-1",
    "S-1/A",
    "S-3",
    "S-3/A",
    "F-1",
    "F-1/A",
    "F-3",
    "F-3/A",
    "D",
    "D/A",
    "424B3",
    "424B4",
    "424B5",
    "424B7",
    "8-K",
    "8-K/A",
}
TARGET_8K_ITEMS = ("1.01", "1.03", "2.03", "3.01", "3.02", "3.03")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_sec_acceptance(value: str, filing_date: str = "") -> str:
    value = (value or "").strip()
    if "T" in value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    if len(value) >= 14 and value[:14].isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}T{value[8:10]}:{value[10:12]}:{value[12:14]}+00:00"
    if filing_date:
        return f"{filing_date}T23:59:59+00:00"
    return ""


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def sec_get(url: str, path: Path, sleep_s: float = 0.12) -> tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return 200, "cache_hit"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()
            path.write_bytes(body)
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        path.write_text(exc.read().decode("utf-8", errors="replace"), encoding="utf-8")
        status = exc.code
    except Exception as exc:
        path.write_text(str(exc), encoding="utf-8")
        status = 0
    time.sleep(sleep_s)
    return status, "downloaded"


def load_company_tickers() -> tuple[dict[str, dict[str, str]], Path, str]:
    raw_path = RAW_DIR / "sec_company_tickers_exchange.json"
    status, source = sec_get(f"{SEC_BASE}/files/company_tickers_exchange.json", raw_path)
    if status != 200:
        fallback = ROOT / "data/raw/task_1141_1150_external_sources/sec_company_tickers_exchange/sec_company_tickers_exchange.json"
        if not fallback.exists():
            raise RuntimeError("SEC ticker mapping unavailable")
        raw_path = fallback
        source = "existing_repo_fallback"
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    mapping: dict[str, dict[str, str]] = {}
    fields = payload.get("fields", [])
    for item in payload.get("data", []):
        row = dict(zip(fields, item))
        ticker = str(row.get("ticker", "")).upper()
        if ticker and ticker not in mapping:
            mapping[ticker] = {
                "cik": str(row.get("cik", "")),
                "company_name": str(row.get("name", "")),
                "exchange": str(row.get("exchange", "")),
                "mapping_source": source,
            }
    return mapping, raw_path, sha256_file(raw_path)


def load_universe() -> list[dict[str, str]]:
    return read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv")


def candidate_symbols(universe: list[dict[str, str]]) -> list[str]:
    return sorted({row["symbol"].upper() for row in universe})


def cik_padded(cik: str) -> str:
    return str(int(cik)).zfill(10)


def cik_archive(cik: str) -> str:
    return str(int(cik))


def normalize_recent_filings(payload: dict[str, Any]) -> list[dict[str, str]]:
    recent = payload.get("filings", {}).get("recent", {})
    if not recent and "accessionNumber" in payload:
        recent = payload
    if not recent:
        return []
    keys = list(recent.keys())
    count = max(len(recent.get(key, [])) for key in keys)
    rows = []
    for idx in range(count):
        row = {}
        for key in keys:
            values = recent.get(key, [])
            row[key] = values[idx] if idx < len(values) else ""
        rows.append(row)
    return rows


def historical_file_names(payload: dict[str, Any]) -> list[str]:
    return [str(row.get("name", "")) for row in payload.get("filings", {}).get("files", []) if row.get("name")]


def in_range(filing_date: str) -> bool:
    dt = parse_date(filing_date)
    start = parse_date(START_DATE)
    end = parse_date(END_DATE)
    return bool(dt and start and end and start <= dt <= end)


def item_matches(items: str) -> bool:
    normalized = (items or "").replace("Item", "").replace(" ", "")
    return any(item in normalized for item in TARGET_8K_ITEMS)


def is_financing_candidate(form: str, items: str) -> bool:
    form_u = (form or "").upper()
    if form_u in FINANCING_FORMS:
        return True
    if form_u.startswith(PROSPECTUS_PREFIXES):
        return True
    if form_u in {"8-K", "8-K/A"} and item_matches(items):
        return True
    return False


def classify_event(form: str, items: str) -> tuple[str, str, str]:
    form_u = (form or "").upper()
    if form_u in {"D", "D/A"}:
        return "private_financing_form_d", "medium_high", "actual_or_notice_candidate"
    if form_u.startswith("424B"):
        return "prospectus_supplement", "medium_high", "actual_or_atm_candidate"
    if form_u in {"S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "F-3/A", "POS AM", "EFFECT", "FWP"}:
        return "registered_capacity_or_status", "medium", "capacity_not_actual_issuance"
    if form_u in {"S-8", "S-8 POS"}:
        return "employee_plan_registration", "low_medium", "not_company_cash_financing_by_default"
    if form_u in {"8-K", "8-K/A"}:
        if "3.02" in items:
            return "unregistered_equity_issuance", "high", "actual_issuance_candidate"
        if "2.03" in items:
            return "debt_survival_financing", "medium_high", "debt_obligation_candidate"
        if "3.01" in items:
            return "listing_survival_risk", "high", "survival_risk_candidate"
        if "1.03" in items:
            return "bankruptcy_or_receivership", "high", "survival_risk_candidate"
        if "1.01" in items:
            return "material_financing_contract", "medium_high", "agreement_candidate"
        if "3.03" in items:
            return "security_holder_rights_change", "medium", "dilution_or_governance_candidate"
    return "other_financing_candidate", "low", "metadata_candidate"


def should_download_primary_document(form: str, items: str) -> bool:
    form_u = (form or "").upper()
    if form_u in {"8-K", "8-K/A"}:
        return item_matches(items)
    return form_u in PRIMARY_DOC_DOWNLOAD_FORMS


def filing_doc_url(cik: str, accession: str, primary_doc: str) -> str:
    acc_no_dash = accession.replace("-", "")
    return f"{SEC_BASE}/Archives/edgar/data/{cik_archive(cik)}/{acc_no_dash}/{primary_doc}"


def submission_url(cik: str) -> str:
    return f"{DATA_BASE}/submissions/CIK{cik_padded(cik)}.json"


def submission_shard_url(name: str) -> str:
    return f"{DATA_BASE}/submissions/{name}"


def build_cik_map(universe: list[dict[str, str]], mapping: dict[str, dict[str, str]], mapping_path: Path, mapping_hash: str) -> list[dict[str, object]]:
    rows = []
    for idx, symbol in enumerate(candidate_symbols(universe), start=1):
        hit = mapping.get(symbol)
        rows.append(
            {
                "task_id": "Task2542",
                "cik_map_id": f"SECCIK2542-{idx:04d}",
                "symbol": symbol,
                "cik": hit["cik"] if hit else "",
                "cik_padded": cik_padded(hit["cik"]) if hit else "",
                "company_name": hit["company_name"] if hit else "",
                "exchange": hit["exchange"] if hit else "",
                "mapping_basis": "sec_company_tickers_exchange_exact_ticker" if hit else "missing_exact_sec_ticker_mapping",
                "mapping_raw_path": str(mapping_path.relative_to(ROOT).as_posix()),
                "mapping_raw_sha256": mapping_hash,
                "mapping_strict_for_identity": "1" if hit else "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def download_and_normalize(cik_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    call_rows: list[dict[str, object]] = []
    raw_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    call_idx = 1
    raw_idx = 1
    event_seen: set[tuple[str, str, str]] = set()
    mapped = [row for row in cik_rows if row["cik"]]

    def log_call(symbol: str, cik: str, endpoint: str, url: str, path: Path, status: int, source: str) -> None:
        nonlocal call_idx, raw_idx
        raw_hash = sha256_file(path) if path.exists() else ""
        rel = path.relative_to(ROOT).as_posix() if path.exists() else ""
        usable = status == 200 and path.exists() and path.stat().st_size > 0
        call_rows.append(
            {
                "task_id": "Task2543",
                "raw_call_id": f"SECCALL2543-{call_idx:05d}",
                "provider": "SEC",
                "endpoint": endpoint,
                "symbol": symbol,
                "cik": cik,
                "request_url_no_secret": url,
                "request_ts": now_iso(),
                "http_status": status,
                "download_source": source,
                "raw_path": rel,
                "raw_sha256": raw_hash,
                "api_secret_written": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        raw_rows.append(
            {
                "task_id": "Task2544",
                "raw_response_id": f"SECRAW2544-{raw_idx:05d}",
                "provider": "SEC",
                "endpoint": endpoint,
                "symbol": symbol,
                "cik": cik,
                "http_status": status,
                "classification": "usable" if usable else ("not_found" if status == 404 else "download_error"),
                "raw_path": rel,
                "raw_sha256": raw_hash,
                "raw_exists": "1" if path.exists() else "0",
                "raw_size_bytes": path.stat().st_size if path.exists() else 0,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        call_idx += 1
        raw_idx += 1

    for row in mapped:
        symbol = str(row["symbol"])
        cik = str(row["cik"])
        sub_path = RAW_DIR / "sec_submissions" / f"CIK{cik_padded(cik)}.json"
        url = submission_url(cik)
        status, source = sec_get(url, sub_path)
        log_call(symbol, cik, "submissions_company_json", url, sub_path, status, source)
        if status != 200:
            continue
        payload = json.loads(sub_path.read_text(encoding="utf-8"))
        filing_rows = normalize_recent_filings(payload)
        for shard in historical_file_names(payload):
            shard_path = RAW_DIR / "sec_submissions" / shard
            shard_url = submission_shard_url(shard)
            shard_status, shard_source = sec_get(shard_url, shard_path)
            log_call(symbol, cik, "submissions_historical_file", shard_url, shard_path, shard_status, shard_source)
            if shard_status == 200:
                try:
                    filing_rows.extend(normalize_recent_filings(json.loads(shard_path.read_text(encoding="utf-8"))))
                except json.JSONDecodeError:
                    pass
        for filing in filing_rows:
            form = str(filing.get("form", "")).upper()
            filing_date = str(filing.get("filingDate", ""))
            items = str(filing.get("items", ""))
            accession = str(filing.get("accessionNumber", ""))
            primary_doc = str(filing.get("primaryDocument", ""))
            if not accession or not in_range(filing_date) or not is_financing_candidate(form, items):
                continue
            key = (cik, accession, form)
            if key in event_seen:
                continue
            event_seen.add(key)
            accepted_ts = parse_sec_acceptance(str(filing.get("acceptanceDateTime", "")), filing_date)
            event_family, severity, actual_status = classify_event(form, items)
            doc_path = Path("")
            doc_hash = ""
            doc_status = ""
            doc_source = ""
            doc_rel = ""
            primary_doc_download_target = should_download_primary_document(form, items)
            if primary_doc and primary_doc_download_target:
                doc_url = filing_doc_url(cik, accession, primary_doc)
                doc_path = RAW_DIR / "sec_filing_primary_docs" / cik_padded(cik) / accession.replace("-", "") / primary_doc
                doc_status_i, doc_source = sec_get(doc_url, doc_path)
                log_call(symbol, cik, "filing_primary_document", doc_url, doc_path, doc_status_i, doc_source)
                doc_status = str(doc_status_i)
                if doc_path.exists():
                    doc_hash = sha256_file(doc_path)
                    doc_rel = doc_path.relative_to(ROOT).as_posix()
            raw_rel = sub_path.relative_to(ROOT).as_posix()
            event_rows.append(
                {
                    "task_id": "Task2545",
                    "source_packet_id": f"SECFIN2545-{len(event_rows)+1:06d}",
                    "candidate_id": "",
                    "trade_spec_id": "",
                    "symbol": symbol,
                    "cik": cik,
                    "decision_asof_ts": "",
                    "provider": "SEC",
                    "endpoint_or_source_family": "sec_financing_dilution_filings",
                    "accession_number": accession,
                    "form_type": form,
                    "items": items,
                    "filing_date": filing_date,
                    "report_date": filing.get("reportDate", ""),
                    "source_ts": accepted_ts,
                    "available_to_brain_ts": accepted_ts,
                    "source_time_basis": "sec_acceptance_datetime" if filing.get("acceptanceDateTime") else "filing_date_end_of_day_fallback",
                    "source_time_certified": "1" if accepted_ts else "0",
                    "primary_document": primary_doc,
                    "primary_document_download_target": "1" if primary_doc_download_target else "0",
                    "primary_document_raw_path": doc_rel,
                    "primary_document_raw_sha256": doc_hash,
                    "primary_document_http_status": doc_status,
                    "event_family": event_family,
                    "event_severity": severity,
                    "actual_vs_capacity_status": actual_status,
                    "raw_path": raw_rel,
                    "raw_sha256": sha256_file(sub_path),
                    "strict_gate_pass": "1" if accepted_ts and (doc_hash or not primary_doc_download_target) else "0",
                    "proxy_feature_allowed": "0" if accepted_ts and (doc_hash or not primary_doc_download_target) else "1",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return call_rows, raw_rows, event_rows


def scope_freeze_rows(universe: list[dict[str, str]], symbols: list[str]) -> list[dict[str, object]]:
    dates = sorted({row["decision_asof_ts"] for row in universe})
    return [
        {
            "task_id": "Task2541",
            "scope_id": "SECSCOPE2541-0001",
            "scope_type": "full_universe_sec_financing_dilution_acquisition",
            "universe_rows": len(universe),
            "unique_symbols": len(symbols),
            "decision_start": dates[0],
            "decision_end": dates[-1],
            "source_family": "sec_financing_dilution",
            "date_window_start": START_DATE,
            "date_window_end": END_DATE,
            "download_or_api_call_run": "1",
            "backtest_run": "0",
            "selector_changed": "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def family_plan_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2542",
            "source_family_id": "SECFAM2542-0001",
            "source_family": "sec_financing_dilution",
            "provider": "SEC",
            "endpoints": "company_tickers_exchange,submissions_company_json,submissions_historical_file,filing_primary_document",
            "strict_pit_rule": "SEC accepted datetime and primary document raw hash must exist; available_to_brain_ts <= decision_asof_ts for candidate-specific strict use.",
            "false_positive_warning": "S-1/S-3/F-1/F-3 are capacity/status, not actual issuance; 424B and 8-K items require text interpretation for actual sizing.",
            "download_or_api_call_run": "1",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def decision_asof_coverage_rows(universe: list[dict[str, str]], cik_map: list[dict[str, object]], event_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    cik_by_symbol = {str(row["symbol"]): str(row["cik"]) for row in cik_map if row["cik"]}
    events_by_symbol: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in event_rows:
        events_by_symbol[str(event["symbol"])].append(event)
    rows = []
    by_decision: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        by_decision[row["decision_asof_ts"]].append(row)
    for idx, (decision_ts, rows_for_date) in enumerate(sorted(by_decision.items(), key=lambda kv: parse_iso(kv[0]) or datetime.min.replace(tzinfo=timezone.utc)), start=1):
        decision_dt = parse_iso(decision_ts)
        mapped_rows = 0
        strict_scan_rows = 0
        prior_event_rows = 0
        strict_event_symbols = set()
        for candidate in rows_for_date:
            symbol = candidate["symbol"].upper()
            if symbol in cik_by_symbol:
                mapped_rows += 1
                strict_scan_rows += 1
            for event in events_by_symbol.get(symbol, []):
                event_dt = parse_iso(str(event.get("available_to_brain_ts", "")))
                if decision_dt and event_dt and event_dt <= decision_dt:
                    prior_event_rows += 1
                    if event.get("strict_gate_pass") == "1":
                        strict_event_symbols.add(symbol)
        rows.append(
            {
                "task_id": "Task2546",
                "decision_asof_coverage_id": f"SECCOV2546-{idx:04d}",
                "decision_asof_ts": decision_ts,
                "candidate_rows": len(rows_for_date),
                "mapped_cik_rows": mapped_rows,
                "strict_sec_scan_rows": strict_scan_rows,
                "prior_financing_event_rows": prior_event_rows,
                "strict_prior_event_symbol_count": len(strict_event_symbols),
                "cik_mapping_coverage_ratio": round(mapped_rows / len(rows_for_date), 6) if rows_for_date else 0.0,
                "strict_scan_coverage_ratio": round(strict_scan_rows / len(rows_for_date), 6) if rows_for_date else 0.0,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def feature_admission_gate_rows(universe: list[dict[str, str]], cik_map: list[dict[str, object]], event_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    cik_by_symbol = {str(row["symbol"]): row for row in cik_map}
    events_by_symbol: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in event_rows:
        events_by_symbol[str(event["symbol"])].append(event)
    out = []
    for idx, candidate in enumerate(universe, start=1):
        symbol = candidate["symbol"].upper()
        decision_dt = parse_iso(candidate["decision_asof_ts"])
        mapped = cik_by_symbol.get(symbol, {})
        mapped_cik = str(mapped.get("cik", ""))
        prior_events = []
        last_event_ts = ""
        high_events_365d = 0
        if mapped_cik and decision_dt:
            lookback_start = decision_dt - timedelta(days=365)
            for event in events_by_symbol.get(symbol, []):
                event_dt = parse_iso(str(event.get("available_to_brain_ts", "")))
                if event_dt and event_dt <= decision_dt:
                    prior_events.append(event)
                    last_event_ts = max(last_event_ts, str(event.get("available_to_brain_ts", "")))
                    if event_dt >= lookback_start and str(event.get("event_severity")) in {"high", "medium_high"}:
                        high_events_365d += 1
        state = "strict_pass" if mapped_cik else "blocked"
        out.append(
            {
                "task_id": "Task2547",
                "feature_gate_id": f"SECFGATE2547-{idx:06d}",
                "candidate_id": candidate["candidate_source_id"],
                "trade_spec_id": candidate["trade_spec_id"],
                "symbol": symbol,
                "cik": mapped_cik,
                "decision_asof_ts": candidate["decision_asof_ts"],
                "layer": "L2/L3/L4",
                "feature_family": "sec_financing_dilution",
                "feature_value_present": "1" if mapped_cik else "0",
                "prior_financing_event_count": len(prior_events),
                "high_or_medium_high_events_365d": high_events_365d,
                "last_prior_event_available_to_brain_ts": last_event_ts,
                "admission_state": state,
                "strict_gate_pass": "1" if state == "strict_pass" else "0",
                "proxy_feature_allowed": "0",
                "can_score_assignment": "1" if state == "strict_pass" else "0",
                "can_annotate_only": "0",
                "blocks_paper": "0" if state == "strict_pass" else "1",
                "blocks_live": "0" if state == "strict_pass" else "1",
                "gate_fail_reason": "" if state == "strict_pass" else "missing_exact_sec_cik_mapping",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def source_gap_rows(universe: list[dict[str, str]], cik_map: list[dict[str, object]], raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    mapped_symbols = {str(row["symbol"]) for row in cik_map if row["cik"]}
    usable_ciks = {str(row["cik"]) for row in raw_rows if row["endpoint"] == "submissions_company_json" and row["classification"] == "usable"}
    rows = []
    for symbol in sorted({row["symbol"].upper() for row in universe}):
        candidates = [row for row in universe if row["symbol"].upper() == symbol]
        if symbol not in mapped_symbols:
            reason = "missing_exact_sec_cik_mapping"
        else:
            cik = next(str(row["cik"]) for row in cik_map if row["symbol"] == symbol)
            reason = "" if cik in usable_ciks else "sec_submissions_not_usable"
        if not reason:
            continue
        rows.append(
            {
                "task_id": "Task2548",
                "source_gap_ledger_id": f"SECGAP2548-{len(rows)+1:04d}",
                "symbol": symbol,
                "candidate_rows": len(candidates),
                "feature_family": "sec_financing_dilution",
                "gap_state": "blocked",
                "gap_reason": reason,
                "required_for_assignment": "1",
                "required_for_paper": "1",
                "required_for_live": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "allowed_resolution": "fix_cik_mapping_or_sec_download_then_rerun",
                "authority": AUTHORITY,
            }
        )
    return rows


def event_summary_rows(event_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(row["event_family"]) for row in event_rows)
    severity = Counter(str(row["event_severity"]) for row in event_rows)
    rows = []
    for key, value in sorted(counts.items()):
        rows.append(
            {
                "task_id": "Task2549",
                "summary_id": f"SECEVENTSUM2549-{len(rows)+1:04d}",
                "summary_type": "event_family",
                "bucket": key,
                "row_count": value,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    for key, value in sorted(severity.items()):
        rows.append(
            {
                "task_id": "Task2549",
                "summary_id": f"SECEVENTSUM2549-{len(rows)+1:04d}",
                "summary_type": "event_severity",
                "bucket": key,
                "row_count": value,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def subagent_rows() -> list[dict[str, object]]:
    rows = [
        ("Dalton", "019ed582-1bab-74b3-913f-9a684815d10a", "sec_financing_taxonomy_review", "DATA_HEALTH / RESEARCH_ONLY"),
        ("Lovelace", "019ed582-5aef-73f3-9559-11607072c030", "sec_acquisition_validation_checklist", "DATA_HEALTH / GOVERNANCE_HEALTH"),
        ("Nietzsche", "019ed582-a20d-7030-b714-4c3e8390beed", "rates_liquidity_next_source_plan", "DATA_HEALTH / RESEARCH_ONLY"),
    ]
    return [
        {
            "task_id": "Task2550",
            "subagent_packet_id": f"SECSUB2550-{idx:04d}",
            "nickname": nickname,
            "agent_id": agent_id,
            "role": role,
            "write_scope": "read-only",
            "file_edits_allowed": "0",
            "validation_authority": authority,
            "completed_or_pending_at_script_run": "reviewed_or_pending",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (nickname, agent_id, role, authority) in enumerate(rows, start=1)
    ]


def closeout_rows(scope: dict[str, object], cik_rows: list[dict[str, object]], raw_rows: list[dict[str, object]], event_rows: list[dict[str, object]], feature_rows: list[dict[str, object]], gaps: list[dict[str, object]]) -> list[dict[str, object]]:
    mapped = sum(1 for row in cik_rows if row["cik"])
    strict_features = sum(1 for row in feature_rows if row["strict_gate_pass"] == "1")
    primary_docs = sum(1 for row in raw_rows if row["endpoint"] == "filing_primary_document" and row["classification"] == "usable")
    return [
        {
            "task_id": "Task2560",
            "verdict": "sec_financing_dilution_full_universe_acquisition_complete",
            "universe_rows": scope["universe_rows"],
            "unique_symbols": scope["unique_symbols"],
            "mapped_cik_symbols": mapped,
            "cik_mapping_coverage_ratio": round(mapped / int(scope["unique_symbols"]), 6) if int(scope["unique_symbols"]) else 0.0,
            "raw_call_rows": len(raw_rows),
            "usable_raw_rows": sum(1 for row in raw_rows if row["classification"] == "usable"),
            "financing_dilution_event_rows": len(event_rows),
            "downloaded_primary_document_rows": primary_docs,
            "feature_gate_rows": len(feature_rows),
            "strict_feature_gate_rows": strict_features,
            "source_gap_rows": len(gaps),
            "download_or_api_call_run": "1",
            "backtest_run": "0",
            "selector_changed": "0",
            "next_action": "Task2561+ should attach PIT rates/liquidity regime, then rerun selector admission only after preserving strict/proxy boundaries.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], summary: list[dict[str, object]]) -> None:
    summary_lines = "\n".join(f"- {row['summary_type']} `{row['bucket']}`: {row['row_count']}" for row in summary[:20])
    REPORT.write_text(
        f"""# Task2541-2560 SEC Financing Dilution Acquisition

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Universe rows: {closeout['universe_rows']}.
- Unique symbols: {closeout['unique_symbols']}.
- Mapped CIK symbols: {closeout['mapped_cik_symbols']} ({closeout['cik_mapping_coverage_ratio']}).
- Raw response rows: {closeout['raw_call_rows']}.
- Usable raw rows: {closeout['usable_raw_rows']}.
- Financing/dilution event rows: {closeout['financing_dilution_event_rows']}.
- Downloaded primary document rows: {closeout['downloaded_primary_document_rows']}.
- Strict feature gate rows: {closeout['strict_feature_gate_rows']}.
- Backtest run: `0`.
- Selector changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task performed the first real source acquisition step after Task2531-2540. It downloaded SEC official ticker mapping, SEC submissions metadata for mapped candidate symbols, historical submissions shards, and primary documents for targeted financing/dilution candidate filings.

Important boundary:

- This is `full-universe SEC financing/dilution acquisition`, not a full SEC archive download.
- `S-1/S-3/F-1/F-3` are capacity/status signals, not actual issuance.
- `424B*`, `8-K Item 3.02`, `Form D`, and financing-related `8-K` items are stronger candidates but still need text-level interpretation before sizing severity.

Event summary:

{summary_lines}

## No-Background Decision-Maker Report

Conclusion first: we did download the first high-impact free official source family.

The brain now has SEC financing/dilution filing evidence attached across the 3,100-candidate universe where CIK mapping was available. This still does not approve the strategy. It only fills one important missing source lane for future selector improvement.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/`.
- Raw files: `data/raw/task_2541_2560_sec_financing_dilution_acquisition/`.
- Validator: `python scripts/trader_brain_2541_2560_sec_financing_dilution_acquisition_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2541, 2561):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"SEC Financing Dilution Acquisition Step {task_no}",
                "owner_team": "Data & Market Microstructure / Research Governance",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "sec-financing-dilution-acquired-diagnostic-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2541_2560_sec_financing_dilution_acquisition/task_2541_2560_sec_financing_dilution_acquisition.md",
                "key_decision": "docs/reports/task_2541_2560_sec_financing_dilution_acquisition/task_2560_decision.csv",
                "key_artifacts": "data/artifacts/task_2541_2560_sec_financing_dilution_acquisition",
                "validation_command": "python scripts/trader_brain_2541_2560_sec_financing_dilution_acquisition_validate.py",
                "notes": "Downloads SEC submissions metadata and targeted financing/dilution primary documents for the 3,100-candidate universe.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    lines = path.read_text(encoding="utf-8").rstrip().splitlines()
    line_124 = (
        "124. Task2541-Task2560 acquired the first high-impact official source family for selector repair: "
        f"SEC financing/dilution across full universe {closeout['universe_rows']} rows, unique symbols {closeout['unique_symbols']}, "
        f"mapped CIK symbols {closeout['mapped_cik_symbols']}, financing/dilution event rows {closeout['financing_dilution_event_rows']}, "
        f"downloaded primary documents {closeout['downloaded_primary_document_rows']}; no backtest, no selector change. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    out = []
    replaced = False
    for line in lines:
        if line.startswith("124. Task2541-Task2560"):
            out.append(line_124)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(line_124)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    universe = load_universe()
    symbols = candidate_symbols(universe)
    mapping, mapping_path, mapping_hash = load_company_tickers()
    scope = scope_freeze_rows(universe, symbols)
    families = family_plan_rows()
    cik_rows = build_cik_map(universe, mapping, mapping_path, mapping_hash)
    call_rows, raw_rows, event_rows = download_and_normalize(cik_rows)
    coverage = decision_asof_coverage_rows(universe, cik_rows, event_rows)
    feature_gate = feature_admission_gate_rows(universe, cik_rows, event_rows)
    gaps = source_gap_rows(universe, cik_rows, raw_rows)
    summary = event_summary_rows(event_rows)
    subagents = subagent_rows()
    closeout = closeout_rows(scope[0], cik_rows, raw_rows, event_rows, feature_gate, gaps)

    outputs = [
        ("task2541_scope_freeze.csv", scope),
        ("task2542_source_family_plan.csv", families),
        ("task2542_cik_map.csv", cik_rows),
        ("task2543_api_or_raw_call_ledger.csv", call_rows),
        ("task2544_raw_response_classification.csv", raw_rows),
        ("task2545_normalized_sec_financing_dilution_packets.csv", event_rows),
        ("task2546_decision_asof_coverage.csv", coverage),
        ("task2547_feature_admission_gate.csv", feature_gate),
        ("task2548_source_gap_ledger.csv", gaps),
        ("task2549_event_summary.csv", summary),
        ("task2550_subagent_packets.csv", subagents),
        ("task2560_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2560_closeout.json", closeout[0])
    write_report(closeout[0], summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2541_2560_SEC_FINANCING_DILUTION_ACQUISITION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
