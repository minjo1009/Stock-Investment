# Task613 Intelligence Source Lane Design

## Decision Summary

- Verdict: `DESIGN_SOURCE_LANE_STACK_BEFORE_BACKTEST`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: Task612 pending lanes are split into source lanes with priority, source hierarchy, allowed features, and leakage guards.
- Next action: implement P0 source certification for political statements, war/geopolitical events, and institutional investment actions before the next historical event backtest.

## Quant Expert Report

### Data Source And Source Readiness

- `trump_major_person_political_statements`: P0. Start with White House official pages and archived official Trump White House pages.
- `war_geopolitical_conflict_events`: P0. Start with OFAC, Defense, and State official releases; use ACLED/GDELT only as structured event supplements after source audit.
- `institution_investment_actions`: P0. Start with SEC 13F and 13D/G. Treat 13F as delayed disclosure, not real-time buying.
- `ceo_ir_transcripts_and_presentations`: P1. Start with company IR pages, SEC 8-K exhibits, and timestamped earnings release material.
- `analyst_reports_and_rating_actions`: P2. Use only if licensed metadata or public timestamped rating action source exists.

### Exact Join Keys

- Political and CEO/IR statement join: `event_timestamp_utc <= entry_ts_utc`, plus direct company/sector/theme tag.
- War/geopolitical join: `event_date/event_timestamp`, affected country, sanction/export-control program, commodity/supply-chain/theme tag.
- Institutional join: SEC accepted timestamp plus CIK/CUSIP/ticker mapping.
- No symbol/date/price/time proximity fallback is allowed for lifecycle outcomes.

### Leakage Audit

- Same-day statements count only if published before entry time.
- Earnings calls after close cannot explain same-day entry.
- 13F holdings must be treated as disclosure-lagged, because the filing can arrive up to 45 days after quarter end.
- GPT can classify narrative after source text exists, but cannot create facts, dates, speaker text, target prices, ratings, or reports.
- Missing source lanes remain `SOURCE_LANE_PENDING`; they are not filled with guessed news.

### Split/OOS Metrics

- This task is design-only.
- The next backtest must split pure event features from Task610 reference triggers.
- Diagnostic pass should require at least 5 triggers, at least +15pp lift over the 39.33% Task612 baseline, clean false ratio no worse than 60%, and fold-forward direction support.

### Failure Decomposition

- Task612 showed SEC/Fed-only event features were too weak.
- Best pure event feature was `earnings_proxy_sec_pre14d`: 13 triggers, 6 failures, 46.15% failure rate, +6.83pp lift.
- Therefore the missing lanes should be added as source-certified risk context first, not as a trading rule.

### Remaining Blockers

- Political statement timestamp capture is not implemented.
- War/geopolitical event source certification is not implemented.
- 13F/13D/G ownership parser is not implemented.
- CEO/IR transcript provider is not certified.
- Analyst reports remain blocked unless a licensed or public timestamped source exists.

## GPT Review Notes

- Chrome ChatGPT in the `1. 코딩/투자` project was asked for source-lane design review.
- GPT output is review-only and `gpt_output_used_as_source_flag=0`.
- GPT agreed with the main guardrail: no timestamped original source, no feature.
- GPT suggested the same broad features: political statement proximity, policy risk statement, sector/company direct mention, statement density, conflict escalation, sanctions/export-control risk, and source-missing treatment.

## No-Background Decision-Maker Report

- 한 줄 결론: 정치/전쟁/기관/CEO 발언은 쓸 수 있지만, 먼저 출처 줄을 깔아야 합니다.
- 제일 먼저 할 일은 Trump/정치 발언, 전쟁/제재, 기관 수급 공시입니다.
- 13F는 실시간 매수 신호가 아닙니다. 늦게 공개되는 보유 내역입니다.
- CEO 발언은 원문과 공개 시간이 있어야 합니다.
- GPT는 정리 도우미일 뿐이고, 사실 출처가 아닙니다.

## Artifact Manifest

### Inputs

- `docs/reports/task_612_historical_intelligence_event_backtest/task_612_decision.csv`
- `docs/reports/task_612_historical_intelligence_event_backtest/source_lane_coverage.csv`
- Chrome ChatGPT review prompt in `1. 코딩/투자`
- Official source research links listed below

### Official Source Pointers

- `https://www.whitehouse.gov/remarks/`
- `https://trumpwhitehouse.archives.gov/remarks/`
- `https://www.sec.gov/edgar/sec-api-documentation`
- `https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f`
- `https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-sections-13d-13g-regulation-13d-g-beneficial-ownership-reporting`
- `https://ofac.treasury.gov/sanctions-list-service`
- `https://www.defense.gov/Newsroom/releases/index.html/`
- `https://acleddata.com/acled-api-documentation`
- `https://docs.gdeltcloud.com/API_DOCUMENTATION_GUIDE`

### Outputs

- `source_lane_priority_matrix.csv`
- `task_613_intelligence_source_lane_design.md`
- `artifact_manifest.csv`

### Validation Commands

- `python scripts\task_registry_validate.py`
- `python scripts\operating_closeout_validate.py`
- `python scripts\governance_completion_audit.py`
