# Task 338: Intraday Evaluation Fix

- Final decision: `PARTIAL_INTRADAY_EDGE`.
- Anchored OOS covered trades: `50`.

## Split Coverage Summary

| split | total_trades | covered_trades | coverage_ratio |
| --- | --- | --- | --- |
| train | 1774 | 340 | 0.191657 |
| anchored_oos | 201 | 50 | 0.248756 |
| full_period | 1969 | 390 | 0.19807 |

## Prediction Metrics (Corrected)

| accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | ranking_correlation | split | window_mode | feature_set | target | model | coverage_trade_count | total_split_trades | coverage_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.511765 | 0.511765 | 0 | 1 |  |  | train | entry_only | core_only | bad_state | majority | 340 | 1774 | 0.191657 | ok |
| 0.629412 | 0.511765 | 0.117647 | 0.609195 |  |  | train | entry_only | core_only | bad_state | band_probability | 340 | 1774 | 0.191657 | ok |
| 0.65 | 0.511765 | 0.138235 | 0.718391 |  |  | train | entry_only | core_only | bad_state | logistic | 340 | 1774 | 0.191657 | ok |
| 0.847059 | 0.847059 | 0 |  | 0 |  | train | entry_only | core_only | clean_state | majority | 340 | 1774 | 0.191657 | ok |
| 0.847059 | 0.847059 | 0 |  | 0 |  | train | entry_only | core_only | clean_state | band_probability | 340 | 1774 | 0.191657 | ok |
| 0.847059 | 0.847059 | 0 |  | 0 |  | train | entry_only | core_only | clean_state | logistic | 340 | 1774 | 0.191657 | ok |
| 0.511765 | 0.511765 | 0 |  |  |  | train | entry_only | core_only | continuation_quality_rank | majority | 340 | 1774 | 0.191657 | ok |
| 0.526471 | 0.511765 | 0.014706 |  |  | 0.044573 | train | entry_only | core_only | continuation_quality_rank | band_probability | 340 | 1774 | 0.191657 | ok |
| 0.644118 | 0.511765 | 0.132353 |  |  | 0.328884 | train | entry_only | core_only | continuation_quality_rank | logistic | 340 | 1774 | 0.191657 | ok |
| 0.68 | 0.68 | 0 | 1 |  |  | anchored_oos | entry_only | core_only | bad_state | majority | 50 | 201 | 0.248756 | ok |
| 0.48 | 0.68 | -0.2 | 0.5 |  |  | anchored_oos | entry_only | core_only | bad_state | band_probability | 50 | 201 | 0.248756 | ok |
| 0.14 | 0.68 | -0.54 | 0.058824 |  |  | anchored_oos | entry_only | core_only | bad_state | logistic | 50 | 201 | 0.248756 | ok |
| 0.9 | 0.9 | 0 |  | 0 |  | anchored_oos | entry_only | core_only | clean_state | majority | 50 | 201 | 0.248756 | ok |
| 0.9 | 0.9 | 0 |  | 0 |  | anchored_oos | entry_only | core_only | clean_state | band_probability | 50 | 201 | 0.248756 | ok |
| 0.9 | 0.9 | 0 |  | 0 |  | anchored_oos | entry_only | core_only | clean_state | logistic | 50 | 201 | 0.248756 | ok |
| 0.68 | 0.68 | 0 |  |  |  | anchored_oos | entry_only | core_only | continuation_quality_rank | majority | 50 | 201 | 0.248756 | ok |
| 0.68 | 0.68 | 0 |  |  |  | anchored_oos | entry_only | core_only | continuation_quality_rank | band_probability | 50 | 201 | 0.248756 | ok |
| 0.34 | 0.68 | -0.34 |  |  | -0.079909 | anchored_oos | entry_only | core_only | continuation_quality_rank | logistic | 50 | 201 | 0.248756 | ok |
| 0.523077 | 0.523077 | 0 | 1 |  |  | full_period | entry_only | core_only | bad_state | majority | 390 | 1969 | 0.19807 | ok |
| 0.620513 | 0.523077 | 0.097436 | 0.602941 |  |  | full_period | entry_only | core_only | bad_state | band_probability | 390 | 1969 | 0.19807 | ok |
| 0.594872 | 0.523077 | 0.071795 | 0.622549 |  |  | full_period | entry_only | core_only | bad_state | logistic | 390 | 1969 | 0.19807 | ok |
| 0.84359 | 0.84359 | 0 |  | 0 |  | full_period | entry_only | core_only | clean_state | majority | 390 | 1969 | 0.19807 | ok |
| 0.84359 | 0.84359 | 0 |  | 0 |  | full_period | entry_only | core_only | clean_state | band_probability | 390 | 1969 | 0.19807 | ok |
| 0.84359 | 0.84359 | 0 |  | 0 |  | full_period | entry_only | core_only | clean_state | logistic | 390 | 1969 | 0.19807 | ok |

## Holdout Results (Corrected)

| accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | ranking_correlation | window_mode | feature_set | target | model | coverage_trade_count | coverage_ratio | status | holdout_type | holdout_value | split |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.45098 | 0.529412 | -0.078431 | 0.583333 |  |  | entry_only | core_only | bad_state | band_probability | 51 | 0.15 | ok | symbol | AMD | train_holdout |
| 0.632653 | 0.530612 | 0.102041 | 0.5 |  |  | entry_only | core_only | bad_state | band_probability | 49 | 0.144118 | ok | symbol | COST | train_holdout |
| 0.543478 | 0.543478 | 0 | 0.52381 |  |  | entry_only | core_only | bad_state | band_probability | 46 | 0.135294 | ok | symbol | GOOGL | train_holdout |
| 0.409091 | 0.818182 | -0.409091 | 0.5 |  |  | entry_only | core_only | bad_state | band_probability | 44 | 0.129412 | ok | symbol | QCOM | train_holdout |
| 0.357143 | 0.571429 | -0.214286 | 0.444444 |  |  | entry_only | core_only | bad_state | band_probability | 42 | 0.123529 | ok | symbol | AAPL | train_holdout |
| 0.243902 | 0.731707 | -0.487805 | 0.818182 |  |  | entry_only | core_only | bad_state | band_probability | 41 | 0.120588 | ok | symbol | MSFT | train_holdout |
| 0.814815 | 0.555556 | 0.259259 | 0.583333 |  |  | entry_only | core_only | bad_state | band_probability | 27 | 0.079412 | ok | symbol | META | train_holdout |
|  |  |  |  |  |  | entry_only | core_only | bad_state | band_probability | 0 |  | insufficient_sample | symbol | AMZN | train_holdout |
|  |  |  |  |  |  | entry_only | core_only | bad_state | band_probability | 0 |  | insufficient_sample | symbol | NVDA | train_holdout |
|  |  |  |  |  |  | entry_only | core_only | bad_state | band_probability | 0 |  | insufficient_sample | symbol | AVGO | train_holdout |
|  |  |  |  |  |  | entry_only | core_only | bad_state | band_probability | 0 |  | insufficient_sample | symbol | TSLA | train_holdout |
| 0.383459 | 0.56391 | -0.180451 | 0.534483 |  |  | entry_only | core_only | bad_state | band_probability | 133 | 0.391176 | ok | sector_bucket | software/internet | train_holdout |
| 0.436364 | 0.6 | -0.163636 | 0.227273 |  |  | entry_only | core_only | bad_state | band_probability | 110 | 0.323529 | ok | sector_bucket | semis | train_holdout |
| 0.632653 | 0.530612 | 0.102041 | 0.5 |  |  | entry_only | core_only | bad_state | band_probability | 49 | 0.144118 | ok | sector_bucket | other | train_holdout |
| 0.4375 | 0.5 | -0.0625 | 0.583333 |  |  | entry_only | core_only | bad_state | band_probability | 48 | 0.141176 | ok | sector_bucket | other tech | train_holdout |
| 0.615385 | 0.512821 | 0.102564 | 0.65 |  |  | entry_only | core_only | bad_state | band_probability | 39 | 0.114706 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.5|hold20|liq20000000|lb10|w0.15 | train_holdout |
| 0.692308 | 0.538462 | 0.153846 | 0.619048 |  |  | entry_only | core_only | bad_state | band_probability | 39 | 0.114706 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.0|hold20|liq20000000|lb10|w0.15 | train_holdout |
| 0.526316 | 0.526316 | 0 | 0.555556 |  |  | entry_only | core_only | bad_state | band_probability | 38 | 0.111765 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr1.5|hold30|liq20000000|lb10|w0.15 | train_holdout |
| 0.638889 | 0.527778 | 0.111111 | 0.705882 |  |  | entry_only | core_only | bad_state | band_probability | 36 | 0.105882 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|STRUCTURE_LOW_STOP|DISABLE_ENTRY_BAR_STOP|atr1.5|hold20|liq20000000|lb10|w0.15 | train_holdout |
| 0.647059 | 0.5 | 0.147059 | 0.647059 |  |  | entry_only | core_only | bad_state | band_probability | 34 | 0.1 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.0|hold30|liq20000000|lb10|w0.15 | train_holdout |
| 0.666667 | 0.515152 | 0.151515 | 0.6875 |  |  | entry_only | core_only | bad_state | band_probability | 33 | 0.097059 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.5|hold30|liq20000000|lb10|w0.15 | train_holdout |
| 0.606061 | 0.575758 | 0.030303 | 0.642857 |  |  | entry_only | core_only | bad_state | band_probability | 33 | 0.097059 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.5|hold20|liq20000000|lb10|w0.10 | train_holdout |
| 0.633333 | 0.633333 | 0 | 0.526316 |  |  | entry_only | core_only | bad_state | band_probability | 30 | 0.088235 | ok | scenario | PIVOT_HIGH|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.0|hold30|liq20000000|age60 | train_holdout |
| 0.655172 | 0.517241 | 0.137931 | 0.714286 |  |  | entry_only | core_only | bad_state | band_probability | 29 | 0.085294 | ok | scenario | RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|STRUCTURE_LOW_STOP|DISABLE_ENTRY_BAR_STOP|atr1.5|hold30|liq20000000|lb10|w0.15 | train_holdout |

