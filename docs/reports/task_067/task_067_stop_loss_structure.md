# Task 067 - STOP Loss Structure Analysis

## Setup
- Entry policy: `LIMITED_CHASE`
- Fee: 0.25% per side
- Slippage: 0.10% per side
- Universe: AAPL, AMD, AMZN, AVGO, COST, GOOGL, META, MSFT, NFLX, NVDA, QCOM, TSLA
- Script: `python -m backtest.analysis_stop_loss_structure`
- Full JSON: `docs/task_067_stop_loss_structure.json`

## Stop Summary
- Total trades: 182
- STOP trades: 71
- STOP trade ratio: 39.01%
- Average STOP loss: -5.71%
- Average holding days before STOP: 9.38
- Max STOP loss: -11.33%
- STOP net PnL: -43,639.94
- Total strategy net PnL: 4,582.87

## Structure Analysis

| Type | Count | Ratio |
|---|---:|---:|
| WEAK_THEN_STOP | 32 | 45.07% |
| GOOD_THEN_STOP | 24 | 33.80% |
| BAD_IMMEDIATE_STOP | 11 | 15.49% |
| FAKE_BREAKOUT | 4 | 5.63% |

- Average MFE: 2.79%
- Median MFE: 2.29%
- Average MAE: -7.63%
- Median MAE: -6.53%

Interpretation:
- Most STOP losses are not instant fake breakouts.
- The dominant issue is weak continuation followed by delayed STOP.
- A meaningful 33.80% of STOP trades moved more than +3% first, then reversed into STOP.

## Timing Analysis
- Average bars to STOP: 7.58
- Median bars to STOP: 7
- STOP within 1-3 bars: 22.54%
- STOP after 5+ bars: 71.83%

Interpretation:
- STOP loss problem is more holding/risk management related than pure entry timing.
- Immediate failure exists, but it is not the main bucket.

## Environment Analysis
- Average ATR at STOP signal: 2.79%
- Average 20-day volatility: 2.17%
- STOP count in BULL: 65 (91.55%)
- STOP count in BEAR: 6 (8.45%)
- STOP net loss in BULL: -39,808.24
- STOP net loss in BEAR: -3,831.70

Interpretation:
- STOP losses are concentrated in BULL regime because most trades occur there.
- This is not primarily a BEAR-only failure.

## Symbol Analysis

### STOP Loss Contribution
| Symbol | STOP Net PnL |
|---|---:|
| TSLA | -6,552.97 |
| AVGO | -4,954.80 |
| NVDA | -4,886.32 |
| NFLX | -4,766.58 |
| META | -4,713.29 |
| GOOGL | -3,554.53 |
| AMZN | -3,433.41 |
| QCOM | -3,168.42 |

### Highest STOP Rate
| Symbol | Stop Rate |
|---|---:|
| TSLA | 57.14% |
| QCOM | 55.56% |
| GOOGL | 50.00% |
| AVGO | 47.06% |
| META | 44.44% |

## DD Relation
- Worst DD peak: 2024-06-21
- Worst DD trough: 2026-04-17
- Worst DD: 9,257.14
- Trades in DD: 83
- STOP trades in DD: 39
- STOP ratio in DD: 46.99%
- STOP net loss in DD: -23,195.71
- Total net PnL in DD: -8,530.26

Interpretation:
- STOP trades are the dominant negative force inside the worst DD.
- Non-STOP exits partially offset STOP losses, but not enough.

## Critical Findings
1. STOP losses are structurally too large relative to total edge.
2. The primary issue is not only fake breakout entry; only 5.63% are classified as FAKE_BREAKOUT.
3. 71.83% of STOPs occur after 5+ bars, suggesting delayed loss realization or weak continuation.
4. 33.80% of STOP trades had MFE > 3% before stopping out, suggesting profit giveback.
5. TSLA, AVGO, NVDA, NFLX, META, and GOOGL are the main STOP loss contributors.

## Decision
Primary cause: risk/exit structure problem, not pure entry failure.

More specifically:
- Entry problem: partial, but not dominant.
- Exit/risk problem: dominant.
- Market environment problem: secondary; STOPs occur mostly in BULL because trade activity is concentrated there.
- Fake breakout weakness: present, but not the main failure mode.

## Next Actions
1. Design Task 068 - Risk Model Layer.
2. Evaluate profit-protection logic for trades with early MFE > 3%.
3. Analyze whether STOP distance / trailing / time stop should be risk-layer candidates.
4. Review high STOP-rate symbols before any normal pilot sizing.
