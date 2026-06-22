# Task621 Source-Retyped Cost Portfolio Validation

## Decision Summary

- Verdict: `PASS_COST_ACCOUNT_EDGE_FAIL_SOURCE_CERTIFICATION_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Source gate action: `HOLD_UNTIL_SOURCE_CERTIFICATION`
- Best proactive full-panel 50bp account: max 10 -> $4,991.39.
- GPT output is review-only and not source truth.

## Quant Expert Report

### Source Retyping Certification

| Split | Source Bucket | Trades | Avg Return | Win | Entry-Reduce | Certified |
|---|---|---:|---:|---:|---:|---:|
| `train_design` | `aerospace_all` | 74 | 32.10% | 83.78% | 14.86% | 0 |
| `train_design` | `aerospace_no_ceo_ir` | 40 | 27.72% | 92.50% | 7.50% | 0 |
| `train_design` | `aerospace_ceo_ir` | 34 | 37.26% | 73.53% | 23.53% | 0 |
| `validation` | `aerospace_all` | 60 | 0.12% | 45.00% | 50.00% | 0 |
| `validation` | `aerospace_no_ceo_ir` | 27 | 7.63% | 51.85% | 48.15% | 0 |
| `validation` | `aerospace_ceo_ir` | 33 | -6.03% | 39.39% | 51.52% | 0 |
| `recent_oos` | `aerospace_all` | 29 | -18.49% | 0.00% | 100.00% | 0 |
| `recent_oos` | `aerospace_no_ceo_ir` | 18 | -16.97% | 0.00% | 100.00% | 0 |
| `recent_oos` | `aerospace_ceo_ir` | 11 | -20.97% | 0.00% | 100.00% | 0 |

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `proactive_hold_until_source_certified` | 5 | $4,870.51 | 387.05% |
| `full_panel` | `rejected_global_ir_filter` | 5 | $4,275.91 | 327.59% |
| `full_panel` | `turboquant_original` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `proactive_hold_until_source_certified` | 10 | $4,991.39 | 399.14% |
| `full_panel` | `rejected_global_ir_filter` | 10 | $3,155.63 | 215.56% |
| `full_panel` | `turboquant_original` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `proactive_hold_until_source_certified` | 20 | $3,689.79 | 268.98% |
| `full_panel` | `rejected_global_ir_filter` | 20 | $2,618.76 | 161.88% |
| `full_panel` | `turboquant_original` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `proactive_hold_until_source_certified` | 50 | $2,620.92 | 162.09% |
| `full_panel` | `rejected_global_ir_filter` | 50 | $2,140.92 | 114.09% |
| `full_panel` | `turboquant_original` | 50 | $2,423.35 | 142.33% |
| `recent_oos` | `proactive_hold_until_source_certified` | 5 | $1,234.88 | 23.49% |
| `recent_oos` | `rejected_global_ir_filter` | 5 | $966.32 | -3.37% |
| `recent_oos` | `turboquant_original` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `proactive_hold_until_source_certified` | 10 | $1,251.43 | 25.14% |
| `recent_oos` | `rejected_global_ir_filter` | 10 | $927.13 | -7.29% |
| `recent_oos` | `turboquant_original` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `proactive_hold_until_source_certified` | 20 | $1,333.58 | 33.36% |
| `recent_oos` | `rejected_global_ir_filter` | 20 | $1,012.30 | 1.23% |
| `recent_oos` | `turboquant_original` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `proactive_hold_until_source_certified` | 50 | $1,164.40 | 16.44% |
| `recent_oos` | `rejected_global_ir_filter` | 50 | $1,003.60 | 0.36% |
| `recent_oos` | `turboquant_original` | 50 | $1,057.44 | 5.74% |
| `validation` | `proactive_hold_until_source_certified` | 5 | $1,191.96 | 19.20% |
| `validation` | `rejected_global_ir_filter` | 5 | $1,470.47 | 47.05% |
| `validation` | `turboquant_original` | 5 | $1,225.81 | 22.58% |
| `validation` | `proactive_hold_until_source_certified` | 10 | $1,157.40 | 15.74% |
| `validation` | `rejected_global_ir_filter` | 10 | $1,247.82 | 24.78% |
| `validation` | `turboquant_original` | 10 | $1,151.47 | 15.15% |
| `validation` | `proactive_hold_until_source_certified` | 20 | $1,224.51 | 22.45% |
| `validation` | `rejected_global_ir_filter` | 20 | $1,126.12 | 12.61% |
| `validation` | `turboquant_original` | 20 | $1,225.36 | 22.54% |
| `validation` | `proactive_hold_until_source_certified` | 50 | $1,153.48 | 15.35% |
| `validation` | `rejected_global_ir_filter` | 50 | $1,157.82 | 15.78% |
| `validation` | `turboquant_original` | 50 | $1,128.52 | 12.85% |

### GPT Review

- Captured status: `CAPTURED_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT agreed the validation design is directionally firm-grade, but classified the source gate as HOLD_UNTIL_SOURCE_CERTIFICATION rather than a permanent block or simple size-down.

## No-Background Decision-Maker Report

- Cost/account test is good for the proactive risk-off candidate on the full panel.
- Recent OOS is mixed: it wins most capacities, but not max 5.
- Source certification still fails: CEO IR does not rescue recent aerospace/space trades.
- Therefore the right action is hold-until-source-certification, not permanent theme ban and not approval.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `source_retyping_certification` | 0 | recent aerospace CEO-IR and no-CEO-IR buckets both remain negative | a source subtype must rescue recent aerospace before source-certified entry can be restored |
| `full_panel_50bp_account_edge` | 1 | max5 proactive=$4870.51 original=$4158.91; max10 proactive=$4991.39 original=$3229.78; max20 proactive=$3689.79 original=$2924.57; max50 proactive=$2620.92 original=$2423.35 | proactive risk-off beats original TurboQuant at every max position under 50bp |
| `recent_oos_50bp_account_edge` | 1 | max5 proactive=$1234.88 original=$1313.22; max10 proactive=$1251.43 original=$1044.35; max20 proactive=$1333.58 original=$1043.58; max50 proactive=$1164.40 original=$1057.44 | proactive risk-off beats original in at least 3 of 4 recent-OOS capacities under 50bp |
| `negative_control_rejected` | 1 | recent_oos rejected_global_ir_filter final capital below $1000 in 2/4 capacities at 50bp | negative control should fail account viability in at least two recent-OOS capacities |
| `trading_promotion` | 0 | source retyping not certified; mixed recent capacity edge; real capital forbidden | source certification plus cost/account and live-source gates must pass |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_baseline_all_candidate_backtest_panel.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_621_source_retyping_certification_matrix.csv`
- `task_621_cost_portfolio_matrix.csv`
- `task_621_cost_portfolio_winner_matrix.csv`
- `task_621_pass_fail_matrix.csv`
- `task_621_gpt_validation_review_status.csv`
- `task_621_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task621_source_retyped_cost_portfolio_validation`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`