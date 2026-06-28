# Decision Summary

- Verdict: `PRIMARY_PASS` for L0 data infrastructure; overall readiness remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this opens no trading, scoring, order, or capital gate.
- Key metrics: 14-source live RSS smoke v2 produced 403 rows with 0 blocked. External RSS smoke v1 produced 122 rows from 8 promoted sources with 0 L1 blocked. Non-newswire v2 RSS smoke produced 75 rows from 15/15 promoted sources with 0 blocked. Non-newswire v2 historical smoke produced 17 rows from AP monthly sitemap, SpaceNews WordPress, Carbon Brief WordPress, and Robot Report WordPress with 0 blocked. v0.1.8 live smoke for Seeking Alpha, Finviz, and 9 Industry Dive sources produced 117 rows with 0 blocked. v0.1.8 Industry Dive all-source archive smoke produced 9 rows from 9/9 monthly sitemap sources with 0 blocked. v0.1.9 sector-Dive expansion live smoke produced 130 rows from 13/13 sources with 0 blocked; v0.1.9 archive smoke produced 13 rows from 13/13 monthly sitemap sources with 0 blocked; v0.1.9 L2 smoke ingested 26 L0 events as 143 news facts and passed L2/L3/no-trade validators. v0.1.10 StockTitan live RSS smoke produced 100 rows, 100/100 explicit source-URL ticker mappings, 0 blocked, and 100 L2 facts with L2/L3/no-trade validators passing. v0.1.11 non-newswire market-source live smoke produced 289 rows from 9/9 sources with 0 blocked; WordPress backfill smoke produced 310 January 2016 rows from 4/4 sources with 0 blocked; combined L2 smoke ingested 599 facts and passed L2/L3/no-trade validators.
- What changed: added `public_market_macro_news_feeds` live watcher and historical backfill paths for Guardian, CNBC sitemap/article metadata, Wikimedia Current Events, CNN Money Common Crawl, The Hill WordPress REST, TechCrunch WordPress REST, Electrek WordPress REST, Teslarati WordPress REST, plus promoted crypto, energy/commodity, cyber, semiconductor, policy, tech/AI, supply-chain, biotech, defense, space, logistics RSS sources, AP monthly sitemap backfill, SpaceNews/Carbon Brief/Robot Report WordPress backfill, Seeking Alpha public RSS, Finviz public headline HTML discovery, Industry Dive RSS plus monthly sitemap archive backfill, v0.1.9 expanded sector-Dive sources, v0.1.10 StockTitan public RSS live ticker-rich headlines using source URL ticker evidence only, and v0.1.11 IBD/InvestorPlace/FXStreet/Defense One/Nareit/ETF Trends/HousingWire/American Banker/Techmeme live RSS plus IBD/InvestorPlace/ETF Trends/HousingWire WordPress backfill.
- Next action: monitor the restarted market/macro live and market/macro backfill workers so the expanded 68-source live and 21-source market/macro archive lanes keep collecting, while the separate 22-source Industry/sector Dive archive lane continues unchanged.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Expand L0 news beyond newswires with free machine-readable market/macro headline sources that are useful for trading context. |
| Target Metrics | Real RSS/API/sitemap/archive smoke, L1-ready context rows, L2 no-trade ingest, background worker started, status reporting visible. |
| Forbidden Actions | No login, paywall, captcha bypass, stealth/proxy evasion, GPT-created headlines, inferred ticker certainty, trade output, score output, order intent, or deployment claim. |
| Available Raw Sources | CNBC RSS and sitemap/article metadata; NPR, PBS, ABC, CBS, Census, Yahoo Finance, NYT, Fox Business, Investing.com, Nasdaq Trader, BBC, FT, MarketWatch RSS; Cointelegraph, Decrypt, CryptoSlate, OilPrice, Mining.com copper, BleepingComputer, KrebsOnSecurity, and Semiconductor Engineering RSS; Seeking Alpha public RSS; StockTitan public RSS; Finviz public headline HTML page; IBD, InvestorPlace, FXStreet, Defense One, Nareit, ETF Trends, HousingWire, American Banker, and Techmeme RSS; Guardian Open Platform API; Wikimedia Current Events monthly archive; CNN Money Common Crawl archive; The Hill, TechCrunch, Electrek, Teslarati, Semiconductor Engineering, Bitcoin Magazine, 9to5Mac, 9to5Google, PV Magazine USA, IBD, InvestorPlace, ETF Trends, and HousingWire WordPress REST; Utility, Supply Chain, BioPharma, Banking, Retail, CIO, Cybersecurity, Payments, Manufacturing, Food, Healthcare, PharmaVoice, Construction, CFO, Restaurant, Grocery, Marketing, HR, MedTech, Higher Ed, K-12, and Smart Cities Dive RSS/monthly sitemap archives. |
| Missing Raw Sources | Historical full backfill for publishers without explicit archive/API/Common-Crawl/WordPress-REST route remains source-specific and not claimed. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_public_market_macro_news_collector/` |
| Large Artifact Directory | `data/artifacts/l0_public_market_macro_news*` |
| Validation | Unit tests, real smoke, L2 canonical validation, L2 no-trade validation, status report validation. |
| Completion Criteria | Market/macro source family collects real rows and passes L1/L2 diagnostic-only gates. |

# Quant Expert Report

## Data Source And Source Readiness

Implemented `public_market_macro_news_feeds` as a separate source family from official context feeds and public newswires.

Live watcher sources:

| Source | Expansion Smoke Rows | Role |
|---|---:|---|
| CNBC RSS | 30 | Market, industry, policy headlines |
| NPR RSS | 30 | Economy, business, technology, world, policy headlines |
| PBS NewsHour RSS | 30 | Economy, politics, world headlines |
| ABC News RSS | 30 | Money, politics, world headlines |
| CBS News RSS | 30 | MoneyWatch, politics, world, technology headlines |
| Census RSS | 18 | Official economic indicators and Census newsroom headlines |
| Yahoo Finance RSS | 30 | Market and business headlines |
| NYT RSS | 30 | Business, technology, world headlines |
| Fox Business RSS | 30 | Latest, economy, markets headlines |
| Investing.com RSS | 30 | Market/economic indicator headlines |
| BBC RSS | 30 | Macro, business, geopolitical headlines |
| FT RSS | 25 | Headline-only macro/market/geopolitical context |
| MarketWatch RSS | 30 | Market and risk-appetite headlines; staleness monitored |
| Nasdaq Trader RSS | 30 | Official market-structure notices |
| Cointelegraph RSS | 20 | Crypto and digital-asset risk appetite headlines |
| Decrypt RSS | 20 | Crypto, AI, and digital-asset market headlines |
| CryptoSlate RSS | 10 | Crypto market and regulation headlines |
| OilPrice RSS | 15 | Energy, commodities, geopolitics, and inflation context |
| Mining.com copper RSS | 20 | Copper, critical minerals, and commodity supply-chain context |
| BleepingComputer RSS | 15 | Cyber incident and software/security risk context |
| KrebsOnSecurity RSS | 10 | Cyber incident and adversary context |
| Semiconductor Engineering RSS | 10 | Semiconductor, AI infrastructure, and data-center hardware context |
| Seeking Alpha Market Currents RSS | 7 | Equity and market headline context |
| StockTitan public RSS | 100 | Ticker-rich public stock headlines; ticker comes only from explicit source URL path |
| Finviz public news HTML | 20 | Market headline discovery from public aggregator page; observed-time only |
| Banking Dive RSS | 10 | Banking, financials, and policy context |
| Retail Dive RSS | 10 | Retail, consumer spending, and risk-appetite context |
| CIO Dive RSS | 10 | Enterprise technology, cloud, and AI context |
| Cybersecurity Dive RSS | 10 | Cybersecurity and technology risk context |
| Payments Dive RSS | 10 | Payments, fintech, and regulation context |
| Manufacturing Dive RSS | 10 | Industrial, supply-chain, and automation context |
| Food Dive RSS | 10 | Consumer staples, food, inflation, and supply-chain context |
| Healthcare Dive RSS | 10 | Healthcare services, policy, and risk context |
| PharmaVoice RSS | 10 | Pharma and biotech industry context |
| Construction Dive RSS | 10 | Construction, infrastructure, housing, and project-cost context |
| CFO Dive RSS | 10 | Corporate finance, capital allocation, and risk-appetite context |
| Restaurant Dive RSS | 10 | Restaurant, food service, consumer, labor, and inflation context |
| Grocery Dive RSS | 10 | Grocery, staples, consumer spending, and food inflation context |
| Marketing Dive RSS | 10 | Advertising, consumer demand, brand, and technology context |
| HR Dive RSS | 10 | Labor-market, wages, hiring, and employment-policy context |
| MedTech Dive RSS | 10 | Medical-device, healthcare, regulation, and risk context |
| Higher Ed Dive RSS | 10 | Education policy, labor-market, technology, and student-debt context |
| K-12 Dive RSS | 10 | Education policy, labor-market, technology, and public-spending context |
| Smart Cities Dive RSS | 10 | Infrastructure, urban policy, climate, grid, and mobility context |

Historical backfill:

| Source | Latest Rows / Smoke | Status |
|---|---:|---|
| Guardian Open Platform | Running production rows | Monthly API backfill from 2016 onward with page offsets |
| CNBC sitemap/article metadata | 3-row 2016 smoke | Sitemap shards plus article metadata; diagnostic-only historical context |
| Wikimedia Current Events | 20-row 2016 smoke | Monthly event archive for macro/geopolitical context; diagnostic-only historical context |
| CNN Money Common Crawl | 11-row 2016 smoke v8 | Date-scoped CDX/WARC archive; stale out-of-window metadata rejected |
| The Hill WordPress REST | 40-row 2016 smoke; production rows after restart | Policy, geopolitics, tax, trade, energy, and macro regime context |
| TechCrunch WordPress REST | 40-row 2016 smoke; production rows after restart | AI, cloud, chips, crypto, autonomous, and mega-cap technology context |
| Electrek WordPress REST | 40-row 2016 smoke; 500 production rows after restart | EV, Tesla, battery, charging, autonomous, and energy transition context |
| Teslarati WordPress REST | 40-row 2016 smoke; 500 production rows after restart | Tesla, EV, battery, charging, Autopilot, SpaceX, and launch context |
| Semiconductor Engineering WordPress REST | 18-row 2016-01 smoke | Semiconductor, chip, data-center, AI, EDA, foundry, and memory context |
| Bitcoin Magazine WordPress REST | 39-row 2016-01 smoke | Bitcoin, crypto regulation, mining, exchange, and ETF context |
| 9to5Mac WordPress REST | 40-row 2016-01 smoke | Apple, iPhone, Mac, App Store, services, chip, AI, China, and supply-chain context |
| 9to5Google WordPress REST | 40-row 2016-01 smoke | Google, Android, Samsung, AI, cloud, ads, Waymo, and autonomous context |
| PV Magazine USA WordPress REST | 1-row 2016-01 smoke | Solar, storage, renewable, grid, and utility-scale energy context |
| Industry/sector Dive monthly sitemap/article metadata | 13-row v0.1.9 expansion smoke; prior 9-row v0.1.8 smoke | Utility, supply chain, biopharma, banking, retail, CIO, cybersecurity, payments, manufacturing, food, healthcare, PharmaVoice, construction, CFO, restaurant, grocery, marketing, HR, medtech, higher ed, K-12, and smart-cities monthly sitemap archives with source-specific start dates and 5-second crawl delay |

v0.1.11 adds non-newswire market-source breadth focused on sources that are public, machine-readable, and useful for market/macro context:

| Lane | Sources | Smoke Rows | Status |
|---|---:|---:|---|
| Live RSS | IBD, InvestorPlace, FXStreet, Defense One, Nareit, ETF Trends, HousingWire, American Banker, Techmeme | 289 | 9/9 exported, 0 blocked |
| WordPress REST January 2016 backfill | IBD, InvestorPlace, ETF Trends, HousingWire | 310 | 4/4 exported, 0 blocked |
| Combined L2 smoke | v0.1.11 live plus WordPress backfill | 599 facts | `L2_NEWS_OK`, `L2_NO_TRADE_OUTPUT_OK`, `L3_L2_INPUT_OK` |

The pre-promotion date-filter probe confirmed that the WordPress routes expose meaningful historical volume: IBD had `X-WP-Total=1410` for January 2016, InvestorPlace `1043`, ETF Trends `205`, and HousingWire `281`. These rows remain context/headline facts and do not become firm-specific ticker claims unless a separate deterministic evidence path exists.

v0.1.8 adds a generic `monthly_sitemap_article_meta` mode. v0.1.9 extends that mode to 13 additional sector-Dive routes and upgrades Utility, Supply Chain, and BioPharma Dive from live-only to archive-capable. It fetches monthly sitemap URL sets, then article metadata titles and publication times, preserving raw response metadata and setting `usable_for_historical_backtest_flag=0` until source-time quality is audited at scale. The mode supports source-specific `backfill_start_date` so sources launched after 2016 do not waste cycles on unavailable archive months.

Rows are collected as macro/context candidates, not ticker-specific claims. `ticker_mapping_required_flag=0`, `macro_context_candidate_flag=1`, and `entity_mapping_status=NOT_REQUIRED_MARKET_MACRO_CONTEXT`.

CNBC, Wikimedia, and Common Crawl historical rows keep `source_time_certified_flag=0` and `usable_for_historical_backtest_flag=0`. Guardian and WordPress REST rows carry explicit API publication timestamps and are marked source-time usable for historical research. None of these paths produce trades, scores, orders, or strategy output.

## Exact Join Keys

- Source event key: `provider`, `source_id`, `updated_at`, `raw_sha256`.
- Headline identity: `provider`, `source_key`, `headline_hash`, `source_url`, `published_at`.
- L2 keys: `source_receipt_id`, `primitive_batch_id`, `primitive_id`, `lineage_edge_id`.

## Leakage Audit

No market labels, returns, lifecycle IDs, orders, fills, or outcomes are read. The collector stores title, URL, source, publication time where available, and provenance only.

## Failure Decomposition

- Google News remains excluded because same-origin robots guard blocks the configured RSS routes.
- NPR archive HTML was reachable but robots-disallowed for the tested archive query, so it was not promoted to historical backfill.
- PBS WordPress REST returned 401 and was not promoted to historical backfill.
- CBS/ABC sitemap probes returned 404/403 and were not promoted to historical backfill.
- Fox Business sitemap only covered recent 2024-2026 pages in the tested article sitemap, so it was not promoted to 2016+ historical backfill.
- Yahoo Finance and Investing.com Common Crawl patterns were removed from historical defaults after stale 2013-2014 article metadata appeared inside 2016 crawl collections; both remain live RSS sources.
- EIA Today in Energy and The Register returned valid-looking candidate routes during discovery but were not promoted to default live collection after robots blocking in the collector smoke.
- StockTitan public RSS was promoted as a live-only ticker-rich source in v0.1.10. Its date archive pages were not promoted for historical backfill because 2025/2024/2022 probes returned 403 and 2016/2018/2020 probes returned 410.
- Historical full backfill outside Guardian, CNBC, Wikimedia, CNN Money Common Crawl, The Hill WordPress, TechCrunch WordPress, Electrek WordPress, Teslarati WordPress, Semiconductor Engineering WordPress, Bitcoin Magazine WordPress, 9to5Mac WordPress, 9to5Google WordPress, PV Magazine USA WordPress, and the 22 promoted Industry/sector Dive monthly sitemap archives is not claimed.

## Cost/Slippage Stress

Not applicable. No PnL or execution claim is made.

## Remaining Blockers

- Add historical archive support for additional publishers only after source capability and terms posture are explicit.
- Continue auditing StockTitan live RSS duplicate/low-signal behavior; do not use its AI score/summary fields as evidence.
- Continue monitoring the restarted background workers with the 59-source live default, 17-source market/macro backfill default, and separate 22-source Industry/sector Dive backfill default.
- Continue monitoring feed staleness and WordPress relevance gates as rows accumulate.
- Continue auditing CNBC, Wikimedia, Common Crawl, and WordPress historical quality filters.

# No-Background Decision-Maker Report

The news dataset is materially broader than the original newswire-only setup. The live lane default now covers 68 public RSS/HTML sources every 30 minutes after restart. The historical market/macro lane default now covers 21 sources: Guardian, AP monthly sitemap, CNBC, Wikimedia Current Events, CNN Money Common Crawl, The Hill, TechCrunch, Electrek, Teslarati, Semiconductor Engineering, Bitcoin Magazine, 9to5Mac, 9to5Google, PV Magazine USA, IBD, InvestorPlace, ETF Trends, HousingWire, SpaceNews, Carbon Brief, and Robot Report. A separate Industry/sector Dive historical lane continues to cover 22 sector archives with source-specific start dates.

The Hill improves policy, geopolitics, tax, trade, energy, and macro regime coverage. TechCrunch improves AI, cloud, semiconductor, crypto, autonomous, and mega-cap technology context. Electrek and Teslarati improve EV, Tesla, battery, charging, autonomous driving, energy transition, and SpaceX context. The newer RSS and WordPress sources add crypto, energy, commodities, cyber, semiconductor, Apple, Google, solar, policy, supply chain, biotech, defense, space, logistics, climate, robotics, IBD market headlines, InvestorPlace market/opinion headlines, FX/rates context, REITs, ETFs, housing/mortgage, banking, and tech aggregator context.

The design does not let GPT invent news or attach tickers by inference. StockTitan ticker mapping uses only explicit `/news/TICKER/...` source URL evidence. It preserves source URL, raw evidence, title source, collection lineage, and source-time flags for L2/L3. It still creates no strategy score, order, or live trading output.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
