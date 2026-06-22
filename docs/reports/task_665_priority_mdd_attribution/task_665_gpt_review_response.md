# Task665 GPT Review Response Summary

Captured via Chrome ChatGPT, review-only.

## Main Review

GPT agreed that Task665 should be an MDD attribution audit, not a new rule-development task.

The warning was clear:

- Do not compare all 27 added and 27 removed trades by average only.
- First identify the MDD peak/trough window.
- Then inspect active trades, added trades, removed trades, and displacement pairs inside that window.
- Do not add risk caps before the drawdown source is decomposed.

## Required Firm-Grade Attribution

GPT recommended these layers:

1. MDD peak/trough window.
2. Active trade inventory during the MDD interval.
3. Added versus removed accepted trades.
4. Same-timestamp displacement pairs.
5. PnL / drawdown contribution by trade and relation state.

## Promotion Blockers

- If MDD is caused by priority-added trades, priority cannot promote without risk controls.
- If validation/recent OOS improvement depends on one or two trades, it may be a capacity artifact.
- Sparse relation states cannot drive promotion.
- If drawdown worsens and the cause is not explained, no promotion is allowed.

## Research-Useful Findings

- Added trades consistently improving entry-reduce.
- Removed trades consistently causing large losses.
- Relation states behaving in the same direction across validation and recent OOS.

Final review position:

`Task665 = MDD Attribution + Displacement Pair Audit`

`Risk cap design only after attribution`
