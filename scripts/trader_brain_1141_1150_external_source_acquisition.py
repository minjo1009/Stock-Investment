from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1141_1150_external_sources"
OUT_DIR = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"
REPORT_DIR = ROOT / "docs/reports/task_1141_1150_external_source_acquisition"
UNIVERSE = ROOT / "data/raw/theme_universe_10x7.csv"
TASK1131 = ROOT / "data/artifacts/task_1131_1140_evidence_fill"

AUTHORITY = "DIAGNOSTIC_EXTERNAL_SOURCE_ACQUISITION_ONLY"
HIST_START = "2021-01-01"
HIST_END = "2026-03-31"
USER_AGENT = "minjo-trader-brain-research contact@example.com"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def download(url: str, path: Path, *, timeout: int = 45) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    started = now_utc()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
        path.write_bytes(body)
        return {
            "url": url,
            "raw_source_path": rel(path),
            "download_status": "downloaded",
            "http_status": status,
            "content_type": content_type,
            "downloaded_at_utc": started,
            "size_bytes": len(body),
            "source_hash": sha256(path),
            "error": "",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "raw_source_path": rel(path),
            "download_status": "failed",
            "http_status": "",
            "content_type": "",
            "downloaded_at_utc": started,
            "size_bytes": 0,
            "source_hash": "",
            "error": str(exc)[:500],
        }


def load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def source_catalog_downloads() -> list[dict[str, object]]:
    downloads: list[tuple[str, str, str, str]] = [
        (
            "Task1141",
            "sec_company_tickers",
            "sec",
            "https://www.sec.gov/files/company_tickers.json",
        ),
        (
            "Task1141",
            "sec_company_tickers_exchange",
            "sec",
            "https://www.sec.gov/files/company_tickers_exchange.json",
        ),
        (
            "Task1141",
            "nasdaq_listed_current",
            "exchange_directory",
            "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt",
        ),
        (
            "Task1141",
            "other_listed_current",
            "exchange_directory",
            "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt",
        ),
    ]
    rows: list[dict[str, object]] = []
    for task_id, source_id, family, url in downloads:
        suffix = ".json" if url.endswith(".json") else ".txt"
        meta = download(url, RAW_DIR / source_id / f"{source_id}{suffix}")
        rows.append(
            {
                "task_id": task_id,
                "source_id": source_id,
                "source_family": family,
                "official_source_url": url,
                "historical_scope": "current_file_not_full_historical_pit"
                if family == "exchange_directory"
                else "official_sec_reference",
                "source_time_field_available": "1" if meta["download_status"] == "downloaded" else "0",
                "pit_membership_candidate": "0",
                "download_status": meta["download_status"],
                "http_status": meta["http_status"],
                "downloaded_at_utc": meta["downloaded_at_utc"],
                "raw_source_path": meta["raw_source_path"],
                "source_hash": meta["source_hash"],
                "size_bytes": meta["size_bytes"],
                "error": meta["error"],
                "authority": AUTHORITY,
            }
        )
    return rows


