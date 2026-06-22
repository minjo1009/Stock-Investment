# Task1911-1920 Watch Recovery Decomposition

## Decision Summary

- Verdict: `watch_recovery_decomposition_complete`.
- Top3 delta vs desk: 52.0012.
- Top5 delta vs desk: -14.6055.
- Primary bottleneck: `top5_recovery_candidate_quality_and_overlap_fragility`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Subtype view:

| Policy | Subtype | Rows | Capital Delta | Incremental PnL | Positive | Negative | Avg Return |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `watch_recovery_top3_v1` | `damage_watch` | 26 | 13.0098 | -0.6467 | 5 | 5 | 0.033536 |
| `watch_recovery_top3_v1` | `information_gap_watch` | 4 | -0.4367 | -0.1329 | 1 | 1 | 0.097798 |
| `watch_recovery_top3_v1` | `normal_winner_volatility_watch` | 14 | 194.8171 | 42.6636 | 7 | 4 | 0.079332 |
| `watch_recovery_top3_v1` | `not_applicable` | 111 | 21.1139 | -2.6521 | 18 | 26 | 0.013874 |
| `watch_recovery_top3_v1` | `overhang_watch` | 3 | -0.1091 | -0.0272 | 1 | 1 | 0.121311 |
| `watch_recovery_top3_v1` | `upgrade_candidate_watch` | 2 | 251.2503 | 12.7965 | 1 | 1 | 0.049496 |
| `watch_recovery_top5_v1` | `damage_watch` | 30 | -45.1758 | -0.0681 | 7 | 8 | 0.031117 |
| `watch_recovery_top5_v1` | `information_gap_watch` | 4 | -10.3641 | -1.4244 | 0 | 3 | 0.097798 |
| `watch_recovery_top5_v1` | `normal_winner_volatility_watch` | 17 | 72.2817 | 15.5549 | 9 | 7 | 0.077453 |
| `watch_recovery_top5_v1` | `not_applicable` | 153 | -355.4849 | -12.6945 | 30 | 49 | 0.018116 |
| `watch_recovery_top5_v1` | `overhang_watch` | 10 | -15.1277 | -0.2453 | 3 | 1 | 0.04555 |
| `watch_recovery_top5_v1` | `upgrade_candidate_watch` | 3 | 280.4705 | -15.7286 | 1 | 2 | -0.010622 |

Overlap/cohort view:

| Policy | Cohort | Rows | Incremental PnL | Avg Return |
| --- | --- | ---: | ---: | ---: |
| `watch_recovery_top3_v1` | `common_top3_top5` | 160 | 52.0012 | 0.027355 |
| `watch_recovery_top5_v1` | `common_top3_top5` | 160 | 7.5008 | 0.027355 |
| `watch_recovery_top5_v1` | `top5_only` | 57 | -22.1068 | 0.025616 |

Worst symbol view:

| Policy | Symbol | Rows | Incremental PnL | Avg Return |
| --- | --- | ---: | ---: | ---: |
| `watch_recovery_top5_v1` | `ANET` | 16 | -25.2444 | 0.04771 |
| `watch_recovery_top3_v1` | `AMZN` | 2 | -12.198 | -0.008985 |
| `watch_recovery_top5_v1` | `AMZN` | 2 | -6.2597 | -0.008985 |
| `watch_recovery_top5_v1` | `ALNY` | 4 | -1.8621 | 0.118854 |
| `watch_recovery_top5_v1` | `AXON` | 1 | -1.099 | 0.525651 |
| `watch_recovery_top5_v1` | `C` | 1 | -1.0653 | 0.135864 |
| `watch_recovery_top5_v1` | `AMD` | 2 | -0.9789 | 0.074252 |
| `watch_recovery_top5_v1` | `AVGO` | 22 | -0.8978 | 0.00983 |
| `watch_recovery_top5_v1` | `AGX` | 3 | -0.8144 | 0.064061 |
| `watch_recovery_top5_v1` | `ADPT` | 1 | -0.7318 | 0.163109 |
| `watch_recovery_top5_v1` | `AZO` | 6 | -0.6638 | 0.044084 |
| `watch_recovery_top5_v1` | `ALL` | 5 | -0.5953 | 0.038696 |

Diagnosis:

- `policy_result`: top3_recovery_helped_but_top5_recovery_hurt (top3_delta_vs_desk=52.0012;top5_delta_vs_desk=-14.6055).
- `candidate_count`: top5_has_more_recovered_rows_but_lower_increment_quality (top3_recovery_rows=16;top5_recovery_rows=20).
- `root`: do_not_expand_recovery_beyond_top3_without_source_field_rule (Top5 deterioration means recovery candidates need a stricter predeclared source-field filter.).
- `slot_overlap`: top5_only_bucket_is_the_first_place_to_audit (top5_only_increment=-22.1068).

Leakage audit:

- This decomposition uses outcome deltas only for audit.
- It does not create an assignment rule.
- Any future narrowed replay must freeze source-field eligibility first.

## No-Background Decision-Maker Report

1. Top3 improved because recovery was applied to a concentrated set where added capital helped.
2. Top5 worsened because the same recovery rule reached weaker extra rows.
3. The next filter must be stricter than just subtype.
4. Do not expand recovery broadly.
5. The top5-only bucket is the first fragility bucket to audit.
6. Either keep recovery top3-only or create a source-field filter for top5.

## Artifact Manifest

- `task1911_input_manifest.csv`
- `task1912_policy_trade_delta.csv`
- `task1913_subtype_view.csv`
- `task1914_symbol_month_views.csv`
- `task1915_overlap_cohort_view.csv`
- `task1916_best_worst_recovery_rows.csv`
- `task1917_narrow_candidate_audit.csv`
- `task1918_diagnosis.csv`
- `task1919_next_task_plan.csv`
- `task1920_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1911_1920_watch_recovery_decomposition_validate.py`
- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```