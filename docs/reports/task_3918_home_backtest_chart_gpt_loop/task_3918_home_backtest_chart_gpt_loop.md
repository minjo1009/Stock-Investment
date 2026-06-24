# Task3918 - Home Backtest Chart GPT Loop

## Status

- Status: COMPLETE_WITH_GPT_AUTOMATION_BLOCKED
- Area: Frontend App Governance
- Mode: Diagnostic-only / read-only
- Strategy acceptance: NOT_ACCEPTED
- Deployment readiness: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN

## Objective

Connect the HOME tab to the selected read-only diagnostic backtest snapshot and render a bounded mobile chart on the HOME screen, using the requested GPT-loop workflow where available.

## GPT Loop Record

Requested GPT consult/loop: 1

Captured GPT response: 0

Result: BLOCKED_AUTOMATION_NO_GPT_CAPTURE

Reason: the available tool surface did not expose a usable Chrome/GPT prompt-and-response capture path during this run. No GPT recommendation was captured or treated as source-of-truth.

Fallback used:

- Current repo operating state and frontend task reports.
- `trader-brain-ios-cockpit-frontend` read-only chart UI guidance.
- `data-analytics:visualize-data` chart selection and QA guidance.
- Local browser screenshot evidence.
- Existing frontend validators.

## Implemented

- HOME hero now uses the selected diagnostic backtest snapshot for diagnostic evaluation value, initial capital, diagnostic P/L, return rate, win rate, and MDD.
- HOME chart now receives `backtestSnapshotFixture` and renders a bounded line chart from the selected diagnostic equity curve.
- The chart supports local range buttons: `최근 5`, `1년`, `3년`, and `전체`.
- QQQ is displayed only as a final benchmark reference line because point-by-point QQQ data is not attached.
- The chart includes principal reference, QQQ reference, drawdown bars, guide labels, and selected/latest value readout.
- HOME fixture and HOME fixture JSON Korean copy were normalized to remove mojibake.
- HOME design validator was updated to require selected backtest snapshot linkage and bounded chart geometry.

## Screenshot Evidence

Local QA screenshots:

- `data/artifacts/home_tab_capture_task3918_backtest_chart.png`
- `data/artifacts/home_tab_capture_task3918_backtest_chart_after.png`
- `data/artifacts/home_tab_capture_task3918_backtest_chart_after_fit.png`

These screenshots are local QA evidence only and are not authoritative trading, account, broker, or performance evidence.

## Validation

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run lint`
- `python scripts/task_registry_validate.py`
- `git diff --check`

## Boundaries

- No DB mutation.
- No runtime API connection.
- No broker/API call.
- No order handler.
- No paper/live permission.
- No deployment readiness.
- No strategy acceptance.
- No real-capital permission.
