# Task3021-3040 iOS Concise Navigation Redesign

## Decision Summary

- Verdict: `ios_concise_navigation_redesign_completed_read_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 5 app screens simplified, 4 worker packets completed, 1 explorer packet completed, replay performed 0, paper order intents created 0, live orders created 0.
- What changed: the iOS cockpit now uses Apple shell, Toss-readable first-screen hierarchy, TradingView-style scanner/detail flow, and compact governance pages.
- Next action: run device or browser visual QA and fix any viewport-specific spacing problems.

## Quant Expert Report

### Data Source And Source Readiness

This task is UI/UX and frontend information architecture work. It does not acquire sources, run replay, change selector logic, or change execution logic.

The app continues to read `CockpitData` through `useCockpit()` and `loadCockpitData()`. The visible fields are constrained to existing runtime/fixture data:

- Home: `summary`, `trades[0]`, `policyCompare`, `sourceMode`, `generatedUtc`.
- Trades: `trades`, `noTradeReasons`, scanner fields, source freshness, and risk fields.
- Detail: trade chart bars/markers, entry/current/exit fields, thesis/risk/source text, source ids and hashes.
- Risk: warning codes, blockers, no-trade reasons, and policy compare blockers.
- Settings: catalog base URL, source mode, contract version, generated time, rules, and standing status.

### Exact Join Keys

No new joins were added. Navigation continues to use `trade.id` from `TradeIntent` for `/trade/[id]`.

### Leakage Audit

No label, future outcome, or assignment logic was added. Missing labels remain missing-state displays and are not converted into negatives.

### Split/OOS Metrics

Not applicable. No replay, split/OOS comparison, backtest, or performance comparison was run.

### Failure Decomposition

The prior iOS cockpit exposed too much information in long scroll surfaces:

1. Home repeated account, market, candidate, list, and status information.
2. Trades mixed search, grouping, sorting, columns, and detail text with equal weight.
3. Detail showed chart, timing audit, evidence, risk, and source blocks as a long sheet.
4. Risk exposed deep freeze/split/gate details by default.
5. Settings exposed long benchmark/reference text instead of connection and safety state.

The redesign keeps only the immediate decision surface on each page and moves secondary detail into tabs or dedicated pages.

### Cost/Slippage Stress

Not applicable. No PnL, cost, slippage, order, fill, or broker-truth logic changed.

### Remaining Blockers

- iPhone visual QA was not run in this task.
- Existing fixture/runtime source text may still contain historical mojibake outside the edited screen copy.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

### What Happened

The app was reduced into a tighter navigation model:

- Home: account state, today check, lead candidate, read-only blocker.
- Trades: grouped scanner and comparison.
- Detail: chart-first symbol review with Evidence, Risk, Sources tabs.
- Risk: current blockers and excluded symbols.
- Settings: connection, data contract, and no-live-order safety.

### Why It Matters

The user no longer has to scroll through one large sheet to find the main answer. Each page now has one job.

### Whether This Changes Capital Or Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

### Plain-Language Next Step

Run visual QA on iPhone-sized screens and repair any spacing, clipping, or text-density issue.

## Artifact Manifest

### Inputs

- `apps/ios-trader-brain/src/types/cockpit.ts`
- `apps/ios-trader-brain/src/lib/use-cockpit.ts`
- `apps/ios-trader-brain/src/lib/cockpit-data.ts`
- `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
- `docs/ownership/subagent_packet_standard.md`
- `docs/architecture/test_validation_canonicalization_map.md`

### Outputs

- `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
- `scripts/trader_brain_3021_3040_ios_concise_navigation_redesign_validate.py`
- `docs/reports/task_3021_3040_ios_concise_navigation_redesign/task_3021_3040_ios_concise_navigation_redesign.md`
- `docs/reports/task_3021_3040_ios_concise_navigation_redesign/task_3040_decision.csv`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/task3040_closeout.csv`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/page_data_contract_map.csv`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/subagent_packet_summary.csv`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/artifact_manifest.md`

### Row Counts

- Subagent packets: 5.
- Page data contract map rows: 5.
- App screens changed: 5.

### Validation Commands

- `cd apps/ios-trader-brain; npx tsc --noEmit`
- `cd apps/ios-trader-brain; npm run lint`
- `python scripts/trader_brain_3021_3040_ios_concise_navigation_redesign_validate.py`
- `python scripts/task_registry_validate.py`

### Source Hashes

Not computed. This task did not acquire or transform market/raw source data.
