# TASK-4155 Context Packet: L4 Goal / Role / Development Plan Review

## Purpose

Ask GPT Pro to review and concretize Layer 4 (L4) for the trading operating system.

User request:

- Define L4's clear goal, role, detailed goals, and detailed responsibilities.
- Provide GPT Pro with Layer 0 through Layer 4 information.
- Get a concrete development plan for L4.

## Hard State

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is `UNKNOWN/BLOCKER`, never negative evidence
- L4 must not produce final policy actions, order intent, sizing, live/paper eligibility, or broker actions.

## Project Layer Model

| Layer | Current Role |
|---|---|
| L0 | Raw/source collection and source-time integrity |
| L1 | Normalize/packetize source data and preserve lineage |
| L2 | Convert admitted source data into diagnostic economic meaning candidates |
| L3 | Build diagnostic relation graph and relation-quality guard |
| L4 | Not yet implemented. Intended to construct and validate thesis bundles at institutional quality |

## L0 Current State

Selected current L0 status as of local status file:

| lane | status | progress | row_count / units | worker state |
|---|---:|---:|---:|---|
| public_newswire_backfill | RUNNING | 43.0139% | 24,162 rows / 1,764 of 4,101 units | RUNNING_ALIVE_INCOMPLETE |
| public_market_macro_news_backfill | RUNNING | 38.7591% | 138,232 rows / 1,012 of 2,611 units | RUNNING_ALIVE_INCOMPLETE |
| public_context_news_backfill | RUNNING | 99.3289% | 267,885 rows / 148 of 149 units | RUNNING_ALIVE |
| five_min_bars | active progress | 17.1556% | 66,147 of 385,280 units; DB rows 48,452,586 | RUNNING_ALIVE |
| daily_bars | active progress | 99.3771% | 11,965 of 12,040 units | RUNNING_ALIVE |

Important:

- Some L0 backfills are still incomplete.
- Missing/incomplete coverage must remain `UNKNOWN/BLOCKER`, not negative evidence.
- Chrome crawling is not the main runtime collector; Python collectors/backfill workers are the main collection path.

## L1 / L2 Current State

TASK-4147 article-level path:

| artifact | rows | notes |
|---|---:|---|
| L1 article packets | 1,093 | all `public_context_news_feeds`; all `READY` |
| L2 diagnostic feature rows | 1,842 | all `public_context_news_feeds` |

L1 article mapping:

- `HIGH_CONFIDENCE_DETERMINISTIC`: 1,022
- `MACRO_OR_CONTEXT_NO_TICKER_REQUIRED`: 71

TASK-4146 wide packetization path:

| artifact | rows | notes |
|---|---:|---|
| L1 wide normalized source packets | 2,252 | mixed L0 batch/wide packets |
| L2 feature materialization candidates | 1,052 | admitted/review-ready candidates |

L1 wide mapping:

- `NOT_EVALUATED`: 1,189
- `MACRO_CONTEXT_NO_SYMBOL_REQUIRED`: 843
- `NEWSWIRE_MAPPED_BY_L0_COLLECTOR`: 209
- `BLOCKED_UNKNOWN`: 11

L2 wide:

- `public_market_macro_news_feeds`: 432
- `public_context_news_feeds`: 411
- `public_newswire_feeds`: 209
- `MACRO_CONTEXT`: 843
- `NEWSWIRE_DISCOVERY`: 209
- `L2_CONTEXT_WIDE_ADMITTED`: 843
- `L2_NEWSWIRE_MAPPED_REVIEW_READY`: 209

## L3 Current State

TASK-4152 L3 relation graph v2:

| artifact | count |
|---|---:|
| relation edges | 7,150 |
| event clusters | 1,850 |
| relation graphs | 5,398 |
| coverage gaps | 181 |

Graph family quality summary from TASK-4154:

