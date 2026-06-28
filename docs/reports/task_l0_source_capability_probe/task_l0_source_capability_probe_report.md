# Decision Summary

- Verdict: `PRIMARY_PASS`; `source_capability_probe` was implemented and real-network smoke succeeded, then expanded beyond newswire sources.
- Strategy acceptance status: `NOT_ACCEPTED`; this is L0 data-source infrastructure only.
- Key metrics: original smoke covered 4 sources; external expansion smoke covered 8 additional candidates with 6 `rss_or_atom`, 1 `api_or_official_index`, and 1 `blocked_or_manual_review`.
- What changed: added a source capability registry, probe engine, CLI wrapper, tests, raw evidence capture, event ledger, summary artifact, disabled diagnostic scheduler job, same-origin robots guard, and external market/macro headline candidates.
- Next action: promote the viable external candidates into a governed RSS/API collector before using Chrome crawling.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Implement a source capability probe that decides whether each free public news source should be collected by API/index, RSS/Atom, sitemap, JSON-LD/meta, static HTML, or Chrome fallback. |
| Target Metrics | Probe SEC, PRNewswire, GlobeNewswire, BusinessWire, and external market/macro headline candidates; write raw evidence; produce source-level recommended capture modes; validate with tests. |
| Forbidden Actions | No login, paywall, captcha bypass, stealth/proxy evasion, GPT-created headlines, ticker inference, trading output, or deployment claim. |
| Available Raw Sources | Public source URLs in `configs/source_registry/l0_public_news_capability_sources.json`; prior Chrome smoke; existing L0/L2 governance; CNBC, MarketWatch, Investing.com, BBC, FT, Nasdaq Trader, Guardian Open Platform, and Google News candidate routes. |
| Missing Raw Sources | Actual extractor cascade and source-date queue are not yet implemented. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_source_capability_probe/` |
| Large Artifact Directory | `data/artifacts/task_l0_source_capability_probe/` |
| Validation | `python -m unittest tests.test_l0_source_capability_probe`; `python scripts/run_l0_source_capability_probe.py`; registry and closeout validators. |
| Completion Criteria | Probe runs on real public sources and produces actionable capture-mode recommendations. |

# Quant Expert Report

## Data Source And Source Readiness

The probe checks each source in a cascade:

1. robots.txt and sitemap hints
2. configured API/index URLs
3. configured RSS/feed URLs
4. configured sitemap URLs
5. static probe page HTML
6. JSON-LD/meta and static article links
7. Chrome fallback need

Smoke result:

| Source | Recommended Mode | Key Finding |
|---|---|---|
| `sec_edgar` | `api_or_official_index` | SEC API/daily index route is available; browser unnecessary. |
| `prnewswire` | `rss_or_atom` | Feed route and sitemaps are available; static page also exposes article links. |
| `globenewswire` | `rss_or_atom` | Feed route and sitemaps are available; static page exposes article links. |
| `businesswire` | `rss_or_atom` | Robots-disallowed feed-options page is skipped; public RSS/sitemap evidence remains available and avoids the prior headless Chrome HTTP2 issue. |

External candidate expansion smoke:

| Source | Recommended Mode | Smoke Evidence | Decision |
|---|---|---:|---|
| `cnbc_public_rss` | `rss_or_atom` | 120 feed items across 4 feeds; sitemap evidence present | High priority live headline watcher |
| `investing_public_rss` | `rss_or_atom` | 30 feed items across stock/economy feeds | High priority live headline watcher |
| `bbc_public_rss` | `rss_or_atom` | 81 feed items across business/world feeds | Medium priority macro context watcher |
| `ft_public_rss` | `rss_or_atom` | 25 feed items; sitemap evidence present | Medium priority headline-only watcher; no full text |
| `nasdaq_trader_notices` | `rss_or_atom` | 45 feed items | High priority official market-structure watcher |
| `marketwatch_public_rss` | `rss_or_atom` | 50 feed items; sitemap evidence present | Medium priority; feed staleness must be monitored |
| `guardian_open_platform` | `api_or_official_index` | 2016 API query returned historical rows | High priority historical macro/news backfill prototype |
| `google_news_business_rss` | `blocked_or_manual_review` | RSS routes skipped by robots guard | Do not promote to regular collector |

This materially reduces reliance on fragile selectors. Chrome should remain fallback only. The external expansion also showed that Google News should not be promoted under current governance: direct RSS can respond, but the same-origin robots guard skips the configured RSS routes.

## Exact Join Keys

- Source capability key: `source_key`.
- Raw evidence key: `provider`, `source_key`, `capability`, `captured_at`, `body_sha256`.
- Future collector route key: `source_key`, `recommended_capture_mode`, `source_url`.

## Leakage Audit

No market labels, returns, lifecycle IDs, orders, fills, or future outcome fields are read. This task does not produce strategy features. It only classifies source acquisition routes.

## Hallucination Audit

No GPT-generated rows are created. Every capability result is based on fetched raw bytes saved under `data/raw/l0_source_capability_probe/` with metadata and hashes.

The probe now skips configured same-origin URLs that are disallowed by robots.txt and records them as `skipped_by_robots` instead of fetching them.

## Split/OOS Metrics

Not applicable. This is source acquisition infrastructure.

## Cost/Slippage Stress

Not applicable. No PnL or execution claim is made.

## Remaining Blockers

- Build the actual RSS/API/sitemap/JSON-LD/static extractor cascade.
- Promote the viable external sources to a separate public market/macro headline collector: CNBC, Investing.com, BBC, FT, Nasdaq Trader, MarketWatch, and Guardian.
- Build source-date queue generation from the probe results, with Guardian Open Platform first for 2016+ historical backfill feasibility.
- Add deterministic entity/ticker mapper after collection.
- Add periodic progress/status integration if this becomes a background collector.

# No-Background Decision-Maker Report

We built the tool that decides how each free news source should be collected, and expanded it beyond the three newswires.

The important result: **we do not need Chrome first** for the initial target sources. SEC and Guardian should use API/index routes. PRNewswire, GlobeNewswire, BusinessWire, CNBC, Investing.com, BBC, FT, Nasdaq Trader, and MarketWatch should start with RSS/feed routes. Chrome remains useful, but only as fallback.

That makes the free news plan more stable, less fragile, and less exposed to selector/captcha problems.

The best next source additions are CNBC, Investing.com, Nasdaq Trader, and Guardian. Google News is not a regular collector candidate under the current robots guard.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
