# Task 016: Risk Completeness / Nullability Policy

## Purpose
- Risk 평가 가능 조건(completeness/nullability)을 코드와 문서에 일관되게 고정한다.

## Background
- RiskInputContext는 존재했지만 account/position nullability, stale snapshot, feature completeness 정책이 모호했다.

## In Scope
- Risk evaluable 정책 정의
- 호출 전 조건 검사 함수 도입
- contracts/risk interface 문서화
- 구조 검증 테스트 추가

## Out of Scope
- ALLOW/BLOCK/REDUCE 계산 로직
- 주문 실행 및 브로커 연동

## Inputs
- `context/architecture/contracts.md`
- `src/common/models.py`
- `src/risk/interface.py`
- `src/app/pipeline.py`

## Outputs
- `is_risk_evaluable` 정책 함수
- Risk nullability/completeness 계약 문서

## Target Files
- `context/architecture/contracts.md`
- `src/common/models.py`
- `src/risk/interface.py`
- `src/app/pipeline.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 006(5-stage 하네스)

## Implementation Notes
- account=None은 paper/foundation에서만 허용, live는 차단.
- position=None은 flat 허용.
- stale snapshot/필수 feature 결측은 평가 금지.

## Acceptance Criteria
- Risk 호출 전 evaluable 검사 존재.
- 문서와 코드 정책이 일치.

## Tests
- account=None 정책 테스트
- position=None 정책 테스트
- stale snapshot 차단 테스트
- feature missing/None 차단 테스트

## Risks
- live 환경 상세 정책은 후속 task에서 확장 필요.

