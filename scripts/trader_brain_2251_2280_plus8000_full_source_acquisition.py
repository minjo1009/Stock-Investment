from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2251_2280_plus8000_full_source_acquisition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
RAW_OUT = ROOT / "data/raw" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2251_2280_plus8000_full_source_acquisition.md"
DECISION = REPORT_DIR / "task_2251_2280_decision.csv"

TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK2121 = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
TASK2231 = ROOT / "data/artifacts/task_2231_2250_plus8000_data_parity"

AUTHORITY = "PLUS8000_FULL_SOURCE_ACQUISITION_RAW_AND_FEATURE_PARITY_ONLY"
USER_AGENT = "codex-plus8000-full-source-acquisition/1.0 contact=local"
FROM_DATE = "2021-01-01"
TO_DATE = "2026-03-31"
FMP_ENDPOINTS = {
    "earnings": ("https://financialmodelingprep.com/stable/earnings", {"period": "quarter", "limit": "40"}),
    "income_statement": ("https://financialmodelingprep.com/stable/income-statement", {"period": "quarter", "limit": "40"}),
    "balance_sheet": ("https://financialmodelingprep.com/stable/balance-sheet-statement", {"period": "quarter", "limit": "40"}),
    "cash_flow": ("https://financialmodelingprep.com/stable/cash-flow-statement", {"period": "quarter", "limit": "40"}),
    "grades_historical": ("https://financialmodelingprep.com/stable/grades-historical", {}),
}
FINNHUB_ENDPOINTS = {
    "stock_filings": ("https://finnhub.io/api/v1/stock/filings", {"from": FROM_DATE, "to": TO_DATE}),
    "stock_recommendation": ("https://finnhub.io/api/v1/stock/recommendation", {}),
}
ALPHA_ENDPOINT = ("https://www.alphavantage.co/query", {"function": "EARNINGS"})
SLEEP = {"finnhub": 1.05, "fmp": 0.25, "alpha_vantage": 12.2, "sec": 0.12}


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


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def params_hash(params: dict[str, object]) -> str:
    clean = {k: v for k, v in sorted(params.items()) if k not in {"token", "apikey"}}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            text = text + "T00:00:00+00:00"
        if " " in text and "T" not in text:
            text = text.replace(" ", "T", 1)
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None", "nan"}:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def response_shape(payload: object) -> tuple[str, str]:
    if isinstance(payload, list):
        keys = list(payload[0].keys())[:12] if payload and isinstance(payload[0], dict) else []
        return f"list:{len(payload)}", "|".join(keys)
    if isinstance(payload, dict):
        for key in ["Information", "Note", "Error Message", "error", "message"]:
            if key in payload:
                return "dict:message", str(payload.get(key, ""))[:180]
        sizes = []
        for key, value in payload.items():
            if isinstance(value, list):
                sizes.append(f"{key}:{len(value)}")
            elif isinstance(value, dict):
                sizes.append(f"{key}:dict")
        return "dict", "|".join(sizes[:10])
    return type(payload).__name__, str(payload)[:180]


def provider_status(http_status: str, call_status: str, note: str) -> tuple[str, str]:
    lowered = note.lower()
    if http_status == "200" and call_status in {"downloaded", "reused"}:
        if "premium" in lowered or "not available under your current subscription" in lowered:
            return "entitlement_blocked", "1"
        if "rate limit" in lowered or "limit reach" in lowered or "thank you for using alpha vantage" in lowered:
            return "quota_or_rate_blocked", "1"
        return "usable", "0"
    if http_status in {"402", "403"} or "premium" in lowered or "subscription" in lowered or "legacy endpoint" in lowered:
        return "entitlement_blocked", "1"
    if http_status == "429" or "rate limit" in lowered or "limit reach" in lowered:
        return "quota_or_rate_blocked", "1"
    if call_status.startswith("skipped"):
        return call_status, "1"
    return call_status or "unknown", "0"


