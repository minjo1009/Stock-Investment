# Task3885 Scope E Source-Time Burn-Down and Scope G Diagnostic Progress

## Objective

Resolve Scope E active source-time blockers and proceed Scope G only within the
diagnostic no-execution boundary.

Scope E goal:

```text
source_ts <= capture_ts <= available_to_brain_ts <= node_asof_ts <= edge_asof_ts <= bundle_asof_ts <= adapter_created_ts <= tradable_after_ts
```

This is a leakage control. A source receipt that says data was captured before
the source timestamp is not replay-eligible.

## GPT Loop Summary

| Loop | Result |
| --- | --- |
| 1 | GPT approved the diagnosis and fix direction: exclude open bars, quarantine invalid receipts, keep Scope G diagnostic-only. |
| 2 | GPT reviewed GitHub-visible commit `0cd5c99` and approved Scope E resolved with active blockers cleared while Scope G remains diagnostic-only `NO-GO`. |

## Source-Time Blocker Detail

Before repair:

```text
Scope E status: PASS_WITH_BLOCKERS
Active blocker class: source_ts > capture_ts
Affected family: market_bars_5m
Observed blocker count: 64 in the pre-repair audit artifact
```

Meaning:

- A 5-minute bar ending at a later timestamp was recorded as already captured.
- This creates a lookahead risk for any replay because the brain could appear to
  know a bar before it had closed.

Root cause:

- The cached 5-minute market-bar evidence path used the table-level maximum
  `bar_end_ts`.
- When an in-progress bar existed in the cached table, that open bar could
  become the receipt `source_ts`.

## Repair Implemented

Implemented changes:

- Cached market-bar evidence now hashes and records only rows whose bar end is
  not later than the capture timestamp.
- Derived diagnostic indicators now consume only closed market bars.
- Historical invalid receipts are preserved in a quarantine table and excluded
  from active source-time audit.
- The source-time audit now exports quarantine evidence separately from active
  blockers.

No strategy logic, broker mutation, live order path, paper promotion, or real
capital path was added.

## Validation Results

Passed:

```text
python -m py_compile tools/db/run_registered_loop_once.py scripts/validate_source_time_audit.py tests/test_db_registered_loop_runner.py
python -m unittest tests.test_db_registered_loop_runner.DbRegisteredLoopRunnerTests.test_current_market_bars_can_be_fresh_without_opening_gates tests.test_db_registered_loop_runner.DbRegisteredLoopRunnerTests.test_market_bars_adapter_excludes_open_bars_and_quarantines_prior_violations
python -m tools.db.run_registered_loop_once --apply --job market_bars_5m_refresh --json data/artifacts/task_3883_news_ops_scope_a_g_implementation/market_bars_source_time_repair_run.json
python scripts/validate_source_time_audit.py
python scripts/validate_diagnostic_backtest_prereqs.py
python scripts/validate_news_ops_to_backtest_goal.py
```

Scope E current result:

```text
status = PASS
source_time_blocker_count = 0
quarantined_receipt_count = 79
```

Scope G current result:

```text
controlled_diagnostic_replay = NO_GO
price_lookup_count = 0
trade_row_count = 0
pnl_metric_count = 0
engine_call_count = 0
```

Known test gap:

```text
python -m unittest tests.test_db_registered_loop_runner
```

The full test class still has three count-expectation failures in older broad
fixture tests. The two focused market-bar source-time tests pass, and the
Task3883 umbrella validator passes. The broad fixture count failures were not
used as acceptance evidence.

## Scope G Status

Scope G progressed to the next diagnostic state:

- Source-time is no longer the active blocker.
- The no-execution harness remains valid.
- Controlled replay still remains `NO-GO`.

Remaining Scope G blockers:

- Certified market-data manifest is not approved.
- Split/OOS plan is not owner-approved.
- Cost/slippage configuration is not owner-approved.
- Explicit controlled diagnostic replay scope is not approved.

## Safety Boundary

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
Broker mutation: FORBIDDEN
Live order: FORBIDDEN
Paper promotion: FORBIDDEN
```

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
