# Cancel / Reconcile Loop Contract

## 1. Problem Definition

실시장에서는 아래 케이스가 실제 손실로 직결된다.

1. timeout 후 fill 발생  
   - 사고: 로컬은 주문 종료로 판단했지만 브로커는 체결 완료
   - 리스크: 의도치 않은 포지션 보유, 중복 주문으로 노출 증가

2. cancel 요청 후 fill 발생 (race condition)  
   - 사고: 취소 중 체결이 확정되는데 로컬이 취소로 잠금
   - 리스크: 포지션/손익 불일치, 헤지 실패

3. partial fill 후 cancel 실패  
   - 사고: 잔량 주문이 시장에 남아 유령 주문화
   - 리스크: 추가 체결로 노출 확대

4. API 장애로 상태 미확정  
   - 사고: submit/cancel 결과를 모른 채 다음 액션 수행
   - 리스크: 상태 분기 오류, 재시도 중복 주문

5. 프로그램 재시작 시 in-flight 주문 존재  
   - 사고: 프로세스 메모리 상태 소실, 로컬 DB와 브로커 상태 어긋남
   - 리스크: 복구 실패 시 실제 주문 통제 상실

---

## 2. Current Behavior Audit

### 현재 코드 기준 흐름
- timeout 발생 시 행동: `orders.status=TIMEOUT` 저장 후 예외 발생 (`run_trade_once.py`)
- cancel 호출 여부: 없음 (timeout 이후 broker cancel API 호출 없음)
- cancel confirmation 여부: 없음
- reconcile 타이밍: 주문 전 1회 수행, timeout 이후 재진입 루프 없음
- in-flight 주문 처리: `list_open_orders` 조회/출력은 있으나 자동 복구 루프 없음

### 핵심 문제
1. `TIMEOUT`이 종료처럼 취급된다.
2. cancel-confirm-reconcile 폐루프가 없다.
3. broker truth를 최종 확정할 후속 단계가 부족하다.
4. 재시작 시 active order 복원 절차가 명시적으로 계약화되어 있지 않다.

---

## 3. Canonical Cancel Loop

정상 cancel 폐루프:

`PENDING`  
→ `TIMEOUT_DETECTED` (event)  
→ `CANCEL_REQUESTED`  
→ broker cancel request  
→ broker status verify  
→ `CANCELLED` or `FILLED`

중요 원칙:
- Cancel은 단발 이벤트가 아니라 반복 프로세스다.
- terminal(`CANCELLED/FILLED/REJECTED/EXPIRED`)이 확정될 때까지 루프를 유지한다.

루프 의사규칙:

```text
while state not in TERMINAL:
    poll broker truth
    if pending/partial and cancel not confirmed:
        send or retry cancel request
    reconcile local vs broker
    persist state + audit event
```

---

## 4. Cancel Loop State Machine

| State | 진입 조건 | 유지 조건 | 다음 상태 | Required Action |
|---|---|---|---|---|
| `PENDING` | open/working 주문 확인 | fill/cancel 미확정 | `CANCEL_REQUESTED`, `FILLED`, `PARTIAL`, `UNKNOWN` | broker poll |
| `TIMEOUT_DETECTED` (event) | SLA 초과 | 이벤트성(상태 아님) | `CANCEL_REQUESTED` | cancel 루프 시작 |
| `CANCEL_REQUESTED` | cancel API 요청 보냄 | confirm 미수신 | `CANCEL_IN_PROGRESS`, `FILLED`, `UNKNOWN` | 요청 기록 |
| `CANCEL_IN_PROGRESS` | cancel 전송 후 대기 | broker 응답 대기 | `CANCELLED`, `FILLED`, `PARTIAL`, `UNKNOWN` | poll + backoff |
| `CANCELLED` | broker cancel 확정 | terminal | (none) | 종료/감사로그 |
| `FILLED` | broker fill 확정 | terminal | (none, late fill correction 제외) | fill 반영 |
| `UNKNOWN` | 응답 모순/미확정 | reconcile 필요 | `PENDING/FILLED/CANCELLED/FAILED` | trading halt + 수동개입/강화된 reconcile |

---

## 5. Retry / Backoff Policy

권장 정책:
- retry interval: 2초 시작
- max attempts: 30
- backoff: 지수 백오프(2, 2, 4, 4, 8... 최대 10초 캡)
- hard stop: 60초 또는 30회 초과 시 `UNKNOWN` 승격 + 신규 주문 차단 + 알림

---

## 6. Conflict Scenarios

1. cancel 요청 후 fill 발생  
   - 최종 상태: `FILLED`
   - 액션: cancel 결과 무시, fill truth 우선 반영, 주문 종료
   - 포지션: 체결수량 기준 반영
   - 로그: `CANCEL_RACE_FILLED`

2. partial fill 후 cancel  
   - 최종 상태: `CANCELLED` 또는 `FILLED`
   - 액션: 누적 fill + 잔량 cancel 확인
   - 포지션: partial 누적 반영
   - 로그: `PARTIAL_THEN_CANCEL`

