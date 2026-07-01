# Test Validation Canonicalization Map

## Purpose

This document is the human-readable summary of Task747.

It answers:

```text
Which tests are current quality gates?
Which tests are historical evidence only?
Which tests must be kept away from fast unit validation?
What does a test PASS mean, and what does it not mean?
```

The full machine-readable table is:

`docs/reports/task_747_test_validation_canonicalization/task747_test_validation_inventory.csv`

## Current Counts

Task747 classifies the formal Git-visible `tests/` surface from Task745.

| Lane | Count | Meaning |
| --- | ---: | --- |
| historical_task_validation | 224 | Historical task regression/evidence. Not a current quality gate. |
| supporting_task_validation | 39 | Supporting lane checks for current research/execution work. |
| fixture_support_not_quality_gate | 27 | Fixtures or support files. Not standalone validation. |
| canonical_package_validation_candidate | 24 | Possible package health tests. Must be mapped to Task746 package candidates before promotion. |
| governance_validation | 18 | Registry, artifact, contract, readiness, or governance checks. |
| active_brain_validation | 14 | Task727-742 brain-layer regression checks. Research-only. |
| execution_broker_truth_validation | 13 | Execution or broker-truth adjacent checks. Must not be mixed into fast unit gate. |
| microstructure_data_validation | 12 | Data/microstructure source contract checks. |
| frontend_reporting_validation | 7 | Frontend, Slack, terminal, or reporting checks. |

## Authority Tags

| Authority Tag | Count | PASS Means | PASS Does Not Mean |
| --- | ---: | --- | --- |
| EVIDENCE_ONLY | 263 | Historical behavior remains reviewable. | Current system quality, strategy acceptance, deployment readiness, or real-capital permission. |
| SUPPORT_ONLY | 27 | Support file is present/importable when applicable. | A quality gate passed. |
| PACKAGE_HEALTH | 24 | Package-level regression was not detected for mapped targets. | Strategy is accepted or deployment-ready. |
| GOVERNANCE_HEALTH | 18 | Governance contract or registry check did not detect a regression. | Trading system is accepted. |
| RESEARCH_ONLY | 14 | Research or brain-layer regression was not detected. | Brain is validated for trading. |
| DATA_HEALTH | 12 | Data/microstructure contract check did not detect a regression. | Source coverage is complete. |
| EXECUTION_HEALTH | 9 | Execution logic check did not detect a regression. | Broker truth is complete. |
| REPORTING_HEALTH | 7 | Reporting contract check did not detect a regression. | Trading system is healthy. |
| ACCEPTANCE_EVIDENCE_REVIEW | 4 | Acceptance evidence is reviewable. | Acceptance is granted. |

## Fast Gate Rule

Only these lanes are candidates for a fast local quality gate:

- `PACKAGE_HEALTH`
- `GOVERNANCE_HEALTH`

These lanes are not fast local quality gates:

- `EVIDENCE_ONLY`
- `RESEARCH_ONLY`
- `SUPPORT_ONLY`
- `EXECUTION_HEALTH`
- `ACCEPTANCE_EVIDENCE_REVIEW`
- `DATA_HEALTH`
- `REPORTING_HEALTH`

They require owner-specific validation commands.

## Package Test Gap

There are 24 `PACKAGE_HEALTH` candidates.

Only 4 currently have a clear target hint:

- `tests/test_data_quality.py` -> `data/quality.py`
- `tests/test_engine_entry_gate_off.py` -> `src/backtest/engine.py`
- `tests/test_execution_policies.py` -> `src/execution`
- `tests/test_risk_policies.py` -> `src/risk`

Task3162 adds one new `PACKAGE_HEALTH` candidate:

- `tests/test_brain_runtime_contracts.py` -> `src/brain/contracts.py`

Task3163 adds one new `PACKAGE_HEALTH` / `REPORTING_HEALTH` boundary candidate:

- `tests/test_brain_runtime_catalog_adapter.py` -> `src/brain/runtime_catalog.py`

Task3164 adds one `REPORTING_HEALTH` validator:

- `scripts/trader_brain_3164_runtime_catalog_adapter_validate.py` -> in-memory `build_paper_ops_runtime_catalog(root)` output to read-only `FrontendReadModel`

