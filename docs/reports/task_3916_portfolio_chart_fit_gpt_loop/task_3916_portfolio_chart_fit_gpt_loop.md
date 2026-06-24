# Task3916 - Portfolio Chart Fit GPT Loop

## Status

- Status: COMPLETE_WITH_GPT_AUTOMATION_BLOCKED
- Area: Frontend App Governance
- Mode: Diagnostic-only / read-only
- Strategy acceptance: NOT_ACCEPTED
- Deployment readiness: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN

## Objective

Re-check the Portfolio diagnostic chart fit after user visual feedback that the chart still did not fit inside its card, use the chart-related skills, attempt the requested GPT loop, and repair the bounded chart rendering issue.

## GPT Loop Record

Requested GPT review loops: 2

Captured GPT review loops: 0

Result: BLOCKED_AUTOMATION_NO_GPT_CAPTURE

Reason: the available tool surface did not expose a usable Chrome/GPT prompt-and-response capture path during this run. No GPT recommendation was treated as source-of-truth.

Fallback used:

- Local browser screenshot before patch.
- `data-analytics:visualize-data` chart QA rules.
- `trader-brain-ios-cockpit-frontend` mobile chart boundary rules.
- Repo validators and screenshot comparison.

## Visual Finding

The chart card size was not the core failure. The rendered trend line was visually broken because each rotated line segment was positioned from the previous point while React Native/Web rotates the element around its own center. That caused segment drift and disconnected-looking line pieces inside the plot box.

## Implemented

- Changed chart segment placement to use the midpoint between adjacent points before applying rotation.
- Accounted for rendered line thickness when calculating each segment's top coordinate.
- Added validator coverage requiring midpoint-based segment placement inside the measured chart box.
- Captured before/after mobile web screenshots for the Portfolio chart.
- Verified the 3D range button still updates the chart and preserves bounded line rendering.

## Screenshot Evidence

Local QA screenshots:

- `data/artifacts/portfolio_tab_capture_task3914_chart_before.png`
- `data/artifacts/portfolio_tab_capture_task3914_chart_after_fit.png`
- `data/artifacts/portfolio_tab_capture_task3914_chart_after_3d.png`

These screenshots are local QA evidence only and are not authoritative trading, account, broker, or performance evidence.

## Validation

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
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
