# Task T095 - Risk Overlay Adoption

## 1. Summary
- selected_overlay: DECORRELATION_PLUS_LIGHT_LOSS_BREAKER
- status: WARNING
- reason: Selected DECORRELATION_PLUS_LIGHT_LOSS_BREAKER as best score=7.263473, balancing return=16.113361%, MDD=2.790222%, Sharpe=0.673152.

## 2. Scenario Comparison
| Case | Return | MDD | Sharpe | Calmar | Score |
|---|---:|---:|---:|---:|---:|
| BASELINE | 15.8254 | 3.9508 | 0.568903 | 0.983976 | 6.352969 |
| DECORRELATION_ONLY | 15.0366 | 2.9890 | 0.629822 | 1.239003 | 6.128478 |
| FULL_COMBINED | 10.1527 | 2.7020 | 0.707265 | 0.940789 | 4.855760 |
| DECORRELATION_PLUS_POSITION_THROTTLE | 13.7589 | 2.3519 | 0.610455 | 1.446944 | 5.482782 |
| DECORRELATION_PLUS_LIGHT_LOSS_BREAKER | 16.1134 | 2.7902 | 0.673152 | 1.417253 | 7.263473 |

## 3. Trade-off Analysis
- Return vs Risk summary:
  - BASELINE: return=15.8254%, mdd=3.9508%, sharpe=0.568903
  - DECORRELATION_ONLY: return=15.0366%, mdd=2.9890%, sharpe=0.629822
  - FULL_COMBINED: return=10.1527%, mdd=2.7020%, sharpe=0.707265
  - DECORRELATION_PLUS_POSITION_THROTTLE: return=13.7589%, mdd=2.3519%, sharpe=0.610455
  - DECORRELATION_PLUS_LIGHT_LOSS_BREAKER: return=16.1134%, mdd=2.7902%, sharpe=0.673152

## 4. Stability Analysis
- BASELINE: loss_streak_max=5, trade_count=39, win_rate=46.1538%
- DECORRELATION_ONLY: loss_streak_max=5, trade_count=39, win_rate=46.1538%
- FULL_COMBINED: loss_streak_max=3, trade_count=32, win_rate=53.1250%
- DECORRELATION_PLUS_POSITION_THROTTLE: loss_streak_max=5, trade_count=39, win_rate=46.1538%
- DECORRELATION_PLUS_LIGHT_LOSS_BREAKER: loss_streak_max=4, trade_count=37, win_rate=48.6486%

## 5. Capital Efficiency
- BASELINE: capital_utilization=0.292453
- DECORRELATION_ONLY: capital_utilization=0.233100
- FULL_COMBINED: capital_utilization=0.199569
- DECORRELATION_PLUS_POSITION_THROTTLE: capital_utilization=0.197359
- DECORRELATION_PLUS_LIGHT_LOSS_BREAKER: capital_utilization=0.233147

## 6. Rejected Candidates
- BASELINE: Higher or equal drawdown versus selected overlay. Lower or equal Sharpe versus selected overlay. Lower composite score.
- DECORRELATION_ONLY: Higher or equal drawdown versus selected overlay. Lower or equal Sharpe versus selected overlay. Lower composite score.
- FULL_COMBINED: Lower composite score.
- DECORRELATION_PLUS_POSITION_THROTTLE: Lower or equal Sharpe versus selected overlay. Lower composite score.

## 7. Selected Overlay
- DECORRELATION_PLUS_LIGHT_LOSS_BREAKER
- components: ['DECORRELATION', 'LIGHT_LOSS_BREAKER']

## 8. Decision
- WARNING

## 9. Final Answer
Which risk overlay should be deployed in production?
- DECORRELATION_PLUS_LIGHT_LOSS_BREAKER
