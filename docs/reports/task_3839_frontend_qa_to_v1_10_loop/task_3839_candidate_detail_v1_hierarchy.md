# Task3839 Loop 9 Candidate Detail v1 Hierarchy

## Decision Summary

Loop 9 promotes Candidate Detail from v0 to v1 hierarchy by reordering existing sections only.

## Change

- Candidate Detail header badge now reads `Candidate Detail v1`.
- Evidence now appears before validation status.
- Chain Trace is relabeled to Evidence Chain.
- Validation is wrapped under a `Validation Status` section with explicit non-acceptance copy.
- Next Action is relabeled to Review Actions.
- The full Scaffold Boundary remains visible at the bottom.

## Non-Goals

- No new field.
- No route-selection authority.
- No chart/business logic.
- No score, rank, confidence, readiness, acceptance, buy, or signal claim.
- No DB/runtime/broker integration.

## Safety Boundary

Candidate Detail remains scaffold-only, fixture-backed, `NOT_AUTHORITY`, and read-only.
