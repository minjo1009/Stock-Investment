# Task595 Feedback Integrated Development Plan

## Decision Summary

- Verdict: ACTIVE_DEVELOPMENT_PLAN_CREATED
- Strategy acceptance status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Objective: 필수가 총괄하고 각 팀장이 daily feedback을 누락 없이 반영해 프로젝트를 deployment-ready 쪽으로 압축 개발한다.
- Target metrics:
  - active rows baseline before Task595 registration: 102
  - active rows after Task595 registration: 103
  - active rows Wave 1 target: <= 40 after parked/stalled triage
  - blocked-source rows: current 30 -> Wave 1 target <= 20 with explicit unblock condition
  - promotion scorecard: 1 canonical PASS/FAIL matrix maintained for the selected promotion target
  - runtime capture: regime state and intraday state must be decision-time facts, joined by `decision_id` and `source_snapshot_id`
  - freshness: latest runtime run date must equal latest EOD session date before any daily report is considered current
- Forbidden actions:
  - No inferred lifecycle matching.
  - No symbol/date/price/time proximity fallback.
  - No missing label to negative conversion.
  - No missing raw source approximation.
  - No deployment claim from diagnostic-only evidence.
  - No Slack or UI success treated as strategy acceptance.
- Available raw/runtime sources:
  - `tasks/task_registry.csv`
  - `docs/reports/daily_feedback_team_summary_2026-06-02/daily_feedback_team_summary_2026-06-02.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_summary.csv`
  - `logs/task588_nasdaq_paper_loop_stdout.log`
  - Current runtime-source reports for Task583-590
- Missing raw/runtime sources:
  - Runtime-persisted regime state for each decision.
  - Runtime-persisted intraday continuation state for each decision.
  - Firm-grade full live microstructure source closure for blocked-source rows.
- Owner team: Regime Research, led by 필수.
- Reviewer teams: Research Governance, Backtest & Simulation Infra, Data & Market Microstructure.
- Output directory: `docs/reports/task_595_feedback_integrated_development_plan/`
- Large artifact directory: not applicable for this planning task.
- Validation:
  - `python scripts/task_registry_validate.py`
  - `python scripts/codeowners_coverage_validate.py`
  - `python scripts/governance_completion_audit.py`
- Completion criteria:
  - Task595 registry row exists.
  - Team execution board exists.
  - Promotion scorecard exists.
  - Blocked-source scoreboard exists.
  - Freshness gate exists.
  - Subagent/team packets exist.
  - Validation commands are recorded and attempted.
- Failure criteria:
  - A team continues work without an owner, artifact path, validation command, or blocker.
  - Any report presents diagnostic evidence as live deployment readiness.

## Quant Expert Report

### Operating Read

The daily feedback from 2026-05-21 through 2026-05-28 repeated the same core failures:

- active lane compression was not enforced.
- runtime regime/intraday state capture was not closed.
- promotion scorecard was not consolidated.
- blocked-source scoreboard was not created.
- Slack/UI/ops improvements were over-read as strategy progress.
- stale EOD closeout was not escalated strongly enough when runtime evidence moved ahead of EOD reporting.

Task595 converts those critiques into governed execution artifacts instead of another narrative reminder.

### Canonical Promotion Target

Wave 1 promotion work is centered on `Task584 Runtime Strategy Decision Gate`.

Reason:

- The repeated blocker is not a lack of new factors.
- The project cannot promote a strategy until decision-time facts are complete.
- Task584 is the natural place to require `decision_id`, `source_snapshot_id`, runtime regime state, runtime intraday state, and order/fill lineage before any candidate is interpreted as promotion-ready.

Dependencies remain active but are no longer parallel promotion lanes:

- Task590: runtime market data source contract.
- Task589: EOD closeout and broker/order/fill feedback.
- Task586/594: frontend blocker badges and lineage visibility.
- Task493/497/550/557: intraday definitions feeding the runtime state dictionary.
- Task489/496/548/567: regime definitions feeding the runtime regime state.
- Task508/509/512/523/528/553: backtest/OOS/cost/replay evidence feeding the scorecard.

