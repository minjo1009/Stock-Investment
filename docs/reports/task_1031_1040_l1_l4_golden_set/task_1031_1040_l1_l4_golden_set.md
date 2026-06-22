# Task1031-1040 L1-L4 Golden Source-To-Thesis Set

## Decision Summary

- Verdict: `l1_l4_golden_source_to_thesis_set_complete_no_replay`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 20 golden cases, 10 buckets x 2 cases, 20 L1 rows, 20 L2 rows, 20 L3 rows, 20 L4 rows, 6 negative failure fixtures.
- What changed: Task1031-1040 converted the Task1021-1030 L1-L4 contracts into hand-reviewable source-to-thesis golden rows.
- Next action: implement deterministic extractors against these golden cases before any replay, selection, or adapter promotion.

## Quant Expert Report

### Data source and source readiness

- Input source catalog: `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1021_institutional_source_catalog.csv`.
- Golden L1 source rows: 20.
- Source readiness in selected golden cases: 19 downloaded, 1 official-source URL present but local download failed with HTTP 403.
- The failed local download is treated as a reported source gap, not approximated evidence.

### Exact join keys

- `case_id` links every L1, L2, L3, L4, validation, and cross-read row.
- `source_name` links golden cases to the Task1021 institutional source catalog.
- `l1_id`, `l2_id`, `l3_id`, and `l4_id` enforce row-level source-to-thesis lineage.

### Leakage audit

- `selection_use_allowed=0` across L1 and golden rows.
- `replay_use_allowed=0` across L1, golden, and validation rows.
- L4 `outcome_used_for_assignment_flag=0`.
- L4 `trade_instruction_allowed=0`.
- L2 forbidden fields include `future_return`, `pnl`, `realized_return`, `outcome_rank`, and `post_entry_price_change`.
- No replay, price lookup, PnL calculation, ranking promotion, buy/sell decision, or sizing was executed.

### Split/OOS metrics

- Not applicable. This task is a research-only golden-set contract.
- Test success does not imply strategy acceptance.

### Failure decomposition

- This task intentionally includes 6 negative failure fixtures:
  - `future_return_in_l2_primitive`
  - `missing_source_lineage`
  - `replay_use_allowed_equals_1`
  - `missing_l3_mechanism`
  - `trade_instruction_present`
  - `missing_valid_time_for_stale_thesis`

### Cost/slippage stress

- Not applicable. No strategy replay or execution simulation was run.

### Remaining blockers

- Extractors are not yet implemented against the golden cases.
- Golden cases require expert human review before they become extractor acceptance fixtures.
- One selected source still has a local download gap and must stay marked as a gap until repaired.

## No-Background Decision-Maker Report

What happened:

Task1031-1040 built the answer-key layer for L1-L4. It now shows how official sources should become economic primitives, relation mechanisms, and thesis cards without jumping straight into trades.

Why it matters:

The prior replay failures were not only an L5 problem. The front of the brain needed better source-to-meaning contracts. This task gives the next extractor work a concrete target.

Whether this changes capital/deployment readiness:

No. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Build extractors that reproduce these 20 source-to-thesis chains, then validate failed cases stay blocked.

## Artifact Manifest

### Inputs

- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1021_institutional_source_catalog.csv`

### Outputs

- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1031_l1_golden_source_contract_rows.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1032_l2_golden_primitive_rows.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1033_l3_golden_mechanism_rows.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1034_l4_golden_thesis_card_rows.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1035_source_to_thesis_golden_set.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1036_cross_read_chain_golden_rows.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1037_l1_l4_golden_validation_results.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1037_negative_golden_failure_cases.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1038_gpt_expert_feedback_synthesis.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1039_no_replay_gate.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/task1040_golden_set_closeout.csv`
- `data/artifacts/task_1031_1040_l1_l4_golden_set/artifact_manifest.csv`

### Row Counts

- Golden cases: 20.
- Buckets: 10.
- Cases per bucket: 2.
- Negative failure fixtures: 6.

### Validation Commands

```text
python scripts/trader_brain_1031_1040_l1_l4_golden_set.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1031_1040_l1_l4_golden_set
python scripts/trader_brain_1031_1040_l1_l4_golden_set_validate.py
python -m unittest tests.test_trader_brain_1031_1040_l1_l4_golden_set
python scripts/trader_brain_1021_1030_l1_l4_institutional_upgrade_validate.py
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `RESEARCH_ONLY`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
