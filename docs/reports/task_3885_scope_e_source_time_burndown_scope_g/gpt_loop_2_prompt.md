# GPT Loop 2 Prompt

Loop 2 review request. Please read GitHub repo/main for
https://github.com/minjo1009/Stock-Investment after commit `0cd5c99`
(`Clear Scope E source-time blockers`). This is review-only; local validator
output remains source of truth.

Inspect these GitHub-visible files if available:

- `tools/db/run_registered_loop_once.py`
- `scripts/validate_source_time_audit.py`
- `tests/test_db_registered_loop_runner.py`
- `data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_e_source_time_audit.json`
- `data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_e_source_time_summary.csv`
- `data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_e_source_time_quarantine.csv`
- `data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_g_controlled_replay_go_no_go_matrix.csv`
- `docs/reports/task_3885_scope_e_source_time_burndown_scope_g/scope_e_source_time_burndown_scope_g_report.md`

Local validation results after commit:

- `python -m py_compile tools/db/run_registered_loop_once.py scripts/validate_source_time_audit.py tests/test_db_registered_loop_runner.py`: PASS
- Focused market-bar source-time tests: PASS
- `python -m tools.db.run_registered_loop_once --apply --job market_bars_5m_refresh --json .../market_bars_source_time_repair_run.json`: PASS
- `python scripts/validate_source_time_audit.py`: PASS, blocker_count=0
- `python scripts/validate_diagnostic_backtest_prereqs.py`: PASS no-execution harness, controlled_replay_blocked_until_explicit_scope=1
- `python scripts/validate_news_ops_to_backtest_goal.py`: PASS
- `python scripts/task_registry_validate.py`: PASS

Current Scope E artifact:

- status=PASS
- source_time_blocker_count=0
- quarantined_receipt_count=79

Current Scope G artifact:

- controlled_diagnostic_replay status=NO_GO
- price_lookup_count=0
- trade_row_count=0
- pnl_metric_count=0
- engine_call_count=0

Known limitation:

- `python -m unittest tests.test_db_registered_loop_runner` still has three older broad count-expectation failures. Focused market-bar tests and umbrella validator pass.

Questions:

A. Does GitHub-visible implementation support Scope E resolved as active source-time blockers cleared?
B. Is quarantining invalid receipts instead of deleting them acceptable?
C. Is Scope G correctly progressed only to diagnostic/no-execution while controlled replay remains NO-GO?
D. Any remaining blocker that should be reported to the user?
