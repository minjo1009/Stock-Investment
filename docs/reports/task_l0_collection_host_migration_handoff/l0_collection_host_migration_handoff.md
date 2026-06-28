# L0 Collection Host Migration Handoff

## Decision Summary

- Purpose: Move the L0 collection host from the notebook Codex environment to the desktop Codex environment without losing provenance or creating duplicate writes.
- Current repository path on notebook: `C:\Users\minjo\OneDrive\바탕 화면\외국주식 퀀트트레이딩`.
- Host migration rule: only one machine should run collectors that write to this OneDrive-backed workspace at a time.
- Current readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`; no strategy, score, order, broker mutation, or real-capital permission is created by these collectors.
- Latest status snapshot used here: `data/artifacts/l0_collection_status/current_status.md`, updated at `2026-06-28T22:52:51Z`.
- Notebook worker stop executed at `2026-06-28T22:59Z`: all notebook collector PIDs listed below were stopped, STOP files were created, and no `python*` collection process remained after cleanup.
- OneDrive sync nudge was requested from notebook after the desktop repo did not yet show the handoff files.

## Migration Rules For Desktop Codex

1. On the notebook, stop running collectors before starting them on desktop.
2. Wait until OneDrive shows sync complete for the repo, especially `trading.db`, `data/artifacts/**`, `data/raw/**`, `logs/**`, `configs/**`, `scripts/**`, and `tools/**`.
3. On desktop, open the same OneDrive repo and run `python scripts/report_l0_collection_status.py` before starting anything.
4. Do not run notebook and desktop workers simultaneously against the same OneDrive files. This can cause duplicate event rows, stale cursor writes, and SQLite lock/contention around `trading.db`.
5. Keep `.env` available on the desktop workspace before starting API-backed collectors. Marketaux token was added during the notebook run; verify it exists after sync.

## Stop Notebook Workers

Preferred graceful stop is to create each STOP file and wait for processes to exit. If they do not exit after a reasonable wait, stop the notebook-local PIDs.

```powershell
New-Item -ItemType File -Force -Path data/artifacts/l0_bar_full_backfill/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_news_full_backfill/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_news_background_collector/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_newswire/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_newswire_backfill/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_context_news/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_context_news_backfill/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_market_macro_news/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_market_macro_news_backfill/STOP | Out-Null
New-Item -ItemType File -Force -Path data/artifacts/l0_public_industry_dive_news_backfill/STOP | Out-Null
```

Notebook PIDs before stop:

| Lane | PID | State |
|---|---:|---|
| Daily bars | 10804 | stopped |
| 5m bars | 12680 | running |
| legacy news full backfill | 16056 | running |
| public newswire live | 9456 | running |
| public newswire backfill | 16756 | running |
| public context news live | 23960 | running |
| public context news backfill | 21940 | running |
| public market/macro news live | 8052 | running |
| public market/macro news backfill | 3504 | running |
| public Industry Dive backfill | 22692 | running |
| keep-awake | detected PID 1152 | running |

Notebook stop verification after cleanup:

| Lane | Final state |
|---|---|
| 5m bars | stopped |
| legacy news full backfill | stopped |
| public newswire live | stopped |
| public newswire backfill | stopped |
| public context news live | stopped |
| public context news backfill | stopped |
| public market/macro news live | stopped |
| public market/macro news backfill | stopped |
| public Industry Dive backfill | stopped |
| old newswire smoke PID `22700` | stopped |
| remaining `python*` processes | none detected |

## Start Desktop Workers

After OneDrive sync is complete and `python scripts/report_l0_collection_status.py` runs on desktop:

```powershell
.\scripts\start_l0_bar_full_backfill.ps1 -Lanes 5m
.\scripts\start_l0_news_background_collector.ps1
.\scripts\start_l0_news_full_backfill.ps1
.\scripts\start_l0_public_newswire_collector.ps1
.\scripts\start_l0_public_newswire_backfill.ps1
.\scripts\start_l0_public_context_news_collector.ps1
.\scripts\start_l0_public_context_news_backfill.ps1
.\scripts\start_l0_public_market_macro_news_collector.ps1
.\scripts\start_l0_public_market_macro_news_backfill.ps1
.\scripts\start_l0_public_industry_dive_news_backfill.ps1
```

Optional: daily bars are at `99.3771%` but stopped. If the operator wants to finish the remaining symbols:

```powershell
.\scripts\start_l0_bar_full_backfill.ps1 -Lanes daily
```

## Current Data Status

| Data family | Current status |
|---|---|
| Daily bars | `11,965/12,040` symbols, `99.3771%`, files `11,965`, failed `0`, stopped |
| 5m bars | `17,333,760` rows, `711` symbols, `5.3748%`, running |
| 1m bars | excluded from current L1/L2 minimum scope; about 5x 5m request/storage surface |
| Quote/trade ticks | postponed, `STOP_REQUESTED`, processed chunks `1,727` |
| Reference | `PRIMARY_PASS`, exported `5`, failed `0` |
| Official news | endpoint refresh `7/7`, retryable failures remain |
| GDELT | `13,869/367,872` chunks, `3.7701%`, cursor `20160524091500`, running |
| Marketaux | `94/26,499` units, `0.3547%`, daily cap exhausted for `2026-06-28` |
| Newswire live | PRNewswire, GlobeNewswire, BusinessWire; `4,750` rows |
| Newswire backfill | `1,761/4,099` archives, `42.9617%`, rows `15,970` |
| Context news live | `17/17` sources, rows `3,598`, blocked `0` |
| Context news backfill | `79/149` units, `53.0201%`, rows `125,115` |
| Market/macro live | `68/68` sources, rows `17,820`, blocked `0` |
| Market/macro backfill | `758/2,611` units, `29.031%`, rows `95,262` |
| Industry Dive backfill | `9/2,338` units, `0.3849%`, rows `943` |

## Weekend Work Summary

### 1. Newswire 3종 고도화

- Main collector: `tools/db/source_acquisition/public_newswire_collector.py`.
- Current important versions completed during the weekend: `v0.1.6` and `v0.1.7`.
- Added article metadata description evidence for historical sitemap/page rows.
- Added source-declared exchange-tag preservation, for example `(NYSE: AKS)` or `(NYSE: CVA)`, without enabling symbol-token fallback.
- Added RSS description/summary evidence for mapping and context classification.
- PRNewswire/GlobeNewswire sitemap backfill can fetch article metadata for mapping enrichment.
- BusinessWire remains supported through its sitemap/article metadata route.
- L2/no-trade/L3 validators passed for governed smokes.

Key docs:

- `docs/reports/task_l0_public_newswire_collector/task_l0_public_newswire_collector_report.md`
- `docs/reports/task_l0_public_newswire_collector/artifact_manifest.csv`
- `docs/reports/task_l0_public_newswire_collector/task_l0_public_newswire_collector_decision.csv`

### 2. Public Context News

- Official/macro context collector continues separately from newswire.
- Sources include Federal Reserve, BLS, BEA, CFTC, Federal Register, White House, Nasdaq Trader, CoinDesk, ECB, Bank of England, EIA, Defense.gov, World Bank, and related official context routes.
- These rows are context facts, not ticker-specific trading claims.
- Backfill is supported for selected official/archive paths such as Federal Register, Federal Reserve, CFTC, and World Bank.

Key docs:

- `docs/reports/task_l0_public_context_news_collector/task_l0_public_context_news_collector_report.md`

### 3. Public Market/Macro News Expansion

- Main collector: `tools/db/source_acquisition/public_market_macro_news_collector.py`.
- Current version after weekend work: `public_market_macro_news_collector.v0.1.11`.
- Live watcher now has `68` public RSS/HTML sources.
- Market/macro backfill now has `21` sources.
- Separate Industry/sector Dive backfill has `22` sources with crawl-delay handling.

Major live source groups:

- Mainstream/market: CNBC, Yahoo Finance, NYT, Fox Business, Investing.com, BBC, FT, MarketWatch.
- Crypto: Cointelegraph, Decrypt, CryptoSlate.
- Energy/commodities: OilPrice, Mining.com copper.
- Cyber/semiconductor/AI: BleepingComputer, KrebsOnSecurity, Semiconductor Engineering, The Verge, WIRED Business, SiliconANGLE, SecurityWeek.
- Sector/Dive: Utility, Supply Chain, BioPharma, Banking, Retail, CIO, Cybersecurity, Payments, Manufacturing, Food, Healthcare, PharmaVoice, Construction, CFO, Restaurant, Grocery, Marketing, HR, MedTech, Higher Ed, K-12, Smart Cities.
- Aggregator/ticker-rich: Seeking Alpha Market Currents, Finviz public headline page, StockTitan public RSS.
- v0.1.11 additions: IBD/Investors.com, InvestorPlace, FXStreet, Defense One, Nareit, ETF Trends, HousingWire, American Banker, Techmeme.

Major historical/backfill source groups:

- Guardian Open Platform, AP monthly sitemap, CNBC sitemap/article metadata, Wikimedia Current Events, CNN Money Common Crawl.
- WordPress REST: The Hill, TechCrunch, Electrek, Teslarati, Semiconductor Engineering, Bitcoin Magazine, 9to5Mac, 9to5Google, PV Magazine USA, SpaceNews, Carbon Brief, Robot Report.
- v0.1.11 WordPress additions: IBD/Investors.com, InvestorPlace, ETF Trends, HousingWire.
- Industry/sector Dive monthly sitemap backfill remains separate with 22 sector archives.

v0.1.11 smoke metrics:

| Source group | Result |
|---|---|
| New live RSS 9 sources | `289` rows, `0` blocked |
| New WordPress January 2016 backfill 4 sources | `310` rows, `0` blocked |
| Combined L2 smoke | `599` facts |
| Validators | `L2_NEWS_OK`, `L2_NO_TRADE_OUTPUT_OK`, `L3_L2_INPUT_OK` |

Key docs:

- `docs/reports/task_l0_public_market_macro_news_collector/task_l0_public_market_macro_news_collector_report.md`
- `docs/reports/task_l0_public_market_macro_news_collector/artifact_manifest.csv`
- `docs/reports/task_l0_public_market_macro_news_collector/task_l0_public_market_macro_news_collector_decision.csv`

### 4. Chrome Crawler Decision

- Chrome/Playwright headline crawler smoke was viable as a fallback.
- It is not the primary plan because selectors, robots/terms, CAPTCHA, and historical archive completeness are weaker than RSS/API/sitemap/WordPress REST.
- Current architecture is machine-readable-first; Chrome is fallback/verification only.

Key docs:

- `docs/reports/task_l0_public_headline_browser_crawler/task_l0_public_headline_browser_crawler_report.md`
- `docs/reports/task_l0_chrome_news_crawler_deep_review/task_l0_chrome_news_crawler_deep_review_report.md`
- `docs/reports/task_l0_free_news_source_mitigation_research/task_l0_free_news_source_mitigation_research_report.md`

## Important Current File Changes For Desktop Codex

- `configs/source_registry/l0_public_news_capability_sources.json`
- `configs/source_registry/l0_public_context_news_sources.json`
- `tools/db/source_acquisition/public_newswire_collector.py`
- `tools/db/source_acquisition/public_market_macro_news_collector.py`
- `tools/db/source_acquisition/l0_collection_status.py`
- `scripts/start_l0_public_newswire_collector.ps1`
- `scripts/start_l0_public_newswire_backfill.ps1`
- `scripts/start_l0_public_market_macro_news_collector.ps1`
- `scripts/start_l0_public_market_macro_news_backfill.ps1`
- `scripts/start_l0_public_industry_dive_news_backfill.ps1`
- `tests/test_l0_public_newswire_collector.py`
- `tests/test_l0_public_market_macro_news_collector.py`
- `tests/test_l0_collection_status.py`
- `tasks/task_registry.csv`

## Validation Commands

Run these on desktop after sync, before restarting collectors if possible:

```powershell
python scripts/report_l0_collection_status.py
python -m unittest tests.test_l0_public_newswire_collector tests.test_l0_public_market_macro_news_collector tests.test_l0_collection_status tests.test_l2_news_canonical_path tests.test_l3_source_reliability
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```

Known non-blocking warnings seen on notebook:

- `protected DB authority not DVC-tracked: trading.db`
- `protected DB authority not DVC-tracked: data/task388_intraday_canonical_continuation_engine.db`

## Desktop Codex First Checklist

- Read this file first.
- Run `python scripts/report_l0_collection_status.py`.
- Confirm notebook workers are stopped and OneDrive sync is complete.
- Confirm `.env` exists and API keys are available.
- Start desktop workers using the commands above.
- Re-run `python scripts/report_l0_collection_status.py` after 3 to 5 minutes.
- Keep reporting hourly progress from `data/artifacts/l0_collection_status/current_status.md`.
