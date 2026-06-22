# Task830 Adapter Input Schema Contract

## Decision Summary

- Verdict: `ADAPTER_INPUT_SCHEMA_IMPLEMENTED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 11 adapter input fields; forbidden content defined per field.
- What changed: Defined the only fields allowed in dry adapter input.
- Next action: Builder must output only this schema.

## Quant Expert Report

The schema carries candidate id, graph id, bundle asof timestamp, mechanism ids, evidence refs, eligible reason, and validation authority. It excludes direction, ranking, scoring, sizing, PnL, order ids, and runtime state.

No backtest execution or backtest eligibility assignment is created.

## No-Background Decision-Maker Report

1. Done: adapter input schema를 만들었다.
2. Allowed: id, asof, mechanism, evidence, reason.
3. Forbidden: 매매 방향, score, sizing, PnL.
4. Next: builder가 이 schema만 출력한다.

## Artifact Manifest

- Outputs: `adapter_input_schema.csv`.
- Validation commands: `python scripts/trader_brain_828_839_program_validate.py`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
