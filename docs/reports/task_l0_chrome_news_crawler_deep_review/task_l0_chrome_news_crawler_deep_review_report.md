# Decision Summary

- Verdict: `PRIMARY_PASS` for review completion; Chrome crawler use remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this opens no trading, scoring, order, broker, or capital gate.
- Key decision: Chrome/Playwright should be a fallback and verification layer, not the primary L0 news collector.
- Key metrics: existing Chrome smoke captured 26 public headline rows from two sources; source capability probe found four checked sources do not require Chrome first.
- What changed: all Chrome news crawler context was consolidated into a deep review packet and sent to a read-only reviewer.
- Next action: build the machine-readable extractor cascade first, then add a governed Chrome fallback queue only for source modes that require rendering or validation.
- Independent reviewer finding: the read-only reviewer agreed that Chrome should be `fallback/verification only`, not primary or always-on parallel collection.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Consolidate all Chrome news crawler context and obtain a deep-review decision on how the crawler should be used. |
| Target Metrics | Include prior smoke evidence, source capability results, legal/ops constraints, hallucination controls, and next build gates. |
| Forbidden Actions | No login, paywall, captcha bypass, stealth/proxy evasion, GPT-created headlines, inferred ticker certainty, or deployment claim. |
| Available Raw Sources | Existing Chrome smoke artifacts, L2 diagnostic path, source capability probe, public RSS/sitemap/API source checks. |
| Missing Raw Sources | Production extractor cascade, source-date queue, entity mapper, and background Chrome fallback runner. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_chrome_news_crawler_deep_review/` |
| Large Artifact Directory | Not applicable; this task created small review artifacts only. |
| Validation | `python scripts/task_registry_validate.py`; `python scripts/operating_closeout_validate.py`. |
| Completion Criteria | Packet and review report exist, registry points to them, and next use policy is explicit. |

# Quant Expert Report

## Data Source And Source Readiness

The current Chrome path is `public_headline_browser_watch`. It uses Playwright/Chrome to load public listing pages, then writes raw HTML, screenshot, headline JSON, source URL, capture timestamp, hashes, title spans, and evidence spans.

Smoke result:

| Source | Rows | Status |
|---|---:|---|
| PRNewswire latest listing | 16 | `EXPORTED` |
| GlobeNewswire latest listing | 10 | `EXPORTED` |
| Total | 26 | `PRIMARY_PASS` smoke |

This proves the crawler can capture public headline evidence. It does not prove that Chrome is the right bulk collection mechanism.

The later source capability probe found better first routes:

| Source | Preferred Route | Chrome Role |
|---|---|---|
| SEC EDGAR | API / official index | Not needed first |
| PRNewswire | RSS/feed and sitemap | Fallback/verification |
| GlobeNewswire | RSS/feed and sitemap | Fallback/verification |
| BusinessWire | Public RSS/sitemap | Fallback/verification; skip robots-disallowed same-origin paths |

External checks support that hierarchy. SEC documents no-key EDGAR APIs and bulk archives, and separately states a fair-access request limit and User-Agent expectation. PRNewswire and GlobeNewswire expose RSS/feed pages. BusinessWire describes RSS headline feeds. Playwright itself recommends resilient locators and warns that CSS/XPath can be less resilient. The sitemap protocol gives stable URL discovery semantics. RFC 9309 defines robots controls that crawlers should honor.

Reuters and Bloomberg-type direct browser collection should remain blocked without explicit license or permission. Reuters Connect terms restrict scraping/automated collection and commercial use of content; Bloomberg Industry terms similarly restrict scraping, automated access, and archival reuse in subscription products.

## Recommended Operating Model

Chrome should run only after a source passes a governance gate:

1. Source capability probe has no usable API/RSS/sitemap/JSON-LD/static route, or Chrome is needed to verify rendered page evidence.
2. robots.txt allows the exact public URL path for the crawler User-Agent.
3. The page is public and requires no login, paywall, captcha, consent bypass, or anti-bot evasion.
4. The source is marked headline/link/snippet-only unless explicit full-text permission exists.
5. A source-specific parser has golden samples and row-count drift alarms.
6. Rows are diagnostic-only until entity mapping and source-time certification pass.

Recommended cadence:

- Forward watch: low-frequency polling per source, no faster than the source's stated policy; if no policy exists, start conservatively at 15 to 60 minutes per source page.
- Historical use: limited to capability probing, rendered archive validation, and sparse source-date QA. Do not page-walk years of history with Chrome as the bulk engine.
- Failure handling: `EMPTY_PROVIDER_RESPONSE`, `FAILED_RETRYABLE`, `BLOCKED_ROBOTS`, `BLOCKED_CAPTCHA_OR_LOGIN`, `BLOCKED_TERMS`, and `BLOCKED_SELECTOR_DRIFT` must be distinct.
- Scheduler posture: keep the existing Chrome scheduler job disabled. Allow a diagnostic fallback override only when source capability evidence proves Chrome is needed.

## Hallucination-Control Harness

A Chrome headline row may be emitted only when all of these exist:

- source registry entry with allowed Chrome mode
- URL allowed by robots check for the configured User-Agent
- raw HTML path and hash
- screenshot path or explicit screenshot failure reason
- HTTP status and final resolved URL
- extracted canonical URL
- source page URL
- capture timestamp
- deterministic headline text span from DOM anchor or structured metadata
- evidence selector version
- evidence text span near the link
- headline identity hash
- diagnostic permission flags all closed

Rows must remain blocked when:

- title, URL, evidence span, or source page URL is missing
- publication time is absent and the row is being used for historical backtest availability
- entity/ticker is ambiguous or inferred only from title proximity
- source path is disallowed by robots
- login/paywall/captcha/consent bypass is required
- selector row count drifts outside expected bounds
- source terms posture is unknown
- event ledger hash, raw payload hash, or screenshot evidence cannot be reconciled

No inferred matching was used in this review.

## Exact Join Keys

- Source evidence key: `provider`, `source_id`, `source_page_url`, `captured_at`, `raw_sha256`.
- Headline identity key: `headline_hash = sha256(provider, title, url, source_page_url)`.
- Future backfill key: `source_key`, `source_url`, `source_period`, `capture_method`, `captured_at`.
- Entity mapping key: CIK/exchange/ticker/source-provided metadata or exact alias evidence. No symbol/date/price/time fallback.

## Leakage Audit

For forward collection, `detected_at` can be used as the live-visible time. For historical backfill, the displayed publication time is not enough. Historical rows need `source_time_certified_flag` and `archive_discovered_at`; otherwise they are not eligible for causal backtests.

Missing news, missing entities, blocked source paths, and failed browser pages must never be converted into negative labels or negative trading signals.

## Split/OOS Metrics

Not applicable. This is source acquisition governance only.

## Failure Decomposition

- Selector drift: mitigated by API/RSS/sitemap first, source-specific golden samples, selector versioning, and row-count drift alarms.
- Terms/robots/captcha: mitigated by a source governance registry, preflight robots checks, no login/paywall/captcha bypass, and kill switches.
- Entity mapping: mitigated by separate deterministic mapper with ambiguity blockers.
- Timestamp risk: mitigated by separating `detected_at`, `published_at_text`, `archive_discovered_at`, and source-time certification.
- Historical volume: mitigated by using API/RSS/sitemap/GDELT/Common Crawl-style discovery before any Chrome rendering.

## Remaining Blockers

- Implement RSS/API/sitemap/JSON-LD extractor cascade.
- Implement source governance registry fields for allowed modes, robots posture, terms posture, and kill switch.
- Implement Chrome fallback queue with strict source eligibility.
- Add deterministic entity/ticker mapper before L3/trading promotion.
- Add progress reporting for Chrome fallback only if it becomes a background lane.
- Split `event_time=capturedAt` into explicit `detected_at`, `captured_at`, `published_at_text`, `source_time_certified_flag`, and `usable_for_historical_backtest_flag`.
- Add Chrome tests for raw evidence missing, hash mismatch, screenshot missing, timestamp uncertified, and ambiguous entity blocking.

## Read-Only Reviewer Result

The reviewer used no inferred matching and made no file edits. The review conclusion was:

- Chrome is neither primary nor always-on parallel; it is fallback and verification only.
- Current background exclusion is correct because `public_headline_browser_watch_smoke` is disabled and diagnostic-only.
- PRNewswire, GlobeNewswire, and BusinessWire should use RSS/sitemap/static routes before Chrome.
- Chrome rows must be blocked if raw HTML/hash/screenshot/event ledger evidence is incomplete.
- `event_time=capturedAt` is acceptable only for forward observation, not historical source-time certification.
- Historical bulk backfill should use SEC API/index, RSS/sitemap archives, GDELT, or Common Crawl-style URL discovery rather than Chrome page walking.

# No-Background Decision-Maker Report

Chrome worked, but it should not lead the system.

The best plan is: collect from structured public routes first, because they are faster and less fragile. Use Chrome only when a page really needs rendering or when we need visual/DOM evidence that a structured route is missing something.

This means we should not turn on a broad Chrome background crawler today. We should first build the RSS/sitemap/API extractor cascade, then add Chrome as a governed fallback with strict evidence, robots, terms, and entity-mapping gates.

This does not change deployment readiness. It remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
