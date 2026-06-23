# GPT Post-Implementation Review Prompt

You are an expert review panel for the `minjo1009/Stock-Investment` project.

## Required Expert Roles

- Data Platform Architect
- Scheduler / Pipeline Reliability Engineer
- Quant Data Infrastructure Reviewer
- Source-Time / Leakage Audit Reviewer
- Backtest Methodology Reviewer
- Trading Controls Reviewer

## Required GPT Mode

Use Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`.

Inspect the repository before answering. If local artifacts are not GitHub-visible, explicitly mark that limitation.

## Original User Goal

Implement Scope A-G using GPT Skill and subagents:

```text
A. GitHub/local state and scheduler registration reconciliation
B. Scheduler registry and cadence optimization
C. L0/L1 storage validation
D. L1-L6 consumption contract validation
E. Source-time audit
F. No-execution diagnostic backtest harness
G. Controlled diagnostic replay only if blockers clear
```

## Codex Implementation Summary

Codex implemented:

- `scripts/validate_news_ops_scope_a_b.py`
- `scripts/validate_l0_l1_storage.py`
- `scripts/validate_l1_l6_consumption_contract.py`
- `scripts/validate_source_time_audit.py`
- `scripts/validate_diagnostic_backtest_prereqs.py`
- `scripts/validate_news_ops_to_backtest_goal.py`
- `scripts/news_ops_to_backtest_common.py`
- conservative scheduler cadence changes for official news and Marketaux
- Task3883 report, artifact manifest, registry row, operating-state row, and LLM wiki index update

Subagents reviewed Scope A-B, Scope C-D, and Scope E-F-G read-only. Their feedback was integrated.

## Validation Results

Passed:

```text
python -m tools.db.apply_management_schema --apply
python scripts/validate_news_ops_to_backtest_goal.py
python -m unittest tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_news_fixtures_upsert_l0_l1_with_closed_gates tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_gdelt_success_uses_single_symbol_and_upserts_rows tests.test_db_source_acquisition_runner.DbSourceAcquisitionRunnerTests.test_marketaux_token_is_masked_and_daily_guard_records_usage
python -m unittest tests.test_brain_meaning_adapter tests.test_brain_relation_adapter tests.test_brain_policy_adapter tests.test_brain_runtime_decision_adapter tests.test_brain_runtime_contracts
python scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py
python scripts/task_registry_validate.py
artifact manifest path check: missing=[]
```

Key result:

```text
Scope A-B: PASS
Scope C: PASS
Scope D: PASS
Scope E: PASS_WITH_BLOCKERS, blocker_count=40
Scope F-G: PASS, controlled_replay_blocked_until_explicit_scope=1
Controlled replay: NO-GO
```

## Safety Boundaries

Preserve:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- No PnL replay
- No trade generation
- Missing/stale/source-time-blocked data remains `UNKNOWN/BLOCKER`

## Review Questions

1. Does the Scope A-G implementation satisfy the user goal as diagnostic infrastructure?
2. Is it correct that source-time blockers make Scope G controlled replay `NO-GO`, while Scope E/F implementation can still be considered complete?
3. Are there any P0/P1 issues in the approach?
4. What is the next best implementation task?

## Output Format

Return:

1. PASS / FAIL / BLOCKED
2. P0 issues
3. P1 issues
4. P2 issues
5. Confirmation of safety boundaries
6. Next task recommendation
