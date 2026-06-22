# Task Frontend Implementation Preconditions Contract

## Decision Summary

- Verdict: `FRONTEND_IMPLEMENTATION_PRECONDITIONS_CONTRACT_DOCS_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

Task3803 defines the implementation preconditions required before Storybook setup, foundation components, or screen implementation.

No app scaffold, UI screen, source code, DB row, scheduler, broker API, order path, replay, paper run, live run, deployment command, or real-capital state was changed.

## Done

- Fixed the reserved frontend app root as `apps/ios-trader-brain`.
- Recorded that no tracked `apps/` scaffold exists yet.
- Marked package manager, Expo Development Build, Storybook, typecheck, lint, tests, screenshot QA, Maestro, and frontend safety validator commands as `REQUIRED_PRE_SCAFFOLD_DECISION`.
- Defined reserved fixture paths under `apps/ios-trader-brain/src/mocks/fixtures/`.
- Mapped fixture paths to `08_FRONTEND_READ_MODEL_CONTRACT.md` view models.
- Defined required P0 components before screens.
- Defined Storybook required components and states.
- Defined screenshot QA device/screen scope.
- Defined frontend safety validator preconditions and forbidden/allowed action language.
- Added implementation start gate conditions.

## Failed

- No runnable frontend command could be finalized because the app scaffold does not exist yet.
- No safety validator command could be finalized because the validator has not been created yet.
- No fixture files were created because the read-model source path has not been selected yet.

## Validation

- `python scripts/task_registry_validate.py`

## Remaining Blockers

- Create `apps/ios-trader-brain` scaffold in a future task.
- Select package manager and lockfile policy.
- Select primary read path: generated JSON catalog, read-only runtime API, or read-only SQLite export.
- Create read-model fixtures from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
- Create frontend safety validator before screens expand.
- Prove Storybook and screenshot QA commands after scaffold exists.

## Next Task Recommendation

Task3804 should be `Expo App Scaffold + Storybook Setup`.

Task3804 must still avoid broker/API/paper/live/deployment/real-capital paths and must not implement trading screens before the foundation component contracts are present.

## Artifact Manifest

See `artifact_manifest.csv`.

