# Daily Feedback 2026-05-27

*Deployment blocker*: active rows `102`, blocked-source `30`, strategy acceptance still `diagnostic-only 63 / not-applicable 39`.

*Runtime capture gap*: Task590 and Task594 still require persisted runtime `regime` and `intraday` state; latest Task588 loop evidence remains repeated `ORDER_SKIPPED`; latest Task589 EOD summary is still `session_date_et=2026-05-22`, `deployment_ready_flag=0`, `diagnostic_only_flag=1`.

*Who missed what*:
- 필수: active lane 축소와 단일 promotion target 고정을 아직 운영 규칙으로 못 만들었다.
- 성원: intraday 연구를 runtime state contract로 닫지 못했다.
- 종찬: missing runtime fact를 blocker badge로 강하게 표현하지 못했다.
- 중훈: active queue 과밀을 governance failure로 끊지 못했다.
- 동승: promotion scorecard를 한 장으로 못 닫았다.
- 윤헌: blocked-source scoreboard를 아직 운영 KPI로 만들지 못했다.
- 서연: Slack 안전성은 좋지만 blocker-first 보고 형식은 더 날카롭게 고정해야 한다.
- 규승: UI는 좋아졌지만 blocker visibility가 polish보다 앞서야 한다.

*Next owner actions*:
- 필수: active strategy lane 1개로 축소안 제출
- 성원: `state dictionary -> runtime column -> source_snapshot_id join` 표 제출
- 종찬: `NOT_CAPTURED_IN_RUNTIME_DB` blocker badge/evidence order 확정
- 중훈: stalled/parked rule + follow-up checklist 도입
- 동승: `split/OOS/cost/slippage/concentration/runtime-capture/broker-truth` PASS/FAIL matrix 제출
- 윤헌: `missing source / owner / last move date / unblock condition` scoreboard 제출
- 서연: daily/EOD Slack 헤더를 blocker-first 3줄로 고정
- 규승: `diagnostic-only / proxy PnL / missing runtime capture` 상단 경고 계층 반영

상세 근거: `docs/reports/daily_feedback_2026-05-27/daily_feedback_2026-05-27.md`
