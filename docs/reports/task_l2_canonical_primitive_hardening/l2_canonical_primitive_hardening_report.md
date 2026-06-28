# L2 Canonical Primitive Hardening Report

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Objective: harden L2 so primitive facts and local features become canonical, traceable, source-time-safe inputs into L3.
- Target metrics: required L2 contract fields exist; runtime contexts are mandatory; validators pass; trade/score/order-intent flags remain zero; historical artifacts cannot be live evidence.
- Forbidden actions: no inferred lifecycle matching, no fake source, no label leakage, no missing-source negative evidence, no strategy acceptance, no deployment readiness, no broker mutation, no paper order intent, no live order, no BUY/SELL signal, no L3/L4/L5/L6 promotion.
- Available raw sources: local runtime DB schema patterns for `market_bars_5m`, `indicator_snapshots`, and current readiness registry; historical Task740/Task741 default artifact paths are known.
- Missing raw sources: local Task740/Task741/Task742 artifact files referenced by the attachment are not present in this workspace; production L1 source receipt ids for runtime market bars and indicator snapshots still need a wiring task.
- Owner team: Data & Market Microstructure.
- Reviewer team: Research Governance.
- Artifact location: `docs/reports/task_l2_canonical_primitive_hardening/`.
- Completion criteria: contract docs, L2 package scaffold, market/indicator builders, schema setup, historical ingest script, L3/L2 validators, complexity audit, registry row, and validation results.
- Failure criteria: any validator permits mixed historical/live context, stale fresh-pass, missing source as negative, or nonzero trade/score/order-intent flags.
- Next action: wire L1 receipt/freshness evidence into the runtime loop and write live diagnostic L2 batches from closed source rows only.

## Quant Expert Report

### Problem Summary

The attachment identifies L2 as the boundary between L1 source receipt/freshness/lineage and L3 economic meaning. The core risk is not lack of more features. The core risk is that historical research packets and live intraday evidence can be confused unless L2 has a canonical contract.

### Historical/Live Confusion Explanation

Historical artifacts must enter L2 as `HISTORICAL_RESEARCH`. Live/runtime evidence must enter L2 as `LIVE_INTRADAY_DIAGNOSTIC`. A Task740/741/742 CSV artifact is not live evidence and cannot be consumed by live L3 without first being ingested into canonical L2 with historical context.

### Files Added

- `docs/contracts/l2_canonical_primitive_contract.md`
- `docs/architecture/l2_runtime_context_policy.md`
- `docs/architecture/l2_historical_live_separation_policy.md`
- `src/l2/`
- `src/brain/l2_to_meaning_adapter.py`
- `scripts/ingest_task740_task741_artifacts_to_l2.py`
- `scripts/validate_l2_canonical_primitive_contract.py`
- `scripts/validate_l2_historical_live_separation.py`
- `scripts/validate_l2_no_trade_outputs.py`
- `scripts/validate_l3_inputs_are_l2_canonical.py`
- `tests/test_l2_canonical_primitive_hardening.py`
- `docs/reports/task_l2_canonical_primitive_hardening/l2_code_complexity_audit.md`
- `docs/reports/task_l2_canonical_primitive_hardening/task_l2_canonical_primitive_hardening_decision.csv`

### Files Modified

- `tools/db/apply_management_schema.py`
- `tasks/task_registry.csv`

### L2PrimitiveFact Contract

`L2PrimitiveFact` is implemented in `src/l2/contracts.py` with mandatory ids, receipt, family, provider, source/capture/available/asof timestamps, primitive type/subtype/payload, freshness, source-time certification, closed-bar flag, runtime context, input/output hashes, lineage edge, diagnostic-only status, and zero trade/score/order-intent flags.

### L3 Adapter Status

`src/brain/l2_to_meaning_adapter.py` adds a thin canonical adapter that reads L3 inputs through `src/l2/stores/primitive_reader.py`. It does not create economic meaning, promote strategy state, or read Task CSVs directly.

### Runtime Context Rules

