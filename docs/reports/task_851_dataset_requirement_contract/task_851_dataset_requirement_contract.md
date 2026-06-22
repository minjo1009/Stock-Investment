# Task851 Dataset Requirement Contract

## Decision Summary

- Verdict: completed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Data readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: required dataset families, target periods, point-in-time universe requirement, canonical manifest columns, and forbidden shortcuts are frozen.
- Next action: Task852 inventory audit output is the source for reuse/block/redownload decisions.

## Quant Expert Report

Task851 owns the requirement contract, not data download. It preserves daily, 15m, calendar, corporate action, symbol master, point-in-time universe, benchmark context, and microstructure scope boundaries from Task850.

Required periods:

- Daily replay target: `2021-01-01` through latest certified completed US session.
- First 15m replay target: `2024-01-02` through latest certified completed US session.
- Calendar target: `2021-01-01` through latest certified completed US session plus 30 calendar days.
- Microstructure target: event-window only, not a first controlled replay common input.

## No-Background Decision-Maker Report

This task decides what data must exist. It does not decide that current data is good.

## Artifact Manifest

- Outputs: Task850 requirement CSV, period/universe CSV, manifest schema, canonical bar schema, and decision CSV.
- Large artifacts: `data/artifacts/task_850_859_data_certification/`.
- Validation command: `python scripts/trader_brain_850_859_data_program_validate.py`.
Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
