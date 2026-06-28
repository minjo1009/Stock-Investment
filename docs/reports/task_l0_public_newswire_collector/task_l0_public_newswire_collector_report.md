# Decision Summary

- Verdict: `PRIMARY_PASS`; PRNewswire, GlobeNewswire, and BusinessWire were added as governed L0 public newswire collectors, deterministic ticker/entity mapping succeeds, and bounded historical backfill smoke now works.
- Strategy acceptance status: `NOT_ACCEPTED`; this is data acquisition infrastructure only.
- Key metrics: mapping smoke v3 exported 75 headline rows total, 23 mapped/L1-ready-discovery rows, 52 intentionally blocked-unmapped rows, and 0 ambiguous rows. Context refinement smoke v9 exported 100 rows: 35 deterministic ticker-mapped rows, 35 `NOT_REQUIRED_CONTEXT_NEWSWIRE` rows, 29 still-blocked rows, and 1 ambiguous row. v0.1.4 mapping smoke exported 100 rows from currently responding sources: GlobeNewswire 34 L1-ready/16 blocked and BusinessWire 40 L1-ready/10 blocked, with PRNewswire currently empty. v0.1.6 PRNewswire January 2016 backfill smoke exported 80 rows, 16 mapped rows, 4 context-ready rows, and 1 source-declared exchange-tag mapping outside the active universe; AK Steel 2016 raw replay maps `AKS` from article metadata `(NYSE: AKS)`. v0.1.7 GlobeNewswire January 2016 backfill smoke exported 80 rows, 11 mapped rows, 11 context-ready rows, and 4 source-declared exchange-tag mappings from article metadata description enrichment. v0.1.7 L2 smoke materialized 80 facts and passed L2/L3/no-trade validators. Regular watcher was restarted under PID `9456`; historical backfill worker was restarted under PID `16756`. Latest status reports Newswire rows `4450`, L1-ready-discovery `1969`, L1-context-ready `808`; Newswire backfill rows `14170`, L1-ready-discovery `3009`, L1-context-ready `838`.
- What changed: added `public_newswire_feeds` source family, RSS/sitemap/static collector, deterministic ticker/entity mapper, expanded context-candidate classification for unmapped market/industry/AI/crypto/capital-markets/fixed-income/corporate-results/defense/infrastructure themes, gzip sitemap support, historical backfill mode, runner, background wrappers, L1/L2 provider support, L0 status reporting, scheduler entry, tests, source registry corrections, v0.1.6 source-declared exchange-tag mapping for historical symbols missing from the current active universe, and v0.1.7 article metadata description enrichment for PRNewswire/GlobeNewswire sitemap rows.
- Next action: keep the watcher and conservative historical backfill running, then continue auditing blocked rows for high-signal context terms without opening ticker inference.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Check SEC credential posture and attach the three feasible public newswire sources as L0 collectors after smoke validation. |
| Target Metrics | SEC key requirement clarified; PRNewswire, GlobeNewswire, BusinessWire smoke; deterministic ticker/entity mapping; regular watcher path; historical backfill path; L1/L2 diagnostic ingestion; no trade/score output. |
| Forbidden Actions | No login, paywall, captcha bypass, stealth/proxy evasion, GPT-created headlines, inferred ticker certainty, or deployment claim. |
| Available Raw Sources | Public PRNewswire sitemap/news pages/monthly gzip indexes, GlobeNewswire monthly news sitemaps, BusinessWire RSS/daily gzip sitemaps, source capability registry. |
| Missing Raw Sources | Historical source-time certification for backtest eligibility; rows without exchange tag or exact unique alias remain blocked rather than inferred. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_public_newswire_collector/` |
| Large Artifact Directory | `data/artifacts/l0_public_newswire/` |
| Validation | Unit tests, real-network mapping smoke, context-refinement smoke, bounded real-network backfill smoke, regular background restart, L2 ingest smoke, L2 validators, registry/closeout validators. |
| Completion Criteria | Three public newswire sources export watcher and backfill rows with raw evidence, deterministic mapping metadata, and L0 progress reporting while all trading gates stay closed. |

# Quant Expert Report

## SEC Credential Posture

`.env` was checked without printing secret values. No `SEC` or `EDGAR` API key is present. This is not a blocker because the SEC EDGAR API/index route does not require an API key in this project design; it requires fair-access behavior and a User-Agent. The collector stack uses explicit User-Agent strings and does not need to request a SEC API key from the operator.

## Data Source And Source Readiness

The new provider is `public_newswire_feeds`.

| Source | Route | Smoke Rows | Regular Path |
|---|---|---:|---|
| PRNewswire | news sitemap / public release URLs | 25 rows; 4 mapped | enabled via background collector |
| GlobeNewswire | news sitemap | 25 rows; 13 mapped | enabled via background collector |
| BusinessWire | public RSS/gzip sitemap | 25 rows; 6 mapped | enabled via background collector |

The first smoke exposed a PRNewswire quality issue where overview/category links were included. The collector was tightened to emit only probable article URLs for static HTML fallback and the v2 smoke was rerun successfully.

Current regular background collector:

- PID: `9456`
- Event path: `data/artifacts/l0_public_newswire/collector_events.jsonl`
- Progress path: `data/artifacts/l0_public_newswire/collector_progress.json`
- Rows at latest status snapshot: see `data/artifacts/l0_collection_status/current_status.md`

## Deterministic Entity Mapping

Rows are mapped only when the headline/evidence span contains one of:

- An explicit exchange tag such as `(NASDAQ: FUTU)` or `(NASDAQ: MSTR, STRF, STRC, STRK, STRD)`. Active-universe symbols keep their universe entity record. v0.1.6 also preserves source-declared exchange tags for historical symbols that are no longer in the current active universe, with `entity_source=public_newswire_source_declared_exchange_tag` and `active_universe_match_flag=0`.
- A unique exact company legal-name alias from the active/tradable universe, after conservative legal-suffix normalization.

Ticker-token-only matching is forbidden. Ambiguous aliases are blocked. Exchange names such as `NASDAQ` are blocked as company aliases to avoid false `NDAQ` matches. Mapping fields are preserved in raw rows and L2 primitive payloads: `symbols`, `entities`, `entity_map`, `entity_mapping_status`, `entity_mapping_methods`, `entity_mapping_version`, and `entity_mapping_inferred_flag=0`.

## Context Candidate Refinement

Newswire rows without deterministic ticker evidence are no longer all treated the same. Rows about macro, policy, AI infrastructure, capital markets, space/satellite, energy transition, mobility, defense drones, crypto, consumer trends, healthcare innovation, or industry market reports are marked as `NOT_REQUIRED_CONTEXT_NEWSWIRE`.

This is not ticker inference. These rows keep `symbols=[]`, `ticker_mapping_required_flag=0`, `macro_context_candidate_flag=1`, and `context_classification_methods=["deterministic_newswire_context_keyword"]`. Low-signal legal, lawsuit, law-firm, personal-injury, lawn-care, supplement, realtor, and similar promotional rows remain blocked.

Real smoke v9 result:

| Metric | Count |
|---|---:|
| Total rows | 100 |
| Deterministic ticker-mapped rows | 35 |
| Context-ready unmapped rows | 35 |
| Still blocked rows | 29 |
| Ambiguous rows | 1 |

The L2 smoke DB materialized 101 facts and passed both canonical-path and no-trade-output validators.

The v0.1.3 refinement adds deterministic context capture for fixed-income/central-bank auction headlines, listings and covered warrants, repo matching, corporate-results headlines, defense/aerospace tests, and infrastructure/construction technology. It still does not map those rows to tickers unless exchange-tag or exact unique alias evidence exists.

The v0.1.4 mapper tightens exact-alias normalization without opening symbol-token fallback:

- HTML entities are unescaped before alias matching, so titles such as `Bed Bath &amp; Beyond` can match an active universe company alias.
- `Common Shares` is stripped as a share descriptor, so `POET Technologies Inc. Common Shares` normalizes to a company alias instead of remaining blocked.
- Recent production replay confirmed deterministic improvements: the latest GlobeNewswire sample moved two POET rows from blocked to mapped, and the latest BusinessWire sample moved one Bed Bath & Beyond row from blocked to mapped. Ambiguous aliases such as Zillow Group remain blocked.

The v0.1.6 mapper closes a historical backfill survivorship gap without opening inference. Article HTML metadata descriptions are now included in the mapping evidence span. If the source text explicitly says `(NYSE: AKS)`, the collector preserves `AKS` even if that symbol is absent from the current active universe. Existing raw replay confirmed AK Steel's 2016 release maps from `/PRNewswire/ -- AK Steel (NYSE: AKS) ...`; the row is marked as source-declared rather than active-universe-verified.

The v0.1.7 mapper adds controlled article metadata enrichment for PRNewswire and GlobeNewswire sitemap rows. Sitemap titles remain the headline source, but article metadata descriptions are fetched and used as mapping evidence where available. Real GlobeNewswire January 2016 smoke found source-declared exchange tags such as `NYMT`, `MVC`, `CHEV`, and `EFUT` in metadata descriptions that were missing from sitemap titles.

## Historical Backfill Mode

Historical backfill is separate from the 30-minute watcher. It writes to separate default paths under `data/raw/l0_public_newswire_backfill/` and `data/artifacts/l0_public_newswire_backfill/`.

| Source | Backfill route | Smoke result |
|---|---|---:|
| PRNewswire | latest `sitemap-news.xml?page=N` plus monthly gzip indexes where available | 5 rows, 0 mapped |
| GlobeNewswire | monthly `https://sitemaps.globenewswire.com/news/en/YYYY-MM.xml` | 5 rows, 0 mapped |
| BusinessWire | daily gzip `.../home/YYYY-MM-DD.xml.gz` plus article HTML meta titles | 5 rows, 5 mapped |

