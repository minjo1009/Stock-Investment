# Task917-920 Multifamily Relation Adapter Design

## Decision Summary

- Verdict: implemented as research-only multifamily L1-L5 extension and adapter-input design.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Purpose: extend Task907-916 beyond SEC companyfacts by attaching the remaining source families, expanding the relation primitive system to nine, strengthening L4 contradiction and invalidation handling, and separating L5 adapter input from backtest execution.
- Source families expected: 6.
- Source families attached: 6.
- L1 evidence rows: 1,204.
- L2 primitive fact rows: 1,204.
- L2 economic meaning rows: 1,204.
- L3 relation edge rows: 14,157.
- Relation primitive catalog rows: 9.
- Relation primitives used in current source-backed edges: 6.
- L4 candidate bundle rows: 4,461.
- Candidate bundles with contradiction: 352.
- L5 dry decision rows: 4,461.
- Adapter schema rows: 14.
- Adapter input design rows: 4,461.
- Ready-for-backtest rows: 0.
- Replay status: `not_run_adapter_design_only`.
- Next action: convert adapter design into controlled harness input only after explicit side, entry, exit, sizing, tradable-after, market-data, cost, and slippage gates are defined and validated.

## Quant Expert Report

The implemented chain is:

```text
existing raw source families
-> L1 multifamily evidence
-> L2 primitive facts and economic meanings
-> L3 nine-primitive relation edge model
-> L4 candidate bundles with contradiction and invalidation diagnostics
-> L5 dry decisions
-> separate adapter input design
-> backtest no-go
```

Attached source families:

```text
company_filings_ir
earnings_guidance
macro_policy_official
supply_chain_customer_capex_cross_read
positioning_liquidity_volatility
sector_specialist_official_docs
```

The implementation uses bounded existing project sources. It does not invent missing raw documents. Missing or weak source support remains visible through source-gap and weakest-layer fields.

The relation primitive catalog is fixed to nine primitives:

```text
reinforces
weakens
invalidates
conditions
sequences
explains
contradicts
source_gap_for
noise_for
```

Current edges use six primitives because the validator forbids fabricated `invalidates`, `sequences`, or `contradicts` edges unless a source-backed trigger exists. The nine-primitive catalog is still present and enforced as the allowed relation system.

L4 was strengthened with these fields:

```text
contradicting_relation_ids
invalidation_relation_ids
source_gap_relation_ids
contradiction_state
invalidation_conditions
weakest_layer
unresolved_source_gaps
```

L5 adapter input is deliberately separated from execution. Adapter rows keep forbidden execution fields empty:

```text
side
entry_rule
exit_rule
position_size_rule
tradable_after_ts
market_data_manifest_id
cost_config_id
slippage_config_id
```

Leakage controls:

- Source rows carry published and brain-available timestamps.
- Validator requires `available_to_brain_ts >= published_ts`.
- L2 rows must reference admitted L1 evidence.
- L3 rows must reference L1 evidence and L2 meanings.
- L5 adapter design rows are not replay-ready.
- No price lookup, trade generation, PnL, or backtest engine call is performed.

Remaining blockers:

- Adapter execution fields are not yet defined.
- Market data manifest, cost config, slippage config, and split/OOS harness config are not attached to adapter rows.
- The source corpus is still bounded to existing local project evidence, not a complete institutional live-source corpus.
- Test success does not change strategy acceptance or deployment readiness.

## No-Background Decision-Maker Report

The requested four items were implemented in the project structure.

First, the remaining five source families were attached alongside the existing SEC family. Second, relation primitives now have a nine-item controlled catalog. Third, L4 now records contradiction, invalidation, weakest-layer, and source-gap diagnostics. Fourth, L5 adapter input is separated from backtest execution.

This does not mean the strategy is tradable. The adapter design intentionally blocks backtest readiness until the execution fields, market-data gate, cost/slippage gate, and split/OOS harness are explicitly completed.

## Artifact Manifest

- Script: `scripts/trader_brain_917_920_multifamily_relation_adapter.py`.
- Validator: `scripts/trader_brain_917_920_multifamily_relation_adapter_validate.py`.
- Test: `tests/test_trader_brain_917_920_multifamily_relation_adapter.py`.
- Source family attachment manifest: `data/artifacts/task_917_920_multifamily_relation_adapter/task917_source_family_attachment_manifest.csv`.
- L1 evidence: `data/artifacts/task_917_920_multifamily_relation_adapter/task917_multifamily_l1_evidence.csv`.
- L2 primitive facts: `data/artifacts/task_917_920_multifamily_relation_adapter/task918_multifamily_l2_primitives.csv`.
- L2 economic meanings: `data/artifacts/task_917_920_multifamily_relation_adapter/task918_multifamily_l2_meanings.csv`.
- Relation primitive catalog: `data/artifacts/task_917_920_multifamily_relation_adapter/task919_relation_primitive_catalog.csv`.
- L3 relation edges: `data/artifacts/task_917_920_multifamily_relation_adapter/task919_relation_edges_9primitive.csv`.
- L4 candidate bundles: `data/artifacts/task_917_920_multifamily_relation_adapter/task919_l4_candidate_bundles_contradiction.csv`.
- L5 dry decisions: `data/artifacts/task_917_920_multifamily_relation_adapter/task919_l5_dry_decisions.csv`.
- Adapter schema: `data/artifacts/task_917_920_multifamily_relation_adapter/task920_adapter_input_schema.csv`.
- Adapter input design rows: `data/artifacts/task_917_920_multifamily_relation_adapter/task920_adapter_input_design_rows.csv`.
- Summary: `data/artifacts/task_917_920_multifamily_relation_adapter/task917_920_summary.json`.
- Validation command: `python scripts/trader_brain_917_920_multifamily_relation_adapter_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
