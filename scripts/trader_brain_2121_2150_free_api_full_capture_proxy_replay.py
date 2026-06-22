from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1991 = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
OUT_DIR = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
RAW_OUT = ROOT / "data/raw/task_2121_2150_free_api_full_capture_proxy_replay"
REPORT_DIR = ROOT / "docs/reports/task_2121_2150_free_api_full_capture_proxy_replay"
REPORT = REPORT_DIR / "task_2121_2150_free_api_full_capture_proxy_replay.md"
DECISION = REPORT_DIR / "task_2121_2150_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_API_FULL_CAPTURE_PROXY_REPLAY_ONLY"
POLICY_ID = "free_api_proxy_top5_to_top2_convex_v1"
SOURCE_POLICY = "winner_defense_budget_top5_v1"
BASELINE_POLICY = "winner_accel_top5_to_top2_convex_v1"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265
USER_AGENT = "codex-free-api-source-capture/1.0 contact=local"


PROVIDER_LIMITS = {
    "finnhub": {"max_calls": 120, "sleep_sec": 1.05},
    "fmp": {"max_calls": 220, "sleep_sec": 0.35},
    "alpha_vantage": {"max_calls": 5, "sleep_sec": 13.0},
}


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


def redact_secrets(text: str, params: dict[str, object]) -> str:
    redacted = text
    for secret_key in ("token", "apikey"):
        secret = str(params.get(secret_key, "") or "")
        if secret:
            redacted = redacted.replace(secret, "[REDACTED_API_KEY]")
    return redacted


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:120].strip("_") or "source"


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.fromisoformat(text + "T00:00:00+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    dt = parse_dt(value)
    return dt.date() if dt else None


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


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "scope": read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv"),
        "l4": read_csv(TASK1991 / "task1995_l4_winner_acceleration_thesis_cards.csv"),
        "l5": read_csv(TASK1991 / "task1996_l5_winner_acceleration_decisions.csv"),
        "trades": read_csv(TASK1991 / "task1997_winner_acceleration_replay_trades.csv"),
        "source_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "metrics": read_csv(TASK1991 / "task1998_winner_acceleration_replay_metrics.csv"),
    }


def request_json(provider: str, endpoint_name: str, url: str, params: dict[str, object], symbol: str, counters: dict[str, int]) -> dict[str, object]:
    limit = PROVIDER_LIMITS[provider]["max_calls"]
    if counters[provider] >= limit:
        return {
            "call_status": "skipped_provider_budget_exhausted",
            "http_status": "",
            "raw_path": "",
            "raw_sha256": "",
            "response_shape": "",
            "response_note": "provider_daily_task_budget_exhausted",
        }
    out_path = RAW_OUT / provider / endpoint_name / symbol / f"{params_hash(params)}.json"
    capture_ts = now_ts()
    if out_path.exists() and out_path.stat().st_size > 0:
        raw_text = out_path.read_text(encoding="utf-8", errors="ignore")
        clean_raw_text = redact_secrets(raw_text, params)
        if clean_raw_text != raw_text:
            out_path.write_text(clean_raw_text, encoding="utf-8")
            raw_text = clean_raw_text
        try:
            payload = json.loads(raw_text)
            shape, note = response_shape(payload)
        except Exception:
            shape, note = "raw_reused_unparsed", raw_text[:180]
        inferred_status = "200"
        lowered = note.lower()
        if "limit reach" in lowered or "rate limit" in lowered:
            inferred_status = "429"
        elif "restricted endpoint" in lowered or "not available under your current subscription" in lowered:
            inferred_status = "402"
        elif "don't have access" in lowered or "access to this resource" in lowered:
            inferred_status = "403"
        return {
            "call_status": "reused" if inferred_status == "200" else "reused_blocked",
            "http_status": inferred_status,
            "raw_path": str(out_path.relative_to(ROOT)),
            "raw_sha256": file_sha256(out_path),
            "response_shape": shape,
            "response_note": note,
            "capture_ts_utc": capture_ts,
        }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(url, params=params, timeout=35, headers={"User-Agent": USER_AGENT})
        raw_text = response.text
        clean_raw_text = redact_secrets(raw_text, params)
        content = clean_raw_text.encode("utf-8")
        out_path.write_bytes(content)
        try:
            payload = json.loads(clean_raw_text)
            shape, note = response_shape(payload)
        except Exception:
            shape, note = "text", clean_raw_text[:180]
        counters[provider] += 1
        time.sleep(float(PROVIDER_LIMITS[provider]["sleep_sec"]))
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
        counters[provider] += 1
        time.sleep(float(PROVIDER_LIMITS[provider]["sleep_sec"]))
        return {
            "call_status": "failed",
            "http_status": "0",
            "raw_path": "",
            "raw_sha256": "",
            "response_shape": "error",
            "response_note": str(exc)[:180],
            "capture_ts_utc": capture_ts,
        }


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


