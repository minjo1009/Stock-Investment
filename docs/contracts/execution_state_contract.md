# Execution State Contract

## 1. Purpose

이 문서의 목적은 주문/체결/포지션/리컨실리에이션에서 사용하는 상태 언어를 단일 계약으로 고정하는 것이다.  
핵심은 다음 사고를 방지하는 데 있다.

- 로컬은 종료로 봤지만 브로커에는 살아있는 주문
- 미체결/취소/실패를 동일하게 처리해 복구 절차가 꼬이는 문제
- 백테스트 상태와 실주문 상태의 의미 불일치로 인한 운영 착시

실계좌 전환 전 이 계약이 선행되어야 하는 이유는, 실계좌에서는 전략 성능보다 **애매한 상태 처리 실패**가 더 큰 손실을 만들기 때문이다.

---

## 2. Current State Audit

### 2.1 상태값 수집 요약

| Layer | Observed States / Values | Where Used |
|---|---|---|
| DB/store (`state/store.py`) | `ALLOWED_RUN_RESULTS`: `ORDER_SUBMITTED`, `FILLED`, `TIMEOUT`, `FAILED`, `SKIPPED_DUPLICATE`, `SKIPPED_RECON_BLOCK` | `trade_runs.result_status` |
| DB/store (`state/store.py`) | `ALLOWED_ORDER_STATUS`: `SUBMITTED`, `PENDING`, `FILLED`, `TIMEOUT`, `FAILED`, `REJECTED` | `orders.status` |
| DB/store (`state/store.py`) | Fill source: `ORDER_STATUS`, `POSITION_DELTA_FALLBACK` | `fills.source` |
| run_trade_once (`src/app/run_trade_once.py`) | Runtime/result: `ORDER_SUBMITTED`, `FILLED`, `TIMEOUT`, `FAILED`, `SKIPPED_DUPLICATE`, `SKIPPED_RECON_BLOCK` | run lifecycle |
| run_trade_once (`src/app/run_trade_once.py`) | Polling local var: `PENDING`, `FILLED` | fill polling path |
| reconciliation (`src/app/reconciliation.py`) | Mapped internal: `SUBMITTED`, `FILLED`, `REJECTED`, `FAILED`, `CANCELLED`, `UNKNOWN` | broker status mapping |
| reconciliation (`src/app/reconciliation.py`) | Outcome status: `CLEAN`, `MISMATCH`, `ERROR` | reconciliation result |
| reconciliation (`src/app/reconciliation.py`) | Severity: `INFO`, `WARN`, `CRITICAL` | blocking logic / UI |
| backtest engine (`src/backtest/engine_full.py`) | Pending order field: `PENDING`, `FILLED`, `EXPIRED` | pending entry/exit internal state |
| backtest engine (`src/backtest/engine_full.py`) | Exit rule metadata: `STOP`, `RISK_BREAK_EVEN_STOP`, `RISK_MFE_GIVEBACK_50`, `RISK_TIME_STOP`, `TREND_BREAK_2BAR`, `TIME_EXIT` | trade metadata |
| backtest engine (`src/backtest/engine_full.py`) | Metadata flags: `entry_order_status=FILLED`, `exit_order_status=FILLED`, `unfilled_flag`, `expired_flag` | analysis/UI payload |
| UI (`src/ui/app.py`) | Displays `trade_runs.result_status`, `orders.status`, reconciliation `status/severity`, fallback `UNKNOWN` labels | Overview/Orders/Reconciliation/Trade Detail |

### 2.2 현재 불일치

1. `CANCELLED`는 reconciliation에는 있으나 `orders.status` 허용 목록에는 없음.  
2. `TIMEOUT`이 `orders.status`와 `trade_runs.result_status`에 들어가 있지만 의미가 혼재(종료 상태처럼 사용).  
3. 백테스트는 `EXPIRED`를 내부 pending 상태로 사용하지만 실주문 DB에는 `EXPIRED`가 없다.  
4. `PENDING`은 DB 허용 상태지만 `run_trade_once` 저장 경로에서는 거의 사용되지 않는다(`SUBMITTED -> FILLED/TIMEOUT/FAILED` 중심).  
5. UI는 상태를 읽어 보여주지만 canonical grouping(ACTIVE/TERMINAL/ERROR/RECON_REQUIRED)이 아직 정의되어 있지 않다.

