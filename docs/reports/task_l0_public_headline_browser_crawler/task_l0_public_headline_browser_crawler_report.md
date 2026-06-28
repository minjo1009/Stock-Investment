# Decision Summary

- Verdict: `PRIMARY_PASS` for a smoke-tested public headline browser crawler MVP; overall readiness remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this is data acquisition infrastructure only.
- Key metrics: Chrome/Playwright smoke captured 26 public headline rows from 2 source listing pages: PRNewswire 16 and GlobeNewswire 10. L2 diagnostic ingest wrote 26 `news_event` facts with trade/score/order flags all 0.
- What changed: added `public_headline_browser_watch` as a diagnostic discovery-only source family, a Chrome/Playwright smoke crawler, and L2 parsing support for evidence-bound browser headline rows.
- Next action: promote this from latest-listing smoke to a source-date queue for PRNewswire/GlobeNewswire first; add entity mapping as a separate blocked-to-ready promotion worker.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Evaluate and smoke-test a free Chrome/Playwright public headline crawler, then compare it with the existing Marketaux/GDELT/official collection path. |
| Target Metrics | At least one real public source smoke with raw HTML, screenshot, payload JSON, event ledger, L2 diagnostic ingest, and no trade/score/order output. |
| Forbidden Actions | No login, no paywall or captcha bypass, no full-text archive claim, no GPT-created headlines, no inferred ticker certainty, no deployment or trading claim. |
| Available Raw Sources | Public PRNewswire and GlobeNewswire listing pages; existing L0/L2 news event pipeline. |
| Missing Raw Sources | Date-archive pagination contracts, source-specific terms audit beyond public headline smoke, deterministic entity/ticker mapper. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_public_headline_browser_crawler/` |
| Large Artifact Directory | `data/artifacts/task_l0_public_headline_browser_crawler/` |
| Validation | Node syntax check, Python compile, unit tests, real Chrome smoke, L2 news validator, L2 no-trade-output validator, L3 canonical input validator. |
| Completion Criteria | Smoke proves evidence-bound public headline capture is possible and comparison with existing approach is documented. |

# Quant Expert Report

## Data Source And Source Readiness

The existing path remains the governed baseline: official public releases, GDELT, and Marketaux produce API/RSS/archive-backed events with low hallucination risk. The weakness is speed and coverage under free caps, especially Marketaux daily requests and GDELT archive volume.

The new path is `public_headline_browser_watch`. It uses Chrome/Playwright to capture public listing pages, then stores raw HTML, screenshot, JSON payload, source URL, capture timestamp, hashes, title spans, and evidence spans. The smoke used only public pages:

- PRNewswire all news releases: `https://www.prnewswire.com/news-releases/`
- GlobeNewswire newsroom: `https://www.globenewswire.com/newsroom`

Official references used for scope and risk framing:

- SEC EDGAR APIs: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC daily index: `https://www.sec.gov/Archives/edgar/daily-index/`
- PRNewswire RSS: `https://www.prnewswire.com/rss/`
- Business Wire feed options: `https://www.businesswire.com/help/feed-options`
- Reuters Connect Terms: `https://www.reutersconnect.com/general-terms`
- Bloomberg Industry Terms: `https://www.bloombergindustry.com/terms-of-service-subscription-products/`

BusinessWire was not included in the MVP because the public page produced a headless Chrome HTTP2 navigation error during exploration. It remains a candidate, not a passed source.

## Exact Join Keys

- L0 source evidence key: `provider`, `source_id`, `source_page_url`, `captured_at`, `raw_sha256`.
- Headline identity key: `headline_hash = sha256(provider, title, url, source_page_url)`.
- L2 source key: `source_receipt_id` and `primitive_id` generated from the event ledger and payload hash.
- Ticker mapping key is intentionally absent in this smoke. Entity mapping must be a separate worker and cannot be inferred by title proximity alone.

## Leakage Audit

No label, return, lifecycle, order, fill, or future outcome data is read. Browser rows carry `detected_at` and `event_time` from capture time. `published_at` is not filled unless the page exposes text evidence. For backtests, archive-discovered headlines must not be treated as live-visible at their publication date unless a source-time proof exists.

## Hallucination Audit

GPT is not in the extraction path. The crawler emits a row only when Chrome exposes a DOM anchor that passes source-specific URL rules. Each event has raw HTML, screenshot, JSON payload, and hashes. Missing title, URL, time, or entity evidence is blocked rather than invented.

## Split/OOS Metrics

Not applicable. This task is source acquisition infrastructure only.

## Failure Decomposition

- PRNewswire first selector captured category links; the selector was tightened to article `.html` URLs and the invalid smoke L2 rows were removed.
- GlobeNewswire latest listing captured 10 article URLs but did not expose a clean publication time through the current generic time extractor; these rows remain evidence-captured but not time-certified beyond `detected_at`.
- Entity/ticker mapping is intentionally missing, so L2 rows remain `BLOCKED` with `missing_entity_or_ticker_mapping` until a separate mapper is added.

## Cost/Slippage Stress

Not applicable. This opens no PnL, execution, or capital gate.

## Comparison

| Option | Strength | Weakness | Best Use | Decision |
|---|---|---|---|---|
| Existing Marketaux/GDELT/official | API/RSS/archive-backed, low hallucination risk, cleaner provenance | Free Marketaux cap is too low; GDELT archive is large and slow; official endpoint coverage is sparse | Baseline governed source and corroboration | Keep |
| Chrome public headline crawler | Free, fast for current public listings, source-first not ticker-first, captures raw evidence | Higher selector/terms/drift risk; historical archive coverage varies by source; entity mapping still needed | Forward headline ledger and source-date backfill where archives are stable | Add in parallel |

## Remaining Blockers

- Need source-date queue design for PRNewswire/GlobeNewswire archive pagination.
- Need BusinessWire fallback or alternate URL validation.
- Need entity/ticker mapping worker with strict alias and ambiguity blocker.
- Need source terms/robots audit per source before long-running backfill.
- Need background runner and progress/status integration if promoted beyond smoke.
- Governance completion audit passed but warned that protected DB authorities including `trading.db` are not DVC-tracked; this is a repository artifact-governance warning, not a crawler smoke failure.

# No-Background Decision-Maker Report

The Chrome crawler idea works as a smoke test. It captured real public headlines from PRNewswire and GlobeNewswire, saved the evidence, and pushed diagnostic-only news facts into L2 without creating any trading output.

This does not replace Marketaux/GDELT/official. It should run beside them. The best design is source-first: collect all headlines from public source pages by date/page, then map tickers later. That avoids choosing 50 or 200 tradable names up front.

The main risk is not GPT hallucination now; the extraction path is deterministic. The remaining risk is source drift, legal/terms boundaries, and entity mapping mistakes. The next practical step is a source-date queue smoke over several historical dates for PRNewswire and GlobeNewswire.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