3. cancel 실패 후 재요청  
   - 최종 상태: `CANCEL_IN_PROGRESS` 유지
   - 액션: backoff 후 retry, 임계 초과 시 `UNKNOWN`
   - 포지션: 변경 없음
   - 로그: `CANCEL_RETRY`

4. timeout 후 실제로는 filled  
   - 최종 상태: `FILLED`
   - 액션: timeout reason은 보존하되 state는 fill로 교정
   - 포지션: fill 반영
   - 로그: `TIMEOUT_BUT_FILLED`

5. broker API inconsistent response  
   - 최종 상태: `UNKNOWN`
   - 액션: 신규 주문 차단, 강제 reconcile 루프, 운영자 알림
   - 포지션: broker snapshot 재조회 전 잠정 동결
   - 로그: `BROKER_INCONSISTENT`

---

## 7. Reconciliation Loop

cancel 이후 필수 순서:

1. broker 상태 pull  
2. local 상태 비교  
3. mismatch 탐지  
4. correction 적용  
5. 이벤트 로그 저장  
6. 상태 업데이트  

의사규칙:

```text
reconcile():
  broker = fetch_broker_truth()
  local = fetch_local_state()
  diff = detect_mismatch(broker, local)
  if diff:
      apply_correction(diff)
      log_recon_event(diff)
  return resolved_state
```

---

## 8. In-flight Order Recovery

프로세스 재시작 시 필수 절차:
1. broker open orders 전체 조회
2. local open orders 조회
3. 매칭/불일치 분류
4. in-flight 주문을 `PENDING/CANCEL_IN_PROGRESS/UNKNOWN`으로 복원
5. terminal 확정 전까지 신규 주문 금지

필수 규칙:
- `UNKNOWN` 1건이라도 존재하면 `TRADING_HALT`.

---

## 9. Late Fill Handling

정의:
- `CANCELLED` 이후 fill 수신은 `LATE_FILL`로 취급 가능.

처리:
1. position update (실제 체결 기준)
2. pnl correction
3. audit log (`LATE_FILL_APPLIED`)
4. reconciliation 상태 재평가

---

## 10. Safety Guards

필수 가드:
1. `UNKNOWN` 존재 시 trading halt
2. ACTIVE 주문 수 상한
3. cancel loop 실패/임계초과 시 alert
4. reconciliation `CRITICAL` mismatch 시 block new orders

---

## 11. UI / Operator Contract

| 상태/상황 | Operator 행동 |
|---|---|
| `PENDING` 단기 | 대기/모니터링 |
| `TIMEOUT_DETECTED` | cancel 루프 즉시 시작 |
| `CANCEL_REQUESTED` 장기 지속 | 재요청 상태 확인, backoff 정책 점검 |
| `UNKNOWN` | 신규 주문 중단, 수동 reconcile 실행 |
| `MISMATCH(CRITICAL)` | trading halt 유지, broker truth 우선 정정 |

---

## 12. Invariants

1. cancel은 confirm될 때까지 반복한다.
2. broker truth > local state.
3. terminal 상태 확정은 broker 기준으로만 한다.
4. `UNKNOWN`은 거래 금지 상태다.
5. `FILLED`는 최소 1개 fill record를 가진다.
6. `CANCELLED` 이후 fill은 `LATE_FILL` 경로로만 허용한다.

---

## 13. Failure Modes

1. cancel loop stuck  
   - fallback: `UNKNOWN` 승격 + trading halt + 알림
   - 개입: 운영자 필수

2. API failure  
   - fallback: retry/backoff, 임계 초과 시 `FAILED/UNKNOWN`
   - 개입: 상황에 따라 필요

3. broker outage  
   - fallback: 신규 주문 중단, 상태 freeze, 주기적 health check
   - 개입: 운영자 필수

4. inconsistent state  
   - fallback: reconcile correction 우선, 미해결 시 `UNKNOWN`
   - 개입: 운영자 필수

---

## 14. Implementation Plan (Next)

1. cancel loop 구현 (`TIMEOUT_DETECTED -> CANCEL_REQUESTED -> confirm`)
2. retry/backoff 정책 반영
3. reconcile 루프를 주문 후/타임아웃 후로 확장
4. late fill correction 경로 추가
5. 테스트 추가:
   - timeout->cancel->cancelled
   - cancel race filled
   - restart in-flight recovery
   - unknown blocks new orders

---

## Evaluation Standard Answers

1. cancel 요청이 실패하면 어떻게 되는가?  
   - retry/backoff 반복 후 임계 초과 시 `UNKNOWN` + trading halt.

2. cancel 중 fill이 발생하면 어떻게 되는가?  
   - `FILLED` 확정, fill truth 우선, cancel 의도는 reason으로만 보존.

3. 시스템이 죽었다가 살아나면 어떻게 되는가?  
   - broker/local 재대조로 in-flight 복원 후 미해결 상태 정리 전 신규 주문 금지.

4. broker와 상태가 다르면 어떻게 되는가?  
   - reconcile correction 실행, 미해결은 `UNKNOWN`으로 승격.

5. 지금 이 주문은 안전한 상태인가?  
   - terminal이 broker 기준으로 확정되었고 `UNKNOWN/MISMATCH`가 없을 때만 안전.

