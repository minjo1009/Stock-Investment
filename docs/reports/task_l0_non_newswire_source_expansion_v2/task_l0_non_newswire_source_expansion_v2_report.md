# Decision Summary

- Verdict: `PRIMARY_PASS` for non-newswire source expansion discovery.
- Strategy acceptance status: `NOT_ACCEPTED`; this opens no trading, score, order, or deployment gate.
- Readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: 18 public RSS candidates returned current items; 15 RSS candidates were promoted to live smoke and produced 75 rows. AP News January 2016 monthly sitemap returned article URLs and produced source-meta rows in governed smoke. Three WordPress REST backfill sources are promoted: SpaceNews, Carbon Brief, and Robot Report. CleanTechnica is not promoted for historical backfill because the smoke showed its date filter returning latest 2026 rows. Politico RSS/sitemap returned 403, and SecurityWeek/STAT WordPress backfill routes are blocked by robots despite RSS being usable.
- What changed: added a governed v0.1.7 expansion path to the market/macro collector defaults: 15 RSS live candidates, AP monthly sitemap historical backfill, and three WordPress historical backfill sources.
- Next action: monitor the restarted market/macro background workers and the first full 37-source live / 17-source backfill cycles.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Find free non-newswire public news sources or pages that can materially broaden L0 news collection beyond newswires. |
| Target Metrics | Real response, source timestamp evidence, repeatable machine-readable route, and L2 diagnostic compatibility. |
| Forbidden Actions | No login, paywall bypass, captcha bypass, stealth/proxy evasion, GPT-created headlines, inferred ticker certainty, trade output, score output, order intent, or deployment claim. |
| Available Raw Sources | Public RSS, WordPress REST posts endpoints, published sitemaps, page-level article metadata, and existing L0 collectors. |
| Missing Raw Sources | Licensed Reuters/Bloomberg/Dow Jones archives and vendor-normalized historical news. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_non_newswire_source_expansion_v2/` |
| Large Artifact Directory | Not applicable; this was discovery-only and did not write raw captures. |
| Validation | `python -m unittest tests.test_l0_public_market_macro_news_collector`; `python scripts/validate_l2_news_canonical_path.py --db-path data/artifacts/l0_pm_non_newswire_v2_l2_smoke/news_l2_smoke.db`; `python scripts/validate_l2_no_trade_outputs.py --db-path data/artifacts/l0_pm_non_newswire_v2_l2_smoke/news_l2_smoke.db`; `python scripts/validate_l3_inputs_are_l2_canonical.py --db-path data/artifacts/l0_pm_non_newswire_v2_l2_smoke/news_l2_smoke.db`; `python scripts/task_registry_validate.py` |
| Completion Criteria | Prioritized candidate list with source route, probe evidence, risk class, and next smoke action. |

# Quant Expert Report

## Data Source And Source Readiness

The best immediate sources are not ticker-selected pages. They are source-level feeds and archives that can fill macro, policy, geopolitics, AI, cyber, energy, supply chain, biotech, defense, space, and logistics context.

Governed smoke results:

| Lane | Sources | Rows | L2 result |
|---|---:|---:|---|
| RSS live smoke | 15/15 exported | 75 | Combined L2 smoke succeeded |
| Historical backfill smoke | 4/4 exported | 17 | Combined L2 smoke succeeded |
| Combined L2 ingestion | 19 L0 events | 92 facts | `L2_NEWS_OK`, `L2_NO_TRADE_OUTPUT_OK`, `L3_L2_INPUT_OK` |

| Priority | Source family | Candidate sources | Best mode | Current view |
|---:|---|---|---|---|
| 1 | Broad public archive | AP News monthly sitemaps | sitemap plus page metadata | Largest new historical candidate; policy-gated low-rate smoke required. |
| 2 | Live macro and policy | Axios RSS | RSS | Useful current policy and macro context; smoke before promotion. |
| 3 | Tech, AI, cloud | The Verge, Wired Business, SiliconANGLE | RSS | Good live context; historical backfill would need separate sitemap or archive path. |
| 4 | Cyber | SecurityWeek RSS, Dark Reading, The Record | RSS | Good live cyber context; SecurityWeek WP backfill is blocked by robots. |
| 5 | Energy and supply chain | Utility Dive, Supply Chain Dive, FreightWaves, The Loadstar | RSS | Good live context; Dive feeds need slow crawl-delay handling. |
| 6 | Biotech and healthcare | BioPharma Dive, Fierce Biotech, STAT RSS | RSS | Useful healthcare context; STAT WP backfill is blocked by robots. |
| 7 | Defense and space | Breaking Defense, Defense News, SpaceNews | RSS and selected WordPress REST | SpaceNews WordPress is a strong historical candidate. |
| 8 | Climate and robotics | Carbon Brief, Robot Report | WordPress REST | Historical candidates with relevance gates. CleanTechnica is excluded from historical promotion until a date-safe archive route is proven. |

## Exact Join Keys

- Source discovery key: `source_key`, `source_url`, `capture_method`, `captured_at`.
- L0 event key after promotion: `provider`, `source_id`, `source_url`, `published_at`, `raw_sha256`.
- L2 diagnostic key: `source_receipt_id`, `primitive_batch_id`, `primitive_id`, and lineage edge IDs.

## Leakage Audit

No labels, outcomes, returns, fills, scores, order data, or strategy decisions were used. These sources are context inputs only. Ticker/entity mapping is optional for macro and industry context and must remain evidence-bound when used.

## Split/OOS Metrics

Not applicable. This is source acquisition discovery, not strategy validation.

## Failure Decomposition

- Newswires are too narrow because direct ticker mapping is sparse and many useful events are macro or industry context rather than issuer-specific.
- Generic Chrome crawling is weaker than machine-readable routes because selectors drift, provenance is harder, and historical backfill is unreliable.
- RSS is good for live/recent coverage but weak for 2016+ backfill.
- WordPress REST is the best free historical route when date filters and source timestamps work.
- Sitemaps can create large archive coverage, but they need strict source policy, rate control, article metadata validation, and duplicate control.
- Premium direct crawls such as Reuters and Bloomberg remain out of scope under the no-paid-source constraint.

## Cost/Slippage Stress

Not applicable. No PnL changed.

## Remaining Blockers

- Monitor the promoted RSS candidates in the regular 37-source live watcher.
- Monitor AP sitemap/page-metadata, SpaceNews, Carbon Brief, and Robot Report in the regular 17-source historical backfill lane.
- Do not promote CleanTechnica historical backfill until a date-safe archive route is proven.
- Add relevance gates before promotion so broad sources do not flood L2 with low-signal text.
- Keep rows diagnostic-only until L2/L3 evidence, reliability, and calibration gates are validated.

# No-Background Decision-Maker Report

Yes, we should look beyond newswires. The strongest path is not Chrome-first scraping. It is:

1. RSS for live/recent market context.
2. WordPress REST for historical backfill where date filters are proven.
3. Sitemaps plus article metadata for broad archive sources such as AP.

The most useful new directions are now attached or queued in the regular collector defaults: AP for broad historical news, Axios for policy/macro live context, tech/AI feeds such as The Verge/Wired/SiliconANGLE, cyber feeds, energy/supply-chain feeds, biotech feeds, and defense/space feeds. This can make the dataset much less sparse, but it remains L0/L2 diagnostic infrastructure, not trading permission.

# Artifact Manifest

See `artifact_manifest.csv` in this directory.
