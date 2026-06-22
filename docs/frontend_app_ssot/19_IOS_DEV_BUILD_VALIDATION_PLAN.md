# iOS Development Build Validation Plan

## Purpose

Define a future iOS development build validation plan for the Expo Development Build iOS-first target.

This document does not run builds, install packages, add EAS/native config, or claim deployment readiness.

## Current Status

- iOS Development Build validation is not complete.
- `npm run ios:dev` is intentionally blocked by required-post-scaffold-hardening.
- No EAS/native build was run in this loop.
- No deployment readiness is implied.
- No product screen readiness is implied.

## Non-Authorization Rule

iOS dev build validation can prove only a selected development-build mode under documented environment evidence. It cannot prove deployment readiness, production readiness, App Store readiness, strategy acceptance, paper/live readiness, broker readiness, order execution permission, real-capital permission, backend/source truth, product screen readiness, screenshot QA pass, or Maestro pass.

## Current Expo / React Native Runtime Context

- Expo SDK: `~56.0.12`
- Expo Router: `~56.2.11`
- React: `19.2.3`
- React Native: `0.85.3`
- Storybook: `@storybook/react-native-web-vite`
- TypeScript: `~6.0.3`
- App root: `apps/ios-trader-brain`
- Main entry: `expo-router/entry`

## Current Command Contract

- `npm run ios` is Expo iOS simulator start, not validated on this Windows environment.
- `npm run ios:dev` is currently an intentional blocker and does not prove development build readiness.
- `npm run start` is Expo start and not a deployment claim.
- `npm run storybook` is Storybook web runtime, not on-device Storybook.

## Local iOS Simulator Boundary

Future local iOS simulator validation requires macOS, Xcode, an iOS simulator target, exact command evidence, and launch evidence. Absence of this environment is `BLOCKED`, not `FAIL`.

## EAS Development Build Boundary

Future EAS development build validation requires explicit future task selection, EAS config review, account/auth boundary recording, exact command evidence, and build artifact evidence. EAS validation is not deployment readiness.

## Future Environment Evidence Required

Future validation must record host OS, macOS version if local simulator is used, Xcode version, simulator device/version, Node/npm versions, Expo/EAS CLI versions if used, account boundary if applicable, selected build mode, exact command, start/end time, and success/failure/blocker reason.

## Future Command Evidence

Candidate command classes:

```text
cd apps/ios-trader-brain && npm run start
cd apps/ios-trader-brain && npm run ios
cd apps/ios-trader-brain && npm run ios:dev only after script is replaced by an approved implementation task
EAS development build command only after EAS config is explicitly added by a future task
```

## Build Artifact Naming Policy

```text
ios-dev-build-validation__<mode>__<device>__<host>__<yyyymmdd>.md
ios-dev-build-validation__<mode>__<device>__<host>__<yyyymmdd>__log.txt
ios-dev-build-validation__<mode>__<device>__<host>__<yyyymmdd>__manifest.csv
```

## Future Run Manifest Fields

`run_id,mode,host_os,macos_version,xcode_version,ios_simulator_device,ios_simulator_runtime,node_version,npm_version,expo_version,expo_router_version,react_native_version,eas_cli_version,command,started_at,completed_at,pass_fail_blocked,blocker_reason,artifact_paths,screenshots_attached,maestro_attached,storybook_attached,safety_validation_attached,fixture_validation_attached,reviewer,notes`

## Pass / Fail / Blocked Criteria

Future validation can pass only if environment and command are recorded, the app launches in the selected development-build mode, safety and fixture validators pass, artifacts/logs are stored, blockers are not hidden, and no deployment readiness is claimed.

Future validation fails if unauthorized build/config/script changes appear, launch requires DB/runtime/broker/KIS/Alpaca, live-order/paper-promote/real-capital affordances appear, safety/fixture validation fails, logs contain unaddressed runtime crash, or readiness claims are made.

Future validation is `BLOCKED`, not `FAIL`, if no macOS/Xcode/simulator environment exists, Apple Developer/EAS account access is unavailable, network/auth blocks EAS, command remains intentional blocker, environment metadata is missing, or native build path is not selected.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, build execution, EAS config, native folder generation, package edit, product screen implementation, or DB/runtime connection is authorized.
