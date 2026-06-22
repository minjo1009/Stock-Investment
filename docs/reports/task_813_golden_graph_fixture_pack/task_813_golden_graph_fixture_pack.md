# Task813 Golden Graph Fixture Pack

## Decision Summary

- Verdict: `GOLDEN_GRAPH_FIXTURE_PACK_DESIGNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 2 positive graph fixtures implemented; 7 graph CSV files added; validator inputs limited to nodes, edges, transitions, and optional update chains.
- What changed: Task813 now contains AI capex mechanism and macro policy source-gap graph fixtures.
- Next action: Keep fixture expansion small and add only mechanisms that preserve exact ids, edge evidence ids, asof timestamps, mechanism ids, and source_gap states.

## Quant Expert Report

The golden pack is intentionally small. It includes one AI infrastructure mechanism, one macro policy source-gap mechanism, and one contradiction path. Each packet passes the existing relationship graph packet validator without producing buy/sell, rank, score, sizing, PnL, backtest eligibility, or deployment claims.

Exact join keys are explicit ids only: `node_id`, `source_node_id`, `target_node_id`, `edge_evidence_id`, `mechanism_id`, and optional predecessor ids. No symbol/date/price/time proximity fallback matching is allowed.

## No-Background Decision-Maker Report

1. Done: 작은 정상 graph 샘플 2개를 만들었다.
2. Why: 정상 샘플이 있어야 다음 batch, failure report, CI를 믿을 수 있다.
3. Not done: 매매 판단은 만들지 않는다.
4. Next: Task814 batch runner 설계로 이어진다.

## Artifact Manifest

- Inputs: Task807 relationship graph validator.
- Outputs: `fixtures/ai_capex_mechanism_graph/` and `fixtures/macro_policy_source_gap_graph/`.
- Validation commands: `python scripts/trader_brain_relationship_graph_packet_validate.py --graph-dir docs/reports/task_813_golden_graph_fixture_pack/fixtures/ai_capex_mechanism_graph`; `python scripts/trader_brain_relationship_graph_packet_validate.py --graph-dir docs/reports/task_813_golden_graph_fixture_pack/fixtures/macro_policy_source_gap_graph`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
