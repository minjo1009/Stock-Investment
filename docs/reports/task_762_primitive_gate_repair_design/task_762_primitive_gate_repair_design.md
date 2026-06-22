# Task762 Primitive Fact Gate Repair Design

## Decision Summary

- Verdict: `PRIMITIVE_GATE_REPAIR_DESIGN_COMPLETE_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `relation_edge`
- Owner team: Backtest & Simulation Infra
- Reviewer team: Research Governance + Regime Research
- Objective: Define the bounded repair design that replaces fixed `primitive_fact_gate_pass = 0` behavior with explicit L2/L3 adapter gate input.
- What changed: Task762 now defines the primitive gate enum, minimal input fields, Task729 state mapping, code-touch boundary, guardrails, and acceptance examples for a later parent implementation.
- Parent implementation update: The narrow Task729 gate path has now been repaired in `src/backtest/five_layer_interaction_engine.py` and covered by focused Task729 tests. No assignment, rank, sizing, backtest eligibility, deployment, or real-capital permission was created.
- Next action: Use the repaired gate path as the input boundary for Task763 typed relation edges.

## Quant Expert Report

### Current Finding

Task761 established the adapter handoff from Task742 pragmatic economic meaning into Task729 relation-engine input. The key handoff field is:

```text
primitive_fact_adapter_gate_state
```

Allowed values are:

```text
pass
cap
context_only
not_ready
source_gap
```

The current Task729 relation engine still contains a hard-coded primitive gate bottleneck:

```text
src/backtest/five_layer_interaction_engine.py
resolve_candidate()
primitive_fact_gate_pass = 0
```

This means even source-backed, medium/high confidence Task742 packets cannot explicitly enter the Task729 primitive gate. The repair should consume the adapter gate state instead of inferring primitive readiness from price, slot, outcome, or backtest behavior.

### Minimal Implementation Target

The complete implementation target is defined in `primitive_gate_repair_contract.md`.

Required minimal input field:

- `primitive_fact_adapter_gate_state`

Recommended trace fields:

- `primitive_id`
- `source_event_id`
- `source_trace`
- `evidence_trace_json`
- `relation_ready_tier`
- `confidence_band`
- `hard_blocker_flags`
- `needed_confirmation`
- `adapter_relation_permission`

Default behavior:

- Missing `primitive_fact_adapter_gate_state`: treat as `not_ready`.
- Blank or invalid value: treat as `not_ready`.
- Missing source or primitive trace already represented by adapter: use `source_gap`.
- No missing field may become a negative label.
- No price, slot, return, PnL, or outcome field may rescue a missing or weak primitive gate.

### Gate Mapping

| Gate state | Task729 primitive flag | Relation effect | Final actionability effect |
| --- | ---: | --- | --- |
| `pass` | `1` | Relation review may use source-backed primitive meaning. | Review-only readiness; still no backtest eligibility. |
| `cap` | `0` | Confidence cap, confirmation-needed, invalidation, or hard-blocker relation remains active. | Watch or blocked research-only state. |
| `context_only` | `0` | Context attachment only; no directional edge. | Research-only context state. |
| `not_ready` | `0` | Primitive relation is not ready. | Needs primitive facts. |
| `source_gap` | `0` | Source repair or source-gap blocker. | Source-gap blocked. |

`pass` may set `primitive_fact_gate_pass_flag = 1`, but it must not set `backtest_eligible_flag = 1`, assignment permission, trade action, rank, score, or sizing. The repaired implementation uses review-only wording and does not imply backtest candidacy by itself.

Visible provenance fields:

- `primitive_fact_adapter_source_task`
- `primitive_fact_adapter_source_packet_id`
- `primitive_fact_gate_reason`

If these fields are absent from the row, the engine emits `not_supplied` instead of inferring provenance.

### Exact Code-Touch Boundary For Later Parent Implementation

Allowed function changes in `src/backtest/five_layer_interaction_engine.py`:

- `resolve_candidate()`: replace the fixed `primitive_fact_gate_pass = 0` with normalized adapter gate consumption from the row.
- `final_actionability()`: accept either the normalized gate state or derived primitive pass flag, and keep all outputs research-only.
- A small helper may be added near `state()` such as `primitive_fact_gate_state(row)` or `primitive_fact_gate_pass_flag(row)`.

Allowed data-shape change:

- Add a resolution output field such as `primitive_fact_gate_state` if the later test expects visible state trace.

Functions that must not be rewritten for Task762 implementation:

- `evaluate_interaction_frame()`
- `evaluate_candidate_edges()`
- `l1_l2_evidence_gate()`
- `l1_l2_source_economic_contradiction()`
- `l2_l3_thesis_confirmation()`
- `l2_l5_thesis_invalidation()`
- `l3_l4_slot_adjustment()`
- `l4_l5_budget_interaction()`
- `all_layer_final_gate()`
- `positive_economic()`
- `is_stale_or_reaffirmed()`
- `make_edge()`

Do not rewrite the whole interaction engine, rule-family catalog, builder, or historical Task729 artifacts in the parent repair. This is a narrow gate-path repair.

### Parent Implementation Applied

After the contract was written, the parent run applied the narrow Task762 gate-path repair.

Changed code boundary:

- `src/backtest/five_layer_interaction_engine.py`
- `tests/test_task729_five_layer_interaction_engine_application.py`

Implementation behavior:

- `resolve_candidate()` now consumes `primitive_fact_adapter_gate_state`.
- Valid gate states are normalized to `pass`, `cap`, `context_only`, `not_ready`, and `source_gap`.
- Missing, blank, or invalid gate state defaults to `not_ready`.
- `primitive_fact_gate_pass_flag` is `1` only when the normalized state is `pass`.
- `primitive_fact_gate_state` is exposed in the interaction resolution output for audit.
- `primitive_fact_adapter_source_task`, `primitive_fact_adapter_source_packet_id`, and `primitive_fact_gate_reason` are exposed in the interaction resolution output for adapter provenance.
- `pass` can only produce `REVIEW_ONLY_PRIMITIVE_FACTS_READY`.
- Existing blocker, invalidation, confidence cap, and source gate failures keep priority over primitive pass.
- `backtest_eligible_flag` remains `0`.
- `interaction_engine_assignment_allowed_flag` remains `0`.
- `real_capital_status` remains `FORBIDDEN`.

Implementation audit file:

- `task762_gate_repair_implementation_audit.csv`

### Acceptance Examples

The acceptance examples are derived from Task761 replay concepts. They are contract examples only, not trading examples.

| Example | Input concept | Gate state | Expected Task729 effect | Forbidden effect |
| --- | --- | --- | --- | --- |
| Directional pass | Direct company evidence, primitive trace, medium/high confidence growth-funding path, no hard blocker. | `pass` | `primitive_fact_gate_pass_flag = 1`; relation review can preserve reinforcing L2/L3 edge. | No buy/sell/rank/sizing/backtest eligibility. |
| Structural cap | Structural mixed activist/control or ownership context with ambiguity. | `cap` | Confidence cap or modifier review; primitive pass flag remains `0`. | No directional economic edge by itself. |
| Context-only | Planned Form 4 sale, stale 13F, or passive ownership context. | `context_only` | Context attachment only; no directional edge. | No negative label from missing denominator. |
| Not-ready | Interpretation exists but relation-ready tier is `not_ready` or needed confirmation is unresolved. | `not_ready` | `RESEARCH_ONLY_NEEDS_PRIMITIVE_FACTS` or equivalent review-only state. | No price rescue. |
| Source-gap | Missing raw source trace, missing primitive identity, or adapter reports source trace gap. | `source_gap` | Source-gap blocker or repair-needed state. | No fallback matching by symbol/date/price/time. |
| Hard-blocker cap/block | Financing overhang, survival funding, or hard blocker flags contradict a positive meaning packet. | `cap` | Existing blocker/invalidation/confidence-cap edge remains dominant. | No pass override from positive direction hint. |

### Leakage And Matching Audit

- Inferred lifecycle matching used: `NO`.
- Symbol/date/price/time fallback matching used: `NO`.
- Future returns/outcomes used: `NO`.
- Labels or outcomes used for gate assignment: `NO`.
- Missing labels treated as negatives: `NO`.
- Gate state creates backtest eligibility by itself: `NO`.

### Validation Authority

Validation authority is diagnostic/research contract validation only.

Planned and requested commands:

```text
python -m unittest tests.test_task729_five_layer_interaction_engine_application
python scripts/trader_brain_program_validate.py
```

Additional parent implementation validation:

```text
python -m unittest tests.test_task728_five_layer_interaction_logic_contract tests.test_task729_five_layer_interaction_engine_application
python scripts/trader_brain_second_batch_validate.py
```

Passing these commands means the research contract and current Task729 regression surface did not detect a local regression. Passing does not mean strategy acceptance, deployment readiness, broker truth, live readiness, or real-capital permission.

## No-Background Decision-Maker Report

1. Done: Task762 gate repair design is complete.
2. Done: The fixed primitive gate value in Task729 has been removed.
3. Done: Task729 now reads `primitive_fact_adapter_gate_state`.
4. Allowed states are `pass`, `cap`, `context_only`, `not_ready`, and `source_gap`.
5. `pass` only means relation review can proceed.
6. It does not mean buy, sell, rank, sizing, backtest eligibility, deployment, or real capital.
7. The code change stayed narrow: repaired the gate path only.

## Artifact Manifest

Inputs:

- `docs/ownership/subagent_packet_standard.md`
- `docs/report_standard.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `docs/architecture/src_canonicalization_map.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/reports/task_757_brain_dependency_dag_supersession/task_757_brain_dependency_dag_supersession.md`
- `docs/reports/task_758_l1_evidence_contract/l1_evidence_contract.md`
- `docs/reports/task_759_l2_primitive_fact_contract/task_759_l2_primitive_fact_contract.md`
- `docs/reports/task_760_l3_pragmatic_meaning_contract/task_760_l3_pragmatic_meaning_contract.md`
- `docs/reports/task_761_task742_to_task729_adapter_contract/task742_task729_adapter_contract.md`
- `src/backtest/five_layer_interaction_engine.py`
- `tests/test_task729_five_layer_interaction_engine_application.py`

