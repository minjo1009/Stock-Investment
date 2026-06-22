# Task825 Attention Memory Eviction Rules

## Decision Summary

- Verdict: `ATTENTION_MEMORY_EVICTION_RULES_IMPLEMENTED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 5 retention policies; 6 fixture rows; noise evicted while source_gap is retained.
- What changed: Added bounded working-memory rules to prevent input over-collection.
- Next action: Apply these rules before expanding attention packets.

## Quant Expert Report

The policy keeps enough evidence, defer states, source gaps, and contradiction pressure, while archiving noise. Source gaps cannot be hidden as noise.

This is a memory policy only. It does not produce buy/sell, rank, score, sizing, PnL, backtest eligibility, runtime, broker integration, or real-capital permission.

## No-Background Decision-Maker Report

1. Done: 뇌 working memory 제한 규칙을 만들었다.
2. Done: noise는 archive로 보내고 source_gap은 남긴다.
3. Important: 정보를 무한히 먹지 않게 한다.
4. Next: backtest adapter readiness를 점검한다.

## Artifact Manifest

- Inputs: Task815 attention corpus.
- Outputs: `memory_eviction_policy.csv` and `memory_eviction_fixture.csv`.
- Validation commands: `python scripts/trader_brain_820_827_program_validate.py`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
