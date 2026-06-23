# Task3839 Loop 7 HOME v1 Hierarchy

## Decision Summary

Loop 7 promotes HOME from v0 to v1 hierarchy by reordering existing sections only.

No new data, component, route, fixture, validator, DB/runtime connector, broker path, or action was added.

## Change

- The top compact boundary strip remains visible.
- Portfolio Snapshot now appears before the large Governance Boundary detail section.
- Brain Snapshot and Attention Queue remain above freshness/blocker/governance details.
- The full Governance Boundary remains visible before Disabled Actions.

## Safety Boundary

HOME remains scaffold-only, fixture-backed, `NOT_AUTHORITY`, and read-only.

Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.
