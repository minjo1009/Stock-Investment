# Source Code Canonicalization Map

## Purpose

This document is the human-readable summary of Task746.

It answers:

```text
Which `src/` files are stable package candidates?
Which files are task-scoped research or acceptance code?
Which owner must review each bucket before future development builds on it?
```

The full machine-readable table is:

`docs/reports/task_746_src_canonicalization/task746_src_canonicalization_inventory.csv`

## Current Counts

| Bucket | Count | Meaning |
| --- | ---: | --- |
| historical_task_code_review | 346 | Historical task research code. Preserve for traceability; do not use as current canonical code without owner review. |
| owner_review_package_candidate | 119 | Non-task package modules that need owner review before promotion. |
| supporting_task_code_review | 44 | Task-scoped code tied to current supporting lanes such as content, microstructure, paper execution, or acceptance. |
| canonical_package_candidate | 33 | Stable package candidates that can become the small canonical code base after validation. |
| active_task_code_review | 16 | Current brain-layer Task727-742 builder code. Review-only; requires supersession notes before reuse. |

## Source Areas

| Area | Count | Current Interpretation |
| --- | ---: | --- |
| backtest | 444 | Main source-code sprawl area. Mixes reusable engines, historical experiments, task builders, and current brain work. |
| app | 37 | Runtime, paper, sidecar, and app entrypoint code are mixed. |
| risk | 14 | Needs execution/risk owner review before it is treated as canonical. |
| execution | 12 | Mostly execution interfaces and policies; owner review required. |
| data | 8 | Small data surface; needs source/readiness owner review. |
| strategy | 6 | Interface-style surface; not strategy acceptance. |
| replay | 5 | Replay support surface; validate against exact-ID rules before reuse. |
| other areas | 32 | Smaller package surfaces. |

## Canonical Package Candidates

These 33 files are the current smallest possible `src` package base. This does not mean they are accepted for trading. It means they are the first files to review for stable package status.

- `src/__init__.py`
- `src/app/__init__.py`
- `src/app/main.py`
- `src/app/pipeline.py`
- `src/app/reconciliation.py`
- `src/app/report_recent_runs.py`
- `src/app/run_trade_loop.py`
- `src/app/run_trade_once.py`
- `src/backtest/__init__.py`
- `src/backtest/analysis.py`
- `src/backtest/data_loader.py`
- `src/backtest/engine.py`
- `src/backtest/engine_full.py`
- `src/backtest/models.py`
- `src/common/__init__.py`
- `src/common/models.py`
- `src/execution/__init__.py`
- `src/execution/interface.py`
- `src/integration/__init__.py`
- `src/integration/kis_auth_manager.py`
- `src/integration/kis_client.py`
- `src/integration/slack_client.py`
- `src/market/__init__.py`
- `src/market/interface.py`
- `src/reporting/__init__.py`
- `src/reporting/interface.py`
- `src/risk/__init__.py`
- `src/risk/interface.py`
- `src/state/__init__.py`
- `src/state/store.py`
- `src/strategy/__init__.py`
- `src/strategy/interface.py`
- `src/ui/app.py`

## Active Brain Code Placement

The current Task727-742 brain builder code is under `src/backtest/`.

That is acceptable as historical placement, but it should not become the long-term architecture.

Future brain work should not import these files as if they are stable engine modules unless a task report states:

- which Task727-742 file is current
- which older file is superseded
- which output contract is stable
- which leakage and source-readiness checks passed

## Task3162 Brain Runtime Contract Candidate

Task3162 adds the first narrow backend contract surface for the brain-to-runtime handoff:

