# Task627 Source Text Theme Linkage Validation

## Decision Summary

- Verdict: `PASS_SOURCE_TEXT_AEROSPACE_RISK_DIAGNOSTIC_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Certified source-text aerospace risk events: 42
- Recent OOS: 2.17% -> 4.67%
- Validation: 9.63% -> 10.19%

## Quant Expert Report

### Policy Variant Evaluation

| Variant | Split | Trades | Avg Return | Win | Entry-Reduce |
|---|---|---:|---:|---:|---:|
| `original_turboquant` | `full_panel` | 735 | 13.92% | 65.31% | 31.70% |
| `original_turboquant` | `validation` | 262 | 9.63% | 62.98% | 33.97% |
| `original_turboquant` | `recent_oos` | 109 | 2.17% | 33.03% | 60.55% |
| `hold_source_text_aerospace_risk` | `full_panel` | 657 | 12.97% | 65.91% | 31.35% |
| `hold_source_text_aerospace_risk` | `validation` | 237 | 10.19% | 64.14% | 33.76% |
| `hold_source_text_aerospace_risk` | `recent_oos` | 98 | 4.67% | 36.73% | 56.12% |

### Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `source_text_linkage_exists` | 1 | source_text_aerospace_risk_events=42 | certified official text must contain both aerospace/theme and risk terms |
| `recent_oos_improves` | 1 | removed_recent=11; recent 4.67% vs original 2.17% | source-text aerospace risk hold must improve recent OOS |
| `validation_not_broken` | 1 | validation 10.19% vs original 9.63% | source-text aerospace risk hold must not reduce validation average |
| `trading_promotion` | 0 | source-text linkage diagnostic only | needs cost/account and parameter/split robustness before strategy use |

## No-Background Decision-Maker Report

- Task626 showed that policy tags were too broad.
- Task627 uses official source text itself to find aerospace/defense risk linkage.
- This gives a smaller but more honest recent OOS improvement.
- It is still diagnostic only until cost/account validation passes.

## Artifact Manifest

### Inputs

- `docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_627_source_text_linkage_scores.csv`
- `task_627_trade_text_linkage_attachment.csv`
- `task_627_policy_variant_evaluation.csv`
- `task_627_pass_fail_matrix.csv`
- `task_627_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task627_source_text_theme_linkage_validation`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`