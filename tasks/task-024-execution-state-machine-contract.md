# Task 024: Execution State Machine Contract

## Purpose
- Execution Layer의 주문 lifecycle을 상태 기반 canonical contract로 고정한다.

## Background
- OrderIntent와 quantity 공급 계약은 정립됐지만 주문 상태 전이 규칙이 명시되지 않아 execution 동작 경계가 불명확했다.

## In Scope
- ExecutionStatus 정의
- BrokerOrder canonical 필드 보강
- 상태 전이 검증/전이 함수 추가
- execution interface submit/cancel/get_status 계약 정리
- contracts/domain-model 문서 정합화
- 상태 전이 테스트 추가

## Out of Scope
- 실제 주문 API/KIS 연동
- 네트워크 호출
- 체결/슬리피지 계산
- 전략/리스크 로직 변경

## Inputs
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/common/models.py`
- `src/execution/interface.py`
- `src/app/pipeline.py`

## Outputs
- Execution state machine canonical contract
- 상태 전이 검증 가능한 코드/테스트

## Target Files
- `src/common/models.py`
- `src/execution/interface.py`
- `src/app/pipeline.py`
- `src/app/main.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 023

## Implementation Notes
- 상태 집합: NEW, SUBMITTED, PARTIAL_FILLED, FILLED, CANCELLED, REJECTED
- invalid transition은 ValueError로 차단
- immutable dataclass 원칙 유지

## Acceptance Criteria
- 상태 타입/전이 함수/전이 규칙이 코드와 문서에 일치한다.
- DummyExecutionPort가 상태 전이를 흉내내는 최소 구현을 가진다.
- 테스트가 valid/invalid 전이를 검증한다.

## Tests
- status 타입 존재 테스트
- valid transition 허용 테스트
- invalid transition 차단 테스트
- NEW->SUBMITTED 허용, NEW->FILLED 금지 테스트
- transition 시 updated_at 변경 테스트

## Risks
- FillEvent 상세 lifecycle은 후속 task에서 상태기계와 더 세밀히 정렬이 필요하다.
