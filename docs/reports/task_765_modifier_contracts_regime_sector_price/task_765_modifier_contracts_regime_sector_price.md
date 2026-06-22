# Task765 Regime Sector Price Modifier Contracts

## Decision Summary

- Verdict: `MODIFIER_CONTRACTS_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `relation_edge`
- Owner team: Regime Research
- Reviewer team: Research Governance + Backtest & Simulation Infra
- Key metrics: 6 modifier families defined; 7 allowed modifier states; 0 allowed buy/sell/rank/sizing/backtest effects.
- What changed: Replaced the Task765 placeholder report, added the Modifier object contract, added the modifier state catalog, refreshed the decision row, and regenerated the artifact manifest.
- Next action: Task766 can use this contract to define compound interaction rules without building a giant brittle rule tree.

Task765 is a research-only contract task. It does not promote code, create a candidate, approve a strategy, approve deployment, permit real capital, or create buy/sell/rank/sizing/backtest eligibility.

## Quant Expert Report

### Objective

Task765 defines market regime, sector leadership, theme rotation, price acceptance, extension risk, and exposure cluster as modifiers attached to already-source-backed L2/L3 meaning. Modifiers are not standalone signals.

The intended flow is:

```text
L1 source evidence
-> L2 PrimitiveFact
-> L3 MeaningObject
-> Task765 modifier review
-> typed relation edge review
-> future compound interaction review
```

### Inputs Reviewed

- `docs/operating_system/project_operating_state.md`
- `docs/ownership/subagent_packet_standard.md`
- `docs/report_standard.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/architecture/src_canonicalization_map.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/reports/task_759_l2_primitive_fact_contract/primitive_fact_contract.md`
- `docs/reports/task_759_l2_primitive_fact_contract/task_759_l2_primitive_fact_contract.md`
- `docs/reports/task_760_l3_pragmatic_meaning_contract/l3_pragmatic_meaning_contract.md`
- `docs/reports/task_760_l3_pragmatic_meaning_contract/task_760_l3_pragmatic_meaning_contract.md`
- `docs/reports/task_762_primitive_gate_repair_design/primitive_gate_repair_contract.md`
- `docs/reports/task_763_typed_relation_edge_schema/task_763_typed_relation_edge_schema.md`
- `docs/reports/task_648_trading_context_state_engine/task_648_trading_context_state_engine.md`
- `docs/reports/task_649_macro_context_state_engine/task_649_macro_context_state_engine.md`
- `docs/reports/task_668_regime_theme_playbook/task_668_regime_theme_playbook.md`
- `docs/reports/task_672_current_data_state_axis_panel/task_672_current_data_state_axis_panel.md`
- `src/backtest/five_layer_interaction_engine.py`
- `tests/test_task728_five_layer_interaction_logic_contract.py`

### Contract Summary

The canonical contract is `modifier_contracts.md`.

Required fields:

- `modifier_id`
- `modifier_family`
- `state`
- `source_inputs`
- `asof_state`
- `applies_to_layer`
- `relation_effect`
- `confidence_cap`
- `invalidation_link`
- `allowed_effect`
- `forbidden_effects`

The allowed modifier families are:

- `market_regime`
- `sector_leadership`
- `theme_rotation`
- `price_acceptance`
- `extension_risk`
- `exposure_cluster`

The allowed states are:

- `supportive`
- `hostile`
- `rotating`
- `extended`
- `accepted`
- `rejected`
- `unclear`

These states are intentionally small. They preserve the user's distinction that a good or bad market regime is not the same object as sector or theme rotation. Market regime may describe broad risk appetite; sector leadership and theme rotation describe where participation is moving; price acceptance and extension risk describe confirmation or stretch; exposure cluster describes concentration pressure.

### Allowed Relation Effects

Modifiers may only affect an already-eligible relation review packet through:

- `reinforcing`
- `offsetting`
- `prerequisite`
- `blocker`
- `confidence_cap`
- `invalidation`

Allowed practical effects are:

- reinforce an existing L2/L3 meaning when source and primitive gates already allow relation review
- cap confidence when context is hostile, extended, crowded, stale, or uncertain
- block relation use when a required state is rejected or source/as-of integrity fails
- require confirmation when leadership, rotation, price acceptance, or cluster context is unclear
- attach context for explanation without directional promotion
- link the modifier to an invalidation path

### Forbidden Effects

Modifiers cannot create or rescue:

- buy/sell/hold
- rank or score
- sizing, allocation, or portfolio budget
- candidate creation
- backtest eligibility
- strategy acceptance
- deployment readiness
- real-capital permission
- future return, PnL, win/loss, or outcome labels

Modifiers also cannot rescue `source_gap`, `context_only`, or `not_ready` primitive states. If L2/L3 is blocked because raw source, primitive identity, as-of trace, or relation readiness is missing, price acceptance, good market tape, sector leadership, or theme rotation may not override that block.

### Exact Join Keys

Task765 creates no data join and no code implementation. Future implementations may use only upstream-supplied identifiers:

- `modifier_id`
- upstream `lifecycle_id` when supplied
- `source_event_id`
- `primitive_fact_id`
- `meaning_object_id`
- `evidence_id`
- `issuer_symbol` as a source-attached attribute, not a proximity fallback
- `as_of_ts`
- explicit `entry_ts` only when already supplied by an upstream packet

Forbidden joins:

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback matching.
- No price rescue of weak or missing source evidence.
- No future outcome or return-based assignment.
- No missing label to negative conversion.

### Leakage Audit

Task765 is document-only. It introduces no future price, return, PnL, outcome label, performance score, assignment flag, order field, fill field, sizing field, or backtest eligibility field.

Price acceptance is treated only as a relation modifier. It is not economic meaning by itself. A price move without source-backed L2/L3 meaning can only be `offsetting`, `prerequisite`, `confidence_cap`, or `context_only` review metadata; it cannot become a candidate.

### Split/OOS Metrics

Not applicable. Task765 is a research contract and artifact task. It does not run a strategy, split, OOS test, optimization, replay, or simulation.

### Cost/Slippage Stress

Not applicable. Task765 creates no trades, orders, fills, allocations, sizes, PnL, or backtest-eligible rows.

### Remaining Blockers

- The modifier contract is not implemented in code.
- Task763 remains only a placeholder in this checkout, so Task765 aligns with the existing engine relation vocabulary but does not depend on a completed Task763 artifact.
- Task766 still must define compound interaction behavior using this small modifier set.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

### Validation

Validation authority: diagnostic/research contract validation only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Commands run:

```text
python -m unittest tests.test_task728_five_layer_interaction_logic_contract
python scripts/trader_brain_program_validate.py
```

Commands not run:

```text
None.
```

Inferred matching used:

```text
No.
```

## No-Background Decision-Maker Report

1. Done: Task765 now defines modifier contracts.
2. Done: Good market, bad market, sector leadership, theme rotation, price acceptance, extension, and cluster exposure are separated.
3. Done: Modifiers can reinforce, cap, block, or require confirmation only after L2/L3 meaning exists.
4. Done: Modifiers cannot create candidates or rescue source gaps.
5. No change: Strategy remains `NOT_ACCEPTED`.
6. No change: Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
7. No change: Real capital remains `FORBIDDEN`.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_765_modifier_contracts_regime_sector_price.md` | report | Task765 decision and expert report. |
| `modifier_contracts.md` | contract | Modifier object fields, allowed effects, and forbidden downstream effects. |
| `modifier_state_catalog.csv` | catalog | Seven-state catalog for market, sector, theme, price, extension, and exposure modifiers. |
| `task_765_decision.csv` | decision | Machine-readable Task765 decision record. |
| `artifact_manifest.csv` | manifest | File sizes and hashes for Task765 artifacts. |

Row counts:

- `modifier_state_catalog.csv`: 7 data rows.
- `task_765_decision.csv`: 1 data row.
- `artifact_manifest.csv`: regenerated after artifact updates.

Validation commands:

```text
python -m unittest tests.test_task728_five_layer_interaction_logic_contract
python scripts/trader_brain_program_validate.py
```

Validation authority: diagnostic/research contract validation only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Inferred matching used: no.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
