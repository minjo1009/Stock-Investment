# Task 086 — Paper Pilot Risk Guard Lock

## 1. Purpose

Task 085는 implementation PASS / operation WARNING 상태다.  
원인은 전략 성능보다 운영 가드 미고정과 샘플 부족이다.  
본 문서는 Paper Pilot 반복 실행 전에 주문/노출/중단 규칙을 고정해 운영 리스크를 선제 차단하기 위한 계약 문서다.

## 2. Locked Pilot Profile

- strategy: `D_PORTFOLIO_SECTOR_FILTER`
- execution: `LIMITED_CHASE`
- risk: `TIME_STOP_ONLY`
- environment: `KIS paper only`
- initial capital reference: `1,000,000 KRW`
- live capital: `not allowed`

## 3. Risk Guard Values

- daily_loss_limit: `-1.0% of reference capital`
- hard_daily_loss_limit_krw: `-10,000 KRW`
- max_gross_exposure: `30% of reference capital`
- max_total_notional_krw: `300,000 KRW`
- max_positions: `3`
- symbol_cap: `15% of reference capital`
- max_symbol_notional_krw: `150,000 KRW`
- sector_cap: `20% of reference capital`
- max_sector_notional_krw: `200,000 KRW`
- max_new_orders_per_day: `3`
- max_cancel_attempts_per_order: `30`
- unknown_order_halt: `true`
- reconciliation_critical_halt: `true`
- kill_switch_required: `true`
- market_order_allowed: `false`

## 4. Mandatory Blocks

아래 조건에서는 신규 주문을 차단한다.

- UNKNOWN order exists
- reconciliation critical mismatch exists
- missing KIS credentials
- not KIS paper environment
- daily loss limit breached
- max exposure breached
- symbol cap breached
- sector cap breached
- stale data
- market closed
- missing broker fill truth

## 5. Operator Checklist

실행 전 체크:

- env variables present
- `KIS_ENVIRONMENT=paper`
- streamlit not required
- reports path writable
- no UNKNOWN order
- no critical reconciliation mismatch
- kill switch OFF

## 6. Stop Conditions

아래 조건에서 즉시 중단한다.

- UNKNOWN 발생
- cancel loop UNKNOWN escalation
- late fill mismatch unresolved
- broker/local position mismatch
- daily loss breach
- unexpected market order path
- test account unavailable

## 7. Non-goals

이번 단계에서 하지 않는 것:

- live trading
- strategy tuning
- ML integration
- universe/ranking modification
- size increase

