# Frontend App SSOT

## Authority

This pack is the current frontend/app planning authority for future implementation work.
It does not grant strategy acceptance, paper permission, deployment readiness, broker mutation, live order permission, or real-capital permission.

Standing project status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Frontend mode: read-only L7 observation surface

## Active Target

The active frontend target is an Expo Development Build, iOS-first mobile app.

The near-term operator preview target is mobile-web-first phone preview because
the project currently has no paid Apple Developer Program and no Mac operator
path. This does not replace the later native iOS app path; it only defines the
current phone-visible implementation route.

The app must preserve:

- `decision -> reason/thesis -> evidence -> source`
- explicit source freshness
- blockers and missing evidence
- provenance for decision-support content
- read-only controls unless a future operating-state document changes permission

## Supersession

The prior React plus TypeScript web architecture pack is retained as design input only.
It is not the active implementation stack.

The prior Expo Go 3052 DOM cockpit is retained as historical UI evidence and migration reference only.
It is not the final route authority.

The mobile web preview path is governed by `23_MOBILE_WEB_PWA_BOUNDARY.md`.

Backtest, paper, and live are lifecycle states. They are not top-level navigation tabs.
