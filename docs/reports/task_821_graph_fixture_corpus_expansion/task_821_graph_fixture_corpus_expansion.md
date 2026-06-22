# Task821 Graph Fixture Corpus Expansion

## Decision Summary

- Verdict: `GRAPH_FIXTURE_CORPUS_EXPANDED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 2 additional graph fixtures; 4 new attention rows; provenance manifest extended.
- What changed: Added semiconductor export-control and space-defense policy graph fixtures.
- Next action: Use these fixtures for candidate bundle adapter validation.

## Quant Expert Report

The added fixtures expand relationship coverage without increasing data hunger. Each fixture has L1 source evidence, L2 salience, L3 mechanism, and either contradiction or source_gap preservation.

Exact ids are used for graph references. No inferred matching, labels, PnL, rank, score, buy/sell, sizing, backtest eligibility, runtime, broker integration, or real-capital permission is introduced.

## No-Background Decision-Maker Report

1. Done: graph fixture 2개를 추가했다.
2. Done: 반도체/export-control과 우주방산/policy 관계를 넣었다.
3. Important: 둘 다 매매 판단이 아니라 관계망 샘플이다.
4. Next: candidate bundle adapter에 연결한다.

## Artifact Manifest

- Inputs: Task813 fixtures and Task816 provenance manifest.
- Outputs: `fixtures/semiconductor_export_control_graph/`, `fixtures/space_defense_policy_graph/`, and `fixture_manifest.csv`.
- Validation commands: `python scripts/trader_brain_820_827_program_validate.py`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
