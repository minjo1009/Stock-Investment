# Task 023: Quantity Supply Responsibility Contract

## Purpose
- OrderIntent.quantity의 공급 책임 주체를 canonical contract로 고정한다.

## Background
- quantity가 최종 수량으로 정의되었지만 공급 주체(upstream/risk/execution) 경계가 명시적으로 고정되지 않았다.
- skeleton 단계에서 quantity 미공급 시 intent 생성 불가 상태가 반복되어 책임 분리가 필요했다.

## In Scope
- `QuantityInstruction` 계약 객체 도입
- `SignalEvent + RiskDecision + QuantityInstruction -> OrderIntent` handoff 조립 규칙 도입
- quantity 공급 책임 문서화
- BLOCK/ALLOW/REDUCE + quantity 유무 조합 검증 테스트 추가

## Out of Scope
- 사이징 계산 로직 구현
- reduce_factor를 final_quantity로 변환하는 계산식 구현
- execution 주문 로직 및 브로커 연동

## Inputs
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/common/models.py`
- `src/app/pipeline.py`
- `src/app/main.py`

## Outputs
- QuantityInstruction canonical 계약
- handoff 조립 함수
- pipeline/main quantity_instruction 주입 경로
- 구조 검증 테스트

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/app/pipeline.py`
- `src/app/main.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 022 (OrderIntent canonical refinement)

## Implementation Notes
- Option A 채택: `quantity = 최종 주문 수량`
- Risk는 판단만 제공(`reduce_factor`), quantity 계산은 수행하지 않는다.
- Execution은 quantity를 재계산하지 않는다.
- `decision == BLOCK`이면 quantity 존재 여부와 무관하게 intent 생성 금지.

## Acceptance Criteria
- QuantityInstruction가 코드에 존재하고 유효성 검증(`final_quantity > 0`)이 구현된다.
- 조립 함수가 BLOCK/quantity 없음 케이스를 차단한다.
- contracts/domain-model 문서에 공급 책임 및 의미 분리가 명시된다.
- 테스트가 계약 조건을 검증한다.

## Tests
- QuantityInstruction import/validation 테스트
- BLOCK + quantity 존재 시 intent 생성 금지 테스트
- quantity_instruction 없음 시 intent 생성 금지 테스트
- ALLOW/REDUCE + quantity 존재 시 intent 생성 가능 테스트
- reduce_factor와 final_quantity 독립 의미 검증 테스트

## Risks
- upstream sizing component의 정확한 시스템 이름/인터페이스는 아직 미결정이다.
- KR/US 수량 단위 및 fractional share 정책은 후속 task에서 상세화가 필요하다.
