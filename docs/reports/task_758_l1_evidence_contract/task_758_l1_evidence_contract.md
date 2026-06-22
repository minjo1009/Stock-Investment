# Task758 L1 Evidence Contract And Context Retention

## Decision Summary

- Verdict: `L1_EVIDENCE_CONTRACT_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `source_evidence`
- Owner team: Data & Market Microstructure
- Reviewer team: Research Governance
- What changed: Task758 defines the minimum L1 evidence fields and source-family retention policy for the Task756 Trader Brain program.
- Next action: Task759 should map retained L1 packets into source-local primitive facts without turning missing fields into negative labels.

Task758 is a contract/report task only. It does not edit router code, interpreters, tests, registry rows, or trading logic.

## Quant Expert Report

### Objective

Task758 converts the Task731 source router principle into an explicit L1 evidence contract:

```text
Keep every source as evidence or context.
Do not allow source text to jump to buy/sell/rank/sizing/backtest eligibility.
Use good-enough source fields, directness, novelty, contamination, and uncertainty.
Do not demand every possible denominator before retaining context.
```

### Inputs Reviewed

- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/architecture/brain_layer_map.md`
- `docs/reports/task_731_source_information_router/task_731_source_information_router.md`
- `docs/reports/task_735_generic_8k_classifier_repair/task_735_generic_8k_classifier_repair.md`
- `docs/reports/task_722_source_attached_review_packets/task_722_source_attached_review_packets.md`
- `src/backtest/source_information_router.py`
- `src/backtest/source_circuit_interpreters.py`
- `tests/test_task731_source_information_router.py`

### Contract Summary

The new L1 contract is stored in `l1_evidence_contract.md`.

Required good-enough fields:

- Stable identity: `evidence_id`, `source_event_id`, `issuer_symbol`, `lifecycle_id`
- Time and as-of trace: `source_event_ts`, `filed_ts`, `observed_ts`, `as_of_state`
- Source family and route: `source_form_family`, `route_circuit`, `source_route_state`
- Evidence trace: `source_url`, `accession_or_document_id`, `raw_text_path`, `evidence_span`, `evidence_span_status`
- Interpretation guards: `source_directness_state`, `novelty_state`, `contamination_state`, `uncertainty_state`
- Permission guards: `allowed_fact_families`, `forbidden_fact_families`, `downstream_edge_required_flag`
- Retention and no-trade flags: `context_retention_state`, `source_is_discarded_flag`, `backtest_eligible_flag`, `outcome_used_for_assignment_flag`

The source-family policy is stored in `l1_source_family_policy.csv`.

### Family Policy

Task758 keeps the Task731 rule that non-operating sources are routed, not blocked:

- `financing_8k` stays in credit/financing context.
- `form4_insider` stays in insider behavior context.
- `schedule_13d_13g` stays in activist/control context.
- `form_13f` stays in institutional positioning context.
- `ownership_or_institutional_filing` stays in ownership structure context.
- `macro_policy_or_geopolitical_source` stays in macro/policy transmission context.
- `generic_8k` stays alive but needs item/family classification before operating use.

No source family is blanket-blocked. Unsafe operating extraction is denied separately from evidence retention.

### Good-Enough Stop Rule

Task758 explicitly rejects excessive denominator requirements at L1.

Example:

```text
Insider non-plan selling may be negative enough as context when transaction type, role, timing, and plan status are visible.
L1 should not require full holdings denominators unless the filing already provides them.
Missing holdings denominator is uncertainty, not a negative label and not a discard reason.
```

The same principle applies to financing terms, ownership filings, macro links, and generic 8-K items: missing comparator data creates `uncertainty_state` or `review_needed`, not a directional label.

### Leakage And Permission Audit

- No outcome, future return, price rescue, rank, sizing, or allocation field is introduced.
- No L1 source text may create a buy/sell/rank/sizing/backtest output.
- Missing data cannot become a negative label.
- Context-only sources must be retained with explicit uncertainty and a required downstream interaction edge.
- L1 output remains research-only and cannot modify strategy acceptance, deployment readiness, or real-capital permission.

### Validation

Validation authority: Research-only source routing validation.

Commands run:

```text
python -m unittest tests.test_task731_source_information_router
```

Expected meaning of pass: Task731 routing still preserves sources, blocks operating promotion, creates cross-circuit edges, and keeps backtest eligibility at zero.

Pass does not mean:

- Strategy accepted.
- Deployment ready.
- Source coverage complete.
- L1 contract implemented in production code.

## No-Background Decision-Maker Report

1. 결론: L1 증거 계약을 만들었습니다.
2. 모든 source family는 버리지 않습니다.
3. 대신 직접 증거, 맥락 증거, 불확실성을 나눕니다.
4. Form 4 매도는 holdings denominator가 없어도 맥락상 부정적일 수 있습니다.
5. 다만 그것만으로 매도, 랭킹, 사이징, 백테스트 진입은 금지입니다.
6. Generic 8-K는 agreement 문구만으로 영업 증거가 아닙니다.
7. Financing, ownership, macro는 operating catalyst가 아니라 compound interaction 입력입니다.
8. 이 작업은 자본 투입 가능 상태를 바꾸지 않습니다.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_758_l1_evidence_contract.md` | report | Task758 decision report. |
| `l1_evidence_contract.md` | contract | Good-enough L1 source evidence field contract. |
| `l1_source_family_policy.csv` | policy | Source-family routing and context-retention policy. |
| `task_758_decision.csv` | decision | Machine-readable Task758 decision row. |
| `artifact_manifest.csv` | manifest | File sizes and hashes for Task758 artifacts. |

Row counts:

- `l1_source_family_policy.csv`: 8 data rows.
- `task_758_decision.csv`: 1 data row.
- `artifact_manifest.csv`: regenerated after artifact updates.

Validation command:

```text
python -m unittest tests.test_task731_source_information_router
```

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
