# Task742 To Task729 Adapter Contract

## Purpose

This contract defines how Task742 pragmatic economic meaning packets may be converted into Task729 five-layer relation-engine inputs. It is a research-only adapter contract. It does not create assignment, trade action, ranking, sizing, outcome, or backtest eligibility outputs.

## Input Contract

The adapter consumes Task742 packet fields:

- Identity: `lifecycle_id`, `source_event_id`, `symbol`, `event_date`, `tradable_after_dt`
- Source family: `source_form_family`, `source_circuit`, `requirement_family`
- Meaning: `interpretation_state`, `economic_direction_hint`, `confidence_band`
- Readiness: `relation_ready_flag`, `relation_ready_tier`, `relation_ready_reason`
- Uncertainty: `ambiguity_flags`, `soft_uncertainty_flags`, `hard_blocker_flags`, `needed_confirmation`
- Trace: `pragmatic_basis_json`, `evidence_trace_json`, `rule_id`
- Guardrails: `direction_hint_trade_instruction_flag`, `trade_output_flag`, `score_output_flag`, `backtest_eligible_flag`, `outcome_used_for_assignment_flag`

## Output Contract

The adapter may emit only review inputs for Task729:

- `adapter_packet_id`
- `lifecycle_id`
- `source_event_id`
- `primitive_id`
- `symbol`
- `event_date`
- `tradable_after_dt`
- `source_trace`
- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `relation_ready_tier`
- `source_type_state`
- `source_directness_state`
- `evidence_strength_state`
- `evidence_brain_state`
- `economic_transmission_state`
- `financing_context_state`
- `funding_path_state`
- `dilution_overhang_state`
- `invalidation_condition`
- `adapter_gate_state`
- `adapter_relation_permission`
- `assignment_allowed_flag`
- `backtest_allowed_flag`
- `real_capital_status`

Required constant guardrails:

- `assignment_allowed_flag = 0`
- `backtest_allowed_flag = 0`
- `real_capital_status = FORBIDDEN`

## Mapping Rules

1. If raw source trace or primitive trace is missing, emit `adapter_gate_state = source_gap`.
2. If Task742 `relation_ready_tier = not_ready`, emit `adapter_gate_state = not_ready`.
3. If Task742 `relation_ready_tier = context_only`, emit `adapter_gate_state = context_only` and `adapter_relation_permission = context_attachment_allowed`.
4. If Task742 `relation_ready_tier = structural_mixed`, emit `adapter_gate_state = cap` unless confidence is high/medium and no hard blocker exists.
5. If Task742 `relation_ready_tier = directional`, confidence is high/medium, and hard blockers are empty, emit `adapter_gate_state = pass`.
6. Positive/negative `economic_direction_hint` may map into L2 relation inputs only when `adapter_gate_state = pass`.
7. Mixed meaning may map only to modifier or confidence-cap relation states.
8. Neutral or unknown meaning cannot create a directional relation edge.
9. Price, slot, or risk states cannot override `source_gap`, `not_ready`, or `context_only`.
10. The adapter must preserve uncertainty fields for review instead of converting missing information into negative labels.

## Task729 Relation State Targets

Recommended state translations:

| Condition | Task729 state target |
| --- | --- |
| Source/primitive missing | `evidence_brain_state = source_gap_unknown_not_negative` |
| Direct company operating source with trace | `source_type_state = company_direct_source` |
| Filing-only ownership/Form4 context | `source_type_state = ownership_or_filing_source` |
| Medium/high confidence directional growth funding | `economic_transmission_state = growth_funding_path_visible` |
| Medium/high confidence dilution overhang | `funding_path_state = funding_need_with_overhang`; `dilution_overhang_state = dilution_overhang_unabsorbed` |
| Structural mixed activist/control context | `economic_transmission_state = control_or_ownership_structure_modifier` |
| Context-only Form4 planned sale/compensation | `economic_transmission_state = no_clear_source_backed_economic_path` |
| Needed confirmation exists | `invalidation_condition = invalid_if_required_confirmation_fails` |

## Primitive Gate Handoff

Task761 does not repair Task729 code. It defines the handoff field that a later repair can consume:

- `primitive_fact_adapter_gate_state`
- allowed values: `pass`, `cap`, `context_only`, `not_ready`, `source_gap`
- default if absent: `not_ready`

The later implementation must not infer primitive gate pass from price behavior, slot state, outcome labels, or backtest results.

## Representative Replay Audit

`adapter_representative_replay_examples.csv` is the required shallow-work guardrail for this contract. It gives ten deterministic Task742 packet examples and maps each one to:

- `adapter_gate_state`
- `adapter_relation_permission`
- intended Task729 review effect
- uncertainty or missing-context flags
- forbidden output list
- `outcome_or_future_return_used = 0`

The replay sample is deliberately not a return sample, PnL sample, or candidate ranking sample. It exists only to confirm the adapter rules can handle real Task742 rows without silently creating assignment, score, sizing, or backtest eligibility.

## Forbidden Outputs

The adapter must never emit:

- `buy`
- `sell`
- `rank`
- `score`
- `size`
- `position`
- `pnl`
- `return`
- `win`
- `loss`
- `label`
- `outcome`
- `backtest_eligible = 1`
- `assignment_allowed = 1`

## Acceptance Boundary

This contract is research-only. It can support future relation-engine repair, but it does not approve a strategy, deployment, broker use, real capital, or backtest promotion.
