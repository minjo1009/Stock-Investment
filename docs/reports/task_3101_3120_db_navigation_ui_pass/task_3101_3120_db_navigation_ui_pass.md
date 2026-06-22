# Task3101-3120 DB Navigation UI Pass

## Decision Summary

- Verdict: `db_linked_navigation_ui_pass_completed_read_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 5 screens updated, 1 typed `dataHealth` contract added, 5 navigation edges exposed, screenshots captured for 5 screens, app code changed only under `apps/ios-trader-brain`, replay performed 0, paper order intents created 0, live orders created 0.
- What changed: the UI now exposes the page-to-page data contract and reads connector/file/risk health from `CockpitData.dataHealth`.
- Image report: `data/artifacts/task_3101_3120_db_navigation_ui_pass/db_navigation_ui_pass_report.png`.

## Quant Expert Report

### Data Source And Source Readiness

This is frontend contract and UI work. No trading raw source was acquired. No replay, selector, sizing, label, order, fill, or broker logic changed.

The app data contract now includes:

- `DataConnectorHealth`
- `RequiredDataFile`
- `RiskHealthMetric`
- `NavigationEdge`
- `CockpitData.dataHealth`

Runtime normalization accepts optional source fields from `source_diagnostics.connector_health`, `source_diagnostics.required_files`, and `risk_metrics`. If those are missing, the app derives explicit display-only health rows from existing runtime catalog state. This derivation is for UI connection/readiness display only; it does not infer trading lifecycle, labels, outcomes, or negative examples.

### Exact Join Keys

- Home -> Detail: `trade.id`
- Trades -> Detail: `trade.id`
- Detail -> Risk: `trade.riskState`, `trade.sourceFreshnessState`, `dataHealth.riskMetrics`
- Risk -> Settings: `dataHealth.connectors.connectorId`, `dataHealth.requiredFiles.fileName`

### Leakage Audit

No outcome labels or future values entered assignment logic. Missing UI fields remain explicit missing/fixture states.

### Split/OOS Metrics

Not applicable. No backtest or split/OOS evaluation was run.

### UI/Data Contract Changes

- Home: added account trend and a compact page connection map.
- Trades: added saved scan/data contract panel above scanner controls.
- Detail: added selected range summary with entry-to-current delta, latest VWAP gap, source state, and chart key.
- Risk: rebuilt around `dataHealth.riskMetrics`, connector freshness, and no-trade blocker rows.
- Settings: rebuilt around connector health, required files, safety locks, and page map.

### Remaining Blockers

- Current runtime may not yet provide full connector/file/risk rows. The UI has a fallback display contract until backend emits those fields.
- Device QA on actual iPhone/Expo Go was not run in this pass.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

### What Happened

The app now shows how each page connects to DB/runtime data:

- Home shows account trend and page path.
- Trades shows scanner contract.
- Detail shows selected range and chart data key.
- Risk shows risk metrics and stale connectors.
- Settings shows connectors, files, safety locks, and page map.

### Whether This Changes Capital Or Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

## Artifact Manifest

### Inputs

- Task3061 actual mobile app benchmark correction.
- Existing iOS cockpit source under `apps/ios-trader-brain`.
- Existing runtime/fixture contract.

### Outputs

- `apps/ios-trader-brain/src/types/cockpit.ts`
- `apps/ios-trader-brain/src/lib/cockpit-data.ts`
- `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
- `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
- `scripts/trader_brain_3101_3120_db_navigation_ui_pass_validate.py`
- `data/artifacts/task_3101_3120_db_navigation_ui_pass/db_navigation_ui_pass_report.png`
- `data/artifacts/task_3101_3120_db_navigation_ui_pass/screenshots_live/*.png`

### Validation

- `cd apps/ios-trader-brain; npx tsc --noEmit`
- `cd apps/ios-trader-brain; npm run lint`
- `cd apps/ios-trader-brain; npx expo export --platform web --clear`
- `python scripts/trader_brain_3101_3120_db_navigation_ui_pass_validate.py`
- `python scripts/task_registry_validate.py`

Validation authority: `REPORTING_HEALTH` and `GOVERNANCE_HEALTH` only. Passing validation does not mean strategy acceptance, deployment readiness, or real-capital permission.

