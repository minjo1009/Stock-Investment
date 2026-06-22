# Task2781-2790 iOS Korean Paraphrase and Toss Fit Repair

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: The mobile cockpit was converted from English/backend wording to Korean investment-app wording.
- Main repair: Home, Trades, Detail, Risk, Settings, tab labels, fixture explanations, status chips, and benchmark text now use Korean paraphrases.
- Next action: Continue visual fit work from real iPhone feedback; the next high-value gap is making Home/holdings closer to Toss Securities' owned/watch/news routine.

## Quant Expert Report

- Data source and source readiness: No data or replay logic changed.
- Exact join keys: No trading joins changed.
- Leakage audit: UI copy only; no assignment, selector, sizing, exit, or paper order logic changed.
- Split/OOS metrics: Not applicable.
- Failure decomposition: The previous app still exposed English labels and backend states such as paper/proxy/source/status. This made it feel unlike a Korean brokerage app. The repair adds Korean display mapping while keeping raw values intact.
- Remaining blockers: Korean UI does not change strategy acceptance, PIT/as-of, paper readiness, broker readiness, or real-capital permission.

## No-Background Decision-Maker Report

- What happened: English and backend terms were replaced with Korean investor-facing language.
- Why it matters: The app now reads more like a Korean investing app and less like an engineering dashboard.
- Whether this changes capital/deployment readiness: No.
- Plain-language next step: Use the app on iPhone and point out the next screen that still feels unlike Toss Securities.

## Artifact Manifest

- Inputs:
  - `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
  - `apps/ios-trader-brain/src/app/trade/[id].tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
  - `apps/ios-trader-brain/src/app/(tabs)/settings.tsx`
- Outputs:
  - `apps/ios-trader-brain/src/lib/korean-labels.ts`
  - `apps/ios-trader-brain/ui-qa-korean-home.png`
  - `apps/ios-trader-brain/ui-qa-korean-trades.png`
  - `apps/ios-trader-brain/ui-qa-korean-detail.png`
  - `apps/ios-trader-brain/ui-qa-korean-settings.png`
- Validation commands:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `python scripts/trader_brain_2701_2720_ios_uiux_reference_upgrade_validate.py`
  - `npx expo export --platform web --clear`
