# Task679 GPT Review

## Review Role

- External review-only professional quant PM and trader.
- GPT output is not used as source truth, labels, market data, or assignment input.

## Core Review

- Task679 is a useful failed prototype.
- The top5 qualification rules found better average trades, but they removed the rare monster winners that drive active cap3 returns.
- Active cap3 appears to be a tail-opportunity strategy, not a broad expected-value ranking strategy.

## Evidence Reviewed

- Active cap3: $1,000 -> $10,887.47, MDD -30.52%.
- Top5 preserve tie-break: $1,000 -> $8,708.80, MDD -30.61%.
- Top5 elite/contender only: $1,000 -> $6,824.94, MDD -19.93%.
- Top5 priority v1: $1,000 -> $6,499.90, MDD -31.05%.
- Top5 priority removed 4 active cap3 big winners.
- Elite/contender-only removed 6 active cap3 big winners.

## Reviewer Interpretation

- The current top5 tiers rank average trade quality, not tail opportunity.
- Elite candidates had the best average return, but normal and contender buckets still contained many big winners.
- Removing lower-average buckets can remove the trades that create most of the portfolio return.
- The winner preservation guardrail is now essential because it explains why new rules fail.

## Do Not Build Next

- Do not add more filters.
- Do not add stronger caps.
- Do not make state scores more complex.
- Do not define top5 qualification from average returns alone.

## Actionable Next Direction

- Build a Winner Capture Engine.
- Build a Tail Opportunity State using entry-time features only.
- Study monster winner survival before any new admission or cap rule.
- Redefine slot qualification around tail opportunity, not average expected-value quality.
