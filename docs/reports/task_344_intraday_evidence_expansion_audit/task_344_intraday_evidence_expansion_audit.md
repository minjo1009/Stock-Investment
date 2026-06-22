# Task 344: Intraday Evidence Expansion Audit

Final decision: **NO_EVIDENCE_EXPANSION_GAIN**

## Retry Attempt

| attempt_scope_count | covered_after_retry | still_insufficient_after_retry | coverage_gain_dates | retry_result |
| --- | --- | --- | --- | --- |
| 17 | 0 | 17 | 0 | no_coverage_gain |

## Anchored OOS Coverage Reasons

| split | reason | trade_count | share |
| --- | --- | --- | --- |
| anchored_oos | incomplete_intraday_window | 149 | 0.741294 |
| anchored_oos | covered | 50 | 0.248756 |
| anchored_oos | missing_date | 2 | 0.00995 |

## Uncovered Anchored OOS Symbols

| symbol | uncovered_trade_count |
| --- | --- |
| AMD | 21 |
| AMZN | 20 |
| GOOGL | 20 |
| COST | 19 |
| TSLA | 15 |
| AAPL | 12 |
| MSFT | 10 |
| NVDA | 10 |
| QCOM | 8 |
| META | 7 |
| NFLX | 7 |
| AVGO | 2 |

## Interpretation

- The targeted backfill retry produced `0` newly covered required dates.
- Remaining anchored OOS gap is dominated by `incomplete_intraday_window`, not by `missing_date` or `missing_symbol`.
- This means the next evidence-quality bottleneck is no longer raw archive presence alone.
- Recommended next step: `priority_overlay_research_should_wait_for_better_coverage_or_better_breakout_alignment`