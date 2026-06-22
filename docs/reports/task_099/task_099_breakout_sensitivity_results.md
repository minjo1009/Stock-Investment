# Task T099 - Breakout Sensitivity Results

## 1. Summary
- status: FAIL
- family_scope: BASELINE_ONLY
- baseline_reproduced: False
- final_answer: FAIL: baseline reproduction failed; sensitivity results are not reliable.

## 2. Baseline
- stage_funnel: {'0': 12432, '1': 8288, '2': 694, '3': 503, '4': 503, '5': 485, '6': 39, '7': 37}
- signal_density: {'candidate_rate': 0.058518, 'generated_rate': 0.004706, 'executed_rate': 0.004464, 'generated_signals': 39, 'executed_signals': 37, 'missed_signals': 2, 'execution_ratio': 0.948718}
- quality_proxy: {'pp10': 0.717949, 'pp20': 0.615385, 'rp20': 0.082474}
- portfolio_metrics: {'profit_factor': 2.375366, 'sharpe': 0.884498, 'mdd_pct': 3.831247, 'return_pct': 31.990129, 'trade_count': 37}

## 3. Runs
| run_id | family | level | decision | gen | exec | pp20 | sharpe | mdd |
|---|---|---|---|---:|---:|---:|---:|---:|
| BASELINE | BASELINE | BASELINE | BASELINE | 39 | 37 | 0.615385 | 0.884498 | 3.831247 |

## 4. Acceptance
- accepted_runs: []
- rejected_runs: []
- hard_fail_runs: []

## 5. Recommended Next
- action: NO_CHANGE_RECOMMENDED
- best_candidates: []
- note: Phase-2 combined tests are allowed only after accepted single-factor review.
