# Task 019: RiskDecision Legacy Field Removal

## Purpose
- RiskDecision의 중복 legacy 필드를 제거해 single source를 고정한다.

## Background
- `decision`과 중복되는 `status/block_reason/approved_size`가 계약 혼선을 유발했다.

## In Scope
- legacy 필드 삭제
- 문서/테스트 정합화

## Out of Scope
- 새 의미 필드 추가
- decision semantics 변경

## Inputs
- `src/common/models.py`
- `context/architecture/contracts.md`
- `tests/unit/test_structure.py`

## Outputs
- legacy 제거된 RiskDecision 구조

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 017

## Implementation Notes
- docstring에 "Legacy fields removed" 명시.
- decision 단일 truth 유지.

## Acceptance Criteria
- legacy 필드 완전 제거.
- 테스트로 제거 상태 검증.

## Tests
- dataclass field 목록 검증.

## Risks
- 과거 문서/샘플 코드 잔존 시 재불일치 가능.

