# Task3895 - Brain Tab V5 Production Spec

## Summary

Task3895 applies the user-provided Brain tab v5 product specification to the read-only Expo frontend.

The Brain surface now prioritizes a user-facing investment interpretation flow:

1. today's issue,
2. latest news and Brain interpretation,
3. cause-and-effect relation map,
4. candidate slider,
5. risk summary,
6. lower supporting source/governance status.

Candidate detail now follows the requested L2-L5 flow: interpretation, evidence, risk factors, and response. The existing chain detail route is reshaped as a source/evidence detail page with metadata, summary, key points, Brain interpretation, and original-text placeholder.

The frontend remains fixture-backed, read-only, and `NOT_AUTHORITY`.

## Implemented

- Replaced the old Brain queue-first tab with a Brain v5 card-based IA.
- Added a compact top bar with title, update time, search placeholder, and settings placeholder.
- Added the today's issue card with theme, one-line interpretation, conviction gauge, and status badge.
- Added three latest-news cards with source, publication timing, summary, Brain interpretation, and evidence-detail links.
- Added horizontal cause-and-effect relation cards.
- Added horizontal candidate cards with state, conviction gauge, main risk, and next response.
- Added a risk summary section using plain Korean copy.
- Moved source freshness, governance, NOT_AUTHORITY, strategy, and real-capital state into a lower supporting section.
- Reworked candidate detail into the requested "지금의 생각 -> 해석 -> 근거 -> 위험 요인 -> 대응" flow.
- Reworked chain detail into a source/evidence detail page with summary, key points, Brain interpretation, and original-text placeholder.
- Updated validators so Brain v5 is validated by product IA, mobile scan/list, and detail hierarchy checks.

## Deferred

- Real news/IR source connection is not attached.
- Real Brain interpretation from backend runtime is not attached.
- Lv2/Lv3 route params remain display context only and do not select authoritative backend rows.
- Relation-map infinite looping, native swipe animation, haptics, source-document copy, external URL opening, and persisted collapse state are deferred.
- Response buttons are display-only and disabled; no trading journal write or system log mutation was added.
- No broker mutation, paper/live permission, strategy acceptance, deployment readiness, native iOS evidence, or real-capital permission changed.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:routes`
- `cd apps/ios-trader-brain && npm run validate:screen-boundary`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:mobile-scan-list-v1`
- `cd apps/ios-trader-brain && npm run validate:detail-v1`
- `cd apps/ios-trader-brain && npm run validate:frontend-governance`
- `cd apps/ios-trader-brain && npm run lint`

## Visual Evidence

No new screenshot artifact was captured in this slice because the local environment does not currently include Playwright/browser screenshot tooling in the project dependencies. This is a documentation gap only; it is not native iOS evidence and does not affect trading authority.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