| graph_family | graph_count | edge_count | singleton_rate | interpretation |
|---|---:|---:|---:|---|
| COVERAGE_GAP | 2 | 181 | 0.0 | newswire gaps grouped into 2 week buckets |
| ENTITY_DIMENSION | 947 | 1,771 | 0.539599 | useful but sparse |
| ENTITY_EVENT | 1,771 | 1,771 | 1.0 | candidate event links only |
| MACRO_FACTOR | 828 | 828 | 1.0 | macro context candidates only, not causal theses |
| SOURCE_EVENT_CLUSTER | 1,850 | 2,599 | 0.659459 | proto event buckets, not confirmed same-event clusters |

Coverage gap summary:

| reason | bucket | count |
|---|---|---:|
| `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` | 2026-W26 | 166 |
| `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` | 2026-W27 | 15 |

Unsupported relation families:

| family | status | L4 interpretation |
|---|---|---|
| MACRO_SECTOR | NOT_IMPLEMENTED | absence is not negative evidence; macro-sector linkage not scanned/cleared |
| SECTOR_THEME | NOT_IMPLEMENTED | absence is not negative evidence; sector-theme linkage not scanned/cleared |
| CONTRADICTION | NOT_IMPLEMENTED | absence is not negative evidence; no contradiction scan/clear yet |

L3-to-L4 handoff manifest hard rules:

- diagnostic_only: true
- strategy_status: `NOT_ACCEPTED`
- deployment_status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real_capital: `FORBIDDEN`
- no_broker_mutation: true
- no_live_order: true
- no_paper_promotion: true
- event_identity_status: `PROTO_BUCKET`
- same_event_assertion: false

Forbidden L4 assumptions:

- graph count does not imply evidence quality
- `SOURCE_EVENT_CLUSTER` does not assert confirmed same event
- `ENTITY_EVENT` does not assert material event
- `MACRO_FACTOR` does not assert causal macro thesis
- absence of `CONTRADICTION` family does not mean no contradiction exists
- coverage gaps are `UNKNOWN/BLOCKER`, not negative evidence
- L3 output does not authorize ranking, sizing, order intent, paper/live trading, strategy acceptance, or deployment readiness

## Existing L4 Governance

`ops/task_profiles.yaml` profile:

`L4_THESIS_BUNDLE`

Purpose:

- Construct and validate thesis bundles at institutional quality.

Required principles:

- thesis_specificity
- evidence_linkage
- source_traceability
- contradiction_handling
- blocked_context_mixed_rate_visibility

Forbidden intents:

- final_policy_action
- broker_mutation
- live_order
- paper_promotion

Required checks:

- thesis_quality_review
- evidence_coverage
- source_access
- institutional_quality_score

`ops/profile_validation_rules.yaml` hard boundaries:

- strategy_status: `NOT_ACCEPTED`
- deployment_status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real_capital: `FORBIDDEN`
- live_order: `FORBIDDEN`

Existing skill file:

`.codex/skills/l4-thesis-bundle/SKILL.md`

It says L4 constructs and validates thesis bundles at institutional quality, with no final policy action, broker mutation, live order, real capital, paper promotion. Missing/stale data must be UNKNOWN/BLOCKER.

## Current L4 Implementation Reality

L4 appears to be governance/profile-level only.

Known existing L4 implementation:

- task profile exists
- profile validator exists
- skill file exists
- no current full L4 thesis bundle builder found
- no current L4 artifact schema found
- no current L4 validator for thesis bundle semantic shape beyond profile rules found

## What We Need GPT Pro To Review

Please define and critique L4 as the next layer after L0-L3.

The user wants:

1. L4 clear goal
2. L4 clear role
3. L4 detailed goals
4. L4 detailed responsibilities
5. What L4 should consume from L0-L3
6. What L4 must not do
7. Concrete L4 development plan
8. Artifact/schema/validator/test plan
9. P0/P1 priority list
10. Codex-executable patch prompt

Avoid over-engineering. L4 should be useful, auditable, and safe.

