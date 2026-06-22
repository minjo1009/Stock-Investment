# Task3481-3485 Runtime Atomicity Preconditions

## Decision Summary

- Verdict: `PRECONDITIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - scheduler lease tests: 2
  - runtime authority contract tests: 7
  - broker calls: 0
  - paper orders: 0
  - live orders: 0
- What changed: implemented the professional backend preconditions found during review before building the full scheduler, single authority adapter, or broker submit state machine.
- Next action: implement Task3486-3500 full diagnostic scheduler using the lease functions added here.

## Quant Expert Report

### Objective

Close the P0/P1 gaps found during professional backend re-review of the Task3481-3530 plan:

1. scheduler lease atomicity was underspecified
2. `PAPER_ELIGIBLE` authority evidence was underspecified
3. broker submit idempotency did not account for a broker API without client order id support
4. SQLite runtime writes lacked explicit concurrency defaults

### Implementation

Code changes:

- `src/state/store.py`
  - strengthened `_connect()` with `timeout=30`, `foreign_keys=ON`, `busy_timeout=5000`, and best-effort WAL
  - added `scheduler_leases`
  - added `acquire_scheduler_lease()`
  - added `heartbeat_scheduler_lease()`
  - added `release_scheduler_lease()`
  - added `get_scheduler_lease()`
- `src/brain/runtime_authority.py`
  - added `RuntimeSnapshotRefs`
  - added `RuntimeLineageHashes`
  - added `RuntimeAuthorityEvidence`
  - added `RuntimeAuthorityResult`
  - added `BrokerSubmitIdempotencyPlan`
  - added `validate_runtime_authority()`
- `src/brain/__init__.py`
  - exported the new authority contract surface
- `tests/test_scheduler_lease_atomicity.py`
  - verifies active lease ownership, expiry steal, token-gated heartbeat, and token-gated release
- `tests/test_runtime_authority_contract.py`
  - verifies shadow-only cannot grant orders, expired decisions block, `PAPER_ELIGIBLE` requires complete evidence, all kill-switch levels are required, and broker idempotency is explicit

### Contract Decisions

Scheduler lease contract:

- one `lease_key` owns one cadence/bucket execution slot
- acquire uses `BEGIN IMMEDIATE`
- active non-expired lease blocks another owner
- expired or released lease may be stolen
- heartbeat and release require the matching `lease_token`

Runtime authority evidence contract:

- `RuntimeDecision` alone is not enough to create paper order permission
- authority evidence must carry L3/L4/L5/L6 lineage hashes
- authority evidence must carry market/economic/universe/policy snapshot ids
- authority evidence must carry `valid_from` and `valid_until`
- all kill-switch levels must be checked
- `PAPER_ELIGIBLE` requires full evidence:
  - `SOURCE_FRESHNESS_OK`
  - `SNAPSHOT_VERSIONED`
  - `LINEAGE_HASH_MATCHED`
  - `BROKER_TRUTH_REVIEWED`
  - `KILL_SWITCH_CLEAR`
  - `PAPER_PERMISSION_EXPLICIT`
  - broker truth refs
  - source quality refs

Broker idempotency contract:

- when the broker supports client order ids, broker client id must equal local idempotency key
- when the broker does not support client order ids, reconciliation before retry is mandatory
- this closes the earlier gap where local `client_order_id` existed but was not guaranteed to reach the KIS API payload

### Validation

Commands run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_scheduler_lease_atomicity tests.test_runtime_authority_contract
```

Result:

```text
Ran 9 tests
OK
```

## No-Background Decision-Maker Report

- What happened: the plan was hardened into actual backend contracts.
- Why it matters: duplicate scheduler owners, stale runtime decisions, incomplete paper eligibility, and broker retry duplication are now testable failure modes.
- What it does not do: it does not install a scheduler, submit a broker order, grant paper eligibility, or change deployment status.
- Plain-language next step: build the dry-run scheduler on top of the lease API, then wire single L6 authority, then order intent atomicity.

## Artifact Manifest

- Inputs:
  - `docs/reports/task_3481_3530_runtime_scheduler_authority_atomicity_plan/task_3481_3530_runtime_scheduler_authority_atomicity_plan.md`
  - `src/state/store.py`
  - `src/brain/contracts.py`
  - professional backend re-review findings from the current Codex thread
- Outputs:
  - `src/brain/runtime_authority.py`
  - `tests/test_scheduler_lease_atomicity.py`
  - `tests/test_runtime_authority_contract.py`
  - `docs/reports/task_3481_3485_runtime_atomicity_preconditions/task_3481_3485_runtime_atomicity_preconditions.md`
  - `docs/reports/task_3481_3485_runtime_atomicity_preconditions/task_3485_decision.csv`
  - `data/artifacts/task_3481_3485_runtime_atomicity_preconditions/artifact_manifest.md`
  - `scripts/trader_brain_3481_3485_runtime_atomicity_preconditions_validate.py`
- Validation commands:
  - `$env:PYTHONPATH='src'; python -m unittest tests.test_scheduler_lease_atomicity tests.test_runtime_authority_contract`
  - `python scripts/trader_brain_3481_3485_runtime_atomicity_preconditions_validate.py`
  - `python scripts/task_registry_validate.py`
  - `python scripts/operating_closeout_validate.py`
- Source hashes: not applicable. No source data was transformed.

Final footer:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
