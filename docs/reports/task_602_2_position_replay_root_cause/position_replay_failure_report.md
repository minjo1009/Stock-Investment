# T602-2 Position Replay Failure Report

## Problem

- Position Match is 0%, so replay acceptance fails even though Decision Match and Fill Match pass.

## Evidence

- 1. Missing Exit: affected=24; No broker-truth exit_order_id or exit_fill_id exists for open lifecycle rows.
- 2. Missing Fill Link: affected=24; Position Match requires exact fill lineage; exit fill linkage is blank.
- 3. Position Lifecycle Error: affected=24; T600-1 lifecycle has zero accepted CLOSED rows, so replay cannot score position closure.
- 4. Position Aggregation Error: affected=24; runtime positions table is symbol-level (3 rows) while lifecycle is position_id-level (24 rows).
- 5. Position Creation Failure: affected=0; Entry position creation exists for 24 rows; this is not the primary failure.

## Root Cause

- Missing Exit and Missing Fill Link dominate the failure.
- Symbol-level runtime position aggregation prevents one-to-one position_id replay comparison.

## Fix Candidate

- Create broker-truth exit fills, then reconcile symbol-level `positions` to position_id lifecycle rows.

## Acceptance Impact

- PASS_TOP5_ROOT_CAUSES_IDENTIFIED, but Replay Acceptance remains FAIL until Position Match reaches 99%.
