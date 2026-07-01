# TASK-4151 L3 Relation Graph Context Packet

## Purpose

Ask GPT Pro to review whether current Layer 3 relation graph implementation is too primitive, why it only produced 27 relation graphs, and how to concretely improve Layer 3 relation graph design.

Use this packet as local current-state evidence. Do not rely on GitHub as current state because recent L0-L3 work is local and uncommitted.

## Required Expert Roles

- Professional Backend Engineer
- Professional Trader
- Quant Data Infrastructure Reviewer

## Hard State

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = `UNKNOWN/BLOCKER`, never negative evidence
- L3 may emit diagnostic economic meaning and relation review state only
- L3 must not emit BUY/SELL, ranking, sizing, order intent, paper/live eligibility, broker mutation, strategy acceptance, or deployment readiness

## User Concern

The user thinks Layer 3 still looks very early. The strongest concern is:

> relation graph count is only 27, which feels too low and hard to understand given the amount of L0 raw/source data.

The user wants GPT Pro to review:

1. What Layer 3's goal should concretely be.
2. Whether current relation graph design is too coarse or too narrow.
3. How to make relation graphs richer, broader, and more useful without turning them into trading signals.
4. How to use available raw/source/L0-L2 data properly through L1/L2 gates.

## Current L0 State

`data/artifacts/l0_collection_status/current_status.json`:

| Source / lane | Status | Progress | Rows / units |
|---|---:|---:|---:|
| `public_context_news_backfill` | RUNNING | `99.3289%` | `267885` rows |
| `public_newswire_backfill` | RUNNING | `42.9651%` | `19562` rows |
| `public_market_macro_news_backfill` | RUNNING | `33.7802%` | `113492` rows |
| `five_min_bars` | in progress | `16.0901%` | `62042 / 385280` units |
| `daily_bars` | in progress | `99.3688%` | `11964 / 12040` units |

Current interpretation:

- L0 collectors/backfill workers are alive and producing data.
- Newswire and market/macro coverage is still incomplete.
- L3 must expose coverage gaps, not treat missing news as negative evidence.

## Current L1/L2 State

From `TASK-4146` wide handoff:

- L0 batch rows: `2019`
- L0 raw item rows reported: `400939`
- L1 packet rows: `2019`
- L1 ready packet rows: `950`
- L1 blocked packet rows: `1069`
- L2 rows: `2019`
- L2 admitted/review rows: `950`
- Feature candidate materialization rows: `950`
- Feature candidate count: `384593`
- Trading authority opened rows: `0`
- Paper/live/broker/order opened rows: `0`

L1 wide packet mapping distribution:

| mapping_status | count |
|---|---:|
| `NOT_EVALUATED` | `1058` |
| `MACRO_CONTEXT_NO_SYMBOL_REQUIRED` | `766` |
| `NEWSWIRE_MAPPED_BY_L0_COLLECTOR` | `184` |
| `BLOCKED_UNKNOWN` | `11` |

L2 wide candidate distribution:

| field | value | count |
|---|---|---:|
| source_family | `public_context_news_feeds` | `411` |
| source_family | `public_market_macro_news_feeds` | `355` |
| source_family | `public_newswire_feeds` | `184` |
| mapping_status | `MACRO_CONTEXT_NO_SYMBOL_REQUIRED` | `766` |
| mapping_status | `NEWSWIRE_MAPPED_BY_L0_COLLECTOR` | `184` |
| event_domain | `MACRO_CONTEXT` | `766` |
| event_domain | `NEWSWIRE_DISCOVERY` | `184` |

From `TASK-4147` article hardening:

- L1 article packets: `1093`
- L1 article ready packets: `1093`
- raw article packet blockers: `0`
- L2 diagnostic feature rows: `1842`
- Newswire mapping review queue rows: `207`
- Newswire L0 mapped rows: `3212`
- Trading eligible rows: `0`
- Signal/order export allowed rows: `0`
- Broker mutation permitted rows: `0`

Important limitation:

- Current L1 article packet artifact is only `public_context_news_feeds`.
- Current L1 article packet source key distribution is `cftc_press_releases: 1093`.
- Current L2 diagnostic feature artifact is only `public_context_news_feeds / cftc_press_releases / official_context_article_presence`.
- Newswire has mapped rows and mapping queue, but not yet broad article-level L2 diagnostic features in the same way.

## Current L3 Implementation

`TASK-4150 L3 Diagnostic Strategy View Bootstrap Implementation`

Current outputs:

- L3 input primitives: `2780`
- L3 meanings: `2780`
- L3 evidence edges: `2780`
- L3 relation graphs: `27`
- L3 rejected/review queue: `0`
- L3 coverage gaps: `2`
- blocker/gap rows: `2`
- row reconciliation: balanced
- L3 validator: `PASS`, failures `0`

