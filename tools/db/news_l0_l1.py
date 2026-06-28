from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Mapping

from src.data.env_loader import load_repo_env
from tools.db.source_acquisition.secret_redaction import mask_secret, redact_text


READY_DISCOVERY_ONLY = "READY_DISCOVERY_ONLY"
READY_DIAGNOSTIC_ONLY = "READY_DIAGNOSTIC_ONLY"
BLOCKED = "BLOCKED"

NEWS_PROVIDER_SPECS = {
    "official_public_releases": {
        "provider_role": "official_primary",
        "authority_class": "official_primary",
        "l1_ready_status": READY_DIAGNOSTIC_ONLY,
        "trade_authority_flag": 0,
    },
    "gdelt_news_events": {
        "provider_role": "news_discovery_proxy",
        "authority_class": "discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
    "marketaux_news_free": {
        "provider_role": "licensed_news_metadata_proxy",
        "authority_class": "metadata_discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
    "public_headline_browser_watch": {
        "provider_role": "public_headline_browser_watch",
        "authority_class": "headline_discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
    "public_newswire_feeds": {
        "provider_role": "public_newswire_feeds",
        "authority_class": "headline_discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
    "public_context_news_feeds": {
        "provider_role": "public_context_news_feeds",
        "authority_class": "macro_context_discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
    "public_market_macro_news_feeds": {
        "provider_role": "public_market_macro_news_feeds",
        "authority_class": "macro_context_discovery_only",
        "l1_ready_status": READY_DISCOVERY_ONLY,
        "trade_authority_flag": 0,
    },
}

MARKETAUX_ENV_PATH = Path("configs/local/marketaux.env")
MARKETAUX_USAGE_LEDGER = Path("data/artifacts/l0_source_acquisition/marketaux_daily_request_ledger.csv")
MARKETAUX_DAILY_REQUEST_LIMIT = 95
MARKETAUX_ARTICLES_PER_REQUEST_LIMIT = 3
MARKETAUX_INITIAL_OPERATOR_CADENCE_MINUTES = 15

GDELT_MAX_RECORDS = 25
GDELT_TIMESPAN_MINUTES = 15
GDELT_REQUEST_INTERVAL_SECONDS = 900
GDELT_COOLDOWN_MINUTES = 15
GDELT_BLOCK_STATE_PATH = Path("data/artifacts/l0_source_acquisition/gdelt_cooldown_state.json")


@dataclass(frozen=True)
class NewsL1Evaluation:
    provider: str
    provider_role: str
    authority_class: str
    promotion_status: str
    quality_flags: tuple[str, ...]
    trade_authority_flag: int
    diagnostic_only_flag: int = 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_role": self.provider_role,
            "authority_class": self.authority_class,
            "promotion_status": self.promotion_status,
            "quality_flags": "|".join(self.quality_flags),
            "trade_authority_flag": self.trade_authority_flag,
            "diagnostic_only_flag": self.diagnostic_only_flag,
        }


def evaluate_news_l1_row(row: Mapping[str, Any]) -> NewsL1Evaluation:
    provider = _provider_name(row)
    spec = NEWS_PROVIDER_SPECS.get(provider, {})
    flags = _quality_flags(row)
    if flags:
        status = BLOCKED
    else:
        status = str(spec.get("l1_ready_status", BLOCKED))
        if status == READY_DISCOVERY_ONLY:
            flags.append("non_authority_discovery_source")
    return NewsL1Evaluation(
        provider=provider,
        provider_role=str(spec.get("provider_role", "unknown")),
        authority_class=str(spec.get("authority_class", "unknown")),
        promotion_status=status,
        quality_flags=tuple(flags),
        trade_authority_flag=int(spec.get("trade_authority_flag", 0)),
    )


def _provider_name(row: Mapping[str, Any]) -> str:
    for key in ("provider", "source_family", "source_name"):
        value = str(row.get(key, "")).strip()
        if value in NEWS_PROVIDER_SPECS:
            return value
    return ""


def _quality_flags(row: Mapping[str, Any]) -> list[str]:
    flags: list[str] = []
    if not _provider_name(row):
        flags.append("unknown_provider")
    if not _first_present(row, ("published_at", "publication_time", "published_ts", "event_time")):
        flags.append("missing_publication_time")
    if not _first_present(row, ("source_url", "url", "article_url", "canonical_url")):
        flags.append("missing_source_url")
    if not _first_present(row, ("title", "headline")):
        flags.append("missing_title")
    if _entity_mapping_required(row) and not _has_entity_mapping(row):
        flags.append("missing_entity_or_ticker_mapping")
    return flags


def _first_present(row: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return ""


def _has_entity_mapping(row: Mapping[str, Any]) -> bool:
    for key in ("symbols", "tickers", "entities", "entity_map"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (list, tuple, set)) and len(value) > 0:
            return True
        if isinstance(value, dict) and len(value) > 0:
            return True
    return False


def _entity_mapping_required(row: Mapping[str, Any]) -> bool:
    provider = _provider_name(row)
    if provider in {"public_context_news_feeds", "public_market_macro_news_feeds"}:
        return False
    value = row.get("ticker_mapping_required_flag")
    if value in (0, "0", False):
        return False
    if row.get("macro_context_candidate_flag") in (1, "1", True):
        return False
    return True


def load_marketaux_token(env: Mapping[str, str] | None = None, *, env_path: Path = MARKETAUX_ENV_PATH) -> str:
    source = env if env is not None else os.environ
    token = source.get("MARKETAUX_API_KEY") or source.get("MARKETAUX_TOKEN") or ""
    if token:
        return token
    if env is None:
        load_repo_env()
        token = os.environ.get("MARKETAUX_API_KEY") or os.environ.get("MARKETAUX_TOKEN") or ""
        if token:
            return token
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in {"MARKETAUX_API_KEY", "MARKETAUX_TOKEN"}:
                return value.strip().strip("'\"")
    return ""


def marketaux_token_audit(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    token = load_marketaux_token(env)
    return {
        "present": bool(token),
        "masked": mask_secret(token),
        "secret_value_logged_flag": 0,
    }


def redact_provider_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in metadata.items():
        lower = str(key).lower()
        if any(term in lower for term in ("token", "api_key", "apikey", "secret", "authorization")):
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = redact_text(value)
    return redacted


def marketaux_request_allowed(
    *,
    ledger_path: Path = MARKETAUX_USAGE_LEDGER,
    daily_limit: int = MARKETAUX_DAILY_REQUEST_LIMIT,
    asof_date: date | None = None,
) -> bool:
    rows = _read_marketaux_ledger(ledger_path)
    day = (asof_date or datetime.now(UTC).date()).isoformat()
    used = sum(int(row.get("request_count", "0") or 0) for row in rows if row.get("request_date") == day)
    return used < int(daily_limit)


def record_marketaux_request(
    *,
    ledger_path: Path = MARKETAUX_USAGE_LEDGER,
    request_count: int = 1,
    asof: datetime | None = None,
) -> None:
    ts = asof or datetime.now(UTC)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    exists = ledger_path.exists()
    with ledger_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["request_date", "request_ts_utc", "request_count"])
        if not exists:
            writer.writeheader()
        writer.writerow({"request_date": ts.date().isoformat(), "request_ts_utc": ts.isoformat().replace("+00:00", "Z"), "request_count": int(request_count)})


def _read_marketaux_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
