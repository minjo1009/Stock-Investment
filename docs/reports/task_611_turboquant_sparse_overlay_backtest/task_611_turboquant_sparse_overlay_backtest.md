# Task611 TurboQuant Sparse Overlay Backtest

## Decision Summary

- Verdict: `PASS_TURBOQUANT_OS_FAIL_TRADING_OVERLAY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Exact review trigger: trigger 6, failure rate 83.33%, clean false ratio 16.67%
- What changed: GPT-reviewed TurboQuant idea is now tested as a sparse overlay OS, not a trading rule.
- Next action: connect certified historical event summary cache and rerun with actual intelligence events.

## Quant Expert Report

### Data Source And Source Readiness

- Input: Task608K 89-entry feature panel plus taxonomy merge.
- GPT review: captured in Chrome ChatGPT coding/investment project; used as review only, not source.
- Plugin source status: live source evidence still uncertified for historical backtest.

### Exact Join Keys

- No news, IR, or quote event was joined into historical trades.
- All assignment uses existing Task608K path features and exact lifecycle rows.
- Future Task612 must join by event id, source id, captured timestamp, and evidence hash.

### Leakage Audit

- Turbo score assignment does not use `entry_reduce_failure_flag`, `net_return_from_entry`, or `failure_type_v2`.
- Labels remain evaluation-only.
- GPT output is not used as a fact source.

### Split/OOS Metrics

- Exact review trigger failure rate: 83.33%
- Exact review trigger clean false ratio: 16.67%
- Exact skip delta: 1.67 pct points
- Exact 50% size-down delta: 0.46 pct points
- Fold eligible count: 5
- Positive test count: 1

### Failure Decomposition

- Exact Task610 trigger is a strong review candidate but sample is too small.
- Broad TurboQuant score thresholds catch too many clean winners and do not improve average returns.
- The correct use is sparse review and source capture, not automatic skip or size-down.

### Cost/Slippage Stress

- Cost/slippage not run because no live entry/exit/sizing rule is accepted.
- Latency/operability is reflected through plugin operability failure.

### Remaining Blockers

- Historical intelligence event cache is not connected.
- Quartr source sequence remains blocked.
- Alpaca multi-symbol snapshot timeout is unresolved.
- Turbo overlay fails trading-rule promotion.

## No-Background Decision-Maker Report

- 사장님, 터보퀀트 방향은 맞습니다.
- 다만 뜻은 'GPT가 대신 매매'가 아닙니다.
- 기본 퀀트는 가볍게 계속 돌리고, 위험한 구간에서만 GPT/뉴스/IR을 부르는 구조입니다.
- 이번 백테스트에서 자동 skip/size-down은 아직 돈을 더 벌게 만들지 못했습니다.
- 그래서 결론은 `운영체계는 통과`, `매매룰은 탈락`입니다.

## GPT Review Summary

- Do not rule-lock Task610; use sparse plugin overlay and TurboQuant-style lightweight gates.
- Plugin calls should happen only on high-risk or ambiguous zones; LLM is a summarizer and risk explainer.
- Pass/fail should require trigger count >= 12, failure lift >= 25pp, clean false ratio <= 25%, and fold stability.

## Top Turbo Score Scenarios

| Scenario | Trigger | Fail | Clean | Failure Rate | Size-down Delta |
|---|---:|---:|---:|---:|---:|
| `turbo_score_ge_0.25` | 50 | 22 | 28 | 44.00% | -2.29pp |
| `turbo_score_ge_0.60` | 12 | 5 | 7 | 41.67% | -0.93pp |
| `turbo_score_ge_0.30` | 46 | 19 | 27 | 41.30% | -2.57pp |
| `turbo_score_ge_0.35` | 44 | 17 | 27 | 38.64% | -2.72pp |
| `turbo_score_ge_0.40` | 32 | 12 | 20 | 37.50% | -2.27pp |

## TurboQuant Architecture

| Layer | Status | Owner |
|---|---|---|
| `G0 data_validity_gate` | `DESIGNED_NOT_FULLY_CONNECTED` | Data & Market Microstructure |
| `G1 price_path_gate` | `IMPLEMENTED_DIAGNOSTIC` | Intraday Continuation Research |
| `G2 sparse_plugin_need_gate` | `IMPLEMENTED_DIAGNOSTIC_NO_LIVE_CALL` | Research Governance |
| `G3 plugin_health_cache` | `DESIGNED_NOT_FULLY_CONNECTED` | Data & Market Microstructure |
| `G4 summary_cache` | `DESIGNED_NOT_FULLY_CONNECTED` | Backtest & Simulation Infra |
| `G5 promotion_gate` | `IMPLEMENTED_DIAGNOSTIC` | Research Governance |

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `exact_rule_review_candidate` | 1 | triggers=6; lift=44.01pp; clean_false_ratio=0.17 | triggers>=5 for review candidate; lift>=25pp; clean_false_ratio<=0.25 |
| `turbo_score_trading_overlay` | 0 | best=turbo_score_ge_0.25; triggers=50; lift=4.67pp; clean_false_ratio=0.56; sizedown_delta=-2.29pp | triggers>=12; lift>=25pp; clean_false_ratio<=0.25; sizedown_delta>=1.0pp |
| `fold_stability` | 0 | eligible_folds=5; positive_folds=1; positive_share=0.20 | eligible_folds>=10 and positive_share>=0.60 |
| `plugin_operability` | 0 | Quartr not called due provider-guide resource; Alpaca multi-symbol snapshot timeout; fallback modeled only | certified source sequence and timeout fallback coverage 100% |

## Artifact Manifest

### Inputs

- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`
- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`
- Chrome ChatGPT coding/investment review text, used as review only.

### Outputs

- `turboquant_entry_score_panel.csv`
- `turboquant_overlay_scenario_summary.csv`
- `task610_exact_rule_turboquant_profile.csv`
- `task610_exact_rule_fold_forward.csv`
- `gpt_turboquant_review_pack.csv`
- `turboquant_system_architecture.csv`
- `task_611_pass_fail_matrix.csv`
- `task_611_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task611_turboquant_sparse_overlay_backtest`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
