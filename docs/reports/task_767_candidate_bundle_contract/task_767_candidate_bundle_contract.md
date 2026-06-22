# Task767 Candidate Thesis Bundle Contract

## Decision Summary

- Verdict: `RESEARCH_CONTRACT_COMPLETE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `candidate_bundle`
- Key metrics: 1 bundle contract, 1 required-field catalog, 1 decision file, and 1 refreshed artifact manifest.
- What changed: replaced the placeholder report and defined the L4 candidate thesis bundle as an explanatory object.
- Next action: Task768 may define same-timestamp slot comparison inputs, but Task767 does not create slot priority.

Task767 completes the bounded Research Governance worker packet for the L4 candidate bundle layer. The bundle gathers a thesis statement, evidence trail, primitive facts, meaning objects, relation edges, modifiers, compound state when supplied, confirmations needed, contradictions, invalidation conditions, weakest layer, and unresolved gaps. It is not a trade candidate, not a slot priority, not a hidden rank, and not backtest eligibility.

## Quant Expert Report

### Data source and source readiness

Inputs are contract artifacts and tests listed in the worker packet:

- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- Task759 L2 primitive contract.
- Task760 L3 pragmatic meaning contract.
- Task762 primitive gate repair design.
- Task763 typed relation edge schema.
- Task764 source circuit good-enough policy.
- Task765 modifier contracts.
- Task766 placeholder report, if available.
- Historical guardrail tests for Task737 semantic modifier bundle attachment and Task738 semantic enrichment requirements.

Task766 has no separate `compound_interaction_engine_contract.md` artifact in this checkout, so Task767 treats `compound_state` as required when supplied by an upstream compound contract and otherwise records the absence as an unresolved gap. Missing compound context is not a rejection, negative label, rank penalty, or slot decision.

### Exact join keys

Allowed identity and trace keys:

- `bundle_id`: stable L4 bundle id.
- `lifecycle_id`: allowed only when supplied by upstream artifacts.
- `symbol`: source-attached issuer symbol for display and audit, not a fallback matching key.
- `asof_ts`: as-of timestamp for the bundle view.
- `evidence_trace`: structured trace to L1 evidence ids, source event ids, raw paths, and source trace states.
- `primitive_facts`: explicit L2 ids and fact states.
- `meaning_objects`: explicit L3 ids and meaning states.
- `relation_edges`: explicit Task763-style edge ids.
- `modifiers`: explicit Task765-style modifier ids.
- `compound_state`: explicit upstream compound state if available.

Forbidden joins:

- inferred lifecycle matching;
- symbol/date/price/time proximity fallback matching;
- price reaction, future return, PnL, win/loss, label, rank, or outcome-assisted matching.

### Leakage audit

The bundle contract forbids future returns, outcomes, PnL, win/loss labels, hidden scores, hidden ranks, and backtest eligibility fields. `evidence_trace`, `primitive_facts`, `meaning_objects`, `relation_edges`, `modifiers`, and `compound_state` must be as-of safe. Missing context is recorded in `unresolved_gaps`, `weakest_layer`, `confirmation_needed`, or `contradictions`; it is never converted into a negative label.

### Split/OOS metrics

Not applicable. This is a research-only contract task. No split, out-of-sample, strategy metric, trade performance, or acceptance claim was produced.

### Failure decomposition

The bundle must expose failure and uncertainty without producing decisions:

- weak L1 source trace -> `weakest_layer=L1_source_evidence` and `unresolved_gaps`.
- weak L2 primitive extraction -> `weakest_layer=L2_primitive_fact` and confirmation request.
- L3 ambiguity or hard blockers -> contradiction or confirmation-needed state.
- Relation edge conflict -> contradiction and invalidation path.
- Modifier disagreement -> confidence cap or confirmation-needed state.
- Missing Task766 compound context -> unresolved gap, not rejection.

### Cost/slippage stress where PnL changed

Not applicable. No PnL, execution, fill, cost, slippage, sizing, allocation, or backtest eligibility output was created.

### Remaining blockers

- Task766 needs a non-placeholder compound interaction contract before `compound_state` can become a fully specified upstream input.
- Task768 must separately define slot comparison inputs. Task767 does not create slot priority.
- Later validation should check that bundle builders preserve the forbidden-output flags and do not use inferred matching.

## No-Background Decision-Maker Report

1. Task767 made the candidate bundle contract complete.
2. The bundle explains a thesis and its evidence trail.
3. It also shows confirmations, contradictions, invalidations, weakest layer, and gaps.
4. It is not a buy/sell candidate.
5. It is not a slot priority.
6. It does not allow sizing, ranking, or backtests.
7. Capital and deployment status do not change.

## Artifact Manifest

Inputs:

- `docs/ownership/subagent_packet_standard.md`
- `docs/report_standard.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- Task759, Task760, Task762, Task763, Task764, Task765, and available Task766 report artifacts.
- `tests/test_task737_semantic_modifier_bundle_attachment.py`
- `tests/test_task738_semantic_enrichment_requirements.py`

Outputs:

- `task_767_candidate_bundle_contract.md`
- `candidate_thesis_bundle_contract.md`
- `bundle_required_fields.csv`
- `task_767_decision.csv`
- `artifact_manifest.csv`

Row counts:

- `bundle_required_fields.csv`: 19 data rows.
- `task_767_decision.csv`: 1 data row.
- `artifact_manifest.csv`: refreshed after file writes.

Validation commands:

- `python -m unittest tests.test_task737_semantic_modifier_bundle_attachment tests.test_task738_semantic_enrichment_requirements`
- `python scripts/trader_brain_program_validate.py`

Validation authority:

- Diagnostic/research contract validation only.
- Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Source hashes:

- See `artifact_manifest.csv`.

Inferred matching used:

- No.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