- `src/brain/__init__.py`
- `src/brain/contracts.py`
- `src/brain/runtime_catalog.py`
- `PAPER_OPS_RUNTIME_CONTRACT_VERSION`

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/__init__.py` | `canonical_package_validation_candidate` | Package export surface for typed brain runtime contracts. |
| `src/brain/contracts.py` | `canonical_package_validation_candidate` | Dataclass and enum contracts for L3/L4/L5/L6/L7 handoff invariants. |
| `src/brain/runtime_catalog.py` | `canonical_package_validation_candidate` | Read-only L6/L7 adapter and `paper-ops-runtime-v1` version constant from paper ops runtime catalog payloads to `FrontendReadModel`. |

This does not promote any strategy, selector, sizing, replay, paper order, live order, or deployment path.

Promotion requirement:

- Contract tests pass.
- The next wrapper task proves one existing L5/L6 script can read or emit these objects without changing replay/runtime behavior.
- Owner review confirms no outcome labels, broker truth, or UI review fields enter assignment.
- The Task3181-3190 operating-loop validator continues to pass after future package exports or adapter changes.

## Task3191-Task3195 Backend Accelerator Promotion

Task3191-Task3195 promotes Polars and DuckDB from diagnostic-only helper status into the core backend acceleration layer.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/infra/accelerators.py` | `canonical_package_validation_candidate` | Core backend acceleration API. Selects Polars first, DuckDB second, and pandas fallback after correctness parity checks. |
| `src/infra/external_tools.py` | `canonical_package_validation_candidate` | Low-level helper implementation for pandas, Polars, DuckDB, and Pandera artifact operations. |
| `src/infra/__init__.py` | `canonical_package_validation_candidate` | Package export surface for core backend accelerators. |

Promotion boundary:

- Polars and DuckDB may accelerate backend artifact/query computations.
- They may not change selector, ranking, sizing, replay, paper-order, live-order, broker, acceptance, or deployment semantics.
- Every future real-path migration must compare against pandas row counts, null counts, strict totals, and checksum before becoming default.
- OpenBB remains outside this core engine layer unless a separate source-acquisition contract promotes a read-only source adapter.

## Task3196-Task3200 Real Accelerator Migration

Task3196-Task3200 migrates one real existing strict-gate aggregate path behind the core backend accelerator API:

- `scripts/trader_brain_3141_external_tool_helper_contract.py`

Migration boundary:

- The script now uses `strict_gate_aggregate_accelerated()`.
- Direct `pandas_strict_gate_aggregate` calls were removed from the migrated script.
- Large SEC and liquidity/rates local artifact aggregates must still match historical Task3127 reference hashes and pandas correctness parity.
- The migration does not change selector, ranking, sizing, replay, source acquisition, paper orders, live orders, broker state, acceptance, or deployment readiness.

## Task3221-Task3280 Backend Acceleration Program

Task3221-Task3280 extends the backend acceleration layer from strict-gate artifact aggregates to generic in-memory grouped numeric aggregates.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/infra/accelerators.py` | `canonical_package_validation_candidate` | Adds `grouped_numeric_aggregate_accelerated()` for count-non-null, mean, and sum with pandas parity/fallback support. |
| `scripts/build_trader_terminal_catalog.py` | `supporting_task_code_review` | Catalog group quality helpers now route through the grouped accelerator API; full catalog build remains reporting health, not trading health. |
| `src/backtest/core/metrics.py` | `canonical_package_validation_candidate` | `grouped_lifecycle_quality()` now routes through the grouped accelerator API while preserving `dropna=False`, non-null lifecycle counts, and NaN mean semantics. |
| `scripts/trader_brain_3142_external_tool_infra_module_promotion.py` | `supporting_task_code_review` | Source-panel strict-gate aggregates now route through `strict_gate_aggregate_accelerated()`. |
| `scripts/trader_brain_3143_external_tool_typed_contract.py` | `supporting_task_code_review` | Typed source-panel parity now uses the core strict-gate accelerator path. |

Promotion boundary:

- `grouped_numeric_aggregate_accelerated()` is a backend computation accelerator, not a strategy engine.
- It may not change selector, ranking, sizing, replay, source acquisition, paper-order, live-order, broker, acceptance, or deployment semantics.
- Catalog runtime may select pandas through the accelerator API when repeated in-memory Polars conversion is slower; Polars/DuckDB adoption still requires focused pandas parity or real-panel reference parity.
- OpenBB remains outside this core engine layer unless a separate source-acquisition contract promotes a read-only source adapter.

## Task3321-Task3330 Large Panel Default Acceleration

Task3321-Task3330 promotes one real large-panel groupby to the default accelerator path.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `scripts/trader_brain_3142_external_tool_infra_module_promotion.py` | `supporting_task_code_review` | The liquidity/rates `provider,series_id` strict-gate aggregate uses `BackendAccelerationEngine.AUTO`; the core accelerator selects Polars after pandas parity. |
| `scripts/trader_brain_3143_external_tool_typed_contract.py` | `supporting_task_code_review` | The typed liquidity/rates parity case uses the same AUTO default path. |

Promotion boundary:

- The default promotion applies only to the named liquidity/rates aggregate.
- The validator measured a 19.669317x speedup against pandas and preserved the Task3127 reference hash.
- This does not change selector, ranking, sizing, replay, source acquisition, paper-order, live-order, broker, acceptance, or deployment semantics.

## Task3331-Task3340 Full Source Default Acceleration

Task3331-Task3340 promotes the next distinct 500k+ source-panel groupby to the default accelerator path.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/infra/external_tools.py` | `canonical_package_validation_candidate` | Strict-gate CSV aggregate helpers now read only group columns plus `strict_gate_pass`, preserving aggregate semantics while avoiding unrelated large payload columns. |
| `scripts/trader_brain_3331_3340_full_source_default_acceleration_validate.py` | `task_scoped_validation` | Validates the 4,588,915-row Task2251 full-source `provider,endpoint_name` strict-gate aggregate with AUTO default, pandas parity, reference hash equality, and minimum 2x speedup. |

