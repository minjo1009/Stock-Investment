# L0 News Enablement Policy

## Decision

L0 news collection has two postures:

- `conservative_default`: all news jobs disabled, `allow_network=false`, safe for CI and public repository state.
- `operator_news_enabled_diagnostic`: a local operator override may enable official, GDELT, and Marketaux diagnostic collection while every trading gate stays closed.

## Provider Roles

`official_public_releases` is `official_primary`. A structurally valid row can become `READY_DIAGNOSTIC_ONLY`, but it is still not a standalone trading authority.

`gdelt_news_events` is `news_discovery_proxy`. A structurally valid row can become `READY_DISCOVERY_ONLY`. It may identify source URLs, themes, entities, or candidate evidence, but it is not original-source truth.

`marketaux_news_free` is `licensed_news_metadata_proxy`. A structurally valid row can become `READY_DISCOVERY_ONLY`. It may provide headline, article metadata, symbols, and entities, but it is not official truth.

Rows missing publication time, source URL, title, or entity/ticker mapping remain `BLOCKED`.

## Marketaux Handling

Marketaux tokens are read only from environment variables or `configs/local/marketaux.env`. Tokens must not appear in raw paths, provider metadata, URL logs, exception logs, reports, or committed config.

The initial operator posture is batch-oriented:

- preferred cadence: 120 minutes
- max articles per request: 3
- daily request cap: below free-tier limits

The request ledger is `data/artifacts/l0_source_acquisition/marketaux_daily_request_ledger.csv`.

## GDELT Handling

GDELT remains discovery-only. Broad high-frequency queries are out of scope. Cooldown and bounded-symbol behavior are the default posture.

## Source Registry

Official source maintenance lives in `configs/source_registry/l0_official_public_releases.json`. Unverified MSFT, NVDA, AMD, and QQQ/Invesco placeholders are disabled with `TODO_VERIFY_ENDPOINT` and `official_primary_candidate`.
