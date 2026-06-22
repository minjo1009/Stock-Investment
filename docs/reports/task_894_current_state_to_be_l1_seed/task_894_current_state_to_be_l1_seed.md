# Task894 Current State TO-BE L1 Seed

## Decision Summary

- Verdict: implemented.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- AS-IS: Task893 recovered 139 internal source-time seed rows, but the project did not yet have 70-symbol coverage, decision-as-of coverage, or L1 brain seed state.
- TO-BE: every 10x7 symbol has an explicit source-time coverage state, every decision-symbol pair has as-of evidence counts, and recovered rows are represented as L1-only brain state.
- What changed:
  - 70-symbol source-time coverage matrix implemented.
  - 4,410-row decision-symbol as-of coverage panel implemented.
  - 139-row L1 source-evidence seed state implemented.
  - 70-row acquisition queue implemented.
- Current coverage: 8 of 70 universe symbols have L1 seed rows.
- Missing coverage: 62 of 70 universe symbols still need source-time seed acquisition.
- Brain layer status: `L1_SOURCE_EVIDENCE_SEED_ONLY`.

## Quant Expert Report

Inputs:

- Universe: `data/raw/theme_universe_10x7.csv`.
- Recovered source-time seed panel: `data/artifacts/task_893_source_time_recovery/recovered_source_time_panel.csv`.
- Historical decision calendar: `data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv`.

Exact join keys:

- Symbol coverage: `symbol`.
- Decision coverage: `symbol`, `decision_asof_ts`, and `available_to_brain_ts <= decision_asof_ts`.
- L1 seed state: `evidence_id`, `symbol`, `available_to_brain_ts`, `first_eligible_decision_id`.

Leakage audit:

- Decision coverage only counts seed rows whose `available_to_brain_ts` is not later than `decision_asof_ts`.
- L1 state does not create primitive facts, economic meanings, relation edges, candidate bundles, scores, ranks, sides, entries, exits, or position sizes.
- Missing evidence remains `source_seed_missing`; it is not converted into a negative label.

Failure decomposition:

- 62 symbols have no L1 source seed.
- All recovered seed rows still carry `raw_external_document_missing`.
- L2 and L3 remain intentionally blocked until raw source attachment and primitive fact construction are implemented.

## No-Background Decision-Maker Report

The project now has a clean map of what is ready and what is missing. There are 70 target symbols. Eight have some L1 evidence seed. Sixty-two do not. The recovered 139 rows are now usable as L1 source-evidence seeds, but not as trading signals.

This improves the system because the next GPT/engineering task no longer has to guess where the data gap is. It has a concrete queue.

## Artifact Manifest

- Script: `scripts/trader_brain_894_current_state_to_be_l1_seed.py`.
- Validator: `scripts/trader_brain_894_current_state_to_be_l1_seed_validate.py`.
- Test: `tests/test_trader_brain_894_current_state_to_be_l1_seed.py`.
- Diagnosis: `data/artifacts/task_894_current_state_to_be_l1_seed/current_state_to_be_diagnosis.csv`.
- Symbol coverage: `data/artifacts/task_894_current_state_to_be_l1_seed/source_time_symbol_coverage_matrix.csv`.
- Decision coverage: `data/artifacts/task_894_current_state_to_be_l1_seed/source_time_decision_coverage_panel.csv`.
- L1 seed state: `data/artifacts/task_894_current_state_to_be_l1_seed/l1_source_evidence_seed_state.csv`.
- Acquisition queue: `data/artifacts/task_894_current_state_to_be_l1_seed/missing_source_acquisition_queue.csv`.
- Summary: `data/artifacts/task_894_current_state_to_be_l1_seed/task_894_current_state_to_be_l1_seed_summary.json`.
- Validation command: `python scripts/trader_brain_894_current_state_to_be_l1_seed_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
