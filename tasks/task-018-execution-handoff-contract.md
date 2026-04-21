# Task 018: Execution Handoff Contract

## Purpose
- RiskDecision에서 OrderIntent로의 handoff 계약을 정의한다.

## Background
- Risk와 Execution 경계는 존재했으나 변환 규칙이 암묵적이었다.

## In Scope
- `RiskDecision -> OrderIntent` 매핑 함수 도입
- BLOCK/ALLOW/REDUCE 매핑 규칙 반영
- pipeline 연결

## Out of Scope
- 주문/가격/수량 계산
- 브로커 API 연동

## Inputs
- `src/common/models.py`
- `src/app/pipeline.py`
- `context/architecture/contracts.md`

## Outputs
- 매핑 함수
- handoff 계약 문서

## Target Files
- `src/common/models.py`
- `src/app/pipeline.py`
- `src/execution/interface.py`
- `context/architecture/contracts.md`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 017

## Implementation Notes
- BLOCK은 intent 생성 금지.
- ALLOW/REDUCE는 intent 생성 가능.

## Acceptance Criteria
- handoff 계약이 코드와 문서에 명시됨.

## Tests
- BLOCK -> None 테스트
- ALLOW/REDUCE intent 매핑 테스트

## Risks
- intent 필드 canonical 정제 필요(후속 refinement).