---

## 3. Canonical Order State

아래를 주문 canonical 상태로 정의한다.

| State | 의미 | 진입 조건 | 다음 상태 | Terminal | Recoverable | Broker Truth Required |
|---|---|---|---|---|---|---|
| `CREATED` | 로컬 intent 생성 완료, 아직 전송 전 | intent 생성 성공 | `SUBMITTED`, `FAILED` | No | Yes | No |
| `SUBMITTED` | 브로커 전송 요청 성공(ack 수신) | submit API 성공 | `PENDING`, `PARTIAL`, `FILLED`, `REJECTED`, `FAILED`, `CANCEL_REQUESTED` | No | Yes | Yes |
| `PENDING` | 미체결 대기 상태 | 브로커가 open/working 계열 | `PARTIAL`, `FILLED`, `CANCEL_REQUESTED`, `EXPIRED`, `FAILED` | No | Yes | Yes |
| `PARTIAL` | 부분 체결 발생, 잔량 존재 | fill_qty > 0 and remain > 0 | `FILLED`, `CANCEL_REQUESTED`, `FAILED`, `EXPIRED` | No | Yes | Yes |
| `FILLED` | 주문 수량 전량 체결 | cumulative fill == order qty | (none, 단 `LATE_FILL` 정정 이벤트 허용) | Yes | Conditional | Yes |
| `CANCEL_REQUESTED` | 취소 요청을 브로커에 전송함 | pending/partial에서 cancel API 호출 | `CANCELLED`, `FILLED`, `FAILED`, `UNKNOWN` | No | Yes | Yes |
| `CANCELLED` | 브로커가 취소 확정 | cancel confirmation | (none, 단 `LATE_FILL` 정정 이벤트 허용) | Yes | Conditional | Yes |
| `EXPIRED` | TIF/만료 정책으로 주문 유효기간 종료 | broker/local expiry rule 확정 | `CANCELLED` or terminal | Yes | Conditional | Yes |
| `REJECTED` | 브로커가 주문 거부 | reject response | (none) | Yes | No | Yes |
| `FAILED` | 전송/처리 실패(브로커/네트워크/로컬) | transport/API/internal failure | `UNKNOWN`, 재시도 흐름 | No(권장) | Yes | Yes |
| `UNKNOWN` | 상태 확정 불가, reconcile 필요 | 응답 불명/상태 충돌 | `PENDING`, `FILLED`, `CANCELLED`, `REJECTED`, `FAILED` | No | Yes | Yes |

---

## 4. Canonical Fill State

| Fill State | 의미 | 사용처 |
|---|---|---|
| `NO_FILL` | 체결 이벤트 없음 | 신규/대기 주문 |
| `PARTIAL_FILL` | 일부 수량 체결 | `PARTIAL` 주문 |
| `FULL_FILL` | 전체 수량 체결 | `FILLED` 주문 |
| `LATE_FILL` | 종료 상태 이후 뒤늦게 수신된 체결 | reconciliation correction path |
| `UNKNOWN_FILL` | 체결 여부 불명/파싱 실패 | broker mismatch triage |

---

## 5. Canonical Position State

| Position State | 의미 | 전이 조건 |
|---|---|---|
| `FLAT` | 보유 수량 0 | 초기 상태 / 전량 청산 |
| `OPEN` | 순보유 수량 > 0 | 최초/추가 체결 |
| `REDUCING` | 보유 축소 진행 중(부분 청산) | `OPEN`에서 부분 매도/부분 취소 |
| `CLOSED` | 포지션 종료 이벤트 확정 | `OPEN/REDUCING`에서 전량 청산 |
| `UNKNOWN_POSITION` | 포지션 진실원 불일치 | broker/local mismatch |

---

## 6. State Transition Table

