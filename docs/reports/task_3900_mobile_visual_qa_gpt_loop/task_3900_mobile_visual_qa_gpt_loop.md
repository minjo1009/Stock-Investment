# Task3900 - Mobile Visual QA GPT Loop

## Summary

Task3900 applies a screenshot-driven mobile visual QA pass to HOME, PORTFOLIO, and BRAIN.

The run used 390x844 web-preview screenshots and GPT expert-agent feedback to create implementation-ready revision specs, then applied the highest-priority cleanup:

1. HOME now leads with portfolio hero, today-check items, and a Korean QQQ-relative return chart.
2. PORTFOLIO now reduces table/detail clipping and replaces prominent internal state copy with user-facing Korean copy.
3. BRAIN now reduces right-edge clipping risk, simplifies the first viewport, and removes lifecycle-promotion wording.
4. A pre-data-connection contract now defines what must be true before fixtures are replaced with real read-only payloads.

## GPT Capture Status

Chrome GPT automation was not used for this closeout. The visual QA relay used bounded GPT expert-agent subagents with local screenshot artifacts. GPT remains review-only and is not source of truth.

## Implemented

- Added HOME, PORTFOLIO, and BRAIN visual QA revision specs.
- Added three-loop ledger for screenshot-based expert feedback.
- Added pre-data-connection contract for HOME/PORTFOLIO/BRAIN real-read-path preparation.
- Reordered HOME so `오늘 확인할 것` appears before the chart.
- Replaced HOME `UNKNOWN 원`, `Performance`, raw chart status, and chart point count with Korean pending-state copy.
- Kept HOME timeframe chips clickable without drawing synthetic chart lines.
- Reduced PORTFOLIO table width pressure and stock-detail chart height.
- Replaced prominent PORTFOLIO raw state copy with `확인 대기`, `연결 대기`, `출처 연결 대기`, and `검증 전 데이터`.
- Reworked BRAIN news interpretation hierarchy and relation/candidate wording.
- Updated validators to reflect the new product-copy expectations.

## Visual Evidence

- `data/artifacts/task_3900_mobile_visual_qa_gpt_loop/screenshots/home_after_390x844.png`
- `data/artifacts/task_3900_mobile_visual_qa_gpt_loop/screenshots/portfolio_after_390x844.png`
- `data/artifacts/task_3900_mobile_visual_qa_gpt_loop/screenshots/brain_after_390x844.png`

Scope: local web-preview screenshot evidence only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:mobile-scan-list-v1`
- `cd apps/ios-trader-brain && npm run validate:detail-v1`
- `cd apps/ios-trader-brain && npm run validate:frontend-governance`

## Deferred

- Native iOS device screenshots remain unavailable in this Windows environment.
- Real account, holdings, chart, news, broker truth, and Brain runtime payloads remain disconnected.
- Chart pan/zoom/crosshair and true sticky table behavior remain future implementation work.
- Chrome GPT tab-based autonomous relay remains deferred because this pass used local expert-agent screenshot review.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
