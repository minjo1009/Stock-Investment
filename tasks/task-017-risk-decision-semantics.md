# Task 017: RiskDecision Semantics Contract

## Purpose
- RiskDecision 의미를 canonical 계약으로 고정한다.

## Background
- RiskDecision 객체는 존재했지만 decision 의미와 필드 역할이 분명하지 않았다.

## In Scope
- `ALLOW/BLOCK/REDUCE` 의미 명시
- `decision/reason/risk_flags/reduce_factor` semantics 고정
- DummyRiskPort 반환 계약 반영
- 구조 검증 테스트 보강

## Out of Scope
- decision 판정식 구현
- 축소 계산 및 실행 로직

## Inputs
- `context/architecture/contracts.md`
- `src/common/models.py`
- `src/risk/interface.py`
- `src/app/main.py`

## Outputs
- RiskDecision 의미 계약 문서/코드 일치

## Target Files
- `context/architecture/contracts.md`
- `src/common/models.py`
- `src/risk/interface.py`
- `src/app/main.py`
- `src/app/pipeline.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 016

## Implementation Notes
- RiskDecision은 주문 지시가 아니라 판단 결과 계약으로 정의.
- reduce_factor 규칙(ALLOW/BLOCK 시 None) 검증 포함.

## Acceptance Criteria
- semantics 문서화 완료.
- DummyRiskPort가 계약 준수 객체 반환.

## Tests
- 필드 존재 테스트
- canonical decision 값 테스트
- reduce_factor 규칙 테스트

## Risks
- 레거시 필드 공존으로 일시적 중복 가능성 존재(후속 제거).

