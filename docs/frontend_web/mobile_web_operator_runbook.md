# Mobile Web Operator Runbook

## Status

- Target: mobile-web-first phone optimized read-only cockpit.
- Native iOS app/dev-client path: preserved for later.
- Apple Developer Program: not required for this near-term path.
- Mac: not required for this near-term path.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Broker mutation: forbidden.
- Paper/live permission: forbidden.

## Local Phone Preview

From `apps/ios-trader-brain`:

```bash
npm run web:mobile
```

Use the LAN URL printed by Expo and open it in mobile Safari on an iPhone connected to the same network.

## Home Screen Install

1. Open the LAN URL in Safari.
2. Tap Share.
3. Choose Safari Share -> Add to Home Screen.
4. Launch Trader Brain from the home screen.

This is a mobile web shell, not an App Store app, not an EAS internal build, and not deployment readiness.

## Safety Boundaries

- No broker mutation.
- No live order.
- No paper promotion.
- No real-capital permission.
- No direct active `trading.db` access from frontend.
- Missing, stale, and unknown data must remain visible as `UNKNOWN` or `BLOCKER`.

## Deferred Items

- Service worker is `DEFERRED_WITH_REASON_AGGRESSIVE_CACHE_RISK`.
- Screenshot QA for the mobile viewport matrix is required next.
- iOS dev-client build remains operator-gated until Apple/EAS/provisioning evidence exists.