| From | To | Trigger | Allowed | Required Action |
|---|---|---|---|---|
| `CREATED` | `SUBMITTED` | submit API ack | Yes | order_id 저장 |
| `CREATED` | `FAILED` | submit 실패 | Yes | 오류 원인 기록, 재시도 정책 결정 |
| `SUBMITTED` | `PENDING` | broker open/working | Yes | polling/reconcile 시작 |
| `SUBMITTED` | `PARTIAL` | first fill received | Yes | fill 누적/잔량 계산 |
| `SUBMITTED` | `FILLED` | full fill | Yes | terminal 처리 + position 반영 |
| `SUBMITTED` | `REJECTED` | broker reject | Yes | terminal 처리 |
| `SUBMITTED` | `FAILED` | transport/API failure | Yes | UNKNOWN or retry path |
| `PENDING` | `PARTIAL` | partial fill | Yes | fill record append |
| `PENDING` | `FILLED` | full fill | Yes | terminal 처리 |
| `PENDING` | `CANCEL_REQUESTED` | cancel 요청 | Yes | cancel request 기록 |
| `CANCEL_REQUESTED` | `CANCELLED` | cancel confirm | Yes | terminal 처리 |
| `CANCEL_REQUESTED` | `FILLED` | 취소 전에 체결 완료 | Yes | fill truth 우선 |
| `PENDING` | `EXPIRED` | TIF/만료 확인 | Yes | terminal 처리(브로커 truth 확인) |
| `PENDING` | `FAILED` | API 장애/처리 실패 | Yes | reconcile required |
| `ANY` | `UNKNOWN` | 상태 충돌/응답 불명 | Yes | 신규 주문 차단 + reconcile |

---

## 7. Timeout / Expiry / Cancel Semantics

### 구분 정의

- `TIMEOUT`: **상태가 아니라 이벤트/이유(reason code)**  
  - 의미: 정해진 시간 내 체결/상태 확정 불가
  - canonical order state로 직접 저장하지 않는다(권장).
- `EXPIRED`: 주문 유효기간 만료로 브로커/정책상 종료
- `CANCELLED`: 취소 요청 후 브로커가 취소 확정
- `FAILED`: 전송/처리 실패(상태 미확정 가능)

### 권장 흐름

`PENDING`  
→ `TIMEOUT_DETECTED` (event)  
→ `CANCEL_REQUESTED`  
→ broker cancel confirmation  
→ `CANCELLED` (or race-condition 시 `FILLED`)

결론: **TIMEOUT은 canonical state가 아니라 이벤트/오류 사유로 다루는 것이 적합**하다.

---

## 8. Broker-to-Local Mapping

| Broker Signal | Local Canonical Order State |
|---|---|
| submitted/open/working/no fill | `PENDING` |
| partial fill | `PARTIAL` |
| full fill | `FILLED` |
| rejected/denied | `REJECTED` |
| cancelled/canceled | `CANCELLED` |
| explicit expiry | `EXPIRED` |
| unknown status text | `UNKNOWN` |
| API transport failure | `FAILED` (then reconcile) |

추가 규칙:
- broker status가 `UNKNOWN`이면 신규 주문은 차단하고 reconcile 우선.
- broker가 fill evidence를 보이면 로컬 상태보다 broker truth를 우선한다.

---

## 9. Backtest-to-Live Mapping

| Backtest Status/Outcome | Live Canonical Mapping |
|---|---|
| entry/exit `FILLED` | broker fill truth 확인 후 `FILLED` |
| pending `EXPIRED` | live에서는 cancel/expiry broker 확정 후 `CANCELLED` 또는 `EXPIRED` |
| stop/time/trend exit rule | live에서는 주문 상태(`PENDING/PARTIAL/FILLED`)와 exit reason을 분리 저장 |
| `unfilled_flag` | live에서는 `PENDING -> CANCEL_REQUESTED -> CANCELLED/EXPIRED`로 상세화 |

핵심: 백테스트의 결과 상태를 live에 1:1 복사하지 않고, **브로커 확정 상태를 기준으로 매핑**한다.

---

## 10. Store / DB Contract

이번 태스크는 변경 없이 “필요 계약”만 정의한다.

