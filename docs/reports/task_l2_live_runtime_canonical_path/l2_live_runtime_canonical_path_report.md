# L2 Live Runtime Canonical Path Report

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: the existing live runtime market/indicator path now writes canonical L2 source receipts, primitive batches, primitive facts, lineage, and freshness records after `task_089` creates `indicator_snapshots`.
- Current completion claim: live runtime canonicalization is complete for the repo's implemented `market_bars_5m` and `indicator_snapshots` L2 path.
- Boundary: this does not claim canonical live wiring for news, SEC, macro, or microstructure families because their live L2 source tables are not present in this local runtime path.
- Next action: add source-backed L2 writers for news, SEC, macro, and microstructure only after their L1 receipt/freshness tables are available.

## Quant Expert Report

### Clarified Task List

| Task | Status | Evidence |
|---|---|---|
| Define live runtime L2 writer responsibilities | Complete | `src/l2/live_runtime.py` |
| Add source receipt ledger for runtime L2 | Complete | `l2_runtime_source_receipts` in `src/l2/stores/sqlite_l2_store.py` |
| Write market bar L2 facts from closed bars only | Complete | `write_live_runtime_l2_primitives()` queries `bar_end_ts <= capture_ts` |
| Write indicator L2 facts from `indicator_snapshots` | Complete | `task_089` calls `write_live_runtime_l2_primitives_from_db()` after snapshot upsert |
| Preserve stale/missing as blockers | Complete | parent market freshness propagates into indicator primitives |
| Prevent L2 trade outputs | Complete | payload excludes `score`, `side`, `action`, `entry_allowed`, and flags remain zero |
| Add live runtime canonical validator | Complete | `scripts/validate_l2_live_runtime_canonical_path.py` |
| Add regression tests | Complete | `tests/test_l2_live_runtime_canonical_path.py` |
| Preserve strategy/deployment/capital gates | Complete | readiness registry unchanged |

### Implementation Details

- `src/l2/live_runtime.py` creates deterministic source receipt ids for `market_bars_5m` and `indicator_snapshots`.
- `task_089_market_data_signal_refresh.py` now writes L2 canonical rows in both normal KIS and KIS-init-failure diagnostic branches.
- `l2_runtime_source_receipts` records source table, source family, provider, symbol set, capture/asof time, row count, hash, freshness, and diagnostic-only status.
- Market bar primitives use closed bars only.
- Indicator primitives inherit stale or missing parent market freshness.
- L3 canonical reads go through `load_l3_inputs()` or `load_canonical_l2_meaning_inputs()`, which exclude stale or source-time-uncertified rows by default.

### Data Integrity

- Inferred matching used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Live source freshness approximated as negative evidence: no.
- Label leakage: no labels or outcomes enter the L2 writer.
- Exact join keys: not applicable; this is source receipt and primitive lineage wiring, not lifecycle matching.
- Split/OOS metrics: not applicable; no strategy performance claim is made.
- Cost/slippage stress: not applicable; no PnL claim is made.

### Validation Results

- `python -m unittest tests.test_l2_live_runtime_canonical_path` passed: 2 tests.
- `python -m unittest tests.test_l2_canonical_primitive_hardening` passed: 5 tests.
- `python -m unittest tests.test_task_089_market_signal_refresh` passed: 5 tests.
- `python -m unittest tests.test_task583_live_signal_refresh_repair` passed: 4 tests.
- `python -m unittest tests.test_task584_runtime_strategy_decision_gate` passed: 3 tests.
- `python scripts/validate_l2_live_runtime_canonical_path.py` passed with `[L2_LIVE_RUNTIME_OK]`.
- `python scripts/validate_l2_canonical_primitive_contract.py` passed with `[L2_CONTRACT_OK]`.
- `python scripts/validate_l2_historical_live_separation.py` passed with `[L2_HISTORICAL_LIVE_OK]`.
- `python scripts/validate_l2_no_trade_outputs.py` passed with `[L2_NO_TRADE_OUTPUT_OK]`.
- `python scripts/validate_l3_inputs_are_l2_canonical.py` passed with `[L3_L2_INPUT_OK]`.
- `python scripts/task_registry_validate.py` passed with `[REGISTRY_OK]`.
- `python scripts/codeowners_coverage_validate.py` passed with `[CODEOWNERS_OK]`.
- `python validate_readiness_registry.py` passed with `[READINESS_REGISTRY_OK]`.
- `python scripts/operating_closeout_validate.py` passed with `[OPERATING_CLOSEOUT_OK]`.
- `python scripts/governance_completion_audit.py` passed with `[GOVERNANCE_COMPLETE]` and an existing warning: `protected DB authority not DVC-tracked: data/task388_intraday_canonical_continuation_engine.db`.

### Remaining Blockers

- News, SEC, macro, and microstructure live L2 builders remain source-blocked until source-specific L1 receipt/freshness tables exist.
- Runtime decision logic remains diagnostic; this task does not implement L3/L4/L5/L6 promotion.
- `runtime_strategy_decisions` is not treated as an L2 primitive source and remains outside L2 order-intent scope.

### Safety Boundaries Preserved

This task does not grant strategy acceptance.
This task does not grant deployment readiness.
This task does not grant paper trading.
This task does not grant live trading.
This task does not permit broker mutation.
This task does not create order intent.
This task does not make L2 features trade signals.

## No-Background Decision-Maker Report

The implemented live runtime L2 path now creates a canonical evidence trail when market bars and indicator snapshots are refreshed. L2 can say which runtime receipt produced each primitive, which batch it belongs to, whether it was fresh or missing, and whether L3 may read it. This is infrastructure hardening, not trading approval.

## Artifact Manifest

See `artifact_manifest.csv`.
