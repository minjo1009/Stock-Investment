# Task823 Candidate Bundle Adapter Contract

## Decision Summary

- Verdict: `CANDIDATE_BUNDLE_ADAPTER_CONTRACT_IMPLEMENTED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 4 research-only candidate bundles; 1 schema; 1 validator script.
- What changed: Relationship graph fixtures now map to candidate thesis bundles without producing trade candidates.
- Next action: Use contradiction and source_gap propagation before any controlled adapter task.

## Quant Expert Report

Candidate bundles contain explicit graph ids, asof timestamps, supporting node ids, supporting edge ids, contradiction nodes, invalidation edges, weakest layer, unresolved gaps, and research-only bundle states.

The validator blocks forbidden markers and requires contradiction/source_gap bundles to remain blocked or context-limited. No buy/sell, rank, score, sizing, backtest eligibility, runtime, broker integration, or real-capital permission is created.

## No-Background Decision-Maker Report

1. Done: 관계망을 candidate thesis bundle로 묶었다.
2. Done: 4개 bundle 모두 research-only다.
3. Important: trade candidate가 아니다.
4. Next: contradiction/source_gap 전파 규칙으로 제한한다.

## Artifact Manifest

- Inputs: Task813 and Task821 graph fixtures.
- Outputs: `candidate_bundle_schema.csv`, `candidate_bundles.csv`, and `scripts/trader_brain_candidate_bundle_validate.py`.
- Validation commands: `python scripts/trader_brain_candidate_bundle_validate.py --bundles docs/reports/task_823_candidate_bundle_adapter_contract/candidate_bundles.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