Current graph states:

| graph_state | count |
|---|---:|
| `RISK_DOMINANT_REVIEW` | `9` |
| `CONTEXT_ONLY` | `11` |
| `MIXED_REVIEW` | `5` |
| `SUPPORT_DOMINANT_REVIEW` | `2` |

Current graph examples:

| graph_key | graph_state | edge_count |
|---|---|---:|
| `MACRO|cftc_press_releases|CUSTOMER_ORDER|swing_1m` | `RISK_DOMINANT_REVIEW` | `18` |
| `MACRO|cftc_press_releases|GUIDANCE|swing_1m` | `CONTEXT_ONLY` | `1` |
| `MACRO|cftc_press_releases|REGULATORY|swing_1m` | `RISK_DOMINANT_REVIEW` | `52` |
| `MACRO|public_context_news_feeds|MACRO_CONTEXT|swing_1m` | `CONTEXT_ONLY` | `119` |
| `MACRO|public_context_news_feeds|RATES|swing_1m` | `CONTEXT_ONLY` | `277` |

Current L3 meaning distribution:

| source_family | target_node_type | economic_dimension | direction_review | count |
|---|---|---|---|---:|
| `public_context_news_feeds` | `SYMBOL` | `REGULATORY` | `CONTEXT_ONLY` | `839` |
| `public_market_macro_news_feeds` | `MACRO` | `MACRO_CONTEXT` | `CONTEXT_ONLY` | `346` |
| `public_context_news_feeds` | `SYMBOL` | `CUSTOMER_ORDER` | `RISK_REVIEW` | `323` |
| `public_context_news_feeds` | `SYMBOL` | `REGULATORY` | `RISK_REVIEW` | `306` |
| `public_context_news_feeds` | `MACRO` | `RATES` | `CONTEXT_ONLY` | `277` |
| `public_context_news_feeds` | `SYMBOL` | `CUSTOMER_ORDER` | `CONTEXT_ONLY` | `235` |
| `public_newswire_feeds` | `SOURCE_FAMILY` | `UNKNOWN` | `CONTEXT_ONLY` | `181` |

## Why 27 Graphs Likely Happened

Current Codex inference:

1. Graph key is too coarse:
   - currently roughly `target_node_type | target_node_key | economic_dimension | swing_1m`.
2. The article-level L2 diagnostic input is too narrow:
   - mostly `public_context_news_feeds / cftc_press_releases`.
3. Newswire is not yet represented as rich ticker/entity/article-level L3 edges:
   - `181` rows appear as `SOURCE_FAMILY | UNKNOWN | CONTEXT_ONLY`.
4. L3 does not yet model multi-axis relation graphs:
   - entity-event
   - entity-sector
   - macro-sector
   - macro-factor
   - source-event-cluster
   - time-window
   - contradiction
   - catalyst-chain
   - supply-chain/theme graph
5. L3 currently avoids direct raw L0 reads, correctly, but it may need broader L1/L2 packetization before it can graph more relationships.
6. Current L3 is a bootstrap, not final relation graph design.

## What GPT Should Review

Please review as both:

1. Professional Backend Engineer: data model, pipeline, graph key design, artifact/schema plan, validator plan.
2. Professional Trader: what relation graphs are actually useful for swing trading research without creating premature trading signals.

Questions:

1. Is 27 relation graphs obviously too low given the current available L0-L2 data, or is it expected because current L2/L3 input is narrow?
2. What should the Layer 3 goal be, concretely, for this project?
3. What should count as a relation graph in Layer 3?
4. What graph grains should exist?
   - by entity/ticker?
   - by source event cluster?
   - by economic dimension?
   - by macro factor?
   - by sector/theme?
   - by horizon/effect window?
   - by source family/provider?
   - by evidence chain?
5. How should L3 use public newswire, public market/macro news, public context news, daily bars, and five-minute bars without leakage or premature signal creation?
6. Should price bars enter L3 at all now, or only later as diagnostic context/calibration artifacts?
7. How should L3 expand relation graphs while preserving:
   - no direct L0 raw bypass
   - missing/stale/incomplete = UNKNOWN/BLOCKER
   - no BUY/SELL/rank/sizing/order
   - diagnostic-only state
8. What should be implemented next as the highest-impact L3 improvement?
9. What should be cut as overengineering?
10. What validators should be added so graph count increases because real relationship coverage improved, not because duplicate/noisy rows are counted?

## Expected Output

Return:

1. Diagnosis of why current graph count is 27.
2. Clear L3 target definition.
3. Recommended relation graph taxonomy.
4. Concrete graph key/schema proposal.
5. Data expansion plan from current L0-L2 artifacts.
6. P0/P1/P2 implementation roadmap.
7. Validator checklist.
8. What not to build now.
9. Final Codex patch prompt for next implementation task.
