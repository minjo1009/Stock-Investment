# Subagent Broker Lifecycle Ops Skill

## Purpose

Own the paper-broker lifecycle operations path:

- order submit
- status/fill polling
- cancel/reconcile
- failure debugging
- evidence and fixture capture

This skill prevents repeated trial-and-error when paper runs fail for non-strategy reasons.

## When To Use

Use this skill whenever work touches:

- `src/app/task_091a_controlled_broker_lifecycle.py`
- `src/execution/cancel_loop.py`
- `src/integration/kis_client.py`
- `docs/reports/task_091a/*`
- `tests/fixtures/kis/real/*`

Also use when the user asks:

- "why did the paper/broker run fail?"
- "why did order submission fail?"
- "verify cancel/fill lifecycle"
- "주문/취소/체결 lifecycle 검증"

## Scope Boundary

This skill manages broker lifecycle operations only.

Never use this skill to tune:

- strategy alpha
- entry/exit rules
- portfolio ranking
- backtest profitability

## Operating Model

The subagent must execute this sequence:

1. Preflight
   - `KIS_ENVIRONMENT == paper`
   - required credentials exist
   - limit-only guard active
   - `qty == 1`
   - `max_notional` within policy
2. Run
   - `CANCEL_TEST` or `FILL_TEST`
3. Trace
   - parse JSON report in `docs/reports/task_091a/`
   - classify failure reason
4. Triage
   - transient vs terminal
5. Fix
   - only lifecycle, pacing, or status-mapping fixes
6. Revalidate
   - rerun same mode and same symbol/notional constraints
7. Record
   - write cause/fix/outcome summary to ops task log

## Failure Taxonomy

Treat causes as one of:

1. Preflight Block
   - `ACTIVE_ORDER_EXISTS_FOR_SYMBOL`
   - `NOTIONAL_CAP_BREACH`
   - missing env/credentials
2. Pacing/Rate-Limit
   - `EGW00201` throttling
3. Status Mapping Drift
   - broker `UNKNOWN` in middle states
   - terminal known but local remains unknown
4. Reconciliation Drift
   - loop transient mismatch vs final mismatch
5. True Critical
   - unresolved final state
   - `UNKNOWN` escalated
   - unresolved broker/local mismatch

## Decision Policy

- PASS:
  - terminal lifecycle reached, such as `FILLED` or `CANCELLED`
  - no unresolved unknown
  - no final critical mismatch
- WARNING:
  - transient throttling or reconciliation issues occurred, but final state resolved safely
- FAIL:
  - unresolved final state
  - unknown escalation
  - unresolved reconciliation critical
  - market/live guard breach

Passing this skill's checks does not mean strategy acceptance, deployment readiness, broker-truth SELL completeness, or real-capital permission.

Use `docs/architecture/test_validation_canonicalization_map.md` for validation authority. Broker lifecycle tests are usually `EXECUTION_HEALTH` or `ACCEPTANCE_EVIDENCE_REVIEW`, not fast unit gates.

Use `docs/architecture/src_canonicalization_map.md` before changing shared execution, risk, integration, or app package modules.

## Required Artifacts

- report JSON: `docs/reports/task_091a/task_091a_controlled_lifecycle.json`
- report MD: `docs/reports/task_091a/task_091a_controlled_lifecycle.md`
- sanitized fixtures: `tests/fixtures/kis/real/task_091a_*.json`

## Runbook Commands

```powershell
$env:PYTHONPATH="src"
python -m app.task_091a_controlled_broker_lifecycle --mode CANCEL_TEST --symbol MSFT --qty 1 --max-notional 500 --env-file "config/kis_paper.env" --cancel-poll-interval-seconds 4 --max-cancel-attempts 8 --hard-timeout-seconds 60
```

```powershell
$env:PYTHONPATH="src"
python -m app.task_091a_controlled_broker_lifecycle --mode FILL_TEST --symbol MSFT --qty 1 --max-notional 500 --env-file "config/kis_paper.env" --status-poll-interval-seconds 2 --max-status-poll-attempts 12 --hard-timeout-seconds 90
```

## Handoff Output Contract

Use this exact block in subagent handoff:

```text
**lifecycle result**
- mode:
- status:
- broker_order_id:
- final_state:

**root cause**
- ...

**fix applied**
- ...

**evidence**
- docs/reports/task_091a/...
- tests/fixtures/kis/real/...

**validation authority**
- EXECUTION_HEALTH or ACCEPTANCE_EVIDENCE_REVIEW

**does not mean**
- strategy accepted
- deployment ready
- real capital allowed
- broker-truth SELL complete unless the exact acceptance artifacts prove it

**next run command**
- ...
```

## T600-6 Broker Truth SELL Certification

Use this section when work touches:

- `src/execution/broker_truth_closed_trade_capture.py`
- `src/execution/exit_fill_reconciliation.py`
- `src/execution/broker_truth_exit_mapper.py`
- `docs/reports/task_600_6_broker_truth_closed_trade_capture/*`
- `tests/test_task600_6_broker_truth_closed_trade_capture.py`

T600-6 is read-only evidence certification. It may inspect local runtime DB tables, but it must not place orders or query live broker state unless the user explicitly asks for a controlled paper status/fill capture run.

Accepted broker-truth SELL sources are exact broker/order-status evidence only:

- `ORDER_STATUS`
- `BROKER_ORDER_STATUS`
- `BROKER_ORDER_STATUS_REFRESH`
- `BROKER_EXECUTION_REPORT`
- `EXECUTION_REPORT`
- `BROKER_FILL`
- `BROKER_TRADE_CONFIRM`
- `KIS_ORDER_STATUS`

Rejected SELL sources must stay rejected:

- `PAPER_RUNTIME_SYNTHETIC_EXIT`
- `POSITION_DELTA_FALLBACK`
- `SHADOW`
- `SYNTHETIC`
- `SIMULATED`
- `BACKTEST`

Required T600-6 command:

```powershell
python -m src.execution.broker_truth_closed_trade_capture --db-path trading.db --report-dir docs\reports\task_600_6_broker_truth_closed_trade_capture
```

Acceptance requires:

- `broker_truth_sell_fills > 0`
- exact broker fill linkage above 95%
- `inferred_matching_used_flag == 0`
- `proximity_fallback_used_flag == 0`
- no runtime/shadow/simulated/position-delta SELL counted as broker truth

Required T600-6 artifacts:

- `docs/reports/task_600_6_broker_truth_closed_trade_capture/broker_truth_closed_trade_report.md`
- `docs/reports/task_600_6_broker_truth_closed_trade_capture/broker_truth_closed_trade_summary.csv`
- `docs/reports/task_600_6_broker_truth_closed_trade_capture/broker_truth_closed_trade_rejected_sources.csv`
