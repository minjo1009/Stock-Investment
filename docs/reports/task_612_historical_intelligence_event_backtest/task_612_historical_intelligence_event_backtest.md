# Task612 Historical Intelligence Event Backtest

## Decision Summary

- Verdict: `FAIL_OFFICIAL_EVENT_OVERLAY_KEEP_TASK610_REVIEW_TRIGGER`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Entries tested: 89
- Failures tested: 35
- Baseline failure rate: 39.33%
- Official source lanes active: 2
- Source lanes pending: 4
- Best event scenario: `earnings_proxy_sec_pre14d` (13 triggers, 6 failures, 46.15% failure rate, 6.83pp lift)
- What changed: SEC company submissions and Federal Reserve FOMC calendar are now connected to the Task608K entry panel without post-entry same-day filing leakage.
- Next action: certify the missing Trump/person/war/institution/transcript lanes before any event overlay can become more than diagnostic review.

## Quant Expert Report

### Data Source And Source Readiness

- SEC company submissions: 1869 relevant events from official SEC submission JSON.
- Federal Reserve FOMC calendar: 44 scheduled events from the official Fed calendar.
- Pending lanes are not approximated: Trump and major-person statements, war/geopolitical events, institution reports and investment actions, CEO/IR transcripts and presentations.
- GPT/Chrome output is review-only and has `gpt_output_used_as_source_flag=0`.

### Exact Join Keys

- Company event join: `symbol` plus `event_date <= trade_date`.
- Same-day SEC leakage guard: same-day filings count only when `acceptance_ts_utc <= entry_ts_utc`.
- Fed event join: scheduled `event_date` within calendar windows around `trade_date`; no policy outcome text is used.
- Lifecycle join remains exact `lifecycle_id`; no symbol/date/price/time proximity fallback is used for lifecycle labels.

### Leakage Audit

- Labels/outcomes are evaluation-only.
- SEC post-entry same-day filings are excluded.
- FOMC is used as known scheduled calendar risk, not statement interpretation.
- Missing source lanes are reported as source gaps, not filled with guesses.

### Split/OOS Metrics

- This is a first diagnostic overlay, not a rule-lock.
- Fold-forward promotion remains blocked until more source lanes are certified and event sample sizes are larger.

### Failure Decomposition

| scenario | trigger_count | failure_count | clean_false_count | failure_rate | failure_rate_lift_pct_point | clean_false_ratio | size_down_50_avg_return_delta_pct_point |
| --- | --- | --- | --- | --- | --- | --- | --- |
| task610_exact_review_trigger | 6 | 5 | 1 | 0.8333 | 44.0075 | 0.1667 | 0.4638 |
| earnings_proxy_sec_pre14d | 13 | 6 | 7 | 0.4615 | 6.8280 | 0.5385 | -0.3152 |
| task610_or_event_density_ge2 | 22 | 9 | 13 | 0.4091 | 1.5832 | 0.5909 | -0.4801 |
| fomc_calendar_near_3d | 36 | 12 | 24 | 0.3333 | -5.9925 | 0.6667 | -3.4221 |
| turboquant_attention_event_gate | 15 | 5 | 10 | 0.3333 | -5.9925 | 0.6667 | -1.5976 |
| capital_market_sec_pre30d | 6 | 2 | 4 | 0.3333 | -5.9925 | 0.6667 | -0.3624 |

### Cost/Slippage Stress

- No new trade execution rule is promoted.
- The 50% size-down delta is reported only as a diagnostic stress proxy.

### Remaining Blockers

| source_lane | coverage_status | backtest_use |
| --- | --- | --- |
| sec_company_submissions | ACTIVE_OFFICIAL | company filing event flags only |
| fed_fomc_calendar | ACTIVE_OFFICIAL | scheduled macro event risk flag only |
| trump_and_major_person_statements | SOURCE_LANE_PENDING | not used; no approximation |
| war_geopolitical_events | SOURCE_LANE_PENDING | not used; no approximation |
| institution_reports_and_investment_actions | SOURCE_LANE_PENDING | not used; no approximation |
| ceo_ir_transcripts_and_presentations | SOURCE_LANE_PENDING | not used until transcript source is certified |

## No-Background Decision-Maker Report

- 한 줄 결론: 공식 이벤트를 붙이는 길은 맞지만, 아직 돈 넣을 규칙은 아닙니다.
- SEC/Fed만 붙였고, 나머지 큰 뉴스 줄은 아직 빈칸입니다.
- 가장 좋은 표식도 지금은 위험 알림 수준입니다.
- 그래서 전략 상태는 그대로 `NOT_ACCEPTED` 입니다.
- 다음은 Trump/전쟁/기관/CEO 발언 줄을 공식 출처로 붙이는 일입니다.

## Artifact Manifest

### Inputs

- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`
- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`
- `data/raw/fundamental/sec_companyfacts/company_tickers.json`
- `data/raw/sec_submissions_task612/`
- `data/raw/fed_fomc_task612/fomccalendars.html`

### Outputs

- `historical_intelligence_events.csv`
- `fed_fomc_events.csv`
- `source_lane_coverage.csv`
- `entry_event_linkage.csv`
- `event_overlay_scenario_summary.csv`
- `task_612_pass_fail_matrix.csv`
- `gpt_historical_event_review_pack.csv`
- `task_612_decision.csv`
- `task_612_historical_intelligence_event_backtest.md`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task612_historical_intelligence_event_backtest`
- `python scripts\task_registry_validate.py`
- `python scripts\operating_closeout_validate.py`
- `python scripts\governance_completion_audit.py`
