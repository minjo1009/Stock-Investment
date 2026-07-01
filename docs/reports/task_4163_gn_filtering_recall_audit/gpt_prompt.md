You are a professional backend/data platform engineer, quant data infrastructure reviewer, and systematic trading research data reviewer.

Task:
Review and design a bounded fix for a GlobeNewswire / public newswire L0-L2 recall problem in a local uncommitted repository.

Important context:
- Do not rely on GitHub as current source of truth. The current local work is not fully committed or pushed.
- Use the local evidence packet below as authoritative for this review.
- You may still reason as an expert backend/data/quant reviewer, but do not assume GitHub has the latest L0/L1/L2 code.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence
- No buy/sell/ranking/sizing/order outputs

User goal:
Clearly define the problem, review how to modify/develop the system with GPT Pro, avoid overengineering, implement the reviewed design, and update already collected / currently collecting Layer 0 data under the improved logic.

Local problem definition:
GlobeNewswire L0 backfill preserves many raw headline rows, but current L0/L1 mapping logic can block too many economically relevant rows from becoming L1/L2 usable packets.

The issue is not simply that L0 discards data. The sharper issue is:

L0 raw headline exists
-> entity_mapping_status = BLOCKED_UNMAPPED
-> row becomes L1/L2 blocker or UNKNOWN collapse
-> important company/industry/macro/policy signal may not reach L2/L3/L4

Evidence snapshot from current local raw L0 GN backfill:

| Month | Raw headline rows | Mapped rows | Context rows | BLOCKED_UNMAPPED | Important keyword unmapped |
|---|---:|---:|---:|---:|---:|
| 2017-04 | 3900 | 606 | 279 | 3011 | 989 |
| 2023-04 | 1650 | 374 | 314 | 961 | 361 |
| 2024-06 | 750 | 150 | 89 | 511 | 103 |
| 2024-11 | 300 | 51 | 29 | 220 | 47 |
| 2025-12 | 1350 | 281 | 173 | 896 | 115 |

Evidence artifacts already created locally:
- data/artifacts/task_4163_gn_filtering_recall_audit/gn_recall_audit_summary.json
- data/artifacts/task_4163_gn_filtering_recall_audit/gn_important_unmapped_samples.csv

Concrete blocked examples:
- TrueCar Forecasts Industry Retail Sales Soar 34% for the 4th Quarter
- Willbros Reports Fourth Quarter and Full Year 2017 Results
- Merus' Interim Data on Petosemtamab...
- LAVA Medtech Acquisition Corp. Announces Liquidation
- Oak Woods Acquisition Corporation Announces Receipt of Nasdaq Notice...
- Fentura Financial, Inc. Announces Fourth Quarter 2024 Earnings

Current code facts:
- Main collector: tools/db/source_acquisition/public_newswire_collector.py
- `build_entity_mapper()` loads data/raw/alpaca_active_us_equity_universe.csv and keeps status=active and tradable=true.
- `company_aliases()` strips share descriptors and legal suffixes, then only keeps aliases passing `_alias_allowed()`.
- `_alias_matches()` requires exact unique alias substring match.
- `_exchange_tag_matches()` maps exchange-tagged symbols if symbol exists in the current mapper.
- Ambiguous aliases become BLOCKED_AMBIGUOUS_ENTITY.
- Otherwise rows become BLOCKED_UNMAPPED.
- `apply_newswire_context_classification()` only promotes a BLOCKED_UNMAPPED row to NOT_REQUIRED_CONTEXT_NEWSWIRE if deterministic title keywords match `NEWSWIRE_CONTEXT_TOPIC_RULES` and exclusion regex does not block.
- L1/L2 currently remain conservative: public newswire rows often stay discovery-only/blocker/UNKNOWN unless mapped or context-classified.

Likely root causes:
1. Survivorship bias: active/tradable current universe misses historical delisted/acquired/SPAC/renamed companies.
2. Exact alias only: company names with abbreviations, old names, SPAC names, ADR variants, punctuation, Unicode, suffix variation, or title phrasing miss mapping.
3. Context classifier too narrow: many industry/macro/policy/market-structure headlines do not get context admission.
4. Candidate hints are present but not broad enough and not being used as a review/admission path.

Required output from you:
1. Verdict: PASS / CONDITIONAL PASS / FAIL on the proposed problem framing.
2. Refined problem definition in simple operational terms.
3. Specific bounded design for implementation.
4. What NOT to do yet because it is overengineering or risky.
5. Exact fields/statuses to add or modify.
6. How to update already collected L0 raw safely.
7. How L1/L2 should consume the improved output without opening trading authority.
8. Validation checklist and smoke tests.
9. Prioritized patch plan for Codex.

Design constraints:
- Avoid overengineering.
- Do not require DB migrations unless absolutely necessary.
- Do not require external paid APIs.
- Do not make fuzzy matches authoritative.
- Do not open trading signal/order/sizing/paper/live gates.
- Do not delete raw data.
- Do not pause or destabilize the running L0 backfill.
- Existing/ongoing L0 raw must be reclassifiable under the improved logic.

Candidate low-overhead directions to review:
- Add `newswire_recall_review_flag`, `newswire_recall_topics`, `newswire_recall_reason`, and `newswire_recall_version`.
- Add deterministic broader topic groups for earnings/results, corporate actions, capital markets, exchange listing/compliance, clinical/FDA, M&A, partnerships/contracts, industry market reports, AI/semis/data center, energy/power/grid, defense/geopolitics, crypto/digital assets.
- Add `ENTITY_CANDIDATE_REVIEW` or similar non-authority status for plausible company rows that are not confidently mapped.
- Keep `symbols=[]` and `entity_mapping_inferred_flag=0` for non-authority candidates.
- Add a reclassification script that reads existing L0 raw headlines.json files and writes derived audit artifacts / optionally updated derived copies, preserving raw.
- Update L1/L2 intake to treat recall/context candidates as diagnostic candidates or review queues, not final trading features.

Please be concrete and pragmatic.
