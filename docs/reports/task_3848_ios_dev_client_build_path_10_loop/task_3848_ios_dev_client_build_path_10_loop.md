# Task3848 — iOS Dev-client Build Path 10-loop Implementation

## Summary

Task3848 moved the frontend from web-preview-only readiness toward a concrete Expo iOS development-build path without executing native build, Apple login, EAS login, iPhone install, broker mutation, DB mutation, paper/live order, or real-capital action.

GPT expert mode used: Agent Mode + Deep Research requested in Chrome GPT.

## GPT Findings Used

GPT inspected the current project context and recommended these 10 loops:

1. Add `expo-dev-client` dependency contract.
2. Add safe `eas.json` profiles.
3. Add governed `ios.bundleIdentifier`.
4. Harden scripts to prevent silent production/native build execution.
5. Add operator runbook for EAS iOS dev build.
6. Add iOS evidence manifest schema.
7. Add simulator/device profile split validation.
8. Add internal distribution readiness contract.
9. Add Maestro native-run evidence gate.
10. Add governance closeout report and validation evidence.

External source facts checked against official Expo documentation:

- Development builds are a customizable native app environment, distinct from Expo Go.
- EAS development profiles use `developmentClient: true`.
- Internal iOS distribution requires operator-owned Apple/EAS credentials and provisioning.
- `ios.bundleIdentifier` belongs under the Expo iOS app config.

## Implemented

1. Installed `expo-dev-client` through Expo-compatible install.
2. Added `eas.json` with `development`, `development-simulator`, and `preview-internal` profiles.
3. Added iOS bundle identifier `com.minjo.stockinvestment.iostraderbrain.dev`.
4. Kept `ios:dev` blocked behind the existing hardening script; no script silently runs `eas build`.
5. Added iOS operator runbook under `docs/frontend_ios`.
6. Added native iOS evidence manifest template.
7. Hardened dev-build readiness validator.
8. Added EAS build contract validator.
9. Hardened iOS evidence, Maestro, and visual regression validators.
10. Recorded this task closeout and artifact manifest.

## Validation

Executed from `apps/ios-trader-brain`:

- `npm run typecheck` — PASS
- `npm run lint` — PASS
- `npm run ios:dev:preflight` — PASS
- `npm run validate:dev-build-readiness` — PASS
- `npm run validate:eas-build-contract` — PASS
- `npm run validate:ios-operator-runbook` — PASS
- `npm run validate:ios-evidence-contract` — PASS
- `npm run validate:maestro-contract` — PASS
- `npm run validate:visual-regression-contract` — PASS
- `npm test` — PASS

Repository-level validation:

- `python scripts/task_registry_validate.py` — PASS
- `git diff --check` — PASS

## Known Warnings

`npx expo install expo-dev-client` completed and updated npm dependencies, but npm reported existing dependency/audit warnings:

- peer dependency warning around `react-native-worklets`
- 10 moderate npm audit findings

These warnings were not fixed in this task because broad dependency remediation could destabilize the Expo scaffold.

## Still Blocked

The following remain operator-owned and were not executed:

- `eas login`
- Apple Developer login
- UDID registration
- EAS cloud build
- iOS simulator build/run
- iPhone install
- native screenshot capture
- actual Maestro traversal

## Safety Confirmation

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation was added.
- No live order path was added.
- No paper promotion was added.
- Missing/stale data remains `UNKNOWN/BLOCKER`.
