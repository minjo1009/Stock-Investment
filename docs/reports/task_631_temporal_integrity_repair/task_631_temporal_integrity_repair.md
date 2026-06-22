# Task631 Temporal Integrity Repair

## Decision Summary

- Verdict: `FAIL_TEMPORAL_STRICT_ACTION_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- GPT/Chrome was used only as review input, not source truth or score input.
- Date-only original action rows: 23
- Strong date-only actions after gate: 0
- Temporal actions: BLOCK/HOLD 0, SIZE_DOWN 0, DELAY_ENTRY 5, SOURCE_TIME_GAP 23, STALE_EVENT_GAP 12.

## Quant Expert Report

Task631 turns time alignment into a hard gate. Date-only events cannot create `BLOCK_HOLD`, `SIZE_DOWN`, or `DELAY_ENTRY`. Timestamped events must be tradable before entry and fresh enough for action.

### Source Time Audit

| Bucket | Rows | Date-only | Time Certified | Fresh Eligible | Source Time Gap | Stale Gap | Strong Date-only Original | Future Timestamp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ALL_ACTION_ROWS` | 40 | 23 | 17 | 5 | 23 | 12 | 22 | 0 |
| `CONFIRMATION_REQUIRED` | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| `DELAY_ENTRY` | 24 | 8 | 16 | 5 | 8 | 11 | 8 | 0 |
| `SIZE_DOWN` | 15 | 14 | 1 | 0 | 14 | 1 | 14 | 0 |

### Gross Evaluation

| Variant | Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |
|---|---|---:|---:|---:|---:|
| `original_turboquant` | `full_panel` | 735 | 13.92% | 0.65% | 0.32% |
| `original_turboquant` | `validation` | 262 | 9.63% | 0.63% | 0.34% |
| `original_turboquant` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |
| `temporal_strict_exact_delay_15m` | `full_panel` | 735 | 13.91% | 0.65% | 0.32% |
| `temporal_strict_exact_delay_15m` | `validation` | 262 | 9.63% | 0.63% | 0.34% |
| `temporal_strict_exact_delay_15m` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |
| `temporal_strict_exact_delay_30m` | `full_panel` | 735 | 13.90% | 0.65% | 0.32% |
| `temporal_strict_exact_delay_30m` | `validation` | 262 | 9.63% | 0.63% | 0.34% |
| `temporal_strict_exact_delay_30m` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |
| `temporal_strict_exact_delay_60m` | `full_panel` | 735 | 13.91% | 0.65% | 0.32% |
| `temporal_strict_exact_delay_60m` | `validation` | 262 | 9.63% | 0.63% | 0.34% |
| `temporal_strict_exact_delay_60m` | `recent_oos` | 109 | 2.17% | 0.33% | 0.61% |

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `temporal_strict_exact_delay_15m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `temporal_strict_exact_delay_30m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `temporal_strict_exact_delay_60m` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `turboquant_original` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `temporal_strict_exact_delay_15m` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `temporal_strict_exact_delay_30m` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `temporal_strict_exact_delay_60m` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `turboquant_original` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `temporal_strict_exact_delay_15m` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `temporal_strict_exact_delay_30m` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `temporal_strict_exact_delay_60m` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `turboquant_original` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `temporal_strict_exact_delay_15m` | 50 | $2,422.26 | 142.23% |
| `full_panel` | `temporal_strict_exact_delay_30m` | 50 | $2,422.65 | 142.27% |
| `full_panel` | `temporal_strict_exact_delay_60m` | 50 | $2,422.03 | 142.20% |
| `full_panel` | `turboquant_original` | 50 | $2,423.35 | 142.33% |
| `recent_oos` | `temporal_strict_exact_delay_15m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `temporal_strict_exact_delay_30m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `temporal_strict_exact_delay_60m` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `turboquant_original` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `temporal_strict_exact_delay_15m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `temporal_strict_exact_delay_30m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `temporal_strict_exact_delay_60m` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `turboquant_original` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `temporal_strict_exact_delay_15m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `temporal_strict_exact_delay_30m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `temporal_strict_exact_delay_60m` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `turboquant_original` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `temporal_strict_exact_delay_15m` | 50 | $1,057.44 | 5.74% |
| `recent_oos` | `temporal_strict_exact_delay_30m` | 50 | $1,057.44 | 5.74% |
| `recent_oos` | `temporal_strict_exact_delay_60m` | 50 | $1,057.44 | 5.74% |
| `recent_oos` | `turboquant_original` | 50 | $1,057.44 | 5.74% |
| `validation` | `temporal_strict_exact_delay_15m` | 5 | $1,225.81 | 22.58% |
| `validation` | `temporal_strict_exact_delay_30m` | 5 | $1,225.81 | 22.58% |
| `validation` | `temporal_strict_exact_delay_60m` | 5 | $1,225.81 | 22.58% |
| `validation` | `turboquant_original` | 5 | $1,225.81 | 22.58% |
| `validation` | `temporal_strict_exact_delay_15m` | 10 | $1,151.47 | 15.15% |
| `validation` | `temporal_strict_exact_delay_30m` | 10 | $1,151.47 | 15.15% |
| `validation` | `temporal_strict_exact_delay_60m` | 10 | $1,151.47 | 15.15% |
| `validation` | `turboquant_original` | 10 | $1,151.47 | 15.15% |
| `validation` | `temporal_strict_exact_delay_15m` | 20 | $1,225.36 | 22.54% |
| `validation` | `temporal_strict_exact_delay_30m` | 20 | $1,225.36 | 22.54% |
| `validation` | `temporal_strict_exact_delay_60m` | 20 | $1,225.36 | 22.54% |
| `validation` | `turboquant_original` | 20 | $1,225.36 | 22.54% |
| `validation` | `temporal_strict_exact_delay_15m` | 50 | $1,128.52 | 12.85% |
| `validation` | `temporal_strict_exact_delay_30m` | 50 | $1,128.52 | 12.85% |
| `validation` | `temporal_strict_exact_delay_60m` | 50 | $1,128.52 | 12.85% |
| `validation` | `turboquant_original` | 50 | $1,128.52 | 12.85% |

