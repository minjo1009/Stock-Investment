# Task667 Promotion Blocker Report

## Decision

`DYNAMIC_RISK_TESTED_NO_PROMOTION_CANDIDATE`

## Simple Reason

No candidate improved return, drawdown, validation, and recent OOS at the same time.

## Main Findings

`task666_active_relation_cap3_reference` is still the strongest return candidate.

- Final capital: $10,887.47
- MDD: -30.52%
- Blocker: MDD is worse than Task639's -23.76%.

`relation_cap3_contextual_risk_sizing` is the most interesting new risk-control candidate.

- Final capital: $7,804.21
- MDD: -29.02%
- Blocker: return barely beats Task639, but MDD still fails.

`dynamic_relation_cap_market_only` improved validation but did not solve full-period drawdown.

- Final capital: $7,899.06
- MDD: -32.43%
- Blocker: MDD is still worse than Task639.

## Rule Hygiene

- return_used_in_assignment = 0
- label_used_in_assignment = 0
- symbol_blacklist = 0
- return-tuned theme blacklist = 0
- exit_changed = 0
- fixed_hold_override = 0

## Next Work

Active relation cap3 needs a more precise MDD repair. Broad cap and sizing rules either cut winners or reduce returns too much. The next step should identify which open-position combinations during the MDD window cause the damage, then test a narrow, entry-time, non-return-tuned risk score.

