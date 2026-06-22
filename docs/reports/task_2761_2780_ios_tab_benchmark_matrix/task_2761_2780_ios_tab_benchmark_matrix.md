# Task2761-2780 iOS Tab Benchmark Matrix

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: The iOS cockpit now has a tab-by-tab benchmark matrix instead of a vague Toss/TradingView claim.
- App change: Settings renders the benchmark map for Home, Trades, Trade detail, Risk, and Settings.
- Next action: Use the matrix to prioritize the next UI iteration: fullscreen chart, watchlist column customization, portfolio composition, and drawdown timeline.

## Quant Expert Report

- Data source and source readiness: No source acquisition or replay changed.
- Exact join keys: No trading joins changed.
- Leakage audit: UI benchmark metadata only; no assignment, outcome, selector, sizing, or exit logic changed.
- Split/OOS metrics: Not applicable.
- Failure decomposition: Previous UI work lacked tab-level acceptance criteria. This task adds explicit per-tab benchmark targets and remaining gaps.
- Remaining blockers: UI benchmark completion is not strategy acceptance, live-source readiness, broker truth, or real-capital permission.

## Tab Benchmark Matrix

| Tab | Primary benchmark | Current target | Implemented | Remaining gap |
| --- | --- | --- | --- | --- |
| Home | Toss Securities portfolio/account overview | Account, equity, P/L, holdings, safety in one pass | My accounts, My Portfolio, market pulse, holdings, paper-only chip | owned/watch split, composition chart, position news/reason feed |
| Trades | TradingView mobile watchlist and advanced/table view | Scan symbol, price, change, risk, mini trend, sorting | dark watchlist, search, filters, P/L/Risk/A-Z sorting, mini sparklines | custom columns, sector grouping, source/news per row |
| Trade detail | TradingView mobile chart-first detail | Symbol/price/range/candles/VWAP/volume/thesis in one flow | hidden native header, chart-first layout, range selector, candles, VWAP, volume, thesis/risk/source tabs | fullscreen chart, safe readout, indicator toggles |
| Risk | Broker safety / portfolio risk cockpit | Explain real-trading block, warnings, rejected candidates | blocked hero, MDD/CAGR, warnings, blockers, rejected candidates | drawdown timeline, daily loss guard, position risk contribution |
| Settings | Trading app connection/data settings | Keep source contracts and safety away from trading screens | base URL, source mode, contract version, SDK54, runtime files, no-live boundary | refresh detail, source freshness ledger, diagnostic export |

## Source Notes

- TradingView watchlist references support watchlist sorting, key metrics, advanced tabs, grouping, and symbol details.
- TradingView mobile chart references emphasize chart layout adaptation on mobile.
- Toss references emphasize portfolio/account readability, holdings/watch separation, and investment routine support.

## No-Background Decision-Maker Report

- What happened: We stopped saying “Toss/TradingView-like” generically and mapped every app tab to a concrete benchmark.
- Why it matters: Future UI work can be judged screen by screen.
- Whether this changes capital/deployment readiness: No.
- Plain-language next step: Improve the highest-value gaps, starting with chart fullscreen and watchlist column customization.

## Artifact Manifest

- Inputs:
  - TradingView watchlist documentation
  - TradingView advanced view documentation
  - TradingView mobile chart documentation
  - Toss UX/research references
- Outputs:
  - `apps/ios-trader-brain/src/lib/tab-benchmarks.ts`
  - `apps/ios-trader-brain/src/components/benchmark-panel.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
  - `apps/ios-trader-brain/ui-qa-tab-benchmark-settings-v2.png`
  - `scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
- Validation commands:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `python scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