Promotion boundary:

- The default promotion applies only to the named full-source normalized aggregate.
- The validator measured a 15.803409x speedup against pandas and matched the fixed pandas reference output hash.
- This does not change selector, ranking, sizing, replay, source acquisition, paper-order, live-order, broker, acceptance, or deployment semantics.

## Task3351-Task3360 Task742 Meaning Adapter

Task3351-Task3360 adds the first adapter from active research meaning packets into the package-level L3 contract.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/meaning_adapter.py` | `canonical_package_validation_candidate` | Translates already-built Task742 review-only rows into `EconomicMeaning` objects while rejecting trade, score, backtest, and outcome-assignment flags. |
| `tests/test_brain_meaning_adapter.py` | `package_health_test` | Protects the Task742-to-L3 adapter mapping and forbidden flag rejection. |

Promotion boundary:

- The adapter is L3 contract plumbing only.
- It does not build Task742 data, create relation edges, build L4 thesis bundles, propose L5 actions, run replay, or create orders.
- It preserves source-event identity as provenance and uses `tradable_after_dt` as L3 as-of time.

## Task3411-Task3420 L0-L6 Diagnostic Orchestration

Task3411-Task3420 adds the first package-level guard for realtime diagnostic heartbeats before a future scheduler or runner can call the brain/runtime stack.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/diagnostic_orchestration.py` | `canonical_package_validation_candidate` | Builds deterministic L0-L6 diagnostic runtime state hashes, cadence-specific idempotency keys, duplicate-state skips, and heartbeat guardrails. |
| `tests/test_brain_diagnostic_orchestration.py` | `package_health_test` | Protects state hash determinism, 5-minute safety vs 10-minute brain separation, duplicate-state idempotency, status boundaries, and no paper/live permission. |

Promotion boundary:

- The module is diagnostic orchestration plumbing only.
- It may be called by a future scheduler before shadow/paper refreshes.
- It does not install a scheduler, call a broker, run replay, create paper order intents, create live orders, or change selector/sizing.
- It keeps Strategy `NOT_ACCEPTED`, Deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and Real Capital `FORBIDDEN`.

## Task3361-Task3370 Relation Thesis Bridge

