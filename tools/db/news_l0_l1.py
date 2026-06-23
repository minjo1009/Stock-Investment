from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


NEWS_SOURCE_FAMILIES = frozenset(
    {
        "official_public_releases",
        "gdelt_news_events",
        "marketaux_news_free",
    }
)

FAMILY_DEFAULT_PROVIDER = {
    "official_public_releases": "official_public_release",
    "gdelt_news_events": "gdelt_doc_api",
    "marketaux_news_free": "marketaux_free_api",
}

FAMILY_AUTHORITY_CLASS = {
    "official_public_releases": "official_primary",
    "gdelt_news_events": "news_discovery_proxy",
    "marketaux_news_free": "licensed_news_metadata_proxy",
}


@dataclass(frozen=True)
class NewsProviderSpec:
    source_family: str
    provider: str
    authority_class: str
    default_enabled: bool
    requires_network: bool
    requires_api_key: bool
    license_note: str


@dataclass(frozen=True)
class NormalizedNewsBundle:
    raw_items: list[dict[str, Any]]
    clusters: list[dict[str, Any]]
    entity_maps: list[dict[str, Any]]
    l1_events: list[dict[str, Any]]
    max_source_ts: str
    provider: str


PROVIDER_SPECS = {
    "official_public_releases": NewsProviderSpec(
        source_family="official_public_releases",
        provider="official_public_release",
        authority_class="official_primary",
        default_enabled=False,
        requires_network=True,
        requires_api_key=False,
        license_note="Official public release RSS/API pages only; store source URL and source time.",
    ),
    "gdelt_news_events": NewsProviderSpec(
        source_family="gdelt_news_events",
        provider="gdelt_doc_api",
        authority_class="news_discovery_proxy",
        default_enabled=False,
        requires_network=True,
        requires_api_key=False,
        license_note="GDELT is discovery metadata, not authority for original article truth.",
    ),
    "marketaux_news_free": NewsProviderSpec(
        source_family="marketaux_news_free",
        provider="marketaux_free_api",
        authority_class="licensed_news_metadata_proxy",
        default_enabled=False,
        requires_network=True,
        requires_api_key=True,
        license_note="Marketaux free API metadata only; respect account quota and terms.",
    ),
}


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _first_text(row: dict[str, Any], names: tuple[str, ...], default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return default


def _split_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        values = [str(item).strip() for item in value]
    else:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                values = [str(item).strip() for item in parsed]
            else:
                values = re.split(r"[;,|]", text)
        else:
            values = re.split(r"[;,|]", text)
    return [value for value in values if value]


def _parse_ts(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonicalize_url(url: str) -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    parts = urlsplit(text)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}
    ]
    netloc = parts.netloc.lower()
    path = re.sub(r"/+$", "", parts.path or "/")
    return urlunsplit((parts.scheme.lower() or "https", netloc, path, urlencode(query), ""))


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", str(title or "").strip().lower())


def _json_list(values: list[str]) -> str:
    return json.dumps(sorted({value for value in values if value}), sort_keys=True)


def _quality_status(
    *,
    publication_ts: str,
    title: str,
    source_url: str,
    tickers: list[str],
    entities: list[str],
    source_family: str,
) -> tuple[list[str], str, str, str]:
    flags: list[str] = []
    if not publication_ts:
        flags.append("missing_publication_time")
    if not title:
        flags.append("missing_title")
    if not source_url:
        flags.append("missing_source_url")
    if not tickers and not entities:
        flags.append("unmapped_entities")
    if source_family != "official_public_releases":
        flags.append("non_authority_discovery_source")
    if flags:
        return flags, "BLOCKED", "L1_NEWS_EVENT_QUALITY_GATE_CLOSED", ",".join(flags)
    return flags, "READY_DIAGNOSTIC_ONLY", "", ""


