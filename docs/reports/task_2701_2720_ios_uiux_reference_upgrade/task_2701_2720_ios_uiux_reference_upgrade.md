# Task2701-2720 iOS UI/UX Reference Upgrade

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: The fresh Expo native iOS cockpit now uses Toss-inspired readable portfolio summaries and TradingView-inspired watchlist/chart interaction patterns without copying protected trade dress.
- Key UI additions: dense symbol rows, search/filter watchlist, range-aware price/VWAP/volume chart, thesis/risk/source detail tabs, no-trade reason panel, SDK54 compatibility note, typed fixture fallback.
- Next action: Use this read-only cockpit for paper/shadow monitoring only; do not add real-order controls until paper, PIT/as-of, acceptance, and broker gates are separately passed.

## Quant Expert Report

- Data source and source readiness: The app still reads `paper_ops_runtime_catalog.json` and `paper_trade_detail_view.json` when `EXPO_PUBLIC_TRADER_BRAIN_CATALOG_BASE_URL` is set. A typed fixture is used only as a fallback and for first render.
- Exact join keys: No new trading joins were introduced. Detail routing uses `trade.id` from normalized paper trade rows.
- Leakage audit: No outcome, backtest, or assignment logic was modified. UI remains read-only and displays existing paper/shadow explanations.
- Split/OOS metrics: Not applicable. No replay or strategy metric changed.
- Failure decomposition: Not applicable. This task changes reporting UX only.
- Cost/slippage stress: Not applicable.
- Remaining blockers: strict raw/as-of complete remains unresolved; real orders remain forbidden; UI polish does not change acceptance.

## No-Background Decision-Maker Report

- What happened: The iPhone cockpit was made much closer to a usable investment app surface: big P/L summary, dense watchlist, chart, risk view, and trade explanation tabs.
- Why it matters: You can now inspect why the brain wants to hold/watch/reject a paper position without opening raw CSVs.
- Whether this changes capital/deployment readiness: No. It is still diagnostic/paper-only.
- Plain-language next step: Use this as the monitor surface while paper/shadow trading logic is hardened.

## Artifact Manifest

- Inputs:
  - `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
  - `apps/ios-trader-brain/src/app/trade/[id].tsx`
  - `apps/ios-trader-brain/src/lib/cockpit-data.ts`
  - `apps/ios-trader-brain/src/lib/use-cockpit.ts`
- Outputs:
  - `apps/ios-trader-brain/src/components/segmented-control.tsx`
  - `apps/ios-trader-brain/src/components/symbol-row.tsx`
  - `apps/ios-trader-brain/src/components/price-chart.tsx`
  - `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
  - `scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
  - `apps/ios-trader-brain/ui-qa-mobile-v4.png`
- Validation commands:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npx expo-doctor`
  - `python scripts/trader_brain_2681_2700_native_ios_cockpit_validate.py`
  - `python scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
  - `npx expo export --platform web --clear`
- Source references used for UX pattern review:
  - Toss App Store listing
  - TradingView App Store listing
  - TradingView mobile product page