Task3181-Task3190 adds one mixed-boundary operating validator:

- `scripts/trader_brain_3181_3190_brain_code_operating_loop_validate.py` -> runbook, registry rows, navigation links, `src/brain` package exports, and read-only adapter boundary

Authority:

- `GOVERNANCE_HEALTH` for runbook, registry, operating-state, and navigation consistency.
- `PACKAGE_HEALTH` for `src/brain` export and contract-surface drift.
- `REPORTING_HEALTH` for read-only runtime catalog to frontend read-model boundary.

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, or real-capital permission.

Task3191-Task3195 adds one `PACKAGE_HEALTH` / `GOVERNANCE_HEALTH` accelerator validator:

- `tests/test_backend_accelerators.py` -> `src/infra/accelerators.py`
- `scripts/trader_brain_3191_3195_backend_accelerator_promotion_validate.py` -> synthetic strict-gate fixture, dependency availability, Polars/DuckDB correctness parity, and auto accelerator selection

PASS means:

- Polars and DuckDB are importable in the current environment.
- Both engines match pandas correctness on the synthetic strict-gate aggregate fixture.
- The core accelerator API can select an accelerator before pandas fallback.

PASS does not mean:

- a real strategy path has been migrated
- strategy acceptance
- deployment readiness
- broker truth completion
- live-source readiness
- paper-order permission
- live-order permission
- real-capital permission

Task3196-Task3200 adds one real-path accelerator migration validator:

- `scripts/trader_brain_3196_3200_real_accelerator_migration_validate.py` -> verifies `scripts/trader_brain_3141_external_tool_helper_contract.py` routes real SEC and liquidity/rates strict-gate aggregates through `strict_gate_aggregate_accelerated()`

Authority:

- `PACKAGE_HEALTH` for accelerator API and migrated script import/use surface.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, and no-trading-state-change closeout.

PASS means:

- the migrated script uses the core accelerator API
- direct pandas strict-gate aggregate call is removed from the migrated script
- real output hashes match Task3127 references
- real output correctness matches pandas parity

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, or real-capital permission.

Task3221-Task3280 adds backend acceleration program validators:

- `tests/test_backend_accelerators.py` -> `src/infra/accelerators.py` generic grouped aggregation API and strict-gate accelerator regressions
- `tests/test_backtest_core_metrics_accelerated.py` -> `src/backtest/core/metrics.py::grouped_lifecycle_quality`
- `scripts/trader_brain_3231_3245_catalog_acceleration_validate.py` -> focused catalog group quality pandas parity and Polars/DuckDB fixture parity
- `scripts/trader_brain_3246_3260_backtest_core_metrics_acceleration_validate.py` -> backtest core grouped metrics pandas parity without replay
- `scripts/trader_brain_3261_3270_source_panel_acceleration_validate.py` -> Task3142/Task3143 source-panel aggregate routing through core accelerators
- `scripts/trader_brain_3221_3280_backend_acceleration_program_validate.py` -> lane validator, registry, report, operating-state, and map closeout

Authority:

- `PACKAGE_HEALTH` for `src/infra/accelerators.py`, `src/backtest/core/metrics.py`, and source-panel accelerator routing.
- `REPORTING_HEALTH` for catalog/read-model output parity.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, map, and no-trading-state-change closeout.

PASS means:

- the named grouped aggregation paths match pandas or reference parity for the checked fixtures/artifacts
- direct selected pandas or low-level Polars/DuckDB groupby work has been routed behind core accelerator APIs for the named paths
- governance surfaces record the status boundaries

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, source coverage completion, paper-order permission, live-order permission, or real-capital permission.

Task3321-Task3330 adds one large-panel default acceleration validator:

- `scripts/trader_brain_3321_3330_large_panel_default_acceleration_validate.py` -> verifies the 768841-row liquidity/rates `provider,series_id` strict-gate aggregate uses AUTO default, selects Polars, passes pandas parity, preserves the Task3127 reference hash, and clears the minimum 2x speedup threshold.

Authority:

- `PACKAGE_HEALTH` for the accelerator API and Task3142/Task3143 source-panel routing.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, and no-trading-state-change closeout.

PASS means:

