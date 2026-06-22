# Task703 GPT Review Packet

## Goal
Move the five-axis source parser upstream from Task702's 19 source-packet rows to all Task636 event-linked candidates, then run a full-period backtest.

## Data Scope
- Full baseline candidate panel: 5,265 lifecycles from Task633/Task632 baseline backtest panel.
- Event-linked lifecycles: 2,445 from Task636 entry_event_links.
- Source predictions: Task636 event_content_predictions.
- Entry/exit returns: exact lifecycle_id + symbol join to Task633/Task632 baseline panel.
- Price confirmation context: exact lifecycle_id + symbol join to Task684 context fields.

## Parser Axes
1. financing_overhang_flag
   - private offering
   - convertible senior notes
   - capped call
   - note purchase agreement
   - aggregate principal amount

2. guidance_quality_axis
   - financing_conflict
   - reaffirm
   - soft_or_cut
   - raise_or_positive_change
   - guidance_present_quality_unclear
   - no_guidance_signal

3. information_novelty_axis
   - conflicted_by_financing
   - not_new_reaffirmation
   - new_multi_family_direct
   - new_thin_direct
   - manual_indirect_economic_terms
   - not_enough_source_novelty

4. high_noise_thin_signal_flag
   - noise_ratio >= 0.75 and direct_event_count <= 1

5. price_absorption_confirmation_flag
   - price_acceptance_score >= 6
   - volume_ratio_prev >= 1.0
   - price_chart_acceptance_state contains price_confirmed

## Action Logic
- no source packet -> RESEARCH_ONLY_NO_SOURCE_PACKET
- financing overhang -> CONFIRMATION_REQUIRED_FINANCING
- guidance reaffirm/soft -> CONFIRMATION_REQUIRED_GUIDANCE_WEAK
- low novelty -> RESEARCH_ONLY_LOW_NOVELTY
- high-noise thin without price absorption -> CONFIRMATION_REQUIRED_HIGH_NOISE
- no price absorption -> CONFIRMATION_REQUIRED_PRICE
- otherwise -> ELIGIBLE_RULE_CANDIDATE

## Backtest Method
- freeze full 5,265 candidates first
- attach outcomes only after freeze
- cost: 50 bps round trip
- compare:
  - all_5265_baseline_costed
  - event_linked_2445_costed
  - full_event_axis_eligible
  - QQQ buy-and-hold same horizon
- starting capital: $1,000
- max positions: 5/10/20

## Required Review
You are a professional quant trader / event-driven equity researcher. Review this before final backtest.
Return Korean, concise.

Questions:
1. Is this parser direction logically better than source-direct only?
2. What are the biggest leakage/overfit risks?
3. Are the action states too strict or too loose?
4. What result patterns would make this promising vs suspicious?
5. What must be reported as caveat even if backtest looks good?

Do not invent external facts. Treat GPT as design reviewer only, not source.
