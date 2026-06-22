# Task3486-3500 Runtime Idempotency Authority Observability

## Decision Summary

- Verdict: `RUNTIME_SAFETY_CONNECTIONS_IMPLEMENTED_PROMOTION_STILL_BLOCKED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - targeted runtime safety tests: 41
  - GPT review-only findings recorded: 10
  - broker calls: 0
  - paper orders: 0
  - live orders: 0
- What changed: connected the precondition contracts to actual runtime code paths for KIS idempotency, durable paper intents, RuntimeDecision authority fields, scheduler fencing, authority evidence immutability, reconciliation resolution, and operating metrics.
- Next action: build the dry-run diagnostic scheduler on top of these contracts, then complete the single-authority execution adapter.

## Quant Expert Report

### Objective

Complete the five professional backend gaps raised by review:

1. KIS order idempotency was not connected to the broker submit path.
2. Scheduler lease semantics needed concrete atomic acquire, TTL, fencing, stale steal, and token validation.
3. `PAPER_ELIGIBLE` evidence gates were underspecified.
4. `RuntimeDecision` lacked direct validity/snapshot/lineage fields.
5. Runtime observability lacked UNKNOWN, reconciliation, heartbeat, and intent metrics.

### Implementation

KIS idempotency and durable order intent:

- `src/integration/kis_client.py`
  - `submit_order()` and `submit_order_with_response()` now accept `idempotency_key`, `broker_client_order_id`, and `reconciliation_before_retry_required`.
  - current KIS client declares `supports_client_order_id() == False`.
  - passing `broker_client_order_id` now raises `KIS_CLIENT_ORDER_ID_UNSUPPORTED`.
  - local idempotency metadata is preserved in the returned response without sending an unsupported payload field.
- `src/app/task_585_kis_paper_order_execution.py`
  - creates durable `paper_order_intents` before broker submit.
  - transitions `CREATED -> SUBMITTING` before KIS submit.
  - transitions `SUBMITTING -> SUBMITTED_LOCAL_RECORDED` after local order record succeeds.
  - transitions `SUBMITTING -> UNKNOWN` when broker submit succeeds but local record fails.
  - blocks duplicate retry when an existing non-CREATED intent is found.
  - active order blocker now includes `UNKNOWN`.

Scheduler lease and fencing:

- `src/state/store.py`
  - strengthened SQLite connection defaults with timeout, busy timeout, foreign keys, and best-effort WAL.
  - `scheduler_leases` stores `lease_key`, `owner_id`, `lease_token`, `heartbeat_at`, `expires_at`, `released_at`, and `status`.
  - acquire uses `BEGIN IMMEDIATE`.
  - active non-expired owner blocks other owners.
  - expired or released lease can be stolen.
  - heartbeat/release require matching token.
  - `validate_scheduler_lease_token()` rejects stale workers before later state-changing writes.

Runtime authority and evidence immutability:

- `src/brain/contracts.py`
  - `RuntimeDecision` now has `valid_from`, `valid_until`, `snapshot_refs`, and `lineage_hash`.
  - these fields are mandatory for `PAPER_ELIGIBLE` or `paper_order_intent_allowed`.
- `src/brain/runtime_authority.py`
  - authority evidence requires L3/L4/L5/L6 lineage hashes.
  - authority evidence requires market/economic/universe/policy snapshot ids.
  - authority evidence requires valid windows and all kill-switch levels.
  - `PAPER_ELIGIBLE` requires source freshness, snapshot versioning, lineage match, broker truth review, kill-switch clear, explicit paper permission, broker truth refs, and source quality refs.
- `src/state/store.py`
  - added append-only `runtime_authority_evidence_ledger`.
  - duplicate same-hash/same-payload insert is idempotent.
  - same-hash/different-payload mutation raises.

Reconciliation and observability:

- `resolve_paper_order_intent_after_reconciliation()` deterministically moves UNKNOWN or local-recorded intents to `RECONCILED` or `BLOCKED`.
- `list_runtime_operating_metrics()` reports:
  - `unknown_order_count`
  - `oldest_unknown_order_age_minutes`
  - `reconciliation_block_count`
  - `paper_order_intent_state_counts`
  - `heartbeat_status_counts`
  - `latest_heartbeat_lag_minutes`

### GPT Review-Only Result

GPT/Chrome review-only found the implementation materially stronger, then raised remaining review items:

- P0 UNKNOWN-state lifecycle and reconciliation guarantees
- P0 crash-consistency proof around submit boundaries
- P0 authority evidence tamper-resistance
- P1 lease fencing across external side effects
- P1 broker reconciliation source-of-truth hierarchy
- P1 idempotency retention horizon
- P1 execution-time freshness enforcement
- P1 scheduler lease chaos testing
- P1 operational kill-switch verification
- P1 recovery playbook encoding

Disposition:

- The first four were converted into code/tests in this task.
- Freshness enforcement is covered by `validate_runtime_authority()`.
- Broker reconciliation hierarchy, retention cleanup policy, scheduler chaos tests, and machine-verifiable recovery playbook remain next scheduler/atomic-submit work, not promotion blockers closed by this task.

### Validation

Commands run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_kis_client_idempotency_contract tests.test_scheduler_lease_atomicity tests.test_runtime_authority_contract tests.test_runtime_diagnostic_ledger tests.test_task585_kis_paper_order_execution tests.test_brain_runtime_contracts tests.test_brain_runtime_decision_adapter
python scripts/trader_brain_3486_3500_runtime_idempotency_authority_observability_validate.py
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
```

