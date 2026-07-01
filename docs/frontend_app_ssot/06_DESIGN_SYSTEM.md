# Design System

## Principles

The app is an operational quant cockpit, not a marketing surface.
It should be dense, calm, scannable, and evidence-forward.

## Token Groups

| Token group | Required use |
| --- | --- |
| Color | status, source freshness, risk severity, disabled controls |
| Type | numeric scan rows, section titles, compact evidence labels |
| Spacing | 4 px rhythm, stable list rows, compact mobile cards |
| Radius | 8 px or less unless native platform conventions require otherwise |
| Elevation | minimal; avoid nested card stacks |
| Motion | optional and non-authoritative |

## Status Color Semantics

Status colors must never imply strategy acceptance, paper permission, deployment readiness, or real-capital permission.

`STALE`, `UNKNOWN`, `BLOCKED`, `SOURCE_NOT_ATTACHED`, and `CHART_MISSING` must be visible states, not hidden fallbacks.

## Chart Rule

Charts must show source attachment or explicit absence.
Synthetic OHLC/VWAP fallback charts are not allowed for decision-support display.

