# Task3827 HOME v0 Scaffold-only Assembly

## Decision Summary

Task3827 completed Loop 2 of the frontend real-implementation GPT run by replacing the HOME placeholder with a scaffold-only fixture-backed `HOME v0`.

`HOME v0` is read-only and `NOT_AUTHORITY`. It is not product screen readiness, backend truth, source truth, broker truth, strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission.

## Quant Expert Report

### Scope

- Created `apps/ios-trader-brain/src/read-models/homeFixture.ts` as a typed wrapper derived from `src/mocks/fixtures/home.json`.
- Replaced `apps/ios-trader-brain/app/(tabs)/index.tsx` placeholder with a HOME v0 scaffold-only screen assembly.
- Used existing components only: foundation, layout, generic, and `DisabledActionBar`.
- Preserved the original JSON fixture payload.

### Screen Evidence

HOME v0 displays:

- scaffold-only fixture-backed boundary
- `NOT_AUTHORITY`
- read-only status
- strategy `NOT_ACCEPTED`
- deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real capital `FORBIDDEN`
- portfolio source `UNKNOWN`
- brain source `STALE`
- freshness and blocker summaries
- disabled action governance reasons

### Safety Boundary

No package, tsconfig, fixture JSON, validator, Storybook, DB, runtime API, broker, KIS, Alpaca, paper/live, screenshot QA, Maestro, EAS, or NativeWind changes were made.

## No-Background Decision-Maker Report

The first visible frontend implementation now exists, but only as a scaffold screen.

It is intentionally conservative. It shows unknown/stale/missing/blocker states instead of hiding them, and it refuses to imply execution permission.

## Artifact Manifest

See `artifact_manifest.csv`.

## Validation

- `cd apps/ios-trader-brain && npm run typecheck`: PASS
- `cd apps/ios-trader-brain && npm run lint`: PASS
- `cd apps/ios-trader-brain && npm test`: PASS
- `cd apps/ios-trader-brain && npm run storybook:smoke`: PASS
- `cd apps/ios-trader-brain && npm run validate:safety`: PASS
- `cd apps/ios-trader-brain && npm run validate:fixtures`: PASS
- content check for scaffold boundary and hard state: PASS
- `python scripts/task_registry_validate.py`: PASS
- `git diff --check`: PASS, with existing CRLF normalization warnings only
- `git diff --cached --check`: PASS

## Next

Recommended Loop 3:

`Candidate Detail v0` scaffold-only fixture-backed assembly.
