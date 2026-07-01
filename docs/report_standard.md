# Task Report Standard

Every new task report must use this shape.

## Decision Summary

- Verdict
- Strategy acceptance status
- Key metrics
- What changed
- Next action

## Quant Expert Report

- Data source and source readiness
- Exact join keys
- Leakage audit
- Split/OOS metrics
- Failure decomposition
- Cost/slippage stress where PnL changed
- Remaining blockers

## No-Background Decision-Maker Report

- What happened
- Why it matters
- Whether this changes capital/deployment readiness
- Plain-language next step

## Artifact Manifest

- Inputs
- Outputs
- Row counts
- File sizes
- Validation commands
- Source hashes when applicable

## Required Phrases

Use exact status language:

- `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- `PRIMARY_PASS`
- `SECONDARY_PASS`
- `NOT_ACCEPTED`
- `SUPERSEDED`
