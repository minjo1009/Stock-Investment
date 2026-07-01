# Task630 Block Hold Coverage And Exact Delay Replay

## Decision Summary

- Verdict: `FAIL_EXACT_DELAY_AND_BLOCK_HOLD_COVERAGE_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- GPT/Chrome was used only as review input, not source truth or score input.
- Best exact delay variant: `block_size_exact_delay_60m`
- Exact delay price coverage: 100.00%
- Action counts: BLOCK/HOLD 0, SIZE_DOWN 15, DELAY_ENTRY 24, CONFIRMATION_REQUIRED 1, NO_ACTION 695.

## Quant Expert Report

Task630 treats `BLOCK_HOLD = 0` as a coverage question first. It then tests delayed entries with real intraday prices instead of deleting delayed-entry trades.

### Block Hold Coverage

| Symbol | Direct Neg Registry | Economic Direct Neg Registry | BLOCK/HOLD Trades | SIZE_DOWN | DELAY_ENTRY | CONFIRM | NO_ACTION |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BA` | 1 | 5 | 0 | 0 | 6 | 0 | 35 |
| `RKLB` | 0 | 3 | 0 | 12 | 3 | 0 | 44 |
| `ASTS` | 0 | 2 | 0 | 2 | 6 | 0 | 24 |
| `RTX` | 0 | 7 | 0 | 1 | 9 | 1 | 20 |
| `ALL` | 1 | 17 | 0 | 15 | 24 | 1 | 695 |

### Exact Delay Gross Evaluation

| Variant | Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |
|---|---|---:|---:|---:|---:|
| `original_turboquant` | `full_panel` | 735 | 13.92% | 0.65% | 0.32% |
| `original_turboquant` | `validation` | 262 | 9.63% | 0.63% | 0.34% |
| `original_turboquant` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |
| `block_and_size_down_only` | `full_panel` | 735 | 13.68% | 0.65% | 0.32% |
| `block_and_size_down_only` | `validation` | 262 | 9.48% | 0.63% | 0.34% |
| `block_and_size_down_only` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |
| `block_size_exact_delay_15m` | `full_panel` | 735 | 13.67% | 0.65% | 0.32% |
| `block_size_exact_delay_15m` | `validation` | 262 | 9.48% | 0.63% | 0.34% |
| `block_size_exact_delay_15m` | `recent_oos` | 109 | 2.16% | 0.33% | 0.61% |
| `block_size_exact_delay_30m` | `full_panel` | 735 | 13.67% | 0.65% | 0.32% |
| `block_size_exact_delay_30m` | `validation` | 262 | 9.48% | 0.63% | 0.34% |
| `block_size_exact_delay_30m` | `recent_oos` | 109 | 2.16% | 0.33% | 0.61% |
| `block_size_exact_delay_60m` | `full_panel` | 735 | 13.68% | 0.65% | 0.32% |
| `block_size_exact_delay_60m` | `validation` | 262 | 9.47% | 0.63% | 0.34% |
| `block_size_exact_delay_60m` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `firm_grade_exact_delay_15m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `firm_grade_exact_delay_30m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `firm_grade_exact_delay_60m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `turboquant_original` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `firm_grade_exact_delay_15m` | 10 | $3,225.00 | 222.50% |
| `full_panel` | `firm_grade_exact_delay_30m` | 10 | $3,226.42 | 222.64% |
| `full_panel` | `firm_grade_exact_delay_60m` | 10 | $3,225.89 | 222.59% |
| `full_panel` | `turboquant_original` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `firm_grade_exact_delay_15m` | 20 | $2,940.57 | 194.06% |
| `full_panel` | `firm_grade_exact_delay_30m` | 20 | $2,940.91 | 194.09% |
| `full_panel` | `firm_grade_exact_delay_60m` | 20 | $2,941.02 | 194.10% |
| `full_panel` | `turboquant_original` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `firm_grade_exact_delay_15m` | 50 | $2,410.34 | 141.03% |
| `full_panel` | `firm_grade_exact_delay_30m` | 50 | $2,411.23 | 141.12% |
| `full_panel` | `firm_grade_exact_delay_60m` | 50 | $2,410.66 | 141.07% |
| `full_panel` | `turboquant_original` | 50 | $2,423.35 | 142.33% |
| `recent_oos` | `firm_grade_exact_delay_15m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `firm_grade_exact_delay_30m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `firm_grade_exact_delay_60m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `turboquant_original` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `firm_grade_exact_delay_15m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `firm_grade_exact_delay_30m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `firm_grade_exact_delay_60m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `turboquant_original` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `firm_grade_exact_delay_15m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `firm_grade_exact_delay_30m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `firm_grade_exact_delay_60m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `turboquant_original` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `firm_grade_exact_delay_15m` | 50 | $1,057.38 | 5.74% |
| `recent_oos` | `firm_grade_exact_delay_30m` | 50 | $1,057.40 | 5.74% |
| `recent_oos` | `firm_grade_exact_delay_60m` | 50 | $1,057.44 | 5.74% |
| `recent_oos` | `turboquant_original` | 50 | $1,057.44 | 5.74% |
| `validation` | `firm_grade_exact_delay_15m` | 5 | $1,225.81 | 22.58% |
| `validation` | `firm_grade_exact_delay_30m` | 5 | $1,225.81 | 22.58% |
| `validation` | `firm_grade_exact_delay_60m` | 5 | $1,225.81 | 22.58% |
| `validation` | `turboquant_original` | 5 | $1,225.81 | 22.58% |
| `validation` | `firm_grade_exact_delay_15m` | 10 | $1,151.60 | 15.16% |
| `validation` | `firm_grade_exact_delay_30m` | 10 | $1,151.57 | 15.16% |
| `validation` | `firm_grade_exact_delay_60m` | 10 | $1,151.34 | 15.13% |
| `validation` | `turboquant_original` | 10 | $1,151.47 | 15.15% |
| `validation` | `firm_grade_exact_delay_15m` | 20 | $1,229.48 | 22.95% |
| `validation` | `firm_grade_exact_delay_30m` | 20 | $1,229.46 | 22.95% |
| `validation` | `firm_grade_exact_delay_60m` | 20 | $1,229.35 | 22.93% |
| `validation` | `turboquant_original` | 20 | $1,225.36 | 22.54% |
| `validation` | `firm_grade_exact_delay_15m` | 50 | $1,122.09 | 12.21% |
| `validation` | `firm_grade_exact_delay_30m` | 50 | $1,122.17 | 12.22% |
| `validation` | `firm_grade_exact_delay_60m` | 50 | $1,121.90 | 12.19% |
| `validation` | `turboquant_original` | 50 | $1,128.52 | 12.85% |

