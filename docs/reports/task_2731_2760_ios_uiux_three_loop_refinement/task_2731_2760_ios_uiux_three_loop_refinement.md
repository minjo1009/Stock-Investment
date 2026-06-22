# Task2731-2760 iOS UI/UX Three-Loop Refinement

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: Three UI/UX loops were applied after the user asked for repeated refinement.
- Loop 1: Added watchlist mini sparklines and removed the default native trade-detail header so the chart becomes the first visual surface.
- Loop 2: Added watchlist sorting controls and improved trader scanning density.
- Loop 3: Reworked the risk cockpit language and reran visual, SDK54, lint, export, and governance validation.

## Quant Expert Report

- Data source and source readiness: No source or replay data changed.
- Exact join keys: No trading joins changed.
- Leakage audit: UI-only changes; no assignment, selector, sizing, exit, or replay logic changed.
- Split/OOS metrics: Not applicable.
- Failure decomposition: Previous UI still felt card-heavy and static. The loops increased market-screen density, reduced navigation chrome, and made risk/no-trade status easier to scan.
- Remaining blockers: UI improvement does not change strict PIT/as-of, acceptance, deployment, broker, or real-capital status.

## No-Background Decision-Maker Report

- What happened: The iPhone app got three polish passes.
- Why it matters: It now feels more like a trading monitor instead of a backend report viewer.
- Whether this changes capital/deployment readiness: No.
- Plain-language next step: Use it on the iPhone and point out the next screen that still feels weak.

## Artifact Manifest

- Inputs:
  - `apps/ios-trader-brain/src/app/_layout.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
  - `apps/ios-trader-brain/src/components/symbol-row.tsx`
- Outputs:
  - `apps/ios-trader-brain/src/components/mini-sparkline.tsx`
  - `apps/ios-trader-brain/ui-qa-loop3-home.png`
  - `apps/ios-trader-brain/ui-qa-loop3-trades.png`
  - `apps/ios-trader-brain/ui-qa-loop3-detail.png`
  - `apps/ios-trader-brain/ui-qa-loop3-risk.png`
- Validation commands:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npx expo-doctor`
  - `python scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
  - `npx expo export --platform web --clear`