## No-Background Decision-Maker Report

- 사장님 지적대로 시간축을 고쳤습니다.
- 날짜만 있는 뉴스는 강한 매매 액션을 만들 수 없습니다.
- 7일 창으로 붙은 이벤트는 `SOURCE_TIME_GAP` 또는 `STALE_EVENT_GAP`으로 빠집니다.
- 이 수정은 성과를 예쁘게 만들기 위한 게 아니라, 틀린 시간 연결을 막기 위한 겁니다.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `date_only_strong_action_blocked` | 1 | strong_date_only_after_gate=0; original_action_date_only=23 | date-only events cannot create BLOCK_HOLD, SIZE_DOWN, or DELAY_ENTRY |
| `future_event_action_blocked` | 1 | future_strong_actions_after_gate=0 | tradable_after_ts must be before or equal to entry_ts |
| `stale_strong_action_blocked` | 1 | stale_strong_actions_after_gate=0 | strong actions require timestamp-certified fresh events |
| `source_time_gap_reported` | 1 | source_time_gap_rows=23 | missing/date-only time gaps must be reported rather than treated as positive or negative |
| `recent_oos_not_worse_gross` | 1 | temporal_strict_exact_delay_15m recent 2.17% vs original 2.17% | temporal strict policy should not reduce recent OOS gross average |
| `validation_not_broken_gross` | 1 | temporal_strict_exact_delay_15m validation 9.63% vs original 9.63% | temporal strict policy should not reduce validation gross average |
| `recent_oos_50bp_account_edge` | 0 | temporal_strict_exact_delay_15m wins=0/4; max5 variant=$1313.22 original=$1313.22; max10 variant=$1044.35 original=$1044.35; max20 variant=$1043.58 original=$1043.58; max50 variant=$1057.44 original=$1057.44 | temporal strict policy beats original in at least 3 of 4 recent-OOS capacities at 50bp |
| `validation_50bp_not_broken` | 0 | temporal_strict_exact_delay_15m wins=0/4; max5 variant=$1225.81 original=$1225.81; max10 variant=$1151.47 original=$1151.47; max20 variant=$1225.36 original=$1225.36; max50 variant=$1128.52 original=$1128.52 | temporal strict policy is at least mixed on validation account performance at 50bp |
| `full_panel_50bp_account_edge` | 0 | temporal_strict_exact_delay_15m wins=0/4; max5 variant=$4158.91 original=$4158.91; max10 variant=$3229.78 original=$3229.78; max20 variant=$2924.57 original=$2924.57; max50 variant=$2422.26 original=$2423.35 | temporal strict policy is at least mixed on full-panel account performance at 50bp |
| `trading_promotion` | 0 | temporal repair diagnostic only | requires live received_at/published_at capture and confirmation-gated entry before promotion |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`
- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_expanded_trade_action_attachment.csv`
- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_expanded_event_linkage_registry.csv`
- `docs/reports/task_630_block_hold_coverage_and_exact_delay_replay/task_630_exact_delayed_entry_replay.csv`

### Outputs

- `task_631_temporal_action_attachment.csv`
- `task_631_policy_variant_evaluation.csv`
- `task_631_cost_account_matrix.csv`
- `task_631_source_time_audit.csv`
- `task_631_pass_fail_matrix.csv`
- `task_631_decision.csv`
- `task_631_gpt_review_capture.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task631_temporal_integrity_repair`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
- `python scripts/governance_completion_audit.py`