# Task761 Task742 To Task729 Adapter Contract

## Decision Summary

- Verdict: `ADAPTER_CONTRACT_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `relation_edge`
- Owner team: Backtest & Simulation Infra
- Reviewer team: Research Governance + Regime Research
- Objective: Define the contract that lets Task742 pragmatic economic meaning packets enter the Task729 relation engine without creating trades, assignments, outcomes, or backtest eligibility.
- Decision: Task761 should be implemented as a document-only adapter contract. It should not modify Task729 code. The next implementation pass must consume explicit adapter/gate fields instead of leaving `primitive_fact_gate_pass_flag` fixed at 0.

## Quant Expert Report

### Current Finding

Task742 creates review-only pragmatic economic meaning packets with source identity, primitive trace, interpretation state, direction hint, confidence band, relation-ready tier, ambiguity, uncertainty, confirmation needs, and hard blocker fields. It also sets forbidden trade/backtest/output flags to zero.

Task729 currently evaluates five-layer relation states and correctly keeps assignment/backtest outputs disabled. However, the relation resolution still uses a fixed `primitive_fact_gate_pass = 0`, so better Task730/740/742 primitive and meaning packets are not strongly reinjected into the relation engine.

### Adapter Contract

Task761 defines an adapter packet, not a trading model.

Required adapter identity fields:

- `adapter_packet_id`
- `lifecycle_id`
- `source_event_id`
- `primitive_id`
- `symbol`
- `event_date`
- `tradable_after_dt`
- `source_trace`
- `task742_rule_id`

Required meaning fields:

- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `relation_ready_tier`
- `relation_ready_flag`
- `ambiguity_flags`
- `soft_uncertainty_flags`
- `hard_blocker_flags`
- `needed_confirmation`

Required relation input fields:

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

### Gate States

The adapter may emit only these gate states:

| adapter_gate_state | Meaning | Task729 effect |
| --- | --- | --- |
| `pass` | Source trace, primitive trace, and medium/high relation-ready meaning are present. | May feed L1/L2 relation inputs for review. |
| `cap` | Meaning is usable but confidence or ambiguity caps the relation. | Must create confidence-cap or confirmation-needed relation state. |
| `context_only` | Packet is useful context but not a directional relation edge. | May attach as context; cannot create directional edge. |
| `not_ready` | Packet lacks relation-ready interpretation. | Must not create relation edge. |
| `source_gap` | Raw source or primitive identity is missing. | Must block or leave source repair state. |

### Tier Mapping

| Task742 `relation_ready_tier` | Adapter permission | Allowed relation behavior |
| --- | --- | --- |
| `directional` | `relation_edge_review_allowed` | May map to positive/negative L2 relation input if source and primitive traces exist. |
| `structural_mixed` | `modifier_review_allowed` | May map to mixed/control/ownership modifier; no direction or trade signal. |
| `context_only` | `context_attachment_allowed` | May preserve source context only. |
| `not_ready` | `relation_edge_blocked` | No relation edge; repair or context review only. |

### Non-Negotiable Invariants

- No assignment output.
- No outcome fields.
- No buy/sell/rank/sizing/backtest eligibility field.
- No price rescue of weak, missing, or context-only source packets.
- Missing labels are not negatives.
- Labels/outcomes are not adapter inputs.
- Direction hints are review metadata, not trade instructions.
- `context_only` and `not_ready` packets cannot become directional Task729 edges.
- Any future Task729 primitive gate repair must remain research-only until separately validated.

### Validation Authority

Validation authority is research-only interaction validation. Passing tests or document checks does not change strategy acceptance, deployment readiness, or real-capital status.

### Representative Replay Examples

Task761 includes `adapter_representative_replay_examples.csv` as a fixed, deterministic review sample from Task742 packets.

The replay examples cover:

- directional packets that may set `adapter_gate_state = pass` for relation review only
- structural mixed packets that may set `adapter_gate_state = cap`
- context-only packets that must remain context and cannot become directional edges
- explicit forbidden outputs showing no buy/sell/rank/sizing/backtest/real-capital fields are created
- `outcome_or_future_return_used = 0` for every replay row

This replay file is not a strategy test. It is a contract audit showing how Task742 interpretation states would be translated before Task762 repairs the current Task729 fixed primitive gate.

### Validation Performed

Planned validation command:

```text
python -m unittest tests.test_task728_five_layer_interaction_logic_contract tests.test_task729_five_layer_interaction_engine_application
```

Artifact manifest regeneration command:

```text
python scripts/task_artifact_manifest.py --task-dir docs/reports/task_761_task742_to_task729_adapter_contract
```

## No-Background Decision-Maker Report

1. 결론: Task761은 계약 문서만 정의했습니다.
2. Task742의 의미 패킷을 Task729 관계 엔진으로 넘기는 필드를 정했습니다.
3. 매수, 매도, 순위, 사이징, 백테스트 허용은 만들지 않았습니다.
4. 현재 남은 문제는 Task729 코드의 primitive gate가 아직 고정 0이라는 점입니다.
5. 그 수리는 Task762 이후 별도 구현 대상입니다.

## Artifact Manifest

- `task742_task729_adapter_contract.md`
- `adapter_field_map.csv`
- `adapter_representative_replay_examples.csv`
- `task_761_decision.csv`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
