# Task T094-REVIEW - Risk Component Attribution

## 1. Summary
- baseline_case: BASELINE
- best_mdd_case: FULL_COMBINED
- best_sharpe_case: LOSS_CLUSTER_BREAKER_ONLY
- recommended_case: FULL_COMBINED

## 2. Component Comparison
| Case | Return % | MDD % | Sharpe | Trades | MDD Reduction % | Sharpe Delta | Return Delta | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BASELINE | 15.8254 | 3.9508 | 0.568903 | 39 | 0.0000 | 0.010805 | 0.0000 | FAIL |
| LOSS_CLUSTER_BREAKER_ONLY | 13.3588 | 4.2453 | 0.750086 | 32 | -7.4543 | 0.191988 | -2.4666 | FAIL |
| POSITION_THROTTLE_ONLY | 12.6374 | 3.3258 | 0.543436 | 39 | 15.8194 | -0.014662 | -3.1880 | WARNING |
| DECORRELATION_ONLY | 15.0366 | 2.9890 | 0.629822 | 39 | 24.3450 | 0.071724 | -0.7888 | WARNING |
| ADAPTIVE_EXPOSURE_ONLY | 15.8254 | 3.9508 | 0.568903 | 39 | 0.0000 | 0.010805 | 0.0000 | FAIL |
| FULL_COMBINED | 10.1527 | 2.7020 | 0.707265 | 32 | 31.6093 | 0.149167 | -5.6727 | PASS |

## 3. Attribution
- strongest_mdd_component: DECORRELATION_ONLY
- strongest_sharpe_component: LOSS_CLUSTER_BREAKER_ONLY
- largest_return_drag_component: POSITION_THROTTLE_ONLY

## 4. Side Effects
- LOSS_CLUSTER_BREAKER_ONLY reduces return by -2.4666% vs baseline.
- LOSS_CLUSTER_BREAKER_ONLY reduces trade count by -7.
- POSITION_THROTTLE_ONLY reduces return by -3.1880% vs baseline.
- DECORRELATION_ONLY reduces return by -0.7888% vs baseline.
- FULL_COMBINED reduces return by -5.6727% vs baseline.
- FULL_COMBINED reduces trade count by -7.

## 5. Final Decision
- status: PASS
- answer: YES

## 6. Final Answer
- Loss clustering is reduced, with the largest impact coming from component-level gating/exposure controls; return drag remains the trade-off.
