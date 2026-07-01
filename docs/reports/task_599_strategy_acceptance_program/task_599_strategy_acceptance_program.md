# Task599 - Strategy Acceptance Program

## Decision Summary

- Verdict: `PRIMARY_PASS` for program definition.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Target status: `ACCEPTANCE_REVIEW`.
- Paper operation status: `READY_FOR_CONTROLLED_PAPER_RUN`.
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital status: `FORBIDDEN`.
- Objective: convert the paper-trading project from an operational diagnostic state into a governed strategy acceptance program with explicit blockers, owners, artifacts, validation commands, and promotion gates.
- What changed: readiness is now controlled by `docs/ownership/readiness_registry.yaml`, strategy and deployment contracts are split under `docs/acceptance/`, and `python validate_readiness_registry.py` validates the program blocker schema.
- Next action: execute P0 work in order: Exit Lifecycle, Candidate Funnel, Exact Replay. New alpha experiments remain forbidden until P0 is complete.

## Quant Expert Report

### Program Read

The project currently supports controlled paper operation, but it has not earned strategy acceptance. The observed paper window contains 24 broker-truth fills, all BUY, with 0 SELL fills. Therefore realized closed-trade performance, exit behavior, win rate, hold-time behavior, stop behavior, and payoff quality cannot be evaluated.

Task599 does not create a new strategy claim. It creates the gate structure required before strategy acceptance review can begin.

### Current Status

| Surface | Status |
|---|---|
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |
| Strategy acceptance | `NOT_ACCEPTED` |
| Target gate | `ACCEPTANCE_REVIEW` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Real capital | `FORBIDDEN` |

### Priority Order

| Priority | Workstream | Owner | Required Gate |
|---|---|---|---|
| P0 | Exit Lifecycle | 주은 | SELL fills, realized PnL, exit distribution, and lifecycle evidence |
| P0 | Candidate Funnel | 성원 | ranked, explainable, non-duplicative candidate funnel |
| P0 | Exact Replay | 동승 | 99%+ match for decisions, orders, fills, and positions |
| P1 | Source Health Ledger | 윤헌 | 20 sessions with source quality thresholds |
| P1 | Readiness Dashboard | 규승 | five-second status diagnosis without CSVs |
| P2 | Governance Enforcement | 중훈 | closeout cannot pass with stale operating state |
| P2 | Exact-ID Review Packet | 종찬 | 100% fill review packets and top skipped candidate packets |
| P2 | Slack Policy Lock | 서연 | Slack sends only allowed state-changing messages |
| P2 | Deployment Gate Separation | 필수 | deployment claims remain blocked until deployment gates pass |

### Required Program Tables

| Table | Owner | Required Columns |
|---|---|---|
| `source_health_ledger` | 윤헌 | `session_id`, `session_date`, `provider`, `universe_count`, `fresh_count`, `stale_count`, `provider_error_count`, `avg_quote_age_ms`, `max_quote_age_ms`, `exchange_fallback_count`, `status` |
| `candidate_funnel_events` | 성원 | `candidate_id`, `symbol`, `generated_time`, `rank_score`, `cooldown_reason`, `eligibility_status`, `skip_reason`, `order_id`, `fill_id` |
| `position_lifecycle` | 주은 | `position_id`, `entry_order_id`, `exit_order_id`, `entry_reason`, `exit_reason`, `holding_minutes`, `realized_pnl`, `exit_type` |
| `replay_diff` | 동승 | `decision_id`, `runtime_value`, `replay_value`, `diff_reason` |
| `readiness_registry.yaml` | 필수 / 중훈 | blocker ID, owner, artifact, validation, next gate, status |

### Acceptance Review Entry Conditions

Strategy acceptance review cannot begin until all conditions pass:

- SELL fills exist.
- 100+ realized closed trades exist.
- decision, order, fill, and position replay match rates are each at least 99%.
- source health is validated for 20 trading sessions.
- candidate funnel is audited.
- kill switch is tested.
- exact-id review packet coverage is 100% for fills and top skipped candidates.

If any condition is missing, status remains `NOT_ACCEPTED`.

### Data Integrity Gate

- Inferred lifecycle matching allowed: no.
- Symbol/date/price/time proximity fallback allowed: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Proxy PnL usable as realized PnL: no.
- Slack/frontend/Graphify success usable as strategy acceptance: no.

### Forbidden Claims

Until SELL lifecycle and realized closed-trade evidence pass, these claims are forbidden:

- strategy validated
- profitable strategy
- deployment ready
- production ready

## No-Background Decision-Maker Report

필수에게 보고합니다.

이번 작업의 목적은 새 전략을 찾는 것이 아니라, 전략 합격 심사를 시작하기 위한 운영 프로그램을 만드는 것입니다.

현재 시스템은 모의매매를 돌릴 수 있습니다. 하지만 체결 24건이 전부 매수이고 매도가 0건이므로, 아직 전략이 돈을 벌 수 있는지 평가할 수 없습니다. 실현손익, 승률, 손절, 익절, 보유기간, exit 품질이 모두 검증되지 않았습니다.

따라서 현재 상태는 그대로 `NOT_ACCEPTED`입니다. 다음 목표는 바로 전략 합격이 아니라 `ACCEPTANCE_REVIEW`로 올라갈 수 있는 증거를 만드는 것입니다.

팀별 첫 순서는 고정입니다. 주은이 exit lifecycle을 먼저 닫고, 성원이 candidate funnel을 정리하고, 동승이 exact replay를 완성합니다. 이 P0가 끝나기 전에는 새 알파 실험을 하지 않습니다.

## Artifact Manifest

See `artifact_manifest.csv`.
