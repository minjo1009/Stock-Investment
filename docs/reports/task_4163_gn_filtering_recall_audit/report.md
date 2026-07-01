# TASK-4163 L0 Public Newswire Recall Hardening Report

## Summary

The concern was valid. L0 was preserving GlobeNewswire raw headlines, but too many economically relevant rows were collapsing into `BLOCKED_UNMAPPED` before L1/L2 could use them.

This task adds a non-authority recall path:

- authoritative ticker/entity mapping remains strict
- source-declared exchange tags can map historical symbols even outside the current active universe
- unmapped but material company/news rows become `ENTITY_CANDIDATE_REVIEW`
- context/news topics receive `newswire_recall_*` overlay fields
- symbols stay empty and authority flags stay closed for weak candidates
- existing L0 raw is not mutated; a derived overlay is generated for review/L1-L2 consumption

## GPT Pro Review

GPT Pro was given the local evidence packet and told not to use GitHub as current truth. The full Pro responses stalled in Chrome, but both visible partial responses converged on the same design:

```text
preserve raw data
separate authoritative ticker mapping from recall/review admission
keep weak/unmapped candidates non-authority
let L1/L2 consume them only as diagnostic/review candidates
```

Capture: `docs/reports/task_4163_gn_filtering_recall_audit/gpt_response.md`

## Implementation

| Area | Done |
|---|---|
| L0 collector | Added `newswire_recall_review_flag`, `newswire_recall_topics`, `newswire_recall_reason`, `newswire_recall_version`, `newswire_recall_candidate_authority_flag`. |
| Mapping | Kept exact alias strict. Added source-declared exchange-tag mapping for symbols outside current active universe. |
| Recall status | Added `ENTITY_CANDIDATE_REVIEW` for non-authority company/event candidates. |
| Context topics | Broadened deterministic topics for earnings, corporate actions, listing compliance, clinical/FDA, capital markets, industry reports, AI/semis, energy, defense/geopolitics, crypto, telecom, food supply chain, and economic development. |
| L1/L2 handoff | Passed `newswire_recall_review_rows` and `entity_candidate_review_rows` into wide ledger/packet/L2 rows. |
| Existing raw update | Added reclassification overlay script. Raw files are preserved; overlay/summary artifacts are written under this task. |
| Safety | No broker mutation, live order, paper promotion, or real-capital gate opened. |

## Evidence

GN latest shard reclassification result:

| Metric | Value |
|---|---:|
| Latest shard files processed | 330 |
| Rows processed | 32,050 |
| Recall/review rows | 12,040 |
| Rows whose mapping status changed | 10,225 |
| `ENTITY_CANDIDATE_REVIEW` after reclassify | 9,562 |
| Remaining `BLOCKED_UNMAPPED` | 15,235 |

Important examples now become non-authority recall candidates:

| Headline type | New handling |
|---|---|
| TrueCar industry retail sales forecast | `ENTITY_CANDIDATE_REVIEW`, topic `industry_market_report` |
| Willbros annual results | `ENTITY_CANDIDATE_REVIEW`, topic `earnings_results` |
| Merus clinical data | `ENTITY_CANDIDATE_REVIEW`, topic `clinical_regulatory` |
| LAVA Medtech liquidation | `ENTITY_CANDIDATE_REVIEW`, topic `corporate_actions` |
| Oak Woods Nasdaq notice | `ENTITY_CANDIDATE_REVIEW`, topic `listing_compliance` |
| Fentura earnings | `ENTITY_CANDIDATE_REVIEW`, topic `earnings_results` |

## Boundaries

This does not make public newswire rows trading-authoritative. It only prevents important unmapped rows from disappearing before review/diagnostic layers.

Still not done:

- no full historical ticker master integration
- no fuzzy match authority
- no external enrichment API
- no ML/NLP classifier
- no DB migration
- no automatic trading feature acceptance

## Validation

- `python -m pytest tests/test_l0_public_newswire_collector.py -q` passed: 25 tests.
- `python -m py_compile tools/db/source_acquisition/public_newswire_collector.py tools/db/source_acquisition/news_background_collector.py scripts/run_l0_l2_wide_handoff_4146.py scripts/reclassify_l0_public_newswire_recall_4163.py scripts/validate_l0_public_newswire_recall_4163.py` passed.
- `python scripts/validate_l0_public_newswire_recall_4163.py` passed.

