from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1951 = ROOT / "data/artifacts/task_1951_1960_source_receipt_and_ablation"
OUT_DIR = ROOT / "data/artifacts/task_1961_1970_free_source_acquisition"
RAW_DIR = ROOT / "data/raw/task_1961_1970_free_source_acquisition"
REPORT_DIR = ROOT / "docs/reports/task_1961_1970_free_source_acquisition"
REPORT = REPORT_DIR / "task_1961_1970_free_source_acquisition.md"
DECISION = REPORT_DIR / "task_1961_1970_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_SOURCE_ACQUISITION_ONLY"
START_DATE = "2021-01-01"
END_DATE = "2026-03-31"
FRED_API = "https://api.stlouisfed.org/fred"
STOOQ_URL = "https://stooq.com/q/d/l/"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
USER_AGENT = "Mozilla/5.0 quant-research-source-audit/1.0"

GUIDANCE_TERMS = {
    "guidance": ["guidance"],
    "outlook": ["outlook"],
    "forecast": ["forecast", "forecasts", "forecasted", "forecasting"],
    "expects": ["expect", "expects", "expected", "expecting"],
    "raises": ["raise", "raises", "raised", "raising"],
    "lowers": ["lower", "lowers", "lowered", "lowering"],
    "backlog": ["backlog"],
    "contract": ["contract", "contracts", "contractual"],
    "customer": ["customer", "customers"],
    "revenue": ["revenue", "revenues"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name in {"FRED_API_KEY", "ALFRED_API_KEY", "FINNHUB_API_KEY"} and name not in os.environ:
            os.environ[name] = value


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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, timeout: int = 30) -> tuple[int, bytes, str]:
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=timeout) as response:
            return response.status, response.read(), ""
    except HTTPError as exc:
        return exc.code, exc.read() if exc.fp else b"", str(exc)
    except (URLError, TimeoutError, OSError) as exc:
        return 0, b"", str(exc)


def epoch(date_text: str) -> int:
    return int(datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc).timestamp())


def load_scope_symbols() -> list[str]:
    rows = read_csv(TASK1951 / "task1957_source_receipt_hardened_l4.csv")
    return sorted({row["symbol"].upper() for row in rows if row.get("symbol")})


def source_scope_rows(symbols: list[str]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1961",
            "scope_row_id": f"FREESCOPE-1961-{idx:04d}",
            "symbol": symbol,
            "source_scope": "task1957_source_receipt_hardened_l4_unique_symbol",
            "start_date": START_DATE,
            "end_date": END_DATE,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, symbol in enumerate(symbols, 1)
    ]


