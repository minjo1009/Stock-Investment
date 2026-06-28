# Current Operating Model

Last updated: 2026-06-03

## Decision

This is the current canonical operating model for paper-trading governance and strategy acceptance program control. Use this file before older task reports, Graphify context packs, or chat-only instructions.

Current standing source:

| Layer | Canonical Source |
|---|---|
| Strategy acceptance program | `docs/reports/task_599_strategy_acceptance_program/` |
| Readiness registry | `docs/ownership/readiness_registry.yaml` |
| Strategy acceptance contract | `docs/acceptance/strategy_acceptance_contract.md` |
| Deployment acceptance contract | `docs/acceptance/deployment_acceptance_contract.md` |
| Paper week diagnosis | `docs/reports/task_598_paper_week_feedback_operating_plan/` |
| Immediate remediation board | `docs/reports/task_597_frontend_backend_paper_ops_triage/owner_remediation_plan.csv` |
| Prior integrated development plan | `docs/reports/task_595_feedback_integrated_development_plan/` |
| Named lead roster | `docs/ownership/team_charter.md` |
| Detailed asset map | `docs/ownership/module_ownership_map.md` |
| Work closeout protocol | `docs/operating_system/work_closeout_protocol.md` |
| Registry state | `tasks/task_registry.csv` |

Task599 is the current strategy acceptance program. Task598 remains the current paper-week diagnosis. Task595 and Task596 remain historical artifacts and should not be used as the current execution board when Task598 or Task599 conflicts with them.

## Current Status

| Area | Status |
|---|---|
| Strategy acceptance | `NOT_ACCEPTED` |
| Strategy target gate | `ACCEPTANCE_REVIEW` |
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Main blocker | T600-4 confirms broker_truth_sell_fills remains 0; runtime synthetic SELL rows are not broker truth |
| P0 blockers | Broker Truth Exit Lifecycle, Exact Replay full 99% review |
| P1 blockers | Source Health Ledger, Readiness Dashboard |
| P2 blockers | Governance Enforcement, Exact-ID Review Packet, Slack Policy Lock, Deployment Gate Separation |

## Named Leads

| Lead | Team | Current Operating Responsibility | Current Gate |
|---|---|---|---|
| 필수 | General Coordination / Regime Research | Keep controlled paper readiness separate from strategy and deployment acceptance | Strategy acceptance gate |
| 윤헌 | Data & Market Microstructure | Session source-health ledger and source gap closure | Data readiness gate |
| 성원 | Intraday Continuation Research | Candidate funnel repair, cooldown, duplicate suppression, runtime intraday state | Candidate quality gate |
| 주은 | Execution & Risk | Exit/trim/stop lifecycle, exposure limits, broker-truth risk reporting | Execution truth and risk exposure gates |
| 동승 | Backtest & Simulation Infra | Exact paper-to-replay acceptance and cost/slippage evidence | Replay acceptance gate |
| 규승 | Frontend/UI | Week-feedback dashboard and blocker visibility | Human review gate |
| 서연 | Slack/EOD | Filled-only Slack policy and blocker-first EOD reporting | Slack noise gate |
| 중훈 | Research Governance | Registry-backed blocker backlog, artifact manifest, active lane discipline | Governance continuity gate |
| 종찬 | Chart Evidence | Exact-id chart/snapshot review packets for fills and top skipped candidates | Human evidence gate |

## Operating Rules

- Do not use Slack success, UI polish, or EOD delivery as strategy acceptance.
- Do not use proxy PnL as realized PnL.
- Do not promote controlled paper runtime SELL rows as broker-truth or real-capital evidence.
- Do not use symbol/date/price/time proximity to connect decisions, orders, fills, or charts.
- Do not treat missing labels or missing runtime facts as negatives.
- Do not use stale Graphify outputs as current project state.
- Every blocker must have an owner, artifact path, validation command, status, and next gate.
- Every non-trivial work item must close with `docs/operating_system/work_closeout_protocol.md`.
- Every readiness change must update `docs/ownership/readiness_registry.yaml`.
- New alpha experiments are forbidden until P0 blockers pass.

## Today-Executable Contract Status

| Task | Area | Status | Artifact | Next Implementation |
|---|---|---|---|---|
| T600-4 | Broker Truth Exit Lifecycle | `BROKER_TRUTH_SELL_ZERO_ACCEPTANCE_BLOCKED` | `docs/reports/task_600_4_broker_truth_exit_lifecycle/broker_truth_exit_report.md` | Create or ingest actual paper broker/order-status SELL fills and rerun exact reconciliation |
| T602-4 | Order Replay Recovery | `ORDER_REPLAY_STRETCH_1_0_POSITION_95_8333` | `docs/reports/task_602_4_order_replay_recovery/order_replay_acceptance_report.md` | Order layer is recovered; full replay review still depends on broker-truth exit lineage and remaining position gap |
| T600-5 | STOP/TP Validation | `FAIL_STOP_TP_ZERO_SOURCE_BLOCKED` | `docs/reports/task_600_5_stop_tp_validation/stop_tp_validation.md` | Capture fresh ATR-at-entry runtime source evidence and rerun STOP/TP validation |
| T601-4 | Concentration Stability | `CONCENTRATION_STABILITY_PASS_TOP3_0_75` | `docs/reports/task_601_4_concentration_stability/concentration_stability_report.md` | Keep sector concentration source-blocked until real sector evidence exists |
| T603-1 | Registry Consumption | `REGISTRY_PAYLOAD_IMPLEMENTED` | `docs/reports/task_603_1_registry_backed_readiness_consumption/` | Keep catalog/frontend data reading canonical readiness payload |

## Graphify Status

Graphify outputs in this repository were last generated on 2026-04-25 and are stale for current paper-ops governance. They may be used only as historical architecture discovery aids.

Current paper-ops and acceptance-program decisions must come from Task599, Task598, Task597, Task589, Task590, Task591, `docs/ownership/readiness_registry.yaml`, and `tasks/task_registry.csv`.

Regenerate Graphify before using it for any claim about Task584, Task589, Task590, Task595, Task596, Task597, Task598, or Task599.

## Cleanup Decisions

| Item | Decision | Reason |
|---|---|---|
| Task595 board | Keep as historical | It records the first integrated development plan but is superseded by Task598 for current paper-week diagnosis. |
| Task596 board | Keep as historical | It records completion of daily feedback application but is not the latest diagnostic board. |
| Task597 remediation plan | Keep as current supporting board | It has owner-level remediation rows and confirms controlled paper readiness versus deployment blocker separation. |
| Task598 operating plan | Canonical current board | It is the latest paper-week diagnosis and team operating plan. |
| Task599 strategy acceptance program | Canonical current acceptance program | It defines the required gates for `NOT_ACCEPTED` to `ACCEPTANCE_REVIEW`. |
| Graphify generated cache | Remove when stale | Generated cache can make old April context look authoritative and is safe to regenerate. |
| Graphify audit reports | Keep as historical | They document how Graphify was produced and why stale outputs must be treated carefully. |

## Next Governance Action

필수 should use the T600-4, T602-4, T600-5, and T601-4 artifacts as the current acceptance implementation packet. Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN` until actual broker-truth SELL fills, full replay review, source-health, and review-packet gates are separately accepted.
