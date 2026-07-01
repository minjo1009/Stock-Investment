# Task632 Temporal Strict Full Period Backtest

## Decision Summary

- Verdict: `FAIL_TEMPORAL_STRICT_FULL_PERIOD_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Temporal strict trades: 377
- Temporal strict average net return: 11.14%

## Quant Expert Report

This reruns the 2024-2026 fresh confirmed candidate universe with chart features plus temporal-certified qualitative information. Date-only events are not allowed to support the qualitative score.

### Source Contract Audit

| Event Rows | Timestamp | Date-only | Time Certified | Strategy Entries | Source Time Gap Entries |
|---:|---:|---:|---:|---:|---:|
| 12072 | 11755 | 317 | 11755 | 377 | 3503 |

### Scenario Summary

| Scenario | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |
|---|---:|---:|---:|---:|
| `fresh_baseline_all_confirmed` | 5041 | 8.62% | 0.59% | 0.35% |
| `task617_original_broad_intelligence_strategy` | 735 | 13.92% | 0.65% | 0.32% |
| `task632_temporal_strict_chart_qual_strategy` | 377 | 11.14% | 0.64% | 0.33% |

### Split Summary

| Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure | Positive Split |
|---|---:|---:|---:|---:|---:|
| `train_design` | 176 | 17.93% | 0.74% | 0.24% | 1 |
| `validation` | 149 | 7.26% | 0.62% | 0.36% | 0 |
| `recent_oos` | 52 | -0.73% | 0.38% | 0.52% | 0 |

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `task617_original_broad_intelligence_strategy` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 5 | $2,642.31 | 164.23% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 10 | $2,283.57 | 128.36% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 20 | $2,209.69 | 120.97% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 50 | $2,423.35 | 142.33% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 50 | $1,502.62 | 50.26% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 5 | $1,000.47 | 0.05% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 10 | $910.69 | -8.93% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 20 | $970.73 | -2.93% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 50 | $1,057.44 | 5.74% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 50 | $985.94 | -1.41% |
| `validation` | `task617_original_broad_intelligence_strategy` | 5 | $1,225.81 | 22.58% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 5 | $1,324.89 | 32.49% |
| `validation` | `task617_original_broad_intelligence_strategy` | 10 | $1,151.47 | 15.15% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 10 | $1,395.94 | 39.59% |
| `validation` | `task617_original_broad_intelligence_strategy` | 20 | $1,225.36 | 22.54% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 20 | $1,152.57 | 15.26% |
| `validation` | `task617_original_broad_intelligence_strategy` | 50 | $1,128.52 | 12.85% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 50 | $1,125.43 | 12.54% |

## No-Background Decision-Maker Report

- This is a full-period diagnostic backtest using chart data plus time-certified qualitative data.
- Date-only events are treated as source-time gaps and cannot support entries.
- The result is not accepted because recent OOS and full-panel account gates fail.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `runtime_temporal_contract_columns` | 1 | received=1; published=1; tradable=1 | event store must carry received_at published_at tradable_after_ts |
| `temporal_strict_candidate_count` | 1 | temporal_strategy_entries=377 | >=50 full-period temporal strict strategy entries |
| `date_only_events_not_used_as_support` | 1 | date_only_support_used=0 | date-only events must be reported as gaps and never support entry |
| `future_event_support_leakage` | 1 | future_event_support_leaks=0 | no event after entry may support the entry score |
| `full_period_avg_beats_baseline` | 1 | strict=11.14% baseline=8.62% original_task617=13.92% | temporal strict avg return must beat all-confirmed baseline by >=2pp |
| `split_stability` | 0 | positive_splits=1/3 | >=2 positive splits across >=3 splits |
| `recent_oos_50bp_account_vs_original` | 0 | strict_wins=0/4; max5 strict=$1000.47 original=$1313.22; max10 strict=$910.69 original=$1044.35; max20 strict=$970.73 original=$1043.58; max50 strict=$985.94 original=$1057.44 | strict strategy beats original Task617 in >=3 of 4 recent-OOS capacities at 50bp |
| `validation_50bp_account_vs_original` | 1 | strict_wins=2/4; max5 strict=$1324.89 original=$1225.81; max10 strict=$1395.94 original=$1151.47; max20 strict=$1152.57 original=$1225.36; max50 strict=$1125.43 original=$1128.52 | strict strategy is at least mixed versus original on validation at 50bp |
| `full_panel_50bp_account_vs_original` | 0 | strict_wins=0/4; max5 strict=$2642.31 original=$4158.91; max10 strict=$2283.57 original=$3229.78; max20 strict=$2209.69 original=$2924.57; max50 strict=$1502.62 original=$2423.35 | strict strategy is at least mixed versus original on full panel at 50bp |
| `trading_promotion` | 0 | full-period temporal strict backtest only | requires live source readiness and confirmation-gated entry before promotion |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_scored_entry_panel.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`
- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`

### Outputs

- `task_632_temporal_intelligence_entry_panel.csv`
- `task_632_temporal_strict_scored_entry_panel.csv`
- `task_632_temporal_strict_strategy_backtest_panel.csv`
- `task_632_scenario_summary.csv`
- `task_632_split_summary.csv`
- `task_632_cost_account_matrix.csv`
- `task_632_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task632_temporal_strict_full_period_backtest`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
- `python scripts/governance_completion_audit.py`