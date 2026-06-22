# Task684 GPT Review

## Review Role

- External review-only professional quant trader and senior quant engineer.
- GPT output is not source truth, market data, label, or assignment input.
- Scope was restricted to the same five engines only.

## Core Finding

Task684 implementation improved structure, but not enough predictive selection quality.

- Pure interaction packet is too aggressive.
- Guarded interaction packet is too conservative.
- The current five engines now have better explanatory structure, but still lack conditional replacement judgment.

## Result Interpretation

- `interaction_context_packet_v3` improved validation, but failed all-period and recent OOS because it removed 3 active cap3 big winners.
- `interaction_context_superiority_guarded_v3` preserved active cap3 winners, but admitted no better challenger and matched active cap3.
- Therefore the next issue is not five-engine existence. The issue is conditional admission logic inside Cohort Slot Qualification.

## Five-Engine Code Feedback

1. Leadership Lifecycle

- Add phase transition, not only phase label.
- Required outputs:
  - `leadership_transition_type`
  - `leadership_price_confirmation`
  - `leadership_market_alignment`

2. Catalyst Quality

- Absorption state is more important than good/bad catalyst quality.
- Required outputs:
  - `catalyst_absorption_state`
  - `catalyst_conflict_state`
  - `catalyst_price_followthrough_context`

3. Archetype Candidate

- `unclear` must not mean reject.
- Required outputs:
  - `archetype_tail_optional_flag`
  - `archetype_uncertain_but_live_flag`
  - `archetype_rejection_reason`

4. Same Symbol Context

- Same-symbol output must remain an interpreter, not a score.
- It should explain whether a setup shift is adverse, neutral, or merely different.

5. Cohort Slot Qualification

- The next improvement is a conditional replacement engine:
  - preserve active cap3 unless challenger has clear superiority,
  - do not require incumbents to be deeply vulnerable,
  - require challenger superiority across multiple dimensions,
  - never use global rank.

## Plain Conclusion

Task684 moved from isolated labels to interaction-aware context.

It still did not become firm-grade because the slot engine lacks a middle path between:

- replacing too much, and
- replacing nothing.