## No-Background Decision-Maker Report

- `BLOCK_HOLD`가 0인 건 아직 발동 기회가 거의 없다는 뜻입니다.
- 억지로 BLOCK을 늘리지 않았습니다. 직접/경제 직접 연결을 분리해서 감사했습니다.
- `DELAY_ENTRY`는 이제 실제 분봉 가격으로 15/30/60분 뒤 진입을 재생했습니다.
- 그래도 전략 승인은 아닙니다. 전체 계좌와 커버리지 검증이 더 필요합니다.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `block_hold_coverage_audited` | 1 | registry_direct_negative=1; registry_economic_direct_negative=17; trade_block_hold=0 | coverage is measured before claiming BLOCK_HOLD effectiveness |
| `theme_only_not_actionable` | 1 | theme-only remains NO_ACTION by construction | broad theme words cannot create BLOCK_HOLD |
| `exact_delay_price_coverage` | 1 | delayed_action_price_coverage=100.00% | at least 95% of delayed actions must have real intraday delayed prices |
| `recent_oos_best_delay_improves` | 0 | block_size_exact_delay_60m recent 2.17% vs original 2.17% | best exact delay scenario must not reduce recent OOS gross average |
| `validation_best_delay_not_broken` | 0 | block_size_exact_delay_60m validation 9.47% vs original 9.63% | best exact delay scenario must not reduce validation gross average |
| `recent_oos_50bp_account_edge` | 0 | firm_grade_exact_delay_60m wins=0/4; max5 variant=$1313.22 original=$1313.22; max10 variant=$1044.35 original=$1044.35; max20 variant=$1043.58 original=$1043.58; max50 variant=$1057.44 original=$1057.44 | best exact delay universe beats original in at least 3 of 4 recent-OOS capacities at 50bp |
| `validation_50bp_not_broken` | 0 | firm_grade_exact_delay_60m wins=1/4; max5 variant=$1225.81 original=$1225.81; max10 variant=$1151.34 original=$1151.47; max20 variant=$1229.35 original=$1225.36; max50 variant=$1121.90 original=$1128.52 | best exact delay universe is at least mixed on validation account performance at 50bp |
| `full_panel_50bp_account_edge` | 0 | firm_grade_exact_delay_60m wins=1/4; max5 variant=$4158.91 original=$4158.91; max10 variant=$3225.89 original=$3229.78; max20 variant=$2941.02 original=$2924.57; max50 variant=$2410.66 original=$2423.35 | best exact delay universe is at least mixed on full-panel account performance at 50bp |
| `trading_promotion` | 0 | coverage and exact delay replay diagnostic only | requires source-owned entity expansion, split robustness, and live-source readiness |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`
- `docs/reports/task_627_source_text_theme_linkage_validation/task_627_source_text_linkage_scores.csv`
- `data/raw/us_intraday/`

### Outputs

- `task_630_expanded_event_linkage_registry.csv`
- `task_630_expanded_trade_action_attachment.csv`
- `task_630_intraday_source_coverage.csv`
- `task_630_exact_delayed_entry_replay.csv`
- `task_630_false_block_audit.csv`
- `task_630_policy_variant_evaluation.csv`
- `task_630_cost_account_matrix.csv`
- `task_630_block_hold_coverage_audit.csv`
- `task_630_pass_fail_matrix.csv`
- `task_630_decision.csv`
- `task_630_gpt_review_capture.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task630_block_hold_coverage_and_exact_delay_replay`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
- `python scripts/governance_completion_audit.py`