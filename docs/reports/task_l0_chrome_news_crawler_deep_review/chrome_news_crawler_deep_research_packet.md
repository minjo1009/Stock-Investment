# Chrome News Crawler Deep Review Packet

## Objective

Review whether the L0 Chrome/Playwright public headline crawler should be used as a primary, parallel, or fallback source in the news collection stack.

## Local Facts To Review

- Current crawler provider: `public_headline_browser_watch`.
- Smoke result: `PRIMARY_PASS`, diagnostic-only.
- Smoke sources:
  - PRNewswire latest listing: 16 headline rows.
  - GlobeNewswire latest listing: 10 headline rows.
- Evidence captured per source: raw HTML, screenshot, headline JSON, source URL, capture timestamp, payload hash, event ledger.
- L2 support exists: browser headline events can be parsed into diagnostic `news_event` facts.
- Trading, score, order, broker mutation, and capital flags remain closed.
- Entity/ticker mapping is intentionally missing and blocks promotion.
- The current hourly L0 background collection does not include Chrome crawler.
- The later source capability probe found:
  - SEC EDGAR should use API or official index.
  - PRNewswire should use RSS/feed and sitemap routes before Chrome.
  - GlobeNewswire should use RSS/feed and sitemap routes before Chrome.
  - BusinessWire should use public RSS/sitemap evidence; same-origin robots-disallowed feed-options path is skipped.

## Local Inputs

- `docs/reports/task_l0_public_headline_browser_crawler/`
- `docs/reports/task_l0_free_news_source_mitigation_research/`
- `docs/reports/task_l0_source_capability_probe/`
- `tools/db/source_acquisition/public_headline_browser_crawler.js`
- `scripts/run_l0_public_headline_browser_smoke.ps1`
- `configs/db_source_acquisition_scheduler.json`
- `configs/source_registry/l0_public_news_capability_sources.json`
- `src/l2/news_runtime.py`
- `tests/test_l2_news_canonical_path.py`
- `tests/test_l0_source_acquisition_hardening.py`
- `data/artifacts/l0_public_headline_browser_smoke/smoke_summary_v2.json`

## External Sources Checked

- SEC EDGAR APIs: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC EDGAR access policy: `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`
- Playwright locators: `https://playwright.dev/docs/locators`
- Sitemap protocol: `https://www.sitemaps.org/protocol.html`
- Robots Exclusion Protocol: `https://www.rfc-editor.org/rfc/rfc9309`
- PRNewswire RSS: `https://www.prnewswire.com/rss/`
- GlobeNewswire RSS list: `https://www.globenewswire.com/rss/list`
- BusinessWire feed options: `https://www.businesswire.com/help/feed-options`
- Reuters Connect terms: `https://www.reutersconnect.com/general-terms/`
- Bloomberg Industry subscription terms: `https://www.bloombergindustry.com/terms-of-service-subscription-products/`

## Review Questions

1. Should Chrome be primary, parallel, or fallback/verification only?
2. What source eligibility rules are required before a Chrome lane can run?
3. What exact evidence must exist before a headline row is emitted?
4. What rows must remain blocked?
5. How should historical backfill use Chrome, if at all?
6. What controls are required for selector drift, robots/terms, captcha/blocking, entity mapping, and stale timestamps?
7. What implementation changes are needed before enabling a background Chrome lane?

## Forbidden Actions

- No login, paywall, captcha bypass, stealth/proxy evasion, or anti-bot circumvention.
- No full-text archive claim unless explicitly permitted by source.
- No GPT-created headlines.
- No inferred ticker certainty.
- No symbol/date/price/time fallback matching.
- Missing labels are never negatives.
- No deployment or trading claim from diagnostic-only evidence.

## Expected Output

A Korean review with verdict, operating model, blocker list, and next build checklist. The review must state whether inferred matching was used.