Backfill stores cursor state by source, archive URL, and entry offset, so large monthly/daily archives can resume without repeating the first rows. Article-page fetches are throttled by `request_sleep_seconds`.

The 2016~ historical backfill worker is running separately from the 30-minute watcher:

- PID: `16756`
- Event path: `data/artifacts/l0_public_newswire_backfill/collector_events.jsonl`
- Progress path: `data/artifacts/l0_public_newswire_backfill/collector_progress.json`
- Current status snapshot: see `data/artifacts/l0_collection_status/current_status.md`
- BusinessWire note: older S3 daily archives can return `403 Forbidden` for unavailable/nonexistent dates instead of `404`; those are recorded as `unavailable_archive_urls` and skipped so the collector does not loop on the same date.

## Exact Join Keys

- L0 event key: `provider`, `source_id`, `raw_sha256`, `updated_at`.
- Raw payload key: `provider`, `source_key`, `captured_at`, `headline_hash`.
- Headline identity key: `headline_hash = sha256(provider, source_key, title, source_url, published_at)`.
- Entity mapping key: exchange/ticker span or exact unique alias evidence only. No proximity fallback and no symbol-token fallback.

## Leakage Audit

Rows store `detected_at`, `captured_at`, `published_at_text`, `source_time_certified_flag`, and `usable_for_historical_backtest_flag`. Newswire rows remain ineligible for historical backtest use unless source-time certification and entity mapping are separately validated.