def normalize_news_records(
    records: list[dict[str, Any]],
    *,
    source_family: str,
    provider: str,
    capture_ts: str,
    raw_path: str,
    raw_sha: str,
    raw_receipt_id: str,
) -> NormalizedNewsBundle:
    if source_family not in NEWS_SOURCE_FAMILIES:
        raise ValueError(f"unknown news source family: {source_family}")
    if not provider:
        provider = FAMILY_DEFAULT_PROVIDER[source_family]

    raw_items: list[dict[str, Any]] = []
    clusters_by_id: dict[str, dict[str, Any]] = {}
    entity_maps: list[dict[str, Any]] = []
    l1_events: list[dict[str, Any]] = []
    max_source_ts = ""

    for index, row in enumerate(records):
        normalized_row = {str(key).strip().lower(): value for key, value in row.items()}
        item_provider = _first_text(normalized_row, ("provider", "source", "source_name"), provider)
        provider_item_id = _first_text(normalized_row, ("provider_item_id", "id", "guid", "uuid"), f"row-{index}")
        source_url = canonicalize_url(_first_text(normalized_row, ("source_url", "url", "link", "article_url")))
        canonical_url = canonicalize_url(_first_text(normalized_row, ("canonical_url", "resolved_url"), source_url))
        title = _first_text(normalized_row, ("title", "headline", "name"))
        summary = _first_text(normalized_row, ("body_or_summary", "summary", "description", "body", "content"))
        publication_ts = _parse_ts(
            _first_text(normalized_row, ("publication_ts", "published_at", "published", "seendate", "datetime"))
        )
        collection_ts = _parse_ts(_first_text(normalized_row, ("collection_ts", "collected_at"), capture_ts)) or capture_ts
        publisher = _first_text(normalized_row, ("publisher", "domain", "source_domain", "source_name"))
        author = _first_text(normalized_row, ("author", "byline"))
        language = _first_text(normalized_row, ("language", "lang"), "unknown")
        tickers = [value.upper() for value in _split_values(_first_text(normalized_row, ("tickers", "symbols", "symbol")))]
        entities = _split_values(_first_text(normalized_row, ("entities", "entity", "company", "organization")))
        event_type = _first_text(normalized_row, ("event_type", "category"), "news_publication")
        event_subtype = _first_text(normalized_row, ("event_subtype", "subcategory"), "")
        keywords = _split_values(_first_text(normalized_row, ("keywords", "themes", "tags")))

        identity = "|".join(
            [
                source_family,
                item_provider,
                provider_item_id,
                canonical_url,
                normalize_title(title),
                publication_ts[:10],
            ]
        )
        raw_hash = _digest_text(identity + "|" + raw_sha)
        raw_item_id = f"news_raw:{source_family}:{raw_hash[:20]}"
        primary_ticker = tickers[0] if tickers else ""
        primary_entity = entities[0] if entities else primary_ticker
        event_hash = _digest_text(
            "|".join([source_family, normalize_title(title), publication_ts[:10], primary_ticker, primary_entity])
        )
        event_id = f"news_event:{event_hash[:20]}"
        cluster_id = f"news_cluster:{event_hash[:16]}"
        quality_flags, promotion_status, blocker_code, blocker_reason = _quality_status(
            publication_ts=publication_ts,
            title=title,
            source_url=source_url,
            tickers=tickers,
            entities=entities,
            source_family=source_family,
        )
        max_source_ts = max(max_source_ts, publication_ts or collection_ts)

        raw_items.append(
            {
                "raw_item_id": raw_item_id,
                "source_family": source_family,
                "provider": item_provider,
                "provider_item_id": provider_item_id,
                "source_url": source_url,
                "canonical_url": canonical_url,
                "title": title,
                "body_or_summary": summary,
                "publication_ts": publication_ts,
                "collection_ts": collection_ts,
                "publisher": publisher,
                "author": author,
                "language": language,
                "raw_hash": raw_hash,
                "raw_receipt_id": raw_receipt_id,
                "raw_path": raw_path,
                "terms_or_license_note": PROVIDER_SPECS[source_family].license_note,
                "provider_metadata_json": json.dumps(
                    {
                        "authority_class": FAMILY_AUTHORITY_CLASS[source_family],
                        "raw_row_index": index,
                        "source_family": source_family,
                    },
                    sort_keys=True,
                ),
            }
        )
        cluster = clusters_by_id.setdefault(
            cluster_id,
            {
                "dedupe_group_id": cluster_id,
                "canonical_event_hash": event_hash,
                "normalized_title": normalize_title(title),
                "primary_entity": primary_entity,
                "primary_ticker": primary_ticker,
                "publication_date": publication_ts[:10] if publication_ts else "",
                "source_count": 0,
                "providers_seen": set(),
                "first_seen_at": collection_ts,
                "last_seen_at": collection_ts,
            },
        )
        cluster["source_count"] = int(cluster["source_count"]) + 1
        cluster["providers_seen"].add(item_provider)
        cluster["first_seen_at"] = min(str(cluster["first_seen_at"]), collection_ts)
        cluster["last_seen_at"] = max(str(cluster["last_seen_at"]), collection_ts)

        subjects = [(entity, "", index == 0) for index, entity in enumerate(entities)]
        subjects.extend((ticker, ticker, not entities and idx == 0) for idx, ticker in enumerate(tickers))
        if not subjects:
            subjects = [("", "", True)]
        for map_index, (entity_name, ticker, is_primary) in enumerate(subjects):
            map_id = f"news_entity:{_digest_text(raw_item_id + entity_name + ticker + str(map_index))[:20]}"
            entity_maps.append(
                {
                    "map_id": map_id,
                    "raw_item_id": raw_item_id,
                    "event_id": event_id,
                    "entity_name_raw": entity_name,
                    "entity_type": "ticker" if ticker else "organization",
                    "ticker": ticker,
                    "mapping_method": "provider_metadata" if entity_name or ticker else "missing",
                    "mapping_confidence": 1.0 if entity_name or ticker else 0.0,
                    "is_primary_subject": int(is_primary),
                    "needs_review": int(not ticker and not entity_name),
                }
            )

        l1_events.append(
            {
                "event_id": event_id,
                "raw_item_id": raw_item_id,
                "dedupe_group_id": cluster_id,
                "source_family": source_family,
                "provider": item_provider,
                "publication_time": publication_ts,
                "event_time": publication_ts,
                "normalized_title": normalize_title(title),
                "normalized_summary": summary,
                "event_type": event_type,
                "event_subtype": event_subtype,
                "affected_tickers_json": _json_list(tickers),
                "affected_entities_json": _json_list(entities),
                "entity_roles_json": json.dumps({"primary": primary_entity, "primary_ticker": primary_ticker}, sort_keys=True),
                "keywords_json": _json_list(keywords),
                "source_count": 1,
                "confidence": 0.0 if promotion_status == "BLOCKED" else 0.5,
                "freshness_status": "UNCERTIFIED",
                "evidence_score": 0.0 if promotion_status == "BLOCKED" else 0.5,
                "contradiction_flag": 0,
                "missing_fields_json": _json_list([flag for flag in quality_flags if flag.startswith("missing_")]),
                "quality_flags_json": _json_list(quality_flags),
                "provider_lineage_json": json.dumps(
                    {
                        "source_family": source_family,
                        "provider": item_provider,
                        "authority_class": FAMILY_AUTHORITY_CLASS[source_family],
                        "raw_receipt_id": raw_receipt_id,
                    },
                    sort_keys=True,
                ),
                "promotion_status": promotion_status,
                "blocker_code": blocker_code,
                "blocker_reason": blocker_reason,
            }
        )

    clusters = []
    for cluster in clusters_by_id.values():
        cluster = dict(cluster)
        cluster["providers_seen_json"] = _json_list(list(cluster.pop("providers_seen")))
        clusters.append(cluster)
    return NormalizedNewsBundle(
        raw_items=raw_items,
        clusters=clusters,
        entity_maps=entity_maps,
        l1_events=l1_events,
        max_source_ts=max_source_ts or capture_ts,
        provider=provider,
    )