- the named large-panel groupby default selects Polars through the core accelerator
- pandas parity and reference hash checks passed for that aggregate
- measured speedup cleared the threshold in the current local environment

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, source coverage completion, catalog speed improvement, paper-order permission, live-order permission, or real-capital permission.

Task3331-Task3340 adds the next 500k+ source-panel default acceleration validator:

- `scripts/trader_brain_3331_3340_full_source_default_acceleration_validate.py` -> verifies the 4,588,915-row Task2251 full-source normalized `provider,endpoint_name` strict-gate aggregate uses AUTO default, selects Polars, passes pandas parity, matches the fixed pandas reference output hash, and clears the minimum 2x speedup threshold.

Authority:

- `PACKAGE_HEALTH` for the strict-gate accelerator API and required-column CSV read optimization.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, and no-trading-state-change closeout.

PASS means:

- the named full-source groupby default selects Polars through the core accelerator
- pandas parity and reference hash checks passed for that aggregate
- measured speedup cleared the threshold in the current local environment

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, source coverage completion, catalog speed improvement, paper-order permission, live-order permission, or real-capital permission.

Task3351-Task3360 adds the Task742-to-L3 meaning adapter validation lane:

- `tests/test_brain_meaning_adapter.py` -> package-health tests for `src/brain/meaning_adapter.py`
- `scripts/trader_brain_3351_3360_task742_meaning_adapter_validate.py` -> rebuilds Task742 packets into a temporary directory and verifies all 3,443 rows adapt to `EconomicMeaning` without order, replay, score, backtest, or outcome-assignment side effects.

Authority:

- `PACKAGE_HEALTH` for the adapter and package exports.
- `GOVERNANCE_HEALTH` for report, registry, and no-trading-state-change closeout.

PASS means:

- already-built Task742 pragmatic meaning rows can enter the L3 `EconomicMeaning` contract
- review-only guardrails are enforced at the adapter boundary

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, relation-edge readiness, thesis-bundle readiness, paper-order permission, live-order permission, or real-capital permission.

Task3361-Task3370 adds the L3 relation edge to L4 thesis bundle validation lane:

- `tests/test_brain_relation_adapter.py` -> package-health tests for `src/brain/relation_adapter.py`
- `scripts/trader_brain_3361_3370_relation_thesis_bridge_validate.py` -> rebuilds Task742 packets into a temporary directory, adapts all 3,443 meanings, and verifies 228 relation edges plus 228 thesis bundles preserve meaning ids without order, replay, score, rank, or outcome-assignment side effects.

Authority:

- `PACKAGE_HEALTH` for the relation edge contract, thesis bridge adapter, and package exports.
- `GOVERNANCE_HEALTH` for report, registry, and no-trading-state-change closeout.

PASS means:

- already-built L3 `EconomicMeaning` objects can become review-only relation edges and L4 `ThesisBundle` objects
- context-only or unknown meanings do not create directional relation edges
- exact meaning identity is preserved through the bridge

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, L5 policy-action readiness, paper-order permission, live-order permission, or real-capital permission.

Task3371-Task3380 adds the L4 thesis bundle to L5 review policy action validation lane:

- `tests/test_brain_policy_adapter.py` -> package-health tests for `src/brain/policy_adapter.py`
- `scripts/trader_brain_3371_3380_policy_review_bridge_validate.py` -> rebuilds Task742 packets into a temporary directory, rebuilds 228 thesis bundles, and verifies 228 review-only `PolicyAction` objects with WATCH/SKIP only, no sizing, no order intent, and no replay/runtime side effect.

Authority:

- `PACKAGE_HEALTH` for the policy review adapter and package exports.
- `GOVERNANCE_HEALTH` for report, registry, and no-trading-state-change closeout.

PASS means:

- L4 thesis bundles can become L5 review-only policy actions
- blocked/source-gap theses remain SKIP
- reviewable mixed/context theses remain WATCH
- L5 review actions do not carry sizing or order intent

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, L6 runtime eligibility, paper-order permission, live-order permission, or real-capital permission.

Task3381-Task3390 adds the L5 review policy action to L6 runtime decision validation lane:

