# L0 Public Context News Collector

## Decision Summary

- Verdict: `PRIMARY_PASS` for diagnostic L0 collection and L2 ingestion smoke.
- Strategy acceptance status: `NOT_ACCEPTED`; this is `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: capability probe v2 covered 9 original sources; watcher smoke v3 produced 65 rows, 65 L1-ready discovery rows, 0 L1-blocked rows; official expansion smoke v2 produced 36 rows from 8 promoted sources with 0 blocked rows; World Bank API backfill smoke produced 11 rows and cursor offset 20; official expansion L2 smoke ingested 9 events into 47 facts and passed L2/L3/no-trade validators.
- What changed: added `public_context_news_feeds` as a ticker-mapping-not-required macro/context/news lane using public RSS, official API, static page, sitemap article metadata capture, plus historical backfill modes for Federal Register, Federal Reserve, CFTC, and World Bank public news API archives.
- Next action: restart the regular context live/backfill workers with the expanded defaults, continue source-level backfill monitoring, and add further source-specific archive routes for BLS, BEA, Nasdaq Trader, CoinDesk, and archived White House administrations where feasible.

## Quant Expert Report

| Field | Value |
|---|---|
| Objective | Expand L0 beyond newswire by collecting public macro, policy, market-structure, and crypto context news in L1/L2-consumable form. |
| Target Metrics | Real-network smoke with all configured sources processed; zero L1 blocks for context rows; L2 canonical path and no-trade validators pass. |
| Forbidden Actions | No inferred ticker mapping; no fake rows; no paywall/login/captcha bypass; no deployment or trading signal claim. |
| Available Data | Public RSS/API/page/sitemap sources in `configs/source_registry/l0_public_context_news_sources.json`; raw captures under `data/raw/l0_public_context_news*`. |
| Missing Data | Source-specific full historical archives for 2016+ are not yet proven for every source. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_public_context_news_collector/` |
| Large Artifact Directory | `data/artifacts/l0_public_context_news/` |
| Validation | Unit tests plus L2 canonical/no-trade validators and task registry validation. |

Data source and readiness:

- Added 17 default context sources: Federal Reserve, BLS CPI, BLS latest releases, BEA, CFTC, Federal Register, White House, Nasdaq Trader, CoinDesk, ECB press, ECB statistical press, Bank of England news, Bank of England speeches, EIA press, Defense public press, Defense public contracts, and World Bank public news API.
- Capture modes from capability probe v2: 7 RSS/Atom, 1 official API, 1 sitemap/page path.
- `public_context_news_feeds` rows explicitly set `ticker_mapping_required_flag=0` and `macro_context_candidate_flag=1`.
- Historical backfill currently supports Federal Register monthly API pages, Federal Reserve yearly press release archive pages, CFTC yearly press release archive pages, and World Bank offset-paginated public news API pages.
- 2026-06-29 official expansion smoke v2: ECB press 5 rows, ECB statistical press 5, Bank of England news 5, Bank of England speeches 5, EIA press 1, Defense press 5, Defense contracts 5, World Bank API 5; total 36 rows, 0 blocked.
- World Bank backfill smoke v1: 11 rows for the 2026-01-01 to 2026-06-28 window, cursor state `worldbank_news_desc_cursor=20`, 0 blocked.

Exact join keys:

- No ticker join is required at L0 for this lane.
- Stable evidence keys are `source_key`, `source_url`, `canonical_url`, `published_at`, and `headline_hash`.
- L2 facts preserve source URL and context topic candidates for later L2/L3 interpretation.

Leakage audit:

- No labels or outcomes are used.
- No missing rows are converted to negatives.
- `usable_for_historical_backtest_flag=0` remains closed. Even for backfill rows, L0 has not yet certified complete source coverage or downstream event-time use for strategy backtests.
- No trade, score, order intent, broker mutation, or real-capital permission is emitted.

Failure decomposition:

- Initial BLS principal URL and White House feed URL returned 404. BLS was corrected to `bls_latest.rss`; White House now uses public page plus sitemap article metadata fallback.
- Historical full backfill is now started for Federal Register, Federal Reserve, and CFTC. Other context sources remain source-specific blockers until archive routes are proven.
- BIS RSS endpoints returned feed rows in a direct probe, but `https://www.bis.org/robots.txt` disallows `/doclist/`; BIS sources are kept in the registry as disabled policy-review candidates and are not part of default collection.

Remaining blockers:

- Backfill depth by source must be audited before claiming 2016+ full context coverage across all context sources.
- Topic mapping is keyword-seeded only; it is evidence-preserving, not a trading interpretation.

## No-Background Decision-Maker Report

We added a new news lane for the kind of information that does not map cleanly to a single ticker: Fed, inflation, regulation, policy, exchange notices, crypto/risk context, central-bank context, energy, defense/geopolitics, and World Bank macro/development news.

Why it matters: the newswire lane is company-release-heavy and too sparse for macro context. This new lane gives L2/L3 a broader context feed without forcing bad ticker mappings.

This does not change capital or deployment readiness. It is a diagnostic data source only.

Plain-language next step: restart the watcher/backfill with the expanded defaults, keep the World Bank and existing official backfills running, then add more historical archive routes source by source.

## Artifact Manifest

See `artifact_manifest.csv` in this directory.
