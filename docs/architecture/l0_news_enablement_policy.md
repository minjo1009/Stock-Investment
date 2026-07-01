# L0 News Enablement Policy

## Decision

L0 news collection has two postures:

- `conservative_default`: all news jobs disabled, `allow_network=false`, safe for CI and public repository state.
- `operator_news_enabled_diagnostic`: a local operator override may enable official, GDELT, and Marketaux diagnostic collection while every trading gate stays closed.

The active staged roadmap is `docs/architecture/l0_source_acquisition_project_management_plan.md`.

## Provider Roles

`official_public_releases` is `official_primary`. A structurally valid row can become `READY_DIAGNOSTIC_ONLY`, but it is still not a standalone trading authority.

`gdelt_news_events` is `news_discovery_proxy`. A structurally valid row can become `READY_DISCOVERY_ONLY`. It may identify source URLs, themes, entities, or candidate evidence, but it is not original-source truth.

`marketaux_news_free` is `licensed_news_metadata_proxy`. A structurally valid row can become `READY_DISCOVERY_ONLY`. It may provide headline, article metadata, symbols, and entities, but it is not official truth.

Rows missing publication time, source URL, title, or entity/ticker mapping remain `BLOCKED`.

Additional public/newswire/context collectors recovered in TASK-4116 are Python
HTTP/RSS/API collectors unless explicitly marked as Chrome smoke. They are
managed by the six-stage L0 plan:

- Stage 1 stabilizes official/core API smoke.
- Stage 2 tunes real-time cadence and quota budgets.
- Stage 3 proves scheduler recurrence.
- Stage 4 optimizes historical backfill.
- Stage 5 runs background historical backfill from 2016 where a source supports it.
- Stage 6 audits L1 mapping and coverage before L2 handoff.

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

Newswire and public context source maintenance lives in:

- `configs/source_registry/l0_public_news_capability_sources.json`
- `configs/source_registry/l0_public_context_news_sources.json`

If OneDrive reports restored collector or registry files as unavailable, that is
a local materialization blocker before execution. It is not negative evidence
about the source and must be recorded as `UNKNOWN/BLOCKER`.

## Mapping Boundary

Ticker/entity/news mapping exists as an initial L0/L1 gate in
`tools/db/news_l0_l1.py`. It is not yet final L2-ready disambiguation. Stage 6
must audit source-time, raw reference, entity ambiguity, ticker collisions, and
macro-context bypasses before L2 handoff.
