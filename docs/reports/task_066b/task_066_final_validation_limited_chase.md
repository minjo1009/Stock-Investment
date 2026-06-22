# Task 066 - Final Validation (LIMITED_CHASE)

## Setup
- Entry policy: `LIMITED_CHASE`
- Universe: AAPL, AMD, AMZN, AVGO, COST, GOOGL, META, MSFT, NFLX, NVDA, QCOM, TSLA
- Initial equity: 100,000
- Validation script: `python -m backtest.analysis_final_validation_limited_chase`

## Final Results - KIS Realistic Scenario
- Scenario: S4_KIS_REALISTIC
- Fee: 0.25% per side
- Slippage: 0.10% per side
- Total PnL: 13,650.70
- Net PnL: 4,582.87
- Trades: 182
- Win rate: 37.36%
- Profit factor: 1.0835
- Max drawdown: 9,885.24
- Sharpe: 0.3893
- Fill rate: 60.87%
- Expired rate: 35.12%
- BIG_MISS: 98

## Cost Sensitivity

| Scenario | Fee | Slippage | PF | Net PnL | MDD | Sharpe | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| S1_ZERO_COST | 0.00% | 0.00% | 1.3422 | 16,500.09 | 8,362.97 | 1.3870 | WARNING |
| S2_LOW_COST | 0.05% | 0.05% | 1.2644 | 13,226.91 | 8,802.51 | 1.1154 | WARNING |
| S3_MEDIUM_COST | 0.10% | 0.05% | 1.2222 | 11,361.65 | 9,077.37 | 0.9592 | WARNING |
| S4_KIS_REALISTIC | 0.25% | 0.10% | 1.0835 | 4,582.87 | 9,885.24 | 0.3893 | WARNING |
| S5_KIS_STRESS_20 | 0.25% | 0.20% | 1.0286 | 1,613.64 | 10,731.74 | 0.1377 | WARNING |
| S6_KIS_STRESS_30 | 0.25% | 0.30% | 0.9758 | -1,400.50 | 12,038.63 | -0.1202 | FAIL |

## Drawdown Analysis
- Worst DD peak: 2024-06-21
- Worst DD trough: 2026-04-17
- Worst DD: 9,257.14
- Trades in worst DD segment: 83
- Largest symbol losses in worst DD:
  - AMZN: -2,040.00
  - COST: -1,771.95
  - TSLA: -1,725.84
  - META: -1,643.97
  - QCOM: -1,154.90
- Exit attribution in worst DD:
  - STOP: -23,195.71
  - TREND_BREAK_2BAR: -2,077.47
  - TIME_EXIT: +16,742.93

## KPI Gate Result
- Task 066 status: WARNING
- Pilot KPI document status: WARNING

Failed checks:
- Scenario 4 PF >= 1.25
- Scenario 4 Sharpe >= 1.0
- Scenario 5 PF >= 1.10
- Scenario 6 PF >= 1.05
- MDD <= 40% of Net PnL

## Final Decision
WARNING - ultra-small constrained pilot only.

The strategy remains positive under KIS realistic costs, but the edge is thin and drawdown is too large relative to net profit. It is not strong enough for normal pilot sizing.

## Next Actions
1. Lock `LIMITED_CHASE` as the current best practical execution candidate.
2. Reduce STOP-driven drawdown before normal pilot approval.
3. Re-check symbol concentration, especially NFLX, TSLA, AVGO, AMZN, and GOOGL.
4. Pilot only under strict constraints if proceeding: tiny size, 1 position max, kill switch active, live PF halt below 1.0.
