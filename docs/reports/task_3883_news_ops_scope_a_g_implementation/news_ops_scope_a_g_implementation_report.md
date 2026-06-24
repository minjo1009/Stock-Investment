# Task3883 News Ops Scope A-G Implementation

## Summary

Task3883 implemented the Scope A-G verification path selected by Task3882.

Implemented path:

```text
A. GitHub/local state and scheduler registration reconciliation
B. Scheduler cadence policy validation
C. L0/L1 storage evidence validation
D. L1-L6 no-trade consumption contract validation
E. Source-time audit with blocker report
F. No-execution diagnostic backtest harness
G. Controlled replay NO-GO matrix
```

This remains diagnostic-only. The source-time blocker burn-down has cleared active
Scope E blockers, but controlled replay is still `NO-GO` because market-data
manifest, split/OOS, cost/slippage, and owner-approved replay scope are not
cleared.

## Scope Results

| Scope | Result | Evidence |
| --- | --- | --- |
| A | PASS | `scope_a_b_scheduler_reconciliation.json` |
| B | PASS | `scope_a_b_config_jobs.csv`, `scope_a_b_db_registry.csv` |
| C | PASS | `scope_c_l0_l1_storage_validation.json` |
| D | PASS | `scope_d_l1_l6_consumption_validation.json` |
| E | PASS | `scope_e_source_time_audit.json`, `scope_e_source_time_blockers.csv`, `scope_e_source_time_quarantine.csv` |
| F | PASS | `scope_f_no_execution_harness_manifest.json` |
| G | NO-GO | `scope_g_controlled_replay_go_no_go_matrix.csv` |

## Implemented Validators

- `scripts/validate_news_ops_scope_a_b.py`
- `scripts/validate_l0_l1_storage.py`
- `scripts/validate_l1_l6_consumption_contract.py`
- `scripts/validate_source_time_audit.py`
- `scripts/validate_diagnostic_backtest_prereqs.py`
- `scripts/validate_news_ops_to_backtest_goal.py`

## Scheduler Cadence Changes

The scheduler posture was aligned with Task3882's conservative cadence plan:

- `official_public_releases`: 30 minutes, disabled by default.
- `gdelt_news_events`: 15 minutes, disabled by default, one-symbol/cooldown behavior remains in the source runner.
- `marketaux_news_free`: 60 minutes, disabled by default, token-gated.

The active DB scheduler registry was reseeded through the guarded management schema. Permission columns remain closed.

## Source-Time Audit Finding

The latest local source-time audit now reports active blocker count zero.

Resolved blocker class:

- Cached `market_bars_5m` receipts where the source timestamp was later than
  the capture timestamp.

Root cause:

- The cached 5-minute market bar evidence path used `MAX(bar_end_ts)` from the
  table. When the table contained an in-progress bar, the recorded source
  timestamp could be later than the diagnostic capture timestamp.

Repair:

- The cached market bars evidence path now excludes rows whose `bar_end_ts` is
  after the capture timestamp.
- Derived diagnostic indicators also exclude open bars.
- Existing invalid receipts are preserved in a quarantine table and exported to
  `scope_e_source_time_quarantine.csv`; they are not deleted and are not treated
  as active replay-eligible source-time evidence.

Current audit:

```text
source_time_blocker_count = 0
quarantined_receipt_count = 79
```

## No-Execution Harness

The harness generated:

- input manifest
- market data gate report
- split/OOS and cost/slippage draft
- dry run plan
- dry run summary
- artifact audit
- controlled replay go/no-go matrix

All execution counts remain zero:

```text
price_lookup_count = 0
trade_row_count = 0
pnl_metric_count = 0
engine_call_count = 0
```

## Validation

Passed:

```text
python -m tools.db.apply_management_schema --apply
python scripts/validate_news_ops_to_backtest_goal.py
python -m unittest tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_news_fixtures_upsert_l0_l1_with_closed_gates tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_gdelt_success_uses_single_symbol_and_upserts_rows tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_marketaux_token_is_masked_and_daily_guard_records_usage
python -m unittest tests.test_brain_meaning_adapter tests.test_brain_relation_adapter tests.test_brain_policy_adapter tests.test_brain_runtime_decision_adapter tests.test_brain_runtime_contracts
python scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py
python scripts/task_registry_validate.py
```

## GPT Review

GPT post-implementation review was captured after asking Agent Mode to inspect
GitHub context for `minjo1009/Stock-Investment`.

Result:

```text
BLOCKED - GitHub-visible review
```

GPT's blocker is that the Task3883 implementation artifacts are local and not
visible on GitHub main. It agreed that, if the local validation results are
accepted as factual, the diagnostic infrastructure is conditionally valid, Scope
E/F are implemented, and Scope G must remain `NO-GO` while source-time blockers
exist. GPT reviewed the earlier 40-blocker run; later local reruns still
observed non-zero blockers.

Next recommendation from GPT:

```text
Task3883 GitHub Reconciliation + Source-Time Blocker Burn-down v1
```

After publishing commit `4150ddc880c0d4a667770d9cb16594f7ed627e1c` to GitHub
main, GPT re-reviewed the GitHub-visible evidence and returned:

```text
PASS - prior GitHub visibility blocker resolved
```

GPT confirmed that Task3883 is GitHub-visible, Scope E remains
`PASS_WITH_BLOCKERS`, and Scope G correctly remains `NO-GO` while blockers are
nonzero. GPT's remaining recommendation is source-time blocker burn-down before
any replay eligibility work.

After the source-time blocker burn-down, Scope E was revalidated as `PASS` with
zero active blockers. Scope G remains diagnostic-only and controlled replay
remains `NO-GO`.

## Safety Boundary

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
No broker mutation added
No live order path added
No paper promotion added
Controlled replay remains NO-GO
Missing/stale/non-approved replay data remains UNKNOWN/BLOCKER
```

## Next Required Work

Define and approve the next Scope G controlled replay prerequisites: certified
market-data manifest, split/OOS plan, cost/slippage config, and explicit
owner-approved diagnostic replay scope. This source-time repair does not grant
strategy acceptance, deployment readiness, paper/live permission, broker
mutation permission, or real-capital permission.
