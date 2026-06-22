# Task766 Compound Interaction Engine Contract

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `relation_edge`
- Owner team: Backtest & Simulation Infra
- Reviewer team: Research Governance + Regime Research
- Key metrics: 1 contract, 12 rule examples, 1 decision row, 1 artifact manifest.
- What changed: Replaced the placeholder report and added a research-only compound interaction contract that emits `compound_state` only.
- Next action: Task767 may consume `compound_state` as explanatory input for candidate-bundle design, but cannot convert it into buy/sell, rank, sizing, slot, or backtest eligibility.

## Quant Expert Report

### Data source and source readiness

Task766 is a contract task. It does not create a data panel, trade panel, outcome label, return series, or executable strategy.

Read sources:

- Task756 step registry.
- Task759 `PrimitiveFact` contract.
- Task760 `MeaningObject` contract.
- Task762 primitive gate repair contract.
- Task763 typed `RelationEdge` schema.
- Task764 source circuit good-enough policy.
- Task765 modifier contracts.
- Current Task729 interaction engine and tests for compatibility context only.

Source readiness is `research_contract_ready`. It is not live-source readiness.

### Exact join keys

No inferred matching was used. The contract permits only explicit upstream ids and traces:

- `evidence_id`
- `source_event_id`
- `primitive_fact_id`
- `meaning_object_id`
- `edge_id`
- `modifier_id`
- `adapter_packet_id`
- `lifecycle_id` only when supplied upstream
- `as_of_ts` only as provenance, not a fallback key

The contract forbids symbol/date/price/time proximity fallback matching and inferred lifecycle matching.

### Leakage audit

No future returns, labels, PnL, win/loss, price outcomes, backtest results, or slot outcomes are allowed in compound state creation.

`price_acceptance` is a modifier only. Price is not meaning. Price cannot fill a missing source, primitive, or lifecycle link.

### Split/OOS metrics

Not applicable. This task is a research-only contract and does not run a backtest or estimate performance.

### Failure decomposition

Dominance is defined in `compound_interaction_engine_contract.md`:

1. `source_gap_blocked`
2. `hard_blocked`
3. `invalidated`
4. `not_ready`
5. `context_only`
6. `confidence_capped`
7. `confirmation_required`
8. `contradictory`
9. `reinforced_review`
10. `review_ready`

This precedence prevents modifier support, macro context, sector leadership, price acceptance, or broad regime support from rescuing `source_gap`, `context_only`, `not_ready`, blocker, cap, or invalidation states.

### Cost/slippage stress where PnL changed

Not applicable. No PnL, fills, costs, slippage, capital, orders, or execution outputs are produced.

### Remaining blockers

- This is not code promotion.
- Task767 must keep bundle output explanatory and research-only.
- Later implementation, if any, must preserve `compound_state` as a state label and must not add a numeric total score, rank, buy/sell action, slot decision, actual position sizing, backtest eligibility, or outcome field.

## No-Background Decision-Maker Report

Task766 is complete as a research contract.

It defines how primitive facts, meaning objects, relation edges, and modifiers combine into one review state named `compound_state`.

It does not approve a strategy. It does not make a trade. It does not size a position. It does not permit backtesting or deployment.

The important result is a safer handoff: future layers can read why a thesis is supported, capped, blocked, contradictory, or invalidated without receiving a hidden score.

## Artifact Manifest

Inputs:

- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/reports/task_759_l2_primitive_fact_contract/primitive_fact_contract.md`
- `docs/reports/task_760_l3_pragmatic_meaning_contract/l3_pragmatic_meaning_contract.md`
- `docs/reports/task_762_primitive_gate_repair_design/primitive_gate_repair_contract.md`
- `docs/reports/task_763_typed_relation_edge_schema/typed_relation_edge_schema.md`
- `docs/reports/task_764_source_circuit_good_enough_interpreters/source_circuit_good_enough_policy.md`
- `docs/reports/task_765_modifier_contracts_regime_sector_price/modifier_contracts.md`
- `src/backtest/five_layer_interaction_engine.py`
- `tests/test_task729_five_layer_interaction_engine_application.py`

Outputs:

- `compound_interaction_engine_contract.md`
- `compound_rule_examples.csv`
- `task_766_decision.csv`
- `artifact_manifest.csv`
- `task_766_compound_interaction_engine_contract.md`

Row counts:

- `compound_rule_examples.csv`: 12 example rows plus header.
- `task_766_decision.csv`: 1 decision row plus header.
- `artifact_manifest.csv`: 5 artifact rows plus header.

Validation commands:

- `python -m unittest tests.test_task729_five_layer_interaction_engine_application`
- `python scripts/trader_brain_program_validate.py`

Validation authority:

- Diagnostic/research contract validation only.
- Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Source hashes:

- See `artifact_manifest.csv`.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