Outputs:

- `task_762_primitive_gate_repair_design.md`
- `primitive_gate_repair_contract.md`
- `gate_state_catalog.csv`
- `task_762_decision.csv`
- `artifact_manifest.csv`

Row counts:

- `gate_state_catalog.csv`: 5 data rows.
- `task_762_decision.csv`: 1 data row.

Changed files:

- `docs/reports/task_762_primitive_gate_repair_design/task_762_primitive_gate_repair_design.md`
- `docs/reports/task_762_primitive_gate_repair_design/primitive_gate_repair_contract.md`
- `docs/reports/task_762_primitive_gate_repair_design/gate_state_catalog.csv`
- `docs/reports/task_762_primitive_gate_repair_design/task_762_decision.csv`
- `docs/reports/task_762_primitive_gate_repair_design/artifact_manifest.csv`

Commands run:

- `python -c "import csv, pathlib; base=pathlib.Path('docs/reports/task_762_primitive_gate_repair_design'); files=['gate_state_catalog.csv','task_762_decision.csv']; [list(csv.DictReader((base/f).open(newline='',encoding='utf-8-sig'))) for f in files]; print('task762_csv_ok')"` -> PASS.
- `python scripts/task_artifact_manifest.py --task-dir 'docs/reports/task_762_primitive_gate_repair_design'` -> PASS.
- `python -m unittest tests.test_task729_five_layer_interaction_engine_application` -> PASS, 5 tests.
- `python scripts/trader_brain_program_validate.py` -> PASS.

Commands not run:

- None.

Source hashes:

- Stored in `artifact_manifest.csv`.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
