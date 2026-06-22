# Task792 Information Relationship Graph Program

## Decision Summary

- Verdict: `INFORMATION_RELATIONSHIP_GRAPH_PROGRAM_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 10 graph tasks; 14 node identity fields; 9 edge types with required evidence; 10 layer transitions; 18 critical review roles; 0 trading outputs.
- What changed: Added a relationship-graph program that links existing Task773-791 artifacts instead of collecting more inputs.
- Next action: Task793 should define node identity in detail before any validator implementation.

Task792 preserves Task773-791. It modifies the next-work order: relationship graph contracts should come before controlled Task773 validator implementation.

## Quant Expert Report

### Data Source And Source Readiness

Inputs were current operating state, Task773 attention budget, Task779 journal trace schema, Task791 handoff, and governance standards. No market data, broker data, labels, returns, PnL, orders, fills, or future outcomes were used.

### Exact Join Keys

The graph may link only through explicit ids:

- `info_node_id`
- `attention_packet_id`
- `source_event_id`
- `evidence_id`
- `journal_trace_id`
- exact `asof_ts`

Symbol/date/price/time proximity fallback matching remains forbidden.

### Leakage Audit

The graph is explanatory. It can show that information reinforces, weakens, invalidates, conditions, sequences, explains, contradicts, or creates a source gap. It cannot emit buy/sell/rank/score/sizing/backtest eligibility.

### Critical GPT/Expert Panel Upgrade

Task792 now includes a bounded GPT/Chrome review packet and an expert critical review matrix. The roles are not sources and not decision makers. They are lenses for finding relationship-graph defects:

- institutional trader lenses test whether relation edges overstate portfolio, liquidity, macro, volatility, market-structure, or systematic evidence.
- domain lenses test whether politics, economics, semiconductor, AI infrastructure, and space/defense links are true mechanisms or just narrative noise.
- backend lenses test whether node identity, edge evidence, validator design, and graph retention are strong enough to prevent hidden scoring or graph sprawl.

The upgrade changes the design in four ways:

- every edge type now has a required evidence field.
- node identity now supports `mechanism_id`, `predecessor_node_id`, `edge_evidence_id`, and `review_owner`.
- layer transitions now include expert lens to mechanism graph, mechanism graph to temporal update, and conflict graph to decision trace routes.
- subagent packets now route expert critique to existing Task793-801 write scopes instead of creating new task families.

### Split/OOS Metrics

Not applicable. No performance test or backtest was run.

### Failure Decomposition

The prior stack handled single information packets well. The gap was organic relation:

- how one item changes another item
- how later information updates earlier belief
- how politics, economy, sector, price, and expert lenses share a mechanism
- how contradiction propagates downstream
- how expert review changes the graph without expanding input hunger

Task792 opens the program to close that gap.

### Cost/Slippage Stress Where PnL Changed

Not applicable. No PnL changed.

### Remaining Blockers

- Task793-801 are design tasks until completed.
- Future validator implementation must include graph checks before Task773 packet checks are treated as complete.
- GPT/Chrome review is still pending live external capture unless a later session uses Chrome. The packet and matrix are review specifications, not source truth.

## No-Background Decision-Maker Report

1. Done: 관계망 10단계 프로그램을 열었습니다.
2. Done: 기존 Task773-791을 버리지 않고 노드와 엣지 원천으로 씁니다.
3. Done: 정보끼리 강화/약화/무효화/조건/순서/설명/충돌/소스갭 관계를 갖게 했습니다.
4. Not done: 백테스트와 매매 판단은 없습니다.
5. Next: Task793에서 정보 노드 id를 잠급니다.

## Artifact Manifest

- `step_registry.csv`
- `node_identity_schema.csv`
- `relationship_edge_taxonomy.csv`
- `layer_transition_map.csv`
- `expert_critical_review_matrix.csv`
- `gpt_review_task792_relationship_graph/gpt_chrome_review_packet.md`
- `subagent_packet_plan.md`
- `task_792_decision.csv`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
