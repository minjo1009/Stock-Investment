# Canonical Domain Model

## Purpose
- 아키텍처 전 레이어에서 공통으로 사용하는 핵심 도메인 객체를 정의한다.
- 레이어별 객체 재정의를 금지하고, 로그/리플레이/백테스트/감사추적의 공통 기준을 제공한다.

## Design Principles
- 모든 객체는 명시적 필드만 사용한다.
- 암묵적 필드, 런타임 임의 확장 필드를 금지한다.
- 동일 의미 객체를 레이어별로 재명명하거나 구조를 바꿔 재정의하지 않는다.
- `paper/live` 환경은 주요 객체에서 식별 가능해야 한다.
- 본 문서는 구현 코드가 아니라 계약 문서이며, 필드 추가/변경은 별도 Task로 관리한다.

## Core Domain Objects
### 1) `signal_event`
- 역할: Strategy Layer 출력
```yaml
signal_event:
  event_id: string
  timestamp: string   # ISO-8601 UTC
  market: string      # KR | US
  symbol: string
  strategy_id: string
  action: string      # ENTER | EXIT | HOLD | SKIP
  side: string        # BUY | SELL | NONE
  reason: string
  score: number|null  # optional
```

### 2) `risk_decision`
- 역할: Risk Layer 출력
```yaml
risk_decision:
  decision_id: string
  event_id: string
  status: string          # ALLOW | BLOCK | REDUCE
  block_reason: string|null
  approved_size: number
  risk_snapshot_id: string
```

### 3) `order_intent`
- 역할: Execution Layer 입력
```yaml
order_intent:
  intent_id: string
  market: string          # KR | US
  symbol: string
  side: string            # BUY | SELL
  quantity: number
  order_type: string      # LIMIT | MARKET
  limit_price: number|null
  stop_loss: number|null
  take_profit: number|null
  timestamp: string       # ISO-8601 UTC
```

### 4) `broker_order`
- 역할: 브로커 주문 상태 표현(KIS API 전달/동기화 대상)
```yaml
broker_order:
  broker_order_id: string
  intent_id: string
  env: string            # paper | live
  status: string         # NEW | PARTIAL | FILLED | CANCELED
  submitted_at: string   # ISO-8601 UTC
```

### 5) `fill_event`
- 역할: 체결 이벤트
```yaml
fill_event:
  fill_id: string
  broker_order_id: string
  symbol: string
  price: number
  quantity: number
  timestamp: string      # ISO-8601 UTC
```

### 6) `position_snapshot`
- 역할: 포지션 상태 스냅샷
```yaml
position_snapshot:
  symbol: string
  quantity: number
  avg_price: number
  unrealized_pnl: number
  realized_pnl: number
```

### 7) `account_snapshot`
- 역할: 계좌 상태 스냅샷
```yaml
account_snapshot:
  env: string               # paper | live
  total_balance: number
  available_balance: number
  timestamp: string         # ISO-8601 UTC
```

## Relationships
- 기본 흐름:
`signal_event -> risk_decision -> order_intent -> broker_order -> fill_event -> position_snapshot`
- 계좌 반영 흐름:
`fill_event -> account_snapshot`
- 참조 규칙:
- `risk_decision.event_id`는 `signal_event.event_id`를 참조한다.
- `broker_order.intent_id`는 `order_intent.intent_id`를 참조한다.
- `fill_event.broker_order_id`는 `broker_order.broker_order_id`를 참조한다.

## Environment Rule
- `paper`와 `live` 데이터는 저장/조회/리포트에서 완전 분리한다.
- `broker_order.env`, `account_snapshot.env`는 필수 필드다.
- 동일 키(`symbol`, `strategy_id`)를 사용하더라도 환경이 다르면 동일 객체로 취급하지 않는다.
- 환경 혼합 계산(예: paper 체결 + live 포지션)은 금지한다.

## Acceptance Criteria
- 핵심 객체 7개가 모두 정의되어 있다.
- 각 객체 필드가 명시적으로 선언되어 있다.
- 객체 관계와 참조 흐름이 문서로 추적 가능하다.
- paper/live 분리 규칙이 객체 수준에서 확인 가능하다.
- 본 문서를 기반으로 후속 설계 Task(Execution/Risk/Strategy 상세)로 분해할 수 있다.