def request_json(provider: str, endpoint_name: str, url: str, params: dict[str, object], symbol: str, raw_root: Path) -> dict[str, object]:
    out_path = raw_root / provider / endpoint_name / symbol / f"{params_hash(params)}.json"
    meta_path = out_path.with_suffix(out_path.suffix + ".meta.json")
    capture_ts = datetime.now(timezone.utc).isoformat()
    if out_path.exists() and out_path.stat().st_size > 0:
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                return {
                    "call_status": "reused" if meta.get("normalized_call_status") == "usable" else "reused_blocked",
                    "http_status": str(meta.get("http_status", "")),
                    "raw_path": str(out_path.relative_to(ROOT)),
                    "raw_sha256": file_sha256(out_path),
                    "response_shape": str(meta.get("response_shape", "")),
                    "response_note": str(meta.get("response_note", "")),
                    "capture_ts_utc": capture_ts,
                }
            except Exception:
                pass
        raw_text = out_path.read_text(encoding="utf-8", errors="ignore")
        try:
            payload = json.loads(raw_text)
            shape, note = response_shape(payload)
        except Exception:
            return {
                "call_status": "reused_unparsed",
                "http_status": "0",
                "raw_path": str(out_path.relative_to(ROOT)),
                "raw_sha256": file_sha256(out_path),
                "response_shape": "raw_reused_unparsed",
                "response_note": raw_text[:180],
                "capture_ts_utc": capture_ts,
            }
        http_status = "200"
        status, _ = provider_status(http_status, "reused", note)
        if status == "quota_or_rate_blocked":
            http_status = "429"
        elif status == "entitlement_blocked":
            http_status = "403"
        meta_path.write_text(
            json.dumps(
                {
                    "http_status": http_status,
                    "call_status": "reused",
                    "normalized_call_status": status,
                    "response_shape": shape,
                    "response_note": note,
                    "capture_ts_utc": capture_ts,
                },
                indent=2,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        return {
            "call_status": "reused" if status == "usable" else "reused_blocked",
            "http_status": http_status,
            "raw_path": str(out_path.relative_to(ROOT)),
            "raw_sha256": file_sha256(out_path),
            "response_shape": shape,
            "response_note": note,
            "capture_ts_utc": capture_ts,
        }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(url, params=params, timeout=35, headers={"User-Agent": USER_AGENT})
        clean_text = response.text
        for secret_key in ("token", "apikey"):
            secret = str(params.get(secret_key, "") or "")
            if secret:
                clean_text = clean_text.replace(secret, "[REDACTED_API_KEY]")
        content = clean_text.encode("utf-8")
        out_path.write_bytes(content)
        try:
            payload = json.loads(clean_text)
            shape, note = response_shape(payload)
        except Exception:
            shape, note = "text", clean_text[:180]
        status, _ = provider_status(str(response.status_code), "downloaded" if response.ok else "http_error", note)
        meta_path.write_text(
            json.dumps(
                {
                    "http_status": str(response.status_code),
                    "call_status": "downloaded" if response.ok else "http_error",
                    "normalized_call_status": status,
                    "response_shape": shape,
                    "response_note": note,
                    "capture_ts_utc": capture_ts,
                },
                indent=2,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        time.sleep(SLEEP.get(provider, 0.2))
        return {
            "call_status": "downloaded" if response.ok else "http_error",
            "http_status": str(response.status_code),
            "raw_path": str(out_path.relative_to(ROOT)),
            "raw_sha256": sha256_bytes(content),
            "response_shape": shape,
            "response_note": note,
            "capture_ts_utc": capture_ts,
        }
    except Exception as exc:  # noqa: BLE001
        time.sleep(SLEEP.get(provider, 0.2))
        return {
            "call_status": "failed",
            "http_status": "0",
            "raw_path": "",
            "raw_sha256": "",
            "response_shape": "error",
            "response_note": str(exc)[:180],
            "capture_ts_utc": capture_ts,
        }


def read_json_raw(path_text: str) -> object:
    path = ROOT / path_text
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def existing_normalized() -> list[dict[str, str]]:
    path = TASK2121 / "task2123_api_normalized_sources.csv"
    return read_csv(path) if path.exists() else []


def existing_symbol_endpoints() -> set[tuple[str, str]]:
    return {(row["symbol"], row["endpoint_name"]) for row in existing_normalized() if row.get("symbol") and row.get("endpoint_name")}


def build_plan(symbols: list[str], env: dict[str, str], existing: set[tuple[str, str]]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    finnhub_key = env.get("FINNHUB_API_KEY", "")
    fmp_key = env.get("FMP_API_KEY", "")
    alpha_key = env.get("ALPHA_VANTAGE_API_KEY", "")
    for symbol in symbols:
        if finnhub_key:
            for endpoint, (url, base_params) in FINNHUB_ENDPOINTS.items():
                if (symbol, endpoint) in existing:
                    continue
                params = {**base_params, "symbol": symbol, "token": finnhub_key}
                plan.append({"provider": "finnhub", "endpoint_name": endpoint, "symbol": symbol, "url": url, "params": params, "fallback_family": ""})
        if fmp_key:
            for endpoint, (url, base_params) in FMP_ENDPOINTS.items():
                if (symbol, endpoint) in existing:
                    continue
                params = {**base_params, "symbol": symbol, "apikey": fmp_key}
                plan.append({"provider": "fmp", "endpoint_name": endpoint, "symbol": symbol, "url": url, "params": params, "fallback_family": "sec_companyfacts" if endpoint in {"income_statement", "balance_sheet", "cash_flow"} else ""})
        if alpha_key and (symbol, "earnings_history") not in existing:
            url, base_params = ALPHA_ENDPOINT
            params = {**base_params, "symbol": symbol, "apikey": alpha_key}
            plan.append({"provider": "alpha_vantage", "endpoint_name": "earnings_history", "symbol": symbol, "url": url, "params": params, "fallback_family": ""})
    return plan


def load_full_pool() -> tuple[list[dict[str, str]], dict[str, str]]:
    pool = read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv")
    specs = read_csv(TASK1201 / "task1203_l5_trade_specs.csv")
    cik_by_symbol: dict[str, str] = {}
    for row in specs:
        symbol = row.get("symbol", "")
        cik = re.sub(r"\D", "", row.get("cik", ""))
        if symbol and cik and symbol not in cik_by_symbol:
            cik_by_symbol[symbol] = cik.zfill(10)
    return pool, cik_by_symbol


def execute_plan(plan: list[dict[str, object]]) -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    for idx, item in enumerate(plan, start=1):
        provider = str(item["provider"])
        endpoint_name = str(item["endpoint_name"])
        symbol = str(item["symbol"])
        result = request_json(provider, endpoint_name, str(item["url"]), dict(item["params"]), symbol, RAW_OUT)
        http_status = str(result.get("http_status", ""))
        call_status = str(result.get("call_status", ""))
        note = str(result.get("response_note", ""))
        status, blocked = provider_status(http_status, call_status, note)
        sanitized = {k: v for k, v in dict(item["params"]).items() if k not in {"token", "apikey"}}
        ledger.append(
            {
                "task_id": "Task2252",
                "api_call_id": f"FULLAPI2252-{idx:07d}",
                "provider": provider,
                "endpoint_name": endpoint_name,
                "symbol": symbol,
                "params_json_without_key": json.dumps(sanitized, sort_keys=True),
                "http_status": http_status,
                "call_status": call_status,
                "normalized_call_status": status,
                "blocked_by_plan_or_entitlement": blocked,
                "fallback_family": item.get("fallback_family", ""),
                "raw_path": result.get("raw_path", ""),
                "raw_sha256": result.get("raw_sha256", ""),
                "capture_ts_utc": result.get("capture_ts_utc", ""),
                "response_shape": result.get("response_shape", ""),
                "response_note": note,
                "request_url_contains_secret": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return ledger


def sec_companyfacts_plan(symbols: list[str], cik_by_symbol: dict[str, str], need_financial_fallback: set[str]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for symbol in symbols:
        cik = cik_by_symbol.get(symbol, "")
        if not cik or symbol not in need_financial_fallback:
            continue
        plan.append(
            {
                "provider": "sec",
                "endpoint_name": "companyfacts",
                "symbol": symbol,
                "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                "params": {},
                "fallback_family": "official_financial_statement_fallback",
            }
        )
    return plan


def execute_sec_plan(plan: list[dict[str, object]], start_idx: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, item in enumerate(plan, start=0):
        provider = "sec"
        endpoint = "companyfacts"
        symbol = str(item["symbol"])
        result = request_json(provider, endpoint, str(item["url"]), {}, symbol, RAW_OUT)
        http_status = str(result.get("http_status", ""))
        call_status = str(result.get("call_status", ""))
        note = str(result.get("response_note", ""))
        status, blocked = provider_status(http_status, call_status, note)
        rows.append(
            {
                "task_id": "Task2252",
                "api_call_id": f"FULLAPI2252-{start_idx + offset:07d}",
                "provider": provider,
                "endpoint_name": endpoint,
                "symbol": symbol,
                "params_json_without_key": "{}",
                "http_status": http_status,
                "call_status": call_status,
                "normalized_call_status": status,
                "blocked_by_plan_or_entitlement": blocked,
                "fallback_family": item.get("fallback_family", ""),
                "raw_path": result.get("raw_path", ""),
                "raw_sha256": result.get("raw_sha256", ""),
                "capture_ts_utc": result.get("capture_ts_utc", ""),
                "response_shape": result.get("response_shape", ""),
                "response_note": note,
                "request_url_contains_secret": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def normalize_rows(ledger: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    row_id = 1
    for row in ledger:
        if row.get("normalized_call_status") != "usable" or not row.get("raw_path"):
            continue
        payload = read_json_raw(str(row["raw_path"]))
        provider = str(row["provider"])
        endpoint = str(row["endpoint_name"])
        symbol = str(row["symbol"])
        records: list[dict[str, object]]
        if provider == "sec" and endpoint == "companyfacts":
            records = []
            facts = payload.get("facts", {}).get("us-gaap", {}) if isinstance(payload, dict) else {}
            for tag, tag_payload in facts.items():
                units = tag_payload.get("units", {}) if isinstance(tag_payload, dict) else {}
                for unit, entries in units.items():
                    if unit not in {"USD", "shares", "pure"} or not isinstance(entries, list):
                        continue
                    for rec in entries:
                        if isinstance(rec, dict):
                            records.append({"tag": tag, "unit": unit, **rec})
        elif isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            if endpoint == "earnings_history":
                records = payload.get("quarterlyEarnings", []) if isinstance(payload.get("quarterlyEarnings"), list) else []
            else:
                records = [payload]
        else:
            records = []
        for rec in records:
            if not isinstance(rec, dict):
                continue
            source_ts = rec.get("acceptedDate") or rec.get("filedDate") or rec.get("filingDate") or rec.get("reportedDate") or rec.get("date") or rec.get("period") or rec.get("filed") or rec.get("end") or ""
            normalized.append(
                {
                    "task_id": "Task2253",
                    "api_normalized_source_id": f"FULLNORM2253-{row_id:08d}",
                    "api_call_id": row["api_call_id"],
                    "provider": provider,
                    "endpoint_name": endpoint,
                    "symbol": symbol,
                    "source_ts": source_ts,
                    "raw_path": row["raw_path"],
                    "raw_sha256": row["raw_sha256"],
                    "record_json": json.dumps(rec, sort_keys=True, ensure_ascii=False),
                    "record_json_truncated": "0",
                    "provider_available_ts_basis": "provider_record_timestamp_or_capture_only",
                    "strict_gate_pass": "0",
                    "proxy_feature_allowed": "1",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            row_id += 1
    return normalized


def parse_record(row: dict[str, str]) -> dict[str, object]:
    try:
        return json.loads(row.get("record_json", "") or "{}")
    except json.JSONDecodeError:
        return {}


def build_index(rows: list[dict[str, str] | dict[str, object]]) -> dict[str, dict[str, list[dict[str, object]]]]:
    index: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        symbol = str(row.get("symbol", ""))
        endpoint = str(row.get("endpoint_name", ""))
        if not symbol or not endpoint:
            continue
        rec = parse_record({k: str(v) for k, v in row.items()})
        packed = {**{k: str(v) for k, v in row.items()}, **rec}
        index[symbol][endpoint].append(packed)
    return index


def latest_before(records: list[dict[str, object]], decision: datetime | None, date_keys: list[str]) -> dict[str, object] | None:
    if decision is None:
        return None
    best: tuple[datetime, dict[str, object]] | None = None
    for rec in records:
        ts = None
        for key in date_keys:
            ts = parse_dt(rec.get(key))
            if ts:
                break
        if ts and ts <= decision and (best is None or ts > best[0]):
            best = (ts, rec)
    return best[1] if best else None


def count_filings(records: list[dict[str, object]], decision: datetime | None) -> tuple[int, int, int]:
    if decision is None:
        return 0, 0, 0
    start = decision - timedelta(days=365)
    total = eightk = tenx = 0
    for rec in records:
        ts = parse_dt(rec.get("acceptedDate") or rec.get("filedDate") or rec.get("source_ts"))
        if not ts or not (start <= ts <= decision):
            continue
        total += 1
        form = str(rec.get("form", ""))
        if form.startswith("8-K"):
            eightk += 1
        if form in {"10-Q", "10-K"}:
            tenx += 1
    return total, eightk, tenx


def sec_latest_fact(records: list[dict[str, object]], tags: set[str], decision: datetime | None) -> float:
    candidates = [rec for rec in records if str(rec.get("tag", "")) in tags]
    rec = latest_before(candidates, decision, ["filed", "end", "source_ts"])
    return to_float((rec or {}).get("val"), 0.0)


def recompute_features(pool: list[dict[str, str]], combined_norm: list[dict[str, object]]) -> list[dict[str, object]]:
    index = build_index(combined_norm)
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(pool, start=1):
        symbol = row["symbol"]
        decision = parse_dt(row["decision_asof_ts"])
        endpoints = index.get(symbol, {})
        filing_total, filing_8k, filing_10x = count_filings(endpoints.get("stock_filings", []), decision)
        earnings = latest_before(endpoints.get("earnings", []) + endpoints.get("earnings_history", []), decision, ["date", "reportedDate", "source_ts"])
        income = latest_before(endpoints.get("income_statement", []), decision, ["acceptedDate", "filingDate", "date", "source_ts"])
        balance = latest_before(endpoints.get("balance_sheet", []), decision, ["acceptedDate", "filingDate", "date", "source_ts"])
        cash_flow = latest_before(endpoints.get("cash_flow", []), decision, ["acceptedDate", "filingDate", "date", "source_ts"])
        grades = latest_before(endpoints.get("grades_historical", []) + endpoints.get("stock_recommendation", []), decision, ["date", "period", "source_ts"])
        sec_records = endpoints.get("companyfacts", [])
        surprise_pct = to_float((earnings or {}).get("surprisePercentage"), 0.0)
        revenue = to_float((income or {}).get("revenue"), 0.0)
        net_income = to_float((income or {}).get("netIncome"), 0.0)
        cash = to_float((balance or {}).get("cashAndCashEquivalents"), 0.0)
        debt = to_float((balance or {}).get("totalDebt"), 0.0)
        fcf = to_float((cash_flow or {}).get("freeCashFlow"), 0.0)
        financial_source = "fmp_financials"
        if revenue == 0.0 and sec_records:
            financial_source = "sec_companyfacts_fallback"
            revenue = sec_latest_fact(sec_records, {"Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"}, decision)
            net_income = sec_latest_fact(sec_records, {"NetIncomeLoss"}, decision)
            cash = sec_latest_fact(sec_records, {"CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"}, decision)
            debt_current = sec_latest_fact(sec_records, {"DebtCurrent", "LongTermDebtCurrent"}, decision)
            debt_long = sec_latest_fact(sec_records, {"LongTermDebtNoncurrent", "LongTermDebtAndFinanceLeaseObligationsNoncurrent"}, decision)
            debt = debt_current + debt_long
            cfo = sec_latest_fact(sec_records, {"NetCashProvidedByUsedInOperatingActivities"}, decision)
            capex = sec_latest_fact(sec_records, {"PaymentsToAcquirePropertyPlantAndEquipment"}, decision)
            fcf = cfo - capex if cfo or capex else 0.0
        strong_buy = to_float((grades or {}).get("analystRatingsStrongBuy") or (grades or {}).get("strongBuy"), 0.0)
        buy = to_float((grades or {}).get("analystRatingsBuy") or (grades or {}).get("buy"), 0.0)
        hold = to_float((grades or {}).get("analystRatingsHold") or (grades or {}).get("hold"), 0.0)
        sell = to_float((grades or {}).get("analystRatingsSell") or (grades or {}).get("sell"), 0.0)
        strong_sell = to_float((grades or {}).get("analystRatingsStrongSell") or (grades or {}).get("strongSell"), 0.0)
        rating_total = strong_buy + buy + hold + sell + strong_sell
        rating_score = ((strong_buy * 2 + buy - sell - strong_sell * 2) / rating_total * 10.0) if rating_total > 0 else 0.0
        quality_score = 0.0
        if revenue > 0:
            quality_score += clamp(net_income / revenue, -0.2, 0.3) * 40
            quality_score += clamp(fcf / revenue, -0.2, 0.3) * 45
        if cash > 0 or debt > 0:
            quality_score += clamp((cash - debt) / max(cash + debt, 1.0), -1, 1) * 8
        filing_score = min(filing_total, 10) * 0.7 + min(filing_8k, 5) * 0.9 + min(filing_10x, 4) * 1.2
        surprise_score = clamp(surprise_pct, -30, 30) * 0.35
        api_proxy_score = round(filing_score + surprise_score + quality_score + rating_score, 4)
        if api_proxy_score >= 18:
            state = "api_proxy_supportive"
        elif api_proxy_score <= -8:
            state = "api_proxy_risk_or_weak_quality"
        elif filing_total == 0 and not earnings and revenue == 0:
            state = "api_proxy_source_gap_neutral"
        else:
            state = "api_proxy_mixed_or_light"
        rows.append(
            {
                "task_id": "Task2256",
                "api_feature_id": f"FULLFEAT2256-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "filing_total_365d": filing_total,
                "filing_8k_365d": filing_8k,
                "filing_10x_365d": filing_10x,
                "latest_earnings_surprise_pct": round(surprise_pct, 4),
                "latest_revenue": revenue,
                "latest_net_income": net_income,
                "latest_free_cash_flow": fcf,
                "latest_cash": cash,
                "latest_debt": debt,
                "rating_score": round(rating_score, 4),
                "api_proxy_score": api_proxy_score,
                "api_proxy_state": state,
                "financial_source": financial_source if revenue or net_income or cash or debt or fcf else "financial_source_gap",
                "strict_transcript_gate_pass": "0",
                "strict_analyst_revision_gate_pass": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def coverage_summary(pool: list[dict[str, str]], ledger: list[dict[str, object]], normalized: list[dict[str, object]], features: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    by_endpoint = Counter((str(row["provider"]), str(row["endpoint_name"]), str(row["normalized_call_status"])) for row in ledger)
    idx = 1
    for (provider, endpoint, status), count in sorted(by_endpoint.items()):
        rows.append(
            {
                "task_id": "Task2257",
                "coverage_row_id": f"FULLCOVER2257-{idx:04d}",
                "provider": provider,
                "endpoint_name": endpoint,
                "status": status,
                "row_count": count,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    feature_metrics = [
        ("nonzero_filing_total", sum(1 for row in features if int(row["filing_total_365d"]) > 0)),
        ("nonzero_earnings_surprise", sum(1 for row in features if to_float(row["latest_earnings_surprise_pct"]) != 0.0)),
        ("nonzero_financials", sum(1 for row in features if row["financial_source"] != "financial_source_gap")),
        ("nonzero_rating_score", sum(1 for row in features if to_float(row["rating_score"]) != 0.0)),
        ("api_proxy_not_source_gap", sum(1 for row in features if row["api_proxy_state"] != "api_proxy_source_gap_neutral")),
    ]
    for metric, covered in feature_metrics:
        rows.append(
            {
                "task_id": "Task2257",
                "coverage_row_id": f"FULLCOVER2257-{idx:04d}",
                "provider": "combined",
                "endpoint_name": metric,
                "status": "feature_coverage",
                "row_count": covered,
                "candidate_rows": len(pool),
                "coverage_ratio": round(covered / len(pool), 6) if pool else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    retry: list[dict[str, object]] = []
    for row in ledger:
        if row["normalized_call_status"] == "usable":
            continue
        retry.append(
            {
                "task_id": "Task2258",
                "retry_queue_id": f"FULLRETRY2258-{len(retry)+1:05d}",
                "provider": row["provider"],
                "endpoint_name": row["endpoint_name"],
                "symbol": row["symbol"],
                "normalized_call_status": row["normalized_call_status"],
                "blocker": str(row["response_note"])[:180],
                "fallback_family": row.get("fallback_family", ""),
                "authority": AUTHORITY,
            }
        )
    return rows, retry


def closeout_rows(pool: list[dict[str, str]], ledger: list[dict[str, object]], normalized: list[dict[str, object]], features: list[dict[str, object]], retry: list[dict[str, object]]) -> list[dict[str, object]]:
    usable_calls = sum(1 for row in ledger if row["normalized_call_status"] == "usable")
    non_gap_features = sum(1 for row in features if row["api_proxy_state"] != "api_proxy_source_gap_neutral")
    financial_rows = sum(1 for row in features if row["financial_source"] != "financial_source_gap")
    return [
        {
            "task_id": "Task2280",
            "verdict": "plus8000_full_source_acquisition_completed_with_provider_blocks",
            "candidate_rows": len(pool),
            "api_call_rows": len(ledger),
            "usable_call_rows": usable_calls,
            "blocked_or_retry_rows": len(retry),
            "normalized_source_rows": len(normalized),
            "feature_rows": len(features),
            "non_gap_feature_rows": non_gap_features,
            "non_gap_feature_ratio": round(non_gap_features / len(features), 6) if features else 0.0,
            "financial_rows_after_sec_fallback": financial_rows,
            "financial_coverage_ratio": round(financial_rows / len(features), 6) if features else 0.0,
            "replay_allowed": "0",
            "next_action": "rerun parity audit then request explicit replay authorization",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], coverage: list[dict[str, object]], retry: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    coverage_lines = "\n".join(
        f"- `{row['provider']}` / `{row['endpoint_name']}` / `{row['status']}`: {row['row_count']}."
        for row in coverage[:40]
    )
    retry_counts = Counter((str(row["provider"]), str(row["endpoint_name"]), str(row["normalized_call_status"])) for row in retry)
    retry_lines = "\n".join(f"- `{provider}` / `{endpoint}` / `{status}`: {count}." for (provider, endpoint, status), count in sorted(retry_counts.items()))
    text = f"""# Task2251-2280 Plus8000 Full Source Acquisition

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Candidate rows: {closeout['candidate_rows']}.
- API call rows: {closeout['api_call_rows']}.
- Usable call rows: {closeout['usable_call_rows']}.
- Blocked or retry rows: {closeout['blocked_or_retry_rows']}.
- Normalized source rows: {closeout['normalized_source_rows']}.
- Feature rows: {closeout['feature_rows']}.
- Non-gap feature rows: {closeout['non_gap_feature_rows']}.
- Financial rows after SEC fallback: {closeout['financial_rows_after_sec_fallback']}.
- Replay allowed: `{closeout['replay_allowed']}`.

## Quant Expert Report

The task attempts full source acquisition for the +8000 data standard across the 3,100-candidate pool. FMP financial endpoints are still attempted, but SEC companyfacts is used as an official fallback for financial statement fields when FMP is blocked.

Coverage:

{coverage_lines}

Retry or blocked queue:

{retry_lines}

## No-Background Decision-Maker Report

Conclusion first: the acquisition pass actually downloads/reuses raw sources and computes a full 3,100-row feature panel. Replay remains blocked until the new parity audit is rerun and explicitly authorized.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2251_2280_plus8000_full_source_acquisition/`.
- Raw sources: `data/raw/task_2251_2280_plus8000_full_source_acquisition/`.
- Validator: `python scripts/trader_brain_2251_2280_plus8000_full_source_acquisition_validate.py`.

Sources consulted for endpoint fallback: FMP official developer docs for stable and legacy endpoint families; SEC companyfacts official endpoint is used as a free official fallback for financial statements.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2251, 2281):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"Plus8000 Full Source Acquisition Step {task_no}",
                "workstream": "Research Governance / Data Management",
                "status": "active",
                "validation_tier": "data-health",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "plus8000-full-source-acquisition-before-replay",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2251 else "Task2250",
                "report_path": "docs/reports/task_2251_2280_plus8000_full_source_acquisition/task_2251_2280_plus8000_full_source_acquisition.md",
                "decision_path": "docs/reports/task_2251_2280_plus8000_full_source_acquisition/task_2251_2280_decision.csv",
                "artifact_path": "data/artifacts/task_2251_2280_plus8000_full_source_acquisition",
                "validation_command": "python scripts/trader_brain_2251_2280_plus8000_full_source_acquisition_validate.py",
                "notes": "Downloads or reuses +8000 data-standard raw sources across the 3100 full candidate pool and builds a full feature panel with SEC companyfacts fallback.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "112. Task2251-Task2280"
    if marker in text:
        return
    line = (
        f"112. Task2251-Task2280 executed +8000 full-source acquisition across the 3,100-candidate pool: "
        f"{closeout['usable_call_rows']}/{closeout['api_call_rows']} usable calls, {closeout['normalized_source_rows']} "
        f"normalized rows, {closeout['feature_rows']} feature rows, non-gap feature ratio "
        f"{closeout['non_gap_feature_ratio']}, financial coverage after SEC fallback "
        f"{closeout['financial_coverage_ratio']}; replay remains `{closeout['replay_allowed']}` until parity is rerun "
        f"and explicitly authorized. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n\n\nTask851-859 data certification status:")
    if insert_at == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    env = load_env()
    pool, cik_by_symbol = load_full_pool()
    symbols = sorted({row["symbol"] for row in pool})
    existing = existing_symbol_endpoints()
    plan = build_plan(symbols, env, existing)
    write_csv(OUT_DIR / "task2251_acquisition_plan.csv", [
        {
            "task_id": "Task2251",
            "plan_row_id": f"FULLPLAN2251-{idx:06d}",
            "provider": row["provider"],
            "endpoint_name": row["endpoint_name"],
            "symbol": row["symbol"],
            "fallback_family": row.get("fallback_family", ""),
            "authority": AUTHORITY,
        }
        for idx, row in enumerate(plan, start=1)
    ])
    ledger = execute_plan(plan)
    failed_financial_symbols = {
        str(row["symbol"])
        for row in ledger
        if row["provider"] == "fmp"
        and row["endpoint_name"] in {"income_statement", "balance_sheet", "cash_flow"}
        and row["normalized_call_status"] != "usable"
    }
    sec_plan = sec_companyfacts_plan(symbols, cik_by_symbol, failed_financial_symbols)
    sec_ledger = execute_sec_plan(sec_plan, len(ledger) + 1)
    ledger.extend(sec_ledger)
    normalized_new = normalize_rows(ledger)
    normalized_existing = existing_normalized()
    combined_norm: list[dict[str, object]] = [dict(row) for row in normalized_existing] + normalized_new
    features = recompute_features(pool, combined_norm)
    coverage, retry = coverage_summary(pool, ledger, normalized_new, features)
    closeout = closeout_rows(pool, ledger, normalized_new, features, retry)
    write_csv(OUT_DIR / "task2252_api_call_ledger.csv", ledger)
    write_csv(OUT_DIR / "task2253_normalized_sources.csv", normalized_new)
    write_csv(OUT_DIR / "task2254_combined_source_index_summary.csv", [
        {
            "task_id": "Task2254",
            "summary_id": "FULLINDEX2254-001",
            "existing_normalized_rows": len(normalized_existing),
            "new_normalized_rows": len(normalized_new),
            "combined_normalized_rows": len(combined_norm),
            "unique_symbols": len({str(row.get("symbol", "")) for row in combined_norm if row.get("symbol")}),
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2255_post_acquisition_coverage_summary.csv", coverage)
    write_csv(OUT_DIR / "task2256_recomputed_plus8000_feature_panel.csv", features)
    write_csv(OUT_DIR / "task2257_retry_or_blocked_queue.csv", retry)
    write_csv(OUT_DIR / "task2280_closeout.csv", closeout)
    write_json(OUT_DIR / "task2280_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], coverage, retry)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2251_2280_PLUS8000_FULL_SOURCE_ACQUISITION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
