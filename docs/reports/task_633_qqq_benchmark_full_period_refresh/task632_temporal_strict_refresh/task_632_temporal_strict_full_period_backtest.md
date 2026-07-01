# Task632 Temporal Strict Full Period Backtest

## Decision Summary

- Verdict: `FAIL_TEMPORAL_STRICT_FULL_PERIOD_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Temporal strict trades: 331
- Temporal strict average net return: 10.29%

## Quant Expert Report

This reruns the 2024-2026 fresh confirmed candidate universe with chart features plus temporal-certified qualitative information. Date-only events are not allowed to support the qualitative score.

### Source Contract Audit

| Event Rows | Timestamp | Date-only | Time Certified | Strategy Entries | Source Time Gap Entries |
|---:|---:|---:|---:|---:|---:|
| 11999 | 11692 | 307 | 11692 | 331 | 3498 |

### Scenario Summary

| Scenario | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |
|---|---:|---:|---:|---:|
| `fresh_baseline_all_confirmed` | 5265 | 5.82% | 0.53% | 0.41% |
| `task617_original_broad_intelligence_strategy` | 633 | 13.39% | 0.63% | 0.32% |
| `task632_temporal_strict_chart_qual_strategy` | 331 | 10.29% | 0.62% | 0.34% |

### Split Summary

| Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure | Positive Split |
|---|---:|---:|---:|---:|---:|
| `train_design` | 164 | 16.28% | 0.74% | 0.23% | 1 |
| `validation` | 121 | 5.46% | 0.57% | 0.38% | 0 |
| `recent_oos` | 46 | 1.66% | 0.35% | 0.59% | 0 |

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `task617_original_broad_intelligence_strategy` | 5 | $3,248.89 | 224.89% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 5 | $2,214.37 | 121.44% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 10 | $2,181.69 | 118.17% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 10 | $2,050.17 | 105.02% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 20 | $2,774.52 | 177.45% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 20 | $1,934.19 | 93.42% |
| `full_panel` | `task617_original_broad_intelligence_strategy` | 50 | $2,116.85 | 111.68% |
| `full_panel` | `task632_temporal_strict_chart_qual_strategy` | 50 | $1,395.15 | 39.52% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 5 | $1,154.85 | 15.48% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 5 | $1,042.40 | 4.24% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 10 | $1,068.36 | 6.84% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 10 | $1,114.51 | 11.45% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 20 | $1,090.66 | 9.07% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 20 | $1,068.05 | 6.80% |
| `recent_oos` | `task617_original_broad_intelligence_strategy` | 50 | $1,064.20 | 6.42% |
| `recent_oos` | `task632_temporal_strict_chart_qual_strategy` | 50 | $1,010.03 | 1.00% |
| `validation` | `task617_original_broad_intelligence_strategy` | 5 | $1,320.39 | 32.04% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 5 | $1,406.95 | 40.70% |
| `validation` | `task617_original_broad_intelligence_strategy` | 10 | $1,234.35 | 23.44% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 10 | $1,250.33 | 25.03% |
| `validation` | `task617_original_broad_intelligence_strategy` | 20 | $1,252.03 | 25.20% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 20 | $1,094.63 | 9.46% |
| `validation` | `task617_original_broad_intelligence_strategy` | 50 | $1,147.45 | 14.74% |
| `validation` | `task632_temporal_strict_chart_qual_strategy` | 50 | $1,117.45 | 11.75% |

## No-Background Decision-Maker Report

- This is a full-period diagnostic backtest using chart data plus time-certified qualitative data.
- Date-only events are treated as source-time gaps and cannot support entries.
- The result is not accepted because recent OOS and full-panel account gates fail.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `runtime_temporal_contract_columns` | 1 | received=1; published=1; tradable=1 | event store must carry received_at published_at tradable_after_ts |
| `temporal_strict_candidate_count` | 1 | temporal_strategy_entries=331 | >=50 full-period temporal strict strategy entries |
| `date_only_events_not_used_as_support` | 1 | date_only_support_used=0 | date-only events must be reported as gaps and never support entry |
| `future_event_support_leakage` | 1 | future_event_support_leaks=0 | no event after entry may support the entry score |
| `full_period_avg_beats_baseline` | 1 | strict=10.29% baseline=5.82% original_task617=13.39% | temporal strict avg return must beat all-confirmed baseline by >=2pp |
| `split_stability` | 0 | positive_splits=1/3 | >=2 positive splits across >=3 splits |
| `recent_oos_50bp_account_vs_original` | 0 | strict_wins=1/4; max5 strict=$1042.40 original=$1154.85; max10 strict=$1114.51 original=$1068.36; max20 strict=$1068.05 original=$1090.66; max50 strict=$1010.03 original=$1064.20 | strict strategy beats original Task617 in >=3 of 4 recent-OOS capacities at 50bp |
| `validation_50bp_account_vs_original` | 1 | strict_wins=2/4; max5 strict=$1406.95 original=$1320.39; max10 strict=$1250.33 original=$1234.35; max20 strict=$1094.63 original=$1252.03; max50 strict=$1117.45 original=$1147.45 | strict strategy is at least mixed versus original on validation at 50bp |
| `full_panel_50bp_account_vs_original` | 0 | strict_wins=0/4; max5 strict=$2214.37 original=$3248.89; max10 strict=$2050.17 original=$2181.69; max20 strict=$1934.19 original=$2774.52; max50 strict=$1395.15 original=$2116.85 | strict strategy is at least mixed versus original on full panel at 50bp |
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