Task3361-Task3370 adds the first package-level bridge from L3 economic meanings into relation edges and L4 thesis bundles.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/contracts.py` | `canonical_package_validation_candidate` | Adds `MeaningRelationEdge` and `RelationEdgeType` as review-only L3 relation context contracts. |
| `src/brain/relation_adapter.py` | `canonical_package_validation_candidate` | Builds same-symbol relation edges and L4 `ThesisBundle` objects from already-built `EconomicMeaning` objects. |
| `tests/test_brain_relation_adapter.py` | `package_health_test` | Protects relation edge classification, context-only directional blocking, symbol/as-of gates, and package exports. |

Promotion boundary:

- The bridge is L3/L4 contract plumbing only.
- It does not build Task742 data, propose L5 actions, run replay, rank candidates, size positions, create paper orders, or create live orders.
- It preserves exact `meaning_ids` and prevents context-only meanings from becoming directional relation edges.

## Task3371-Task3380 Policy Review Bridge

Task3371-Task3380 adds the first package-level bridge from L4 thesis bundles into L5 review-only policy actions.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/policy_adapter.py` | `canonical_package_validation_candidate` | Builds review-only `PolicyAction` objects from `ThesisBundle` objects, emitting only WATCH or SKIP with no sizing or order intent. |
| `tests/test_brain_policy_adapter.py` | `package_health_test` | Protects WATCH/SKIP mapping, source-gap skip behavior, evidence-path requirement, non-review action rejection, and package exports. |

Promotion boundary:

- The bridge is L5 review-action contract plumbing only.
- It does not create runtime decisions, paper-order eligibility, live-order eligibility, replay, ranking, sizing, selector changes, or broker mutations.
- It preserves thesis identity and keeps blocked/source-gap theses as SKIP.

## Task3381-Task3390 Runtime Review Bridge

Task3381-Task3390 adds the first package-level bridge from L5 review actions into L6 runtime decisions.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/runtime_decision_adapter.py` | `canonical_package_validation_candidate` | Builds L6 `RuntimeDecision` objects from review-only `PolicyAction` objects, mapping WATCH to SHADOW_ONLY and SKIP to BLOCKED with no paper/live permission. |
| `tests/test_brain_runtime_decision_adapter.py` | `package_health_test` | Protects WATCH/SHADOW_ONLY mapping, SKIP/BLOCKED mapping, validation-ref requirement, non-review action rejection, PAPER_ELIGIBLE rejection, and package exports. |

Promotion boundary:

- The bridge is L6 review-runtime contract plumbing only.
- It does not create frontend read models, paper-order eligibility, live-order eligibility, replay, ranking, sizing, selector changes, or broker mutations.
- It preserves policy action identity and keeps all generated runtime decisions non-paper-eligible.

## Task3391-Task3400 Frontend Review Bridge

Task3391-Task3400 adds the first package-level bridge from L6 runtime decisions into L7 read-only frontend read models.

Current classification:

| File | Bucket | Meaning |
| --- | --- | --- |
| `src/brain/frontend_read_model_adapter.py` | `canonical_package_validation_candidate` | Builds L7 `FrontendReadModel` objects from review `RuntimeDecision` objects, mapping SHADOW_ONLY/BLOCKED to review-only display states and preserving blockers/provenance. |
| `tests/test_brain_frontend_read_model_adapter.py` | `package_health_test` | Protects read-only output, SHADOW_ONLY/BLOCKED display mapping, provenance requirement, PAPER_ELIGIBLE rejection, and package exports. |

Promotion boundary:

- The bridge is L7 read-model contract plumbing only.
- It does not write cockpit catalogs, change UI code, create paper-order eligibility, live-order eligibility, replay, ranking, sizing, selector changes, or broker mutations.
- It preserves runtime decision identity and keeps all generated read models read-only.

## Rule For 2/5 Cleanup

During this pass:

- do not delete `src` files
- do not move `src` files
- do not change imports
- do not change strategy acceptance
- do not treat package candidates as production-ready

Classification first. Extraction and movement later.

## Next Pass Dependency

Task747 should classify `tests/` against this map.

The key question for 3/5 is:

```text
Which tests protect the 33 canonical package candidates,
which tests only preserve historical task behavior,
and which slow/integration tests need separate validation lanes?
```
