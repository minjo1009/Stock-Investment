# Task3839 Loop 6 Story Coverage Regression

## Decision Summary

Loop 6 adds a narrow story coverage validator for the Task3836 regression-critical components: `Badge` and `StatusRow`.

## Scope

- Verify `badge.stories.tsx` exists.
- Verify `status-row.stories.tsx` exists.
- Verify each story file includes required state exports.

## Non-Goals

- No screenshot capture.
- No visual approval.
- No Storybook runtime rewrite.
- No package install.
- No route, fixture, DB, runtime, broker, paper/live, deployment, or real-capital change.

## Validation

Run from `apps/ios-trader-brain`:

```bash
npm run validate:story-coverage
```

Expected output:

```text
[STORY_COVERAGE_OK]
```
