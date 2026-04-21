# Task 020: Risk Flag Taxonomy

## Purpose
- `risk_flags`를 자유 문자열이 아닌 canonical taxonomy로 고정한다.

## Background
- 리스크 원인 설명은 필요했으나 값 집합이 고정되지 않아 해석 일관성이 낮았다.

## In Scope
- `RiskFlag` Literal 정의
- 허용 값 집합 상수화
- invalid flag 차단 검증
- taxonomy 문서화

## Out of Scope
- flag 생성 판정 로직
- threshold 계산

## Inputs
- `src/common/models.py`
- `context/architecture/contracts.md`

## Outputs
- 타입화된 risk_flags 계약

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `src/risk/interface.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 019

## Implementation Notes
- taxonomy는 설명 계약이며 로직을 포함하지 않는다.

## Acceptance Criteria
- canonical flag 집합이 코드와 문서에 일치.
- invalid flag 입력 차단.

## Tests
- taxonomy 값 검증
- invalid flag 예외 검증

## Risks
- 신규 flag 확장 시 문서/코드 동시 반영 필요.

