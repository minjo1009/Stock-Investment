# Task847 Failure Decomposition Schema

## Decision Summary

- Verdict: `FAILURE_DECOMPOSITION_SCHEMA_IMPLEMENTED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 9 failure classes.
- What changed: Defined how future harness failures should be decomposed.
- Next action: Use failure classes in future controlled replay reports.

## Quant Expert Report

Failure classes cover input manifests, timestamp gates, market data blocks, replay config errors, cost/slippage plan gaps, source gaps, contradictions, artifact audit failures, and forbidden execution attempts.

This schema is diagnostic only and does not imply a strategy is good or bad.

## No-Background Decision-Maker Report

1. Done: failure decomposition schema를 만들었다.
2. Classes: 9개.
3. Important: 실패 이유를 숨기지 않게 한다.
4. Not done: 성과 분석은 아직 없다.

## Artifact Manifest

- Outputs: `failure_decomposition_schema.csv`.
- Validation commands: `python scripts/trader_brain_840_849_program_validate.py`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
