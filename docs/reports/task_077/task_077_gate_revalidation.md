# Task 077 - Gate Locked Full Revalidation

- selected gate candidate: `H_KER_VOLUME_DAILY_BIAS`
- gate decision source: `FAIL`
- policy lock: `A_BASELINE`

| Scenario | Trades | WinRate | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S1_ZERO_COST | 186 | 32.26% | 1.4938 | 20716.66 | 7457.56 | 1.7741 | 61.39% | 55 | 16 | 97 |
| S2_LOW_COST | 186 | 32.26% | 1.3918 | 17281.22 | 7886.22 | 1.4837 | 61.39% | 55 | 15 | 97 |
| S3_MEDIUM_COST | 186 | 32.26% | 1.3407 | 15431.44 | 8098.87 | 1.3265 | 61.39% | 55 | 15 | 97 |
| S4_KIS_REALISTIC | 186 | 32.26% | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 61.39% | 55 | 15 | 97 |
| S5_KIS_STRESS_20 | 186 | 31.18% | 1.0894 | 4596.76 | 9228.08 | 0.4002 | 61.18% | 55 | 15 | 98 |
| S6_KIS_STRESS_30 | 188 | 28.72% | 0.9747 | -1378.71 | 12568.58 | -0.1209 | 61.04% | 57 | 11 | 100 |

## Summary
- S4 status: WARNING
- pilot answer: WARNING
- notes: Task 076 rejected gate adoption; baseline policy locked for revalidation.
