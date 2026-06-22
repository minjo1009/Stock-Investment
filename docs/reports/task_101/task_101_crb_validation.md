# Task T101 - CRB Validation

## 1. Metrics Table (Baseline vs CRB)
| Metric | Baseline | CRB |
|---|---:|---:|
| Sharpe | -0.44311 | 0.365116 |
| MDD % | 1.39571 | 0.115351 |
| Trade count | 45 | 2 |
| Win rate % | 33.333333 | 50.0 |
| Expectancy | -11.8695 | 40.224 |
| Profit factor | 0.836908 | 1.696056 |

## 2. Delta Summary
- delta_sharpe: 0.808226
- delta_mdd_pct: -1.280359
- delta_trade_count: -43
- delta_expectancy: 52.0935

## 3. Decision
- status: WARNING
- answer: NO
- decision_reasons: ['Trade-count uplift guard failed']

## 4. Implementation Check
- Range excludes current bar via shifted rolling high/low.
- Compression uses ATR5(t-1) / ATR20(t-6).
- All trigger inputs are computed from past bars only.
- Baseline and CRB run on identical universe/execution/risk/cost settings.

## 5. Failure Diagnosis
- No hard-fail signature detected; inspect regime-level behavior next.

## 6. Next Action
- T101-REV (structure revision)

## Final
Does compressed range breakout produce better risk-adjusted returns than pure breakout?
- NO
