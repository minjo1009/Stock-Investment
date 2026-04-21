# Task 025: FillEvent Contract Alignment

## Purpose
- FillEvent를 Execution State Machine과 정합되는 canonical 이벤트 계약으로 고정한다.

## Background
- Execution 상태(NEW/SUBMITTED/PARTIAL_FILLED/FILLED/...)는 정의되었지만, FillEvent가 상태 전이를 어떻게 유발하는지 계약이 부족했다.

## In Scope
- FillEvent canonical 필드 보강
- apply_fill_event 함수 도입
- overfill/wrong-order 차단 규칙 반영
- contracts/domain-model 문서 반영
- execution interface 최소 보강(on_fill)
- dummy fill 시뮬레이션 및 테스트 추가

## Out of Scope
- 가격/슬리피지/VWAP 계산
- 실제 브로커/KIS 연동
- retry/idempotency 구현

## Inputs
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/common/models.py`
- `src/execution/interface.py`
- `src/app/pipeline.py`

## Outputs
- 이벤트 기반 상태 전이 계약
- FillEvent 적용 함수 및 검증 테스트

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/execution/interface.py`
- `src/app/main.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 024 (Execution State Machine Contract)

## Implementation Notes
- FillEvent는 상태 전이의 원인 이벤트로 취급.
- apply_fill_event는 immutable update만 수행.
- PARTIAL/FILLED 기준은 cumulative filled와 order.quantity 비교로 판정.

## Acceptance Criteria
- FillEvent canonical 구조가 코드/문서에 일치.
- apply_fill_event가 partial/full/overfill/wrong-order를 규칙대로 처리.
- 테스트가 이벤트-상태 정합성을 검증.

## Tests
- partial fill -> PARTIAL_FILLED
- full fill -> FILLED
- overfill -> ValueError
- wrong order_id -> ValueError
- cumulative filled 업데이트 검증

## Risks
- 다중 partial fill 집계 정책은 현재 최소 계약 수준이며 후속 상세화가 필요하다.