def provider_endpoint_plan(symbols: list[str], env: dict[str, str]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    finnhub_key = env.get("FINNHUB_API_KEY", "")
    fmp_key = env.get("FMP_API_KEY", "")
    alpha_key = env.get("ALPHA_VANTAGE_API_KEY", "")
    for symbol in symbols:
        if finnhub_key:
            plan.append(
                {
                    "provider": "finnhub",
                    "endpoint_name": "stock_filings",
                    "symbol": symbol,
                    "url": "https://finnhub.io/api/v1/stock/filings",
                    "params": {"symbol": symbol, "from": "2021-01-01", "to": "2026-03-31", "token": finnhub_key},
                    "l0_l5_role": "L1 filing index; L2 financing/dilution/invalidation support",
                    "strict_gate_permission": "source_support_only_not_transcript_or_analyst_gate",
                }
            )
            plan.append(
                {
                    "provider": "finnhub",
                    "endpoint_name": "stock_recommendation",
                    "symbol": symbol,
                    "url": "https://finnhub.io/api/v1/stock/recommendation",
                    "params": {"symbol": symbol, "token": finnhub_key},
                    "l0_l5_role": "L2 weak analyst sentiment proxy; L5 direct gate forbidden",
                    "strict_gate_permission": "proxy_only_not_pit_revision_gate",
                }
            )
        if fmp_key:
            for endpoint_name, path, params in [
                ("earnings", "earnings", {"symbol": symbol}),
                ("income_statement", "income-statement", {"symbol": symbol, "period": "quarter", "limit": "5"}),
                ("balance_sheet", "balance-sheet-statement", {"symbol": symbol, "period": "quarter", "limit": "5"}),
                ("cash_flow", "cash-flow-statement", {"symbol": symbol, "period": "quarter", "limit": "5"}),
                ("grades_historical", "grades-historical", {"symbol": symbol}),
            ]:
                full_params = {**params, "apikey": fmp_key}
                plan.append(
                    {
                        "provider": "fmp",
                        "endpoint_name": endpoint_name,
                        "symbol": symbol,
                        "url": f"https://financialmodelingprep.com/stable/{path}",
                        "params": full_params,
                        "l0_l5_role": "L1/L2 fundamentals or analyst-adjacent proxy",
                        "strict_gate_permission": "proxy_only_or_financial_statement_support",
                    }
                )
        if alpha_key:
            # Alpha is heavily quota-limited; capture transcript canaries only for the first few symbols.
            plan.append(
                {
                    "provider": "alpha_vantage",
                    "endpoint_name": "earnings_history",
                    "symbol": symbol,
                    "url": "https://www.alphavantage.co/query",
                    "params": {"function": "EARNINGS", "symbol": symbol, "apikey": alpha_key},
                    "l0_l5_role": "L2 earnings surprise proxy",
                    "strict_gate_permission": "proxy_only_not_analyst_revision_gate",
                }
            )
    return plan


def execute_plan(plan: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    counters = {"finnhub": 0, "fmp": 0, "alpha_vantage": 0}
    ledger: list[dict[str, object]] = []
    capability: dict[tuple[str, str], dict[str, object]] = {}
    for idx, item in enumerate(plan, start=1):
        provider = str(item["provider"])
        endpoint_name = str(item["endpoint_name"])
        symbol = str(item["symbol"])
        result = request_json(provider, endpoint_name, str(item["url"]), dict(item["params"]), symbol, counters)
        http_status = str(result.get("http_status", ""))
        call_status = str(result.get("call_status", ""))
        note = str(result.get("response_note", ""))
        blocked = "1" if http_status in {"402", "403", "429"} or call_status.startswith("skipped") or "premium" in note.lower() or "not available" in note.lower() else "0"
        sanitized_params = {k: v for k, v in dict(item["params"]).items() if k not in {"token", "apikey"}}
        ledger_row = {
            "task_id": "Task2122",
            "api_call_id": f"APICALL-2122-{idx:06d}",
            "provider": provider,
            "endpoint_name": endpoint_name,
            "symbol": symbol,
            "params_json_without_key": json.dumps(sanitized_params, sort_keys=True),
            "http_status": http_status,
            "call_status": call_status,
            "blocked_by_plan_or_entitlement": blocked,
            "raw_path": result.get("raw_path", ""),
            "raw_sha256": result.get("raw_sha256", ""),
            "capture_ts_utc": result.get("capture_ts_utc", now_ts()),
            "response_shape": result.get("response_shape", ""),
            "response_note": note,
            "l0_l5_role": item["l0_l5_role"],
            "strict_gate_permission": item["strict_gate_permission"],
            "request_url_contains_secret": "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        ledger.append(ledger_row)
        key = (provider, endpoint_name)
        cap = capability.setdefault(
            key,
            {
                "task_id": "Task2121",
                "provider_capability_id": f"CAPABILITY-2121-{len(capability) + 1:03d}",
                "provider": provider,
                "endpoint_name": endpoint_name,
                "attempted_symbols": 0,
                "success_rows": 0,
                "blocked_rows": 0,
                "first_blocker": "",
                "strict_gate_permission": item["strict_gate_permission"],
                "authority": AUTHORITY,
            },
        )
        cap["attempted_symbols"] = int(cap["attempted_symbols"]) + 1
        if blocked == "1":
            cap["blocked_rows"] = int(cap["blocked_rows"]) + 1
            if not cap["first_blocker"]:
                cap["first_blocker"] = f"{http_status}:{note[:80]}"
        elif call_status in {"downloaded", "reused"} and http_status == "200":
            cap["success_rows"] = int(cap["success_rows"]) + 1
    return ledger, list(capability.values())


def read_json_raw(row: dict[str, str]) -> object:
    path = ROOT / str(row.get("raw_path", ""))
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def normalize_source_rows(ledger: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, dict[str, list[dict[str, object]]]]]:
    normalized: list[dict[str, object]] = []
    by_symbol_endpoint: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    row_id = 1
    for lrow in ledger:
        if str(lrow.get("http_status")) != "200" or not lrow.get("raw_path"):
            continue
        payload = read_json_raw({k: str(v) for k, v in lrow.items()})
        provider = str(lrow["provider"])
        endpoint = str(lrow["endpoint_name"])
        symbol = str(lrow["symbol"])
        records: list[dict[str, object]]
        if isinstance(payload, list):
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
            source_ts = (
                rec.get("acceptedDate")
                or rec.get("filedDate")
                or rec.get("filingDate")
                or rec.get("reportedDate")
                or rec.get("date")
                or rec.get("period")
                or ""
            )
            norm = {
                "task_id": "Task2123",
                "api_normalized_source_id": f"APINORM-2123-{row_id:07d}",
                "api_call_id": lrow["api_call_id"],
                "provider": provider,
                "endpoint_name": endpoint,
                "symbol": symbol,
                "source_ts": source_ts,
                "raw_path": lrow["raw_path"],
                "raw_sha256": lrow["raw_sha256"],
                "record_json": json.dumps(rec, sort_keys=True, ensure_ascii=False)[:4000],
                "provider_available_ts_basis": "provider_record_timestamp_or_capture_only",
                "strict_gate_pass": "0",
                "proxy_feature_allowed": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
            normalized.append(norm)
            by_symbol_endpoint[symbol][endpoint].append({**rec, "_norm_id": norm["api_normalized_source_id"], "_source_ts": source_ts})
            row_id += 1
    return normalized, by_symbol_endpoint


def latest_before(records: list[dict[str, object]], decision: datetime, date_keys: list[str]) -> dict[str, object] | None:
    best: tuple[datetime, dict[str, object]] | None = None
    for rec in records:
        ts = None
        for key in date_keys:
            ts = parse_dt(rec.get(key))
            if ts:
                break
        if ts and ts <= decision:
            if best is None or ts > best[0]:
                best = (ts, rec)
    return best[1] if best else None


def count_filings(records: list[dict[str, object]], decision: datetime, lookback_days: int = 365) -> tuple[int, int, int]:
    start = decision - timedelta(days=lookback_days)
    total = eightk = annual_quarterly = 0
    for rec in records:
        ts = parse_dt(rec.get("acceptedDate") or rec.get("filedDate"))
        if not ts or not (start <= ts <= decision):
            continue
        total += 1
        form = str(rec.get("form", ""))
        if form.startswith("8-K"):
            eightk += 1
        if form in {"10-Q", "10-K"}:
            annual_quarterly += 1
    return total, eightk, annual_quarterly


def proxy_features(inputs: dict[str, list[dict[str, str]]], normalized_index: dict[str, dict[str, list[dict[str, object]]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in inputs["l4"]}
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    features: list[dict[str, object]] = []
    semantics: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    cards: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["l5"], start=1):
        decision = parse_dt(row["decision_asof_ts"])
        if not decision:
            continue
        symbol = row["symbol"]
        endpoints = normalized_index.get(symbol, {})
        filing_total, filing_8k, filing_10x = count_filings(endpoints.get("stock_filings", []), decision)
        earnings = latest_before(endpoints.get("earnings", []), decision, ["date"])
        fmp_income = latest_before(endpoints.get("income_statement", []), decision, ["acceptedDate", "filingDate", "date"])
        fmp_balance = latest_before(endpoints.get("balance_sheet", []), decision, ["acceptedDate", "filingDate", "date"])
        fmp_cash = latest_before(endpoints.get("cash_flow", []), decision, ["acceptedDate", "filingDate", "date"])
        grades = latest_before(endpoints.get("grades_historical", []), decision, ["date"])
        surprise_pct = to_float((earnings or {}).get("surprisePercentage"), 0.0)
        revenue = to_float((fmp_income or {}).get("revenue"), 0.0)
        net_income = to_float((fmp_income or {}).get("netIncome"), 0.0)
        cash = to_float((fmp_balance or {}).get("cashAndCashEquivalents"), 0.0)
        debt = to_float((fmp_balance or {}).get("totalDebt"), 0.0)
        fcf = to_float((fmp_cash or {}).get("freeCashFlow"), 0.0)
        strong_buy = to_float((grades or {}).get("analystRatingsStrongBuy"), 0.0)
        buy = to_float((grades or {}).get("analystRatingsBuy"), 0.0)
        hold = to_float((grades or {}).get("analystRatingsHold"), 0.0)
        sell = to_float((grades or {}).get("analystRatingsSell"), 0.0)
        strong_sell = to_float((grades or {}).get("analystRatingsStrongSell"), 0.0)
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
        elif filing_total == 0 and not earnings and not fmp_income:
            state = "api_proxy_source_gap_neutral"
        else:
            state = "api_proxy_mixed_or_light"
        base_rank = to_float(l4_by_spec.get(row["trade_spec_id"], {}).get("winner_acceleration_rank_score"))
        adjusted_rank = round(base_rank + api_proxy_score, 4)
        feature_id = f"APIFEAT-2124-{idx:06d}"
        features.append(
            {
                "task_id": "Task2124",
                "api_feature_id": feature_id,
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
                "strict_transcript_gate_pass": "0",
                "strict_analyst_revision_gate_pass": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        semantics.append(
            {
                "task_id": "Task2125",
                "api_l2_semantic_id": f"APIL2-2125-{idx:06d}",
                "api_feature_id": feature_id,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "api_proxy_state": state,
                "semantic_summary": f"filings={filing_total}; surprise={round(surprise_pct,2)}; quality={round(quality_score,2)}; rating={round(rating_score,2)}",
                "l5_direct_gate_permission": "0",
                "authority": AUTHORITY,
            }
        )
        for rel_idx, rel in enumerate(["filing_activity_context", "earnings_surprise_proxy", "fundamental_quality_proxy"], start=1):
            edges.append(
                {
                    "task_id": "Task2126",
                    "api_l3_edge_id": f"APIL3-2126-{idx:06d}-{rel_idx}",
                    "from_api_feature_id": feature_id,
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": symbol,
                    "relation_type": rel,
                    "relation_permission": "proxy_only_not_strict_gate",
                    "authority": AUTHORITY,
                }
            )
        cards.append(
            {
                "task_id": "Task2127",
                "api_l4_card_id": f"APIL4-2127-{idx:06d}",
                "api_feature_id": feature_id,
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "target_policy_variant_id": row["target_policy_variant_id"],
                "base_winner_acceleration_rank_score": base_rank,
                "api_proxy_score": api_proxy_score,
                "api_adjusted_rank_score": adjusted_rank,
                "api_proxy_state": state,
                "winner_acceleration_state": row["winner_acceleration_state"],
                "winner_thesis_state": row["winner_thesis_state"],
                "strict_gate_status": "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return features, semantics, edges, cards


def replay_proxy(inputs: dict[str, list[dict[str, str]]], cards: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    card_by_spec = {row["trade_spec_id"]: row for row in cards}
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["source_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["l5"]:
        if row["target_policy_variant_id"] == SOURCE_POLICY:
            grouped[row["decision_asof_ts"]].append(row)
    capital = INITIAL_CAPITAL
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    trade_idx = 1
    for decision_ts in sorted(grouped):
        candidates = sorted(
            grouped[decision_ts],
            key=lambda row: (
                to_float(card_by_spec.get(row["trade_spec_id"], {}).get("api_adjusted_rank_score")),
                to_float(card_by_spec.get(row["trade_spec_id"], {}).get("base_winner_acceleration_rank_score")),
            ),
            reverse=True,
        )[:2]
        base_alloc = capital / 2.0
        period_pnl = 0.0
        allocated = 0
        for row in candidates:
            src = source_trades.get((SOURCE_POLICY, row["trade_spec_id"]))
            decision = l5_by_spec.get(row["trade_spec_id"])
            card = card_by_spec.get(row["trade_spec_id"])
            if not src or not decision or not card:
                continue
            raw_mult = to_float(decision["raw_combined_multiplier"])
            state = str(card["api_proxy_state"])
            if state == "api_proxy_supportive":
                raw_mult *= 1.04
            elif state == "api_proxy_risk_or_weak_quality":
                raw_mult *= 0.82
            mult = clamp(raw_mult, 0.0, 1.42)
            cap_alloc = base_alloc * mult
            pnl = cap_alloc * to_float(src["net_return"])
            capital += pnl
            period_pnl += pnl
            allocated += 1
            trades.append(
                {
                    "task_id": "Task2128",
                    "trade_row_id": f"APIPROXYREPLAY-2128-{trade_idx:07d}",
                    "policy_variant_id": POLICY_ID,
                    "source_policy_variant_id": SOURCE_POLICY,
                    "baseline_policy_variant_id": BASELINE_POLICY,
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "api_proxy_state": state,
                    "base_rank_score": card["base_winner_acceleration_rank_score"],
                    "api_proxy_score": card["api_proxy_score"],
                    "api_adjusted_rank_score": card["api_adjusted_rank_score"],
                    "final_budget_multiplier": round(mult, 6),
                    "source_net_return": src.get("net_return", ""),
                    "capital_allocated": round(cap_alloc, 4),
                    "pnl": round(pnl, 4),
                    "net_return": src.get("net_return", ""),
                    "entry_date": src.get("entry_date", ""),
                    "actual_exit_date": src.get("actual_exit_date", ""),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            trade_idx += 1
        equity.append(
            {
                "task_id": "Task2129",
                "policy_variant_id": POLICY_ID,
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "candidate_pool_count": len(grouped[decision_ts]),
                "allocated_count": allocated,
                "authority": AUTHORITY,
            }
        )
    metrics = [metrics_for(trades, equity, inputs)]
    return trades, equity, metrics


def metrics_for(trades: list[dict[str, object]], equity: list[dict[str, object]], inputs: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1] if values else INITIAL_CAPITAL
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date() if equity else date(2021, 1, 1)
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final / INITIAL_CAPITAL) ** (1 / years) - 1.0
    mdd = replay.max_drawdown(values)
    baseline = next(row for row in inputs["metrics"] if row["policy_variant_id"] == BASELINE_POLICY)
    return {
        "task_id": "Task2130",
        "policy_variant_id": POLICY_ID,
        "source_policy_variant_id": SOURCE_POLICY,
        "baseline_policy_variant_id": BASELINE_POLICY,
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final, 4),
        "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(mdd, 6),
        "trade_count": len(trades),
        "qqq_benchmark_final": QQQ_BENCHMARK_FINAL,
        "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
        "baseline_final_equity": baseline["final_equity"],
        "baseline_cagr": baseline["cagr"],
        "baseline_max_drawdown": baseline["max_drawdown"],
        "delta_vs_baseline_final_equity": round(final - to_float(baseline["final_equity"]), 4),
        "delta_vs_baseline_cagr": round(cagr - to_float(baseline["cagr"]), 6),
        "delta_vs_baseline_mdd": round(mdd - to_float(baseline["max_drawdown"]), 6),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def closeout_rows(symbols: list[str], ledger: list[dict[str, object]], capability: list[dict[str, object]], features: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2150",
            "verdict": "free_api_capture_proxy_replay_complete_diagnostic_only",
            "scope_symbols": len(symbols),
            "api_call_rows": len(ledger),
            "downloaded_or_reused_rows": sum(1 for row in ledger if row["call_status"] in {"downloaded", "reused"}),
            "blocked_rows": sum(1 for row in ledger if row["blocked_by_plan_or_entitlement"] == "1"),
            "provider_capability_rows": len(capability),
            "feature_rows": len(features),
            "best_policy_variant_id": metrics[0]["policy_variant_id"],
            "best_final_equity": metrics[0]["final_equity"],
            "best_cagr": metrics[0]["cagr"],
            "best_max_drawdown": metrics[0]["max_drawdown"],
            "joint_target_met": metrics[0]["joint_target_met"],
            "strict_transcript_gate_pass_rows": 0,
            "strict_analyst_revision_gate_pass_rows": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Task2121-2150 Free API Full Capture Proxy Replay

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Scope symbols: {closeout['scope_symbols']}.
- API call rows: {closeout['api_call_rows']}.
- Downloaded or reused rows: {closeout['downloaded_or_reused_rows']}.
- Blocked rows: {closeout['blocked_rows']}.
- Feature rows: {closeout['feature_rows']}.
- Replay policy: `{metrics['policy_variant_id']}`.
- Final equity: {metrics['final_equity']}.
- CAGR: {metrics['cagr']}.
- MDD: {metrics['max_drawdown']}.
- Baseline: `{metrics['baseline_policy_variant_id']}` final {metrics['baseline_final_equity']}, CAGR {metrics['baseline_cagr']}, MDD {metrics['baseline_max_drawdown']}.
- Delta final equity: {metrics['delta_vs_baseline_final_equity']}.
- Strict transcript gate pass rows: 0.
- Strict analyst PIT gate pass rows: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task uses the newly provided free API keys with a fixed acquisition rule:

1. Capture raw JSON, hash it, and store a sanitized call ledger.
2. Treat free transcript and analyst-like data as proxy-only unless publication/provider availability and revision timestamps are certified.
3. Build L1/L2/L3/L4 proxy features from captured source fields only.
4. Run one controlled diagnostic replay using the existing frozen winner-acceleration candidate pool and source replay returns.

The replay is diagnostic only. It does not prove paper readiness because transcript and analyst PIT gates remain closed.

## No-Background Decision-Maker Report

1. 무료 API로 받을 수 있는 건 최대한 받았다.
2. 받은 건 원문 raw와 hash로 남겼다.
3. transcript/analyst strict gate는 아직 안 열었다.
4. 무료 API 데이터는 보조 점수로만 넣었다.
5. 그 점수로 다시 top2를 고르는 백테스트를 돌렸다.

## Artifact Manifest

- `task2121_provider_capability_gate.csv`
- `task2122_api_call_ledger.csv`
- `task2123_api_normalized_sources.csv`
- `task2124_l1_api_proxy_features.csv`
- `task2125_l2_api_proxy_semantics.csv`
- `task2126_l3_api_proxy_edges.csv`
- `task2127_l4_api_proxy_score_cards.csv`
- `task2128_api_proxy_replay_trades.csv`
- `task2129_api_proxy_replay_equity.csv`
- `task2130_api_proxy_replay_metrics.csv`
- `task2150_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2121," in text:
        return
    rows = []
    for task_num in range(2121, 2151):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": f"Free API Capture Proxy Replay Step {task_num}",
                "owner_team": "Research Governance / Data & Market Microstructure / Backtest & Simulation Infra",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "free-api-proxy-captured-strict-gates-still-blocked",
                "parent_task": "Task2120" if task_num == 2121 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2121_2150_free_api_full_capture_proxy_replay/task_2121_2150_free_api_full_capture_proxy_replay.md",
                "key_decision": "docs/reports/task_2121_2150_free_api_full_capture_proxy_replay/task_2121_2150_decision.csv",
                "key_artifacts": "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay",
                "validation_command": "python scripts/trader_brain_2121_2150_free_api_full_capture_proxy_replay_validate.py",
                "notes": "Captures free API raw data under quota, converts proxy-only features, and runs diagnostic replay without opening strict transcript/analyst gates.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    row = (
        f"106. Task2121-Task2150 captured newly available free API sources for the frozen aggressive-policy scope: "
        f"{closeout['scope_symbols']} symbols, {closeout['api_call_rows']} API call rows, {closeout['downloaded_or_reused_rows']} downloaded/reused raw rows, "
        f"{closeout['feature_rows']} proxy feature rows, and a diagnostic proxy replay ending final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} "
        f"MDD {closeout['best_max_drawdown']}; strict transcript and analyst PIT gates remain closed while strategy remains NOT_ACCEPTED / "
        f"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.startswith("106. Task2121-Task2150"):
            lines[idx] = row
            path.write_text("".join(lines), encoding="utf-8")
            return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("105. Task2091-Task2120"):
            insert_at = idx + 1
            break
    lines.insert(insert_at, row)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    env = load_env()
    inputs = load_inputs()
    symbols = sorted({row["symbol"] for row in inputs["scope"]})
    plan = provider_endpoint_plan(symbols, env)
    ledger, capability = execute_plan(plan)
    normalized, norm_index = normalize_source_rows(ledger)
    features, semantics, edges, cards = proxy_features(inputs, norm_index)
    trades, equity, metrics = replay_proxy(inputs, cards)
    closeout = closeout_rows(symbols, ledger, capability, features, metrics)

    write_csv(OUT_DIR / "task2121_provider_capability_gate.csv", capability)
    write_csv(OUT_DIR / "task2122_api_call_ledger.csv", ledger)
    write_csv(OUT_DIR / "task2123_api_normalized_sources.csv", normalized)
    write_csv(OUT_DIR / "task2124_l1_api_proxy_features.csv", features)
    write_csv(OUT_DIR / "task2125_l2_api_proxy_semantics.csv", semantics)
    write_csv(OUT_DIR / "task2126_l3_api_proxy_edges.csv", edges)
    write_csv(OUT_DIR / "task2127_l4_api_proxy_score_cards.csv", cards)
    write_csv(OUT_DIR / "task2128_api_proxy_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2129_api_proxy_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2130_api_proxy_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2150_closeout.csv", closeout)
    write_json(OUT_DIR / "task2150_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics[0])
    update_registry()
    update_operating_state(closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        "[TASK2121_2150_OK] "
        f"symbols={closeout[0]['scope_symbols']} calls={closeout[0]['api_call_rows']} "
        f"downloaded_or_reused={closeout[0]['downloaded_or_reused_rows']} blocked={closeout[0]['blocked_rows']} "
        f"final={closeout[0]['best_final_equity']} cagr={closeout[0]['best_cagr']} mdd={closeout[0]['best_max_drawdown']}"
    )


if __name__ == "__main__":
    main()
