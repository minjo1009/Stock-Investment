# Task 076 - Minimal Regime & Entry Quality Gate

## Experiment Setup
- baseline: TIME_STOP_ONLY(t=10,mfe=0.03,g=0.5,p=0.0)
- candidate set: A~H
- symbols: 12
- data_dir: data\raw\us_daily

## Gate Definitions
- KER: abs(close_t-close_t-20)/sum(abs(diff(close)),20), TREND if >0.50
- Volume percentile: rolling(100) percentile rank >= 0.60
- Daily bias: close>SMA50 and optional SMA20>SMA50

## Results Table (S4)

| Candidate | Trades | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS | Skipped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_BASELINE | 186 | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 61.39% | 55 | 15 | 97 | 0 |
| B_KER_ONLY | 64 | 1.7525 | 11996.08 | 2834.20 | 1.5935 | 10.55% | 19 | 7 | 41 | 490 |
| C_VOLUME_ONLY | 131 | 1.3000 | 9779.09 | 6754.46 | 0.9506 | 29.24% | 31 | 14 | 97 | 200 |
| D_DAILY_BIAS_ONLY | 186 | 1.1684 | 8373.70 | 8919.73 | 0.7238 | 61.39% | 55 | 15 | 97 | 0 |
| E_KER_VOLUME | 45 | 1.9232 | 10922.50 | 2183.55 | 1.5448 | 6.55% | 13 | 6 | 30 | 591 |
| F_KER_DAILY_BIAS | 64 | 1.7525 | 11996.08 | 2834.20 | 1.5935 | 10.55% | 19 | 7 | 41 | 490 |
| G_VOLUME_DAILY_BIAS | 131 | 1.3000 | 9779.09 | 6754.46 | 0.9506 | 29.24% | 31 | 14 | 97 | 200 |
| H_KER_VOLUME_DAILY_BIAS | 45 | 1.9232 | 10922.50 | 2183.55 | 1.5448 | 6.55% | 13 | 6 | 30 | 591 |

## S4 Comparison (vs Baseline)
- A_BASELINE: PF +0.0000, Net +0.00, MDD +0.00, Sharpe +0.0000, Trades +0
- B_KER_ONLY: PF +0.5841, Net +3622.38, MDD -6085.53, Sharpe +0.8697, Trades -122
- C_VOLUME_ONLY: PF +0.1316, Net +1405.39, MDD -2165.27, Sharpe +0.2268, Trades -55
- D_DAILY_BIAS_ONLY: PF +0.0000, Net +0.00, MDD +0.00, Sharpe +0.0000, Trades +0
- E_KER_VOLUME: PF +0.7548, Net +2548.80, MDD -6736.18, Sharpe +0.8211, Trades -141
- F_KER_DAILY_BIAS: PF +0.5841, Net +3622.38, MDD -6085.53, Sharpe +0.8697, Trades -122
- G_VOLUME_DAILY_BIAS: PF +0.1316, Net +1405.39, MDD -2165.27, Sharpe +0.2268, Trades -55
- H_KER_VOLUME_DAILY_BIAS: PF +0.7548, Net +2548.80, MDD -6736.18, Sharpe +0.8211, Trades -141

## Stress Comparison (S5/S6)
- A_BASELINE: S5 PF 1.0894, S6 PF 0.9747, S6 PF delta vs baseline +0.0000
- B_KER_ONLY: S5 PF 1.6778, S6 PF 1.5900, S6 PF delta vs baseline +0.6153
- C_VOLUME_ONLY: S5 PF 1.1841, S6 PF 1.1165, S6 PF delta vs baseline +0.1419
- D_DAILY_BIAS_ONLY: S5 PF 1.0894, S6 PF 0.9747, S6 PF delta vs baseline +0.0000
- E_KER_VOLUME: S5 PF 1.8258, S6 PF 1.7351, S6 PF delta vs baseline +0.7605
- F_KER_DAILY_BIAS: S5 PF 1.6778, S6 PF 1.5900, S6 PF delta vs baseline +0.6153
- G_VOLUME_DAILY_BIAS: S5 PF 1.1841, S6 PF 1.1165, S6 PF delta vs baseline +0.1419
- H_KER_VOLUME_DAILY_BIAS: S5 PF 1.8258, S6 PF 1.7351, S6 PF delta vs baseline +0.7605

## Gate Attribution (S4)
- A_BASELINE: skipped=0, avg=0.00, median=0.00, winner_ratio=0.00%, reasons={}
- B_KER_ONLY: skipped=490, avg=944.30, median=683.03, winner_ratio=98.57%, reasons={'KER_MEAN_REV': 194, 'KER_MIXED_BLOCKED': 296}
- C_VOLUME_ONLY: skipped=200, avg=795.56, median=664.70, winner_ratio=98.50%, reasons={'VOLUME_PERCENTILE_LOW': 200}
- D_DAILY_BIAS_ONLY: skipped=0, avg=0.00, median=0.00, winner_ratio=0.00%, reasons={}
- E_KER_VOLUME: skipped=591, avg=919.38, median=670.00, winner_ratio=98.65%, reasons={'KER_MEAN_REV': 199, 'KER_MIXED_BLOCKED': 319, 'VOLUME_PERCENTILE_LOW': 288}
- F_KER_DAILY_BIAS: skipped=490, avg=944.30, median=683.03, winner_ratio=98.57%, reasons={'KER_MEAN_REV': 194, 'KER_MIXED_BLOCKED': 296}
- G_VOLUME_DAILY_BIAS: skipped=200, avg=795.56, median=664.70, winner_ratio=98.50%, reasons={'VOLUME_PERCENTILE_LOW': 200}
- H_KER_VOLUME_DAILY_BIAS: skipped=591, avg=919.38, median=670.00, winner_ratio=98.65%, reasons={'KER_MEAN_REV': 199, 'KER_MIXED_BLOCKED': 319, 'VOLUME_PERCENTILE_LOW': 288}

## Decision
- recommendation candidate: H_KER_VOLUME_DAILY_BIAS
- status: FAIL
- final question answer: NO
