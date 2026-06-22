# Task772 Trader Brain Precision Program

## Decision Summary

- Verdict: `TRADER_BRAIN_PRECISION_10_STEP_PROGRAM_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 10 planned tasks; 6 owner lanes; 0 buy/sell/rank/score/sizing outputs; 0 backtests run.
- What changed: Added a bounded 10-step program for strengthening the Task756-771 brain stack without expanding input hunger.
- Next action: Execute Task773 through Task781 as contract and governance tasks before any controlled adapter implementation.

Task772 starts the next program after Task771. It is not a trading system, not a strategy acceptance task, not a backtest, and not deployment readiness.

## Quant Expert Report

### Data Source And Source Readiness

Inputs reviewed were the current operating state, Task771 canonical brain registry report, Task756 parent summary, the subagent packet standard, the skill and subagent canonicalization map, the project status authority matrix, and the report standard.

No market data, broker data, fills, order records, returns, future prices, labels, or PnL were used.

### Exact Join Keys

No data joins were performed. Future work must use explicit upstream ids and exact timestamps only:

- `evidence_id`
- `source_event_id`
- `primitive_fact_id`
- `meaning_object_id`
- `edge_id`
- `candidate_bundle_id`
- exact `asof_ts`
- exact `entry_ts` when same-timestamp review is required

Inferred lifecycle matching and symbol/date/price/time proximity fallback matching remain forbidden.

### Leakage Audit

The program is designed around a small but more trader-like reasoning loop:

```text
attention budget
-> salience triage
-> working memory
-> hypothesis ladder
-> contradiction pressure
-> minimal disconfirmation
-> decision journal trace
-> controlled adapter boundary
-> governance closeout
```

The guardrail is that better judgment must come from better compression and explicit uncertainty, not from pouring in every possible input. Each step has an overengineering stop rule.

Forbidden outputs across the program:

- buy or sell instruction
- rank or global top list
- alpha score or hidden numeric total
- actual sizing or allocation
- optimizer output
- order, fill, or broker-truth claim
- backtest eligibility or performance claim
- deployment readiness
- real-capital permission

### Split/OOS Metrics

Not applicable. Task772 does not run split, OOS, performance, cost, slippage, optimizer, or backtest analysis.

### Failure Decomposition

The unfinished part after Task771 is not that the brain needs more raw information. The gap is that the brain still needs a better bounded reasoning spine:

- what to pay attention to
- what to ignore
- what stays in working memory
- what contradicts the thesis
- what would falsify the current interpretation
- what can be passed to a future adapter without becoming a trading signal

### Cost/Slippage Stress Where PnL Changed

Not applicable. No PnL changed.

### Remaining Blockers

- Task773-781 are design and governance tasks until completed.
- The controlled adapter boundary must remain separate from strategy logic.
- Future backtest work still requires a separate controlled adapter implementation task.

## No-Background Decision-Maker Report

1. Done: 다음 10단계 프로그램을 만들었습니다.
2. Done: 핵심은 더 많은 데이터를 넣는 것이 아니라 더 좋은 압축과 중지 규칙입니다.
3. Done: 각 단계는 서브에이전트에 배정할 수 있게 쪼갰습니다.
4. Not done: 백테스트는 하지 않았습니다.
5. Not done: 전략 승인도 아닙니다.
6. Next: Task773부터 순서대로 계약을 실행합니다.

## Artifact Manifest

### Inputs

- `docs/operating_system/project_operating_state.md`
- `docs/reports/task_771_canonical_brain_registry/task_771_canonical_brain_registry.md`
- `docs/reports/task_756_trader_brain_15_step_program/task756_summary.csv`
- `docs/ownership/subagent_packet_standard.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `docs/architecture/project_status_authority_matrix.md`
- `docs/report_standard.md`

### Outputs

- `task_772_trader_brain_precision_program.md`
- `step_registry.csv`
- `gpt_review_packet.md`
- `gpt_institutional_backend_review_summary.csv`
- `subagent_packet_plan.md`
- `task772_summary.csv`
- `task_772_decision.csv`
- `validation_log.md`
- `artifact_manifest.csv`

### Validation Commands

- `python scripts/trader_brain_precision_program_validate.py`

Validation authority: governance and research contract validation only.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
