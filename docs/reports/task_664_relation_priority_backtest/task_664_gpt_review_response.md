# Task664 GPT Review Response Summary

Captured via Chrome ChatGPT, review-only.

## Main Review

GPT agreed that Task664 is a defensible next step after Task663.

The reasoning:

- Task663 showed relation states have explanatory power.
- Hard filtering damaged full-period robustness.
- With timing and exit unchanged, the smallest defensible intervention is max5 capacity allocation.
- Therefore priority within the same `entry_ts` candidate group is a reasonable diagnostic test.

## Defensible Priority

Predeclared promotion-eligible priority should be based on relation semantics, not observed returns:

1. `mechanism_reinforcing_company_positive`
2. `mechanism_offsetting_company_positive`
3. `company_positive_needs_confirmation`
4. `company_quality_price_confirmed`
5. `sparse_mechanism_cell`

GPT warned that recent-OOS weak/strong state sorting is outcome-derived and must be diagnostic-only.

## Pass/Fail Gates

- Entry rule, timing, exit, and cost must match Task639.
- Priority must be the only changed assignment input.
- Validation and recent OOS must both improve while QQQ outperformance remains.
- Capacity attribution must show which trades were displaced and accepted.
- Sparse states cannot become a top-priority promotion source.

## Promotion View

Even if Task664 improves results, it should be treated as allocation evidence first, not automatic strategy acceptance.

Final review position:

`Task663 = selection test`

`Task664 = allocation/priority test`

`Task665+ = promotion review only if Task664 passes gates`
