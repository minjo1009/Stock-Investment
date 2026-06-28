# Decision Summary

- Verdict: `PRIMARY_PASS` for research and mitigation planning; overall readiness remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this opens no trading, scoring, order, or capital gate.
- Key decision: do not promote the Chrome/Playwright crawler as a selector-first primary collector. Promote a **machine-readable-first free news L0 architecture** where RSS/Atom, sitemaps, JSON-LD/meta tags, SEC indexes/APIs, and other public structured feeds are attempted before Chrome rendering.
- What changed: the browser crawler is reframed as a fallback and verification layer, not the first extraction layer.
- Next action: implement a `source_capability_probe` and `extractor_cascade` smoke for PRNewswire, GlobeNewswire, BusinessWire, SEC, and one sitemap-enabled source before any full historical crawl.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Find ways to mitigate or replace Chrome crawler weaknesses: selector drift, terms/captcha/blocking, entity mapping risk, and historical backfill uncertainty. |
| Target Metrics | Concrete mitigation plan; source architecture; risk controls; implementation priority; project artifacts and registry row. |
| Forbidden Actions | No paid vendor assumption; no login/paywall/captcha bypass; no GPT-created headlines; no inferred ticker certainty; no full-text archive claim; no deployment claim. |
| Available Raw Sources | Existing Marketaux/GDELT/official lanes; smoke-tested PRNewswire/GlobeNewswire browser headline rows; SEC public APIs and daily index; public RSS/sitemaps/JSON-LD candidates. |
| Missing Raw Sources | Source capability registry, robots/terms posture registry, deterministic entity mapper, historical source-date queue implementation. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_free_news_source_mitigation_research/` |
| Large Artifact Directory | `data/artifacts/task_l0_free_news_source_mitigation_research/` |
| Validation | `python scripts/task_registry_validate.py`; `python scripts/operating_closeout_validate.py`; governance validators where available. |
| Completion Criteria | Research report and decision artifacts describe a feasible mitigation/replacement path and update the task registry. |

# Quant Expert Report

## Data Source And Source Readiness

The previous smoke proved that Chrome/Playwright can collect real public headlines with raw HTML, screenshot, hashes, and L2 diagnostic-only facts. It also exposed the main weakness: selector rules can capture wrong links unless constrained.

The recommended architecture is a layered free-source cascade:

1. **Structured official/API layer**: SEC EDGAR APIs and daily indexes; issuer RSS/API where available.
2. **Feed layer**: RSS/Atom feeds from PRNewswire, GlobeNewswire, BusinessWire, and other public distribution sources.
3. **Discovery index layer**: XML sitemaps, news sitemaps, page metadata, JSON-LD `NewsArticle`, Open Graph/Twitter card tags.
4. **Static HTML archive layer**: deterministic URL/page parsers for source-date listings.
5. **Chrome fallback layer**: Playwright only when the page requires JS rendering or selector validation.
6. **External public archive layer**: Common Crawl/GDELT for historical web-scale discovery where source archives are incomplete.

Research references:

- Playwright locator guidance: `https://playwright.dev/docs/locators`
- Sitemaps protocol: `https://www.sitemaps.org/protocol.html`
- robots.txt standard: `https://www.rfc-editor.org/rfc/rfc9309`
- Google article structured data guidance: `https://developers.google.com/search/docs/appearance/structured-data/article`
- schema.org `NewsArticle`: `https://schema.org/NewsArticle`
- SEC EDGAR APIs: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC daily index: `https://www.sec.gov/Archives/edgar/daily-index/`
- PRNewswire RSS: `https://www.prnewswire.com/rss/`
- Business Wire feed options: `https://www.businesswire.com/help/feed-options`
- Reuters Connect Terms: `https://www.reutersconnect.com/general-terms`
- Bloomberg Industry Terms: `https://www.bloombergindustry.com/terms-of-service-subscription-products/`

## Mitigation By Weakness

### 1. Selector Drift And Site Structure Changes

Do not rely on one DOM selector. Use an extractor cascade:

| Priority | Extractor | Why It Helps |
|---|---|---|
| 1 | RSS/Atom parser | Stable machine-readable title/link/time fields. |
| 2 | Sitemap/news sitemap URL harvest | Finds article URLs without brittle listing-page selectors. |
| 3 | JSON-LD `NewsArticle` and meta tags | Pulls headline/date/url from semantic markup. |
| 4 | Source-specific static HTML parser | Faster and less fragile than full browser if page is server-rendered. |
| 5 | Playwright DOM parser | Fallback for JS-only pages and selector drift diagnosis. |

Add controls:

- source-specific golden samples stored under `data/artifacts/source_capability_probe/`
- selector versioning and per-source row-count drift alarms
- article URL shape validation before accepting a row
- duplicate/canonical URL checks
- screenshot and raw HTML hash only for browser fallback, not every feed row

### 2. Terms, Blocking, Captcha, And Legal/Ops Risk

Use a source governance registry before long-running collection:

```text
source_id
base_url
collection_modes_allowed
robots_status
terms_posture
login_required_flag
paywall_flag
captcha_seen_flag
rate_limit_policy
store_full_text_allowed_flag
store_headline_only_flag
kill_switch_flag
```

Policy:

- Use official RSS/API/sitemap before browser.
- No login, paywall, captcha bypass, stealth evasion, or proxy rotation.
- Store headline/link/time/snippet/evidence only; do not archive full article bodies unless the source explicitly permits it.
- Reuters/Bloomberg direct browser collection remains `BLOCKED_FOR_DIRECT_COLLECTION`; aggregator-visible headline references can be `DISCOVERY_ONLY`.

### 3. Ticker/Entity Mapping Risk

Separate collection from mapping. A headline can be `RAW_CAPTURED` without ticker.

Mapping cascade:

1. SEC CIK/ticker/company mapping and issuer domain mapping.
2. Source-provided metadata if feed/API exposes ticker, exchange, CIK, or company.
3. Exact company legal name and alias dictionary from the active plus historical universe.
4. Conservative regex for exchange-tagged spans such as `(NASDAQ: MSTR)`.
5. GPT/LLM only as a review assistant that must return evidence spans, never as authority.

Gate statuses:

- `RAW_CAPTURED`
- `EXTRACTED_WITH_EVIDENCE`
- `ENTITY_MAPPED_LOW_CONFIDENCE`
- `ENTITY_MAPPED_HIGH_CONFIDENCE`
- `READY_DISCOVERY_ONLY`
- `BLOCKED_AMBIGUOUS_ENTITY`

Ambiguous tickers such as `A`, `ON`, `NOW`, `ALL`, `IT`, `ARE`, and `LIFE` must be blocked unless an exchange tag, CIK, source metadata, or exact company alias is present.

### 4. Historical Full Backfill Uncertainty

Do not try to solve historical backfill with Chrome page walking alone.

Backfill architecture:

- **SEC**: full daily-index backfill from 2016 onward is feasible and should be first-class official event data.
- **RSS/feed sources**: useful for forward and recent history; may not cover 2016.
- **Sitemaps/source archives**: probe each source for date depth before queueing.
- **Common Crawl/GDELT**: use as public web-scale historical discovery when source archives do not expose old listings.
- **Chrome**: use for capability probing, rendering fallback, and evidence validation, not as the bulk historical engine.

Historical rows must store:

```text
published_at_text
archive_discovered_at
capture_method
source_time_certified_flag
usable_for_historical_backtest_flag
```

If only discovered in 2026 through an archive, it must not be treated as available in 2016 for causal backtests unless source-time availability is proven.

## Alternative Approaches Considered

| Approach | Decision | Reason |
|---|---|---|
| Chrome selector-first crawler | Downgrade to fallback | Works, but too brittle and high-ops-risk as primary. |
| RSS/API-first collector | Adopt | Best free balance of speed, provenance, and hallucination control. |
| Sitemap/JSON-LD extractor | Adopt | Reduces selector drift and improves historical URL discovery. |
| SEC event backfill | Adopt | Official, stable, and strong entity mapping through CIK. |
| Common Crawl historical discovery | Research/Prototype | Potentially useful for 2016~ public web headlines without hammering sources. |
| Reuters/Bloomberg direct browser scrape | Block | Terms, paywall, and automated access risks outweigh value under free-only constraint. |
| Search engine/aggregator RSS only | Use as discovery only | Fast but biased and not full-source coverage. |

## Exact Join Keys

- Source capture key: `source_id`, `source_url`, `capture_method`, `captured_at`, `raw_sha256`.
- Article/headline identity: canonical URL, headline hash, source page URL, provider.
- Entity mapping key: CIK/exchange/ticker when available; otherwise exact alias evidence. No proximity fallback.
- L2 key remains `source_receipt_id`, `primitive_batch_id`, `primitive_id`, and `lineage_edge_id`.

## Leakage Audit

Backtest features must use `detected_at` or certified source availability time, not simply the article's displayed publication date. Archive-discovered rows require an explicit `source_time_certified_flag` before historical evaluation. Missing entity mappings are never negatives.

## Split/OOS Metrics

Not applicable. This is source acquisition architecture only.

## Cost/Slippage Stress

Not applicable. No PnL, execution, order, or capital decision is made.

## Remaining Blockers

- Implement source capability probe.
- Implement RSS/sitemap/JSON-LD extractor cascade.
- Implement source governance registry with robots/terms posture.
- Implement deterministic entity mapper with CIK/ticker/alias evidence.
- Prototype Common Crawl or GDELT URL-level historical discovery for old public headlines.
- Integrate progress reporting for the new source families if promoted from research to collector.
- Governance completion audit passed with existing protected-DB warnings for `trading.db` and `data/task388_intraday_canonical_continuation_engine.db` not being DVC-tracked; this is not caused by this research artifact.

# No-Background Decision-Maker Report

The Chrome crawler worked, but we should not make it the center of the system. The safer plan is to collect news from machine-readable public sources first: RSS, sitemaps, JSON-LD metadata, SEC indexes, and source archives. Chrome should only be used when those fail or when we need to verify what a public page actually shows.

This reduces hallucination, selector breakage, and legal/ops risk. It also avoids picking a small set of tickers up front. We collect the source's headline universe first, then map companies later with strict evidence.

The practical next build is a `source_capability_probe`: for each news source, automatically decide whether RSS, sitemap, JSON-LD, static HTML, or Chrome is the correct capture mode.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
