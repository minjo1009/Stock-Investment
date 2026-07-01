# iOS Dev-client Operator Runbook

## Status

- Status: `BLOCKED_UNTIL_USER_OPERATOR`
- App target: Expo Development Build / iOS-first
- Bundle identifier: `com.minjo.stockinvestment.iostraderbrain.dev`
- Expo Go: not the active target
- App authority: `NOT_AUTHORITY`

## Hard Boundaries

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- No DB/runtime/KIS/Alpaca/broker connection is authorized by this runbook.

## Profiles

Use the checked-in `eas.json` profiles:

- `development`: iPhone development client / internal distribution profile.
- `development-simulator`: iOS Simulator development client profile. Requires macOS and Xcode.
- `preview-internal`: internal review build profile. This is not App Store or TestFlight readiness.

## Operator-owned Prerequisites

The following are not performed by Codex:

1. `eas login`
2. Apple Developer login
3. iPhone UDID registration
4. Apple provisioning profile creation or repair
5. EAS cloud build execution
6. iOS Simulator launch
7. iPhone install
8. Native screenshot capture
9. Maestro native traversal execution

## Commands For Operator Evidence

Run only when the operator has Apple/EAS credentials and accepts the external account actions.

```powershell
cd apps/ios-trader-brain
npm run ios:dev:preflight
npx eas-cli build --platform ios --profile development
```

For a macOS simulator build:

```bash
cd apps/ios-trader-brain
npm run ios:dev:preflight
npx eas-cli build --platform ios --profile development-simulator
```

For internal review only:

```bash
cd apps/ios-trader-brain
npx eas-cli build --platform ios --profile preview-internal
```

## Required Evidence Before Marking Native App Seen

Record the evidence outside chat before any readiness wording changes:

1. EAS build id or local Xcode build log.
2. Installed app bundle id equals `com.minjo.stockinvestment.iostraderbrain.dev`.
3. iPhone or simulator launch screenshot.
4. Read-only tab traversal proof.
5. No broker mutation path reachable.
6. `npm test` result from the same code revision.

## Non-Authorization

Successful installation does not imply:

- strategy acceptance,
- deployment readiness,
- product readiness,
- paper/live permission,
- broker mutation permission,
- real-capital permission.
