# Task 068 - Risk Model Layer Experiment

## Setup
- Entry policy: `LIMITED_CHASE`
- Fee: 0.25% per side
- Slippage: 0.10% per side
- Universe: AAPL, AMD, AMZN, AVGO, COST, GOOGL, META, MSFT, NFLX, NVDA, QCOM, TSLA
- Script: `python -m backtest.analysis_risk_model_layer`
- Full JSON: `docs/task_068_risk_model_layer.json`

## Risk Policies
- `BASELINE`: current STOP only
- `BREAK_EVEN_STOP`: if MFE >= +3%, lift stop to entry fill
- `MFE_GIVEBACK_50`: if MFE >= +3%, exit after giving back 50% of max profit
- `TIME_STOP`: after 10 bars, exit if profit is below +1%
- `HYBRID`: break-even stop + MFE giveback + time stop

## Results Table

| Policy | PF | Net PnL | MDD | Sharpe | STOP Count | GOOD_THEN_STOP Reduction |
|---|---:|---:|---:|---:|---:|---:|
| BASELINE | 1.0835 | 4,582.87 | 9,885.24 | 0.3893 | 71 | 0 |
| BREAK_EVEN_STOP | 0.8450 | -5,987.21 | 11,112.91 | -0.6860 | 49 | 24 |
| MFE_GIVEBACK_50 | 0.7054 | -12,876.48 | 13,450.49 | -2.1187 | 66 | 23 |
| TIME_STOP | 1.0938 | 4,588.73 | 9,874.46 | 0.4002 | 57 | 10 |
| HYBRID | 0.4810 | -23,269.52 | 23,748.90 | -4.1000 | 59 | 24 |

## Key Observations
1. `BREAK_EVEN_STOP` and `HYBRID` eliminate GOOD_THEN_STOP, but both destroy performance.
2. `MFE_GIVEBACK_50` turns many trades into small exits, but KIS costs overwhelm the captured profit.
3. `TIME_STOP` is the only policy that improves PF, Net PnL, MDD, Sharpe, STOP count, and GOOD_THEN_STOP at the same time.
4. No policy reaches PF >= 1.2 under KIS realistic cost.
5. The first risk-layer candidates are too aggressive for the current strategy/cost structure.

## Best Policy
No policy satisfies the full selection criteria:
- PF >= 1.2
- Net PnL increase
- MDD decrease
- GOOD_THEN_STOP reduction

Best practical candidate: `TIME_STOP`.
- PF: 1.0835 -> 1.0938
- Net PnL: 4,582.87 -> 4,588.73
- MDD: 9,885.24 -> 9,874.46
- STOP Count: 71 -> 57
- GOOD_THEN_STOP: 24 -> 14

The improvement is real but too small to unlock pilot PASS.

## Risk Analysis
- Break-even and giveback policies increase trade count by freeing capital faster, but the extra turnover is costly.
- The policies reduce STOP labels but can replace them with low-quality early exits.
- Profit protection must avoid converting trend winners into small fee-adjusted losses.
- The strategy needs a less aggressive risk layer or symbol/regime-aware risk model.

## Decision
Do not apply `BREAK_EVEN_STOP`, `MFE_GIVEBACK_50`, or `HYBRID` as currently defined.

`TIME_STOP` is worth keeping as a candidate for the next experiment, but it is not strong enough by itself.

## Next Actions
1. Run a parameter grid around time stop thresholds without changing entry logic.
2. Test less aggressive giveback rules, such as MFE trigger >= 5% and giveback 60-70%.
3. Add cost-aware minimum profit buffer before any protective exit.
4. Re-check risk policies by symbol group to avoid penalizing strong trend symbols.
