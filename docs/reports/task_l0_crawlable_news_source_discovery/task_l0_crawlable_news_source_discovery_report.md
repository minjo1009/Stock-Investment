# Decision Summary

- Verdict: `PRIMARY_PASS` for source discovery; readiness remains `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this opens no trading, score, order, or deployment gate.
- Key metrics: 10 WordPress REST candidates were probed for January 2016. 7 returned historical rows, 1 returned no 2016 rows, and 2 were rate/permission blocked. 14 RSS candidates were probed; most returned current items. AP News monthly sitemap was probed and showed 6,924 URLs in 2016-01, with source page metadata available, but it requires conservative policy review and low-rate handling before any promotion.
- What changed: identified non-newswire source families for macro, crypto, energy, commodities, cyber, semiconductor, and big-tech ecosystem context.
- Next action: run governed smoke tests for the highest-priority RSS and WordPress REST candidates before adding them to the regular L0 collector.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Find free, crawlable non-newswire news sources/pages that can broaden L0 news beyond PRNewswire, GlobeNewswire, and BusinessWire. |
| Target Metrics | Real source response, source-time evidence, public machine-readable path, L1/L2 diagnostic-only compatibility, no ticker inference requirement. |
| Forbidden Actions | No login, paywall bypass, captcha bypass, stealth/proxy evasion, GPT-created headlines, inferred ticker certainty, trade output, score output, order intent, or deployment claim. |
| Available Raw Sources | Public RSS, WordPress REST posts endpoints, published sitemaps, page-level OpenGraph/article metadata. |
| Missing Raw Sources | Paid Reuters/Bloomberg archives, licensed Dow Jones content, and vendor-grade normalized historical news. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_crawlable_news_source_discovery/` |
| Large Artifact Directory | Not applicable; discovery-only probe used live HTTP checks and did not write raw captures. |
| Validation | `python scripts/task_registry_validate.py` |
| Completion Criteria | Prioritized candidate list with source URLs, evidence, risks, and next smoke path. |

# Quant Expert Report

## Data Source And Source Readiness

Highest-priority sources to smoke next:

| Priority | Source family | Candidate sources | Why it matters | Collection mode |
|---:|---|---|---|---|
| 1 | Crypto and digital assets | CoinDesk, Cointelegraph, Decrypt, CryptoSlate | BTC/crypto risk appetite, regulatory shocks, liquidity regime | RSS live/recent |
| 2 | Energy and commodities | OilPrice, EIA Today in Energy, Mining.com copper | Oil, power, uranium/metals, energy inflation, AI power demand | RSS live/recent |
| 3 | Cyber/security | BleepingComputer, KrebsOnSecurity, SecurityWeek feed | Cyber incidents that move software, cloud, security, geopolitics | RSS live/recent |
| 4 | Semiconductor and AI infrastructure | Semiconductor Engineering, The Register, Tom's Hardware | Chips, data centers, hardware supply chain | RSS plus selected WordPress REST |
| 5 | EV and clean energy extension | CleanTechnica, PV Magazine USA, 9to5Mac, 9to5Google | Tesla/EV/solar/battery and mega-cap ecosystem context | WordPress REST or RSS, rate-limited |
| 6 | Broad macro/public news archive | AP News monthly sitemap | Large 2016+ public news URL surface with article metadata | Sitemap then article metadata, policy-gated |

Observed probe evidence:

| Candidate | Probe result | Promotion view |
|---|---|---|
| `https://semiengineering.com/wp-json/wp/v2/posts` | January 2016 rows returned; `X-WP-Total=93` for the tested month | Strong historical backfill candidate |
| `https://9to5mac.com/wp-json/wp/v2/posts` | January 2016 rows returned; `X-WP-Total=322` | Useful Apple ecosystem context; needs relevance terms |
| `https://9to5google.com/wp-json/wp/v2/posts` | January 2016 rows returned; `X-WP-Total=290` | Useful Google/Android/Samsung ecosystem context; needs relevance terms |
| `https://bitcoinmagazine.com/wp-json/wp/v2/posts` | January 2016 rows returned | Useful crypto historical context; respect crawl delay |
| `https://pv-magazine-usa.com/wp-json/wp/v2/posts` | January 2016 row returned | Useful solar/energy, lower volume |
| `https://cleantechnica.com/wp-json/wp/v2/posts` | January 2016 rows returned, but robots reports `Crawl-delay: 600` | Usable only as very slow backfill/live lane |
| `https://apnews.com/sitemap.xml` and monthly `ap-sitemap-YYYYMM.xml` | 2016-01 sitemap had 6,924 URLs; sample page had `article:published_time`, `og:title`, `og:description` | Potentially large broad archive; requires policy review and strict low-rate mode |
| VentureBeat WordPress REST | HTTP 429 in probe | Do not promote now |
| Ars Technica WordPress REST | HTTP 403 in probe | Do not promote now |
| Reuters direct sitemap | HTTP 401 in probe | Do not promote direct crawler |
| Bloomberg direct sitemap | HTTP 403 in probe | Do not promote direct crawler |
| Nasdaq.com category RSS | Timeout in probe | Low priority until stable response is proven |

