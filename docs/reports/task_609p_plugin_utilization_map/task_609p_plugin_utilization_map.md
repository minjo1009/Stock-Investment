# Task609P Plugin Utilization Map

## Decision Summary

- Verdict: `USE_PUBLIC_EQUITY_AND_DATA_ANALYTICS_AS_P0_IB_AS_P2_CONTEXT`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- P0 plugins: Public Equity Investing, Data Analytics
- Investment Banking: P2 context-only, not a daily trading workflow.
- Next action: use Public Equity routes for source capture and Data Analytics for replay/report validation.

## Quant Expert Report

### Plugin Roles

- Public Equity Investing owns listed-equity research context, catalysts, earnings, IR documents, and price/quote evidence.
- Data Analytics owns backtest diagnostics, KPI gates, reports, dashboards, and validation surfaces.
- Investment Banking is useful only when issuer financing, deal, M&A, restructuring, or board context matters.

### Source Readiness

- Tools were discovered, but this task does not certify any source feed as production-ready.
- Public Equity and Investment Banking saved setup context is missing, so workflows should attempt real reads only when needed.
- Data Analytics source-routing preferences and semantic layers are missing; use project files until onboarding or explicit source setup exists.

### Exact Join Keys

- Any plugin output must become repo-native rows before strategy use.
- Required keys remain `source_id`, `published_at_utc`, `captured_at_utc`, `symbol`, `theme_id`, and `evidence_hash`.
- No symbol/date proximity fallback is allowed.

### Leakage Audit

- Plugin analysis cannot see future trade outcome labels during assignment.
- Quartr/Alpaca/Data Analytics outputs are evidence or review inputs, not strategy acceptance evidence by themselves.
- Broker truth remains separate from market data snapshots.

### Remaining Blockers

- No live source capture loop is connected yet.
- No Task608 failure has been replayed against plugin-derived event windows yet.
- No dashboard/report artifact has been rendered for the intelligence layer yet.

## No-Background Decision-Maker Report

- 사장님, 제일 쓸만한 건 Public Equity와 Data Analytics입니다.
- Public Equity는 뉴스/실적콜/IR/가격 근거를 가져오는 쪽입니다.
- Data Analytics는 그 근거가 진짜 성과를 개선했는지 표와 차트로 검증하는 쪽입니다.
- Investment Banking은 평소에는 쓰지 말고, 기업의 자금조달/인수합병/구조조정 이슈가 테마를 흔들 때만 씁니다.
- 이 플러그인들이 있어도 전략은 아직 미승인입니다.

## Artifact Manifest

### Inputs

- Public Equity Investing, Investment Banking, and Data Analytics plugin skill/router instructions.
- Discovered Alpaca, Quartr, and Data Analytics widget tool surfaces.

### Outputs

- `plugin_priority_map.csv`
- `project_workflow_plugin_map.csv`
- `task609_source_lane_plugin_map.csv`
- `plugin_guardrails.csv`
- `task_609p_decision.csv`
- `artifact_manifest.csv`

### Row Counts

- plugin_priority_rows: 3
- workflow_rows: 5
- source_lane_rows: 5
- guardrail_rows: 6

### Validation Commands

- `python -m unittest tests.test_task609p_plugin_utilization_map`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
