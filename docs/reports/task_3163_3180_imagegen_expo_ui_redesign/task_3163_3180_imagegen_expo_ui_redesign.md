# Task3163-3180 ImageGen + Expo UI Redesign

## Decision Summary

- Verdict: implemented a fresh UI pass using ImageGen reference direction plus Expo native implementation instead of the previous Product Design-only flow.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 5 tab screenshots captured, 1 montage generated, TypeScript pass, Expo lint pass, Expo web export pass, custom UI boundary validator pass.
- What changed: bottom tabs were rebuilt with Expo Tabs and `expo-symbols`, Home was kept concise, Scanner was centered and tightened as a dark tactical console, Market was fully rewritten, Risk/Analysis remain read-only command surfaces.
- Next action: use the montage as the visual baseline for the next polish loop; remaining visual gap is native-iOS icon verification because web captures use text fallback for SF Symbols.

## Quant Expert Report

- Data source and source readiness: no new raw source, replay source, selector source, broker source, or live-source acquisition was performed. UI reads the existing `useCockpit` runtime contract.
- Exact join keys: UI still routes scanner rows to detail by `trade.id`; market/theme/risk panels consume existing optional runtime fields such as `marketContext`, `themeHeat`, `eventTimeline`, `dataHealth`, `policyCompare`, and `tradeReview`.
- Leakage audit: not applicable. No model, replay, label, lifecycle matching, price proximity fallback, or outcome assignment logic changed.
- Split/OOS metrics: not applicable. No backtest or replay was run.
- Failure decomposition: previous UI line failed on visual credibility and broken benchmark execution. This pass replaced the tool path with ImageGen reference synthesis, direct Expo implementation, and screenshot-based QA.
- Cost/slippage stress: not applicable. No PnL logic changed.
- Remaining blockers: strategy remains `NOT_ACCEPTED`; deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; real capital remains `FORBIDDEN`; native iOS device screenshot is still needed to verify SF Symbol rendering outside web fallback.

## No-Background Decision-Maker Report

- What happened: the app UI was rebuilt toward the requested benchmark mix: TradingView tactical console 70%, Toss/Apple-like Home 20%, Analysis/Risk 10%.
- Why it matters: the result is now closer to a real investment app surface, with less scrolling, denser scanner information, cleaner market/risk boards, and fewer amateur visual artifacts.
- Whether this changes capital/deployment readiness: no. This is UI/reporting only and does not authorize trading or deployment.
- Plain-language next step: review the montage, then run one more visual polish pass if the Scanner/Home balance still feels below the target examples.

## Artifact Manifest

- Inputs: existing Expo app under `apps/ios-trader-brain`, existing cockpit runtime contract, ImageGen reference direction produced in-session.
- Outputs:
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/task3163_3180_ui_result_montage.png` size 233844 bytes.
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/01_home.png` size 44403 bytes.
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/02_scanner.png` size 42993 bytes.
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/03_analysis.png` size 34799 bytes.
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/04_market.png` size 33490 bytes.
  - `data/artifacts/task_3163_3180_imagegen_expo_ui_redesign/screenshots_live/05_risk.png` size 40502 bytes.
- Row counts: not applicable for UI artifacts.
- Validation commands:
  - `cd apps/ios-trader-brain; npx tsc --noEmit`
  - `cd apps/ios-trader-brain; npm run lint`
  - `cd apps/ios-trader-brain; npx expo export --platform web --clear`
  - `python scripts/trader_brain_3163_3180_imagegen_expo_ui_redesign_validate.py`
- Source hashes: not applicable. No source acquisition was performed.
