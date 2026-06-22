# Daily Feedback Team Summary - 2026-06-02

## Decision Summary

- objective: 지금까지 작성된 daily feedback과 Task589 EOD trading-team feedback을 팀별로 중복 없이 정리한다.
- source coverage:
  - `docs/reports/daily_feedback_2026-05-21/daily_feedback_2026-05-21.md`
  - `docs/reports/daily_feedback_2026-05-23/daily_feedback_2026-05-23.md`
  - `docs/reports/daily_feedback_2026-05-24/daily_feedback_2026-05-24.md`
  - `docs/reports/daily_feedback_2026-05-25/daily_feedback_2026-05-25.md`
  - `docs/reports/daily_feedback_2026-05-27/daily_feedback_2026-05-27.md`
  - `docs/reports/daily_feedback_2026-05-28/daily_feedback_2026-05-28.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-20.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-21.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-22.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-27.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-28.md`
  - `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-06-01.md`
- dedup rule: 날짜별로 반복된 같은 지시는 한 번만 남기고, 증거 수치나 freshness gap처럼 날짜에 따라 새로 추가된 내용만 별도 항목으로 보존한다.
- overall status: 대부분의 반복 피드백은 아직 닫히지 않았다. 핵심 미해결 축은 active lane compression, runtime regime/intraday capture, promotion scorecard, blocked-source scoreboard, stale EOD closeout이다.

## Team-by-Team Feedback

### Regime Research / Overall Strategy Lead - 필수

- Active lane이 계속 과다하다. 2026-05-23부터 2026-05-28까지 active rows 102개가 반복 확인됐고, single canonical promotion target으로 수렴했다는 증거가 없다.
- 운영 개선, Slack 안정화, 모바일 UI 개선을 전략 승격 진전처럼 소비하게 두면 안 된다. daily top line은 `active delta / blocked-source delta / scorecard delta / runtime capture delta` 중심이어야 한다.
- 승격 조건을 명시적으로 잠가야 한다. 최소 조건은 `runtime regime state`, `runtime intraday state`, `promotion scorecard`, `blocked-source delta`다.
- 다음 조치: active 전략 lane을 1개 canonical promotion target 중심으로 줄이고, 나머지 active 후보를 `parked` 또는 `stalled` 후보 표로 분리한다.

### Intraday Continuation Research - 성원

- Intraday 연구 산출물은 늘었지만 runtime DB에 남는 canonical state contract로 닫히지 않았다. 반복 지적의 핵심은 새 factor 부족이 아니라 decision-time state persistence 부재다.
- 다음 산출물 형식은 `state dictionary -> runtime column -> source_snapshot_id exact join key -> capture proof -> frontend exposure` 순서로 고정한다.
- daily 보고 지표는 새 후보 수가 아니라 runtime에 기록 가능한 intraday state 수와 캡처 증거여야 한다.
- 다음 조치: 도윤 역할 범위로 intraday state dictionary와 exact join key 표를 먼저 제출한다.

### Chart Evidence / Strategy Review Evidence - 종찬

- Chart surface와 paper trade review 화면은 개선됐지만, missing runtime fact를 blocker로 충분히 강하게 표현하지 못했다.
- trade detail evidence order는 `decision_id -> source_snapshot_id -> regime -> intraday -> order/fill lineage -> PnL`로 고정한다.
- `NOT_CAPTURED_IN_RUNTIME_DB`와 stale EOD는 중립 정보 문구가 아니라 blocker badge로 표시해야 한다.
- 다음 조치: blocker badge 규칙과 evidence order 고정안을 제출하고, 시각 polish보다 evidence completeness를 우선한다.

### Research Governance / Project Discipline - 중훈

- Active queue 과밀을 governance failure로 차단하지 못했다. Research Governance active 29개와 전체 active rows 102개가 반복 확인됐다.
- 지난 피드백의 액션이 registry 상태 변화로 이어졌는지 닫는 follow-up loop가 약하다.
- `active` 유지 기준에 `최근 blocker 변화`, `scorecard linkage`, `runtime capture linkage`를 넣어야 한다.
- 2026-05-28에 새로 강조된 문제: latest runtime run은 2026-05-27까지 갱신됐지만 Task589 EOD closeout은 2026-05-22에 머물렀다. daily feedback 전에 `latest runtime date == latest EOD session date` 검사를 추가해야 한다.
- 다음 조치: stalled/parked registry rule, follow-up checklist, stale EOD detection rule을 운영 규칙으로 추가한다.

### Slack Reporting - 서연

