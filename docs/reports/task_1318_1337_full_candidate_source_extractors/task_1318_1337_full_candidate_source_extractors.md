# Task1318-1337 Full Candidate Source Extractors

## Decision Summary

- Verdict: `full_candidate_source_extractors_attached_no_replay`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Candidate rows: 3100.
- Filing bindings: 14166.
- Unique accessions: 4934.
- Downloaded/cached complete submissions: 4934.
- L2 candidate rows: 3100.
- L3 evidence edges: 18600.
- What changed: the extractor expanded from selected slot5 rows to the full 3,100 candidate pool.
- Next action: preregister candidate replacement replay using this full-candidate source panel.

## Quant Expert Report

- Data source and source readiness: SEC bulk submissions metadata and SEC Archives complete submission text files were used for full-candidate source binding.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `symbol`, `cik`, `decision_asof_ts`, `accession`, `evidence_id`.
- Leakage audit: every filing binding requires `available_to_brain_ts <= decision_asof_ts`; L1-L3 assignment does not use future return, PnL, realized exit, or outcome labels.
- Split/OOS metrics: not applicable; no replay was executed.
- Failure decomposition: analyst PIT, symbol-level policy/news affected-entity extraction, and full as-of market acceptance factors remain explicit gaps.
- Cost/slippage stress: not applicable because no PnL changed.

## No-Background Decision-Maker Report

The previous weakness was real: only the already-selected 310 rows had source extraction.

This task attaches source extraction to all 3,100 candidates.

Now the next replay can actually drop weak selected names and replace them with stronger candidates from the same decision month.

This still does not approve the strategy.

## Artifact Manifest

- `task1318_full_candidate_source_schema.csv`
- `task1319_full_candidate_source_plan.csv`
- `task1320_candidate_filing_bindings.csv`
- `task1321_sec_complete_submission_download_ledger.csv`
- `task1322_sec_exhibit_document_index.csv`
- `task1323_accession_source_evidence.csv`
- `task1324_candidate_l1_source_bindings.csv`
- `task1325_candidate_l2_interpretation.csv`
- `task1326_candidate_l3_evidence_edges.csv`
- `task1327_full_candidate_readiness_panel.csv`
- `task1328_remaining_source_gap_ledger.csv`
- `task1329_candidate_replacement_readiness_gate.csv`
- `task1330_task_plan.csv`
- `task1337_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1318_1337_full_candidate_source_extractors_validate.py`
- `python -m unittest tests.test_trader_brain_1318_1337_full_candidate_source_extractors`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
