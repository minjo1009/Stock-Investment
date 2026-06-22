# Task3481-3530 Runtime Scheduler Authority Atomicity Plan

## Decision Summary

- Verdict: `PLAN_APPROVED_FOR_IMPLEMENTATION_NOT_PROMOTION`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - planned implementation lanes: 3
  - GPT/Chrome review-only findings incorporated: 6 P0, 5 P1
  - broker calls in this plan task: 0
  - paper orders in this plan task: 0
  - live orders in this plan task: 0
- What changed: planning artifacts only. No runtime code, scheduler install, replay, selector, sizing, source acquisition, paper order, broker mutation, live order, deployment claim, or real-capital permission changed.
- Next action: implement Task3481-3500 first, then Task3501-3520, then Task3521-3530.

## Quant Expert Report

### Objective

Convert the remaining runtime blockers into a concrete backend implementation program:

1. scheduler
2. single execution authority
3. order atomicity

GPT/Chrome review-only agreed the sequencing is sound, but added six P0 controls that must be included before any paper-runtime consideration:

- global state-machine specification
- decision lineage immutability
- scheduler singleton/lease ownership
- runtime snapshot consistency/versioning
- kill-switch hierarchy
- reconciliation authority/conflict model

### Implementation Program

| Range | Lane | Goal | Non-Negotiable Boundaries |
| --- | --- | --- | --- |
| Task3481-3500 | Full Diagnostic Scheduler | Build a dry-run scheduler module with event-driven, 5-minute safety, 10-minute changed-candidate brain, 30-minute heavy-source/reporting, and daily close buckets. | No scheduler install, no broker call, no paper order, no live order. |
| Task3501-3520 | Single Runtime Authority | Introduce a runtime authority adapter that accepts only latest L6 `RuntimeDecision` objects and blocks every legacy order-capable path by default. | Legacy Task583/584/585 cannot create execution permission. Env flags cannot bypass authority. |
| Task3521-3530 | Broker Submit Atomicity | Add durable `paper_order_intents` and recoverable submit state machine before any submit-capable path can advance. | No unattended broker submission; all submit paths remain diagnostic/paper gated. |

### Task3481-3500 Scheduler Plan

Build:

- `src/app/diagnostic_scheduler.py` or equivalent narrow module.
- Dry-run CLI only, for example `python -m src.app.diagnostic_scheduler --once --cadence safety`.
- Reuse `L0L6DiagnosticRuntimeState` and `diagnostic_runtime_heartbeats`.
- Add `scheduler_leases` or equivalent singleton lease table.
- Add state-machine spec artifact for scheduler ticks.

Cadence contracts:

- event-driven: source/broker/risk/freshness event only
- 5-minute safety: market/session/account/order/freshness only
- 10-minute brain: changed candidates only, requires L6 runtime refs
- 30-minute heavy-source/reporting: requires source receipt refs
- daily close: journal/reconciliation/blocker report only

Required tests:

- duplicate bucket skip
- restart idempotency
- lease prevents two owners executing one bucket
- stale/missing source skip
- non-paper environment block
- no KIS client calls
- 5-minute safety cannot run L3-L5 brain work
- 10-minute brain with no changed candidates skips
- 30-minute heavy-source with no source receipt skips

### Task3501-3520 Single Runtime Authority Plan

Build:

- `src/brain/runtime_authority.py` or equivalent adapter.
- Authority input: latest L6 `RuntimeDecision`.
- Authority output: `BLOCKED`, `SHADOW_ONLY`, or future `PAPER_ELIGIBLE` only when explicit evidence gates exist.
- Persist authority decision hash and lineage hash.

Must include:

- L3 `EconomicMeaning` hash
- L4 `ThesisBundle` hash
- L5 `PolicyAction` hash
- L6 `RuntimeDecision` hash
- snapshot ids: market data version, economic data version, universe version, policy version
- `valid_from` and `valid_until`
- kill-switch hierarchy: `GLOBAL_BLOCK`, `STRATEGY_BLOCK`, `SYMBOL_BLOCK`, `BROKER_BLOCK`, `SCHEDULER_BLOCK`

Required tests:

- legacy `PAPER_ORDER_CANDIDATE` blocked
- `RuntimeDecision` without paper permission blocked
- stale/expired `RuntimeDecision` blocked
- lineage hash mismatch blocked
- read-only frontend model cannot grant execution
- env flags cannot bypass authority
- every kill-switch level blocks authority

