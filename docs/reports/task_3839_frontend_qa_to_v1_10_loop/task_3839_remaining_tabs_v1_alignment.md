# Task3839 Loop 10 Remaining Tabs v1 Alignment

## Decision Summary

Loop 10 performs minimal v1 alignment for PORTFOLIO, ORDERS, and SYSTEM.

This is not a broad bundle refactor.

## Changes

- PORTFOLIO header badge now reads `PORTFOLIO v1`.
- PORTFOLIO shows summary and position rows before the full Governance Boundary detail section.
- ORDERS header badge now reads `ORDERS v1`.
- ORDERS shows lifecycle summary and order rows before the full Governance Boundary detail section.
- SYSTEM header badge now reads `SYSTEM v1`; its operating boundary remains first because control state and kill switch are the core system summary.

## Non-Goals

- No broker sync.
- No order handler.
- No DB/runtime data.
- No new fixture/read-model/component/validator/route.
- No ready/approved/accepted/eligible wording.

## Safety Boundary

All tabs remain scaffold-only, fixture-backed, `NOT_AUTHORITY`, and read-only.
