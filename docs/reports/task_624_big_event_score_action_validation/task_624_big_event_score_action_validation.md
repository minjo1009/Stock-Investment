# Task624 Big Event Score Action Validation

## Decision Summary

- Verdict: `PASS_AEROSPACE_SCORE_ACTION_DIAGNOSTIC_REJECT_GLOBAL_RISK_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Original recent OOS avg: 2.17%
- Hold aerospace risk-off recent OOS avg: 9.65%
- Reject global risk-off recent OOS avg: -0.26%
- Global risk-off is rejected as too broad. Aerospace-specific risk-off is diagnostic only.

## Quant Expert Report

### Policy Variant Evaluation

| Variant | Split | Trades | Avg Return | Win | Entry-Reduce |
|---|---|---:|---:|---:|---:|
| `original_turboquant` | `full_panel` | 735 | 13.92% | 65.31% | 31.70% |
| `original_turboquant` | `validation` | 262 | 9.63% | 62.98% | 33.97% |
| `original_turboquant` | `recent_oos` | 109 | 2.17% | 33.03% | 60.55% |
| `reject_global_risk_off` | `full_panel` | 29 | 3.26% | 51.72% | 44.83% |
| `reject_global_risk_off` | `validation` | 8 | 3.50% | 62.50% | 37.50% |
| `reject_global_risk_off` | `recent_oos` | 6 | -0.26% | 33.33% | 66.67% |
| `hold_aerospace_risk_off` | `full_panel` | 575 | 14.58% | 68.17% | 28.70% |
| `hold_aerospace_risk_off` | `validation` | 205 | 12.27% | 67.80% | 29.76% |
| `hold_aerospace_risk_off` | `recent_oos` | 80 | 9.65% | 45.00% | 46.25% |
| `sector_support_watch_only` | `full_panel` | 46 | 15.68% | 84.78% | 15.22% |
| `sector_support_watch_only` | `validation` | 11 | 13.76% | 63.64% | 36.36% |
| `sector_support_watch_only` | `recent_oos` | 0 | 0.00% | 0.00% | 0.00% |

### Score Slice Metrics

| Split | Slice | Trades | Avg Return | Entry-Reduce |
|---|---|---:|---:|---:|
| `full_panel` | `all_trades` | 735 | 13.92% | 31.70% |
| `full_panel` | `global_risk_off` | 706 | 14.36% | 31.16% |
| `full_panel` | `no_global_risk_off` | 29 | 3.26% | 44.83% |
| `full_panel` | `aerospace_risk_off` | 160 | 11.55% | 42.50% |
| `full_panel` | `sector_support_watch` | 46 | 15.68% | 15.22% |
| `full_panel` | `support_entry_candidate` | 0 | 0.00% | 0.00% |
| `validation` | `all_trades` | 262 | 9.63% | 33.97% |
| `validation` | `global_risk_off` | 254 | 9.83% | 33.86% |
| `validation` | `no_global_risk_off` | 8 | 3.50% | 37.50% |
| `validation` | `aerospace_risk_off` | 57 | 0.14% | 49.12% |
| `validation` | `sector_support_watch` | 11 | 13.76% | 36.36% |
| `validation` | `support_entry_candidate` | 0 | 0.00% | 0.00% |
| `recent_oos` | `all_trades` | 109 | 2.17% | 60.55% |
| `recent_oos` | `global_risk_off` | 103 | 2.31% | 60.19% |
| `recent_oos` | `no_global_risk_off` | 6 | -0.26% | 66.67% |
| `recent_oos` | `aerospace_risk_off` | 29 | -18.49% | 100.00% |
| `recent_oos` | `sector_support_watch` | 0 | 0.00% | 0.00% |
| `recent_oos` | `support_entry_candidate` | 0 | 0.00% | 0.00% |

### GPT Review

- Captured status: `CARRIED_FROM_TASK623_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT direction was to score major events but forbid source-presence and broad-event direct entry; Task624 validates the resulting actions before any strategy use.

## No-Background Decision-Maker Report

- Big-event scores are useful only after slicing.
- Global risk-off is too wide and makes the strategy worse.
- Aerospace-specific risk-off explains the recent damage better.
- Still no direct company support exists, so this is not approved for trading.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `global_risk_off_rejected` | 1 | recent -0.26% vs original 2.17%; full 3.26% | global risk-off score is too broad and must not become a trade filter |
| `aerospace_risk_off_diagnostic_improves_recent` | 1 | recent 9.65% vs original 2.17%; validation 12.27% | aerospace-specific risk-off hold improves recent OOS and does not break validation |
| `company_direct_support_still_missing` | 1 | support_entry_candidate_count=0 | no entry restoration until company-direct support exists |
| `trading_promotion` | 0 | diagnostic action validation only | needs full text source certification plus cost/account rerun before strategy use |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`
- `docs/reports/task_623_big_event_interpretation_scoring_sidecar/event_interpretation_scores.csv`

### Outputs

- `task_624_trade_event_score_attachment.csv`
- `task_624_score_action_slice_metrics.csv`
- `task_624_policy_variant_evaluation.csv`
- `task_624_pass_fail_matrix.csv`
- `task_624_gpt_score_action_validation_review_status.csv`
- `task_624_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task624_big_event_score_action_validation`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`