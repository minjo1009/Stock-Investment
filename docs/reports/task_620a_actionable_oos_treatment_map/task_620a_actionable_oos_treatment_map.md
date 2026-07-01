# Task620A Actionable OOS Treatment Map

## Decision Summary

- Verdict: `LOCK_ACTIONABLE_OOS_TREATMENT_MAP_TEST_AEROSPACE_BLOCK_FIRST`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- First treatment to test: `block_theme_aerospace_defense` as `ENTRY_BLOCK`.
- GPT output is review-only and not source truth.

## Quant Expert Report

### Failure Bucket Treatment Map

| Bucket | Treatment | Problems | Avg Return | Entry-Reduce | Next Task |
|---|---|---:|---:|---:|---|
| `theme_specific_collapse_aerospace_defense` | `ENTRY_BLOCK` | 29 | -18.49% | 100.00% | `Task620B_theme_block_validation` |
| `trailing_stop_path_failure` | `EXIT_TREATMENT` | 14 | -10.62% | 85.71% | `Task621_exit_path_research` |
| `broad_event_support_without_recent_ir_proxy` | `SOURCE_RETYPING` | 11 | -9.65% | 90.91% | `Task620C_source_retyping` |
| `late_midday_continuation_decay` | `DELAY_ENTRY` | 9 | -9.65% | 88.89% | `Task620D_delay_entry_validation` |
| `residual_recent_oos_problem` | `DO_NOT_USE_YET` | 8 | -5.26% | 62.50% | `Task620F_residual_taxonomy` |
| `overextended_persistent_theme_leader` | `SIZE_DOWN` | 2 | -11.35% | 100.00% | `Task620E_size_down_validation` |
| `clean_recent_oos_winner` | `KEEP` | 0 | 32.75% | 0.00% | `Task620B_theme_block_validation` |

### Actionable Trigger Effects

| Treatment | Split | Trigger Trades | Trigger Avg | Kept Avg | Kept Entry-Reduce | Kept Delta |
|---|---|---:|---:|---:|---:|---:|
| `block_aerospace_persistent_leader` | `recent_oos` | 28 | -18.95% | 9.47% | 46.91% | 7.30pp |
| `block_aerospace_persistent_leader` | `validation` | 56 | 0.88% | 12.01% | 29.61% | 2.38pp |
| `block_aerospace_theme_ret20_gt15` | `recent_oos` | 25 | -18.95% | 8.45% | 48.81% | 6.29pp |
| `block_aerospace_theme_ret20_gt15` | `validation` | 47 | -1.21% | 12.00% | 29.30% | 2.37pp |
| `block_theme_aerospace_defense` | `recent_oos` | 29 | -18.49% | 9.65% | 46.25% | 7.49pp |
| `block_theme_aerospace_defense` | `validation` | 60 | 0.12% | 12.46% | 29.21% | 2.83pp |
| `delay_or_block_midday_theme_ret20_gt15` | `recent_oos` | 15 | -20.50% | 5.78% | 54.26% | 3.62pp |
| `delay_or_block_midday_theme_ret20_gt15` | `validation` | 21 | 2.90% | 10.22% | 32.78% | 0.59pp |
| `size_down_persistent_theme_ret20_gt15` | `recent_oos` | 28 | -17.56% | 8.99% | 48.15% | 6.82pp |
| `size_down_persistent_theme_ret20_gt15` | `validation` | 54 | 0.78% | 11.93% | 29.81% | 2.30pp |
| `source_retype_broad_event_without_recent_ir` | `recent_oos` | 71 | 2.72% | 1.13% | 52.63% | -1.04pp |
| `source_retype_broad_event_without_recent_ir` | `validation` | 144 | 11.68% | 7.13% | 34.75% | -2.50pp |
| `watch_theme_ret20_gt20` | `recent_oos` | 24 | -17.14% | 7.62% | 50.59% | 5.45pp |
| `watch_theme_ret20_gt20` | `validation` | 35 | -2.55% | 11.51% | 30.40% | 1.88pp |

### GPT Review

- Captured status: `CAPTURED_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT agreed Task620 must move from bad-OOS confirmation to actionable treatment mapping: entry block aerospace first, source retyping second, delay midday third, exit research for trailing stop.

## No-Background Decision-Maker Report

- The point is no longer proving recent OOS was bad.
- The first practical treatment is to test whether aerospace/defense-space should be blocked at entry.
- Broad news/event flags need retyping because they are too wide to separate winners from failures.
- Trailing-stop failures belong to exit research, not entry blocking.
- Midday hot-theme continuation should be tested with delayed entry, not immediately deleted.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `gpt_treatment_review_captured` | 1 | CAPTURED_CHROME_CHATGPT_PROJECT_TAB | Chrome ChatGPT treatment review captured as non-source interpretation |
| `aerospace_entry_block_candidate` | 1 | recent_kept_avg=9.65%; recent_kept_er=46.25%; validation_kept_avg=12.46% | recent kept avg>=5%, recent kept entry_reduce<=50%, validation kept avg>=base |
| `bucket_treatment_classes_complete` | 1 | DELAY_ENTRY,DO_NOT_USE_YET,ENTRY_BLOCK,EXIT_TREATMENT,KEEP,SIZE_DOWN,SOURCE_RETYPING | failure buckets mapped to action classes |
| `trading_promotion` | 0 | actionable map only; no rule accepted yet | treatment rules must pass separate validation before promotion |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`
- `docs/reports/task_620_recent_oos_failure_decomposition/recent_oos_failure_taxonomy_summary.csv`

### Outputs

- `task_620a_actionable_trigger_effects.csv`
- `task_620a_failure_bucket_treatment_map.csv`
- `task_620a_gpt_treatment_review_status.csv`
- `task_620a_pass_fail_matrix.csv`
- `task_620a_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task620a_actionable_oos_treatment_map`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`