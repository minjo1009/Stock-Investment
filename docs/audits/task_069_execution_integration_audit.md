# Task 069 — Execution Integration Audit (Phase 2)

## 1. Overall Verdict

- 상태: **NOT_READY**
- 실거래 가능 여부: **CONDITIONAL (현재 기준은 사실상 NO)**

근거 요약:
1. 주문은 실제 API로 나가지만, 실행 상태기계/복구/리스크 통제가 “실계좌 운영 수준”으로 닫혀 있지 않음.
2. 연구 엔진(`engine_full`)과 실주문 경로(`run_trade_once`)가 분리되어, 백테스트-실행 정합성이 구조적으로 약함.
3. 모니터링 UI는 존재하지만 운영 의사결정(킬스위치/장애복구/미체결 처리)을 완결적으로 지원하지 않음.

---

## 2. Execution Readiness Score

| Category | Score (0~10) |
|---|---:|
| Order Execution | 5 |
| State Management | 6 |
| Risk Control | 3 |
| Data Reliability | 4 |
| Monitoring | 6 |

---

## 3. 4인 전문가 관점 평가

### A) Execution Trader 관점

1. 실제 주문 발생 위치:
   - `src/app/run_trade_once.py`에서 `kis.submit_order(...)` 호출로 직접 주문 전송(약 284행).
2. 주문 타입:
   - KIS payload의 `ORD_DVSN` 기본값 `"00"` 사용, 사실상 지정가 경로 중심(`src/integration/kis_client.py`).
3. fill 판단:
   - `kis.get_order_status(order_id)` polling + 보조로 `get_position_quantity` 델타 fallback(`run_trade_once.py` 303~311행).
4. 미체결 처리:
   - 10회 polling 후 `TIMEOUT` 상태로 종료, 자동 `cancel` 호출 없음(377~388행).
5. 슬리피지/지연:
   - 백테스트는 슬리피지/비용 반영, 실주문 경로는 체결가를 브로커 fill로 확정하지 않고 요청가(`price`) 기반 기록.

판정:
- **실제 주문은 가능**하나, **체결 실패/지연/부분체결/취소 시나리오 대응은 불충분**.

### B) Backend Architect 관점

1. Order lifecycle:
   - 저장소 상태는 `SUBMITTED/PENDING/FILLED/TIMEOUT/FAILED/REJECTED` (`state/store.py`).
   - 그러나 `CANCELLED`가 `ALLOWED_ORDER_STATUS`에 없음(29행), 반면 reconciliation은 CANCELLED를 다룸(`app/reconciliation.py`).
2. 상태 저장:
   - sqlite에 `trade_runs/orders/fills/positions/position_events/reconciliation_*` 테이블 존재(`initialize_store`).
3. 재시작 복구:
   - DB 기반 조회(`list_open_orders`, `list_positions`)는 있으나, “미완료 주문 재구독/재동기화 루프”는 제한적.
4. Idempotency:
   - `intent_key` 기반 중복 차단 + recent window 차단 존재(`has_blocking_order_intent`, `has_recent_order_intent`).

판정:
- **기초 persistence/idempotency는 양호**하지만, **운영 상태기계 일관성(CANCELLED 부재, late-fill 처리 흐름)**이 미완성.

### C) Portfolio / Risk 관점

1. 동시 포지션/자본배분:
   - 실주문 경로가 사실상 단일 심볼/고정 수량(`AAPL`, qty=1) 중심(`run_trade_once.py` 202~204행).
2. 포트폴리오 risk:
   - exposure cap, portfolio DD guard, 계좌별 alloc 엔진이 실주문 경로에 없음.
3. 리스크 실행:
   - 연구용 `risk.policies`는 백테스트 엔진에서 동작하나 실주문 루프에 통합되지 않음.

판정:
- **트레이드 단위 데모는 가능**, **포트폴리오 운용 시스템은 아님**.

### D) Data / Reality 관점

1. 백테스트 vs 실실행 정합성:
   - `engine_full` 실행모델(정책/비용/리스크)과 `run_trade_once` 실주문 로직이 별도 코드 경로.
2. 시그널 타이밍 vs fill 타이밍:
   - 실주문은 즉시 현재가 기반 limit 제출 + polling 결과 반영, 백테스트의 bar 기반 fill 모델과 직접 매핑이 약함.
3. latency/API delay:
   - polling(최대 10초) 수준 외에 네트워크/거래소 지연 모델 관리가 제한적.
4. freshness:
   - UI/모델에 freshness 개념은 있으나, 실주문 직전 데이터 신선도 게이트는 강하지 않음.

판정:
- **연구 결과를 실실행으로 신뢰 이전하기엔 데이터-실행 정합성 갭이 큼**.

### E) Frontend / Monitoring 관점

1. UI에 운영 탭 존재:
   - Overview / Orders-Fills / Positions / Reconciliation / Trade Detail / Portfolio Overview.
2. 상태 가시성:
   - 테이블 부재/빈 데이터 사유 표시, 주문/체결/포지션/recon 조회 가능.
3. 한계:
   - kill-switch/control-state 직접 제어/시각화, 알람 우선순위 큐, 장애 대응 플레이북 UI는 미흡.

판정:
- **읽기 중심 모니터링은 가능**하나, **운영 제어형 콘솔로는 미완성**.

---

## 4. Critical Gaps (Top 7)

