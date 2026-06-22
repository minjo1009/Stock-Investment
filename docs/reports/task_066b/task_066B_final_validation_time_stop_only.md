# Task 066-B Final Validation (TIME_STOP_ONLY)

## Comparison Setup
- Baseline: LIMITED_CHASE
- Candidate: TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0)

## Results Table

| Scenario | Policy | Trades | WinRate | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S1_ZERO_COST | LIMITED_CHASE | 182 | 37.91% | 1.3422 | 16500.09 | 8362.97 | 1.3870 | 60.87% | 71 | 25 | 98 |
| S1_ZERO_COST | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 186 | 32.26% | 1.4938 | 20716.66 | 7457.56 | 1.7741 | 61.39% | 55 | 16 | 97 |
| S2_LOW_COST | LIMITED_CHASE | 182 | 37.36% | 1.2644 | 13226.91 | 8802.51 | 1.1154 | 60.87% | 71 | 24 | 98 |
| S2_LOW_COST | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 186 | 32.26% | 1.3918 | 17281.22 | 7886.22 | 1.4837 | 61.39% | 55 | 15 | 97 |
| S3_MEDIUM_COST | LIMITED_CHASE | 182 | 37.36% | 1.2222 | 11361.65 | 9077.37 | 0.9592 | 60.87% | 71 | 24 | 98 |
| S3_MEDIUM_COST | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 186 | 32.26% | 1.3407 | 15431.44 | 8098.87 | 1.3265 | 61.39% | 55 | 15 | 97 |
| S4_KIS_REALISTIC | LIMITED_CHASE | 182 | 37.36% | 1.0835 | 4582.87 | 9885.24 | 0.3893 | 60.87% | 71 | 24 | 98 |
| S4_KIS_REALISTIC | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 186 | 32.26% | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 61.39% | 55 | 15 | 97 |
| S5_KIS_STRESS_20 | LIMITED_CHASE | 182 | 36.26% | 1.0286 | 1613.64 | 10731.74 | 0.1377 | 60.87% | 71 | 23 | 98 |
| S5_KIS_STRESS_20 | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 186 | 31.18% | 1.0894 | 4596.76 | 9228.08 | 0.4002 | 61.18% | 55 | 15 | 98 |
| S6_KIS_STRESS_30 | LIMITED_CHASE | 182 | 36.26% | 0.9758 | -1400.50 | 12038.63 | -0.1202 | 60.87% | 71 | 19 | 98 |
| S6_KIS_STRESS_30 | TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0) | 188 | 28.72% | 0.9747 | -1378.71 | 12568.58 | -0.1209 | 61.04% | 57 | 11 | 100 |

## S4 Detailed Comparison

- Baseline PF/Net/MDD/Sharpe: 1.0835 / 4582.87 / 9885.24 / 0.3893
- Candidate PF/Net/MDD/Sharpe: 1.1684 / 8373.70 / 8919.73 / 0.7238
- Delta (candidate-baseline): PF 0.0849, Net 3790.83, MDD -965.51, Sharpe 0.3345

## Risk Comparison

- STOP-driven DD ratio: baseline 46.99% -> candidate 35.14%
- STOP count delta (S4): -16
- GOOD_THEN_STOP delta (S4): -9

## KPI Gate Result

- Status: WARNING
- PF>=1.2: False
- NetPnL>0: True
- Sharpe>=1.0: False
- MDD<=40% of NetPnL: False

## Final Decision

- Pilot Decision: WARNING
- Reason: Positive PF/Net on S4 but full gate not satisfied (Sharpe or MDD constraint).

## Next Actions
- If WARNING, run ultra-small pilot with strict daily loss cap and UNKNOWN-order halt.
- Track S4-equivalent live slippage and fill-rate drift against backtest deltas.
- If S4 live metrics degrade for 2 consecutive weeks, rollback to baseline policy.
