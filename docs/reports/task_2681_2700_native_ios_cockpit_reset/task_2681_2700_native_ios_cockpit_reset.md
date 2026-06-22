# Task2681-2700 Native iOS Cockpit Reset

## Decision Summary

Task2641-2680 PWA-first mobile cockpit is superseded after user rejection.

Implemented a fresh Expo native iOS app at:

- `apps/ios-trader-brain`

The new app does not use `mobile_cockpit_catalog.json`.

It reads:

- `paper_ops_runtime_catalog.json`
- `paper_trade_detail_view.json`

The app is read-only paper/shadow observation only.

Strategy: `NOT_ACCEPTED`  
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`  
Real Capital: `FORBIDDEN`

## Quant Expert Report

This task does not change strategy, selector, sizing, exit, capital path, source feature set, or replay results.

Scope:

- Remove active PWA mobile cockpit path from `frontend/trader-terminal`.
- Remove mobile cockpit generator from `scripts/build_trader_terminal_catalog.py`.
- Create a fresh Expo Router app with native tabs, trade detail, chart, reasons, risk blockers, and settings.
- Keep real-order and live-order mutation absent.

Data contract:

- `EXPO_PUBLIC_TRADER_BRAIN_CATALOG_BASE_URL` optionally points at a catalog host.
- Missing or failed catalog fetch falls back to `src/fixtures/cockpit-fixture.json`.
- Fallback is UI-review only and not trading evidence.

## No-Background Decision-Maker Report

Done:

- Bad PWA mobile path removed from active UI.
- New iOS app created from scratch.
- App shows account summary, trades, why-buy, hold/reduce/exit reason, chart, risk blockers.
- App has no order execution.

Not done:

- No App Store build.
- No native broker order execution.
- No strategy acceptance.

Next:

- Point the app at a live paper catalog URL.
- Run on iPhone with Expo Go.
- Add paper daily journal views after the runtime writes stable daily snapshots.

## Artifact Manifest

| Artifact | Path |
| --- | --- |
| Expo app root | `apps/ios-trader-brain` |
| Validation script | `scripts/trader_brain_2681_2700_native_ios_cockpit_validate.py` |
| Codex Run action | `apps/ios-trader-brain/.codex/environments/environment.toml` |
| Run script | `apps/ios-trader-brain/script/build_and_run.sh` |
| Windows run script | `apps/ios-trader-brain/script/build_and_run.ps1` |
