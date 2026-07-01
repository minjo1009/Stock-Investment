# TASK-4163 GN Filtering Recall Audit Problem Definition

## Problem

GlobeNewswire L0 backfill preserves many raw headline rows, but current L0/L1 mapping logic can block too many economically relevant rows from becoming L1/L2 usable packets.

The issue is not simply that L0 discards data. The sharper issue is:

```text
L0 raw headline exists
-> entity_mapping_status = BLOCKED_UNMAPPED
-> row becomes L1/L2 blocker or UNKNOWN collapse
-> important company/industry/macro/policy signal may not reach L2/L3/L4
```

## Evidence Snapshot

Sample months from current local raw L0 GN backfill:

| Month | Raw headline rows | Mapped rows | Context rows | BLOCKED_UNMAPPED | Important keyword unmapped |
|---|---:|---:|---:|---:|---:|
| 2017-04 | 3900 | 606 | 279 | 3011 | 989 |
| 2023-04 | 1650 | 374 | 314 | 961 | 361 |
| 2024-06 | 750 | 150 | 89 | 511 | 103 |
| 2024-11 | 300 | 51 | 29 | 220 | 47 |
| 2025-12 | 1350 | 281 | 173 | 896 | 115 |

Evidence artifacts:

- `data/artifacts/task_4163_gn_filtering_recall_audit/gn_recall_audit_summary.json`
- `data/artifacts/task_4163_gn_filtering_recall_audit/gn_important_unmapped_samples.csv`

## Concrete Examples

Rows currently blocked as `BLOCKED_UNMAPPED` include examples that are plausibly relevant:

- `TrueCar Forecasts Industry Retail Sales Soar 34% for the 4th Quarter`
- `Willbros Reports Fourth Quarter and Full Year 2017 Results`
- `Merus' Interim Data on Petosemtamab...`
- `LAVA Medtech Acquisition Corp. Announces Liquidation`
- `Oak Woods Acquisition Corporation Announces Receipt of Nasdaq Notice...`
- `Fentura Financial, Inc. Announces Fourth Quarter 2024 Earnings`

## Likely Root Causes

| Cause | Current evidence |
|---|---|
| Current active universe only | `build_entity_mapper()` loads `data/raw/alpaca_active_us_equity_universe.csv` and keeps only active/tradable rows. Historical delisted/acquired/SPAC names are missing. |
| Exact alias matching only | `_alias_matches()` requires exact unique alias substring match. |
| Ambiguous aliases fail closed | Ambiguous aliases become `BLOCKED_AMBIGUOUS_ENTITY`. |
| Context classifier is keyword/title-only | `newswire_context_topics()` only checks deterministic title tokens and exclusion regex. |
| L1/L2 handoff treats many newswire rows as discovery/blockers | Prior reports intentionally kept public newswire rows conservative, but current evidence shows recall loss. |

## Desired Direction

Improve recall without opening trading authority:

1. Preserve precision for authoritative symbol mapping.
2. Add a second non-authority path for plausible company/entity candidates.
3. Add context-only admission for macro/policy/industry/market-structure news.
4. Avoid using missing/stale data as negative evidence.
5. Apply the improved classification to already collected L0 raw, not only future collection.

## Hard Boundaries

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- No buy/sell/ranking/sizing output.
- Candidate hints are not authority.
- Historical mapping must avoid lookahead and survivorship bias.

## Implementation Bias

Avoid overengineering. Preferred first pass:

- deterministic audit/classification fields
- bounded candidate hints
- review queue artifacts
- reclassification script for existing L0 raw
- validators proving no authority/trading gate opened

Defer heavy work unless proven necessary:

- full historical ticker master integration
- fuzzy matching as authority
- external enrichment APIs
- ML/NLP classifiers
- database migrations
