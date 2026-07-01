# TASK-4113 Root Capture Artifact Cleanup

## Goal

Remove unreferenced root-level capture PNG artifacts from `data/artifacts`
without deleting operational JSON state, ledgers, or task-scoped evidence.

## Results

- Searched docs/code references for the root capture filenames.
- Found no references in docs, ops, apps, src, scripts, or tests.
- Deleted 21 root-level PNG capture files.
- Removed 2,447,394 bytes.
- Kept root operational JSON files:
  - `gdelt_access_block_state.json`
  - `sec_live_access_block_state.json`
  - `marketaux_usage_ledger.json`

## Safety Boundary Check

- Broker mutation: none.
- Live order: none.
- Paper promotion: none.
- Real capital: none.
- DB schema: none.
- Scheduler code: none.
- Strategy acceptance: unchanged.

## Known Limitation

This task only cleaned root-level capture PNG files. Task-scoped screenshot
directories that are still referenced by current operating docs were retained.