### Task3521-3530 Broker Submit Atomicity Plan

Build:

- durable `paper_order_intents` table
- append-only order event ledger
- explicit submit state machine:

```text
CREATED -> AUTHORIZED -> SUBMITTING -> SUBMITTED_LOCAL_RECORDED -> RECONCILED
CREATED -> BLOCKED
SUBMITTING -> UNKNOWN
UNKNOWN -> RECONCILED
UNKNOWN -> BLOCKED
```

Every transition must be versioned and audited. Impossible transitions must raise.

Submit requirements:

- existing authorized intent
- runtime decision id
- authority token/id
- lineage hash
- idempotency key
- kill-switch check
- scheduler lease/tick reference

Recovery requirements:

- `SUBMITTING` blocks duplicate submits
- `UNKNOWN` blocks duplicate submits
- broker says filled/local says submitted has deterministic conflict rule
- broker says not found/local says submitted has deterministic conflict rule
- reconciliation writes `broker_state`, `local_state`, and `resolution_state`

Required tests:

- submit succeeds but local write fails, retry does not duplicate
- broker timeout leaves `UNKNOWN` blocking
- duplicate intent same state skipped
- impossible transition rejected
- live env blocked
- kill-switch cannot be overridden
- reconciliation conflict resolution deterministic

### GPT/Chrome Review-Only Result

GPT/Chrome review-only found the 3-lane sequencing sound:

1. deterministic orchestration
2. single decision authority
3. execution durability/atomicity

It also added the following minimum P0 set before paper-runtime consideration:

- formal global state-machine specification
- immutable decision lineage hashes
- scheduler singleton/lease ownership
- runtime snapshot consistency/versioning
- hierarchical kill-switches
- explicit reconciliation authority/conflict model

It added P1 controls:

- append-only event sourcing/audit ledger
- RuntimeDecision expiration
- explicit data quality gates
- replayability from persisted events
- authority proof carried through every execution boundary

These findings are review-only and not source-of-truth.

### Completion Criteria For The Program

The program is complete only when:

- Task3481-3500, Task3501-3520, and Task3521-3530 each have reports, manifests, registry rows, and validators.
- Every order-capable path requires latest L6 authority proof.
- Every scheduler tick is lease-protected and idempotent.
- Every order intent transition is durable and replayable.
- Negative-path tests pass for missing state, stale state, duplicate tick, duplicate intent, broker timeout, partial local write, kill-switch, non-paper env, and lineage mismatch.

PASS still does not mean:

- strategy accepted
- deployment ready
- broker truth complete
- source complete
- paper/live trading approved
- real capital allowed

## No-Background Decision-Maker Report

- What happened: the next work is now a concrete 3-lane backend program, not a vague “make runtime better” request.
- Why it matters: the scheduler must be deterministic, execution must have one authority, and broker submission must be recoverable before paper-runtime promotion can even be considered.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: implement the scheduler first, with lease and idempotency, then authority, then atomic submit.

## Artifact Manifest

- Inputs:
  - `docs/reports/task_3431_3480_runtime_promotion_blocker_hardening/task_3431_3480_runtime_promotion_blocker_hardening.md`
  - GPT/Chrome review-only response
  - `docs/llm_wiki/realtime_trading_operations.md`
  - `docs/operating_system/project_operating_state.md`
- Outputs:
  - `docs/reports/task_3481_3530_runtime_scheduler_authority_atomicity_plan/task_3481_3530_runtime_scheduler_authority_atomicity_plan.md`
  - `docs/reports/task_3481_3530_runtime_scheduler_authority_atomicity_plan/task_3530_decision.csv`
  - `data/artifacts/task_3481_3530_runtime_scheduler_authority_atomicity_plan/implementation_lanes.csv`
  - `data/artifacts/task_3481_3530_runtime_scheduler_authority_atomicity_plan/gpt_review_findings.csv`
  - `data/artifacts/task_3481_3530_runtime_scheduler_authority_atomicity_plan/artifact_manifest.md`
  - `scripts/trader_brain_3481_3530_runtime_scheduler_authority_atomicity_plan_validate.py`
- Row counts:
  - implementation lanes: 3
  - GPT review findings: 11
  - decision rows: 1
- Validation commands:
  - `python scripts/trader_brain_3481_3530_runtime_scheduler_authority_atomicity_plan_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes: not applicable. No source data was transformed.

Final footer:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