### Team Execution Model

필수 owns the integrated decision. Each team lead owns a bounded delivery surface:

- 필수 / Regime Research: single promotion target, regime runtime state requirement, final acceptance gate.
- 성원 / Intraday Continuation Research: intraday runtime state dictionary and exact join key contract.
- 종찬 / Chart Evidence: evidence order and blocker badge semantics.
- 중훈 / Research Governance: active lane triage, stale EOD gate, registry/report discipline.
- 서연 / Slack Reporting: blocker-first report header and stale closeout escalation.
- 동승 / Backtest & Simulation Infra: promotion scorecard PASS/FAIL matrix.
- 윤헌 / Data & Market Microstructure: blocked-source scoreboard and source gap closure.
- 규승 / Frontend/UI: warning hierarchy and catalog-backed blocker visibility.
- Execution & Risk: broker truth, open exposure, proxy PnL, kill-switch, reconciliation.

### Data Integrity Gate

Task595 does not make new strategy claims. It explicitly states:

- inferred matching used: no
- missing labels treated as negatives: no
- missing raw sources approximated: no
- deployment-ready claim: no

Any future Task584 promotion claim must show:

- exact key used for joins
- lifecycle identity source
- available raw fields
- missing raw fields
- inferred matching flag
- label leakage audit
- source path and artifact lineage

### Development Waves

Wave 1 closes governance and runtime evidence basics.

1. 중훈 reduces active work into one promotion lane plus dependency lanes.
2. 성원 and 윤헌 define runtime state columns and source lineage for regime/intraday capture.
3. 동승 publishes the scorecard and marks unknowns as blockers, not negatives.
4. 종찬 and 규승 make missing capture and stale EOD first-class blocker badges.
5. 서연 forces blocker-first Slack/EOD wording.
6. Execution & Risk keeps broker truth and proxy PnL separate.

Wave 2 implements runtime state persistence and replay validation.

1. Add runtime-persisted `regime_state` and `intraday_state` facts keyed by `decision_id` and `source_snapshot_id`.
2. Rebuild the frontend catalog from runtime facts only.
3. Rerun scorecard checks with source paths and validation dates.
4. Reclassify active rows after blocked-source movement.

Wave 3 considers promotion only after the scorecard is no longer mostly blocker-driven.

Required before promotion:

- split/OOS evidence
- leakage audit
- cost/slippage validation
- broker truth reconciliation
- live-source readiness
- runtime capture completeness
- stale EOD freshness pass

### Remaining Blockers

- active rows baseline was 102 before Task595 registration and is 103 after registering this governance/development task.
- blocked-source rows remain 30 at Task595 creation time.
- runtime regime/intraday states are still not proven captured as decision-time facts.
- promotion scorecard exists as a control artifact but is currently blocker-heavy.
- this task does not implement live trading readiness.

## No-Background Decision-Maker Report

이번 개발 방향은 새 전략을 더 찾는 것이 아니다. 먼저 프로젝트가 스스로를 속이지 못하게 만드는 운영 장치를 박는 것이다.

필수가 총괄한다. 한 번에 여러 전략을 승격하려 하지 않고 `Task584 Runtime Strategy Decision Gate`를 첫 promotion target으로 잡는다. 각 팀장은 자기 영역의 반복 피드백을 하나의 실행 산출물로 닫는다: 성원은 runtime intraday state, 윤헌은 source closure, 동승은 scorecard, 중훈은 registry 압축, 서연은 blocker-first 보고, 종찬/규승은 evidence UI, Execution & Risk는 broker truth와 proxy PnL 분리다.

현재 결론은 여전히 `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`다. 다만 이제 무엇을 해야 하는지 흩어진 피드백이 아니라 추적 가능한 개발 보드와 검증 명령으로 바뀌었다. Task595 자체가 active governance/development task로 등록되어 active row는 기준선 102에서 103이 되었고, Wave 1의 목표는 이 신규 관리 row를 포함해 <=40으로 압축하는 것이다.

## Artifact Manifest

See `artifact_manifest.csv`.
