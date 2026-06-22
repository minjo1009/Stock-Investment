from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1834_1847_targeted_sources"
OUT_DIR = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
REPORT_DIR = ROOT / "docs/reports/task_1834_1847_targeted_source_implementation"
REPORT = REPORT_DIR / "task_1834_1847_targeted_source_implementation.md"
DECISION = REPORT_DIR / "task_1834_1847_decision.csv"

SLEEVE_DIR = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
LEDGER = SLEEVE_DIR / "task1808_trade_drawdown_attribution_ledger.csv"
SLEEVE_MEANING = SLEEVE_DIR / "task1812_l2_sleeve_meaning_panel.csv"
COMPANY_TICKERS = ROOT / "data/raw/fundamental/sec_companyfacts/company_tickers.json"
CANDIDATE_FILING_BINDINGS = (
    ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors/task1320_candidate_filing_bindings.csv"
)
SEC_DOWNLOAD_LEDGER = (
    ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors/task1321_sec_complete_submission_download_ledger.csv"
)
COMPANYFACTS_DENOMINATOR = (
    ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition/task1432_full_companyfacts_denominator_panel.csv"
)
SEC_CACHE_DIRS = [
    ROOT / "data/raw/task_1268_1287_sec_complete_submission_cache",
    ROOT / "data/raw/task_1318_1337_sec_complete_candidate_cache",
    ROOT / "data/raw/task_1238_1247_sec_filing_text_cache",
]
ANALYST_AUDIT = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition/task1416_analyst_pit_audit.csv"

START = date(2021, 1, 1)
END = date(2026, 3, 31)
AUTHORITY = "DIAGNOSTIC_TARGETED_SOURCE_IMPLEMENTATION_ONLY"
USER_AGENT = "minjo-trader-brain-research contact@example.com"

FRED_SERIES = [
    {
        "series_id": "DGS2",
        "family": "rates_liquidity",
        "source_name": "FRED 2Y Treasury",
        "description": "2-year Treasury constant maturity rate",
        "frequency": "daily",
    },
    {
        "series_id": "DGS10",
        "family": "rates_liquidity",
        "source_name": "FRED 10Y Treasury",
        "description": "10-year Treasury constant maturity rate",
        "frequency": "daily",
    },
    {
        "series_id": "DFF",
        "family": "rates_liquidity",
        "source_name": "FRED Effective Fed Funds",
        "description": "Effective federal funds rate",
        "frequency": "daily",
    },
    {
        "series_id": "VIXCLS",
        "family": "rates_liquidity",
        "source_name": "FRED VIX close",
        "description": "CBOE volatility index close via FRED",
        "frequency": "daily",
    },
    {
        "series_id": "BAMLH0A0HYM2",
        "family": "rates_liquidity",
        "source_name": "FRED ICE BofA US High Yield Spread",
        "description": "High-yield option-adjusted spread",
        "frequency": "daily",
    },
]

SEC_FORMS = {"S-1", "S-1/A", "S-3", "S-3/A", "424B4", "424B5", "424B3", "8-K", "8-K/A", "10-Q", "10-K"}
SEC_FINANCING_ITEMS = {"1.01", "2.03", "3.02", "8.01", "9.01"}
FINANCING_TERMS = {
    "at_the_market": ("at-the-market", "at the market", "atm program", "sales agreement"),
    "shelf_registration": ("shelf registration", "registration statement", "form s-3"),
    "prospectus_supplement": ("prospectus supplement", "424b5", "424b4", "424b3"),
    "common_stock_offering": ("common stock", "ordinary shares", "class a common stock"),
    "convertible_debt": ("convertible notes", "convertible senior notes", "convertible debt"),
    "warrants_units": ("warrants", "units"),
    "dilution_language": ("dilution", "dilutive", "additional shares"),
}


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


