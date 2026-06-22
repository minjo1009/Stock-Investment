# Task595 Team Packets

## 필수 - Regime Research

Objective: Own the integrated promotion target and prevent diagnostic evidence from becoming a deployment claim.
Owner Team: Regime Research
Read Scope: `tasks/task_registry.csv`, Task489/496/548/567 reports, Task584 report, Task595 artifacts.
Write Scope: Task595 report updates and future Regime runtime-state contract artifacts only.
Inputs: Daily feedback summary, promotion scorecard, active lane triage.
Required Outputs: Single promotion target decision, acceptance gate language, regime runtime state requirements.
Forbidden Actions:
- No deployment claim from diagnostic-only evidence.
- No future outcome label in assignment logic.
Validation Command: `python scripts/task_registry_validate.py`
Report Requirement: Update Task595 or successor report with acceptance status and next blocker.

## 성원 - Intraday Continuation Research

Objective: Convert intraday research into decision-time runtime state facts.
Owner Team: Intraday Continuation Research
Read Scope: Task491/493/497/550/557 reports and Task590 runtime source contract.
Write Scope: Future intraday runtime state dictionary artifact under a task report directory.
Inputs: Task590 missing runtime state blockers, Task595 scorecard.
Required Outputs: `state_name`, `runtime_column`, `decision_id`, `source_snapshot_id`, `capture_proof_path`.
Forbidden Actions:
- No new factor work before the runtime state dictionary is defined.
- No missing labels treated as negatives.
Validation Command: `python -m unittest tests.test_task584_runtime_strategy_decision_gate`
Report Requirement: State whether inferred matching was used.

## 종찬 - Chart Evidence

Objective: Make evidence order enforce strategy-review truth, not visual polish.
Owner Team: Intraday Continuation Research
Read Scope: `frontend/trader-terminal/src/ChartBlocks.jsx`, Task586/594 reports, Task589 EOD evidence.
Write Scope: Future chart evidence contract artifact or frontend chart implementation task only.
Inputs: Missing runtime fact and stale EOD blockers.
Required Outputs: Evidence order and blocker badge contract.
Forbidden Actions:
- No raw task CSV read from React.
- No chart-only strategy decisions.
Validation Command: `python scripts/frontend_continuity_validate.py`
Report Requirement: Show how missing facts are surfaced as blockers.

## 중훈 - Research Governance

Objective: Turn repeated feedback into registry state, freshness gates, and follow-up checks.
Owner Team: Research Governance
Read Scope: `tasks/task_registry.csv`, Task595 artifacts, daily feedback reports.
Write Scope: Registry row updates and governance reports only.
Inputs: Active lane triage, freshness gate, blocked-source scoreboard.
Required Outputs: parked/stalled candidate list, active lane reduction proposal, stale EOD check.
Forbidden Actions:
- No undocumented artifact moves.
- No active row without validation command.
Validation Command: `python scripts/governance_completion_audit.py`
Report Requirement: Include active rows delta and blocked-source delta.

## 서연 - Slack Reporting

Objective: Make blocker-first reporting unavoidable.
Owner Team: Research Governance
Read Scope: Task587/589 reports, Task588 logs, Task595 freshness gate.
Write Scope: Future Slack/EOD report template task only.
Inputs: Latest runtime date, latest EOD session date, deployment blocker.
Required Outputs: Header with `deployment blocker`, `freshness gap`, `next owner action`, and `STALE_EOD_CLOSEOUT` when needed.
Forbidden Actions:
- No Slack sent status as strategy success.
- No secrets in messages.
Validation Command: `python -m unittest tests.test_task589_nasdaq_paper_ops_hardening`
Report Requirement: State diagnostic-only flag in the first lines.

## 동승 - Backtest & Simulation Infra

Objective: Collapse replay/OOS/cost evidence into one promotion scorecard.
Owner Team: Backtest & Simulation Infra
Read Scope: Task508/509/512/523/528/553 reports.
Write Scope: Future scorecard update artifact only.
Inputs: Task595 promotion scorecard.
Required Outputs: PASS/FAIL matrix with source path and validation date.
Forbidden Actions:
- No same-bar fantasy fills.
- No cost/slippage omission for PnL claims.
Validation Command: `python -m unittest tests.test_task512_backtest_correctness_overfit_audit`
Report Requirement: Mark unknowns as blockers, not failures or negatives.

## 윤헌 - Data & Market Microstructure

Objective: Reduce blocked-source rows through explicit source closure.
Owner Team: Data & Market Microstructure
Read Scope: Task490-590 data/source reports, `data/raw/`, runtime DB/source contracts.
Write Scope: Future source readiness scoreboard update artifact only.
Inputs: Task595 blocked-source scoreboard.
Required Outputs: Missing source, owner, last move date, unblock condition, source proof path.
Forbidden Actions:
- No unavailable raw source approximation.
- No quote/depth/status/LULD approximation as real microstructure.
Validation Command: `python -m unittest tests.test_task590_runtime_market_data_source_unification`
Report Requirement: State missing raw sources explicitly.

## 규승 - Frontend/UI

Objective: Put blockers above product polish.
Owner Team: Research Governance
Read Scope: `frontend/trader-terminal/src/App.jsx`, `frontend/trader-terminal/src/styles.css`, Task586/594 reports.
Write Scope: Future frontend warning hierarchy implementation task only.
Inputs: Blocker badge contract, freshness gate, runtime capture status.
Required Outputs: Top warning hierarchy: stale EOD, diagnostic-only, missing runtime capture, proxy PnL.
Forbidden Actions:
- No raw task CSV reads from React.
- No UI copy that implies deployment readiness.
Validation Command: `python -m unittest tests.test_task586_frontend_paper_ops_integration`
Report Requirement: Include mobile evidence that warnings render above polish.

## Execution & Risk

Objective: Keep broker truth, open exposure, proxy PnL, and kill-switch state explicit.
Owner Team: Execution & Risk
Read Scope: Task582/585/588/589 reports and broker/order/fill artifacts.
Write Scope: Future execution readiness report only.
Inputs: Task589 trading-team feedback, promotion scorecard.
Required Outputs: Broker/order/fill reconciliation status, open exposure review, kill-switch state.
Forbidden Actions:
- No broker truth inferred from local state only.
- No proxy PnL mixed with realized PnL for deployment decisions.
Validation Command: `python -m unittest tests.test_task589_nasdaq_paper_ops_hardening`
Report Requirement: State deployment readiness as diagnostic-only unless all gates pass.
