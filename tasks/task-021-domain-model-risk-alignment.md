# Task 021: Domain Model Risk Alignment

## Purpose
- `domain-model.md`를 최신 RiskDecision/RiskFlag 구조와 정합화한다.

## Background
- 코드가 선행 업데이트되며 domain-model 문서가 구버전 구조를 유지했다.

## In Scope
- RiskDecision 최신 필드 반영
- legacy 제거 상태 명시
- RiskFlag taxonomy/의미 문서화
- RiskInputContext 구조 검증 반영

## Out of Scope
- Python 코드 변경
- 계약 의미 재설계

## Inputs
- `context/architecture/domain-model.md`
- `src/common/models.py`
- `context/architecture/contracts.md`

## Outputs
- 코드와 일치하는 domain model 문서

## Target Files
- `context/architecture/domain-model.md`

## Dependencies
- 선행: Task 020

## Implementation Notes
- Facts vs Interpretation 구분 유지.
- Deprecated 항목은 제거가 아닌 제거 사실을 명시.

## Acceptance Criteria
- domain-model과 models.py Risk 구조 100% 일치.
- legacy 구조 불일치 해소.

## Tests
- 문서-코드 수동 대조 검증.

## Risks
- 후속 코드 변경 시 문서 동기화 누락 가능.

