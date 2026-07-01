from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data.alpaca_historical_microstructure_export import AlpacaHistoricalMicrostructureProvider  # noqa: E402
from tools.db.news_l0_l1 import (  # noqa: E402
    MARKETAUX_ARTICLES_PER_REQUEST_LIMIT,
    evaluate_news_l1_row,
    load_marketaux_token,
    marketaux_request_allowed,
    record_marketaux_request,
)
from tools.db.source_acquisition.news_registry_loader import (  # noqa: E402
    GDELT_REGISTRY_PATH,
    MARKETAUX_REGISTRY_PATH,
    enabled_official_sources,
    load_registry,
)
from tools.db.source_acquisition.secret_redaction import redact_text  # noqa: E402


TASK_ID = "TASK-4119"
DEFAULT_OUT_DIR = ROOT / "docs/reports/task_4119_l0_stage_1_bounded_network_smoke_execution"
DEFAULT_SYMBOL = "AAPL"
DEFAULT_ALPACA_START = "2024-01-03T15:30:00Z"
DEFAULT_ALPACA_END = "2024-01-03T15:31:00Z"
REQUEST_TIMEOUT_SECONDS = 45


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> str:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    path.write_text(text, encoding="utf-8")
    return sha256_file(path)


def classify_error(exc: Exception) -> tuple[str, str, str]:
    if isinstance(exc, HTTPError):
        if exc.code in {401, 403}:
            return "BLOCKED", "AUTH_OR_ACCESS_BLOCKED", f"HTTP {exc.code}"
        if exc.code == 429:
            return "BLOCKED", "RATE_LIMITED", "HTTP 429"
        return "FAILED_RETRYABLE", "HTTP_ERROR", f"HTTP {exc.code}"
    if isinstance(exc, TimeoutError):
        return "FAILED_RETRYABLE", "TIMEOUT", type(exc).__name__
    if isinstance(exc, URLError):
        return "FAILED_RETRYABLE", "URL_ERROR", str(exc.reason)
    if isinstance(exc, RuntimeError) and "credentials" in str(exc).lower():
        return "BLOCKED", "CREDENTIAL_BLOCKED", "credentials missing"
    return "FAILED_RETRYABLE", type(exc).__name__, str(exc)


def request_bytes(url: str, *, headers: dict[str, str] | None = None) -> tuple[int, bytes, dict[str, str]]:
    request_headers = {"User-Agent": "Codex-L0-Stage1-Network-Smoke/1.0"}
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
        return int(response.status), response.read(), dict(response.headers.items())


def response_summary_bytes(*, provider: str, source_id: str, url: str, status_code: int, data: bytes, headers: dict[str, str]) -> dict[str, Any]:
    text = data[:8192].decode("utf-8", errors="ignore")
    return {
        "provider": provider,
        "source_id": source_id,
        "url": redact_text(url),
        "status_code": status_code,
        "byte_count": len(data),
        "content_type": headers.get("Content-Type", ""),
        "response_sha256": hashlib.sha256(data).hexdigest(),
        "text_preview": redact_text(text),
        "captured_at": now_z(),
        "secret_value_logged_flag": 0,
    }


