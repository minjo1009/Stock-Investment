# Task 345: Intraday Coverage Alignment Audit & Covered-Subset Recovery

Final decision: **MATERIAL_RECOVERABLE_COVERAGE**

## Failure Taxonomy

| failure_reason | trade_count | share_of_incomplete | anchored_oos_trade_count | software_internet_anchored_oos_trade_count |
| --- | --- | --- | --- | --- |
| insufficient_prebreak_bars | 487 | 0.308423 | 93 | 33 |
| insufficient_postbreak_bars | 0 | 0 | 0 | 0 |
| breakout_bar_not_found | 107 | 0.067764 | 0 | 0 |
| short_session_or_holiday_session | 0 | 0 | 0 | 0 |
| provider_session_truncation | 10 | 0.006333 | 0 | 0 |
| timezone_or_timestamp_misalignment | 975 | 0.617479 | 56 | 29 |

## Anchored OOS Alignment / Window Comparison

| split | alignment_rule | window_rule | prebreak_min_bars | postbreak_min_bars | covered_trade_count | recovered_trade_count_vs_current | coverage_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | close_confirmed_break | relaxed_prebreak_minimum | 1 | 5 | 98 | 48 | 0.487562 |
| anchored_oos | high_touch_first_touch | relaxed_prebreak_minimum | 1 | 5 | 84 | 34 | 0.41791 |
| anchored_oos | tolerant_max_high_close | relaxed_prebreak_minimum | 1 | 5 | 84 | 34 | 0.41791 |
| anchored_oos | close_confirmed_break | current_strict | 3 | 5 | 75 | 25 | 0.373134 |
| anchored_oos | close_confirmed_break | relaxed_postbreak_minimum | 3 | 1 | 75 | 25 | 0.373134 |
| anchored_oos | high_touch_first_touch | current_strict | 3 | 5 | 50 | 0 | 0.248756 |

## Recovery Summary

| split | variant | covered_trade_count | delta_vs_current | coverage_ratio | software_internet_trade_count |
| --- | --- | --- | --- | --- | --- |
| full_period | current_strict_high_touch | 390 | 0 | 0.19807 | 149 |
| full_period | strict_close_confirm | 449 | 59 | 0.228035 | 158 |
| full_period | relaxed_prebreak_high_touch | 481 | 91 | 0.244286 | 173 |
| full_period | relaxed_postbreak_high_touch | 390 | 0 | 0.19807 | 149 |
| full_period | combined_best_recovery | 551 | 161 | 0.279837 | 200 |
| anchored_oos | current_strict_high_touch | 50 | 0 | 0.248756 | 16 |
| anchored_oos | strict_close_confirm | 75 | 25 | 0.373134 | 16 |
| anchored_oos | relaxed_prebreak_high_touch | 84 | 34 | 0.41791 | 24 |
| anchored_oos | relaxed_postbreak_high_touch | 50 | 0 | 0.248756 | 16 |
| anchored_oos | combined_best_recovery | 98 | 48 | 0.487562 | 29 |

## Interpretation

- The dominant current failure mode is `timezone_or_timestamp_misalignment`.
- `tolerant_max_high_close` is mathematically equivalent to `high_touch_first_touch`, so it does not create extra recovery by construction.
- Relaxing the post-break minimum does not materially help because the current failures are almost entirely pre-break alignment / pre-break window failures.
- Best combined recovery adds `48` anchored OOS covered trades and `13` software/internet anchored OOS trades.
- If this recovery is accepted as diagnostic-valid, rerunning Tasks 338-342 is justified before moving to priority overlay research.