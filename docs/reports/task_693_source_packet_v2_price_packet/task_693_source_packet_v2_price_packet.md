# Task693 Source Packet V2 and Price Packet Review

## Decision Summary

- Verdict: SOURCE_PACKET_V2_AND_PRICE_PACKET_REVIEW_BUILT_NO_TRADING_PROMOTION.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: source events 192, leader packets 19, direct supported leaders 9, manual-review leaders 0, price packets 2.
- What changed: source packet interpretation now re-reads certified raw text and guards against ownership-filing noise.
- Next action: Review v2 source packet states and the two price packets before defining any allocation eligibility rule.

## Quant Expert Report

### Data source and source readiness

Inputs are Task636 entry-event links and source-text predictions, Task691 leader review, and Task692 price absorption confirmation output.

### Exact join keys

- Source packet v2: `lifecycle_id` to entry-event links, then `event_id` to event predictions and raw text paths.
- Price packet: Task692 review-ready price candidates by `lifecycle_id`.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Source Packet V2 Rulebook

| rule_id | purpose | positive_requirement |
| --- | --- | --- |
| ownership_sale_noise_guard | Prevent Form 4, 144, 13G, and ownership filings from becoming bullish catalysts by default. | Must include independent economic bridge; ownership filing alone is not enough. |
| direct_company_bridge | Promote only source packets with direct company linkage plus contract/customer/order/backlog/revenue/guidance/margin signal. | Company-direct source, certified text, not generic filing, and at least two economic evidence families. |
| policy_breadth_guard | White House or political events must not be mapped to one stock unless direct symbol or sector mechanism is explicit. | Policy text must name the company or contain sector-specific mechanism and direct stock linkage. |
| manual_review_bucket | Keep ambiguous 8-K or IR filings out of allocation while preserving them for human packet review. | Economic terms exist but direct causal bridge is incomplete. |

### Source Event V2 Summary

| source_event_v2_state | event_count |
| --- | --- |
| broad_policy_not_symbol_specific | 62 |
| direct_economic_source_supported | 18 |
| no_direct_economic_bridge | 1 |
| ownership_filing_with_weak_economic_terms | 13 |
| ownership_or_sale_filing_noise | 98 |

### Leader Packet V2 Summary

| source_packet_v2_state | source_packet_v2_verdict | leader_count |
| --- | --- | --- |
| source_packet_direct_economic_supported | review_ready_not_trade_approved | 9 |
| source_packet_economic_terms_but_no_direct_bridge | not_promotable | 10 |

### Price Absorption Review-Ready Packets

| symbol | entry_ts | human_packet_summary | residual_review_risk |
| --- | --- | --- | --- |
| TEAM | 2025-01-30 14:30:00+00:00 | symbol=TEAM\|price_score=7.0\|range_pos=0.85\|volume_ratio=1.55\|near_high60=0.95\|flags=price_acceptance_score_ok\|volume_support\|opening_extension | opening_extension |
| LMT | 2026-01-15 14:30:00+00:00 | symbol=LMT\|price_score=6.0\|range_pos=0.87\|volume_ratio=1.12\|near_high60=0.99\|flags=price_acceptance_score_ok\|volume_support\|near_high60_extension | near_high_extension |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Ownership and sale filings dominate many leader packets and are not treated as bullish catalysts.
- Broad policy items remain non-promotable unless directly tied to the company or sector mechanism.
- Price absorption packets are review-ready only, not allocation-approved.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Manually review source packet v2 `manual_review_required` cases.
- Decide whether TEAM and LMT price packets are economically coherent before any allocation test.
- Add deterministic incumbent replay before replacement claims.

## No-Background Decision-Maker Report

- What happened: source packets were re-read with stronger guards, and the two price-ready candidates became readable packets.
- Why it matters: we avoid treating ownership filings or broad policy as direct company catalysts.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: review v2 packets before writing any trading rule.

## Artifact Manifest

- Inputs: Task636 event links/predictions, Task691 leader review, Task692 price absorption panel.
- Outputs: v2 rulebook, event evidence, leader packet v2 review, price packet review, integrity audit, decision, pass/fail, manifest.
- Row counts: event evidence 192, leader packets 19, price packets 2.
- Validation commands: `python src/backtest/build_task693_source_packet_v2_price_packet.py`; `python -m unittest tests.test_task693_source_packet_v2_price_packet`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| source_event_evidence_present | PRIMARY_PASS | 1 | events=192; lifecycles=19 | source event v2 evidence for all 19 leader source packets |
| source_packet_v2_states_present | PRIMARY_PASS | 1 | packet_states=2 | v2 interpreter should separate noise/manual/direct states where data supports it |
| price_review_ready_packet_count | PRIMARY_PASS | 1 | price_packets=2 | one packet for each Task692 review-ready price absorption candidate |
| no_outcome_columns_in_task693_outputs | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded |
| no_strategy_promotion | PRIMARY_PASS | 1 | no PnL simulation or allocation rule promotion was run | packet review only |
