# Task T096 - Risk Overlay Revalidation

## 1. Summary
- adopted_overlay: DECORRELATION_PLUS_LIGHT_LOSS_BREAKER
- final_verdict: WARNING
- answer: NO

## 2. Performance Comparison
| Metric | Baseline | Overlay | Delta |
|---|---:|---:|---:|
| Return % | 15.825403 | 16.113361 | 0.287958 |
| MDD % | 3.950773 | 2.790222 | -1.160551 |
| Sharpe | 0.558098 | 0.673152 | 0.115054 |
| Profit Factor | 1.947915 | 2.391508 | 0.443593 |
| Trade Count | 39 | 37 | -2 |

## 3. Drawdown Behavior
- baseline_mdd_pct: 3.950773
- overlay_mdd_pct: 2.790222
- mdd_change_pct: -1.160551

## 4. Stability Analysis
- baseline_loss_streak: 5
- overlay_loss_streak: 4
- blocked_entries_count: 2
- blocked_by_reason: {'LOSS_CLUSTER_BREAKER': 2}
- scaled_pnl_volatility: 163.856353

## 5. Capital Efficiency
- baseline_capital_utilization: 0.325241
- overlay_capital_utilization: 0.233147

## 6. System Consistency
- t092_status: PASS
- t092_answer: YES
- evidence_unknown_events: 0
- evidence_reconciliation_critical_count: 0

## 7. Decision
- WARNING

## 8. Final Answer
Is the adopted risk overlay ready for real paper operation? NO
