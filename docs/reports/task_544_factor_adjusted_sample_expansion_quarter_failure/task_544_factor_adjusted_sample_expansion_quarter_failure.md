# Task 544 Factor-Adjusted Sample Expansion and Quarter Failure Decomposition

## Decision Summary

- Strategy acceptance: FACTOR_ADJUSTED_SAMPLE_EXPANSION_DIAGNOSTIC_ONLY
- Expansion candidates tested: 6
- Recent OOS sample-expanded candidates: 6
- Recent OOS positive expanded candidates: 6
- Deployment-ready: NO

## Quant Expert Report

Task544 tests adjacent entry-safe expansion candidates; it does not optimize thresholds on residual outcomes.
base_trend_closepos_097: recent OOS adjusted count 110, residual 15.57%, entry_reduce 31.01%.
expanded_trend_closepos_099: recent OOS adjusted count 118, residual 15.24%, entry_reduce 31.09%.
strict_regime_near_high_upper_range: recent OOS adjusted count 100, residual 14.81%, entry_reduce 34.45%.
strict_regime_opening_midday: recent OOS adjusted count 108, residual 14.92%, entry_reduce 31.20%.
strict_regime_trend_closepos_099: recent OOS adjusted count 115, residual 15.42%, entry_reduce 31.05%.
strict_regime_volume_confirmed: recent OOS adjusted count 61, residual 18.18%, entry_reduce 36.41%.
2025Q1-Q3 failure decomposition top contributors:
exit_reason=trailing_stop_exit: count 13, residual -28.94%, entry_reduce 92.31%.
timing_state=opening_drive: count 29, residual -12.93%, entry_reduce 51.72%.
intraday_entry_state_v4=intraday_breakout_acceptance: count 35, residual -9.97%, entry_reduce 42.86%.
multi_day_market_state_v4=constructive_risk_on: count 35, residual -9.97%, entry_reduce 42.86%.
symbol_multiday_setup_state=volume_confirmed_reclaim: count 14, residual -15.32%, entry_reduce 57.14%.

## No-Background Decision-Maker Report

We tried to increase the recent OOS sample without inventing data or changing labels.
We also decomposed the weak 2025 quarters to see whether the problem came from regime, theme, entry structure, or exits.
This remains diagnostic. A larger positive recent OOS sample is required before any firm-grade claim.

## Artifact Manifest

See `artifact_manifest.csv`.
