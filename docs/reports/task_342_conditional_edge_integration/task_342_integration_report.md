# Task 342: Conditional Edge Integration & Portfolio-Level Validation

Final decision: **NO_IMPROVEMENT**

## Best Overlay

- best_primary_variant: `overlay_2p0_0p5`
- anchored_oos_sharpe_delta: `0.497383`
- anchored_oos_mdd_delta: `-8.1074`
- anchored_oos_expectancy_delta: `0.118183`
- symbol_concentration_share: `0.16668`
- sector_concentration_share: `0.571473`

## Hybrid Full Anchored OOS Comparison

| variant | baseline_sharpe | overlay_sharpe | sharpe_delta | baseline_max_drawdown_pct | overlay_max_drawdown_pct | mdd_delta | expectancy_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| overlay_1p5_1p0 | -0.64761 | -0.427785 | 0.219825 | 59.0855 | 58.105 | -0.980445 | 0.034399 |
| overlay_1p5_0p5 | -0.64761 | -0.362365 | 0.285245 | 59.0855 | 52.1213 | -6.96418 | 0.083784 |
| overlay_2p0_1p0 | -0.64761 | -0.227161 | 0.420449 | 59.0855 | 57.1047 | -1.98079 | 0.068799 |
| overlay_2p0_0p5 | -0.64761 | -0.150227 | 0.497383 | 59.0855 | 50.9781 | -8.1074 | 0.118183 |
| conservative_1p5_1p0 | -0.64761 | -0.427785 | 0.219825 | 59.0855 | 58.105 | -0.980445 | 0.034399 |
| filter_skip | -0.64761 | -0.505599 | 0.142011 | 59.0855 | 46.596 | -12.4895 | 0.09877 |
| filter_reduce_0p25 | -0.64761 | -0.558472 | 0.089138 | 59.0855 | 50.0255 | -9.06002 | 0.074078 |

## Rolling OOS

| window_id | subset_trade_count | condition_met_trade_count | baseline_expectancy | overlay_expectancy | baseline_sharpe_proxy | overlay_sharpe_proxy | baseline_mdd_proxy | overlay_mdd_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| window_1 | 10 | 10 | 0.789819 | 0.712111 | 1.92306 | 1.85099 | 51.6267 | 50.7285 |
| window_2 | 18 | 0 | 0.76823 | 0.745264 | 1.6095 | 1.57063 | 42.0754 | 39.2511 |
| window_3 | 17 | 12 | 0.485162 | 0.5114 | 1.62134 | 1.65489 | 32.2778 | 29.1391 |
| window_4 | 33 | 16 | -0.27516 | -0.156977 | -0.64761 | -0.150227 | 59.0855 | 50.9781 |

## Cost Stress

| scenario | expectancy_after_cost | sharpe_after_cost | return_after_cost | mdd_after_cost | edge_survives_cost |
| --- | --- | --- | --- | --- | --- |
| baseline_cost | -0.156977 | -0.150227 | -27.4047 | 50.9781 | False |
| cost_2x | -0.256464 | -0.538178 | -40.2143 | 57.1101 | False |
| cost_3x | -0.306207 | -0.723581 | -45.7491 | 59.8844 | False |

## Interpretation

- Overlay improved Sharpe: `True`
- Overlay reduced drawdown: `True`
- CAGR / expectancy preserved or improved: `True`
- Rolling OOS improvement repeated: `2` windows
- Cost stress survived through 2x: `False`
- Next step: research-only monitoring