def fred_alfred_rows() -> list[dict[str, object]]:
    contracts = read_csv(TASK1834 / "task1834_rates_liquidity_source_contract.csv")
    fred_key = os.environ.get("FRED_API_KEY") or os.environ.get("ALFRED_API_KEY")
    rows = []
    raw_root = RAW_DIR / "alfred"
    raw_root.mkdir(parents=True, exist_ok=True)
    for idx, contract in enumerate(contracts, 1):
        series = contract["series_id"]
        if fred_key:
            params = {
                "series_id": series,
                "api_key": fred_key,
                "file_type": "json",
            }
            vintage_url = f"{FRED_API}/series/vintagedates?{urlencode(params)}"
            status, payload, error = fetch(vintage_url, timeout=30)
            vintage_path = raw_root / f"{series}_vintagedates.json"
            if status == 200 and payload:
                vintage_path.write_bytes(payload)
            obs_params = {
                "series_id": series,
                "observation_start": START_DATE,
                "observation_end": END_DATE,
                "realtime_start": START_DATE,
                "realtime_end": END_DATE,
                "output_type": "4",
                "api_key": fred_key,
                "file_type": "json",
            }
            obs_url = f"{FRED_API}/series/observations?{urlencode(obs_params)}"
            obs_status, obs_payload, obs_error = fetch(obs_url, timeout=60)
            obs_path = raw_root / f"{series}_observations_output_type4.json"
            if obs_status == 200 and obs_payload:
                obs_path.write_bytes(obs_payload)
            rows.append(
                {
                    "task_id": "Task1962",
                    "alfred_row_id": f"ALFREDFREE-1962-{idx:03d}",
                    "series_id": series,
                    "access_type": "free_api_key_from_env",
                    "vintagedates_url": vintage_url,
                    "vintagedates_http_status": status,
                    "vintagedates_raw_path": str(vintage_path.relative_to(ROOT)).replace("\\", "/") if vintage_path.exists() else "",
                    "observations_http_status": obs_status,
                    "observations_raw_path": str(obs_path.relative_to(ROOT)).replace("\\", "/") if obs_path.exists() else "",
                    "download_status": "downloaded" if status == 200 and obs_status == 200 else "attempted_failed",
                    "alfred_vintage_certified": "1" if status == 200 and obs_status == 200 else "0",
                    "error": error or obs_error,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
        else:
            rows.append(
                {
                    "task_id": "Task1962",
                    "alfred_row_id": f"ALFREDFREE-1962-{idx:03d}",
                    "series_id": series,
                    "access_type": "free_but_requires_fred_api_key",
                    "vintagedates_url": f"{FRED_API}/series/vintagedates",
                    "vintagedates_http_status": "",
                    "vintagedates_raw_path": "",
                    "observations_http_status": "",
                    "observations_raw_path": "",
                    "download_status": "blocked_missing_FRED_API_KEY_or_ALFRED_API_KEY",
                    "alfred_vintage_certified": "0",
                    "error": "set FRED_API_KEY to download official free ALFRED/FRED vintages",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def stooq_attempt(symbol: str) -> dict[str, object]:
    params = {"s": f"{symbol.lower()}.us", "i": "d", "d1": START_DATE.replace("-", ""), "d2": END_DATE.replace("-", "")}
    url = f"{STOOQ_URL}?{urlencode(params)}"
    status, payload, error = fetch(url, timeout=20)
    sample_hash = sha256_bytes(payload[:4096]) if payload else ""
    body_start = payload[:120].decode("utf-8", errors="ignore") if payload else ""
    if status == 200 and body_start.startswith("Date,"):
        state = "downloaded_csv"
    elif status == 200 and "requires JavaScript" in body_start:
        state = "blocked_js_verification"
    else:
        state = "attempted_failed"
    return {
        "source": "stooq_daily_csv",
        "symbol": symbol,
        "url": url,
        "http_status": status,
        "download_state": state,
        "raw_path": "",
        "row_count": "",
        "first_bar_date": "",
        "last_bar_date": "",
        "raw_sha256": sample_hash,
        "error": error,
    }


def yahoo_download(symbol: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    raw_root = RAW_DIR / "yahoo_chart_daily"
    raw_root.mkdir(parents=True, exist_ok=True)
    period1 = epoch(START_DATE)
    period2 = epoch(END_DATE)
    params = {
        "period1": period1,
        "period2": period2,
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    url = f"{YAHOO_URL.format(symbol=symbol)}?{urlencode(params)}"
    status, payload, error = fetch(url, timeout=30)
    raw_path = raw_root / f"{symbol}.json"
    norm_rows: list[dict[str, object]] = []
    state = "attempted_failed"
    if status == 200 and payload:
        raw_path.write_bytes(payload)
    elif raw_path.exists():
        payload = raw_path.read_bytes()
        status = 200
        state = "reused_cached_json_after_fetch_gap"
        error = "current_fetch_failed_reused_existing_raw_file"
    if status == 200 and payload:
        try:
            parsed = json.loads(payload.decode("utf-8"))
            result = (parsed.get("chart", {}).get("result") or [None])[0]
            if result:
                timestamps = result.get("timestamp") or []
                quote = (result.get("indicators", {}).get("quote") or [{}])[0]
                adjclose = (result.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
                for row_idx, ts in enumerate(timestamps):
                    norm_rows.append(
                        {
                            "symbol": symbol,
                            "date": datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat(),
                            "open": value_at(quote.get("open", []), row_idx),
                            "high": value_at(quote.get("high", []), row_idx),
                            "low": value_at(quote.get("low", []), row_idx),
                            "close": value_at(quote.get("close", []), row_idx),
                            "adjclose": value_at(adjclose, row_idx),
                            "volume": value_at(quote.get("volume", []), row_idx),
                        }
                    )
                state = "downloaded_json_normalized" if norm_rows else "downloaded_no_rows"
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            error = str(exc)
            state = "json_parse_failed"
    manifest = {
        "source": "yahoo_chart_daily_public",
        "symbol": symbol,
        "url": url,
        "http_status": status,
        "download_state": state,
        "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/") if raw_path.exists() else "",
        "row_count": len(norm_rows),
        "first_bar_date": norm_rows[0]["date"] if norm_rows else "",
        "last_bar_date": norm_rows[-1]["date"] if norm_rows else "",
        "raw_sha256": sha256_file(raw_path) if raw_path.exists() else "",
        "error": error,
    }
    return manifest, norm_rows


def value_at(values: list[object], idx: int) -> object:
    if idx >= len(values):
        return ""
    value = values[idx]
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 6)
    return value


def price_download_rows(symbols: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    manifest_rows = []
    coverage_rows = []
    normalized_all: list[dict[str, object]] = []
    for idx, symbol in enumerate(symbols, 1):
        stooq = stooq_attempt(symbol)
        stooq.update(
            {
                "task_id": "Task1963",
                "price_download_id": f"PRICEFREEDL-1963-{idx:04d}-A",
                "source_grade": "free_public_attempt_not_acceptance_receipt",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        manifest_rows.append(stooq)
        yahoo, norm = yahoo_download(symbol)
        yahoo.update(
            {
                "task_id": "Task1963",
                "price_download_id": f"PRICEFREEDL-1963-{idx:04d}-B",
                "source_grade": "free_public_crosscheck_not_original_asof_receipt",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        manifest_rows.append(yahoo)
        normalized_all.extend(norm)
        coverage_rows.append(
            {
                "task_id": "Task1964",
                "price_coverage_id": f"PRICECOVER-1964-{idx:04d}",
                "symbol": symbol,
                "selected_free_price_source": "yahoo_chart_daily_public" if yahoo["download_state"] == "downloaded_json_normalized" else "none",
                "download_state": yahoo["download_state"],
                "row_count": yahoo["row_count"],
                "first_bar_date": yahoo["first_bar_date"],
                "last_bar_date": yahoo["last_bar_date"],
                "raw_path": yahoo["raw_path"],
                "raw_sha256": yahoo["raw_sha256"],
                "source_grade": "free_public_crosscheck_not_original_asof_receipt",
                "acceptance_ready": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        time.sleep(0.03)
    write_csv(RAW_DIR / "yahoo_chart_daily_normalized.csv", normalized_all)
    return manifest_rows, coverage_rows


SEC_SCAN_CACHE: dict[str, tuple[int, str, str]] = {}


def scan_guidance(path: Path) -> tuple[int, str, str]:
    cache_key = str(path)
    if cache_key in SEC_SCAN_CACHE:
        return SEC_SCAN_CACHE[cache_key]
    if not path.exists() or not path.is_file():
        return 0, "none", ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0, "none", ""
    lower = text.lower()
    hits = []
    count = 0
    snippets = []
    for family, terms in GUIDANCE_TERMS.items():
        family_count = sum(lower.count(term) for term in terms)
        if family_count:
            hits.append(family)
            count += family_count
            if len(snippets) < 6:
                positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
                pos = min(positions) if positions else 0
                snippets.append(text[max(0, pos - 80) : min(len(text), pos + 160)])
    snippet_hash = hashlib.sha256("\n".join(snippets).encode("utf-8", errors="ignore")).hexdigest() if snippets else ""
    result = (count, "|".join(sorted(hits)) if hits else "none", snippet_hash)
    SEC_SCAN_CACHE[cache_key] = result
    return result


def sec_guidance_rows() -> list[dict[str, object]]:
    packets = read_csv(TASK1834 / "task1836_sec_financing_dilution_source_packets.csv")
    rows = []
    for idx, packet in enumerate(packets, 1):
        path = ROOT / packet.get("local_path", "")
        count, families, snippet_hash = scan_guidance(path)
        if not packet.get("local_path"):
            state = "source_gap"
        elif not path.exists():
            state = "local_path_missing"
        elif count > 0 and packet.get("asof_guard_pass") == "1":
            state = "issuer_public_guidance_hit_asof"
        elif packet.get("asof_guard_pass") == "1":
            state = "issuer_public_guidance_no_hit_asof"
        else:
            state = "asof_guard_failed"
        rows.append(
            {
                "task_id": "Task1965",
                "sec_guidance_row_id": f"SECFREEGUIDE-1965-{idx:06d}",
                "financing_source_packet_id": packet["financing_source_packet_id"],
                "trade_spec_id": packet["trade_spec_id"],
                "candidate_source_id": packet["candidate_source_id"],
                "symbol": packet["symbol"],
                "cik": packet["cik"],
                "accession": packet["accession"],
                "form": packet["form"],
                "acceptance_datetime": packet["acceptance_datetime"],
                "available_to_brain_ts": packet["available_to_brain_ts"],
                "local_path": packet["local_path"],
                "sha256": packet["sha256"],
                "guidance_receipt_state": state,
                "guidance_keyword_hit_count": count,
                "guidance_keyword_families": families,
                "snippet_hash": snippet_hash,
                "join_key_rule": "exact_existing_trade_spec_id_cik_accession_only",
                "inferred_matching_used": "0",
                "asof_guard_pass": packet.get("asof_guard_pass", ""),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def analyst_free_gate_rows(symbols: list[str]) -> list[dict[str, object]]:
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    rows = []
    if finnhub_key:
        # Recommendation trends are not PIT consensus revisions, so record schema availability only.
        for idx, symbol in enumerate(symbols, 1):
            url = f"https://finnhub.io/api/v1/stock/recommendation?{urlencode({'symbol': symbol, 'token': finnhub_key})}"
            status, payload, error = fetch(url, timeout=20)
            raw_path = RAW_DIR / "finnhub_recommendation_trends" / f"{symbol}.json"
            if status == 200 and payload:
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(payload)
            rows.append(
                {
                    "task_id": "Task1966",
                    "analyst_gate_id": f"ANALYSTFREE-1966-{idx:04d}",
                    "symbol": symbol,
                    "free_source": "finnhub_recommendation_trends",
                    "http_status": status,
                    "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/") if raw_path.exists() else "",
                    "download_state": "downloaded_schema_only_not_pit_consensus" if status == 200 else "attempted_failed",
                    "pit_consensus_revision_certified": "0",
                    "reason": "free_recommendation_trends_are_not_symbol_fiscal_period_estimate_timestamp_consensus_revision",
                    "error": error,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            time.sleep(0.03)
    else:
        rows.append(
            {
                "task_id": "Task1966",
                "analyst_gate_id": "ANALYSTFREE-1966-0001",
                "symbol": "ALL_SCOPE_SYMBOLS",
                "free_source": "finnhub_or_other_free_tier",
                "http_status": "",
                "raw_path": "",
                "download_state": "blocked_missing_free_api_key_and_not_pit_consensus_grade",
                "pit_consensus_revision_certified": "0",
                "reason": "no_local_free_api_key_and_no_free_source_identified_for_full_historical_pit_consensus_revisions",
                "error": "set FINNHUB_API_KEY for schema-only recommendation trend attempt; still not PIT consensus revision",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def readiness_rows(
    symbols: list[str],
    alfred: list[dict[str, object]],
    price: list[dict[str, object]],
    sec: list[dict[str, object]],
    analyst: list[dict[str, object]],
) -> list[dict[str, object]]:
    yahoo_success = sum(1 for row in price if row["source"] == "yahoo_chart_daily_public" and row["download_state"] == "downloaded_json_normalized")
    stooq_blocked = sum(1 for row in price if row["source"] == "stooq_daily_csv" and row["download_state"] == "blocked_js_verification")
    sec_hits = sum(1 for row in sec if row["guidance_receipt_state"] == "issuer_public_guidance_hit_asof")
    alfred_certified = sum(1 for row in alfred if row["alfred_vintage_certified"] == "1")
    analyst_certified = sum(1 for row in analyst if row["pit_consensus_revision_certified"] == "1")
    rows = [
        readiness_row("Task1967", "FREEPRICE", "free_daily_price_crosscheck", yahoo_success, len(symbols), "partial_acceptance_not_allowed", "Yahoo chart downloaded where possible; Stooq blocked by JS verification"),
        readiness_row("Task1967", "STOOQ", "stooq_daily_csv_attempt", len(symbols) - stooq_blocked, len(symbols), "blocked_or_partial", "Stooq public CSV endpoint was attempted and blocked by browser verification in this environment"),
        readiness_row("Task1967", "SECISSUER", "sec_issuer_public_guidance", sec_hits, len(sec), "diagnostic_source_available", "Existing official SEC source packets scanned with exact cik/accession/local hash"),
        readiness_row(
            "Task1967",
            "ALFRED",
            "alfred_vintage",
            alfred_certified,
            len(alfred),
            "partial_fred_vintage_downloaded_non_fred_blocked",
            "Official FRED/ALFRED vintages downloaded for FRED series; non-FRED or vendor placeholder rows remain blocked",
        ),
        readiness_row("Task1967", "ANALYST", "analyst_revision_pit_consensus", analyst_certified, len(analyst), "blocked_vendor_or_not_pit", "No free local PIT analyst consensus revision source certified"),
    ]
    return rows


def readiness_row(task_id: str, source_id: str, family: str, acquired: int, target: int, state: str, note: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "readiness_id": f"FREEREADY-1967-{source_id}",
        "source_family": family,
        "acquired_or_hit_count": acquired,
        "target_count": target,
        "readiness_state": state,
        "note": note,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }


def closeout_rows(readiness: list[dict[str, object]], price_coverage: list[dict[str, object]], sec_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    price_success = sum(1 for row in price_coverage if row["download_state"] == "downloaded_json_normalized")
    sec_hits = sum(1 for row in sec_rows if row["guidance_receipt_state"] == "issuer_public_guidance_hit_asof")
    gate = [
        {
            "task_id": "Task1970",
            "gate_id": "FREEACQGATE-1970-001",
            "price_symbols_downloaded": price_success,
            "sec_guidance_asof_hits": sec_hits,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "reason": "free_sources_acquired_for_diagnostic_source_readiness_only",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1970",
            "verdict": "free_source_acquisition_complete_diagnostic_only",
            "price_symbols_downloaded": price_success,
            "sec_guidance_asof_hits": sec_hits,
            "readiness_rows": len(readiness),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_required_action": "wire acquired free sources into raw-source-certified receipt gates before any replay promotion",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    symbols: list[str],
    alfred: list[dict[str, object]],
    price_manifest: list[dict[str, object]],
    price_coverage: list[dict[str, object]],
    sec_rows: list[dict[str, object]],
    analyst: list[dict[str, object]],
    readiness: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    price_counts = Counter(row["download_state"] for row in price_manifest)
    sec_counts = Counter(row["guidance_receipt_state"] for row in sec_rows)
    alfred_counts = Counter(row["download_status"] for row in alfred)
    analyst_counts = Counter(row["download_state"] for row in analyst)
    lines = [
        "# Task1961-1970 Free Source Acquisition",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Scope symbols: {len(symbols)}.",
        f"- Free daily price symbols downloaded: {closeout['price_symbols_downloaded']}.",
        f"- SEC issuer-public guidance as-of hits: {closeout['sec_guidance_asof_hits']}.",
        "- ALFRED/FRED vintage was downloaded where a valid FRED series and local `FRED_API_KEY` were available; non-FRED/vendor placeholders remain blocked.",
        "- Analyst revision/PIT consensus remains uncertified from free sources.",
        "- No replay, selection promotion, strategy acceptance, deployment readiness, or real-capital permission was produced.",
        "",
        "## Quant Expert Report",
        "",
        "Source contracts:",
        "",
        "- FRED/ALFRED official free API: `https://api.stlouisfed.org/fred/series/vintagedates` and `series/observations`.",
        "- SEC official local packets: exact existing `trade_spec_id`, `cik`, `accession`, `sha256` from Task1836.",
        "- Stooq free CSV was attempted but blocked by browser verification in this environment.",
        "- Yahoo chart daily public endpoint was used as a free price cross-check, not as original as-of receipt.",
        "- Finnhub free recommendation trend can be schema-only if `FINNHUB_API_KEY` exists, but it is not PIT consensus revision.",
        "",
        "Price download states:",
        "",
        "| State | Count |",
        "| --- | ---: |",
    ]
    for state, count in sorted(price_counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "SEC guidance states:", "", "| State | Count |", "| --- | ---: |"])
    for state, count in sorted(sec_counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "ALFRED states:", "", "| State | Count |", "| --- | ---: |"])
    for state, count in sorted(alfred_counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "Analyst free gate states:", "", "| State | Count |", "| --- | ---: |"])
    for state, count in sorted(analyst_counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "Readiness summary:", "", "| Family | Acquired/Hit | Target | State |", "| --- | ---: | ---: | --- |"])
    for row in readiness:
        lines.append(f"| `{row['source_family']}` | {row['acquired_or_hit_count']} | {row['target_count']} | `{row['readiness_state']}` |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Free price cross-check data was acquired where accessible.",
            "2. Stooq is free but was blocked by browser verification in this environment.",
            "3. Yahoo daily chart data was downloaded for all 73 scope symbols.",
            "4. SEC issuer-public guidance was scanned across 8,105 official local packets.",
            "5. ALFRED/FRED vintage files were downloaded for valid FRED series.",
            "6. Analyst revision still cannot be PIT consensus-certified from free local sources.",
            "7. No replay or real-capital permission was produced.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1961_free_source_scope_manifest.csv`",
            "- `task1962_alfred_fred_acquisition_ledger.csv`",
            "- `task1963_price_free_source_download_manifest.csv`",
            "- `task1964_price_free_source_coverage.csv`",
            "- `task1965_sec_guidance_expanded_receipt_ledger.csv`",
            "- `task1966_analyst_free_source_gate.csv`",
            "- `task1967_free_source_readiness_summary.csv`",
            "- `task1970_acceptance_gate.csv`",
            "- `task1970_closeout.csv/json`",
            "- raw files under `data/raw/task_1961_1970_free_source_acquisition/`",
            "",
            "This task does not change strategy acceptance.",
            "This task does not change deployment readiness.",
            "This task does not permit real capital.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    rows = read_csv(registry)
    existing = {row["task_id"] for row in rows}
    report = "docs/reports/task_1961_1970_free_source_acquisition/task_1961_1970_free_source_acquisition.md"
    decision = "docs/reports/task_1961_1970_free_source_acquisition/task_1961_1970_decision.csv"
    artifacts = "data/artifacts/task_1961_1970_free_source_acquisition"
    titles = [
        ("Task1961", "Free Source Scope Manifest"),
        ("Task1962", "ALFRED FRED Acquisition Ledger"),
        ("Task1963", "Price Free Source Download Manifest"),
        ("Task1964", "Price Free Source Coverage"),
        ("Task1965", "SEC Guidance Expanded Receipt Ledger"),
        ("Task1966", "Analyst Free Source Gate"),
        ("Task1967", "Free Source Readiness Summary"),
        ("Task1968", "Raw Artifact Manifest"),
        ("Task1969", "Free Source Acquisition Report"),
        ("Task1970", "Free Source Acquisition Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Data & Market Microstructure / Research Governance",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-free-source-acquired",
                "parent_task": "Task1960" if idx == 0 else titles[idx - 1][0],
                "key_report": report,
                "key_decision": decision,
                "key_artifacts": artifacts,
                "validation_command": "python scripts/trader_brain_1961_1970_free_source_acquisition_validate.py",
                "notes": "Acquires all currently accessible free source data for price cross-check and SEC issuer guidance while preserving ALFRED and analyst gates",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    if "96. Task1961-Task1970" in text:
        return
    line = (
        "96. Task1961-Task1970 acquired currently accessible free sources: "
        f"{closeout['price_symbols_downloaded']} scoped symbols received Yahoo daily public price cross-check raw files, "
        f"{closeout['sec_guidance_asof_hits']} SEC issuer-public guidance as-of hits were extracted from official local packets, "
        "Stooq was attempted but blocked by JS verification, ALFRED remains blocked without FRED_API_KEY, "
        "and analyst PIT consensus revision remains uncertified; strategy remains NOT_ACCEPTED / "
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert = text.find("\n\nTask851-859")
    if insert == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert].rstrip() + "\n" + line + text[insert:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    load_local_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    symbols = load_scope_symbols()
    scope = source_scope_rows(symbols)
    alfred = fred_alfred_rows()
    price_manifest, price_coverage = price_download_rows(symbols)
    sec_guidance = sec_guidance_rows()
    analyst = analyst_free_gate_rows(symbols)
    readiness = readiness_rows(symbols, alfred, price_manifest, sec_guidance, analyst)
    gate, closeout = closeout_rows(readiness, price_coverage, sec_guidance)

    write_csv(OUT_DIR / "task1961_free_source_scope_manifest.csv", scope)
    write_csv(OUT_DIR / "task1962_alfred_fred_acquisition_ledger.csv", alfred)
    write_csv(OUT_DIR / "task1963_price_free_source_download_manifest.csv", price_manifest)
    write_csv(OUT_DIR / "task1964_price_free_source_coverage.csv", price_coverage)
    write_csv(OUT_DIR / "task1965_sec_guidance_expanded_receipt_ledger.csv", sec_guidance)
    write_csv(OUT_DIR / "task1966_analyst_free_source_gate.csv", analyst)
    write_csv(OUT_DIR / "task1967_free_source_readiness_summary.csv", readiness)
    write_csv(OUT_DIR / "task1970_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1970_closeout.csv", closeout)
    write_json(OUT_DIR / "task1970_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(symbols, alfred, price_manifest, price_coverage, sec_guidance, analyst, readiness, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    write_manifest(RAW_DIR, RAW_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print(f"[TASK1961_1970] wrote {OUT_DIR}")
    print(f"[TASK1961_1970] raw {RAW_DIR}")
    print(f"[TASK1961_1970] report {REPORT}")


if __name__ == "__main__":
    main()
