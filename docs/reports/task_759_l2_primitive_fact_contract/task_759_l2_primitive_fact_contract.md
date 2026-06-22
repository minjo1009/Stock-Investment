# Task759 L2 Primitive Fact Contract Unification

## Decision Summary

- Verdict: `L2_PRIMITIVE_FACT_CONTRACT_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `primitive_fact`
- Owner team: Data & Market Microstructure
- Reviewer team: Research Governance + Backtest & Simulation Infra
- Key metrics: Task730 event packets 5302; Task730 injected rows 5265; Task740 primitive rows 3443; Task740 unresolved join blockers 4729.
- What changed: Replaced the placeholder Task759 report, added a PrimitiveFact contract, added a non-directional primitive fact catalog, refreshed the decision row, and regenerated the artifact manifest.
- Next action: Task760 should interpret primitive facts into review-only pragmatic economic meaning; Task762 should use explicit primitive gate inputs instead of hard-coded primitive gate failure.

Task759 is a research contract task only. It does not promote code, create a strategy claim, approve deployment, permit real capital, or create buy/sell/rank/sizing/backtest eligibility.

## Quant Expert Report

### Objective

Task759 unifies the Task730 and Task740 primitive outputs into one L2 contract:

```text
L1 evidence packet
-> L2 source-local PrimitiveFact
-> L3 pragmatic meaning review
-> L4 relation edge review
-> L5/backtest gate remains unavailable here
```

The contract keeps facts pragmatic and source-local. A fact may say "a named customer contract of USD 250 million over 5 years was extracted from this span." It may not say that the issuer is bullish, ranked, sized, or backtest eligible.

### Inputs Reviewed

- `docs/operating_system/project_operating_state.md`
- `docs/report_standard.md`
- `docs/ownership/subagent_packet_standard.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `docs/reports/task_757_brain_dependency_dag_supersession/task_757_brain_dependency_dag_supersession.md`
- `docs/reports/task_758_l1_evidence_contract/l1_evidence_contract.md`
- `docs/reports/task_758_l1_evidence_contract/task_758_l1_evidence_contract.md`
- `docs/reports/task_730_economic_reality_packet_builder/task_730_economic_reality_packet_builder.md`
- `docs/reports/task_740_engineering_high_resolver_completion/task_740_engineering_high_resolver_completion.md`
- `tests/test_task730_economic_reality_packet_builder.py`
- `tests/test_task740_engineering_high_resolver_completion.py`

The requested files `src/backtest/economic_reality_packet_builder.py` and `src/backtest/engineering_high_resolver_completion.py` do not exist at the requested paths in this checkout, so Task759 did not rely on them.

### Contract Summary

The canonical contract is `primitive_fact_contract.md`.

Required field groups:

- Identity: `primitive_fact_id`, `evidence_id`, `source_event_id`, `issuer_symbol`, optional `lifecycle_id`.
- Provenance: `source_form_family`, `source_circuit`, `source_url`, `accession_or_document_id`, `raw_text_path`, `source_hash`.
- As-of timing: `source_event_ts`, `filed_ts`, `observed_ts`, `as_of_ts`, `as_of_state`.
- Evidence reference: `extraction_span`, `extraction_span_start`, `extraction_span_end`, `evidence_reference_id`.
- Extraction quality: `extractor_name`, `extractor_version`, `extraction_method`, `extraction_confidence`, `confidence_reason`.
- Raw/source circuit: `source_trace_state`, `raw_source_available_flag`, `source_circuit_state`.
- Fact payload: `fact_family`, `fact_type`, `fact_value`, `fact_unit`, `fact_value_normalized`, `fact_period`, `counterparty_or_actor`.
- Uncertainty: `uncertainty_flags`, `missing_required_context`, `join_blocker_state`, `review_state`.
- Forbidden effects: `directional_signal_created_flag`, `rank_created_flag`, `sizing_created_flag`, `backtest_eligible_flag`, `outcome_used_for_assignment_flag`, `downstream_forbidden_effects`.

