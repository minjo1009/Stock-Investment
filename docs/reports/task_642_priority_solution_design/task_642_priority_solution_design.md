# Task642 Priority Solution Design

## Decision Summary

- Verdict: `LOCK_PRIORITY_ORDER_ENTRY_RISK_TIER_TURNOVER_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Baseline: Task639, `$1000 -> $7639.62`, max drawdown `-23.76%`
- Main plan: entry quality first, volatility sizing second, signal tier sizing third, capital recycling fourth.

## Quant Expert Report

Task642 converts the Task641 diagnosis and Chrome ChatGPT review-only critique into a test order. The goal is not to add random alpha. The goal is to keep the Task639 content signal fixed and improve the trade wrapper around it.

### Why This Order

1. Entry quality comes first because current accepted trades all share a broad `intraday_breakout_acceptance` label. VWAP, opening range, relative strength, and volume confirmation are not locked.
2. Risk sizing comes second because equal max5 treats all trades as the same risk. That can make a few high-volatility losers dominate drawdown.
3. Signal tier sizing comes third because Task639 currently treats `contract_customer`, `supply_demand`, and both together as the same bet.
4. Exit/capital recycling comes fourth because median hold is 85.4 days and capacity skips are huge, but changing exit first risks killing the large winners.
5. Microstructure source readiness is a parallel data blocker because accepted-trade microstructure availability is 0%.

## No-Background Decision-Maker Report

- Do not chase ETF overlays now.
- Do not use MDB blacklist now.
- First fix the entry moment.
- Then size volatile trades smaller.
- Then size stronger content signals bigger.
- Only then touch exits and capital recycling.

## Artifact Manifest

- `task_642_decision.csv`
- `task_642_solution_queue.csv`
- `task_642_gpt_solution_discussion_response.md`
- `artifact_manifest.csv`