def sec_ticker_map(universe_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    tickers_path = RAW_DIR / "sec_company_tickers/sec_company_tickers.json"
    exchange_path = RAW_DIR / "sec_company_tickers_exchange/sec_company_tickers_exchange.json"
    tickers_json = load_json(tickers_path)
    exchange_json = load_json(exchange_path)

    by_ticker: dict[str, dict[str, object]] = {}
    if isinstance(tickers_json, dict):
        for item in tickers_json.values():
            if isinstance(item, dict) and item.get("ticker"):
                by_ticker[str(item["ticker"]).upper()] = item

    exchange_by_ticker: dict[str, dict[str, object]] = {}
    if isinstance(exchange_json, dict):
        fields = exchange_json.get("fields")
        data = exchange_json.get("data")
        if isinstance(fields, list) and isinstance(data, list):
            for row in data:
                if isinstance(row, list):
                    mapped = {str(fields[i]): row[i] for i in range(min(len(fields), len(row)))}
                    ticker = str(mapped.get("ticker", "")).upper()
                    if ticker:
                        exchange_by_ticker[ticker] = mapped

    rows = []
    for idx, item in enumerate(universe_rows, start=1):
        symbol = item["symbol"].upper()
        sec = by_ticker.get(symbol, {})
        exch = exchange_by_ticker.get(symbol, {})
        cik = str(sec.get("cik_str", "")).zfill(10) if sec.get("cik_str") not in ("", None) else ""
        rows.append(
            {
                "task_id": "Task1142",
                "sec_map_id": f"SECMAP1142-{idx:03d}",
                "theme": item["theme"],
                "symbol": symbol,
                "role": item["role"],
                "cik": cik,
                "sec_entity_name": sec.get("title", ""),
                "sec_exchange": exch.get("exchange", ""),
                "sec_exchange_ticker": exch.get("ticker", ""),
                "sec_mapping_pass": "1" if cik else "0",
                "mapping_source_path": rel(tickers_path) if tickers_path.exists() else "",
                "mapping_source_hash": sha256(tickers_path) if tickers_path.exists() else "",
                "exchange_source_path": rel(exchange_path) if exchange_path.exists() else "",
                "exchange_source_hash": sha256(exchange_path) if exchange_path.exists() else "",
                "pit_theme_membership_pass": "0",
                "pit_theme_membership_block_reason": "sec_ticker_mapping_proves_entity_identity_not_10x7_historical_theme_membership",
                "authority": AUTHORITY,
            }
        )
    return rows


def sec_submission_downloads(sec_map: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(sec_map, start=1):
        cik = str(row["cik"])
        symbol = str(row["symbol"])
        if not cik:
            rows.append(
                {
                    "task_id": "Task1143",
                    "sec_submission_download_id": f"SECSUBDL1143-{idx:03d}",
                    "symbol": symbol,
                    "cik": "",
                    "official_source_url": "",
                    "download_status": "skipped_missing_cik",
                    "http_status": "",
                    "downloaded_at_utc": now_utc(),
                    "raw_source_path": "",
                    "source_hash": "",
                    "accepted_datetime_rows_2021_2026q1": 0,
                    "asof_source_time_available": "0",
                    "authority": AUTHORITY,
                }
            )
            continue
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        path = RAW_DIR / "sec_submissions" / f"CIK{cik}_{symbol}.json"
        meta = download(url, path)
        accepted_count = 0
        if meta["download_status"] == "downloaded":
            payload = load_json(path)
            recent = payload.get("filings", {}).get("recent", {}) if isinstance(payload, dict) else {}
            dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
            accepted = recent.get("acceptanceDateTime", []) if isinstance(recent, dict) else []
            for filing_date, accepted_ts in zip(dates, accepted):
                if HIST_START <= str(filing_date) <= HIST_END and accepted_ts:
                    accepted_count += 1
        rows.append(
            {
                "task_id": "Task1143",
                "sec_submission_download_id": f"SECSUBDL1143-{idx:03d}",
                "symbol": symbol,
                "cik": cik,
                "official_source_url": url,
                "download_status": meta["download_status"],
                "http_status": meta["http_status"],
                "downloaded_at_utc": meta["downloaded_at_utc"],
                "raw_source_path": meta["raw_source_path"],
                "source_hash": meta["source_hash"],
                "accepted_datetime_rows_2021_2026q1": accepted_count,
                "asof_source_time_available": "1" if accepted_count > 0 else "0",
                "authority": AUTHORITY,
            }
        )
        time.sleep(0.12)
    return rows


def current_exchange_directory(universe_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    files = [
        ("nasdaq", RAW_DIR / "nasdaq_listed_current/nasdaq_listed_current.txt"),
        ("other", RAW_DIR / "other_listed_current/other_listed_current.txt"),
    ]
    directory: dict[str, dict[str, str]] = {}
    for venue, path in files:
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            continue
        header = lines[0].split("|")
        for line in lines[1:]:
            if not line or line.startswith("File Creation Time"):
                continue
            parts = line.split("|")
            if len(parts) < 2:
                continue
            mapped = {header[i]: parts[i] for i in range(min(len(header), len(parts)))}
            symbol = mapped.get("Symbol") or mapped.get("ACT Symbol") or ""
            if symbol:
                mapped["directory_file"] = venue
                directory[symbol.upper()] = mapped

    rows = []
    for idx, item in enumerate(universe_rows, start=1):
        symbol = item["symbol"].upper()
        found = directory.get(symbol, {})
        rows.append(
            {
                "task_id": "Task1144",
                "exchange_directory_id": f"EXDIR1144-{idx:03d}",
                "theme": item["theme"],
                "symbol": symbol,
                "role": item["role"],
                "directory_file": found.get("directory_file", ""),
                "security_name": found.get("Security Name", "") or found.get("Security Name", ""),
                "listing_exchange": found.get("Listing Exchange", ""),
                "etf_flag": found.get("ETF", ""),
                "test_issue": found.get("Test Issue", ""),
                "current_directory_match": "1" if found else "0",
                "pit_membership_pass": "0",
                "block_reason": "nasdaq_directory_is_current_snapshot_not_2021_2026_row_level_theme_membership",
                "authority": AUTHORITY,
            }
        )
    return rows


def federal_register_downloads() -> list[dict[str, object]]:
    terms = [
        ("ai_semiconductors", "semiconductor"),
        ("cloud_ai_platforms", "artificial intelligence cloud"),
        ("cybersecurity", "cybersecurity"),
        ("data_devops_software", "data artificial intelligence"),
        ("ev_autonomy_mobility", "electric vehicle autonomous"),
        ("power_grid_electrification", "power grid electricity"),
        ("biotech_glp1_healthcare", "drug approval diabetes obesity"),
        ("crypto_fintech", "cryptocurrency digital asset"),
        ("aerospace_defense_space", "space defense aerospace"),
        ("industrial_automation_robotics", "robotics automation"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (theme, term) in enumerate(terms, start=1):
        query = urllib.parse.urlencode(
            {
                "conditions[term]": term,
                "conditions[publication_date][gte]": HIST_START,
                "conditions[publication_date][lte]": HIST_END,
                "per_page": "1000",
                "order": "newest",
            }
        )
        url = f"https://www.federalregister.gov/api/v1/documents.json?{query}"
        path = RAW_DIR / "federal_register" / f"{idx:02d}_{theme}.json"
        meta = download(url, path, timeout=60)
        count = 0
        if meta["download_status"] == "downloaded":
            payload = load_json(path)
            count = int(payload.get("count", 0)) if isinstance(payload, dict) else 0
        rows.append(
            {
                "task_id": "Task1145",
                "fr_download_id": f"FR1145-{idx:03d}",
                "theme": theme,
                "search_term": term,
                "official_source_url": url,
                "download_status": meta["download_status"],
                "http_status": meta["http_status"],
                "downloaded_at_utc": meta["downloaded_at_utc"],
                "raw_source_path": meta["raw_source_path"],
                "source_hash": meta["source_hash"],
                "result_count": count,
                "published_asof_source_available": "1" if count > 0 else "0",
                "project_historical_receipt_available": "0",
                "dynamic_replay_use_allowed": "0",
                "block_reason": "official_publication_date_available_but_no_project_historical_receipt_and_no_symbol_level_extractor_yet",
                "authority": AUTHORITY,
            }
        )
        time.sleep(0.1)
    return rows


def macro_vintage_downloads() -> list[dict[str, object]]:
    series = ["DFF", "DGS10", "CPIAUCSL", "UNRATE", "PAYEMS", "INDPRO"]
    vintages = ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31", "2026-03-31"]
    rows: list[dict[str, object]] = []
    idx = 0
    for series_id in series:
        for vintage in vintages:
            idx += 1
            query = urllib.parse.urlencode({"id": series_id, "vintage_date": vintage})
            url = f"https://alfred.stlouisfed.org/graph/fredgraph.csv?{query}"
            path = RAW_DIR / "alfred_vintages" / series_id / f"{series_id}_{vintage}.csv"
            meta = download(url, path, timeout=8)
            rows.append(
                {
                    "task_id": "Task1146",
                    "macro_vintage_download_id": f"MACRO1146-{idx:04d}",
                    "series_id": series_id,
                    "vintage_date": vintage,
                    "official_source_url": url,
                    "download_status": meta["download_status"],
                    "http_status": meta["http_status"],
                    "downloaded_at_utc": meta["downloaded_at_utc"],
                    "raw_source_path": meta["raw_source_path"],
                    "source_hash": meta["source_hash"],
                    "source_time_field_available": "1" if meta["download_status"] == "downloaded" else "0",
                    "project_historical_receipt_available": "0",
                    "dynamic_replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
            time.sleep(0.05)
    return rows


def pit_resolution_matrix(
    universe_rows: list[dict[str, str]],
    sec_map: list[dict[str, object]],
    exchange_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    sec_by_symbol = {str(row["symbol"]): row for row in sec_map}
    exchange_by_symbol = {str(row["symbol"]): row for row in exchange_rows}
    rows = []
    for idx, item in enumerate(universe_rows, start=1):
        symbol = item["symbol"].upper()
        sec = sec_by_symbol.get(symbol, {})
        exch = exchange_by_symbol.get(symbol, {})
        rows.append(
            {
                "task_id": "Task1147",
                "pit_resolution_id": f"PITRES1147-{idx:03d}",
                "theme": item["theme"],
                "symbol": symbol,
                "role": item["role"],
                "sec_identity_pass": sec.get("sec_mapping_pass", "0"),
                "current_exchange_directory_match": exch.get("current_directory_match", "0"),
                "row_level_theme_membership_source": "0",
                "effective_start_ts": "",
                "published_ts": "",
                "received_ts": "",
                "available_to_brain_ts": "",
                "pit_membership_pass": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "block_reason": "external_official_sources_prove_entity_or_current_listing_not_custom_10x7_historical_theme_membership",
                "authority": AUTHORITY,
            }
        )
    return rows


def receipt_resolution_matrix(
    sec_submissions: list[dict[str, object]],
    fr_rows: list[dict[str, object]],
    macro_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    sec_symbols = sum(1 for row in sec_submissions if row["asof_source_time_available"] == "1")
    sec_accepted = sum(int(row["accepted_datetime_rows_2021_2026q1"]) for row in sec_submissions)
    fr_downloads = sum(1 for row in fr_rows if row["download_status"] == "downloaded")
    fr_docs = sum(int(row["result_count"]) for row in fr_rows)
    macro_downloads = sum(1 for row in macro_rows if row["download_status"] == "downloaded")
    rows = [
        {
            "task_id": "Task1148",
            "source_family": "sec_submissions",
            "official_downloaded_units": sec_symbols,
            "official_asof_rows": sec_accepted,
            "official_publication_or_acceptance_time_available": "1" if sec_accepted > 0 else "0",
            "project_historical_receipt_available": "0",
            "dynamic_replay_use_allowed": "0",
            "resolution_state": "official_acceptance_time_available_but_project_historical_receipt_not_proven",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1148",
            "source_family": "federal_register",
            "official_downloaded_units": fr_downloads,
            "official_asof_rows": fr_docs,
            "official_publication_or_acceptance_time_available": "1" if fr_docs > 0 else "0",
            "project_historical_receipt_available": "0",
            "dynamic_replay_use_allowed": "0",
            "resolution_state": "official_publication_time_available_but_symbol_linkage_and_project_receipt_not_proven",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1148",
            "source_family": "alfred_macro_vintage",
            "official_downloaded_units": macro_downloads,
            "official_asof_rows": macro_downloads,
            "official_publication_or_acceptance_time_available": "1" if macro_downloads > 0 else "0",
            "project_historical_receipt_available": "0",
            "dynamic_replay_use_allowed": "0",
            "resolution_state": "vintage_files_downloaded_when_available_but_project_historical_receipt_not_proven",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1148",
            "source_family": "custom_10x7_theme_universe",
            "official_downloaded_units": 0,
            "official_asof_rows": 0,
            "official_publication_or_acceptance_time_available": "0",
            "project_historical_receipt_available": "0",
            "dynamic_replay_use_allowed": "0",
            "resolution_state": "no_external_official_source_can_prove_after_the_fact_custom_theme_membership_creation_time",
            "authority": AUTHORITY,
        },
    ]
    return rows


def replay_readiness(
    pit_rows: list[dict[str, object]],
    receipt_rows: list[dict[str, object]],
    fr_rows: list[dict[str, object]],
    macro_rows: list[dict[str, object]],
    sec_submissions: list[dict[str, object]],
) -> list[dict[str, object]]:
    pit_pass = sum(1 for row in pit_rows if row["pit_membership_pass"] == "1")
    sec_accepted = sum(int(row["accepted_datetime_rows_2021_2026q1"]) for row in sec_submissions)
    fr_docs = sum(int(row["result_count"]) for row in fr_rows)
    macro_downloaded = sum(1 for row in macro_rows if row["download_status"] == "downloaded")
    project_receipt_pass = sum(1 for row in receipt_rows if row["project_historical_receipt_available"] == "1")
    return [
        {
            "task_id": "Task1149",
            "readiness_id": "READINESS1149-001",
            "pit_rows": len(pit_rows),
            "pit_membership_pass_rows": pit_pass,
            "sec_accepted_datetime_rows_2021_2026q1": sec_accepted,
            "federal_register_official_doc_count": fr_docs,
            "alfred_vintage_files_downloaded": macro_downloaded,
            "project_historical_receipt_pass_families": project_receipt_pass,
            "policy_preregistration_allowed": "0",
            "replay_executed": "0",
            "selection_promoted": "0",
            "verdict": "blocked_pit_theme_membership_and_project_receipt_not_proven",
            "authority": AUTHORITY,
        }
    ]


def closeout(readiness: list[dict[str, object]]) -> dict[str, object]:
    row = readiness[0]
    return {
        "task_id": "Task1141-1150",
        "verdict": row["verdict"],
        "pit_rows": row["pit_rows"],
        "pit_membership_pass_rows": row["pit_membership_pass_rows"],
        "sec_accepted_datetime_rows_2021_2026q1": row["sec_accepted_datetime_rows_2021_2026q1"],
        "federal_register_official_doc_count": row["federal_register_official_doc_count"],
        "alfred_vintage_files_downloaded": row["alfred_vintage_files_downloaded"],
        "policy_preregistration_allowed": "0",
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "decide_between_historical_capture_evidence_vendor_feed_or_redefine_replay_universe_to_official_public_listing_universe",
        "authority": AUTHORITY,
    }


def write_report(decision: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1141_1150_external_source_acquisition.md"
    lines = [
        "# Task1141-1150 External Source Acquisition",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision['verdict']}`.",
        f"- Strategy acceptance: `{decision['strategy_acceptance']}`.",
        f"- Deployment readiness: `{decision['deployment_readiness']}`.",
        f"- Real capital: `{decision['real_capital']}`.",
        "- Replay executed: 0.",
        "- Selection promoted: 0.",
        "- What changed: official external sources were actually downloaded and hashed.",
        "",
        "## Quant Expert Report",
        "",
        "Downloaded source families:",
        "",
        "- SEC ticker and submission APIs.",
        "- Nasdaq Trader current symbol directories.",
        "- Federal Register historical search API, 2021-01-01 through 2026-03-31.",
        "- ALFRED vintage CSV attempts for macro series.",
        "",
        "Key results:",
        "",
        f"- PIT universe rows: {decision['pit_rows']}.",
        f"- PIT membership pass rows: {decision['pit_membership_pass_rows']}.",
        f"- SEC accepted-datetime rows in historical window: {decision['sec_accepted_datetime_rows_2021_2026q1']}.",
        f"- Federal Register official document count: {decision['federal_register_official_doc_count']}.",
        f"- ALFRED vintage files downloaded: {decision['alfred_vintage_files_downloaded']}.",
        "",
        "Leakage decision:",
        "",
        "- SEC acceptedDateTime is a valid official source-time field for SEC filings.",
        "- Federal Register publication dates are official public dates, but not project historical receipt.",
        "- Nasdaq directories downloaded here are current snapshots, not historical PIT membership snapshots.",
        "- No external official file proves when the custom 10x7 theme universe was knowable to this project.",
        "- Therefore no replay or selection promotion was executed.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We stopped pretending local files solve the problem.",
        "",
        "We downloaded official outside sources. SEC and Federal Register give real historical publication or acceptance dates. That helps.",
        "",
        "But the custom 10x7 universe is still not PIT-proven. Current exchange listings and SEC identity maps do not prove that this project could have chosen those 70 stocks as those 10 themes back in 2021.",
        "",
        "So the honest result is: official source acquisition improved the evidence base, but the backtest is still not allowed.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1141_external_source_catalog.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1142_sec_ticker_cik_map.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1143_sec_submission_download_panel.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1144_current_exchange_directory_panel.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1145_federal_register_policy_archive_panel.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1146_macro_vintage_download_panel.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1147_pit_universe_resolution_matrix.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1148_historical_receipt_resolution_matrix.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1149_replay_readiness_after_external_acquisition.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1150_external_source_acquisition_closeout.csv`",
        "- `data/artifacts/task_1141_1150_external_source_acquisition/task1150_external_source_acquisition_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    decision_csv = REPORT_DIR / "task_1141_1150_decision.csv"
    write_csv(decision_csv, [decision])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    universe_rows = read_csv(UNIVERSE)

    source_rows = source_catalog_downloads()
    sec_map_rows = sec_ticker_map(universe_rows)
    sec_submission_rows = sec_submission_downloads(sec_map_rows)
    exchange_rows = current_exchange_directory(universe_rows)
    fr_rows = federal_register_downloads()
    macro_rows = macro_vintage_downloads()
    pit_rows = pit_resolution_matrix(universe_rows, sec_map_rows, exchange_rows)
    receipt_rows = receipt_resolution_matrix(sec_submission_rows, fr_rows, macro_rows)
    readiness_rows = replay_readiness(pit_rows, receipt_rows, fr_rows, macro_rows, sec_submission_rows)
    decision = closeout(readiness_rows)

    write_csv(OUT_DIR / "task1141_external_source_catalog.csv", source_rows)
    write_csv(OUT_DIR / "task1142_sec_ticker_cik_map.csv", sec_map_rows)
    write_csv(OUT_DIR / "task1143_sec_submission_download_panel.csv", sec_submission_rows)
    write_csv(OUT_DIR / "task1144_current_exchange_directory_panel.csv", exchange_rows)
    write_csv(OUT_DIR / "task1145_federal_register_policy_archive_panel.csv", fr_rows)
    write_csv(OUT_DIR / "task1146_macro_vintage_download_panel.csv", macro_rows)
    write_csv(OUT_DIR / "task1147_pit_universe_resolution_matrix.csv", pit_rows)
    write_csv(OUT_DIR / "task1148_historical_receipt_resolution_matrix.csv", receipt_rows)
    write_csv(OUT_DIR / "task1149_replay_readiness_after_external_acquisition.csv", readiness_rows)
    write_csv(OUT_DIR / "task1150_external_source_acquisition_closeout.csv", [decision])
    write_json(OUT_DIR / "task1150_external_source_acquisition_closeout.json", decision)
    write_report(decision)

    print(
        "[TRADER_BRAIN_1141_1150_EXTERNAL_SOURCE_ACQUISITION_OK] "
        f"verdict={decision['verdict']} "
        f"pit_pass={decision['pit_membership_pass_rows']}/{decision['pit_rows']} "
        f"sec_accepted={decision['sec_accepted_datetime_rows_2021_2026q1']} "
        f"fr_docs={decision['federal_register_official_doc_count']} "
        f"alfred_files={decision['alfred_vintage_files_downloaded']} "
        "replay=0"
    )


if __name__ == "__main__":
    main()
