# Task620 Recent OOS Failure Decomposition

## Decision Summary

- Verdict: `FAIL_RECENT_OOS_STABILITY_SOURCE_FLAGS_TOO_BROAD`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Recent OOS: 109 trades, avg 2.17%, win 33.03%, entry-reduce 60.55%.
- Top failure taxonomy: `theme_specific_collapse_aerospace_defense` with 29 problem trades.
- GPT/plugin output is not used as a source or score input.

## Quant Expert Report

### Failure Taxonomy Summary

| Taxonomy | Trades | Problems | Avg Return | Win | Entry-Reduce | Avg Event Density |
|---|---:|---:|---:|---:|---:|---:|
| `theme_specific_collapse_aerospace_defense` | 29 | 29 | -18.49% | 0.00% | 100.00% | 23.03 |
| `trailing_stop_path_failure` | 14 | 14 | -10.62% | 0.00% | 85.71% | 30.79 |
| `broad_event_support_without_recent_ir_proxy` | 11 | 11 | -9.65% | 0.00% | 90.91% | 26.55 |
| `late_midday_continuation_decay` | 9 | 9 | -9.65% | 0.00% | 88.89% | 23.78 |
| `residual_recent_oos_problem` | 8 | 8 | -5.26% | 0.00% | 62.50% | 22.38 |
| `overextended_persistent_theme_leader` | 2 | 2 | -11.35% | 0.00% | 100.00% | 35.50 |
| `clean_recent_oos_winner` | 36 | 0 | 32.75% | 100.00% | 0.00% | 23.11 |

### Biggest Degradation Buckets

| Dimension | Bucket | Validation Count | Validation Avg | Recent Count | Recent Avg | Delta | Recent Entry-Reduce |
|---|---|---:|---:|---:|---:|---:|---:|
| `theme_id` | `aerospace_defense_space` | 60 | 0.12% | 29 | -18.49% | -18.60pp | 100.00% |
| `theme_id` | `industrial_automation_robotics` | 109 | 23.90% | 58 | 5.85% | -18.05pp | 58.62% |
| `theme_ret20_gt_15` | `1` | 54 | 0.78% | 31 | -16.26% | -17.04pp | 93.55% |
| `theme_regime_state_v4` | `persistent_theme_leader` | 98 | 7.46% | 73 | -6.25% | -13.71pp | 73.97% |
| `timing_state` | `midday_continuation` | 72 | 8.64% | 42 | -1.16% | -9.79pp | 66.67% |
| `ceo_ir_proxy_pre14d_flag` | `0` | 144 | 11.68% | 71 | 2.72% | -8.96pp | 64.79% |
| `overall` | `all` | 262 | 9.63% | 109 | 2.17% | -7.47pp | 60.55% |
| `exit_reason` | `time_exit` | 201 | 17.98% | 72 | 11.08% | -6.90pp | 48.61% |

### Intelligence Source Findings

| Source Flag | Recent Active Share | Discriminates In Recent OOS | Finding |
|---|---:|---:|---|
| `political_statement_pre7d_flag` | 100.00% | 0 | `too_broad_in_recent_oos` |
| `geopolitical_event_pre7d_flag` | 100.00% | 0 | `too_broad_in_recent_oos` |
| `institution_ownership_pre30d_flag` | 100.00% | 0 | `too_broad_in_recent_oos` |
| `passive_13g_pre30d_flag` | 20.18% | 1 | `has_some_cross_sectional_variation` |
| `insider_form4_or_144_pre30d_flag` | 99.08% | 1 | `has_some_cross_sectional_variation` |
| `ceo_ir_proxy_pre14d_flag` | 34.86% | 1 | `has_some_cross_sectional_variation` |
| `p0_source_event_density_ge2_flag` | 100.00% | 0 | `too_broad_in_recent_oos` |

## No-Background Decision-Maker Report

- Recent OOS weakness is real and still blocks promotion.
- The intelligence layer helps diagnosis, but the current event flags are too broad in recent OOS.
- The largest damage comes from aerospace/defense-space, overextended persistent theme leaders, and trailing-stop path failures.
- This supports better source typing and recent-OOS decomposition before strategy refinement.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `taxonomy_coverage` | 1 | 100.00% | >=80.00% of recent OOS problem trades assigned to a taxonomy |
| `recent_oos_performance` | 0 | avg=2.17%; win=33.03%; entry_reduce=60.55% | avg>=5.00%, win>=50.00%, entry_reduce<=40.00% |
| `degradation_explained` | 1 | top_taxonomy_problem_count=29; overall_delta=-7.47pp | top taxonomy count >=20 and recent OOS degradation visible |
| `trading_promotion` | 0 | recent OOS performance gate fails | must pass recent OOS, cost/slippage, and live-source gates |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `recent_oos_failure_taxonomy.csv`
- `recent_oos_failure_taxonomy_summary.csv`
- `recent_oos_degradation_matrix.csv`
- `recent_oos_intelligence_source_discrimination.csv`
- `recent_oos_source_findings.csv`
- `task_620_pass_fail_matrix.csv`
- `task_620_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task620_recent_oos_failure_decomposition`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`