### orders.status canonical set (제안)
- `CREATED`, `SUBMITTED`, `PENDING`, `PARTIAL`, `FILLED`, `CANCEL_REQUESTED`, `CANCELLED`, `EXPIRED`, `REJECTED`, `FAILED`, `UNKNOWN`

### fills contract
- fill source는 transport source(`ORDER_STATUS`, `POSITION_DELTA_FALLBACK`, future `BROKER_EXECUTION_REPORT`)와 분리해,
  fill state(`NO_FILL`, `PARTIAL_FILL`, `FULL_FILL`, `LATE_FILL`, `UNKNOWN_FILL`)를 별도 저장 필요.

### position_events linkage
- order terminal 상태 + fill 누적량과 정합되어야 하며, `LATE_FILL` correction event 허용 규칙 명시 필요.

### reconciliation event type
- `MISSING_BROKER`, `MISSING_LOCAL`, `STATUS_MISMATCH`, `FILL_MISMATCH`, plus `UNKNOWN_STATUS` 권장.

---

## 11. UI Display Contract

UI 배지 그룹 제안:

| UI Group | Mapped States |
|---|---|
| `ACTIVE` | `CREATED`, `SUBMITTED`, `PENDING`, `PARTIAL`, `CANCEL_REQUESTED` |
| `TERMINAL` | `FILLED`, `CANCELLED`, `EXPIRED`, `REJECTED` |
| `ERROR` | `FAILED` |
| `NEEDS_RECONCILIATION` | `UNKNOWN`, state conflict, late fill pending |

표시 규칙:
- `TIMEOUT`은 badge state가 아니라 이벤트/사유 텍스트로 노출.
- reconciliation severity(`WARN/CRITICAL`)는 상태 배지와 분리해 별도 경고 표시.

---

## 12. Invariants

1. `FILLED` order must have at least one fill record.  
2. `CANCELLED` order must not receive new fills except `LATE_FILL` correction path.  
3. `PARTIAL` order must track remaining quantity > 0.  
4. terminal 상태는 reconciliation correction 외 직접 전이 금지.  
5. `UNKNOWN` 상태 주문이 있으면 신규 주문 차단.  
6. broker truth와 local truth가 충돌 시 broker truth 우선 + 이벤트 기록 필수.  
7. position quantity는 fill 누적합과 일치해야 한다.

---

## 13. Immediate Implementation Plan

1. Store allowed status 확장 및 TIMEOUT 의미 분리(event화)  
2. `run_trade_once` 전이 경로를 canonical state에 맞게 정렬 (`CANCEL_REQUESTED/CANCELLED` 포함)  
3. reconciliation mapping에 canonical state 직접 매핑 + UNKNOWN 강제 차단  
4. UI badge mapping(`ACTIVE/TERMINAL/ERROR/NEEDS_RECONCILIATION`) 적용  
5. 테스트 확장:
   - 상태 전이 unit test
   - timeout->cancel flow integration test
   - late fill reconciliation test

---

## 14. Non-goals

- 코드 변경
- DB migration 실행
- broker API 구현 확장
- UI 구현 변경

---

## Evaluation Standard Answers

1. 주문이 지금 살아있는가?  
   - `ACTIVE` 상태군(`CREATED/SUBMITTED/PENDING/PARTIAL/CANCEL_REQUESTED`)으로 즉시 판정 가능.

2. 주문이 끝났는가?  
   - `TERMINAL` 상태군(`FILLED/CANCELLED/EXPIRED/REJECTED`)으로 판정.

3. 브로커와 로컬 상태가 다른가?  
   - `STATUS_MISMATCH`, `MISSING_*`, `FILL_MISMATCH`, `UNKNOWN`로 판정.

4. 새 주문을 내도 안전한가?  
   - `UNKNOWN`/`CRITICAL MISMATCH`/미해결 in-flight 주문이 없을 때만 허용.

5. 장애 후 복구 시 무엇을 먼저 확인해야 하는가?  
   - broker truth pull → local reconcile → `UNKNOWN/ACTIVE` 정리 → 신규 주문 허용 여부 결정.