All forbidden effect flags must remain `0` at L2.

### Primitive Catalog

The catalog is `primitive_fact_catalog.csv`. It keeps only pragmatic fact families visible in the current Task730/740 evidence:

- contract/customer
- backlog/orderbook
- guidance raise/reaffirm/cut/soft
- margin/cost
- demand/supply
- financing terms/use-of-proceeds
- Form4 behavior
- ownership/control
- macro/policy context

Each family is non-directional. For example, `guidance_cut_mentioned` is a fact type, not a short signal; `open_market_purchase` is a fact type, not a buy instruction.

### Exact Join Keys

L2 may preserve existing join keys only:

- `evidence_id`
- `source_event_id`
- `issuer_symbol`
- `lifecycle_id` when already supplied by L1/upstream
- `source_form_family`
- `source_circuit`
- `as_of_ts`
- `accession_or_document_id`
- `raw_text_path`

Forbidden joins:

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback matching.
- No price rescue of weak source traces.
- No missing fact to negative conversion.
- No unavailable raw source approximation.

### Leakage Audit

Task759 introduces no outcome, return, price-after-event, score, rank, allocation, sizing, order, or broker-truth field.

Labels and outcomes remain evaluation-only and must not enter primitive assignment logic. Missing primitive facts remain `unknown`, `not_extracted`, `source_gap`, or an explicit uncertainty flag; they are never converted into bearish, negative, failed, or rejected facts.

### Split/OOS Metrics

Not applicable. Task759 is a research-only contract and artifact task. It does not run a strategy, split, OOS test, optimization, replay, or simulation.

### Cost/Slippage Stress

Not applicable. Task759 creates no PnL, order, fill, sizing, allocation, or backtest eligibility output.

### Task760 And Task762 Handoff

Task760 may consume `PrimitiveFact` rows to build pragmatic economic meaning packets with explicit ambiguity and confirmation needs. Task760 must not treat fact existence as a trade instruction.

Task762 may consume `review_state`, `source_trace_state`, `join_blocker_state`, `extraction_confidence`, and `downstream_forbidden_effects` to design an explicit primitive gate input. Gate states may be `pass`, `cap`, `context_only`, `not_ready`, or `source_gap`, but no gate state may create buy/sell/rank/sizing/backtest eligibility by itself.

### Remaining Blockers

- The Task759 contract is not implemented in code.
- Task729 still requires Task762 gate repair before primitive facts can be represented as explicit gate input.
- Task760 still must define the economic meaning layer between primitive facts and relation edges.
- Raw source availability and unresolved denominator joins remain explicit uncertainties, not approximations.

## No-Background Decision-Maker Report

1. Done: Task759 now defines the L2 primitive fact contract.
2. Done: Facts stay factual and non-directional.
3. Done: Missing facts are uncertainty, not negative labels.
4. Done: Task760 gets clean fact inputs for meaning review.
5. Done: Task762 gets gate input fields without direct trading permission.
6. No change: Strategy remains `NOT_ACCEPTED`.
7. No change: Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
8. No change: Real capital remains `FORBIDDEN`.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_759_l2_primitive_fact_contract.md` | report | Task759 decision and expert report. |
| `primitive_fact_contract.md` | contract | L2 PrimitiveFact object and forbidden downstream effects. |
| `primitive_fact_catalog.csv` | catalog | Non-directional primitive fact families from current Task730/740 evidence. |
| `task_759_decision.csv` | decision | Machine-readable Task759 decision row. |
| `artifact_manifest.csv` | manifest | File sizes and SHA-256 hashes for Task759 artifacts. |

Row counts:

- `primitive_fact_catalog.csv`: 9 data rows.
- `task_759_decision.csv`: 1 data row.
- `artifact_manifest.csv`: regenerated after artifact updates.

Validation commands:

```text
python -m unittest tests.test_task730_economic_reality_packet_builder tests.test_task740_engineering_high_resolver_completion
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
