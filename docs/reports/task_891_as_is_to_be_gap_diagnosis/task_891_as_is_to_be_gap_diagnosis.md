# Task891 AS-IS / TO-BE Gap Diagnosis

## Decision Summary

- Verdict: implemented.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Purpose: diagnose the exact gap between current project state and the TO-BE historical Trader Brain backtest.
- Key finding: repo has many source/evidence-like artifacts, but zero raw historical evidence files are directly compliant with the Task883 source-time standard.
- First real historical brain replay: `no_go`.
- Next action: build the Task883 source-time bridge from eligible repo-native artifacts and explicitly reject non-compliant artifacts.

## Quant Expert Report

AS-IS:

- Market data is not the active blocker.
- Task880 has 70-symbol universe data plus QQQ benchmark.
- Task881-890 prep has 63 monthly decision dates, 4,410 universe membership rows, and 630 blocked brain-state previews.
- Leakage negative fixtures exist and reject 5/5 bad cases.
- Repo source/evidence inventory found 937 candidate CSV files.
- Direct source-time bridge-ready files: 0.
- Derived event context candidates: 2.

TO-BE:

- Every evidence row used by the brain must have:
  - `evidence_id`
  - `source_family`
  - `published_ts`
  - `received_ts`
  - `available_to_brain_ts`
  - `source_hash`
  - `source_gap_flag`
- Every `available_to_brain_ts` must be less than or equal to `decision_asof_ts`.
- Missing historical evidence must remain `source_gap`, `not_ready`, or blocked.
- Existing derived event artifacts can support diagnostics only after normalization and lineage review.
- No candidate bundle, decision, or trade spec can be opened from price-only or outcome-derived artifacts.

Gap matrix:

- Universe: partial. It is fixed research universe, not PIT universe.
- Market data: ready for diagnostic replay data gate.
- Historical source-time panel: not ready.
- Brain state: blocked.
- Relationship graph: blocked.
- Candidate/decision/trade spec: blocked.
- Leakage guard: initial guard implemented.

## No-Background Decision-Maker Report

The project is not missing price data now. It is missing proof of what the brain knew at each historical point. There are many old evidence-like files, but they are not yet normalized into a safe source-time panel. The next work is to bridge or reject those files, not to run another backtest.

## Artifact Manifest

- Script: `scripts/trader_brain_891_as_is_to_be_gap_diagnosis.py`.
- Validator: `scripts/trader_brain_891_as_is_to_be_gap_diagnosis_validate.py`.
- Inventory: `data/artifacts/task_891_as_is_to_be_gap_diagnosis/repo_source_evidence_inventory.csv`.
- Gap matrix: `data/artifacts/task_891_as_is_to_be_gap_diagnosis/as_is_to_be_gap_matrix.csv`.
- TO-BE backlog: `data/artifacts/task_891_as_is_to_be_gap_diagnosis/to_be_requirement_backlog.csv`.
- Summary: `data/artifacts/task_891_as_is_to_be_gap_diagnosis/task_891_gap_diagnosis_summary.json`.
- Validation command: `python scripts/trader_brain_891_as_is_to_be_gap_diagnosis_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
