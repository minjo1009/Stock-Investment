# Implementation Architecture

## Active Target

Future frontend implementation should target an Expo Development Build, iOS-first app.

The preferred implementation path is `apps/ios-trader-brain` unless a future task report selects a different path.

## Suggested Structure

```text
apps/ios-trader-brain/
  app/
  src/
    components/
    features/
      home/
      brain/
      portfolio/
      orders/
      system/
    read-models/
    services/
    theme/
    qa/
    stories/
```

## Backend Integration

The app consumes read-only catalogs, generated read models, or API endpoints produced by the Python/DB backend.

The app must not:

- open write connections to `trading.db`
- call KIS, Alpaca, or any broker mutation endpoint
- create live orders
- create real-capital permissions
- treat validator success as strategy acceptance

## P0 Implementation Preconditions

Before code implementation expands, the implementation task must name:

- the exact frontend app path
- the read-model source paths or API endpoints
- the disabled action contract
- the Storybook and screenshot QA commands
- the no-live-order/no-broker-mutation validator

Task3803 records these preconditions in `docs/frontend_app_ssot/11_IMPLEMENTATION_PRECONDITIONS.md`.
