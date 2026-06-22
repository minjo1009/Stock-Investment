# Task647 Intelligence Coverage Interaction Audit

## Decision Summary

- Verdict: `FAIL_SOURCE_LANES_AND_INTERACTION_LAYER_INCOMPLETE`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Current intelligence work is no longer just source-presence based.
- Current content interpretation is useful, but still too event-by-event.
- Firm-grade readiness is blocked by missing macro regime sources and missing multi-event interaction states.

## Quant Expert Report

Current source lanes found in the active intelligence store:

| Source Lane | Count | Current Role |
|---|---:|---|
| `institution_investment_actions` | 9708 | ownership, insider, institution, filing-style actions |
| `ceo_ir_transcripts_and_presentations` | 1044 | CEO, IR, earnings, presentation, company communication |
| `trump_major_person_political_statements` | 940 | Trump or other major-person political and policy statements |
| `war_geopolitical_conflict_events` | 307 | war, geopolitical, sanctions, conflict risk |

Current interpretation fields include direction, transmission channel, company relevance, timing quality, priced-in risk, evidence quality, materiality, confidence, and action bucket. Current content prediction fields include customer/counterparty, revenue/backlog, guidance/margin, supply/demand, regulatory/policy transmission, and priced-in risk.

Task636 showed that source-text content interpretation can produce stable predictive fields:

| Stable Feature | Meaning |
|---|---|
| `content_guidance_margin_flag` | guidance or margin language survived validation and recent OOS |
| `content_negative_score_flag` | negative-content/oversold-reaction style feature survived validation and recent OOS |
| `content_supply_demand_flag` | supply/demand language survived validation and recent OOS |

However, Task647 diagnosis finds two gaps:

1. Source lanes are too narrow for firm-grade context.
2. Event interpretation is not yet merged into a combined market state.

### Missing Source Lanes

| Priority | Missing Lane | Why It Matters |
|---:|---|---|
| 1 | Macro regime series | employment, CPI/PCE, rates, Fed tone, dollar, oil, credit, and liquidity change how company news is interpreted |
| 2 | Earnings revision and analyst actions | checks whether company news changes institutional expectations |
| 3 | Sector and ETF flow | checks whether single-name news is supported by sector money flow |
| 4 | Options, positioning, crowding | explains why good news can fail when already crowded or priced |
| 5 | Credit and funding stress | important for high-growth and funding-sensitive names |

### Missing Interpretation Axes

| Axis | Current Issue |
|---|---|
| Surprise versus expectation | current text score does not fully know whether the event beat or missed market expectations |
| Crowding and priced-in | `priced_in_risk_score` exists, but positioning and run-up context are not deeply merged |
| Duration | one-day headline and multi-quarter backlog/guidance change need different horizons |
| Transmission horizon | immediate price reaction, earnings impact, and multiple re-rating should be separated |
| Conflict/offset | company positive plus macro/policy/geopolitical negative needs a conflict resolver |

### Required Interaction State

The next layer should combine:

```text
Macro State
+ Policy State
+ Geopolitical State
+ Sector Flow State
+ Company Content State
+ Price/Chart State
= Trading Context State
```

Example trading context states:

| State | Plain Meaning |
|---|---|
| `supportive_alignment` | company, macro, sector, and price mostly point the same way |
| `mixed_alignment` | company is good but one context layer is unclear |
| `conflicted_alignment` | company is good but macro/policy/geopolitical layer pushes against it |
| `risk_off_override` | broad risk is bad enough to override company good news |
| `priced_in_risk` | event may be good, but crowding/run-up suggests limited upside |
| `source_gap` | data is not good enough to make an interpretation |

## No-Background Decision-Maker Report

- We are better than before because we are reading event content, not just checking whether news exists.
- But this is still not enough.
- Stocks move from mixed forces: jobs, inflation, Fed, dollar, oil, war, Trump/policy, sector money, and company news.
- Right now we mostly score each event separately.
- The next upgrade is to build one combined market state that says: this company news is strong, but the market background is supportive, mixed, or hostile.
- Only after that should we test entry, size, delay, confirmation, or block actions.

## Artifact Manifest

- `task_647_decision.csv`
- `task_647_gpt_review_packet.txt`
- `task_647_gpt_review_response.md`
- `task_647_intelligence_coverage_interaction_audit.md`
- `artifact_manifest.csv`
