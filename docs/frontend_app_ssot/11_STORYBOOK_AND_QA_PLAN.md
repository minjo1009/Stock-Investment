# Storybook And QA Plan

## Storybook Coverage

Storybook must cover:

- five top-level IA tabs
- universal detail frame V2
- source freshness badges
- blocker states
- disabled action controls
- chart missing/source not attached states
- governance status panels

## Screenshot QA

Screenshot QA must capture:

- `HOME`
- `BRAIN`
- candidate detail
- `PORTFOLIO`
- position detail
- `ORDERS`
- order detail
- `SYSTEM`
- stale source state
- disabled action state

## Validator Targets

Frontend validation should include:

- no live order text or handlers that imply permission
- no broker mutation controls with active handlers
- no synthetic chart fallback for source-required charts
- required freshness and provenance fields visible
- backtest/paper/live not used as top-level tabs