Result:

```text
Ran 41 tests
OK
```

## No-Background Decision-Maker Report

- What happened: the unsafe gaps are now wired into code paths, not just described in a plan.
- Why it matters: duplicate broker submit, stale scheduler ownership, incomplete paper eligibility, stale runtime decisions, and invisible UNKNOWN orders are now testable failure modes.
- What still does not change: no scheduler was installed, no broker order was sent, no paper permission was granted, no live trading was enabled.
- Plain-language next step: implement the dry-run scheduler and single-authority execution adapter using these contracts.

## Artifact Manifest

- Inputs:
  - `docs/reports/task_3481_3485_runtime_atomicity_preconditions/task_3481_3485_runtime_atomicity_preconditions.md`
  - `src/state/store.py`
  - `src/brain/contracts.py`
  - `src/brain/runtime_authority.py`
  - `src/integration/kis_client.py`
  - `src/app/task_585_kis_paper_order_execution.py`
  - GPT/Chrome review-only response
- Outputs:
  - `tests/test_kis_client_idempotency_contract.py`
  - updated `tests/test_scheduler_lease_atomicity.py`
  - updated `tests/test_runtime_authority_contract.py`
  - updated `tests/test_runtime_diagnostic_ledger.py`
  - updated `tests/test_task585_kis_paper_order_execution.py`
  - `data/artifacts/task_3486_3500_runtime_idempotency_authority_observability/gpt_review_findings.csv`
  - `data/artifacts/task_3486_3500_runtime_idempotency_authority_observability/artifact_manifest.md`
  - `docs/reports/task_3486_3500_runtime_idempotency_authority_observability/task_3486_3500_runtime_idempotency_authority_observability.md`
  - `docs/reports/task_3486_3500_runtime_idempotency_authority_observability/task_3500_decision.csv`
  - `scripts/trader_brain_3486_3500_runtime_idempotency_authority_observability_validate.py`
- Validation commands:
  - `$env:PYTHONPATH='src'; python -m unittest tests.test_kis_client_idempotency_contract tests.test_scheduler_lease_atomicity tests.test_runtime_authority_contract tests.test_runtime_diagnostic_ledger tests.test_task585_kis_paper_order_execution tests.test_brain_runtime_contracts tests.test_brain_runtime_decision_adapter`
  - `python scripts/trader_brain_3486_3500_runtime_idempotency_authority_observability_validate.py`
  - `python scripts/task_registry_validate.py`
  - `python scripts/operating_closeout_validate.py`
- Source hashes: not applicable. No source data was transformed.

Final footer:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
