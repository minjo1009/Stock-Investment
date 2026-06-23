# Task3839 Loop 4 Compact Source Reference Presentation

## Decision Summary

Loop 4 reduces P2 vertical density in governance/status rows by making long `StatusRow` value and source-reference text single-line with middle ellipsis.

This is a bounded `StatusRow`-only patch.

## Behavior

- `value` remains visible.
- `sourceRef` remains visible.
- Long paths preserve beginning and end context through middle ellipsis.
- No tap, modal, tooltip, bottom sheet, or hidden expansion path was added.

## Files Changed

- `apps/ios-trader-brain/src/components/generic/status-row.tsx`

## Non-Goals

- No new generic component.
- No fixture change.
- No read-model change.
- No route change.
- No backend/runtime/DB/broker integration.
- No visual approval or readiness claim.

## Safety Boundary

Strategy remains `NOT_ACCEPTED`.

Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

Real capital remains `FORBIDDEN`.