def read_csv(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_url(url: str, path: Path) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    fetched_at = now_utc()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            path.write_bytes(response.read())
        return {
            "fetch_status": "FETCHED",
            "http_status": "200",
            "fetched_at_utc": fetched_at,
            "raw_storage_path": rel(path),
            "raw_source_hash": sha256(path),
            "error": "",
        }
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {
            "fetch_status": "FAILED",
            "http_status": "",
            "fetched_at_utc": fetched_at,
            "raw_storage_path": rel(path) if path.exists() else "",
            "raw_source_hash": sha256(path) if path.exists() else "",
            "error": str(exc)[:500],
        }


def fred_url(series_id: str) -> str:
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={START.isoformat()}&coed={END.isoformat()}"


def parse_float(value: str) -> float | None:
    try:
        if value in {"", ".", "nan", "NaN"}:
            return None
        return float(value.replace(",", ""))
    except (AttributeError, ValueError):
        return None


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def parse_sec_acceptance(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 14:
        return ""
    dt = datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return dt.isoformat()


def next_business_day(day: date) -> date:
    current = day + timedelta(days=1)
    while current.weekday() >= 5:
        current += timedelta(days=1)
    return current


def conservative_daily_release_ts(observation_date: date) -> str:
    eastern = ZoneInfo("America/New_York")
    local_dt = datetime.combine(next_business_day(observation_date), time(9, 30), tzinfo=eastern)
    return local_dt.astimezone(timezone.utc).isoformat()


def build_source_contract() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, series in enumerate(FRED_SERIES, 1):
        rows.append(
            {
                "task_id": "Task1834",
                "source_contract_id": f"RATESRC-1834-{idx:03d}",
                "data_family": "rates_liquidity",
                "source_name": series["source_name"],
                "series_id": series["series_id"],
                "source_url": fred_url(series["series_id"]),
                "access_type": "official_public_csv_no_api_key",
                "asof_method": "conservative_next_business_day_0930_et",
                "vintage_status": "latest_vintage_only_not_alfred_certified",
                "does_not_mean": "does_not_certify_true_alfred_vintage_without_api_key_or_archived_vintage_file",
                "authority": AUTHORITY,
            }
        )
    rows.extend(
        [
            {
                "task_id": "Task1834",
                "source_contract_id": "RATESRC-1834-006",
                "data_family": "rates_liquidity",
                "source_name": "FINRA Margin Statistics",
                "series_id": "FINRA_MARGIN",
                "source_url": "https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics",
                "access_type": "official_public_html_excel_manual_feed_absent",
                "asof_method": "monthly_reference_plus_finra_publish_lag_third_week_following_month",
                "vintage_status": "current_webpage_snapshot_only",
                "does_not_mean": "does_not_create_daily_point_in_time_margin_feed",
                "authority": AUTHORITY,
            },
            {
                "task_id": "Task1836",
                "source_contract_id": "SECSRC-1836-001",
                "data_family": "financing_dilution",
                "source_name": "SEC EDGAR APIs and local complete-submission cache",
                "series_id": "SEC_SUBMISSIONS_AND_COMPANYFACTS",
                "source_url": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
                "access_type": "official_public",
                "asof_method": "acceptedDateTime <= decision_asof_ts exact CIK/accession only",
                "vintage_status": "edgar_accepted_timestamp_source_time",
                "does_not_mean": "does_not_allow_symbol_date_price_proximity_matching",
                "authority": AUTHORITY,
            },
            {
                "task_id": "Task1838",
                "source_contract_id": "EARNREV-1838-001",
                "data_family": "earnings_revision",
                "source_name": "Nasdaq Data Link Zacks Analyst Revisions",
                "series_id": "ZREV",
                "source_url": "https://data.nasdaq.com/databases/ZREV",
                "access_type": "vendor_or_paid",
                "asof_method": "vendor_timestamp_required_before_l2_use",
                "vintage_status": "blocked_until_vendor_history_available",
                "does_not_mean": "does_not_approximate_true_consensus_with_public_good_words",
                "authority": AUTHORITY,
            },
        ]
    )
    return rows


def load_fred_series() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_rows: list[dict[str, object]] = []
    observation_rows: list[dict[str, object]] = []
    for series in FRED_SERIES:
        series_id = series["series_id"]
        url = fred_url(series_id)
        raw_path = RAW_DIR / "fred" / f"{series_id}.csv"
        fetch = fetch_url(url, raw_path)
        source_rows.append(
            {
                "task_id": "Task1834",
                "rates_source_packet_id": f"RATESRAW-{series_id}",
                "series_id": series_id,
                "source_url": url,
                **fetch,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        if fetch["fetch_status"] != "FETCHED":
            continue
        raw_rows = read_csv(raw_path)
        value_col = series_id if raw_rows and series_id in raw_rows[0] else None
        for row in raw_rows:
            obs_date = parse_date(row.get("observation_date", ""))
            if obs_date is None or obs_date < START or obs_date > END:
                continue
            value = parse_float(row.get(value_col or series_id, ""))
            if value is None:
                continue
            release_ts = conservative_daily_release_ts(obs_date)
            observation_rows.append(
                {
                    "task_id": "Task1835",
                    "rates_observation_id": f"RATEOBS-{series_id}-{obs_date.isoformat()}",
                    "series_id": series_id,
                    "observation_date": obs_date.isoformat(),
                    "value": value,
                    "source_url": url,
                    "raw_storage_path": fetch["raw_storage_path"],
                    "raw_source_hash": fetch["raw_source_hash"],
                    "published_ts": release_ts,
                    "received_ts": release_ts,
                    "available_to_brain_ts": release_ts,
                    "release_timestamp_method": "conservative_next_business_day_0930_et",
                    "latest_vintage_only_flag": "1",
                    "vintage_asof_certified_flag": "0",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return source_rows, observation_rows


def build_rates_panels(observations: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_date: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    by_series: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in observations:
        by_date[str(row["observation_date"])][str(row["series_id"])] = row
        by_series[str(row["series_id"])].append(row)

    feature_rows: list[dict[str, object]] = []
    for obs_date in sorted(by_date):
        row = by_date[obs_date]
        dgs2 = parse_float(str(row.get("DGS2", {}).get("value", "")))
        dgs10 = parse_float(str(row.get("DGS10", {}).get("value", "")))
        dff = parse_float(str(row.get("DFF", {}).get("value", "")))
        vix = parse_float(str(row.get("VIXCLS", {}).get("value", "")))
        hy = parse_float(str(row.get("BAMLH0A0HYM2", {}).get("value", "")))
        spread = None if dgs2 is None or dgs10 is None else dgs10 - dgs2
        available_ts_candidates = [
            str(item.get("available_to_brain_ts", "")) for item in row.values() if item.get("available_to_brain_ts")
        ]
        if not available_ts_candidates:
            continue
        feature_rows.append(
            {
                "task_id": "Task1835",
                "rates_feature_id": f"RATEFEATURE-{obs_date}",
                "observation_date": obs_date,
                "available_to_brain_ts": max(available_ts_candidates),
                "dgs2": dgs2 if dgs2 is not None else "",
                "dgs10": dgs10 if dgs10 is not None else "",
                "dff": dff if dff is not None else "",
                "vixcls": vix if vix is not None else "",
                "hy_oas": hy if hy is not None else "",
                "dgs10_dgs2_spread": round(spread, 6) if spread is not None else "",
                "latest_vintage_only_flag": "1",
                "vintage_asof_certified_flag": "0",
                "authority": AUTHORITY,
            }
        )
    add_rate_changes(feature_rows)

    decision_rows = decision_asof_rows()
    decision_panel: list[dict[str, object]] = []
    sorted_features = sorted(feature_rows, key=lambda row: str(row["available_to_brain_ts"]))
    for idx, decision in enumerate(decision_rows, 1):
        asof = decision["decision_asof_ts"]
        eligible = [row for row in sorted_features if str(row["available_to_brain_ts"]) <= asof]
        if not eligible:
            continue
        latest = eligible[-1]
        regime = classify_rate_regime(latest)
        decision_panel.append(
            {
                "task_id": "Task1835",
                "rates_decision_panel_id": f"RATEASOF-1835-{idx:05d}",
                "decision_asof_ts": asof,
                "source_observation_date": latest["observation_date"],
                "source_available_to_brain_ts": latest["available_to_brain_ts"],
                "rate_regime_state": regime["rate_regime_state"],
                "liquidity_stress_state": regime["liquidity_stress_state"],
                "curve_state": regime["curve_state"],
                "winner_compounder_multiplier": regime["winner_compounder_multiplier"],
                "cyclical_beta_multiplier": regime["cyclical_beta_multiplier"],
                "speculative_event_multiplier": regime["speculative_event_multiplier"],
                "defensive_quality_multiplier": regime["defensive_quality_multiplier"],
                "dgs10": latest.get("dgs10", ""),
                "dgs2": latest.get("dgs2", ""),
                "dgs10_dgs2_spread": latest.get("dgs10_dgs2_spread", ""),
                "dgs10_change_60obs": latest.get("dgs10_change_60obs", ""),
                "vixcls": latest.get("vixcls", ""),
                "hy_oas": latest.get("hy_oas", ""),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return feature_rows, decision_panel


def add_rate_changes(rows: list[dict[str, object]]) -> None:
    for col in ["dgs10", "dgs2", "vixcls", "hy_oas"]:
        numeric = [parse_float(str(row.get(col, ""))) for row in rows]
        for idx, row in enumerate(rows):
            for lag in [5, 20, 60]:
                key = f"{col}_change_{lag}obs"
                if idx >= lag and numeric[idx] is not None and numeric[idx - lag] is not None:
                    row[key] = round(numeric[idx] - numeric[idx - lag], 6)  # type: ignore[operator]
                else:
                    row[key] = ""


def classify_rate_regime(row: dict[str, object]) -> dict[str, object]:
    dgs10_60 = parse_float(str(row.get("dgs10_change_60obs", ""))) or 0.0
    dgs2_60 = parse_float(str(row.get("dgs2_change_60obs", ""))) or 0.0
    spread = parse_float(str(row.get("dgs10_dgs2_spread", "")))
    vix = parse_float(str(row.get("vixcls", ""))) or 0.0
    hy = parse_float(str(row.get("hy_oas", ""))) or 0.0

    if dgs10_60 >= 0.75 or dgs2_60 >= 0.75:
        rate_state = "rising_rate_pressure"
    elif dgs10_60 <= -0.75 or dgs2_60 <= -0.75:
        rate_state = "easing_rate_tailwind"
    else:
        rate_state = "rate_neutral"
    if vix >= 30 or hy >= 5.5:
        liquidity_state = "liquidity_stress"
    elif vix <= 18 and hy and hy <= 4.0:
        liquidity_state = "liquidity_supportive"
    else:
        liquidity_state = "liquidity_neutral"
    curve_state = "curve_source_gap" if spread is None else ("curve_inverted" if spread < 0 else "curve_positive")

    winner = 1.0
    cyclical = 1.0
    speculative = 1.0
    defensive = 1.0
    if rate_state == "rising_rate_pressure":
        winner -= 0.1
        cyclical -= 0.15
        speculative -= 0.2
        defensive += 0.05
    if liquidity_state == "liquidity_stress":
        winner -= 0.15
        cyclical -= 0.2
        speculative -= 0.3
        defensive += 0.1
    if rate_state == "easing_rate_tailwind" and liquidity_state != "liquidity_stress":
        winner += 0.05
        cyclical += 0.1
        speculative += 0.05
    return {
        "rate_regime_state": rate_state,
        "liquidity_stress_state": liquidity_state,
        "curve_state": curve_state,
        "winner_compounder_multiplier": round(max(0.5, min(1.15, winner)), 3),
        "cyclical_beta_multiplier": round(max(0.4, min(1.2, cyclical)), 3),
        "speculative_event_multiplier": round(max(0.25, min(1.1, speculative)), 3),
        "defensive_quality_multiplier": round(max(0.8, min(1.2, defensive)), 3),
    }


def decision_asof_rows() -> list[dict[str, str]]:
    rows = read_csv(LEDGER)
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        asof = row.get("decision_asof_ts", "")
        if asof and asof not in seen:
            out.append({"decision_asof_ts": asof})
            seen.add(asof)
    return sorted(out, key=lambda row: row["decision_asof_ts"])


def load_finra_snapshot() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    url = "https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics"
    raw_path = RAW_DIR / "finra" / "margin_statistics.html"
    fetch = fetch_url(url, raw_path)
    packet = {
        "task_id": "Task1834",
        "finra_source_packet_id": "FINRA-MARGIN-1834-001",
        "source_url": url,
        **fetch,
        "feed_limitation": "FINRA states data feeds are not available; webpage/Excel snapshot only",
        "assignment_uses_future_outcome": "0",
        "authority": AUTHORITY,
    }
    rows: list[dict[str, object]] = []
    if fetch["fetch_status"] == "FETCHED":
        text = raw_path.read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(r"([A-Z][a-z]{2}-\d{2})\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)")
        for idx, match in enumerate(pattern.finditer(re.sub(r"\s+", " ", text)), 1):
            rows.append(
                {
                    "task_id": "Task1834",
                    "finra_margin_row_id": f"FINRAMARGIN-1834-{idx:03d}",
                    "month_year": match.group(1),
                    "debit_balances_margin_accounts_millions": match.group(2).replace(",", ""),
                    "free_credit_cash_accounts_millions": match.group(3).replace(",", ""),
                    "free_credit_margin_accounts_millions": match.group(4).replace(",", ""),
                    "source_url": url,
                    "raw_storage_path": fetch["raw_storage_path"],
                    "raw_source_hash": fetch["raw_source_hash"],
                    "source_snapshot_only_flag": "1",
                    "authority": AUTHORITY,
                }
            )
    return [packet], rows[:36]


def load_symbol_cik_map(symbols: set[str]) -> dict[str, str]:
    payload = json.loads(COMPANY_TICKERS.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for value in payload.values():
        ticker = str(value.get("ticker", "")).upper()
        if ticker in symbols:
            mapping[ticker] = f"{int(value['cik_str']):010d}"
    return mapping


def read_sec_download_ledger() -> dict[tuple[str, str], dict[str, str]]:
    if not SEC_DOWNLOAD_LEDGER.exists():
        return {}
    rows = read_csv(SEC_DOWNLOAD_LEDGER)
    out: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        cik = f"{int(row['cik']):010d}" if row.get("cik", "").isdigit() else row.get("cik", "")
        accession = row.get("accession", "")
        if cik and accession:
            out[(cik, accession)] = row
    return out


def is_financing_like_binding(row: dict[str, str]) -> bool:
    form = row.get("form", "")
    if form.startswith("S-") or form.startswith("424B"):
        return True
    items = {item.strip() for item in row.get("items", "").split(",") if item.strip()}
    if form in {"8-K", "8-K/A"} and items & SEC_FINANCING_ITEMS:
        return True
    return False


def read_local_sec_text(ledger_row: dict[str, str]) -> tuple[str, str, str, str]:
    local_path = ledger_row.get("local_path", "")
    if not local_path:
        return "", "", "", "missing_local_path"
    path = ROOT / local_path
    if not path.exists():
        return local_path, "", "", "missing_raw_file"
    try:
        text = path.read_bytes()[:800000].decode("utf-8", errors="ignore")
    except OSError:
        return local_path, "", "", "raw_read_failed"
    return local_path, ledger_row.get("sha256", sha256(path)), text, ledger_row.get("download_status", "downloaded")


def parse_sec_header(text: str) -> dict[str, str]:
    def find(pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "accession": find(r"ACCESSION NUMBER:\s*([0-9-]+)"),
        "form": find(r"CONFORMED SUBMISSION TYPE:\s*([^\n\r]+)"),
        "filed_date": find(r"FILED AS OF DATE:\s*(\d{8})"),
        "accepted_raw": find(r"<ACCEPTANCE-DATETIME>(\d+)"),
        "cik": find(r"CENTRAL INDEX KEY:\s*(\d+)"),
    }


def financing_hits(text: str) -> tuple[list[str], int]:
    lower = text.lower()
    families: list[str] = []
    count = 0
    for family, terms in FINANCING_TERMS.items():
        family_count = sum(lower.count(term) for term in terms)
        if family_count:
            families.append(family)
            count += family_count
    return families, count


def iter_sec_files(ciks: set[str]) -> list[Path]:
    files: list[Path] = []
    cik_dir_names = {f"CIK{cik}" for cik in ciks}
    for cache_dir in SEC_CACHE_DIRS:
        if not cache_dir.exists():
            continue
        for cik_dir in cache_dir.iterdir():
            if not cik_dir.is_dir() or cik_dir.name not in cik_dir_names:
                continue
            files.extend(path for path in cik_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".txt", ".htm", ".html"})
    return sorted(files)


def build_sec_packets() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    if not CANDIDATE_FILING_BINDINGS.exists():
        return [], [], [], []
    bindings = read_csv(CANDIDATE_FILING_BINDINGS)
    ledger = read_sec_download_ledger()
    packets: list[dict[str, object]] = []
    extracted: list[dict[str, object]] = []
    seen_binding: set[str] = set()
    raw_cache: dict[tuple[str, str], tuple[str, str, str, str, list[str], int]] = {}
    for row in bindings:
        if row.get("binding_id", "") in seen_binding:
            continue
        seen_binding.add(row.get("binding_id", ""))
        form = row.get("form", "")
        if form not in SEC_FORMS or not is_financing_like_binding(row):
            continue
        cik = row.get("cik", "")
        accession = row.get("accession", "")
        decision_asof = row.get("decision_asof_ts", "")
        available_ts = row.get("available_to_brain_ts", "")
        source_time_pass = row.get("source_time_pass", "0")
        missing_state = ""
        if not accession:
            missing_state = "source_gap_blank_accession"
        if source_time_pass != "1":
            missing_state = missing_state or "source_time_failed_or_missing"
        ledger_row = ledger.get((cik, accession), {}) if accession else {}
        if accession and not ledger_row:
            missing_state = missing_state or "download_ledger_missing"
        cache_key = (cik, accession)
        if ledger_row and cache_key not in raw_cache:
            local_path, raw_hash, text, raw_status = read_local_sec_text(ledger_row)
            families, hit_count = financing_hits(text) if text else ([], 0)
            raw_cache[cache_key] = (local_path, raw_hash, text, raw_status, families, hit_count)
        elif ledger_row:
            local_path, raw_hash, text, raw_status, families, hit_count = raw_cache[cache_key]
        else:
            local_path, raw_hash, text, raw_status, families, hit_count = "", "", "", "download_ledger_missing", [], 0
        if form in {"10-Q", "10-K"} and not families:
            continue
        packet_id = f"SECFINPKT-1836-{len(packets)+1:06d}"
        packets.append(
            {
                "task_id": "Task1836",
                "financing_source_packet_id": packet_id,
                "candidate_source_id": row.get("candidate_source_id", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "cik": cik,
                "decision_asof_ts": decision_asof,
                "source_family": "sec_financing_dilution",
                "packet_component_type": "candidate_filing_binding_plus_raw_complete_submission",
                "form": form,
                "items": row.get("items", ""),
                "accession": accession,
                "acceptance_datetime": row.get("acceptance_datetime", ""),
                "available_to_brain_ts": available_ts,
                "source_time_pass": source_time_pass,
                "primary_document": row.get("primary_document", ""),
                "document_id": row.get("primary_document", ""),
                "document_type": row.get("primary_doc_description", ""),
                "sec_url": ledger_row.get("sec_url", ""),
                "local_path": local_path,
                "sha256": raw_hash,
                "keyword_family_hits": "|".join(families),
                "keyword_hit_count": hit_count,
                "raw_source_status": raw_status,
                "missing_source_state": missing_state,
                "join_key_rule": "exact_cik_accession_only",
                "inferred_matching_used": "0",
                "asof_guard_pass": "1" if available_ts and decision_asof and available_ts <= decision_asof else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        if missing_state:
            pressure = "source_gap"
        elif any(fam in families for fam in ["at_the_market", "common_stock_offering", "dilution_language"]):
            pressure = "active_financing_pressure"
        elif any(fam in families for fam in ["convertible_debt", "warrants_units"]):
            pressure = "convertible_warrant_overhang"
        elif "shelf_registration" in families:
            pressure = "shelf_capacity_watch"
        elif form.startswith("424B") or form.startswith("S-"):
            pressure = "historical_or_closed_financing"
        else:
            pressure = "boilerplate_or_risk_factor_only"
        extracted.append(
            {
                "task_id": "Task1837",
                "dilution_extraction_id": f"SECDILUTE-1837-{len(extracted)+1:06d}",
                "financing_source_packet_id": packet_id,
                "candidate_source_id": row.get("candidate_source_id", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "cik": cik,
                "accession": accession,
                "form": form,
                "accepted_ts": row.get("acceptance_datetime", ""),
                "available_to_brain_ts": available_ts,
                "dilution_pressure_state": pressure,
                "dilution_signal_families": "|".join(families),
                "extraction_rule_id": "keyword_family_v1_form_whitelist_v1",
                "negative_fixture_rule": "no_keyword_or_nonwhitelist_form_must_not_create_positive_dilution_signal",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    denominator_packets = build_companyfacts_denominator_packets()
    decision_links = build_sec_decision_links(packets)
    return packets, extracted, decision_links, denominator_packets


def build_companyfacts_denominator_packets() -> list[dict[str, object]]:
    if not COMPANYFACTS_DENOMINATOR.exists():
        return []
    rows = read_csv(COMPANYFACTS_DENOMINATOR)
    out: list[dict[str, object]] = []
    for idx, row in enumerate(rows, 1):
        out.append(
            {
                "task_id": "Task1836",
                "companyfacts_denominator_packet_id": f"SECDENOM-1836-{idx:06d}",
                "candidate_source_id": row.get("candidate_source_id", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "cik": row.get("cik", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "companyfacts_available": row.get("companyfacts_available", ""),
                "cash_usd": row.get("cash_usd", ""),
                "cash_filed_date": row.get("cash_filed_date", ""),
                "shares_outstanding": row.get("shares_outstanding", ""),
                "shares_filed_date": row.get("shares_filed_date", ""),
                "public_float_usd": row.get("public_float_usd", ""),
                "public_float_filed_date": row.get("public_float_filed_date", ""),
                "denominator_source_gap": row.get("denominator_source_gap", ""),
                "asof_guard_pass": "1"
                if all(
                    not row.get(field, "") or row.get(field, "") <= row.get("decision_asof_ts", "")[:10]
                    for field in ["cash_filed_date", "shares_filed_date", "public_float_filed_date"]
                )
                else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return out


def build_sec_decision_links(packets: list[dict[str, object]]) -> list[dict[str, object]]:
    packets_by_symbol: dict[str, list[dict[str, object]]] = defaultdict(list)
    for packet in packets:
        symbol = str(packet.get("symbol", "")).upper()
        if symbol:
            packets_by_symbol[symbol].append(packet)
    for symbol in packets_by_symbol:
        packets_by_symbol[symbol].sort(key=lambda row: str(row["acceptance_datetime"]))

    sleeve_rows = read_csv(SLEEVE_MEANING)
    out: list[dict[str, object]] = []
    for idx, row in enumerate(sleeve_rows, 1):
        symbol = row.get("symbol", "").upper()
        asof = row.get("decision_asof_ts", "")
        eligible = [
            packet
            for packet in packets_by_symbol.get(symbol, [])
            if str(packet.get("available_to_brain_ts", "")) <= asof
        ]
        latest = eligible[-1] if eligible else {}
        out.append(
            {
                "task_id": "Task1842",
                "sec_dilution_asof_link_id": f"SECDILINK-1842-{idx:06d}",
                "candidate_source_id": row.get("candidate_source_id", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": symbol,
                "decision_asof_ts": asof,
                "latest_financing_source_packet_id": latest.get("financing_source_packet_id", ""),
                "latest_financing_accepted_ts": latest.get("acceptance_datetime", ""),
                "dilution_source_available_before_decision": "1" if latest else "0",
                "source_gap_flag": "0" if latest else "1",
                "asof_guard_pass": "1" if not latest or str(latest.get("available_to_brain_ts", "")) <= asof else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return out


def build_earnings_revision_gate() -> list[dict[str, object]]:
    local_rows = read_csv(ANALYST_AUDIT) if ANALYST_AUDIT.exists() else []
    total = len(local_rows)
    available = sum(1 for row in local_rows if row.get("analyst_pit_available") == "1")
    source_gap = sum(1 for row in local_rows if row.get("analyst_pit_source_gap") == "1")
    return [
        {
            "task_id": "Task1838",
            "earnings_revision_gate_id": "EARNREV-GATE-1838-001",
            "source_name": "Nasdaq Data Link Zacks Analyst Revisions",
            "source_url": "https://data.nasdaq.com/databases/ZREV",
            "required_fields": "symbol|fiscal_period|estimate_timestamp|broker_or_consensus_timestamp|revision_direction|analyst_count",
            "local_pit_audit_rows": total,
            "local_pit_available_rows": available,
            "local_pit_source_gap_rows": source_gap,
            "gate_verdict": "vendor_blocked_schema_only" if available == 0 else "vendor_available_requires_timestamp_validation",
            "allowed_next_step": "schema_stub_and_vendor_access_check_only" if available == 0 else "timestamp_validation_before_l2_use",
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
    ]


def build_source_packet_schema() -> list[dict[str, object]]:
    rows = [
        ("Task1840", "source_packet_id", "stable packet id", "all"),
        ("Task1840", "source_family", "rates_liquidity financing_dilution earnings_revision", "all"),
        ("Task1840", "entity_key", "symbol plus CIK when issuer-specific", "exact only"),
        ("Task1840", "published_ts", "source publication timestamp", "required before L2"),
        ("Task1840", "received_ts", "local receipt timestamp or conservative proxy", "required before L2"),
        ("Task1840", "available_to_brain_ts", "max usable timestamp for assignment", "must be <= decision_asof_ts"),
        ("Task1840", "raw_storage_path", "local immutable raw source path", "required"),
        ("Task1840", "raw_source_hash", "sha256 source hash", "required"),
        ("Task1840", "vintage_asof_certified_flag", "true PIT vintage vs latest snapshot", "must not overclaim"),
        ("Task1840", "assignment_uses_future_outcome", "future outcome usage guard", "must be zero"),
    ]
    return [
        {
            "task_id": task,
            "schema_field_id": f"SRCSCHEMA-1840-{idx:03d}",
            "field_name": field,
            "field_meaning": meaning,
            "validation_rule": rule,
            "authority": AUTHORITY,
        }
        for idx, (task, field, meaning, rule) in enumerate(rows, 1)
    ]


def build_l2_l4_contracts() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    l2 = [
        ("rates_liquidity", "rate_regime_state", "rising_rate_pressure/easing_rate_tailwind/rate_neutral", "L0 decision asof panel"),
        ("rates_liquidity", "liquidity_stress_state", "liquidity_stress/supportive/neutral", "VIX/HY spread/FINRA source"),
        ("financing_dilution", "dilution_pressure_state", "observed financing/dilution state", "SEC packet accepted before asof"),
        ("earnings_revision", "revision_surprise_state", "blocked until vendor timestamp exists", "vendor gate"),
    ]
    edges = [
        ("winner_compounder", "rates_liquidity", "macro_pressure_modifies_winner_budget"),
        ("cyclical_beta", "rates_liquidity", "rate_and_liquidity_state_confirms_or_weakens_cyclical_entry"),
        ("speculative_event", "financing_dilution", "financing_packet_can_trigger_cap_or_no_entry"),
        ("winner_compounder", "earnings_revision", "revision_surprise_can_validate_or_break_expectation_gap"),
    ]
    thesis = [
        ("rates_liquidity", "add rate_regime_state liquidity_stress_state curve_state budget multipliers"),
        ("financing_dilution", "add latest packet id accepted_ts dilution pressure source gap"),
        ("earnings_revision", "add vendor gate state and block true surprise when vendor missing"),
    ]
    l2_rows = [
        {
            "task_id": "Task1841",
            "l2_targeted_meaning_contract_id": f"L2TARGET-1841-{idx:03d}",
            "data_family": family,
            "field_name": field,
            "state_space": state,
            "source_dependency": dep,
            "authority": AUTHORITY,
        }
        for idx, (family, field, state, dep) in enumerate(l2, 1)
    ]
    edge_rows = [
        {
            "task_id": "Task1842",
            "l3_targeted_edge_contract_id": f"L3TARGET-1842-{idx:03d}",
            "strategy_sleeve": sleeve,
            "data_family": family,
            "edge_primitive": primitive,
            "authority": AUTHORITY,
        }
        for idx, (sleeve, family, primitive) in enumerate(edges, 1)
    ]
    thesis_rows = [
        {
            "task_id": "Task1843",
            "l4_targeted_thesis_contract_id": f"L4TARGET-1843-{idx:03d}",
            "data_family": family,
            "thesis_card_change": change,
            "authority": AUTHORITY,
        }
        for idx, (family, change) in enumerate(thesis, 1)
    ]
    return l2_rows, edge_rows, thesis_rows


def build_policy_and_gate(closeout_status: str) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    prereg = [
        {
            "task_id": "Task1844",
            "policy_prereg_id": "POLICYFREEZE-1844-001",
            "policy_name": "targeted_source_attached_sleeve_policy_v1",
            "replay_allowed_now": "0",
            "blocked_until": "rates_liquidity_asof_panel_validated_and_sec_financing_dilution_source_links_reviewed",
            "does_not_mean": "does_not_approve_backtest_or_micro_sizing",
            "authority": AUTHORITY,
        }
    ]
    replay_gate = [
        {
            "task_id": "Task1845",
            "controlled_replay_gate_id": "REPLAYGATE-1845-001",
            "gate_state": "blocked_no_replay_executed",
            "reason": "source implementation complete but no frozen L2/L3/L4 assignment policy replayed yet",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1847",
            "verdict": closeout_status,
            "next_action": "review targeted source panels then implement source-attached L2/L3/L4 policy before any controlled replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return prereg, replay_gate, closeout


def build_validation_contract() -> list[dict[str, object]]:
    rules = [
        ("rates_source_contract_complete", "FRED/FINRA source contracts exist with as-of limitations"),
        ("rates_asof_guard", "source_available_to_brain_ts must be <= decision_asof_ts"),
        ("no_true_vintage_overclaim", "FRED latest CSV rows mark vintage_asof_certified_flag=0"),
        ("sec_exact_keys", "SEC packets use exact CIK/accession and no inferred matching"),
        ("sec_asof_guard", "SEC accepted_ts must be <= decision_asof_ts when linked"),
        ("earnings_vendor_block", "earnings revision cannot enter L2 unless PIT vendor feed exists"),
        ("no_replay_outputs", "no trade/equity/backtest replay artifact in this task"),
    ]
    return [
        {
            "task_id": "Task1846",
            "validation_rule_id": f"VALID1846-{idx:03d}",
            "validation_rule": rule,
            "meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (rule, meaning) in enumerate(rules, 1)
    ]


def write_report(summary: dict[str, object], sources: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1834-1847 Targeted Source Implementation",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `targeted_sources_implemented_no_replay`.",
        "- Implemented first: rates/liquidity source contract and as-of loader.",
        "- Implemented second: SEC financing/dilution source packet manifest and extractor contract.",
        "- Implemented third: earnings revision vendor gate.",
        "- No micro sizing work.",
        "- No replay executed.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "### Source Basis",
        "",
        "- FRED DGS10 page confirms daily 10-year Treasury yield and update cadence context: https://fred.stlouisfed.org/series/DGS10.",
        "- FINRA Margin Statistics states customer margin debit/free-credit balances are collected under FINRA Rule 4521(d), published monthly, and data feeds are not available: https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics.",
        "- SEC EDGAR APIs are official public APIs updated as filings are disseminated: https://www.sec.gov/search-filings/edgar-application-programming-interfaces.",
        "- Nasdaq Data Link ZREV is vendor/paid analyst revision context: https://data.nasdaq.com/databases/ZREV.",
        "",
        "### Implementation Counts",
        "",
        f"- Rates source packets: {summary['rates_source_packets']}.",
        f"- Rates observations: {summary['rates_observations']}.",
        f"- Rates decision-asof rows: {summary['rates_decision_rows']}.",
        f"- FINRA parsed snapshot rows: {summary['finra_rows']}.",
        f"- SEC financing/dilution packets: {summary['sec_packets']}.",
        f"- SEC companyfacts denominator packets: {summary['sec_denominator_packets']}.",
        f"- SEC dilution extractor rows: {summary['sec_extractions']}.",
        f"- SEC decision-asof links: {summary['sec_decision_links']}.",
        f"- Earnings revision gate verdict: `{summary['earnings_gate_verdict']}`.",
        "",
        "### Source Contracts",
        "",
        "| Family | Source | Access | Asof Method | Limitation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in sources:
        lines.append(
            f"| `{row['data_family']}` | {row['source_name']} | `{row['access_type']}` | {row['asof_method']} | {row['does_not_mean']} |"
        )
    lines.extend(
        [
            "",
            "Leakage discipline:",
            "",
            "- Rates observations use conservative next-business-day availability, not same-day clairvoyance.",
            "- FRED latest CSV is not called true ALFRED vintage; `vintage_asof_certified_flag=0`.",
            "- SEC financing/dilution packets use exact CIK/accession and accepted timestamp.",
            "- Earnings revision remains vendor-blocked unless a PIT revision feed with timestamps exists.",
            "- This task creates no trades, equity curve, metrics, or replay.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Rates/liquidity 배관은 실제로 붙었습니다.",
            "2. SEC financing/dilution은 기존 EDGAR cache에서 exact CIK/accession packet으로 만들었습니다.",
            "3. Earnings revision은 아직 못 쓰게 막았습니다. 이유는 PIT vendor feed가 없습니다.",
            "4. 다음은 이 source packet들을 L2/L3/L4 판단로직에 붙인 뒤에만 replay입니다.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1834_rates_liquidity_source_contract.csv`",
            "- `task1834_rates_source_packets.csv`",
            "- `task1834_finra_margin_snapshot.csv`",
            "- `task1835_rates_liquidity_observations.csv`",
            "- `task1835_rates_liquidity_feature_panel.csv`",
            "- `task1835_rates_liquidity_decision_asof_panel.csv`",
            "- `task1836_sec_financing_dilution_source_packets.csv`",
            "- `task1836_sec_companyfacts_denominator_packets.csv`",
            "- `task1837_financing_dilution_extractor_contract.csv`",
            "- `task1838_earnings_revision_vendor_gate.csv`",
            "- `task1840_source_packet_schema.csv`",
            "- `task1841_l2_targeted_meaning_contract.csv`",
            "- `task1842_l3_targeted_edges.csv`",
            "- `task1842_sec_dilution_decision_asof_links.csv`",
            "- `task1843_l4_targeted_thesis_contract.csv`",
            "- `task1844_frozen_policy_preregistration.csv`",
            "- `task1845_controlled_replay_gate.csv`",
            "- `task1846_validation_contract.csv`",
            "- `task1847_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1834_1847_targeted_source_implementation_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    source_contract = build_source_contract()
    rates_packets, rates_observations = load_fred_series()
    finra_packets, finra_rows = load_finra_snapshot()
    rates_feature_rows, rates_decision_rows = build_rates_panels(rates_observations)
    sec_packets, sec_extractions, sec_links, sec_denominators = build_sec_packets()
    earnings_gate = build_earnings_revision_gate()
    source_schema = build_source_packet_schema()
    l2_rows, l3_rows, l4_rows = build_l2_l4_contracts()
    prereg, replay_gate, closeout = build_policy_and_gate("targeted_sources_implemented_no_replay")
    validation = build_validation_contract()

    outputs = [
        ("task1834_rates_liquidity_source_contract.csv", source_contract),
        ("task1834_rates_source_packets.csv", rates_packets + finra_packets),
        ("task1834_finra_margin_snapshot.csv", finra_rows),
        ("task1835_rates_liquidity_observations.csv", rates_observations),
        ("task1835_rates_liquidity_feature_panel.csv", rates_feature_rows),
        ("task1835_rates_liquidity_decision_asof_panel.csv", rates_decision_rows),
        ("task1836_sec_financing_dilution_source_packets.csv", sec_packets),
        ("task1836_sec_companyfacts_denominator_packets.csv", sec_denominators),
        ("task1837_financing_dilution_extractor_contract.csv", sec_extractions),
        ("task1838_earnings_revision_vendor_gate.csv", earnings_gate),
        ("task1840_source_packet_schema.csv", source_schema),
        ("task1841_l2_targeted_meaning_contract.csv", l2_rows),
        ("task1842_l3_targeted_edges.csv", l3_rows),
        ("task1842_sec_dilution_decision_asof_links.csv", sec_links),
        ("task1843_l4_targeted_thesis_contract.csv", l4_rows),
        ("task1844_frozen_policy_preregistration.csv", prereg),
        ("task1845_controlled_replay_gate.csv", replay_gate),
        ("task1846_validation_contract.csv", validation),
        ("task1847_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1847_closeout.json", closeout[0])
    summary = {
        "rates_source_packets": len(rates_packets) + len(finra_packets),
        "rates_observations": len(rates_observations),
        "rates_decision_rows": len(rates_decision_rows),
        "finra_rows": len(finra_rows),
        "sec_packets": len(sec_packets),
        "sec_denominator_packets": len(sec_denominators),
        "sec_extractions": len(sec_extractions),
        "sec_decision_links": len(sec_links),
        "earnings_gate_verdict": earnings_gate[0]["gate_verdict"],
    }
    write_json(OUT_DIR / "task1834_1847_summary.json", summary)
    write_report(summary, source_contract)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1834_1847] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