- 잘한 점은 명확하다. Slack delivery는 반복적으로 `SENT`였고, secret leakage guard도 개선됐다.
- 부족한 점은 보고 구조다. Slack 성공이 운영 성공처럼 보이면 안 되고, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`와 실거래 전환 금지 사유를 첫 줄에서 잠가야 한다.
- 모든 daily/EOD Slack 헤더는 `deployment blocker / runtime capture gap or freshness gap / next owner action` 3줄로 고정한다.
- 2026-05-28 이후에는 `latest runtime run > latest EOD session`이면 `STALE_EOD_CLOSEOUT`를 첫 줄에 강제 표시한다.
- 다음 조치: PnL, fills, Slack delivery는 하단 참고 섹션으로 내리고 blocker-first 템플릿을 고정한다.

### Backtest & Simulation Infra - 동승

- Replay, OOS, cost/slippage 근거는 쌓였지만 promotion-ready 판단면을 한 장으로 압축하지 못했다.
- 반복 요구된 산출물은 `split/OOS/cost/slippage/concentration/runtime-capture/broker-truth` PASS/FAIL matrix다.
- 각 PASS/FAIL에는 source path와 마지막 검증 날짜를 붙여야 한다.
- 다음 조치: 새 분석보다 promotion scorecard 통합표 1장을 먼저 제출한다.

### Data & Market Microstructure - 윤헌

- Runtime source plumbing은 개선됐지만 blocked-source 감축이 KPI로 운영되지 않았다. 전체 blocked-source 30개, Data & Market Microstructure active 중 blocked-source 비중이 반복 지적됐다.
- 필요한 scoreboard 컬럼은 `missing source / owner / last move date / unblock condition`이다.
- Task590 계열은 partial runtime observability를 개선했지만 firm-grade source closure는 아니다. regime/intraday runtime persistence에 필요한 저장 컬럼과 source lineage를 성원/규승과 공동 명세로 잠가야 한다.
- Task589 technical feedback 기준으로 indicator/source-price evidence는 timestamp, freshness, decision snapshot alignment, `source_price_ts`가 빠지면 promotion blocker다.
- 다음 조치: blocked-source scoreboard와 runtime tables missing-field/live-grade source gap 표를 제출한다.

### Frontend/UI - 규승

- iPhone-first paper UI, provenance visibility, trade detail 흐름은 실제로 개선됐다.
- 부족한 점은 blocker visibility다. product polish가 `diagnostic-only`, `proxy PnL`, `missing runtime capture`, stale EOD보다 앞서 보이면 안 된다.
- 최신 우선순위는 `stale EOD -> diagnostic-only -> missing runtime capture -> proxy PnL` 상단 경고 체계다.
- Frontend는 catalog-only contract를 유지하되, blocker badge와 lineage visibility를 polish보다 먼저 배치해야 한다.
- 다음 조치: 종찬과 함께 blocker badge 및 lineage visibility를 mobile polish보다 먼저 반영한다.

### Execution & Risk / PM-CIO Review

- Broker-truth fill count가 canonical execution source다. live readiness claim 전에는 event/order/fill reconciliation이 보여야 한다.
- Open-position PnL은 proxy이며 realized PnL과 섞어 deployment decision에 쓰면 안 된다. 다음 세션 전 open exposure, max symbol concentration, stop policy, kill-switch state를 확인해야 한다.
- Task589 EOD report는 operational review artifact일 뿐 real-capital deployment approval이 아니다.
- Runtime decisions는 evidence only다. label, future outcome, AI-generated judgement가 order signal로 들어가면 안 된다.
- 다음 조치: live switch 전 `split/OOS evidence`, `cost/slippage validation`, `reconciliation`, `live-source readiness`를 모두 요구한다.

## Cross-Team Operating Order

Daily review 순서는 다음으로 고정한다.

1. active rows delta
2. blocked-source delta
3. runtime regime/intraday capture delta
4. promotion scorecard delta
5. fresh runtime date vs latest EOD session date
6. 마지막에만 PnL, fills, Slack delivery

## No-Background Decision-Maker Report

- 좋아진 것: Slack 안전성, 모바일 관측성, runtime DB 기반 UI 정합성, 일부 운영 접근성.
- 그대로 남은 것: active lane 102개, blocked-source 30개, runtime regime/intraday state 미캡처, promotion scorecard 부재, blocked-source scoreboard 부재.
- 새로 추가된 핵심 리스크: runtime loop는 갱신됐는데 EOD closeout이 stale인 상태가 발생했다.
- 결론: 현재 상태는 계속 `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`다. 다음 성공 기준은 새 기능이 아니라 lane 축소, runtime state capture, scorecard/scoreboard 제출, fresh runtime와 fresh EOD의 날짜 일치다.

## Artifact Manifest

See `artifact_manifest.csv`.