- `tests/test_brain_runtime_decision_adapter.py` -> package-health tests for `src/brain/runtime_decision_adapter.py`
- `scripts/trader_brain_3381_3390_runtime_review_bridge_validate.py` -> rebuilds Task742 packets into a temporary directory, rebuilds 228 L5 review actions, and verifies 228 L6 runtime decisions with SHADOW_ONLY/BLOCKED only, no PAPER_ELIGIBLE, no paper order intent, no live order permission, and no replay/broker side effect.

Authority:

- `PACKAGE_HEALTH` for the runtime review adapter and package exports.
- `GOVERNANCE_HEALTH` for report, registry, and no-trading-state-change closeout.

PASS means:

- L5 review actions can become L6 runtime decisions
- WATCH actions remain SHADOW_ONLY
- SKIP actions remain BLOCKED
- generated runtime decisions are not paper-eligible and cannot create orders

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, or real-capital permission.

Task3391-Task3400 adds the L6 runtime decision to L7 frontend read model validation lane:

- `tests/test_brain_frontend_read_model_adapter.py` -> package-health tests for `src/brain/frontend_read_model_adapter.py`
- `scripts/trader_brain_3391_3400_frontend_review_bridge_validate.py` -> rebuilds Task742 packets into a temporary directory, rebuilds 228 L6 runtime decisions, and verifies 228 L7 read-only `FrontendReadModel` objects with review-only display status, preserved blockers/provenance, no forbidden display claims, no paper/live permission exposure, and no catalog write/runtime side effect.

Authority:

- `PACKAGE_HEALTH` for the frontend read model adapter and package exports.
- `GOVERNANCE_HEALTH` for report, registry, and no-trading-state-change closeout.

PASS means:

- L6 runtime decisions can become L7 read-only frontend read models
- SHADOW_ONLY and BLOCKED remain review-only display states
- blockers and provenance are preserved
- generated read models do not expose paper/live permission or deployment claims

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, UI implementation completion, or real-capital permission.

Task3401-Task3410 adds one L0-L6 realtime operating cadence audit validator:

- `scripts/trader_brain_3401_3410_l0_l6_realtime_ops_audit_validate.py` -> verifies the audit report, decision row, gap audit, cadence recommendation, Obsidian/LLM navigation, registry rows, and no-trading-state-change status footer.

Authority:

- `GOVERNANCE_HEALTH` for report, registry, operating-state, Obsidian, LLM wiki, and cadence artifact consistency.

PASS means:

