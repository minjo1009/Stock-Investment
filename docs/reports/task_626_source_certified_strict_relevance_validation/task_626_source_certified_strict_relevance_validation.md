# Task626 Source-Certified Strict Relevance Validation

## Decision Summary

- Verdict: `FAIL_TASK624_AEROSPACE_RULE_UNDER_STRICT_SOURCE_RELEVANCE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Strict aerospace risk-off trades: 1
- Strict recent OOS risk-off removed: 0
- Original recent OOS avg: 2.17%
- Strict relevance recent OOS avg: 2.17%
- Policy-only events are no longer allowed to attach to trades as if they were symbol/theme-specific.

## Quant Expert Report

### Policy Variant Evaluation

| Variant | Split | Trades | Avg Return | Win | Entry-Reduce |
|---|---|---:|---:|---:|---:|
| `original_turboquant` | `full_panel` | 735 | 13.92% | 65.31% | 31.70% |
| `original_turboquant` | `validation` | 262 | 9.63% | 62.98% | 33.97% |
| `original_turboquant` | `recent_oos` | 109 | 2.17% | 33.03% | 60.55% |
| `hold_strict_aerospace_risk_off` | `full_panel` | 734 | 13.98% | 65.40% | 31.61% |
| `hold_strict_aerospace_risk_off` | `validation` | 262 | 9.63% | 62.98% | 33.97% |
| `hold_strict_aerospace_risk_off` | `recent_oos` | 109 | 2.17% | 33.03% | 60.55% |

### Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `policy_only_link_disallowed` | 1 | policy_tags alone are no longer sufficient for trade linkage | macro policy-only events stay context until symbol or theme linkage exists |
| `task624_aerospace_rule_source_certified` | 0 | strict_aerospace_risk_off_trades=1; recent_removed=0 | Task624 aerospace hold must remove certified recent-OOS symbol/theme-linked risk events and improve recent OOS |
| `strict_relevance_recent_improvement` | 0 | recent 2.17% vs original 2.17% | strict source-certified relevance rule must improve recent OOS |
| `trading_promotion` | 0 | strict relevance validation only | needs certified source-rescore and cost/account rerun before strategy use |

### GPT Review

- Captured status: `DERIVED_FROM_TASK625_GPT_PERFECTION_REVIEW`
- Summary: GPT perfection criteria require source integrity and directness; Task626 tests whether Task624 survives stricter source-certified relevance rather than policy-only linkage.

## No-Background Decision-Maker Report

- Task624 looked good because broad policy events were allowed to attach too easily.
- Under strict source-certified relevance, the aerospace risk-off rule has no qualifying trades.
- So Task624 is downgraded from useful candidate to not certified.
- Next work is real symbol/theme-specific source linkage, not trading promotion.

## Artifact Manifest

### Inputs

- `docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_626_strict_trade_event_attachment.csv`
- `task_626_strict_policy_variant_evaluation.csv`
- `task_626_pass_fail_matrix.csv`
- `task_626_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task626_source_certified_strict_relevance_validation`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`