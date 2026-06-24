# Task3913 - Portfolio Chart Skill Alignment

## Status

- Status: COMPLETE_WITH_GPT_AUTOMATION_BLOCKED
- Area: Frontend App Governance
- Mode: Diagnostic-only / read-only
- Strategy acceptance: NOT_ACCEPTED
- Deployment readiness: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN

## Objective

Rework the Portfolio tab diagnostic chart using the chart-related skills and saved project UI specifications, with range buttons, slider controls, automatic chart sizing, guide lines, and selected-value readout.

## Chart Contract

- Analytical question: How did the selected diagnostic backtest equity curve move over the currently selected time window?
- Takeaway supported: the user can inspect recent or earlier diagnostic equity movement without confusing it for account truth or broker truth.
- Chart family: trend over time.
- Concrete variant: source-gated line chart with drawdown bars, value guide lines, range buttons, slider window controls, and selected-point readout.
- Data sufficiency: the current selected diagnostic snapshot exposes 62 monthly equity-curve points. Short ranges intentionally show fewer points; the UI labels the visible count.
- Palette policy: dark chart surface, green performance line, muted neutral guide lines, pink drawdown bars, white selected-value bubble.
- Source policy: no fake per-symbol price or volume data; the chart uses only attached diagnostic equity-curve data.

## Skill And MD Evidence Used

- `data-analytics:visualize-data`: trend chart selection, chart contract, label/scale QA, no decorative/underpowered chart rules.
- `trader-brain-ios-cockpit-frontend`: read-only cockpit chart expectations, range controls, touch/crosshair-style selection, VWAP/volume/marker posture.
- `docs/reports/task_3891_portfolio_tab_v2_production_spec/task_3891_portfolio_tab_v2_production_spec.md`: Portfolio V2 table/detail structure and chart-control expectations.
- `docs/reports/task_3900_mobile_visual_qa_gpt_loop/portfolio_visual_qa_spec.md`: mobile visual QA constraints.
- `DESIGN.md`: dark financial chart surface, restrained financial palette, chart accent colors.

## Implemented

- Chart geometry now uses actual rendered plot size instead of fixed pixel assumptions.
- The chart renders value guide lines with y-axis labels derived from the visible window.
- The chart recomputes min/max/mid guide lines per selected range and slider window.
- Range buttons remain connected to `1D`, `3D`, `5D`, `1M`, `3M`, and `ALL`.
- `이전` and `최근` controls remain connected to the visible chart window.
- Tapping the chart selects the nearest point and displays a selected-value readout.
- A latest-point readout is visible by default so the chart is interpretable before touch interaction.
- Drawdown bars and high-water line remain controlled by indicator chips.
- Validator coverage now requires actual plot-size measurement, chart guide lines, selected readout, and source-gated geometry.

## GPT Loop Record

Requested GPT review loops: 2

Captured GPT review loops: 0

Result: BLOCKED_AUTOMATION_NO_GPT_CAPTURE

Reason: the current available tool surface did not provide a usable Chrome/GPT prompt-and-response capture path during this run. No GPT recommendation was treated as source-of-truth.

## Screenshot Evidence

Local QA screenshots:

- `data/artifacts/portfolio_tab_capture_task3913_chart_5d_guides.png`
- `data/artifacts/portfolio_tab_capture_task3913_chart_3d_slider.png`
- `data/artifacts/portfolio_tab_capture_task3913_chart_point_select.png`
- `data/artifacts/portfolio_tab_capture_task3913_chart_point_select_center.png`
- `data/artifacts/portfolio_tab_capture_task3913_chart_selected_default.png`

These screenshots are local QA evidence only and are not authoritative data artifacts.

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
