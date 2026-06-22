# Task T098.5 - Signal Funnel Attribution Audit

## 1. Executive Summary
- status: PASS
- primary_bottleneck: BREAKOUT
- over_filtering_detected: True

## 2. Stage Funnel (0..7)
| Stage | Label | Count | Drop vs prior |
|---:|---|---:|---:|
| 0 | All bars (default universe, analyzable window) | 12432 | 0 |
| 1 | Selected-universe bars | 8288 | 4144 |
| 2 | Breakout pass | 694 | 7594 |
| 3 | Breakout + MA pass | 503 | 191 |
| 4 | Liquidity pass | 503 | 0 |
| 5 | Gap pass (pre-risk candidates) | 485 | 18 |
| 6 | Generated signals (from T098) | 39 | 446 |
| 7 | Executed signals | 37 | 2 |

## 3. Filter Attribution
| Filter | Removed | Removal Rate | Avg 20-bar Fwd Ret | Net Impact (20-bar sum) |
|---|---:|---:|---:|---:|
| UNIVERSE_SELECTION | 4144 | 0.333333 | 0.018593 | 5.243186 |
| BREAKOUT | 7594 | 0.916264 | 0.020941 | 159.023377 |
| MA_TREND | 191 | 0.275216 | 0.024552 | 4.689346 |
| LIQUIDITY | 0 | 0.0 | 0.0 | 0.0 |
| GAP | 18 | 0.035785 | 0.0458 | 0.824394 |
| SIGNAL_MATERIALIZATION | 446 | 0.919588 | 0.0 | 0.0 |
| RISK_OVERLAY | 2 | 0.051282 | 0.0 | -148.9515 |

## 4. Selected vs Unselected
- selected_symbols: 8
- unselected_symbols: 4
- selected_stage5_candidates: 485
- unselected_stage5_candidates_counterfactual: 282

## 5. Time-Series Behavior
- months: 50
- median_stage5_per_month: 9.0
- zero_stage5_month_ratio: 0.18

## 6. Over-Filtering Detection
- detected: True
- BREAKOUT: removal_rate=0.916264 removed_avg_ret20=0.020941

## 7. Root Cause
- primary_filter_bottleneck: BREAKOUT
- secondary_filters: UNIVERSE_SELECTION, SIGNAL_MATERIALIZATION

## 8. Recommended Next Task
- task_id: T099
- objective: Run constrained filter-relaxation sensitivity tests on the identified bottleneck filter only, with fixed alpha logic and explicit winner/loser preservation checks.

## 9. Final Answer
Primary bottleneck is BREAKOUT: it removes the largest share before execution, while risk-overlay blocking is comparatively small and net blocked impact is not winner-dominant.
