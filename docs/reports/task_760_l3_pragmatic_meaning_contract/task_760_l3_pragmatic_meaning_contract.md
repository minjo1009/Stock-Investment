# Task760 L3 Pragmatic Economic Meaning Contract

## Decision Summary

- Verdict: `L3_PRAGMATIC_MEANING_CONTRACT_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `economic_meaning`
- Owner team: Regime Research
- Reviewer team: Research Governance + Data & Market Microstructure
- Key metrics: Task742 currently has 3,443 pragmatic meaning packets, 2,159 relation-ready packets, 4 directional candidates, 231 structural mixed packets, 1,924 context-only attachments, 1,284 not-ready packets, and 0 trade-output violations.
- What changed: Task760 defines the L3 MeaningObject contract, a good-enough meaning taxonomy, a decision record, and a refreshed artifact manifest. No source code, tests, registries, Task756, Task759, Task761, or Task762 files were edited.
- Next action: Task762 can use the explicit L3 relation-ready and uncertainty fields when designing primitive gate repair, but cannot infer assignment, ranking, sizing, or backtest eligibility from them.

This task does not promote code, approve a strategy, approve deployment, or permit real capital.

## Quant Expert Report

### Objective

Task760 turns Task742 pragmatic economic meaning packets into an explicit L3 research contract. The contract makes practical economic interpretation available to downstream relation work while preserving uncertainty and forbidding trade effects.

Success criteria:

```text
Meaning objects cannot emit buy/sell/rank/sizing/backtest eligibility; uncertainty remains explicit.
```

### Inputs Reviewed

- `docs/ownership/subagent_packet_standard.md`
- `docs/report_standard.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/reports/task_757_brain_dependency_dag_supersession/task_757_brain_dependency_dag_supersession.md`
- `docs/reports/task_758_l1_evidence_contract/l1_evidence_contract.md`
- `docs/reports/task_759_l2_primitive_fact_contract/task_759_l2_primitive_fact_contract.md`
- `docs/reports/task_742_pragmatic_economic_meaning_layer/task_742_pragmatic_economic_meaning_layer.md`
- `docs/reports/task_761_task742_to_task729_adapter_contract/task742_task729_adapter_contract.md`
- `src/backtest/pragmatic_economic_meaning_layer.py`
- `tests/test_task742_pragmatic_economic_meaning_layer.py`

### Contract Summary

The contract is stored in `l3_pragmatic_meaning_contract.md`.

The L3 MeaningObject requires:

- primitive references and source trace
- source family and source circuit
- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- ambiguity and soft uncertainty
- hard blockers
- needed confirmation
- `relation_ready_tier`
- invalidation clue
- forbidden effects

Meaning states are practical review metadata. A direction hint is not a trade instruction. Meaning states are not buy/sell instructions. They do not create ranks, scores, sizing, candidate assignment, backtest eligibility, or real-capital permission.

### Good-Enough Taxonomy

The taxonomy is stored in `meaning_taxonomy.csv`.

It covers current-data meaning families for:

- financing growth funding, survival or refinancing funding, and dilution overhang
- guidance raise, reaffirm, cut, and soft/unclear guidance
- demand and supply pressure
- margin and cost pressure
- contract and customer quality
- Form 4 planned sale, non-plan sale, purchase, and context-only insider activity
- passive ownership, active/control ownership, and ownership context
- macro and policy context

The taxonomy deliberately uses good-enough current facts and explicit uncertainty. It does not require every possible denominator. Missing context remains uncertainty, not a negative label.

### Task759 Consumption Boundary

Task760 can consume Task759 PrimitiveFact-style primitives when available. The L3 MeaningObject treats primitive references as source-local factual inputs:

- `primitive_fact_id`
- `primitive_source_task`
- `primitive_rule_id`
- `primitive_fact_family`
- `primitive_as_of_ts`
- `primitive_evidence_span_ref`
- `primitive_extraction_confidence`

If a primitive trace is missing, the object must use `source_gap` or `not_ready` handling. It must not repair missing primitive identity through symbol, date, price, time, outcome, or proximity fallback matching.

### Task761 And Task762 Handoff

Task760 feeds Task761 and Task762 only through review fields:

- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `relation_ready_tier`
- `ambiguity`
- `soft_blockers`
- `hard_blockers`
- `needed_confirmation`
- `invalidation_clue`
- `forbidden_effects`

Allowed downstream interpretation:

- `directional` means positive or negative economic direction is reviewable when source and primitive traces are present.
- `structural_mixed` means the packet may create a modifier or confidence-cap relation for review.
- `context_only` means the packet may attach context but cannot create a directional edge.
- `not_ready` means no relation edge should be created.

Forbidden downstream interpretation:

- No buy/sell/rank/sizing/allocation output.
- No assignment output.
- No score output.
- No backtest eligibility.
- No real-capital permission.
- No price rescue of weak sources.
- No missing context to negative conversion.
- No inferred lifecycle matching.
- No symbol/date/price/time fallback matching.

### Leakage Audit

Task760 is document-only and introduces no outcome, return, PnL, win/loss, future price, or assignment field. Direction hints remain review metadata. Labels and outcomes are evaluation-only and must not enter L3 assignment logic.

### Split/OOS Metrics

Not applicable. Task760 is a research contract task, not a strategy test. No split, OOS, PnL, win rate, return, cost, or slippage metric was created.

### Cost/Slippage Stress

Not applicable. Task760 does not create trades, positions, orders, fills, backtests, or PnL.

### Remaining Blockers

- Task759 is now a completed research-only L2 contract, but its contract is not yet implemented in the live relation engine.
- Task762 still needs to design the primitive gate repair before Task729 can consume explicit gate states.
- Task764 may later refine circuit-specific good-enough interpretation policy.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

### Validation

Validation authority: diagnostic/research contract validation only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Commands run:

```text
python -m unittest tests.test_task742_pragmatic_economic_meaning_layer
python scripts/trader_brain_program_validate.py
```

Observed result:

```text
Task742 unittest: 3 tests ran, OK.
Trader Brain program validator: [TRADER_BRAIN_PROGRAM_OK] Task756 parent and Task757-Task771 steps are registered.
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

1. Conclusion: Task760 defines the L3 meaning contract only.
2. It keeps Task742 useful, but still research-only.
3. Direction hints are review metadata, not trades.
4. Missing data stays uncertainty, not a negative label.
5. Task761/762 may consume the fields as gate and relation inputs only.
6. This does not change capital, deployment, or strategy status.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_760_l3_pragmatic_meaning_contract.md` | report | Task760 decision and expert report. |
| `l3_pragmatic_meaning_contract.md` | contract | MeaningObject field and boundary contract. |
| `meaning_taxonomy.csv` | taxonomy | Good-enough L3 meaning states using current data only. |
| `task_760_decision.csv` | decision | Machine-readable Task760 decision record. |
| `artifact_manifest.csv` | manifest | File sizes and hashes for Task760 artifacts. |

Row counts:

- `meaning_taxonomy.csv`: 24 data rows.
- `task_760_decision.csv`: 1 data row.
- `artifact_manifest.csv`: regenerated after artifact updates.

Validation commands:

```text
python -m unittest tests.test_task742_pragmatic_economic_meaning_layer
python scripts/trader_brain_program_validate.py
```

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
