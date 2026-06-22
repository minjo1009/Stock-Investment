# Disabled Action And Order Control Contract

## Current Rule

All trading mutation controls are disabled under current governance.

Disabled controls include:

- approve
- reject as trading authority
- cancel order
- execute
- submit
- paper promote
- live promote
- broker sync mutation
- real-capital action

## Required UX

Disabled controls must show the governance reason:

- strategy acceptance is `NOT_ACCEPTED`
- deployment readiness is `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real capital is `FORBIDDEN`
- broker mutation is not permitted
- source gates may be stale or blocked
- kill switch/control state may block execution

## Engineering Rule

Disabled controls must not have hidden broker-submit or DB-write handlers.

If a handler is present for future implementation, it must fail closed and return a governance-blocked result without side effects.

