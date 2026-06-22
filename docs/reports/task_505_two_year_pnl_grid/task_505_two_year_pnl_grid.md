# Task 505 - Two-Year PnL Grid

## Decision Summary

- Best strategy: task505_theme_id_timing_state_avg12_win55_er45_pos10
- Two-year capital PnL: 722.99%
- Count / avg net / win / entry_reduce: 103 / 29.800% / 62.1% / 35.9%
- Median holding days / max drawdown: 84.60 / -18.99%
- Inferred lifecycle matching used: NO
- Label/outcome used in assignment: NO
- Strategy acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## Quant Expert Report

Task505 converts the Task503 exact lifecycle population into a two-year portfolio grid. It evaluates practical cell portfolios with a capacity-aware capital path instead of ranking only by average trade return. The selected strategy is still diagnostic because source coverage remains OHLCV/VWAP based and live execution readiness is not complete.

## No-Background Decision-Maker Report

This task answers which currently available strategy variant made the best two-year simulated portfolio PnL. It does not claim a deployable strategy. It uses only already linked lifecycle rows and does not guess missing trades.

## Key Metrics

- Accepted trades after position cap: 103
- Position cap: 10
- Capacity skips: 713