## Hallucination Audit

No GPT-generated headlines or ticker assignments are created. Every row comes from fetched RSS/news-sitemap/static public source content and has raw response metadata, payload JSON, event hash, provider lineage, and mapping method evidence. Rows without deterministic evidence remain blocked.

## Failure Decomposition

- PRNewswire overview-link capture: fixed by stricter article URL filter and explicit news sitemap route.
- BusinessWire robots issue: same-origin robots-disallowed help page remains non-primary; collector uses public feed URL and gzip sitemap fallback.
- Entity mapping false-positive: `NASDAQ` was initially caught as `Nasdaq Inc.`; exchange-name aliases are now blocked and regression-tested.
- Current-active-universe survivorship gap: v0.1.6 preserves explicit source-declared exchange tags for historical symbols outside the active universe; rows without exchange tag or exact unique alias evidence remain blocked.
- Language/region breadth: BusinessWire and PRNewswire can emit non-English/global releases; downstream filters must be explicit rather than assumed.
- Sparse direct ticker coverage: improved by context-candidate routing and the v0.1.3 mapper, but still not solved by newswire alone; non-newswire context collectors remain required.

## Split/OOS Metrics

Not applicable. This is source acquisition infrastructure.

## Cost/Slippage Stress

Not applicable. No PnL, execution, order, broker, or capital decision is made.

## Remaining Blockers

- Add source-time certification gates for historical evaluation.
- Decide whether to keep global/non-English releases or add an explicit language filter.
- Continue expanding non-newswire public context sources where RSS/API/archive routes are explicit.
- Continue monitoring the separate Newswire backfill lane until PRNewswire/GlobeNewswire archives and the BusinessWire available-date range are exhausted.

# No-Background Decision-Maker Report

SEC does not need an API key here. We do not have one in `.env`, and that is fine.

The three new actionable sources are PRNewswire, GlobeNewswire, and BusinessWire. They are now attached as a real collector, not Chrome. The collector uses RSS/sitemap/public structured routes first.

Smoke passed, ticker/entity mapping is now present, the regular background collector is running, and a separate historical backfill mode is running. The v0.1.7 mapper also catches explicit historical tickers in article metadata such as `AK Steel (NYSE: AKS)` or GlobeNewswire metadata descriptions with `Nasdaq:NYMT`, even when the ticker is no longer in the current active universe. These rows are still not trading signals because the provider remains discovery-only and historical source-time certification is not granted.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
