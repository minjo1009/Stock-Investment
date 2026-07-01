# Mobile Web / PWA Boundary

## Authority

This document defines the current phone-visible preview path for the frontend app.
It does not grant strategy acceptance, paper permission, deployment readiness,
broker mutation, live order permission, or real-capital permission.

Standing project status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Frontend mode: read-only diagnostic observation surface

## Current Target

The current near-term target is mobile-web-first phone preview through Expo web.
The later native iOS development build and App Store path remains preserved, but
it is not the active implementation dependency while the project has no paid
Apple Developer Program and no Mac operator path.

## Allowed Now

- Expo web development preview.
- Static web export validation.
- iPhone Safari LAN preview.
- Safari Share -> Add to Home Screen.
- Read-only placeholder, fixture, and source-attached frontend views.
- Unknown, stale, and missing states rendered as `UNKNOWN` or `BLOCKER`.

## Forbidden Now

- Broker mutation.
- KIS or Alpaca connection from frontend.
- Direct active `trading.db` access from frontend.
- Runtime API connection from frontend.
- Paper/live order creation.
- Paper promotion.
- Deployment readiness claim.
- Real-capital permission.
- Service worker caching until an explicit stale-data and cache-update policy exists.

## Implementation Contract

Mobile web appification must include:

- A web app manifest.
- iOS home-screen metadata.
- Phone viewport targets.
- A runbook for local phone preview.
- A fail-closed validator that preserves read-only governance.

Mobile web appification must not infer readiness from a passing build, screenshot,
storybook story, or visual polish.
