# Task610 Plugin Assisted Intelligence Backtest

## Decision Summary

- Verdict: `PASS_PLUGIN_REVIEW_CANDIDATE_FAIL_RULE_LOCK`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Selected review rule: `vwap_fail_30 & opening_range_reject_120 & volume_decay`
- Key metrics: trigger 6, failure 5, clean false 1, failure rate 83.33%
- Fold result: eligible folds 5, positive tests 1
- What changed: plugin usage is now backtested as an intelligence-review trigger, not a trading rule.
- Next action: connect certified historical event sources before any paper gate simulation.

## Quant Expert Report

### Data Source And Source Readiness

- Input: Task608K 89-entry feature panel plus taxonomy merge.
- Public Equity / Alpaca: single-symbol quote probe observed, but current quote is not used as historical signal.
- Public Equity / Quartr: not called because the required provider-guide resource was unavailable.
- Data Analytics: available for validated report/dashboard artifacts.
- Investment Banking: not used; P2 context-only.

### Exact Join Keys

- Assignment uses only existing live-detectable path features from Task608K.
- No source proximity join was used.
- No news, quote, IR, or GPT text was joined into historical trades.

### Leakage Audit

- Selected rule assignment does not use `entry_reduce_failure_flag`, `net_return_from_entry`, or `failure_type_v2`.
- Labels are evaluation-only.
- GPT output was not used because Chrome review completion was not confirmed.

### Split/OOS Metrics

- Baseline failure rate: 39.33%
- Selected rule failure rate: 83.33%
- Failure-rate lift: 44.01 pct points
- Eligible fold count: 5
- Positive test count: 1

### Failure Decomposition

- Best rule catches a small opening-trap style review bucket.
- It is useful as a plugin-review trigger.
- It is not yet a block/exit/reduce rule.

### Cost/Slippage Stress

- Not run. This task does not change entries, exits, or sizing.

### Remaining Blockers

- Historical Quartr/IR/news windows are not connected.
- Alpaca multi-symbol snapshot timed out.
- Candidate has only six triggers and does not pass rule-lock.

## No-Background Decision-Maker Report

- 사장님, 플러그인을 바로 매매룰에 넣으면 아직 위험합니다.
- 그래도 쓸만한 첫 신호는 나왔습니다.
- 30분 VWAP 실패 + 120분 박스 거부 + 거래량 감소가 같이 나오면 6개 중 5개가 실패였습니다.
- 하지만 표본이 작고, 한 번은 +10.14%짜리 깨끗한 수익 거래도 걸렸습니다.
- 그래서 결론은 `검토 트리거로는 좋다`, `자동 차단룰은 아직 아니다`입니다.

## Plugin Review Status

- GPT attempt: `ATTEMPTED_BUT_NOT_CONFIRMED`
- GPT output used: `0`
- Public Equity used: Alpaca single-symbol quote probe only.
- Data Analytics use: report/dashboard validation surface ready; no rendered artifact claim in this report unless separately rendered.

## Top Candidate Snapshot

| Rule | Trigger | Fail | Clean False | Failure Rate |
|---|---:|---:|---:|---:|
| `vwap_fail_30 & vwap_fail_120 & volume_decay` | 4 | 4 | 0 | 100.00% |
| `vwap_fail_30 & opening_range_reject_120 & volume_decay` | 6 | 5 | 1 | 83.33% |
| `gap_high & sym_vs_theme_pre_neg` | 4 | 3 | 1 | 75.00% |
| `midday & opening_range_reject_120 & gap_high` | 4 | 3 | 1 | 75.00% |
| `midday & gap_neg & sym_vs_theme_pre_neg` | 4 | 3 | 1 | 75.00% |

## Artifact Manifest

### Inputs

- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`
- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`

### Outputs

- `plugin_review_candidate_summary.csv`
- `selected_plugin_review_rule_profile.csv`
- `selected_rule_fold_forward_validation.csv`
- `plugin_source_probe_status.csv`
- `gpt_review_status.csv`
- `task_610_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task610_plugin_assisted_intelligence_backtest`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