Allowed contexts are `HISTORICAL_RESEARCH`, `BACKTEST_RESEARCH`, `LIVE_INTRADAY_DIAGNOSTIC`, and `OPERATOR_REPLAY_DIAGNOSTIC`. A primitive batch may contain exactly one context. Historical artifacts and live intraday evidence must never share a batch.

### Market/Indicator Primitive Builder Status

`build_market_bar_primitives()` creates closed 5-minute bar primitives only and excludes open bars. `build_indicator_primitives()` creates diagnostic-only local feature primitives, inherits stale parent freshness, and excludes score/action/side/entry/order-intent fields from payloads.

### Historical Artifact Ingest Status

`scripts/ingest_task740_task741_artifacts_to_l2.py` ingests Task740/Task741-style CSV artifacts as `HISTORICAL_RESEARCH` only, attaches artifact hash and lineage, and never marks them as `LIVE_INTRADAY_DIAGNOSTIC`. The default Task740/Task741 paths are missing in this local workspace, so the script reports missing artifacts instead of approximating them.

### Validators And Results

- `python -m unittest tests.test_l2_canonical_primitive_hardening` passed: 5 tests.
- `python scripts/validate_l2_canonical_primitive_contract.py` passed with `[L2_CONTRACT_OK]`.
- `python scripts/validate_l2_historical_live_separation.py` passed with `[L2_HISTORICAL_LIVE_OK]`.
- `python scripts/validate_l2_no_trade_outputs.py` passed with `[L2_NO_TRADE_OUTPUT_OK]`.
- `python scripts/validate_l3_inputs_are_l2_canonical.py` passed with `[L3_L2_INPUT_OK]`.
- `python -m unittest tests.test_db_source_acquisition_scheduler_scripts` passed: 3 tests.
- `python -m unittest tests.test_l0_source_acquisition_hardening` passed: 8 tests.
- `python scripts/task_registry_validate.py` passed with `[REGISTRY_OK]`.
- `python scripts/codeowners_coverage_validate.py` passed with `[CODEOWNERS_OK]`.
- `python validate_readiness_registry.py` passed with `[READINESS_REGISTRY_OK]`.
- `python scripts/operating_closeout_validate.py` passed with `[OPERATING_CLOSEOUT_OK]`.
- `python scripts/governance_completion_audit.py` passed with `[GOVERNANCE_COMPLETE]` and an existing warning: `protected DB authority not DVC-tracked: data/task388_intraday_canonical_continuation_engine.db`.

### Data Integrity

- Inferred matching used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Diagnostic-only or deployment-ready: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Exact join keys: not applicable; this task adds source receipt and lineage primitives, not a label join.
- Leakage audit: no labels or outcomes enter L2 builders or validators.
- Split/OOS metrics: not applicable; no strategy claim is made.
- Cost/slippage stress: not applicable; no PnL claim is made.

### Remaining Blockers

- Runtime market bars and indicator snapshots still need L1 source receipt/freshness ids wired into the runner path.
- Historical Task740/Task741/Task742 artifacts referenced by the attachment are absent in this local workspace.
- News, SEC, macro, and microstructure primitive builders are scaffolded but not source-wired.
- L3 adapters must be updated in a later task to call canonical L2 reader functions only.

### Safety Boundaries Preserved

This task does not grant strategy acceptance.
This task does not grant deployment readiness.
This task does not grant paper trading.
This task does not grant live trading.
This task does not permit broker mutation.
This task does not create order intent.
This task does not make L2 features trade signals.

## No-Background Decision-Maker Report

L2 now has a formal contract and validation layer. It tells the system whether a fact is historical or live diagnostic, where it came from, whether it is fresh, and whether it is safe for L3 to read. This does not make the strategy tradable. It makes future evidence harder to misuse.

## Artifact Manifest

See `artifact_manifest.csv`.

## Closeout Notes

- Validation results: task-specific tests, task-specific validators, related L0 tests, and operating closeout validators passed.
- Registry update: `TaskL2CanonicalPrimitiveHardening` added to `tasks/task_registry.csv`.
- Readiness update: no readiness promotion; strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.
- Next blocker: L1 receipt/freshness wiring for live diagnostic L2 batches.
