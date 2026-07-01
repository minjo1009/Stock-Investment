# NativeWind Deferral Revalidation

## Purpose

Revalidate the styling-tool decision before product screen implementation.

This document does not install NativeWind, edit package/config files, or migrate components.

## Current Status

NativeWind remains `DEFERRED_WITH_REASON_TASK3806`.

## Non-Authorization Rule

NativeWind revalidation does not authorize package installation, Metro/Babel/Tailwind/CSS config changes, product screens, deployment readiness, or trading permission.

## Current Styling Path

- tokenized React Native style props
- shared design tokens
- Storybook web-vite compatible component isolation
- no NativeWind dependency
- no Tailwind/className runtime contract yet

## Current Runtime / Build Context

- Expo SDK 56
- Expo Router
- React Native 0.85.3
- TypeScript
- Storybook web-vite
- iOS-first target
- Expo Development Build target
- iOS dev build command still intentionally blocked
- product screens not implemented

## Deferral Decision

Decision: `KEEP_NATIVEWIND_DEFERRED_WITH_REASON_TASK3806_REVALIDATED_LOOP9`.

Rationale: current token/style-prop path is sufficient for the scaffold and Storybook-covered component contracts. No product screen has proven className/Tailwind necessity. Installing NativeWind now would expand package/config/runtime surface before screenshot QA, Maestro preflight, iOS dev build validation, and screen implementation authorization.

## Reasons To Keep Deferred

1. No product screens exist yet.
2. Current P0 components are props-only and can render with style props.
3. Storybook web-vite stability is already part of QA baseline.
4. iOS dev build remains unvalidated.
5. Screenshot QA and Maestro remain preflight/planning paths.
6. NativeWind would add package/config/runtime surface area.
7. Current docs do not prove Tailwind/className is required.
8. Styling migration before screen architecture creates avoidable churn.

## Future Installation Trigger Conditions

NativeWind may be reconsidered only if a future implementation loop explicitly selects it, product screen implementation proves style props materially block consistency or velocity, Storybook web-vite compatibility is verified, Expo SDK 56 / Expo Router / React Native compatibility is verified, config changes are documented, typecheck/lint/test/storybook smoke pass after install, iOS development build evidence is recorded or explicitly blocked for unrelated reasons, rollback plan exists, and no trading/deployment/broker permission changes are introduced.

## Required Evidence Before Installation

- official install path reviewed
- dependency versions pinned
- config files listed
- Storybook web-vite proof
- Expo start proof
- typecheck proof
- lint proof
- Storybook smoke proof
- safety validator proof
- fixture validator proof
- rollback diff plan

## Failure Criteria

This revalidation fails if NativeWind is installed, package/config files are edited, components are migrated to `className`, Storybook config is changed, product screens are implemented, NativeWind is described as required without evidence, or DB/runtime/broker/KIS/Alpaca connections are added.

## Forbidden Claims

NativeWind deferral revalidation does not prove product screen readiness, HOME implementation authorization, Candidate Detail implementation authorization, iOS dev build readiness, deployment readiness, strategy acceptance, paper readiness, live readiness, broker readiness, real-capital permission, or UI quality acceptance.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, package install, config edit, component migration, or product screen implementation is authorized.
