# Task 319 - TBL Volume Multiplier Sweep

## Summary
- Grid: `1.00~2.00, step 0.05`
- Fixed params: breakout=10, stop ATR=2.0, partial=2.0R, trailing=3.0ATR, execution/risk unchanged

## Top Sharpe
- vol=1.20, sharpe=0.416506, cagr=3.332145%, expectancy_r=0.302793, trades=137
- vol=1.15, sharpe=0.367602, cagr=3.02644%, expectancy_r=0.258916, trades=150
- vol=1.10, sharpe=0.342018, cagr=2.909531%, expectancy_r=0.198949, trades=169

## KPI Table

| volume_multiplier | cagr_pct | sharpe | expectancy_r | trade_count |
|---:|---:|---:|---:|---:|
| 1.00 | 1.746708 | 0.233374 | 0.178076 | 132 |
| 1.05 | 2.093302 | 0.272533 | 0.211377 | 114 |
| 1.10 | 2.909531 | 0.342018 | 0.198949 | 169 |
| 1.15 | 3.02644 | 0.367602 | 0.258916 | 150 |
| 1.20 | 3.332145 | 0.416506 | 0.302793 | 137 |
