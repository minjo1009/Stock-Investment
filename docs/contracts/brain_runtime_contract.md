# Brain Runtime Contract

## Purpose

This contract fixes the handoff between the Trader Brain layers and the automated trading runtime.

It covers:

- L3 economic meaning and relation context
- L4 thesis bundle and invalidation state
- L5 policy/action output
- L6 runtime, paper/shadow, broker-truth gates
- L0-L6 diagnostic orchestration state hash and idempotency guard
- L7 frontend read model

This contract does not accept a strategy, permit deployment, or allow real capital.

## Layer Boundary

```text
L3 EconomicMeaning
-> L3 MeaningRelationEdge
-> L4 ThesisBundle
-> L5 PolicyAction
-> L6 RuntimeDecision
-> L7 FrontendReadModel
```

Rules:

- L3 may not emit orders, sizing, rank, or exits.
- L4 may not emit orders, sizing, rank, or exits.
- L5 may propose a policy action only under a named policy and evidence path.
- L6 owns runtime eligibility, paper/shadow gates, broker-truth gates, and order-intent permission.
- L7 is read-only and must show provenance and blockers.

## Contract Objects

| Object | Layer | Role | Forbidden |
| --- | --- | --- | --- |
| `EconomicMeaning` | L3 | Interprets source-local facts into direction, confidence, uncertainty, and relation readiness. | Buy/sell, rank, sizing, order intent. |
| `MeaningRelationEdge` | L3 | Groups same-symbol economic meanings into reviewable support, risk, mixed, context, or blocked relation context. | Buy/sell, rank, sizing, order intent. |
| `ThesisBundle` | L4 | Groups meaning objects into a candidate thesis with catalyst, invalidation, source gaps, and blockers. | Orders, sizing, broker actions. |
| `PolicyAction` | L5 | States hold/reduce/exit/rerisk/watch/skip under a frozen policy. | Creating paper/live orders directly. |
| `RuntimeDecision` | L6 | Converts policy action into runtime status such as shadow-only, paper-eligible, blocked, or broker-review-required. | Live-order permission in this repository state. |
| `L0L6DiagnosticRuntimeState` | L0-L6 | Summarizes one diagnostic heartbeat state for deterministic hashing and idempotency. | Paper order intent, live order, broker mutation, replay, selector/sizing changes. |
| `DiagnosticOrchestrationDecision` | L0-L6 | Decides whether a diagnostic heartbeat should execute or skip based on state hash, cadence, and idempotency. | Trading permission, deployment readiness, real-capital permission. |
| `FrontendReadModel` | L7 | Publishes read-only cockpit state with provenance and blockers. | Mutating strategy, replay, paper orders, live orders, or broker state. |

## Hard Gates

- `outcome_used_for_assignment` must stay false.
- Missing sources must remain source gaps.
- L3 meaning `asof_ts` may not be after the L4 thesis decision timestamp.
- L3 meaning symbol and L4 thesis symbol must match.
- Context-only or unknown meanings may not create directional relation edges.
- Relation edges and thesis bundles must preserve exact `meaning_ids`.
- `RuntimeGate.PAPER_ELIGIBLE` may not carry blocker flags.
- Paper order intent requires `RuntimeGate.PAPER_ELIGIBLE`.
- Live order permission is forbidden while real capital is `FORBIDDEN`.
- Diagnostic orchestration state must keep strategy `NOT_ACCEPTED`, deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital `FORBIDDEN`.
- Diagnostic orchestration state must keep paper order intents and live orders at 0.
- 5-minute safety heartbeats may check market/session/account/order state and existing L6 runtime state, but may not run changed-candidate L3-L5 brain work.
- 10-minute brain heartbeats with changed candidates require L6 runtime decision references.
- 30-minute heavy-source heartbeats require source receipt references.
- L7 display status may not claim strategy acceptance, deployment readiness, live-order permission, or real-capital permission.
- Frontend read models must be read-only.
- Every object must carry source/provenance references sufficient for review.

## Implementation

Initial implementation:

- `src/brain/contracts.py`
- `src/brain/meaning_adapter.py`
- `src/brain/relation_adapter.py`
- `src/brain/policy_adapter.py`
- `src/brain/runtime_decision_adapter.py`
- `src/brain/diagnostic_orchestration.py`
- `src/brain/frontend_read_model_adapter.py`
- `src/brain/runtime_catalog.py`
- `PAPER_OPS_RUNTIME_CONTRACT_VERSION`

Initial validation:

- `tests/test_brain_meaning_adapter.py`
- `tests/test_brain_relation_adapter.py`
- `tests/test_brain_policy_adapter.py`
- `tests/test_brain_runtime_decision_adapter.py`
- `tests/test_brain_diagnostic_orchestration.py`
- `tests/test_brain_frontend_read_model_adapter.py`
- `tests/test_brain_runtime_contracts.py`
- `tests/test_brain_runtime_catalog_adapter.py`
- `scripts/trader_brain_3351_3360_task742_meaning_adapter_validate.py`
- `scripts/trader_brain_3361_3370_relation_thesis_bridge_validate.py`
- `scripts/trader_brain_3371_3380_policy_review_bridge_validate.py`
- `scripts/trader_brain_3381_3390_runtime_review_bridge_validate.py`
- `scripts/trader_brain_3391_3400_frontend_review_bridge_validate.py`
- `scripts/trader_brain_3411_3420_l0_l6_diagnostic_orchestration_validate.py`
- `scripts/trader_brain_3164_runtime_catalog_adapter_validate.py`

