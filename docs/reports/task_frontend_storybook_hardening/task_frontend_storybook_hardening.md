# Task Frontend Storybook Hardening

## Decision Summary

- Verdict: `STORYBOOK_RUNTIME_AND_QA_BASELINE_INSTALLED_WITH_LIMITED_SCOPE`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

Task3805 installs a runnable Storybook web baseline for the Expo/React Native scaffold, adds minimal scaffold lint/test commands, and hardens the frontend safety validator.

No product screen, DB connection, broker/API call, runtime API connection, KIS/Alpaca integration, paper/live order path, deployment command, chart implementation, strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission was added.

## Done

- Installed Storybook web runtime dependencies:
  - `storybook`
  - `@storybook/react-native-web-vite`
  - `vite`
  - `react-native-web`
  - `react-dom@19.2.3`
- Added `.storybook/main.ts` and `.storybook/preview.ts`.
- Replaced `npm run storybook` hard blocker with `storybook dev -p 6006 --ci --no-open`.
- Added `npm run storybook:smoke` and validated smoke startup.
- Expanded foundation stories for `AppText`, `Badge`, and `CardContainer` with default, read-only, blocked, and stale/unknown states.
- Added `npm run lint` as scaffold boundary lint.
- Added `npm test` as Storybook story export smoke plus safety validator.
- Hardened `npm run validate:safety`:
  - detects forbidden integration imports and broker/API/SQLite patterns
  - detects forbidden visible action terms
  - allows forbidden action terms only with disabled/blocked governance context and no action handlers
  - scans `.storybook`, `app`, and `src`
- Added allowed disabled-action safety fixture.
- Deferred NativeWind with an explicit reason.

## Failed

- NativeWind was not installed. It is `DEFERRED_WITH_REASON_TASK3805` because current stable NativeWind install adds Tailwind/Metro/Babel surface area before any scaffold component uses `className`, while the current app is token/inline-style based and already has npm peer warnings.
- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Maestro remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Expo iOS development build remains `REQUIRED_POST_SCAFFOLD_HARDENING` and was not run on this Windows environment.
- npm still reports 10 moderate audit findings. No automatic audit fix was run.
- npm still reports peer warnings around `react-native-worklets`. No dependency override was applied.

## Validation

- `npm run typecheck`
- `npm run validate:safety`
- `npm run lint`
- `npm test`
- `npm run storybook:smoke`
- `python scripts/task_registry_validate.py`
- `git diff --check`

## Remaining Blockers

- Select primary read-model fixture source.
- Replace fixture `.gitkeep` with source-derived payloads from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
- Add screenshot QA and decide Maestro.
- Decide NativeWind install versus continued token/inline-style path after component needs are clear.
- Validate iOS development build on a suitable macOS/iOS environment.

## Next Task Recommendation

Task3806 should be `Read Model Fixtures And Domain Component Contracts`.

It should create source-derived fixtures and add domain component contracts without implementing product screens or trading actions.

## Artifact Manifest

See `artifact_manifest.csv`.
