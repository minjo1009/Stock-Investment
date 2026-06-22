# Task T098 - Signal Density & Opportunity Frequency Diagnosis

## 1. Executive Summary
- primary_cause: Signals are inherently sparse after breakout+MA+liquidity filters; execution is not the limiting step.
- classification: Signal density / opportunity frequency problem
- final_answer: The main bottleneck is low opportunity frequency (signal density), not execution fill/deployment, because most generated signals are executed and missed ones were not profitable.

## 2. Filter Funnel (Selected Universe)
| Stage | Count |
|---|---:|
| Bars Evaluated | 8440 |
| Breakout True | 725 |
| MA True | 3816 |
| Breakout & MA | 511 |
| Liquidity Pass | 511 |
| Gap Pass | 493 |
| Pre-risk Candidates | 493 |

## 3. Signal Density
- total_signals: 39
- executed_signals: 37
- missed_signals: 2
- execution_ratio: 0.948718

## 4. Opportunity Frequency / Universe
- default_universe_size: 12
- selected_universe_size: 8
- selected_symbols_with_trades: 8
- selected_symbols_without_trades: 0
- unselected_symbols_candidate_count: 290

## 5. Risk Overlay Impact on Re-entry
- blocked_by_loss_breaker: 2
- blocked_by_slot_or_sector: 0
- missed_winners: 0
- missed_losers: 2

## 6. Recommended Next Task
- task_id: T098.5
- title: Signal Funnel Attribution Audit (No Rule Change)
- objective: Quantify per-filter elimination share over time/symbols (breakout, MA, liquidity, universe/sector selection) and identify where opportunity frequency is structurally constrained.

## 7. Final Answer
The main bottleneck is low opportunity frequency (signal density), not execution fill/deployment, because most generated signals are executed and missed ones were not profitable.