- the L0-L6 cadence recommendation is recorded as event-driven plus a 10-minute changed-candidate brain heartbeat
- 5-minute operation is limited to safety/freshness checks rather than full L0-L6 recompute
- status boundaries remain `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and `FORBIDDEN`

PASS does not mean strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, UI implementation completion, or real-capital permission.

Task3411-Task3420 adds one L0-L6 diagnostic orchestration package and validator:

- `tests/test_brain_diagnostic_orchestration.py` -> package-health tests for `src/brain/diagnostic_orchestration.py`
- `scripts/trader_brain_3411_3420_l0_l6_diagnostic_orchestration_validate.py` -> validates deterministic state hashes, cadence-specific idempotency keys, duplicate-state skips, 5-minute safety vs 10-minute brain separation, report artifacts, and no-trading-state-change closeout.

Authority:

- `PACKAGE_HEALTH` for the diagnostic orchestration module and package exports.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, wiki, and status boundary closeout.

PASS means:

- a future scheduler can call a package-level diagnostic guard before running 5-minute or 10-minute heartbeats
- repeated identical runtime state can be skipped by state hash/idempotency key
- 5-minute safety heartbeats cannot run changed-candidate L3-L5 brain work
- 10-minute changed-candidate heartbeats require L6 runtime decision references

PASS does not mean scheduler installation, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, or real-capital permission.

Task3917 adds the L1-L5 institutional hardening package validation lane:

- `tests/test_l1_l5_institutional_hardening_package.py` -> package-health tests for `src/brain/institutional_hardening/*` and `src/validation/l1_l5_institutional_hardening_validator.py`
- `scripts/validate_l1_l5_institutional_hardening_package.py` -> integrated diagnostic package checks and artifact row output

Authority:

- `PACKAGE_HEALTH` for pure package score bounds, blocked-state behavior, and
  no-order/no-paper/no-live guardrails.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, and status
  boundary closeout.

PASS means:

- the diagnostic package modules are importable
- the named score functions remain bounded and deterministic for synthetic
  fixtures
- missing inputs/source gaps block rather than becoming negative evidence
- no order intent, paper/live permission, replay execution, or acceptance state
  change is introduced

PASS does not mean strategy acceptance, deployment readiness, broker truth
completion, live-source readiness, paper-order permission, live-order
permission, or real-capital permission.

Task3481-Task3485 adds the runtime atomicity precondition validation lane:

- `tests/test_scheduler_lease_atomicity.py` -> package-health tests for SQLite-backed scheduler lease atomic acquire, expiry steal, token-gated heartbeat, and token-gated release.
- `tests/test_runtime_authority_contract.py` -> package-health tests for runtime authority evidence, snapshot/version/lineage requirements, paper-eligibility evidence, kill-switch coverage, and broker idempotency contract.
- `scripts/trader_brain_3481_3485_runtime_atomicity_preconditions_validate.py` -> validates code contracts, package exports, task report, artifact manifest, registry, operating-state, and LLM wiki closeout.

Authority:

- `PACKAGE_HEALTH` for `src/state/store.py` lease helpers and `src/brain/runtime_authority.py`.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, wiki, and status boundary closeout.

PASS means:

- scheduler lease acquisition is token-gated and expiry-aware for future dry-run scheduler work
- runtime authority evidence requires lineage hashes, snapshot ids, valid windows, kill-switch coverage, and complete paper-eligibility evidence
- broker retry safety must use broker client-order-id support or reconciliation-before-retry

PASS does not mean scheduler installation, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, broker submission permission, or real-capital permission.

Task3486-Task3500 adds the runtime safety connection validation lane:

- `tests/test_kis_client_idempotency_contract.py` -> package-health tests for KIS submit idempotency parameters, unsupported broker client-order-id rejection, and local idempotency metadata preservation.
- `tests/test_task585_kis_paper_order_execution.py` -> package-health tests for Task585 durable intent behavior and broker-submit/local-record failure becoming UNKNOWN.
- `tests/test_scheduler_lease_atomicity.py` -> package-health tests for paper order intent state machine, authority evidence append-only ledger, lease token validation, and reconciliation resolver.
- `tests/test_runtime_authority_contract.py` -> package-health tests for RuntimeDecision authority fields, evidence expiry, paper eligibility requirements, and broker idempotency plan.
- `tests/test_runtime_diagnostic_ledger.py` -> package-health tests for runtime operating metrics.
- `scripts/trader_brain_3486_3500_runtime_idempotency_authority_observability_validate.py` -> validates code contracts, report, manifest, GPT review-only findings, registry, operating-state, wiki, and status boundary closeout.

Authority:

- `PACKAGE_HEALTH` for `src/integration/kis_client.py`, `src/app/task_585_kis_paper_order_execution.py`, `src/state/store.py`, `src/brain/contracts.py`, and `src/brain/runtime_authority.py`.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, wiki, GPT review-only artifact, and status boundary closeout.

PASS means:

- the selected runtime paths have durable local idempotency and UNKNOWN blocking behavior for broker-submit/local-record failure
- `PAPER_ELIGIBLE` requires RuntimeDecision validity/snapshot/lineage fields plus authority evidence
- scheduler lease tokens and authority evidence hashes are testable package contracts
- runtime diagnostics can surface UNKNOWN and reconciliation-block operating metrics

PASS does not mean scheduler installation, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, broker submission permission, or real-capital permission.

Task3501-Task3529 adds the runtime scheduler authority submit-state validation lane:

- `tests/test_diagnostic_scheduler.py` -> package-health tests for one-tick dry-run scheduler behavior, non-paper environment blocking, duplicate-state skipping, active-lease skipping, token validation, and heartbeat persistence.
- `tests/test_runtime_authority_contract.py` -> package-health tests for single latest-L6 authority selection and tied-latest rejection.
- `tests/test_broker_submit_state.py` -> package-health tests for local authorized paper intent lifecycle, UNKNOWN-after-submit blocking until reconciliation, and blocked-authority rejection.
- `scripts/trader_brain_3501_3529_runtime_scheduler_authority_submit_state_validate.py` -> validates code contracts, package tests, report, manifest, registry, operating-state, Obsidian, LLM wiki, and status boundary closeout.

Authority:

- `PACKAGE_HEALTH` for `src/app/diagnostic_scheduler.py`, `src/brain/runtime_authority.py`, and `src/execution/broker_submit_state.py`.
- `GOVERNANCE_HEALTH` for report, registry, operating-state, Obsidian, LLM wiki, and status boundary closeout.

PASS means:

- a dry-run scheduler tick can be executed with deterministic state-hash/idempotency behavior and token-gated lease validation
- one latest L6 `RuntimeDecision` authority can be selected or rejected on tie
- local paper intent submit/reconciliation states are explicit and testable

PASS does not mean recurring scheduler installation, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, broker submission permission, or real-capital permission.

Task3531-Task3560 adds the runtime scheduler broker-truth paper-eligibility validation lane:

- `tests/test_runtime_scheduler_supervisor.py` -> package-health tests for operator dry-run scheduler config loading, due-cadence execution, disabled cadence skipping, and paper-only environment enforcement.
- `tests/test_broker_truth_reconciliation.py` -> package-health tests for broker truth reconciliation run recording, critical mismatch blocking, broker truth refs, and UNKNOWN intent resolution.
- `tests/test_paper_eligibility_path.py` -> package-health tests for full-evidence PAPER_ELIGIBLE latest-L6 authority creating only a local paper intent and incomplete evidence blocking before intent creation.
- `scripts/trader_brain_3531_3560_runtime_scheduler_broker_truth_paper_eligibility_validate.py` -> validates code contracts, config/scripts, package tests, report, manifest, registry, operating-state, Obsidian, LLM wiki, and status boundary closeout.

Authority:

- `PACKAGE_HEALTH` for `src/app/runtime_scheduler_supervisor.py`, `src/app/broker_truth_reconciliation.py`, `src/execution/paper_eligibility_path.py`, and `src/state/store.py`.
- `GOVERNANCE_HEALTH` for scheduler config/scripts, report, registry, operating-state, Obsidian, LLM wiki, and status boundary closeout.

PASS means:

- the dry-run scheduler can be installed by an operator as a recurring diagnostic supervisor
- broker truth snapshots can be hashed, recorded, and used for local reconciliation evidence
- a PAPER_ELIGIBLE runtime path can create a local paper intent only when authority evidence is complete

PASS does not mean the scheduler was registered on the workstation, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, broker submit permission, live-order permission, or real-capital permission.

Task3561-Task3570 adds the operations cleanup and skillization validation lane:

- `scripts/trader_brain_3561_3570_ops_cleanup_skillization_validate.py` -> validates generated-cache cleanup evidence, cleanup audit rows, skillization backlog rows, task report, artifact manifest, registry rows, operating-state closeout, and Obsidian cockpit update.

Authority:

- `GOVERNANCE_HEALTH` for cleanup audit, skillization backlog, report, registry, operating-state, Obsidian, LLM wiki, and status boundary closeout.

PASS means:

- generated cache cleanup was performed and recorded
- evidence-bearing logs, DBs, Graphify outputs, external references, source data, and reports were not deleted without a retention or migration policy
- P0 skill candidates for scheduler operations and cleanup retention are recorded for future skill creation

PASS does not mean source/archive/DB/log deletion is approved, strategy acceptance, deployment readiness, broker truth completion, live-source readiness, paper-order permission, live-order permission, broker submission permission, or real-capital permission.

The other 20 must be mapped to Task746 canonical package candidates before they become official package health gates.

## Acceptance Evidence Rule

The 4 `ACCEPTANCE_EVIDENCE_REVIEW` tests are:

- `tests/test_t603_6_broker_trade_lineage.py`
- `tests/test_task600_4_broker_truth_exit_lifecycle.py`
- `tests/test_task600_6_broker_truth_closed_trade_capture.py`
- `tests/test_task602_4_order_replay_recovery.py`

PASS on these tests only means reviewable acceptance evidence exists.

PASS does not mean:

- broker truth complete
- strategy accepted
- deployment-ready
- real capital allowed

## Required CI Footer

Any future CI or validation report should end with:

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

## Next Pass Dependency

Task748 should use this map when cleaning skills, MD files, and subagents.

The important rule:

```text
Subagent and skill docs may reference test lanes,
but they must not say that passing tests means strategy acceptance or deployment readiness.
```