1. 실주문 경로가 연구용 execution/risk 레이어와 분리
   - 영향: 백테스트 성능과 실거래 결과 괴리 확대
   - 실제 돈 기준 리스크: 전략 edge가 실거래에서 재현되지 않을 수 있음

2. 미체결/타임아웃 후 cancel 미보장
   - 영향: 브로커 측 잔존 주문 가능성
   - 실제 돈 기준 리스크: 의도치 않은 체결/노출 발생

3. 상태기계 불일치 (`CANCELLED` 저장 상태 부재 vs reconciliation 사용)
   - 영향: 상태 동기화/정합성 판단 혼선
   - 실제 돈 기준 리스크: 복구 로직 오판, 운영자 판단 오류

4. 부분체결/다중 fill 실거래 처리 취약
   - 영향: fill 집계/포지션 평균단가 정확도 저하 가능
   - 실제 돈 기준 리스크: 손익/노출 계산 왜곡

5. 포트폴리오 리스크 통제 부재
   - 영향: 동시 포지션/자본배분/총노출 관리 불가
   - 실제 돈 기준 리스크: 단일 이벤트에서 손실 집중

6. 재시작 후 in-flight 주문 회복 시나리오 미완결
   - 영향: 프로세스 장애 시 주문 상태 누락 가능
   - 실제 돈 기준 리스크: 중복 주문 또는 미청산 상태 방치

7. 데이터/체결 진실원 단일화 미흡
   - 영향: 요청가/추정 체결가/실제 체결가가 혼재
   - 실제 돈 기준 리스크: 성과 분석 착시(거짓 신뢰)

---

## 5. False Confidence Risks

1. 백테스트에서는 체결/비용 모델이 명시적이라 좋아 보이지만, 실주문은 timeout/cancel/partial-fill 처리 차이로 성과가 붕괴될 수 있음.
2. `POSITION_DELTA_FALLBACK` 기반 fill 확정은 편의적이고, 브로커 체결 이벤트와 불일치 시 잘못된 fill truth를 만들 수 있음.
3. 단일 golden(S4) 통과는 연구 성과 안정성만 보장하며, 실주문 운영 안전성(상태복구/장애내성)은 별개 문제다.
4. UI가 데이터 없음/테이블 없음을 잘 보여도, 이것이 운영 통제 가능성을 의미하지는 않는다.

---

## 6. Minimal Requirements for Pilot

1. 주문 상태기계 통일
   - `CREATED/PENDING/PARTIAL/FILLED/CANCELLED/EXPIRED/FAILED`를 DB/코드/리컨실리 모두 동일 계약으로 통합
2. timeout 후 브로커 cancel 및 재확인 의무화
   - “TIMEOUT=종료”가 아니라 “취소 확인 완료”까지 한 트랜잭션으로 처리
3. in-flight 주문 복구 루프
   - 재시작 시 브로커 truth pull → 로컬 reconcile → 잔존 주문 정리 자동화
4. partial fill 표준 처리
   - 누적 체결량/평균가/잔량 기반 포지션 반영 + 이벤트 원장화
5. 포트폴리오 레벨 가드
   - max gross exposure, symbol cap, daily loss cap, kill-switch 자동 조건
6. 체결 truth 고정
   - 요청가가 아닌 브로커 체결 데이터(시간/가격/수량) 기반 PnL 및 리뷰

---

## 7. Immediate Next Actions (우선순위)

1. Execution State Contract 정합성 감사
   - 왜 필요한지: DB/리컨실리/실주문 상태 언어를 통일해야 복구 가능
   - 영향: 장애 시 오판/중복주문 리스크 즉시 감소

2. Timeout-Cancel-Reconcile 운영 시나리오 정의
   - 왜 필요한지: 실거래에서 가장 흔한 실패 케이스를 닫아야 함
   - 영향: 잔존 주문/유령 포지션 리스크 감소

3. Pilot용 포트폴리오 리스크 게이트 추가 설계(문서 레벨)
   - 왜 필요한지: 단일 주문 성공과 포트폴리오 안전은 별개
   - 영향: 손실 집중 방지, 운영 기준 명확화

4. Broker fill truth 기반 기록 경로 점검
   - 왜 필요한지: 분석/리뷰/운영 모두 동일 진실원을 써야 함
   - 영향: 성과 해석 신뢰도 상승

5. 운영 모니터링 플레이북 정의(UI + 알람 + 수동 개입 절차)
   - 왜 필요한지: 운영자는 “보는 것”뿐 아니라 “조치” 가능해야 함
   - 영향: 실시간 사고 대응력 개선

---

## 8. Final Decision

**이 시스템은 실제 돈을 넣을 수 있는 상태인가?**

**NO (현재 기준)**  

사유:
1. 주문 전송 자체는 가능하나, 미체결/취소/부분체결/복구를 포함한 실행 안전성 계약이 미완성.
2. 연구용 엔진과 실주문 경로의 정합성이 충분히 잠기지 않아, “백테스트 성과=실거래 성과” 가정이 성립하지 않음.
3. 포트폴리오 리스크 제어와 운영 제어(킬스위치/복구/모니터링)의 폐루프가 완성되지 않음.

결론:
- 실계좌 파일럿은 “조건부 소액 테스트” 수준으로만 가능하며,
- 그 이전에 Execution 통합 감사 후속(상태기계 통일 + timeout/cancel/reconcile 폐루프)이 선행되어야 함.

