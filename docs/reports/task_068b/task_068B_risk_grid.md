# Task 068-B Risk Grid Result

## Setup
- strategy: US_BREAKOUT_V0
- execution_policy: LIMITED_CHASE
- symbols: 12
- grid_size: 80

## Top 5 Candidates (S4 Filtered)

| Rank | Policy | PF(S4) | Net(S4) | MDD(S4) | Sharpe(S4) | GOOD->STOP delta |
|---:|---|---:|---:|---:|---:|---:|
| 1 | TIME_STOP_ONLY (t=10, mfe=0.03, g=0.5, p=0.0) | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 9 |
| 2 | TIME_STOP_PROFIT_BUFFER (t=10, mfe=0.03, g=0.5, p=0.0) | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 9 |
| 3 | TIME_STOP_MFE (t=15, mfe=0.05, g=0.5, p=0.0) | 1.1287 | 5716.12 | 9615.51 | 0.5353 | 13 |
| 4 | TIME_STOP_MFE (t=10, mfe=0.05, g=0.5, p=0.0) | 1.1121 | 4858.74 | 9530.03 | 0.4601 | 16 |

## Notes
- Primary filter: PF>=1.1, Net>PnL baseline, MDD<=baseline (S4).
- Secondary filter: Sharpe improved, GOOD_THEN_STOP reduced.
