# Task773 Attention Budget Contract

## Decision Summary

- Verdict: `ATTENTION_BUDGET_CONTRACT_COMPLETE_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 5 intake states; 8 minimal packet fields; 15 expert lens budget rows; 0 trading outputs.
- What changed: Defined the Task773 attention budget contract that controls what information is enough for review before salience triage.
- Next action: Task774 should consume only `enough_for_review` packets and preserve `defer`, `source_gap`, `block`, and `noise` states.

Task773 is the first real branchpoint. It prevents the trader brain from confusing more input with better judgment.

## Quant Expert Report

### Data Source And Source Readiness

Task773 used only governance and prior contract artifacts. It did not use market data, broker data, returns, labels, prices, PnL, orders, fills, or future outcomes.

The attention contract is split into three artifacts:

- `intake_state_catalog.csv`
- `minimal_input_packet_schema.csv`
- `expert_lens_budget.csv`

### Exact Join Keys

No joins were performed. Any future generated packet must carry explicit ids:

- `attention_packet_id`
- `source_event_id`
- `evidence_id`
- `asof_ts`

Forbidden matching remains:

- symbol/date/price/time fallback matching
- inferred lifecycle matching
- price reaction matching
- future PnL or outcome-assisted matching

### Leakage Audit

The allowed state that can move forward is only `enough_for_review`. It means only that the packet can enter salience triage. It does not mean the thesis is correct, tradable, ranked, scored, or backtest eligible.

The five states are:

- `enough_for_review`
- `defer`
- `source_gap`
- `block`
- `noise`

Missing source remains missing. It is never converted into negative evidence.

### Split/OOS Metrics

Not applicable. No performance test or backtest was run.

### Failure Decomposition

Task773 blocks three failure modes:

- input hunger: asking for every possible source before thinking
- premature promotion: passing weak packets because the narrative sounds plausible
- expert sprawl: letting specialist lenses create unlimited research requests

### Cost/Slippage Stress Where PnL Changed

Not applicable. No PnL changed.

### Remaining Blockers

- Task774 must not turn salience into a score.
- Task788/789 can later harden backend schema and source sufficiency states.
- Task791 must hand off implementation without backtest execution.

## No-Background Decision-Maker Report

1. Done: 입력 예산 계약을 만들었습니다.
2. Done: 충분함, 보류, 소스갭, 차단, 노이즈 상태를 나눴습니다.
3. Done: 전문가별 입력 요구를 작게 제한했습니다.
4. Not done: 백테스트는 하지 않았습니다.
5. Next: Task774에서 중요한 정보와 잡음을 나눕니다.

## Artifact Manifest

- `task_773_attention_budget_contract.md`
- `intake_state_catalog.csv`
- `minimal_input_packet_schema.csv`
- `expert_lens_budget.csv`
- `task_773_decision.csv`
- `artifact_manifest.csv`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