## Task742 Meaning Adapter

`src/brain/meaning_adapter.py` adapts already-built Task742 pragmatic economic meaning rows into L3 `EconomicMeaning` objects.

It may:

- translate `economic_direction_hint` into `MeaningDirection`
- translate `confidence_band` into bounded confidence
- carry ambiguity, soft uncertainty, hard blockers, and needed confirmations as uncertainty flags
- preserve `source_event_id` as `source_packet_ids`
- use `tradable_after_dt` as the L3 as-of timestamp

It may not:

- build Task742 packets
- run replay or backtest
- emit trade instructions
- emit scores or ranks
- create paper or live order intent

## Policy Review Bridge

`src/brain/policy_adapter.py` adapts L4 `ThesisBundle` objects into L5 review-only `PolicyAction` objects.

It may:

- create `WATCH` for reviewable mixed/context theses
- create `SKIP` for blocked, unknown, or source-gap theses
- preserve `thesis_id`
- attach evidence paths and blocker reason codes

It may not:

- emit `HOLD`, `REDUCE`, `EXIT`, or `RERISK`
- carry a sizing directive
- create paper or live order intent
- run replay or backtest
- claim deployment or acceptance readiness

## Runtime Review Bridge

`src/brain/runtime_decision_adapter.py` adapts L5 review-only `PolicyAction` objects into L6 `RuntimeDecision` objects.

It may:

- map `WATCH` to `SHADOW_ONLY`
- map `SKIP` to `BLOCKED`
- preserve `policy_action_id`
- attach validation references and blocker flags

It may not:

- emit `PAPER_ELIGIBLE`
- allow paper order intent
- allow live orders
- run replay or backtest
- mutate broker or runtime state

## Frontend Review Bridge

`src/brain/frontend_read_model_adapter.py` adapts L6 review `RuntimeDecision` objects into L7 read-only `FrontendReadModel` objects.

It may:

- map `SHADOW_ONLY` to `review_shadow_only`
- map `BLOCKED` to `review_blocked`
- preserve `runtime_decision_id`
- expose blocker flags and provenance paths

It may not:

- display acceptance, deployment, paper-order, live-order, or real-capital readiness
- expose paper or live order permission
- write frontend catalogs
- mutate runtime or broker state
- accept rows using outcome fields for assignment

## Diagnostic Orchestration Guard

`src/brain/diagnostic_orchestration.py` builds deterministic state hashes and idempotency keys for L0-L6 diagnostic heartbeats.

It may:

- model event-driven, 5-minute safety, 10-minute brain, 30-minute heavy-source, and daily-close cadences
- hash runtime state references deterministically
- build idempotency keys from cadence, heartbeat bucket, and state hash
- skip duplicate state
- skip 10-minute brain heartbeats when no candidates changed
- expose allowed and forbidden diagnostic operations

It may not:

- create paper order intent
- submit live orders
- mutate broker state
- run replay
- change selector or sizing
- claim strategy acceptance
- claim deployment readiness
- permit real capital

## Relation Thesis Bridge

`src/brain/relation_adapter.py` adapts already-built L3 `EconomicMeaning` objects into `MeaningRelationEdge` objects and L4 `ThesisBundle` objects.

It may:

- group meanings by an explicit caller-owned key such as `lifecycle_id` and `symbol`
- create review-only relation edge types such as `MIXED_CONTEXT`, `CONTEXT_ONLY`, or `BLOCKED_NOT_READY`
- preserve exact `meaning_ids` and `source_packet_ids`
- propagate blocker flags and source gaps into the thesis bundle

It may not:

- infer symbol/date/price/time proximity matches
- turn neutral or unknown context into directional support or risk
- rank candidates
- size positions
- create policy actions
- run replay or backtest
- create paper or live order intent

## Runtime Catalog Adapter

`src/brain/runtime_catalog.py` adapts an already-built `paper-ops-runtime-v1` payload into `FrontendReadModel`.

It may:

- read a supplied in-memory payload
- enforce `paper-ops-runtime-v1`
- verify `ui_reads_catalog_only`
- reject deployment claims
- reject missing-source approximation
- copy runtime quality flags into read-model blockers

It may not:

- call the catalog builder
- write files
- run replay
- submit paper or live orders
- mutate broker or runtime state

Validation authority:

- `PACKAGE_HEALTH` for object contract regression.
- `REPORTING_HEALTH` for read-only runtime catalog adapter validation.
- `GOVERNANCE_HEALTH` for registry/report closeout.

PASS does not mean:

- strategy acceptance
- deployment readiness
- broker truth completion
- live-source readiness
- real-capital permission
