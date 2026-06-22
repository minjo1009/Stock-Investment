# Active Frontend Target And Stack Decision

## Decision

Active target: Expo Development Build, iOS-first mobile app.

## Stack

| Layer | Current decision |
| --- | --- |
| Runtime | Expo Development Build |
| Platform priority | iOS first |
| Navigation | Expo Router |
| UI language | React Native plus TypeScript |
| Styling | NativeWind |
| Component base | React Native Reusables where practical |
| Micro charts | Skia |
| Main charts | TradingView Lightweight Charts through WebView when required |
| Component isolation | Storybook |
| Visual QA | screenshot checklist plus device/emulator captures |

## Backend Boundary

The frontend reads backend-generated read models, catalogs, and API responses.
It must not write to the active DB directly.
It must not call broker APIs.
It must not create or submit orders.
It must not infer permissions from paper-looking, live-looking, or successful-test states.

## Non-Active Inputs

React web, Next.js, Kubernetes, AWS, Cypress, Playwright, and the 3052 DOM cockpit are not active stack requirements unless a future operating document explicitly reauthorizes them.