## Exact Join Keys

- Source candidate key: `source_key`, `source_url`, `capture_method`, `probe_time_utc`.
- Event key after promotion: `provider`, `source_id`, `source_url`, `published_at`, `raw_sha256`.
- L2 path remains diagnostic-only through `source_receipt_id`, `primitive_batch_id`, `primitive_id`, and lineage edge IDs.

## Leakage Audit

The discovery probes did not use returns, fills, labels, outcomes, model scores, or order data. Candidate promotion must keep ticker mapping optional for macro/industry context and must not infer firm-level relevance without evidence.

## Split/OOS Metrics

Not applicable. This is data-source discovery only.

## Failure Decomposition

- Direct premium media crawl is weak: Reuters and Bloomberg direct sitemap probes were blocked; these should not become primary free collectors.
- Some public sources respond but are not automatically acceptable. Robots, crawl delay, paywall status, and source terms must gate promotion.
- RSS feeds are excellent for live/recent context but usually insufficient for 2016+ full backfill.
- WordPress REST is the best free historical path when the endpoint allows date filtering and source timestamps.
- AP News is the largest discovered non-newswire archive candidate, but the collector must be slow, metadata-only, and policy-reviewed before use.

## Cost/Slippage Stress

Not applicable. No PnL or execution claim is made.

## Remaining Blockers

- Run real L0 smoke for the top RSS candidates and selected WordPress REST sources.
- Add source-specific relevance gates before regular collection to avoid dilution.
- Confirm robots and terms posture before AP sitemap promotion.
- Keep Chrome as fallback/verification, not a primary collection method.

## 2026-06-29 Follow-Up: Non-Newswire Source Search

Question: if newswire volume is still too thin, what other crawlable news pages/sources should we look at?

Short answer: yes, but prioritize public machine-readable sources, not generic Chrome page walking. The best next additions are official/public sources with RSS/API/archive surfaces:

| Priority | Source | Probe evidence | Best use | Next action |
|---:|---|---|---|---|
| 1 | World Bank News API | JSON returned `total=63481` documents in live probe | Large macro/geopolitical/development news archive | Build API backfill mode with date cursor and source URL evidence |
| 2 | ECB RSS | `press.html` and `statpress.html` returned 15 RSS items each | Monetary policy and Europe macro live context | Add to `public_context_news_feeds` smoke |
| 3 | BIS RSS | Press/all/speech RDF feeds returned 25 items each | Central-bank/global financial-system context | Add RSS smoke; parser already handles namespaced items in market/macro collector |
| 4 | Bank of England RSS | News and speeches feeds returned 50 items each | UK rates, regulation, financial-stability context | Add RSS smoke |
| 5 | EIA press RSS | Returned 8 items; existing Today in Energy already available | Energy/inflation/oil shock context | Add press feed beside Today in Energy |
| 6 | GovInfo RSS/API surface | Federal Register RSS returned 100 items; feeds page exposes many official collections | Official policy/regulatory archive | Keep Federal Register API path primary; evaluate govinfo bulk/API only for targeted collections |
| 7 | Defense.gov/DoD public RSS | Press and contracts RSS returned 10 items each | Defense/geopolitics/contracting context | Add cautious RSS smoke; no full-text scraping |

Deprioritized direct media crawl:

| Source family | Reason |
|---|---|
| Reuters/Bloomberg direct crawl | Prior probe saw blocked direct sitemap responses; do not use as a free primary crawler. |
| Generic Chrome crawling | Too brittle for historical full backfill; use only when RSS/API/sitemap/static metadata are unavailable or for visual verification. |
| Any source needing login/paywall/captcha bypass | Forbidden for this project. |

Implementation view:

1. Add official RSS sources first because they are low-risk and ticker mapping is not required.
2. Add World Bank as a separate backfill collector mode, not as a simple RSS source, because it exposes a large paginated JSON archive.
3. Keep AP monthly sitemap and WordPress REST backfills running for breadth, but do not treat them as complete market news coverage until source-level completeness is audited.
4. Route these rows as macro/context facts in L2/L3, not ticker-specific company news unless deterministic source evidence supports mapping.

# No-Background Decision-Maker Report

Yes, we should look beyond newswires. The best free direction is not generic Chrome crawling. It is a source ladder:

1. Public RSS for live/recent macro, crypto, energy, cyber, and semiconductor context.
2. WordPress REST for historical backfill where date filters and source timestamps work.
3. Sitemaps plus page metadata only for very broad archives such as AP News, after policy and rate-limit review.

The immediate candidates that look most useful are CoinDesk/Cointelegraph/Decrypt/CryptoSlate for crypto, OilPrice/EIA/Mining.com for energy and commodities, BleepingComputer/Krebs/SecurityWeek for cyber, and Semiconductor Engineering/9to5Mac/9to5Google/Bitcoin Magazine/PV Magazine for historical industry context.

This still does not create trading readiness. It only increases L0 context coverage.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory.