## Economic Action Test (Corrected)

| split | window_mode | feature_set | policy_name | baseline_expectancy | diagnostic_expectancy | baseline_return_proxy | diagnostic_return_proxy | saved_loss | missed_gain | trade_count | total_split_trades | diagnostic_trade_count | coverage_trade_count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | entry_only | core_only | bad_skip_clean_fullsize | -0.116889 | -0.366192 | -5.84447 | -16.1124 | 0 | 10.6218 | 50 | 201 | 44 | 50 | ok |
| anchored_oos | entry_only | intraday_only_entry_only | bad_skip_clean_fullsize | -0.116889 | -0.47408 | -5.84447 | -6.63711 | 17.0939 | 18.444 | 50 | 201 | 14 | 50 | ok |
| anchored_oos | entry_only | intraday_only_immediate_post_break | bad_skip_clean_fullsize |  |  |  |  |  |  | 50 | 201 | 0 | 50 | insufficient_intraday_coverage |
| anchored_oos | entry_only | core_plus_intraday_entry_only | bad_skip_clean_fullsize | -0.116889 | -0.675229 | -5.84447 | -10.8037 | 15.0964 | 18.444 | 50 | 201 | 16 | 50 | ok |
| anchored_oos | entry_only | core_plus_intraday_immediate_post_break | bad_skip_clean_fullsize |  |  |  |  |  |  | 50 | 201 | 0 | 50 | insufficient_intraday_coverage |
| anchored_oos | entry_only | intraday_plus_volume | bad_skip_clean_fullsize | -0.116889 | 0.315628 | -5.84447 | 7.57508 | 14.8348 | 1.41527 | 50 | 201 | 24 | 50 | ok |
| anchored_oos | entry_only | intraday_plus_vwap | bad_skip_clean_fullsize | -0.116889 | -0.68692 | -5.84447 | -10.9907 | 15.0964 | 18.444 | 50 | 201 | 16 | 50 | ok |
| anchored_oos | entry_only | all_combined_entry_only | bad_skip_clean_fullsize | -0.116889 | -0.675229 | -5.84447 | -10.8037 | 15.0964 | 18.444 | 50 | 201 | 16 | 50 | ok |
| anchored_oos | entry_only | all_combined_immediate_post_break | bad_skip_clean_fullsize |  |  |  |  |  |  | 50 | 201 | 0 | 50 | insufficient_intraday_coverage |
| anchored_oos | immediate_post_break | core_only | bad_skip_clean_fullsize | -0.106171 | -0.143208 | -5.09621 | -6.30115 | 0 | 3.36349 | 48 | 201 | 44 | 48 | ok |
| anchored_oos | immediate_post_break | intraday_only_entry_only | bad_skip_clean_fullsize |  |  |  |  |  |  | 48 | 201 | 0 | 48 | insufficient_intraday_coverage |
| anchored_oos | immediate_post_break | intraday_only_immediate_post_break | bad_skip_clean_fullsize | -0.106171 | 0.467782 | -5.09621 | 9.82342 | 15.0964 | 2.54883 | 48 | 201 | 21 | 48 | ok |
| anchored_oos | immediate_post_break | core_plus_intraday_entry_only | bad_skip_clean_fullsize |  |  |  |  |  |  | 48 | 201 | 0 | 48 | insufficient_intraday_coverage |
| anchored_oos | immediate_post_break | core_plus_intraday_immediate_post_break | bad_skip_clean_fullsize | -0.106171 | 0.110148 | -5.09621 | 3.19428 | 10.2818 | 2.54883 | 48 | 201 | 29 | 48 | ok |
| anchored_oos | immediate_post_break | intraday_plus_volume | bad_skip_clean_fullsize | -0.106171 | 0.261399 | -5.09621 | 7.31918 | 13.4908 | 1.13356 | 48 | 201 | 28 | 48 | ok |
| anchored_oos | immediate_post_break | intraday_plus_vwap | bad_skip_clean_fullsize | -0.106171 | -0.638799 | -5.09621 | -8.94319 | 15.0964 | 18.444 | 48 | 201 | 14 | 48 | ok |
| anchored_oos | immediate_post_break | all_combined_entry_only | bad_skip_clean_fullsize |  |  |  |  |  |  | 48 | 201 | 0 | 48 | insufficient_intraday_coverage |
| anchored_oos | immediate_post_break | all_combined_immediate_post_break | bad_skip_clean_fullsize | -0.106171 | 0.110148 | -5.09621 | 3.19428 | 10.2818 | 2.54883 | 48 | 201 | 29 | 48 | ok |

## Final Answer

- Covered-subset evaluation now uses only trades with valid intraday windows.
- Splits with partial coverage are evaluated on the covered subset instead of being dropped wholesale.
- Splits below the minimum covered-sample threshold are marked `insufficient_sample` rather than `insufficient_intraday_coverage`.