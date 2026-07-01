# GPT Pro Prompt: TASK-4155 L4 Goal / Role / Development Plan Review

You are reviewing a local working copy that may not be fully reflected in GitHub.

Act as:

1. Professional Backend Engineer
2. Quant Data Infrastructure Reviewer
3. Institutional Equity Research PM
4. Systematic PM / Trading Research Reviewer
5. Risk and Trading Controls Reviewer

Do not assume GitHub has the latest local L0-L3 work. Use the current-state packet below as the source of truth for the latest local work. You may use GitHub only for broader project context if available, but do not override this packet with stale GitHub state.

Project hard state:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is `UNKNOWN/BLOCKER`, never negative evidence
- L4 must not produce final policy actions, order intent, sizing, live/paper eligibility, broker mutation, strategy acceptance, or deployment readiness.

User goal:

Define L4's clear goal, role, detailed goals, and detailed responsibilities. Review Layer 0 through Layer 4 context and propose a concrete L4 development plan.

## Current Local State Packet

### Project Layer Model

| Layer | Current Role |
|---|---|
| L0 | Raw/source collection and source-time integrity |
| L1 | Normalize/packetize source data and preserve lineage |
| L2 | Convert admitted source data into diagnostic economic meaning candidates |
| L3 | Build diagnostic relation graph and relation-quality guard |
| L4 | Not yet implemented. Intended to construct and validate thesis bundles at institutional quality |

### L0 Current State

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
- Python collectors/backfill workers are the main collection path.

### L1 / L2 Current State

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

### L3 Current State

TASK-4152 L3 relation graph v2:

| artifact | count |
|---|---:|
| relation edges | 7,150 |
| event clusters | 1,850 |
| relation graphs | 5,398 |
| coverage gaps | 181 |

TASK-4154 L3 quality guard:

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

L3-to-L4 handoff hard rules:

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

### Existing L4 Governance

`L4_THESIS_BUNDLE` purpose:

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

Hard boundaries:

- strategy_status: `NOT_ACCEPTED`
- deployment_status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real_capital: `FORBIDDEN`
- live_order: `FORBIDDEN`

Current implementation reality:

- L4 profile exists.
- L4 profile validator exists.
- L4 skill file exists.
- No full L4 thesis bundle builder found.
- No L4 artifact schema found.
- No L4 semantic validator for thesis bundle shape found.

## Review Questions

Please answer directly.

1. What should L4's clear goal be?
2. What should L4's role be, in plain language?
3. What detailed responsibilities should L4 own?
4. What should L4 consume from L0-L3?
5. What must L4 refuse to consume or refuse to infer?
6. What exact artifact schema should L4 produce first?
7. What validator/test plan is needed?
8. What P0/P1 development plan should Codex execute next?
9. What is explicitly out-of-scope to avoid over-engineering?
10. Is current L0-L3 state sufficient to start L4 as diagnostic thesis bundle work?

## Required Output

Use this exact structure:

1. Verdict
   - PASS / CONDITIONAL PASS / FAIL / BLOCKED
   - one plain-language conclusion

2. L4 Goal
   - one-sentence goal
   - what L4 is
   - what L4 is not

3. L4 Detailed Role And Responsibilities
   - table: responsibility, input, output, guardrail

4. Required L4 Artifact Schema
   - concrete files and required columns/fields
   - keep it practical and implementable

5. L4 Validator Plan
   - validator checks
   - failure conditions

6. L4 Development Plan
   - P0/P1 prioritized table

7. What L4 Must Not Do
   - explicit cut list

8. Codex Patch Prompt
   - a bounded implementation prompt for Codex
   - avoid over-engineering
   - do not open trading authority

