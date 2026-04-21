# Task 026: Fill Acceptance Policy (Default Deny)

## Purpose
- CANCELLED/REJECTED 이후 fill 처리 정책을 포함해 FillEvent 허용 상태를 보수적으로 고정한다.

## Background
- FillEvent와 상태 전이 계약은 존재하지만, 상태별 허용/차단 규칙이 충분히 명시되지 않아 해석 편차가 발생할 수 있었다.

## In Scope
- apply_fill_event 허용 상태 제한(`SUBMITTED`, `PARTIAL_FILLED`)
- 차단 상태(`NEW`, `FILLED`, `CANCELLED`, `REJECTED`) 정책 반영
- contracts/domain-model 정책 문구 보강
- 상태별 허용/차단 테스트 추가

## Out of Scope
- late fill reconciliation 구현
- duplicate fill 처리 엔진
- 네트워크/브로커 연동

## Inputs
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/common/models.py`
- `src/execution/interface.py`
- `tests/unit/test_structure.py`

## Outputs
- FillEvent acceptance canonical policy
- 상태별 차단/허용 테스트

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/execution/interface.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 025 (FillEvent Contract Alignment)

## Implementation Notes
- 현재 단계 정책은 default deny.
- 허용 상태 외 fill은 ValueError.
- partial/full/overfill/wrong-order 기존 규칙은 유지.

## Acceptance Criteria
- apply_fill_event가 허용 상태를 코드로 강제한다.
- contracts/domain-model에 정책이 명시된다.
- 테스트가 차단/허용 케이스를 검증한다.

## Tests
- NEW/CANCELLED/REJECTED/FILLED 차단 테스트
- SUBMITTED/PARTIAL_FILLED 허용 테스트

## Risks
- 실전 late fill은 후속 reconciliation task가 필요하다.
