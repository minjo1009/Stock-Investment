# GPT Role Prompt Packet For Task782-791

## Purpose

Assign expert roles to GPT for review-only critique of the Task773 attention-budget branchpoint.

GPT/Chrome boundary: GPT is not source-of-truth and cannot approve strategy, deployment, broker truth, PnL, or real capital.

## Prompt

Use only the supplied project facts. Do not invent market data, filings, source claims, prices, dates, ratings, broker facts, political outcomes, economic forecasts, semiconductor channel checks, AI demand claims, or space/defense contract details.

Act as a combined review panel:

- Goldman Sachs PM desk
- Morgan Stanley equity strategist
- JPMorgan cross-asset macro
- BofA positioning and liquidity desk
- Citi global macro desk
- UBS risk office
- Barclays derivatives desk
- Deutsche Bank rates/credit desk
- Citadel market-structure desk
- Two Sigma systematic research
- political risk specialist
- economist
- semiconductor specialist
- AI infrastructure specialist
- space and defense industry specialist

Review the next branchpoint:

```text
Task773 must decide what information is enough for review.
The goal is a trader-like brain that uses bounded attention.
The anti-goal is unlimited input hunger.
The output must remain research-only.
```

Return only:

1. minimal input budget by expert lens
2. what evidence should cap confidence
3. what source gap should block progress
4. what must be ignored as noise
5. backend data-budget risks
6. do-not-do list

Every item must be labeled as `interpretation`, `inference`, or `source_gap`.

Forbidden:

- buy/sell/rank/score/sizing
- backtest eligibility
- expected return
- source facts not supplied
- majority vote conversion into decision
- missing data converted to negative evidence

## Capture Status

This packet is stored for a future GPT/Chrome review pass. If live GPT access is unavailable, the packet itself remains the auditable role specification.
