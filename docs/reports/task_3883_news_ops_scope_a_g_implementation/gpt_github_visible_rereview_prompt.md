# GPT Re-Review Prompt After GitHub Main Publication

You are an expert review panel for the `minjo1009/Stock-Investment` project.

Required mode: Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`.

Required expert roles:
- Data Platform Architect
- Scheduler / Pipeline Reliability Engineer
- Quant Data Infrastructure Reviewer
- Source-Time / Leakage Audit Reviewer
- Backtest Methodology Reviewer
- Trading Controls Reviewer

Original issue:
Your prior post-implementation review for Task3883 was BLOCKED because core Task3883 artifacts were local-only and not visible on GitHub main.

Current update:
Codex committed and pushed the Task3882 planning evidence and Task3883 implementation/evidence to GitHub main.

Commit:
`4150ddc880c0d4a667770d9cb16594f7ed627e1c` / `4150ddc Publish news ops backtest verification`

Codex verified via remote git tree that these paths now exist on `origin/main`:
- `docs/reports/task_3883_news_ops_scope_a_g_implementation/news_ops_scope_a_g_implementation_report.md`
- `scripts/validate_news_ops_to_backtest_goal.py`
- `data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_e_source_time_audit.json`
- `tasks/task_registry.csv`

Also included:
- Task3882 plan report and GPT plan prompt/response
- Task3883 GPT post-implementation prompt/response
- Scope A-G validators
- Task3883 artifact manifest and source-time/no-execution/go-no-go artifacts
- News L0/L1 source normalization and scheduler registration dependencies needed by the validators

Validation before push:
- `git diff --cached --check`: PASS
- `python scripts/validate_news_ops_to_backtest_goal.py`: PASS with `Scope E PASS_WITH_BLOCKERS`; latest local blocker count observed 66 at validation time
- `python scripts/task_registry_validate.py`: PASS
- Task3882/Task3883 manifest path check: PASS
- News provider unit tests selected: PASS
- Registered-loop cached news test selected: PASS

Safety boundaries preserved:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- No PnL replay
- No trade generation
- Source-time blocked data remains UNKNOWN/BLOCKER
- Controlled replay remains NO-GO while source-time blockers are nonzero

Review task:
1. Re-check GitHub main at commit `4150ddc` or latest main.
2. Determine whether the prior `GitHub-visible artifact not found` BLOCKED reason is now resolved.
3. Evaluate whether Task3883 satisfies the original diagnostic infrastructure goal:
   - A. GitHub/local state and scheduler registration reconciliation
   - B. Scheduler registry and cadence optimization
   - C. L0/L1 storage validation
   - D. L1-L6 consumption contract validation
   - E. Source-time audit
   - F. No-execution diagnostic backtest harness
   - G. Controlled diagnostic replay NO-GO while blockers remain
4. Identify any remaining P0/P1 issues.
5. Confirm whether Scope G correctly remains NO-GO due nonzero source-time blockers.

Return:
1. PASS / FAIL / BLOCKED
2. Whether prior GitHub-visibility blocker is resolved
3. P0 issues
4. P1 issues
5. P2 issues
6. Safety boundary confirmation
7. Next task recommendation