def official_network_smoke(out_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sources = enabled_official_sources()
    source = next((item for item in sources if str(item.get("source_type")) == "rss"), sources[0] if sources else None)
    if source is None:
        return event("official_public_releases", "official", "BLOCKED", "NO_ENABLED_SOURCE", "no enabled official source"), []
    source_id = str(source.get("source_id", "official"))
    url = str(source.get("url", ""))
    try:
        status_code, data, headers = request_bytes(url)
        summary = response_summary_bytes(provider="official_public_releases", source_id=source_id, url=url, status_code=status_code, data=data, headers=headers)
        raw_path = (out_dir / "raw_summaries" / "official_public_releases" / f"{source_id}.json").resolve()
        raw_sha = write_json(raw_path, summary)
        row = {
            "provider": "official_public_releases",
            "published_at": now_z(),
            "source_url": url,
            "title": f"network smoke {source_id}",
            "symbols": source.get("symbol_scope") or source.get("macro_scope") or ["MACRO"],
        }
        return event("official_public_releases", source_id, "EXPORTED", "", "official endpoint reachable", raw_path, raw_sha, 1), [source_packet(row, raw_path, raw_sha, "official_primary_network_smoke")]
    except Exception as exc:  # noqa: BLE001
        status, category, message = classify_error(exc)
        return event("official_public_releases", source_id, status, category, message, network_call_made=1), []


def gdelt_network_smoke(out_dir: Path, symbol: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    registry = load_registry(GDELT_REGISTRY_PATH)
    query_template = str(registry.get("queries", [{}])[0].get("query_template", "\"{symbol}\""))
    query = query_template.replace("{symbol}", symbol)
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(min(int(registry.get("max_records", 25)), 1)),
        "timespan": f"{int(registry.get('timespan_minutes', 15))}m",
        "sort": "DateDesc",
    }
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?{urlencode(params)}"
    try:
        status_code, data, headers = request_bytes(url)
        try:
            payload = json.loads(data.decode("utf-8")) if data else {}
        except json.JSONDecodeError:
            payload = {}
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        summary = response_summary_bytes(provider="gdelt_news_events", source_id=symbol, url=url, status_code=status_code, data=data, headers=headers)
        summary["article_count"] = len(articles)
        summary["json_parse_status"] = "PASS" if payload else "EMPTY_OR_NON_JSON"
        raw_path = (out_dir / "raw_summaries" / "gdelt_news_events" / f"{symbol}.json").resolve()
        raw_sha = write_json(raw_path, summary)
        packets = []
        for idx, article in enumerate(articles[:1], start=1):
            if isinstance(article, dict):
                row = {
                    "provider": "gdelt_news_events",
                    "published_at": article.get("seendate") or article.get("date") or now_z(),
                    "source_url": article.get("url") or "",
                    "title": article.get("title") or f"GDELT smoke article {idx}",
                    "symbols": [symbol],
                }
                packets.append(source_packet(row, raw_path, raw_sha, "gdelt_discovery_network_smoke"))
        status = "EXPORTED" if packets else "EMPTY_PROVIDER_RESPONSE"
        return event("gdelt_news_events", symbol, status, "", f"gdelt endpoint reachable; rows={len(packets)}", raw_path, raw_sha, 1), packets
    except Exception as exc:  # noqa: BLE001
        status, category, message = classify_error(exc)
        return event("gdelt_news_events", symbol, status, category, message, network_call_made=1), []


def marketaux_network_smoke(out_dir: Path, symbol: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    token = load_marketaux_token()
    if not token:
        return event("marketaux_news_free", symbol, "BLOCKED", "CREDENTIAL_BLOCKED", "Marketaux token missing"), []
    registry = load_registry(MARKETAUX_REGISTRY_PATH)
    daily_cap = int(registry.get("daily_request_cap", 95))
    if not marketaux_request_allowed(daily_limit=daily_cap):
        return event("marketaux_news_free", symbol, "BLOCKED", "DAILY_REQUEST_CAP_REACHED", "Marketaux daily request cap reached"), []
    params = {
        "symbols": symbol,
        "limit": str(min(int(registry.get("articles_per_request", 3)), MARKETAUX_ARTICLES_PER_REQUEST_LIMIT, 1)),
        "language": "en",
        "api_token": token,
    }
    safe_params = dict(params)
    safe_params["api_token"] = "***REDACTED***"
    url = f"https://api.marketaux.com/v1/news/all?{urlencode(params)}"
    safe_url = f"https://api.marketaux.com/v1/news/all?{urlencode(safe_params)}"
    try:
        status_code, data, headers = request_bytes(url)
        record_marketaux_request(request_count=1)
        try:
            payload = json.loads(data.decode("utf-8")) if data else {}
        except json.JSONDecodeError:
            payload = {}
        articles = payload.get("data", []) if isinstance(payload, dict) else []
        summary = response_summary_bytes(provider="marketaux_news_free", source_id=symbol, url=safe_url, status_code=status_code, data=data, headers=headers)
        summary["article_count"] = len(articles)
        summary["json_parse_status"] = "PASS" if payload else "EMPTY_OR_NON_JSON"
        raw_path = (out_dir / "raw_summaries" / "marketaux_news_free" / f"{symbol}.json").resolve()
        raw_sha = write_json(raw_path, summary)
        packets = []
        for idx, article in enumerate(articles[:1], start=1):
            if isinstance(article, dict):
                row = {
                    "provider": "marketaux_news_free",
                    "published_at": article.get("published_at") or now_z(),
                    "source_url": article.get("url") or "",
                    "title": article.get("title") or f"Marketaux smoke article {idx}",
                    "symbols": [symbol],
                }
                packets.append(source_packet(row, raw_path, raw_sha, "marketaux_metadata_network_smoke"))
        status = "EXPORTED" if packets else "EMPTY_PROVIDER_RESPONSE"
        return event("marketaux_news_free", symbol, status, "", f"marketaux endpoint reachable; rows={len(packets)}", raw_path, raw_sha, 1), packets
    except Exception as exc:  # noqa: BLE001
        status, category, message = classify_error(exc)
        return event("marketaux_news_free", symbol, status, category, message, network_call_made=1), []


def alpaca_microstructure_smoke(out_dir: Path, symbol: str, *, feed: str, start: str, end: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    try:
        provider = AlpacaHistoricalMicrostructureProvider(feed=feed, page_limit=50)
        quote_frame = provider.fetch_quotes(symbol, start=start, end=end)
        trade_frame = provider.fetch_trades(symbol, start=start, end=end)
        for kind, frame, ts_col in [("quotes", quote_frame, "quote_ts"), ("trades", trade_frame, "trade_ts")]:
            raw_path = (out_dir / "raw_summaries" / "microstructure" / f"{symbol}_{kind}.csv").resolve()
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            frame.head(5).to_csv(raw_path, index=False, encoding="utf-8")
            raw_sha = sha256_file(raw_path)
            status = "EXPORTED" if len(frame) else "EMPTY_PROVIDER_RESPONSE"
            events.append(event(f"microstructure_{kind}", symbol, status, "", f"alpaca {kind} endpoint reachable; rows={len(frame)}", raw_path, raw_sha, 1))
            if len(frame):
                first = frame.iloc[0].to_dict()
                packets.append(
                    {
                        "task_id": TASK_ID,
                        "source_packet_id": f"{TASK_ID}:microstructure_{kind}:{symbol}:network_smoke",
                        "candidate_id": "",
                        "trade_spec_id": "",
                        "symbol": symbol,
                        "decision_asof_ts": now_z(),
                        "provider": "alpaca",
                        "endpoint_or_source_family": f"microstructure_{kind}",
                        "source_ts": str(first.get(ts_col, "")),
                        "available_to_brain_ts": now_z(),
                        "source_time_basis": "provider_timestamp_capture_time_not_strict_certified",
                        "source_time_certified": 0,
                        "raw_path": rel(raw_path),
                        "raw_sha256": raw_sha,
                        "strict_gate_pass": 0,
                        "proxy_feature_allowed": 0,
                        "missing_source_is_negative": 0,
                        "assignment_uses_future_outcome": 0,
                        "outcome_used_for_assignment": 0,
                        "authority": "raw_microstructure_network_smoke",
                    }
                )
    except Exception as exc:  # noqa: BLE001
        status, category, message = classify_error(exc)
        events.append(event("microstructure_quotes_trades", symbol, status, category, message, network_call_made=1))
    return events, packets


def event(
    family: str,
    source_id: str,
    status: str,
    error_category: str,
    message: str,
    raw_path: Path | None = None,
    raw_sha256: str = "",
    network_call_made: int = 0,
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "source_family": family,
        "source_id": source_id,
        "status": status,
        "error_category": error_category,
        "message": redact_text(message),
        "raw_path": "" if raw_path is None else rel(raw_path),
        "raw_sha256": raw_sha256,
        "network_call_made": int(network_call_made),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }


def source_packet(row: dict[str, Any], raw_path: Path, raw_sha256: str, authority: str) -> dict[str, Any]:
    evaluation = evaluate_news_l1_row(row)
    return {
        "task_id": TASK_ID,
        "source_packet_id": f"{TASK_ID}:{row.get('provider')}:{sha256_text(str(row))[:16]}",
        "candidate_id": "",
        "trade_spec_id": "",
        "symbol": "|".join(row.get("symbols", [])) if isinstance(row.get("symbols"), list) else str(row.get("symbols", "")),
        "decision_asof_ts": now_z(),
        "provider": row.get("provider", ""),
        "endpoint_or_source_family": row.get("provider", ""),
        "source_ts": row.get("published_at", ""),
        "available_to_brain_ts": now_z(),
        "source_time_basis": "provider_record_timestamp_or_capture_only",
        "source_time_certified": 0,
        "raw_path": rel(raw_path),
        "raw_sha256": raw_sha256,
        "strict_gate_pass": 0,
        "proxy_feature_allowed": 0,
        "missing_source_is_negative": 0,
        "assignment_uses_future_outcome": 0,
        "outcome_used_for_assignment": 0,
        "authority": authority,
        "l1_promotion_status": evaluation.promotion_status,
        "l1_quality_flags": "|".join(evaluation.quality_flags),
    }


def scope_rows(symbol: str) -> list[dict[str, Any]]:
    return [
        {
            "task_id": TASK_ID,
            "stage": 1,
            "scope": "bounded_network_smoke_execution",
            "symbols": symbol,
            "network_permission_basis": "user_goal_continue_plan_layer_01_to_6",
            "max_official_sources": 1,
            "max_gdelt_requests": 1,
            "max_marketaux_requests": 1,
            "max_alpaca_quote_windows": 1,
            "max_alpaca_trade_windows": 1,
            "db_mutation_made": 0,
            "broker_mutation_made": 0,
        }
    ]


def run_smoke(out_dir: Path, *, symbol: str, feed: str, alpaca_start: str, alpaca_end: str) -> dict[str, Any]:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []

    official_event, official_packets = official_network_smoke(out_dir)
    gdelt_event, gdelt_packets = gdelt_network_smoke(out_dir, symbol)
    marketaux_event, marketaux_packets = marketaux_network_smoke(out_dir, symbol)
    micro_events, micro_packets = alpaca_microstructure_smoke(out_dir, symbol, feed=feed, start=alpaca_start, end=alpaca_end)

    events.extend([official_event, gdelt_event, marketaux_event, *micro_events])
    packets.extend([*official_packets, *gdelt_packets, *marketaux_packets, *micro_packets])

    source_plan = [
        {"task_id": TASK_ID, "source_family": "official_public_releases", "network_smoke_bound": "one enabled official RSS/source", "status_authority": "diagnostic_only"},
        {"task_id": TASK_ID, "source_family": "gdelt_news_events", "network_smoke_bound": "one AAPL request maxrecords=1", "status_authority": "discovery_only"},
        {"task_id": TASK_ID, "source_family": "marketaux_news_free", "network_smoke_bound": "one AAPL request limit=1 when token present", "status_authority": "metadata_discovery_only"},
        {"task_id": TASK_ID, "source_family": "microstructure_quotes_trades", "network_smoke_bound": "one AAPL one-minute quotes/trades window", "status_authority": "raw_microstructure_diagnostic_only"},
    ]
    raw_classification = [
        {
            "task_id": TASK_ID,
            "source_family": item["source_family"],
            "source_id": item["source_id"],
            "raw_response_status": "CAPTURED_SUMMARY" if item.get("raw_path") else "NO_RAW_CAPTURE",
            "status": item["status"],
            "error_category": item.get("error_category", ""),
            "raw_path": item.get("raw_path", ""),
            "raw_sha256": item.get("raw_sha256", ""),
        }
        for item in events
    ]
    coverage = [
        {
            "task_id": TASK_ID,
            "coverage_name": "stage1_bounded_network_smoke",
            "network_calls_made": sum(int(item.get("network_call_made", 0)) for item in events),
            "captured_raw_summaries": sum(1 for item in events if item.get("raw_path")),
            "exported_or_empty_count": sum(1 for item in events if item.get("status") in {"EXPORTED", "EMPTY_PROVIDER_RESPONSE"}),
            "blocked_count": sum(1 for item in events if item.get("status") == "BLOCKED"),
            "failed_retryable_count": sum(1 for item in events if item.get("status") == "FAILED_RETRYABLE"),
        }
    ]
    gate = [
        {
            "task_id": TASK_ID,
            "gate": "stage1_to_stage2",
            "status": "BLOCKED_UNTIL_OPERATOR_ACCEPTS_SMOKE_RESULTS",
            "reason": "Network smoke evidence exists, but Stage 2 cadence optimization requires owner review of provider blockers and quota posture.",
            "strict_gate_opened": 0,
            "replay_permission_granted": 0,
        }
    ]
    gaps = [
        item
        for item in events
        if item.get("status") in {"BLOCKED", "FAILED_RETRYABLE"}
    ]
    write_csv(out_dir / "task_4119_scope_freeze.csv", scope_rows(symbol), list(scope_rows(symbol)[0].keys()))
    write_csv(out_dir / "task_4119_source_family_plan.csv", source_plan, list(source_plan[0].keys()))
    write_csv(out_dir / "task_4119_api_or_raw_call_ledger.csv", events, list(events[0].keys()))
    write_csv(out_dir / "task_4119_raw_response_classification.csv", raw_classification, list(raw_classification[0].keys()))
    packet_fields = [
        "task_id",
        "source_packet_id",
        "candidate_id",
        "trade_spec_id",
        "symbol",
        "decision_asof_ts",
        "provider",
        "endpoint_or_source_family",
        "source_ts",
        "available_to_brain_ts",
        "source_time_basis",
        "source_time_certified",
        "raw_path",
        "raw_sha256",
        "strict_gate_pass",
        "proxy_feature_allowed",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
        "authority",
        "l1_promotion_status",
        "l1_quality_flags",
    ]
    write_csv(out_dir / "task_4119_normalized_source_packets.csv", packets, packet_fields)
    write_csv(out_dir / "task_4119_decision_asof_coverage.csv", coverage, list(coverage[0].keys()))
    write_csv(out_dir / "task_4119_feature_admission_gate.csv", gate, list(gate[0].keys()))
    write_csv(out_dir / "task_4119_source_gap_ledger.csv", gaps, list(events[0].keys()))

    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "network_calls_made": coverage[0]["network_calls_made"],
        "captured_raw_summaries": coverage[0]["captured_raw_summaries"],
        "exported_or_empty_count": coverage[0]["exported_or_empty_count"],
        "blocked_count": coverage[0]["blocked_count"],
        "failed_retryable_count": coverage[0]["failed_retryable_count"],
        "normalized_packet_count": len(packets),
        "stage1_status": "NETWORK_SMOKE_EXECUTED_OWNER_REVIEW_PENDING",
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_json(out_dir / "stage1_network_smoke_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded L0 Stage 1 network smoke and write governed task artifacts.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--feed", default="iex", choices=["iex", "sip"])
    parser.add_argument("--alpaca-start", default=DEFAULT_ALPACA_START)
    parser.add_argument("--alpaca-end", default=DEFAULT_ALPACA_END)
    args = parser.parse_args()
    summary = run_smoke(args.out_dir, symbol=args.symbol.upper(), feed=args.feed, alpaca_start=args.alpaca_start, alpaca_end=args.alpaca_end)
    print(
        "[L0_STAGE1_BOUNDED_NETWORK_SMOKE] "
        f"status={summary['stage1_status']} network_calls={summary['network_calls_made']} "
        f"captured={summary['captured_raw_summaries']} blocked={summary['blocked_count']} "
        f"failed_retryable={summary['failed_retryable_count']} packets={summary['normalized_packet_count']} "
        "diagnostic_only=1 broker_mutation_permitted=0 real_capital_permitted=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
