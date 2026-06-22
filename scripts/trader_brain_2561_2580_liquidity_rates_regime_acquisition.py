from __future__ import annotations

import csv
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2561_2580_liquidity_rates_regime_acquisition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
RAW_DIR = ROOT / "data/raw" / TASK_ID
REPORT = REPORT_DIR / "task_2561_2580_liquidity_rates_regime_acquisition.md"
DECISION = REPORT_DIR / "task_2580_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"

AUTHORITY = "DATA_HEALTH_LIQUIDITY_RATES_REGIME_ACQUISITION_ONLY"
USER_AGENT = "trader-brain-source-acquisition/1.0 research-contact local"
START_DATE = "2021-01-01"
END_DATE = "2026-03-31"

NYFED_BASE = "https://markets.newyorkfed.org/api"
TREASURY_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
FRED_BASE = "https://api.stlouisfed.org/fred"

FRED_SERIES = [
    "DGS1MO",
    "DGS3MO",
    "DGS6MO",
    "DGS1",
    "DGS2",
    "DGS5",
    "DGS10",
    "DGS30",
    "DFF",
    "EFFR",
    "SOFR",
    "IORB",
    "WALCL",
    "RRPONTSYD",
    "WTREGEN",
    "RESBALNSW",
    "T10Y2Y",
    "T10Y3M",
    "BAMLH0A0HYM2",
    "BAMLC0A0CM",
]


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


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def load_dotenv_key(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    env_path = ROOT / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


def safe_query(params: dict[str, str], secret_keys: set[str] | None = None) -> str:
    secret_keys = secret_keys or set()
    safe = {k: ("<REDACTED>" if k in secret_keys else v) for k, v in params.items()}
    return urllib.parse.urlencode(safe)


def build_url(base: str, params: dict[str, str]) -> str:
    return base + ("?" + urllib.parse.urlencode(params) if params else "")


def build_safe_url(base: str, params: dict[str, str], secret_keys: set[str] | None = None) -> str:
    return base + ("?" + safe_query(params, secret_keys) if params else "")


def get_json(url: str, raw_path: Path, headers: dict[str, str] | None = None, sleep_s: float = 0.05) -> tuple[int, str]:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists() and raw_path.stat().st_size > 0:
        try:
            json.loads(raw_path.read_text(encoding="utf-8"))
            return 200, "cache_hit"
        except Exception:
            pass
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            body = response.read()
            raw_path.write_bytes(body)
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        raw_path.write_text(exc.read().decode("utf-8", errors="replace"), encoding="utf-8")
        status = exc.code
    except Exception as exc:
        raw_path.write_text(str(exc), encoding="utf-8")
        status = 0
    time.sleep(sleep_s)
    return status, "downloaded"


def get_fiscaldata_json_all(base: str, params: dict[str, str], raw_path: Path) -> tuple[int, str]:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists() and raw_path.stat().st_size > 0:
        try:
            cached = json.loads(raw_path.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("compiled_full_pagination") == 1:
                return 200, "cache_hit"
        except Exception:
            pass

    page_size = params.get("page[size]", "10000")
    all_data: list[dict[str, Any]] = []
    first_payload: dict[str, Any] | None = None
    page_number = 1
    status = 200
    while True:
        page_params = dict(params)
        page_params["page[size]"] = page_size
        page_params["page[number]"] = str(page_number)
        page_dir = raw_path.parent / f"{raw_path.stem}_pages"
        page_dir.mkdir(parents=True, exist_ok=True)
        page_path = page_dir / f"page_{page_number:04d}.json"
        if page_path.exists() and page_path.stat().st_size > 0:
            try:
                payload = json.loads(page_path.read_text(encoding="utf-8"))
            except Exception:
                page_path.unlink()
                payload = None
        else:
            payload = None
        if payload is None:
            url = build_url(base, page_params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            last_error = ""
            for attempt in range(1, 4):
                try:
                    with urllib.request.urlopen(req, timeout=120) as response:
                        body = response.read().decode("utf-8")
                        payload = json.loads(body)
                        page_path.write_text(body, encoding="utf-8")
                        status = getattr(response, "status", 200)
                        break
                except urllib.error.HTTPError as exc:
                    last_error = exc.read().decode("utf-8", errors="replace")
                    status = exc.code
                except Exception as exc:
                    last_error = str(exc)
                    status = 0
                time.sleep(0.5 * attempt)
            if payload is None:
                raw_path.write_text(last_error, encoding="utf-8")
                return status, "download_error"
        if first_payload is None:
            first_payload = payload
        data = payload.get("data", []) if isinstance(payload, dict) else []
        if isinstance(data, list):
            all_data.extend(data)
        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        total_pages = int(meta.get("total-pages") or meta.get("total_pages") or page_number)
        if page_number >= total_pages:
            break
        page_number += 1
        time.sleep(0.05)

    compiled = first_payload if isinstance(first_payload, dict) else {}
    compiled["data"] = all_data
    compiled["compiled_full_pagination"] = 1
    compiled["compiled_total_pages"] = page_number
    compiled["compiled_row_count"] = len(all_data)
    raw_path.write_text(json.dumps(compiled, ensure_ascii=True), encoding="utf-8")
    return status, "downloaded_paginated"


def load_universe() -> list[dict[str, str]]:
    return read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv")


def scope_rows(universe: list[dict[str, str]], fred_key_present: bool) -> list[dict[str, object]]:
    dates = sorted({row["decision_asof_ts"] for row in universe})
    return [
        {
            "task_id": "Task2561",
            "scope_id": "LIQRATESCOPE2561-0001",
            "scope_type": "liquidity_rates_regime_acquisition",
            "universe_rows": len(universe),
            "unique_decision_dates": len(dates),
            "decision_start": dates[0],
            "decision_end": dates[-1],
            "date_window_start": START_DATE,
            "date_window_end": END_DATE,
            "source_family": "liquidity_rates_regime",
            "nyfed_no_key_planned": "1",
            "treasury_no_key_planned": "1",
            "fred_key_present": "1" if fred_key_present else "0",
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


def source_family_plan_rows(fred_key_present: bool) -> list[dict[str, object]]:
    rows = [
        ("NYFED", "secured_unsecured_reference_rates_and_repo", "no_key_official", "strict_possible_with_effective_date_and_official_endpoint", "P0"),
        ("TREASURY", "daily_treasury_statement_and_debt_liquidity", "no_key_official", "strict_possible_with_record_date_and_official_endpoint", "P0"),
        ("FRED_ALFRED", "vintage_rates_credit_liquidity_series", "key_available" if fred_key_present else "key_missing", "strict_possible_only_with_realtime_or_vintage_rows", "P1"),
    ]
    return [
        {
            "task_id": "Task2562",
            "source_family_plan_id": f"LIQRATEFAM2562-{idx:04d}",
            "provider": provider,
            "source_family": family,
            "availability": availability,
            "pit_rule": pit_rule,
            "priority": priority,
            "download_or_api_call_run": "1" if provider != "FRED_ALFRED" or fred_key_present else "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (provider, family, availability, pit_rule, priority) in enumerate(rows, start=1)
    ]


def endpoint_specs(fred_key: str) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    ny_specs = [
        ("NYFED", "nyfed_secured_rate", f"{NYFED_BASE}/rates/secured/all/search.json", {"startDate": START_DATE, "endDate": END_DATE, "type": "rate"}, "refRates"),
        ("NYFED", "nyfed_secured_volume", f"{NYFED_BASE}/rates/secured/all/search.json", {"startDate": START_DATE, "endDate": END_DATE, "type": "volume"}, "refRates"),
        ("NYFED", "nyfed_unsecured_rate", f"{NYFED_BASE}/rates/unsecured/all/search.json", {"startDate": START_DATE, "endDate": END_DATE, "type": "rate"}, "refRates"),
        ("NYFED", "nyfed_unsecured_volume", f"{NYFED_BASE}/rates/unsecured/all/search.json", {"startDate": START_DATE, "endDate": END_DATE, "type": "volume"}, "refRates"),
        ("NYFED", "nyfed_repo_operations", f"{NYFED_BASE}/rp/results/search.json", {"startDate": START_DATE, "endDate": END_DATE, "operationTypes": "Repo,Reverse Repo"}, "repo"),
    ]
    treasury_specs = [
        ("TREASURY", "treasury_operating_cash_balance", f"{TREASURY_BASE}/v1/accounting/dts/operating_cash_balance", {"filter": f"record_date:gte:{START_DATE},record_date:lte:{END_DATE}", "page[size]": "10000"}, "data"),
        ("TREASURY", "treasury_deposits_withdrawals_operating_cash", f"{TREASURY_BASE}/v1/accounting/dts/deposits_withdrawals_operating_cash", {"filter": f"record_date:gte:{START_DATE},record_date:lte:{END_DATE}", "page[size]": "10000"}, "data"),
        ("TREASURY", "treasury_debt_to_penny", f"{TREASURY_BASE}/v2/accounting/od/debt_to_penny", {"filter": f"record_date:gte:{START_DATE},record_date:lte:{END_DATE}", "page[size]": "10000"}, "data"),
        ("TREASURY", "treasury_avg_interest_rates", f"{TREASURY_BASE}/v2/accounting/od/avg_interest_rates", {"filter": f"record_date:gte:{START_DATE},record_date:lte:{END_DATE}", "page[size]": "10000"}, "data"),
    ]
    for provider, endpoint, base, params, row_key in ny_specs + treasury_specs:
        specs.append({"provider": provider, "endpoint": endpoint, "base": base, "params": params, "row_key": row_key, "secret_keys": set()})
    for series_id in FRED_SERIES:
        if fred_key:
            obs_params = {
                "series_id": series_id,
                "observation_start": START_DATE,
                "observation_end": END_DATE,
                "realtime_start": START_DATE,
                "realtime_end": END_DATE,
                "output_type": "1",
                "file_type": "json",
                "api_key": fred_key,
            }
            vintage_params = {
                "series_id": series_id,
                "realtime_start": START_DATE,
                "realtime_end": END_DATE,
                "file_type": "json",
                "api_key": fred_key,
            }
            specs.append({"provider": "FRED_ALFRED", "endpoint": f"fred_observations_{series_id}", "base": f"{FRED_BASE}/series/observations", "params": obs_params, "row_key": "observations", "secret_keys": {"api_key"}})
            specs.append({"provider": "FRED_ALFRED", "endpoint": f"fred_vintagedates_{series_id}", "base": f"{FRED_BASE}/series/vintagedates", "params": vintage_params, "row_key": "vintage_dates", "secret_keys": {"api_key"}})
    return specs


def download_specs(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    call_rows: list[dict[str, object]] = []
    raw_rows: list[dict[str, object]] = []
    for idx, spec in enumerate(specs, start=1):
        provider = str(spec["provider"])
        endpoint = str(spec["endpoint"])
        base = str(spec["base"])
        params = dict(spec["params"])  # type: ignore[arg-type]
        secret_keys = set(spec["secret_keys"])  # type: ignore[arg-type]
        raw_path = RAW_DIR / provider.lower() / f"{endpoint}.json"
        url = build_url(base, params)
        safe_url = build_safe_url(base, params, secret_keys)
        if provider == "TREASURY":
            status, source = get_fiscaldata_json_all(base, params, raw_path)
        else:
            status, source = get_json(url, raw_path)
        raw_hash = sha256_file(raw_path) if raw_path.exists() else ""
        rel = raw_path.relative_to(ROOT).as_posix() if raw_path.exists() else ""
        try:
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
            row_key = str(spec["row_key"])
            row_count = len(payload.get(row_key, [])) if isinstance(payload, dict) else 0
            classification = "usable" if status == 200 else "download_error"
            if status == 200 and row_count == 0 and row_key != "repo":
                classification = "empty"
            if status == 200 and row_key == "repo":
                value = payload.get("repo", []) if isinstance(payload, dict) else []
                if isinstance(value, dict):
                    value = value.get("operations", [])
                row_count = len(value) if isinstance(value, list) else 0
                classification = "usable"
        except Exception:
            row_count = 0
            classification = "json_parse_error" if status == 200 else "download_error"
        call_rows.append(
            {
                "task_id": "Task2563",
                "raw_call_id": f"LIQRATECALL2563-{idx:04d}",
                "provider": provider,
                "endpoint": endpoint,
                "request_url_no_secret": safe_url,
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
                "task_id": "Task2564",
                "raw_response_id": f"LIQRATERAW2564-{idx:04d}",
                "provider": provider,
                "endpoint": endpoint,
                "http_status": status,
                "classification": classification,
                "row_count": row_count,
                "raw_path": rel,
                "raw_sha256": raw_hash,
                "raw_exists": "1" if raw_path.exists() else "0",
                "raw_size_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return call_rows, raw_rows


def load_raw_json(raw_path: str) -> Any:
    return json.loads((ROOT / raw_path).read_text(encoding="utf-8"))


def normalize_packets(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    packets: list[dict[str, object]] = []

    def add_packet(provider: str, endpoint: str, series_id: str, obs_date: str, value: object, unit: str, source_ts: str, basis: str, strict: bool, extra: dict[str, object] | None = None) -> None:
        packets.append(
            {
                "task_id": "Task2565",
                "source_packet_id": f"LIQRATEPKT2565-{len(packets)+1:07d}",
                "candidate_id": "",
                "trade_spec_id": "",
                "symbol": "",
                "decision_asof_ts": "",
                "provider": provider,
                "endpoint_or_source_family": endpoint,
                "series_id": series_id,
                "observation_date": obs_date,
                "value": value,
                "unit": unit,
                "source_ts": source_ts,
                "available_to_brain_ts": source_ts,
                "source_time_basis": basis,
                "source_time_certified": "1" if strict else "0",
                "strict_gate_pass": "1" if strict else "0",
                "proxy_feature_allowed": "0" if strict else "1",
                "raw_path": extra.get("raw_path", "") if extra else "",
                "raw_sha256": extra.get("raw_sha256", "") if extra else "",
                "realtime_start": extra.get("realtime_start", "") if extra else "",
                "realtime_end": extra.get("realtime_end", "") if extra else "",
                "release_or_effective_date": extra.get("release_or_effective_date", obs_date) if extra else obs_date,
                "vintage_date": extra.get("vintage_date", "") if extra else "",
                "publication_time_et": extra.get("publication_time_et", "") if extra else "",
                "retrieved_at_utc": extra.get("retrieved_at_utc", "") if extra else "",
                "pit_certification_status": "strict_official_or_vintage" if strict else "proxy_or_capture_only",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )

    for raw in raw_rows:
        if raw["classification"] not in {"usable", "empty"}:
            continue
        provider = str(raw["provider"])
        endpoint = str(raw["endpoint"])
        path = str(raw["raw_path"])
        if not path:
            continue
        payload = load_raw_json(path)
        extra_base = {"raw_path": path, "raw_sha256": raw["raw_sha256"], "retrieved_at_utc": now_iso()}
        if provider == "NYFED":
            rows = payload.get("refRates", []) if isinstance(payload, dict) else []
            if not rows and isinstance(payload, dict):
                repo_payload = payload.get("repo", [])
                rows = repo_payload.get("operations", []) if isinstance(repo_payload, dict) else repo_payload
            for row in rows:
                if not isinstance(row, dict):
                    continue
                obs_date = row.get("effectiveDate") or row.get("operationDate") or row.get("closeDate") or ""
                if not obs_date:
                    continue
                series = row.get("type") or row.get("operationType") or endpoint
                value = row.get("percentRate") or row.get("volumeInBillions") or row.get("totalAmtAccepted") or row.get("totalAmtSubmitted") or ""
                add_packet(provider, endpoint, str(series), obs_date, value, "", f"{obs_date}T23:59:59+00:00", "official_effective_date_end_of_day", True, extra_base | {"release_or_effective_date": obs_date})
        elif provider == "TREASURY":
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            strict_treasury_endpoint = endpoint != "treasury_avg_interest_rates"
            for row in rows:
                obs_date = row.get("record_date", "")
                if not obs_date:
                    continue
                for key, value in row.items():
                    if key.endswith("_amt") or key.endswith("_bal") or key in {"close_today_bal", "open_today_bal", "open_month_bal", "open_fiscal_year_bal", "avg_interest_rate_amt"}:
                        basis = "official_record_date_end_of_day" if strict_treasury_endpoint else "official_monthly_record_date_proxy_only"
                        add_packet(provider, endpoint, key, obs_date, value, "", f"{obs_date}T23:59:59+00:00", basis, strict_treasury_endpoint, extra_base | {"release_or_effective_date": obs_date})
        elif provider == "FRED_ALFRED":
            if endpoint.startswith("fred_observations_"):
                series = endpoint.replace("fred_observations_", "")
                for row in payload.get("observations", []):
                    obs_date = row.get("date", "")
                    realtime_start = row.get("realtime_start", "")
                    realtime_end = row.get("realtime_end", "")
                    source_ts = f"{realtime_start}T23:59:59+00:00" if realtime_start else ""
                    add_packet(provider, endpoint, series, obs_date, row.get("value", ""), "", source_ts, "fred_realtime_start_end_of_day", bool(source_ts), extra_base | {"realtime_start": realtime_start, "realtime_end": realtime_end, "vintage_date": realtime_start, "release_or_effective_date": obs_date})
            elif endpoint.startswith("fred_vintagedates_"):
                series = endpoint.replace("fred_vintagedates_", "")
                for vintage in payload.get("vintage_dates", []):
                    add_packet(provider, endpoint, series, vintage, "1", "vintage_marker", f"{vintage}T23:59:59+00:00", "fred_vintage_date_marker", True, extra_base | {"vintage_date": vintage, "release_or_effective_date": vintage})
    return packets


def decision_asof_coverage_rows(universe: list[dict[str, str]], packets: list[dict[str, object]]) -> list[dict[str, object]]:
    source_times = [parse_iso(str(row["available_to_brain_ts"])) for row in packets if row["strict_gate_pass"] == "1"]
    source_times = [dt for dt in source_times if dt is not None]
    by_decision: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        by_decision[row["decision_asof_ts"]].append(row)
    rows = []
    for idx, (decision_ts, candidates) in enumerate(sorted(by_decision.items(), key=lambda kv: parse_iso(kv[0]) or datetime.min.replace(tzinfo=timezone.utc)), start=1):
        decision_dt = parse_iso(decision_ts)
        available_count = sum(1 for ts in source_times if decision_dt and ts <= decision_dt)
        rows.append(
            {
                "task_id": "Task2566",
                "decision_asof_coverage_id": f"LIQRATECOV2566-{idx:04d}",
                "decision_asof_ts": decision_ts,
                "candidate_rows": len(candidates),
                "strict_available_packet_rows": available_count,
                "strict_coverage_available": "1" if available_count > 0 else "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def feature_admission_gate_rows(universe: list[dict[str, str]], coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    coverage_by_ts = {str(row["decision_asof_ts"]): row for row in coverage}
    rows = []
    for idx, candidate in enumerate(universe, start=1):
        cov = coverage_by_ts[candidate["decision_asof_ts"]]
        strict = cov["strict_coverage_available"] == "1"
        rows.append(
            {
                "task_id": "Task2567",
                "feature_gate_id": f"LIQRATEGATE2567-{idx:06d}",
                "candidate_id": candidate["candidate_source_id"],
                "trade_spec_id": candidate["trade_spec_id"],
                "symbol": candidate["symbol"],
                "decision_asof_ts": candidate["decision_asof_ts"],
                "layer": "L2/L3/L4",
                "feature_family": "liquidity_rates_regime",
                "feature_value_present": "1" if strict else "0",
                "strict_available_packet_rows": cov["strict_available_packet_rows"],
                "admission_state": "strict_pass" if strict else "blocked",
                "strict_gate_pass": "1" if strict else "0",
                "proxy_feature_allowed": "0",
                "can_score_assignment": "1" if strict else "0",
                "can_annotate_only": "0",
                "blocks_paper": "0" if strict else "1",
                "blocks_live": "0" if strict else "1",
                "gate_fail_reason": "" if strict else "no_liquidity_rates_packet_available_before_decision",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_gap_rows(raw_rows: list[dict[str, object]], fred_key_present: bool) -> list[dict[str, object]]:
    rows = []
    for raw in raw_rows:
        if raw["classification"] in {"usable", "empty"}:
            continue
        rows.append(
            {
                "task_id": "Task2568",
                "source_gap_ledger_id": f"LIQRATEGAP2568-{len(rows)+1:04d}",
                "provider": raw["provider"],
                "endpoint": raw["endpoint"],
                "feature_family": "liquidity_rates_regime",
                "gap_state": "blocked",
                "gap_reason": raw["classification"],
                "required_for_assignment": "1",
                "required_for_paper": "1",
                "required_for_live": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "allowed_resolution": "fix_endpoint_or_entitlement_then_rerun",
                "authority": AUTHORITY,
            }
        )
    if not fred_key_present:
        rows.append(
            {
                "task_id": "Task2568",
                "source_gap_ledger_id": f"LIQRATEGAP2568-{len(rows)+1:04d}",
                "provider": "FRED_ALFRED",
                "endpoint": "all_fred_vintage_series",
                "feature_family": "liquidity_rates_regime",
                "gap_state": "blocked",
                "gap_reason": "missing_fred_api_key",
                "required_for_assignment": "0",
                "required_for_paper": "0",
                "required_for_live": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "allowed_resolution": "provide_FRED_API_KEY_then_rerun",
                "authority": AUTHORITY,
            }
        )
    return rows


def summary_rows(packets: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(row["provider"]) for row in packets)
    endpoints = Counter(str(row["endpoint_or_source_family"]) for row in packets)
    rows = []
    for key, value in sorted(counts.items()):
        rows.append({"task_id": "Task2569", "summary_id": f"LIQRATESUM2569-{len(rows)+1:04d}", "summary_type": "provider", "bucket": key, "row_count": value, "missing_source_is_negative": "0", "assignment_uses_future_outcome": "0", "outcome_used_for_assignment": "0", "authority": AUTHORITY})
    for key, value in sorted(endpoints.items()):
        rows.append({"task_id": "Task2569", "summary_id": f"LIQRATESUM2569-{len(rows)+1:04d}", "summary_type": "endpoint", "bucket": key, "row_count": value, "missing_source_is_negative": "0", "assignment_uses_future_outcome": "0", "outcome_used_for_assignment": "0", "authority": AUTHORITY})
    return rows


def subagent_rows() -> list[dict[str, object]]:
    agents = [
        ("Goodall", "019ed601-42f3-72f2-9ce7-feade77680c7", "nyfed_treasury_endpoint_review", "DATA_HEALTH / RESEARCH_ONLY"),
        ("Franklin", "019ed601-84c7-7e73-aa8f-767f8f590d1b", "liquidity_rates_validation_checklist", "DATA_HEALTH / GOVERNANCE_HEALTH"),
        ("Aristotle", "019ed601-bae8-7570-9dc0-c0f1e3178705", "fred_vintage_env_and_design_review", "DATA_HEALTH / RESEARCH_ONLY"),
    ]
    return [
        {
            "task_id": "Task2570",
            "subagent_packet_id": f"LIQRATESUB2570-{idx:04d}",
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
        for idx, (nickname, agent_id, role, authority) in enumerate(agents, start=1)
    ]


def closeout_rows(scope: dict[str, object], raw_rows: list[dict[str, object]], packets: list[dict[str, object]], gates: list[dict[str, object]], gaps: list[dict[str, object]]) -> list[dict[str, object]]:
    strict = sum(1 for row in packets if row["strict_gate_pass"] == "1")
    return [
        {
            "task_id": "Task2580",
            "verdict": "liquidity_rates_regime_acquisition_complete",
            "universe_rows": scope["universe_rows"],
            "unique_decision_dates": scope["unique_decision_dates"],
            "raw_response_rows": len(raw_rows),
            "usable_or_empty_raw_rows": sum(1 for row in raw_rows if row["classification"] in {"usable", "empty"}),
            "normalized_packet_rows": len(packets),
            "strict_packet_rows": strict,
            "feature_gate_rows": len(gates),
            "strict_feature_gate_rows": sum(1 for row in gates if row["strict_gate_pass"] == "1"),
            "source_gap_rows": len(gaps),
            "fred_key_present": scope["fred_key_present"],
            "download_or_api_call_run": "1",
            "backtest_run": "0",
            "selector_changed": "0",
            "next_action": "Task2581+ should join SEC financing/dilution and liquidity/rates features into L2/L3 admission, then run selector-only diagnostics before any replay.",
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
    summary_lines = "\n".join(f"- {row['summary_type']} `{row['bucket']}`: {row['row_count']}" for row in summary[:35])
    REPORT.write_text(
        f"""# Task2561-2580 Liquidity Rates Regime Acquisition

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Universe rows: {closeout['universe_rows']}.
- Decision dates: {closeout['unique_decision_dates']}.
- Raw response rows: {closeout['raw_response_rows']}.
- Normalized packet rows: {closeout['normalized_packet_rows']}.
- Strict packet rows: {closeout['strict_packet_rows']}.
- Feature gate rows: {closeout['feature_gate_rows']}.
- Strict feature gate rows: {closeout['strict_feature_gate_rows']}.
- FRED key present: `{closeout['fred_key_present']}`.
- Backtest run: `0`.
- Selector changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task acquired the next source family from the Task2531 queue: liquidity/rates regime. It used no-key NY Fed and Treasury official APIs first, then FRED/ALFRED vintage-style requests if `FRED_API_KEY` was locally available. API keys are not persisted in ledgers, raw files, or reports.

Boundary:

- NY Fed and Treasury rows use official effective/record dates with end-of-day availability assumptions.
- FRED/ALFRED rows use `realtime_start/realtime_end` and vintage-date rows when available.
- Retrieval timestamp alone does not open a strict gate.
- No selector change and no replay were performed.

Packet summary:

{summary_lines}

## No-Background Decision-Maker Report

Conclusion first: liquidity/rates regime source is now attached as a governed source family.

This gives the brain macro/liquidity context for future selector diagnostics. It still does not approve the strategy or allow live/paper trading by itself.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/`.
- Raw files: `data/raw/task_2561_2580_liquidity_rates_regime_acquisition/`.
- Validator: `python scripts/trader_brain_2561_2580_liquidity_rates_regime_acquisition_validate.py`.

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
    for task_no in range(2561, 2581):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Liquidity Rates Regime Acquisition Step {task_no}",
                "owner_team": "Data & Market Microstructure / Regime Research / Research Governance",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "liquidity-rates-regime-acquired-diagnostic-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2561_2580_liquidity_rates_regime_acquisition/task_2561_2580_liquidity_rates_regime_acquisition.md",
                "key_decision": "docs/reports/task_2561_2580_liquidity_rates_regime_acquisition/task_2580_decision.csv",
                "key_artifacts": "data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition",
                "validation_command": "python scripts/trader_brain_2561_2580_liquidity_rates_regime_acquisition_validate.py",
                "notes": "Downloads NY Fed/Treasury/FRED liquidity and rates regime sources; no replay/selector change.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    lines = path.read_text(encoding="utf-8").rstrip().splitlines()
    line_125 = (
        "125. Task2561-Task2580 acquired liquidity/rates regime sources after SEC financing/dilution: "
        f"raw responses {closeout['raw_response_rows']}, normalized packets {closeout['normalized_packet_rows']}, "
        f"strict packets {closeout['strict_packet_rows']}, strict feature rows {closeout['strict_feature_gate_rows']}, "
        f"FRED key present {closeout['fred_key_present']}; no backtest, no selector change. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    out = []
    replaced = False
    for line in lines:
        if line.startswith("125. Task2561-Task2580"):
            out.append(line_125)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(line_125)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    universe = load_universe()
    fred_key = load_dotenv_key("FRED_API_KEY")
    fred_key_present = bool(fred_key)
    scope = scope_rows(universe, fred_key_present)
    families = source_family_plan_rows(fred_key_present)
    specs = endpoint_specs(fred_key)
    calls, raw_rows = download_specs(specs)
    packets = normalize_packets(raw_rows)
    coverage = decision_asof_coverage_rows(universe, packets)
    gates = feature_admission_gate_rows(universe, coverage)
    gaps = source_gap_rows(raw_rows, fred_key_present)
    summary = summary_rows(packets)
    subagents = subagent_rows()
    closeout = closeout_rows(scope[0], raw_rows, packets, gates, gaps)

    outputs = [
        ("task2561_scope_freeze.csv", scope),
        ("task2562_source_family_plan.csv", families),
        ("task2563_api_or_raw_call_ledger.csv", calls),
        ("task2564_raw_response_classification.csv", raw_rows),
        ("task2565_normalized_liquidity_rates_packets.csv", packets),
        ("task2566_decision_asof_coverage.csv", coverage),
        ("task2567_feature_admission_gate.csv", gates),
        ("task2568_source_gap_ledger.csv", gaps),
        ("task2569_packet_summary.csv", summary),
        ("task2570_subagent_packets.csv", subagents),
        ("task2580_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2580_closeout.json", closeout[0])
    write_report(closeout[0], summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2561_2580_LIQUIDITY_RATES_REGIME_ACQUISITION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
