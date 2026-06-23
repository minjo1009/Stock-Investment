# Mobile Viewport Visual QA Runbook

## Scope

Web Preview Evidence Only.

This runbook defines the web-preview viewport capture matrix for the read-only
mobile frontend. It is Not Native Evidence and Not Deployment Evidence.

## Viewports

- 390x844
- 393x852
- 430x932

## Routes

- HOME: `/`
- BRAIN: `/brain`
- PORTFOLIO: `/portfolio`
- ORDERS: `/orders`
- SYSTEM: `/system`
- Candidate Detail: `/brain/candidate/fixture-candidate-review`
- Chain Detail: `/brain/chain/fixture-chain`
- Position Detail: `/portfolio/position/fixture-position-unknown`
- Order Detail: `/orders/fixture-order-blocked`

## Boundary Checklist

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No paper/live permission.
- Missing, stale, and unknown states remain visible.
